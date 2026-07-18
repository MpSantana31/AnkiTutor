"""Chat panel GUI (PyQt6, already bundled with Anki).

``TutorPanel`` is a modal dialog: shows the card context, lets the user type a
question, calls the blocking ``tutor.ask`` and renders the answer. All
``TutorError`` failures are caught here and shown as a friendly message
(ADR-005 — Error Boundary); they never propagate to the Anki hook.
"""

from __future__ import annotations

from typing import Any

try:
    from aqt import mw
    from aqt.qt import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QTextBrowser,
        QThread,
        QVBoxLayout,
        QWidget,
        pyqtSignal,
    )
except ImportError:  # Outside Anki (tests/CI)
    mw = None  # type: ignore[assignment]
    QComboBox = QDialog = QDialogButtonBox = (  # type: ignore[assignment]
        QHBoxLayout
    ) = QLabel = QPlainTextEdit = QPushButton = QTextBrowser = QVBoxLayout = QWidget = (
        None
    )
    QThread = pyqtSignal = None  # type: ignore[assignment]

from . import utils
from .errors import TutorError
from .history import load_history
from .prompts import DIRECT_MODES

_MODES = ("explain", "simplify", "example", "relate")


def user_label(question: str, mode: str) -> str:
    """Label shown on the user bubble (mode name for direct modes)."""
    if mode in DIRECT_MODES:
        return f"You ({mode})"
    return "You"


def build_conversation_markdown(turns, user_label=user_label) -> str:
    """Render ``turns`` (question, mode, answer, is_error) as Markdown bubbles.

    Each turn becomes a ``**Role:** text`` heading followed by the answer,
    separated by a horizontal rule. Kept module-level so the chat layout can be
    unit-tested without PyQt/Anki.
    """
    parts = []
    for question, mode, answer, _is_error in turns:
        role = user_label(question, mode)
        if mode in DIRECT_MODES and not question:
            shown = f"[{mode}]"
        else:
            shown = question or f"[{mode}]"
        parts.append(f"**{role}:** {shown}\n\n{answer}")
    return "\n\n---\n\n".join(parts)


_STYLESHEET = """
QWidget#panel {
    background: #1e1e2e;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QLabel#header {
    color: #89b4fa;
    font-weight: bold;
    font-size: 14px;
}
QPlainTextEdit, QTextBrowser {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}
QTextBrowser#card-display {
    background: #181825;
    border: 1px solid #313244;
    max-height: 120px;
    min-height: 60px;
}
QTextBrowser#answer-display {
    background: #181825;
    border: 1px solid #313244;
}
QComboBox {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
}
QPushButton {
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 6px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background: #74c7ec;
}
QPushButton:pressed {
    background: #89dceb;
}
QPushButton#close-btn {
    background: #45475a;
    color: #cdd6f4;
}
QPushButton#close-btn:hover {
    background: #585b70;
}
QTextBrowser#chat-display {
    background: #181825;
    border: 1px solid #313244;
}
.bubble-user {
    background: #313244;
    border-left: 4px solid #89b4fa;
    border-radius: 6px;
    padding: 6px 8px;
    margin: 4px 0;
    color: #cdd6f4;
}
.bubble-ai {
    background: #1e1e2e;
    border-left: 4px solid #a6e3a1;
    border-radius: 6px;
    padding: 6px 8px;
    margin: 4px 0;
    color: #cdd6f4;
}
.bubble-error {
    background: #1e1e2e;
    border-left: 4px solid #f38ba8;
    border-radius: 6px;
    padding: 6px 8px;
    margin: 4px 0;
    color: #f38ba8;
}
.bubble-role {
    font-weight: bold;
}
"""


class TutorWorker(QThread if QThread is not None else object):
    """Background worker that streams a provider answer (ADR-003).

    Runs the network call off the UI thread. Emits tokens and the final result
    so the panel can render progressively without freezing Anki. When PyQt6 is
    unavailable (tests/CI) it degrades to a plain ``object`` so the module still
    imports.
    """

    token = pyqtSignal(str) if pyqtSignal is not None else None
    done = pyqtSignal(object) if pyqtSignal is not None else None
    error = pyqtSignal(object) if pyqtSignal is not None else None

    def __init__(self, card, question, mode) -> None:
        if QThread is not None:
            super().__init__()
        self.card = card
        self.question = question
        self.mode = mode

    def run(self) -> None:
        from . import tutor

        try:
            tutor.ask_stream(
                self.card,
                self.question,
                self.mode,
                on_token=self._emit_token,
                on_done=self._emit_done,
                on_error=self._emit_error,
            )
        except TutorError as exc:
            self._emit_error(exc)

    def _emit_token(self, piece: str) -> None:
        if self.token is not None:
            self.token.emit(piece)

    def _emit_done(self, answer) -> None:
        if self.done is not None:
            self.done.emit(answer)

    def _emit_error(self, exc) -> None:
        if self.error is not None:
            self.error.emit(exc)


class TutorPanel:
    """Chat panel wrapper; lazily builds the real QDialog when shown.

    Uses streaming for the answer (ADR-003). In direct modes
    (``simplify``/``example``/``relate``) the question input is disabled and a
    fixed question is sent to the provider.
    """

    def __init__(self, card: Any) -> None:
        self.card = card
        self._dlg = None
        self._worker = None
        self._streamed = ""
        self._conversation = []
        self._last_answer = None

    def show(self) -> None:
        if mw is None or QDialog is None:
            return
        self._build()
        self._dlg.exec()

    def _build(self) -> None:
        dlg = QDialog(mw)
        dlg.setWindowTitle("AnkiTutor — Ask a doubt")
        dlg.setMinimumSize(560, 520)
        dlg.setObjectName("panel")
        dlg.setStyleSheet(_STYLESHEET)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        header = QLabel("AnkiTutor")
        header.setObjectName("header")
        layout.addWidget(header)

        front, back = utils.extract_card(self.card)
        card_display = QTextBrowser()
        card_display.setObjectName("card-display")
        card_display.setOpenExternalLinks(False)
        card_display.setHtml(
            f'<span style="color:#a6e3a1;font-weight:bold;">Front:</span> {front}'
            f"<br>"
            f'<span style="color:#f38ba8;font-weight:bold;">Back:</span> {back}'
        )
        layout.addWidget(card_display)

        chat_label = QLabel("Conversation")
        chat_label.setObjectName("header")
        layout.addWidget(chat_label)

        # Chat history (accumulated Q/A bubbles); scrolls on its own.
        self.chat = QTextBrowser()
        self.chat.setObjectName("chat-display")
        self.chat.setOpenExternalLinks(False)
        self.chat.setPlaceholderText("Your conversation will appear here.")
        layout.addWidget(self.chat, stretch=1)

        q_row = QHBoxLayout()
        q_label = QLabel("Question")
        q_row.addWidget(q_label)
        q_row.addStretch(1)
        layout.addLayout(q_row)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Type your question here…")
        self.input.setMaximumHeight(80)
        layout.addWidget(self.input)

        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_row.addWidget(mode_label)
        self.mode_box = QComboBox()
        self.mode_box.addItems(_MODES)
        self.mode_box.currentTextChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_box)
        mode_row.addStretch(1)
        ask_btn = QPushButton("Ask")
        ask_btn.clicked.connect(self._on_ask)
        mode_row.addWidget(ask_btn)
        save_btn = QPushButton("Save to note")
        save_btn.setObjectName("save-btn")
        save_btn.clicked.connect(self._on_save)
        mode_row.addWidget(save_btn)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("close-btn")
        close_btn.clicked.connect(dlg.reject)
        mode_row.addWidget(close_btn)
        layout.addLayout(mode_row)

        self._last_answer = None
        self._dlg = dlg
        self._apply_mode_ui(self.mode_box.currentText())
        self._render_history()

    def _on_mode_changed(self, mode: str) -> None:
        self._apply_mode_ui(mode)

    def _apply_mode_ui(self, mode: str) -> None:
        """Enable/disable the question input for direct modes (M3 modes)."""
        if mode in DIRECT_MODES:
            self.input.setDisabled(True)
            self.input.setPlaceholderText("This mode asks automatically — click Ask.")
        else:
            self.input.setDisabled(False)
            self.input.setPlaceholderText("Type your question here…")

    def _user_label(self, question: str, mode: str) -> str:
        """Label shown on the user bubble (mode name for direct modes)."""
        return user_label(question, mode)

    def _render_history(self) -> None:
        """Render past Q/A turns for this card as chat bubbles."""
        _, card_id = utils.extract_card_meta(self.card)
        self._conversation = []
        entries = load_history(card_id)
        for e in entries:
            mode = e.get("mode", "explain")
            question = e.get("question", "")
            if mode in DIRECT_MODES and not question:
                question = f"[{mode}]"
            self._conversation.append((question, mode, e.get("answer", ""), False))
        self._redraw()

    def _on_ask(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        mode = self.mode_box.currentText()
        question = "" if mode in DIRECT_MODES else self.input.toPlainText().strip()
        self._streamed = ""
        self._conversation.append((question, mode, "Thinking…", False))
        self._redraw()
        if mode not in DIRECT_MODES and self.input.toPlainText().strip():
            self.input.clear()
        self._worker = TutorWorker(self.card, question, mode)
        self._worker.token.connect(self._on_token)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_token(self, piece: str) -> None:
        self._streamed += piece
        if self._conversation:
            question, mode, _, _ = self._conversation[-1]
            self._conversation[-1] = (question, mode, self._streamed, False)
            self._redraw()

    def _on_done(self, answer) -> None:
        self._last_answer = answer
        if self._conversation:
            question, mode, _, _ = self._conversation[-1]
            self._conversation[-1] = (question, mode, answer.answer, False)
            self._redraw()

    def _on_error(self, exc) -> None:
        msg = exc.user_message if isinstance(exc, TutorError) else f"Error: {exc}"
        if self._conversation:
            question, mode, _, _ = self._conversation[-1]
            self._conversation[-1] = (question, mode, msg, True)
            self._redraw()

    def _redraw(self) -> None:
        """Re-render the whole conversation as Markdown bubbles."""
        markdown = build_conversation_markdown(self._conversation, self._user_label)
        self.chat.setMarkdown(markdown)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        bar = self.chat.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())

    def _on_save(self) -> None:
        if self._last_answer is None:
            self._conversation.append(
                ("", "explain", "Ask a question first, then save its answer.", True)
            )
            self._redraw()
            return
        answer = self._last_answer
        save_text = utils.build_save_text(answer.question, answer.answer, answer.mode)
        result = utils.save_answer_to_note(self.card, save_text)
        field = result.field
        detail = f" (field: {field})" if field else ""
        preview = (answer.question or answer.mode).strip()
        if len(preview) > 80:
            preview = preview[:77] + "…"
        self._conversation.append(
            ("", "explain", f"Saved to note{detail}.\n\n> {preview}", True)
        )
        self._redraw()
