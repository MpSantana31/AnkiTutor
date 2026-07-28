"""Configuration dialog and helpers for AnkiTutor.

Reads/writes the add-on config through Anki's ``addonManager`` (ADR-004), so
the API key never lives in the repo. A ``QDialog`` lets the user set the
provider, API key, model and response language.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

try:
    from aqt import mw
    from aqt.qt import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTimer,
        QVBoxLayout,
    )
except ImportError:  # Outside Anki (tests/CI)
    mw = None  # type: ignore[assignment]
    QComboBox = QDialog = QDialogButtonBox = QFormLayout = (  # type: ignore[assignment]
        QLineEdit
    ) = QLabel = QVBoxLayout = QTimer = None

ADDON_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ADDON_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "language": "en",
    # API keys kept separate per provider so they are never mixed.
    "api_keys": {
        "openai": "",
        "openrouter": "",
        "opencode-zen": "",
        "opencode-go": "",
    },
}

PROVIDERS = ("openai", "openrouter", "opencode-zen", "opencode-go")
LANGUAGES = ("en", "pt-BR", "es", "fr", "de")

# Endpoints that list available models (used to populate the model combo live).
MODELS_ENDPOINT: dict[str, str] = {
    "openai": "https://api.openai.com/v1/models",
    "openrouter": "https://openrouter.ai/api/v1/models",
    "opencode-zen": "https://opencode.ai/zen/v1/models",
    "opencode-go": "https://opencode.ai/zen/go/v1/models",
}

# Local fallback catalogue per provider (used when the API is unreachable).
PROVIDER_MODELS: dict[str, tuple[str, ...]] = {
    "openai": (
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "o4-mini",
    ),
    "openrouter": (
        "openai/gpt-4.1",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/o4-mini",
        "openai/o3-mini",
        "anthropic/claude-sonnet-4",
        "anthropic/claude-3.5-haiku",
        "google/gemini-2.5-flash",
        "meta-llama/llama-4-maverick",
        "deepseek/deepseek-chat-v3-0324",
    ),
    "opencode-zen": ("claude-fable-5", "claude-opus-4-8"),
    "opencode-go": ("minimax-m3", "minimax-m2.7"),
}

DEFAULT_MODEL_FOR = {
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
    "opencode-zen": "claude-fable-5",
    "opencode-go": "minimax-m3",
}

MODELS_TIMEOUT = 10

__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_MODEL_FOR",
    "PROVIDER_MODELS",
    "PROVIDERS",
    "LANGUAGES",
    "fetch_models",
    "get_config",
    "show_config_dialog",
    "write_config",
]


def _load_default() -> dict[str, Any]:
    """Load defaults from ``config.json`` if present, else use hard-coded defaults."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return copy.deepcopy(DEFAULT_CONFIG)


# Anki manages config per add-on package name, not per module. This add-on's
# folder/package is "anki-tutor", so we use that literal id for get/write.
ADDON_NAME = "anki-tutor"


def get_config() -> dict[str, Any]:
    """Return the current config merged over defaults.

    Prefers Anki's managed config when running inside Anki; falls back to the
    local ``config.json`` (used in tests/CI) so the module stays usable.
    """
    defaults = _load_default()
    if mw is not None:
        managed = mw.addonManager.getConfig(ADDON_NAME)
        if managed:
            defaults.update(managed)
    return defaults


def write_config(config: dict[str, Any]) -> None:
    """Persist config via Anki's manager, or to ``config.json`` outside Anki."""
    if mw is not None:
        mw.addonManager.writeConfig(ADDON_NAME, config)
    else:
        CONFIG_PATH.write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def fetch_models(provider: str, api_key: str = "") -> tuple[str, ...]:
    """Fetch the live model list for ``provider`` from its API.

    Falls back to the local ``PROVIDER_MODELS`` catalogue on any error or when
    the network is unavailable, so the dialog never blocks the user.
    """
    url = MODELS_ENDPOINT.get(provider)
    if not url:
        return PROVIDER_MODELS.get(provider, ())

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        import requests
    except ImportError:
        return PROVIDER_MODELS.get(provider, ())

    try:
        resp = requests.get(url, headers=headers, timeout=MODELS_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ):
        return PROVIDER_MODELS.get(provider, ())

    models = _parse_models(provider, data)
    return tuple(models) if models else PROVIDER_MODELS.get(provider, ())


def _parse_models(provider: str, data: dict[str, Any]) -> list[str]:
    """Extract model ids from a provider's ``/models`` response."""
    if provider == "openrouter":
        return [m["id"] for m in data.get("data", []) if m.get("id")]

    raw = data.get("data", data.get("models", []))
    ids: list[str] = []
    for item in raw:
        mid = item.get("id") or item.get("name") if isinstance(item, dict) else None
        if mid:
            ids.append(mid)
    return ids


def show_config_dialog() -> None:
    """Open the configuration dialog. No-op outside Anki."""
    if mw is None or QDialog is None:
        return

    current = get_config()
    api_keys = dict(current.get("api_keys", {}) or {})
    dlg = QDialog(mw)
    dlg.setWindowTitle("AnkiTutor — Configuration")
    dlg.setMinimumWidth(420)

    layout = QVBoxLayout(dlg)
    form = QFormLayout()

    provider_box = QComboBox()
    provider_box.addItems(PROVIDERS)
    if current["provider"] in PROVIDERS:
        provider_box.setCurrentText(current["provider"])

    api_key_edit = QLineEdit(api_keys.get(provider_box.currentText(), ""))
    api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    api_key_edit.setPlaceholderText("sk-...")

    # When the provider changes, remember the edited key for the previous
    # provider and load the key stored for the newly selected one.
    def _on_provider_changed(new_provider: str) -> None:
        api_key_edit.setText(api_keys.get(new_provider, ""))
        _populate_models(new_provider)

    # Debounce timer for _on_key_edited: wait 500ms after the last keystroke
    # before calling _populate_models, so we don't fire a network request on
    # every character typed.
    _key_timer = QTimer()  # type: ignore[operator]
    _key_timer.setSingleShot(True)
    _key_timer.setInterval(500)

    def _on_key_edited(_: str) -> None:
        api_keys[provider_box.currentText()] = api_key_edit.text().strip()
        _key_timer.start()

    _key_timer.timeout.connect(lambda: _populate_models(provider_box.currentText()))

    model_box = QComboBox()

    def _populate_models(provider: str) -> None:
        models = fetch_models(provider, api_keys.get(provider, ""))
        if not models:
            models = PROVIDER_MODELS.get(
                provider, (DEFAULT_MODEL_FOR.get(provider, ""),)
            )
        model_box.clear()
        model_box.addItems(models)
        saved = current.get("model", "")
        if saved in models:
            model_box.setCurrentText(saved)
        elif DEFAULT_MODEL_FOR.get(provider):
            model_box.setCurrentText(DEFAULT_MODEL_FOR[provider])

    _populate_models(provider_box.currentText())
    provider_box.currentTextChanged.connect(_on_provider_changed)
    api_key_edit.textChanged.connect(_on_key_edited)

    refresh_btn = QPushButton("Refresh models")
    refresh_btn.clicked.connect(lambda: _populate_models(provider_box.currentText()))

    language_box = QComboBox()
    language_box.addItems(LANGUAGES)
    if current["language"] in LANGUAGES:
        language_box.setCurrentText(current["language"])

    form.addRow(QLabel("Provider"), provider_box)
    form.addRow(QLabel("API key"), api_key_edit)
    form.addRow(QLabel("Model"), model_box)
    form.addRow(QLabel(""), refresh_btn)
    form.addRow(QLabel("Response language"), language_box)
    layout.addLayout(form)

    hint = QLabel(
        "The card front/back is sent to the chosen provider's cloud API.\n"
        "API keys are stored separately per provider in Anki's config."
    )
    hint.setWordWrap(True)
    layout.addWidget(hint)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        # Persist the key edited for the active provider too.
        api_keys[provider_box.currentText()] = api_key_edit.text().strip()
        new_config = {
            "provider": provider_box.currentText(),
            "model": model_box.currentText(),
            "language": language_box.currentText(),
            "api_keys": api_keys,
        }
        write_config(new_config)
