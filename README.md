# AnkiTutor

> AI tutor for your Anki cards — explain concepts and clarify doubts during
> review, using the card's own context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Demo

![AnkiTutor demo](assets/demo.gif)

> Review a card → click **Ask AI** (or `Ctrl+Shift+T`) → type a question → watch the
> streamed, Markdown-rendered answer → **Save to note**.

## Why?

Studying with Anki is repetition. AnkiTutor adds a layer of *comprehension*:
the AI explains the card based on what is on its front and back.

## Installation

- **AnkiWeb:** (submitted — awaiting review)
- **Manual:** clone this repo into `addons21/anki-tutor`:
  ```bash
  git clone https://github.com/MpSantana31/AnkiTutor.git \
    ~/Anki2/addons21/anki-tutor
  ```
- Set your API key in **Tools → AnkiTutor → Config**.

## Supported providers

| Provider      | Cloud? | API key | Cost |
|---------------|--------|---------|------|
| OpenAI        | yes    | required | pay-per-use |
| OpenRouter    | yes    | required | pay-per-use |
| OpenCode Zen  | yes    | required | credits |
| OpenCode Go   | yes    | required | credits |

**Your data:** only the card's front and back text plus your question are sent
to the LLM provider. No personal info (deck names, review stats, etc.) is
transmitted. Your API key is stored locally by Anki and never committed to the
repository. The add-on makes no external calls besides the LLM provider API.

## Architecture (overview)

- **Strategy + Factory** for LLM providers (`LLMProvider`).
- **Error Boundary** so Anki never crashes (`TutorError` + subclasses).
- **100% testable without network** (`FakeProvider` in tests).

## Support / Apoie

If AnkiTutor helps your study, consider supporting its development.
Se o AnkiTutor te ajuda a estudar, considere apoiar o desenvolvimento.

[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/marcospsantana)
[![Sponsor](https://img.shields.io/badge/GitHub-Sponsor-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/MpSantana31)

### Support via Crypto (Web3)

If you prefer to support using cryptocurrencies, send EVM-compatible tokens to:
Se preferir apoiar com criptomoedas, envie tokens compatíveis com EVM para:

> **EVM Address (Ethereum, Polygon, Arbitrum, Optimism):**
> `0x370D0C7d3105677138C3719722239fB2A03dC9C8`

<img src="assets/crypto-qr.png" alt="EVM donation QR" width="200" />

*Please double-check the address and network before sending. / Confira o endereço e a rede antes de enviar.*

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

![AnkiTutor demo](assets/demo.gif)

> Revise um card → clique **Tirar dúvida** (ou `Ctrl+Shift+T`) → digite uma
> pergunta → veja a resposta em streaming renderizada em Markdown → **Salvar na nota**.

## Por que?

Estudar com Anki é repetir. O AnkiTutor adiciona uma camada de
*compreensão*: a IA explica o card com base no que está na frente e no verso.

## Instalação

- **AnkiWeb:** (submetido — aguardando revisão)
- **Manual:** clone este repositório em `addons21/anki-tutor`:
  ```bash
  git clone https://github.com/MpSantana31/AnkiTutor.git \
    ~/Anki2/addons21/anki-tutor
  ```
- Configure sua API key em **Ferramentas → AnkiTutor → Config**.

## Provedores suportados

| Provedor      | Nuvem? | API key | Custo |
|---------------|--------|---------|-------|
| OpenAI        | sim    | obrigatória | pay-per-use |
| OpenRouter    | sim    | obrigatória | pay-per-use |
| OpenCode Zen  | sim    | obrigatória | créditos |
| OpenCode Go   | sim    | obrigatória | créditos |

**Seus dados:** apenas o texto da frente e do verso do card mais sua pergunta
são enviados ao provedor de LLM. Nenhuma informação pessoal (nomes de baralho,
estatísticas de revisão, etc.) é transmitida. Sua chave de API é armazenada
localmente pelo Anki e nunca é versionada no repositório. O addon não faz
nenhuma chamada externa além da API do provedor de LLM.

## Arquitetura (resumo)

- **Strategy + Factory** para provedores de LLM (`LLMProvider`).
- **Error Boundary** para não crashear o Anki (`TutorError` + subclasses).
- **100% testável sem rede** (`FakeProvider` nos testes).

## Para devs

O addon vive em `anki-tutor/`. Qualidade é garantida por CI:
`ruff` (lint + format) e `pytest` com cobertura. Veja a arquitetura e os
ADRs no repositório.

## Support / Apoie

If AnkiTutor helps your study, consider supporting its development.
Se o AnkiTutor te ajuda a estudar, considere apoiar o desenvolvimento.

[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/marcospsantana)
[![Sponsor](https://img.shields.io/badge/GitHub-Sponsor-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/MpSantana31)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/<bmc_username>)

### Apoio via Cripto (Web3)

If you prefer to support using cryptocurrencies, send EVM-compatible tokens to:
Se preferir apoiar com criptomoedas, envie tokens compatíveis com EVM para:

> **EVM Address (Ethereum, Polygon, Arbitrum, Optimism):**
> `0x370D0C7d3105677138C3719722239fB2A03dC9C8`

<img src="assets/crypto-qr.png" alt="EVM donation QR" width="200" />

*Please double-check the address and network before sending. / Confira o endereço e a rede antes de enviar.*

## Licença

MIT — veja [LICENSE](LICENSE).
