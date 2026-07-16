# Git Commands

Category-based `git add` / `git commit` reference. Short, English, conventional.

## Source modules

```bash
git add anki-tutor/*.py anki-tutor/providers/
git commit -m "feat: add AI tutor panel and chat GUI"
```

## Providers / config

```bash
git add anki-tutor/providers/ anki-tutor/config.py anki-tutor/config.schema.json anki-tutor/manifest.json
git commit -m "feat: add OpenRouter and OpenCode providers"
```

## Bug fix

```bash
git add anki-tutor/config.py
git commit -m "fix: persist config via package name"
```

## Refactor

```bash
git add anki-tutor/__init__.py
git commit -m "refactor: use QShortcut for ask shortcut"
```

## Tests

```bash
git add anki-tutor/tests/
git commit -m "test: add provider and tutor unit tests"
```

## Infra

```bash
git add .github/ pyproject.toml .gitignore
git commit -m "chore: ignore runtime config with API keys"
```
