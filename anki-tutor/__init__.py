"""AnkiTutor — add-on entry point.

Registers an "Ask" button in the Reviewer and a Tools menu item to open the
chat panel and the configuration dialog. Imports of `gui`/`config` are lazy
so the module loads without dependencies that do not exist yet.
"""

from __future__ import annotations

try:
    from aqt import gui_hooks, mw
    from aqt.qt import QAction, QKeySequence, QShortcut
    from aqt.reviewer import Reviewer
    from aqt.webview import WebContent
except ImportError:
    # Outside Anki (e.g. tests/CI) the module must be importable without crashing.
    gui_hooks = mw = QAction = Reviewer = WebContent = None  # type: ignore[assignment]
    QKeySequence = QShortcut = None  # type: ignore[assignment]


def _current_card():
    """Card currently being reviewed, or None outside the Reviewer."""
    if mw is None or mw.reviewer is None:
        return None
    return mw.reviewer.card


def open_panel() -> None:
    """Open the chat panel with the current card's context."""
    from . import gui

    card = _current_card()
    if card is None:
        return
    panel = gui.TutorPanel(card=card)
    panel.show()


def open_config() -> None:
    """Open the add-on configuration dialog."""
    from . import config

    config.show_config_dialog()


def _inject_button(web_content: WebContent, context) -> None:
    if not isinstance(context, Reviewer):
        return
    from aqt.theme import theme_manager

    night = theme_manager.night_mode
    if night:
        bg = "#404040"
        fg = "#fcfcfc"
        border = "#202020"
        hover_bg = "#4a4a4a"
    else:
        bg = "#fcfcfc"
        fg = "#020202"
        border = "#c4c4c4"
        hover_bg = "#e8e8e8"
    web_content.body += f"""
<style>
#ankitutor-btn {{
    margin: 4px 6px;
    padding: 4px 10px;
    border: 1px solid {border};
    border-radius: 4px;
    background: {bg};
    color: {fg};
    font-weight: 600;
    cursor: pointer;
}}
#ankitutor-btn:hover {{ background: {hover_bg}; }}
</style>
<button id="ankitutor-btn" onclick="pycmd('ankitutor-btn')"
        title="Ask a doubt (Ctrl+Shift+T)">Ask AI</button>
"""


def _handle_js_message(handled, message, context):
    if message == "ankitutor-btn":
        open_panel()
        return (True, None)
    return handled


def open_support() -> None:
    """Open the support/donations dialog."""
    from . import support

    support.open_support()


def _setup_menu() -> None:
    action = QAction("AnkiTutor…", mw)
    action.triggered.connect(open_config)
    mw.form.menuTools.addAction(action)

    support_action = QAction("Support AnkiTutor…", mw)
    support_action.triggered.connect(open_support)
    mw.form.menuTools.addAction(support_action)


def _setup_shortcut() -> None:
    shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), mw)
    shortcut.activated.connect(open_panel)


def init() -> None:
    # Anki 23+ uses reviewer_did_render_bottom; Anki 25 renamed it to
    # webview_will_set_content. Register whichever is available.
    if hasattr(gui_hooks, "reviewer_did_render_bottom"):
        gui_hooks.reviewer_did_render_bottom.append(_inject_button)
    else:
        gui_hooks.webview_will_set_content.append(_inject_button)
    gui_hooks.webview_did_receive_js_message.append(_handle_js_message)
    _setup_menu()
    _setup_shortcut()


if mw is not None:
    init()
