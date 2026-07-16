"""Offline tests for ``config`` module (no Anki, no network)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent.parent


def _load_config_module(tmp_path: Path, monkeypatch):
    """Load ``config`` with an isolated ADDON_DIR for config.json writes."""
    spec = importlib.util.spec_from_file_location(
        "ankitutor_config", ADDON_DIR / "config.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ankitutor_config"] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ADDON_DIR", tmp_path)
    monkeypatch.setattr(module, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(module, "mw", None)
    return module


def test_default_config_shape(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    default = cfg._load_default()
    assert default["provider"] == "openai"
    assert default["model"] == "gpt-4o-mini"
    assert "api_keys" in default
    assert set(default["api_keys"]) == set(cfg.PROVIDERS)


def test_get_config_merges_defaults(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    config = cfg.get_config()
    assert config["language"] in cfg.LANGUAGES
    assert config["provider"] in cfg.PROVIDERS


def test_write_and_read_roundtrip(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    written = {
        "provider": "openrouter",
        "model": "gpt-4o",
        "language": "pt-BR",
        "api_keys": {
            "openrouter": "sk-test",
            "openai": "",
            "opencode-zen": "",
            "opencode-go": "",
        },
    }
    cfg.write_config(written)
    assert (tmp_path / "config.json").exists()
    assert cfg.get_config()["provider"] == "openrouter"
    assert cfg.get_config()["api_keys"]["openrouter"] == "sk-test"


def test_show_config_dialog_noop_without_anki(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    # Should not raise outside Anki.
    cfg.show_config_dialog()


def test_fetch_models_fallback_without_network(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    # No network / requests broken -> should fall back to local catalogue.
    models = cfg.fetch_models("openai", "")
    assert len(models) > 0
    assert "gpt-4o-mini" in models


def test_fetch_models_unknown_provider_returns_empty(monkeypatch, tmp_path):
    cfg = _load_config_module(tmp_path, monkeypatch)
    assert cfg.fetch_models("nonexistent", "") == ()


def test_write_and_read_via_anki_manager(monkeypatch, tmp_path):
    """Config must persist through Anki's addonManager using the package name."""
    cfg = _load_config_module(tmp_path, monkeypatch)
    store: dict[str, dict] = {}

    class FakeManager:
        def getConfig(self, name):
            return dict(store.get(name, {}))

        def writeConfig(self, name, data):
            store[name] = dict(data)

    class FakeMw:
        addonManager = FakeManager()

    fake_mw = FakeMw()
    monkeypatch.setattr(cfg, "mw", fake_mw)
    monkeypatch.setattr(cfg, "ADDON_NAME", "anki-tutor")

    written = {
        "provider": "openai",
        "model": "gpt-4o",
        "language": "pt-BR",
        "api_keys": {
            "openai": "sk-persist",
            "openrouter": "",
            "opencode-zen": "",
            "opencode-go": "",
        },
    }
    cfg.write_config(written)
    assert store["anki-tutor"]["api_keys"]["openai"] == "sk-persist"
    assert cfg.get_config()["api_keys"]["openai"] == "sk-persist"
    assert cfg.get_config()["provider"] == "openai"
