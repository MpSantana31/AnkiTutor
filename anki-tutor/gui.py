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
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # Outside Anki (tests/CI)
    mw = None  # type: ignore[assignment]
    QComboBox = QDialog = QDialogButtonBox = (  # type: ignore[assignment]
        QHBoxLayout
    ) = QLabel = QPlainTextEdit = QPushButton = QTextBrowser = QVBoxLayout = QWidget = (
        None
    )

from . import utils
from .errors import TutorError

_MODES = ("explain", "simplify", "example", "relate")

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
"""


class TutorPanel:
    """Chat panel wrapper; lazily builds the real QDialog when shown."""

    def __init__(self, card: Any) -> None:
        self.card = card
        self._dlg = None

    def show(self) -> None:
        if mw is None or QDialog is None:
            return
        self._build()
        self._dlg.exec()

    def _build(self) -> None:
        dlg = QDialog(mw)
        dlg.setWindowTitle("AnkiTutor — Ask a doubt")
        dlg.setMinimumSize(560, 500)
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
        mode_row.addWidget(self.mode_box)
        mode_row.addStretch(1)
        ask_btn = QPushButton("Ask")
        ask_btn.clicked.connect(self._on_ask)
        mode_row.addWidget(ask_btn)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("close-btn")
        close_btn.clicked.connect(dlg.reject)
        mode_row.addWidget(close_btn)
        layout.addLayout(mode_row)

        a_label = QLabel("Answer")
        layout.addWidget(a_label)

        self.output = QTextBrowser()
        self.output.setObjectName("answer-display")
        self.output.setPlaceholderText("The answer will appear here.")
        layout.addWidget(self.output)

        self._dlg = dlg

    def _on_ask(self) -> None:
        from . import tutor

        question = self.input.toPlainText()
        self.output.setPlainText("Thinking…")
        try:
            answer = tutor.ask(self.card, question, self.mode_box.currentText())
        except TutorError as exc:
            self.output.setPlainText(str(exc.user_message))
            return
        self.output.setPlainText(answer)
