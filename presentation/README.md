# ops-knowledge-loop — Presentation Package

5-minute manager walkthrough for the `ops-knowledge-loop` AI incident-triage pipeline,
built for **Ember Grid**.

**Source of truth:** `slides_content.md` — especially the 10-query results table and
featured terminal captures (Q1, Q3, Q6). HTML and PDF outputs are generated from that file.

---

## Before You Present — Fill in Two Placeholders

Every output reads from a single location. Search for these tokens and update them:

| File | Location | Token |
|------|----------|-------|
| `presentation.slides.html` | line ~12 | `const DEMO_DAYS = "[X days]"` |
| `presentation.slides.html` | line ~13 | `const DEMO_ROLE_NAME = "[Role Name]"` |
| `presentation.slides.vanilla.html` | line ~14 | `const DEMO_DAYS = "[X days]"` |
| `presentation.slides.vanilla.html` | line ~15 | `const DEMO_ROLE_NAME = "[Role Name]"` |
| `pdf/typst/presentation.typ` | line ~7 | `#let demo-days = "[X days]"` |
| `pdf/typst/presentation.typ` | line ~8 | `#let demo-role-name = "[Role Name]"` |
| `pdf/beamer/presentation.tex` | line ~12 | `\newcommand{\demodays}{[X days]}` |
| `pdf/beamer/presentation.tex` | line ~13 | `\newcommand{\demorole}{[Role Name]}` |

The placeholders appear as **amber-highlighted tokens** on the closing slide so they are visually obvious if you forget to fill them in before presenting.

---

## Deliverables

```
presentation/
├── presentation.slides.html          ← Reveal.js animated deck (recommended, needs internet first time)
├── presentation.slides.vanilla.html  ← Zero-dependency offline deck (double-click on Windows)
├── slides_content.md                 ← Canonical slide content reference
├── pdf/
│   ├── typst/presentation.typ        ← Typst source
│   └── beamer/presentation.tex       ← LaTeX Beamer source (fully dark projector style)
└── README.md
```

Generated PDFs are not currently checked into this workspace. Build them
from the sources above when needed.

---

## Opening the HTML Files on Windows

### `presentation.slides.html` (Reveal.js — recommended for live demo)

- **Requirements:** Modern browser (Edge 100+, Chrome, Firefox). Internet on first open to load Reveal.js from CDN (`cdn.jsdelivr.net`) and Google Fonts.
- **After first load:** Reveal.js is browser-cached. Subsequent opens work offline.
- **Double-click** the file to open, or drag it into your browser window.

Keyboard shortcuts:

| Key | Action |
|-----|--------|
| `→` / `Space` | Next slide |
| `←` | Previous slide |
| `ESC` | Slide overview |
| `F` | Fullscreen |
| `S` | Speaker notes view |
| `?` | Keyboard help overlay |
| `B` | Blackout screen |

### `presentation.slides.vanilla.html` (zero-dependency — fully offline)

- **Requirements:** Any browser. **No internet needed at any point.**
- Double-click to open. Works identically on Windows, Mac, Linux.

Keyboard shortcuts:

| Key | Action |
|-----|--------|
| `→` / `Space` / `PageDown` | Next slide / fragment |
| `←` / `Backspace` / `PageUp` | Previous slide / fragment |
| `Home` | First slide |
| `End` | Last slide |

Deep-link to a specific slide: append `#/4` to the URL (1-indexed).  
Touch/swipe navigation is also supported.

---

## PDF Files

| File | Description | Best for |
|------|-------------|----------|
| `pdf/presentation.typst.pdf` | Hybrid: dark covers + light content pages with dark terminal panels | Printing, sharing as document, screen reading |
| `pdf/presentation.reveal.pdf` | Exact snapshot of the Reveal.js deck | Sending to stakeholders who want the full dark deck |
| `pdf/presentation.beamer.pdf` | Fully dark LaTeX Beamer, projector-style | Conferences, projectors, maximum dark aesthetic |

These are generated outputs. If they are absent, rebuild the one you need
with the commands below.

---

## Rebuilding PDFs

### Typst

```bash
cd presentation/pdf/typst
typst compile presentation.typ ../presentation.typst.pdf
```

Install Typst if needed:
```bash
# Linux — download binary
curl -sL "https://github.com/typst/typst/releases/download/v0.12.0/typst-x86_64-unknown-linux-musl.tar.xz" \
  | tar -xJ --strip-components=1 -C ~/.local/bin/ --wildcards '*/typst'
```

### Reveal.js PDF (via decktape)

```bash
cd presentation
python3 -m http.server 8742 &
decktape \
  --chrome-arg=--no-sandbox \
  --chrome-arg=--disable-gpu \
  --size 1280x720 \
  reveal \
  "http://localhost:8742/presentation.slides.html" \
  "pdf/presentation.reveal.pdf"
kill %1
```

### LaTeX Beamer

**Option A — Tectonic** (auto-fetches packages, no full TeX install):

```bash
cd presentation/pdf/beamer
tectonic presentation.tex --outdir=..
mv ../presentation.pdf ../presentation.beamer.pdf
```

**Option B — XeLaTeX** (requires texlive):

```bash
# Install (once, requires sudo):
sudo apt-get install -y texlive-xetex texlive-fonts-extra texlive-latex-extra

cd presentation/pdf/beamer
xelatex -output-directory=../ presentation.tex
xelatex -output-directory=../ presentation.tex   # second pass resolves cross-refs
mv ../presentation.pdf ../presentation.beamer.pdf
```

On **Windows** install MiKTeX (<https://miktex.org>) and use `xelatex` from the MiKTeX console.

---

## Slide Structure (22 slides: 14 main + 8 appendix)

| # | Title | Speaker timing |
|---|-------|---------------|
| 1 | ops-knowledge-loop (Title) | ~30s |
| 2 | Prior Art | ~45s |
| 3 | The On-Call Problem | ~30s |
| 4 | How It Works (pipeline) | ~45s |
| 5 | What the RAG Searches | ~30s |
| 6 | Ops Dashboard | ~20s |
| 7 | 10 Queries · Live Run (HERO) | ~60s |
| 8 | Featured terminal output — Query 1 | ~20s |
| 9 | Featured terminal output — Query 3 | ~20s |
| 10 | Featured terminal output — Query 6 | ~20s |
| 11 | The Gate is the Point | ~45s |
| 12 | Observability | ~30s |
| 13 | Stack | ~20s |
| 14 | Where This Goes Next | ~30s |
| A0 | Appendix — Additional Terminal Outputs (divider) | optional |
| A1–A7 | Q2, Q4, Q5, Q7, Q8, Q9, Q10 terminal outputs | optional |

Core walkthrough: ~5 minutes. Appendix slides are at the very end for manager follow-up.

---

## Content Source of Truth

All slide text, the results table, and embedded terminal snippets live in `slides_content.md`.
If you need to update content, edit that file and then regenerate the output you want to use.
