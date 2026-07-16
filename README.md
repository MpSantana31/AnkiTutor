# AnkiTutor

> AI tutor for your Anki cards — explain concepts and clarify doubts during
> review, using the card's own context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Demo

<!-- GIF: review a card → click "Ask" → AI answer -->

## Why?

Studying with Anki is repetition. AnkiTutor adds a layer of *comprehension*:
the AI explains the card based on what is on its front and back.

## Installation

- **AnkiWeb:** (link coming soon)
- **Manual:** clone this repo into `addons21/anki-tutor`:
  ```bash
  git clone https://github.com/MpSantana31/AnkiTutor.git \
    ~/Anki2/addons21/anki-tutor
  ```
- Set your API key in **Tools → AnkiTutor → Config**.

## Supported providers

| Provider   | Cloud? | Privacy                     |
|------------|--------|-----------------------------|
| OpenAI     | yes    | data leaves the machine     |
| OpenRouter | yes    | data leaves the machine     |
| OpenCode   | yes    | data leaves the machine (requires key + credits) |

## Architecture (overview)

- **Strategy + Factory** for LLM providers (`LLMProvider`).
- **Error Boundary** so Anki never crashes (`TutorError` + subclasses).
- **100% testable without network** (`FakeProvider` in tests).

## For developers

The addon lives in `anki-tutor/`. Quality is enforced by CI: `ruff`
(lint + format) and `pytest` with coverage. See the architecture and ADRs
in the repository.

## License

MIT — see [LICENSE](LICENSE).

---

# AnkiTutor (Português)

> Tutor de IA para seus cards do Anki — explique conceitos e tire dúvidas
> durante a revisão, com o contexto do próprio card.

## Demo

<!-- GIF: revisar card → clicar "Tirar dúvida" → resposta da IA -->

## Por que?

Estudar com Anki é repetir. O AnkiTutor adiciona uma camada de
*compreensão*: a IA explica o card com base no que está na frente e no verso.

## Instalação

- **AnkiWeb:** (link em breve)
- **Manual:** clone este repositório em `addons21/anki-tutor`:
  ```bash
  git clone https://github.com/MpSantana31/AnkiTutor.git \
    ~/Anki2/addons21/anki-tutor
  ```
- Configure sua API key em **Ferramentas → AnkiTutor → Config**.

## Provedores suportados

| Provedor  | Nuvem? | Privacidade                |
|-----------|--------|----------------------------|
| OpenAI    | sim    | dados saem da máquina      |
| OpenRouter| sim    | dados saem da máquina      |
| OpenCode  | sim    | dados saem da máquina (requer chave + créditos) |

## Arquitetura (resumo)

- **Strategy + Factory** para provedores de LLM (`LLMProvider`).
- **Error Boundary** para não crashear o Anki (`TutorError` + subclasses).
- **100% testável sem rede** (`FakeProvider` nos testes).

## Para devs

O addon vive em `anki-tutor/`. Qualidade é garantida por CI:
`ruff` (lint + format) e `pytest` com cobertura. Veja a arquitetura e os
ADRs no repositório.

## Licença

MIT — veja [LICENSE](LICENSE).
