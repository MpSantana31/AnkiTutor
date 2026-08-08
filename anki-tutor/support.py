"""Support dialog (ADR-009 — Donations & Funding).

Opt-in, discreet — accessible via ``Tools > Support AnkiTutor…``. Opens a
native ``QDialog`` with donation channels; each button opens the browser via
``QDesktopServices.openUrl``. Never pops up automatically.
"""

from __future__ import annotations

try:
    from aqt import mw
    from aqt.qt import (
        QDesktopServices,
        QDialog,
        QLabel,
        QPushButton,
        QUrl,
        QVBoxLayout,
    )
except ImportError:
    mw = None  # type: ignore[assignment]
    QDesktopServices = QDialog = QLabel = None  # type: ignore[assignment]
    QPushButton = QVBoxLayout = QUrl = None  # type: ignore[assignment]

# GitHub and Ko-fi usernames are already set per ADR-009.
KOFI_URL = "https://ko-fi.com/marcospsantana"
GH_SPONSORS_URL = "https://github.com/sponsors/MpSantana31"

__all__ = ["open_support"]


def open_support() -> None:
    """Show the native support dialog. No-op outside Anki."""
    if mw is None or QDialog is None:
        return

    dlg = QDialog(mw)
    dlg.setWindowTitle("Support AnkiTutor")
    dlg.setMinimumWidth(380)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    thanks = QLabel(
        "Thanks for using AnkiTutor!\n"
        "Obrigado por usar o AnkiTutor!\n\n"
        "Your support helps keep this project independent and evolving.\n"
        "Seu apoio ajuda a manter este projeto independente e em evolução."
    )
    thanks.setWordWrap(True)
    layout.addWidget(thanks)

    for label_text, url in [
        ("☕ Ko-fi", KOFI_URL),
        ("💜 GitHub Sponsors", GH_SPONSORS_URL),
    ]:
        btn = QPushButton(label_text)
        btn.clicked.connect(lambda _ignored, u=url: QDesktopServices.openUrl(QUrl(u)))
        layout.addWidget(btn)

    dlg.exec()
