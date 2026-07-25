# ADR-009 — Donations & Funding

**Context:** AnkiTutor is open-source (MIT) and a portfolio piece. We want to accept voluntary financial support **without friction** and **without violating AnkiWeb rules** (which discourage pop-ups/nagging), while keeping personal data out of a public repository and package.

## Decision

### Channels (all external, international)

- **Ko-fi**
- **GitHub Sponsors**
- **Buy Me a Coffee**

Focus on global channels since the AnkiWeb audience is international.

### No Pix in repository/package

- **Do not** version QR Code or Pix key. Pix is BR-only and a static QR/key would permanently expose personal data in a public repo + AnkiWeb package.
- If Pix is ever added, keep it **outside** the package (e.g., on an external link/page), never in `assets/` in the add-on.

### Crypto / Web3 (optional, global)

- Accept **EVM-compatible** tokens (ETH, MATIC, USDC, USDT) at a single address, valid on **Ethereum, Polygon, Arbitrum, and Optimism**.
- **EVM address:** `0x370D0C7d3105677138C3719722239fB2A03dC9C8`
- Unlike Pix, a public EVM address **is not sensitive personal data** — it was designed to be shared; it can go in the repo/README and in a versioned QR.
- Generate a **QR Code** of the address (with a crypto symbol in the center) in `assets/` for the README.
- Always include the notice: *"Please double-check the address and network before sending."*

### In the add-on (opt-in, discreet)

- A **`Tools > Support AnkiTutor…`** menu item opens a native `QDialog` with the 3 channels.
- Buttons open the browser via `QDesktopServices.openUrl(QUrl(...))`.
- **Never opens automatically** — no pop-up after responses (avoids AnkiWeb review rejection and user annoyance).
- No payment data passes through the add-on; it only opens external URLs.

### On GitHub

- **`.github/FUNDING.yml`** activates the repository's "Sponsor" button.

### In README

- **"Support"** bilingual section (EN + PT-BR) with badges/links for the 3 channels plus a **"Support via Crypto (Web3)"** subsection (EVM address + QR).

## Alternatives

- **Auto pop-up after response:** higher conversion, but high risk of AnkiWeb rejection + user annoyance. Rejected.
- **Embedded Pix QR in the add-on (original Strategy 1):** UX without leaving Anki, but exposes personal data in repo/public package and is BR-only. Rejected.
- **Open Ko-fi directly from the menu (no QDialog):** simpler, but doesn't showcase all 3 channels. Deferred in favor of `QDialog`.

## Rationale

- **AnkiWeb compliance:** opt-in and discreet reduces risk in manual review.
- **Privacy:** no personal data in the repo; the add-on only opens URLs.
- **Reach:** international channels cover the global AnkiWeb audience.
- **Modularity:** isolated `support.py` maintains the project's pattern.

## Status

Accepted. Implement in **M5 — Publication & Portfolio**.
