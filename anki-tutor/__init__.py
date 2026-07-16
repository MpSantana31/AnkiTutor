"""AnkiTutor — add-on entry point.

Registers an "Ask" button in the Reviewer and a Tools menu item to open the
chat panel and the configuration dialog. Imports of `gui`/`config` are lazy
so the module loads without dependencies that do not exist yet.
"""

from __future__ import annotations

try:
    from aqt import gui_hooks, mw
    from aqt.qt import QAction
    from aqt.reviewer import Reviewer
    from aqt.webview import WebContent
except ImportError:
    # Outside Anki (e.g. tests/CI) the module must be importable without crashing.
    gui_hooks = mw = QAction = Reviewer = WebContent = None  # type: ignore[assignment]


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
    web_content.body += (
        '<button id="ankitutor-btn" title="Ask a doubt (Ctrl+T)">Ask</button>'
    )


def _handle_js_message(handled, message, context):
    if message == "ankitutor-btn":
        open_panel()
        return (True, None)
    return handled


def _setup_menu() -> None:
    action = QAction("AnkiTutor…", mw)
    action.triggered.connect(open_config)
    mw.form.menuTools.addAction(action)  # Tools menu


def _setup_shortcut() -> None:
    from aqt import keyboard

    keyboard.addShortcut("Ctrl+T", open_panel)


def init() -> None:
    gui_hooks.reviewer_did_render_bottom.append(_inject_button)
    gui_hooks.webview_did_receive_js_message.append(_handle_js_message)
    _setup_menu()
    _setup_shortcut()


if mw is not None:
    init()
