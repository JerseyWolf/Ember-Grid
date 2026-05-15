# INDEX — Where Everything Lives in `ops-knowledge-loop` (Ember Grid)

This file is the front door for an engineer who has never seen the
project. Open it after [`README.md`](README.md), then follow the
pointers below to whichever part of the system you need.

If you only have 90 seconds, the order is:

1. [`README.md`](README.md) — the engineering proposal and the four-command demo.
2. This file (`INDEX.md`) — the map.
3. [`knowledge-base/systems/ember-grid-architecture.md`](knowledge-base/systems/ember-grid-architecture.md) — the platform topology.
4. The relevant per-folder `CONTEXT.md` (where to look, what to skip).
5. The matching per-folder `IMPLEMENTATION_NOTES.md` (design decisions, trade-offs, known limitations).

---

## Quick Start (offline-first, no credentials required)

```bash
git clone <repo>
pip install -r requirements.txt
python rag/populate_database.py && python incident_pipeline/run_pipeline.py
python dashboard/generate_dashboard.py && xdg-open dashboard/dashboard.html
```

Everything runs against `MOCK_MODE=true` by default. Ollama is optional;
if it's unavailable the pipeline degrades to a deterministic rule-based
fallback so no command crashes mid-demo.

---

## Directory Map

Every active subsystem ships with two markdown files:

- `CONTEXT.md` — the *routing table*: what to read, what to skip, entry
  points, inputs, outputs, one demo talking point.
- `IMPLEMENTATION_NOTES.md` — design decisions, how it fits the
  architecture, how to extend, demo talking points, known limitations.

| Directory | Purpose | Where to look | Design rationale |
|-----------|---------|---------------|------------------|
| [`dashboard/`](dashboard/) | One self-contained HTML dashboard for managers | [`CONTEXT.md`](dashboard/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](dashboard/IMPLEMENTATION_NOTES.md) |
| [`dora/`](dora/) | MTTR / change failure / deploy frequency / lead time metrics | [`CONTEXT.md`](dora/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](dora/IMPLEMENTATION_NOTES.md) |
| [`incident_pipeline/`](incident_pipeline/) | Fetch → recommend → gate → execute → close → learn | [`CONTEXT.md`](incident_pipeline/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](incident_pipeline/IMPLEMENTATION_NOTES.md) |
| [`knowledge-base/`](knowledge-base/) | Handwritten runbooks, systems docs, auto-generated incident notes | [`CONTEXT.md`](knowledge-base/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](knowledge-base/IMPLEMENTATION_NOTES.md) |
| [`mock_data/`](mock_data/) | Offline replicas of ServiceNow, Rundeck and incident sources | [`CONTEXT.md`](mock_data/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](mock_data/IMPLEMENTATION_NOTES.md) |
| [`policies/`](policies/) | OPA Rego rules enforced at PR time | [`CONTEXT.md`](policies/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](policies/IMPLEMENTATION_NOTES.md) |
| [`rag/`](rag/) | ChromaDB ingest + semantic search over the knowledge base | [`CONTEXT.md`](rag/CONTEXT.md) | [`IMPLEMENTATION_NOTES.md`](rag/IMPLEMENTATION_NOTES.md) |
| [`presentation/`](presentation/) | Manager walkthrough deck, PDFs, slide source | [`README.md`](presentation/README.md) | — |
| [`tests/`](tests/) | Pytest suite for the confidence gate | [`test_confidence_gate.py`](tests/test_confidence_gate.py) | — |
| [`chroma_db/`](chroma_db/) | Pre-built persistent vector store (committed, rebuildable) | — | See [`rag/IMPLEMENTATION_NOTES.md`](rag/IMPLEMENTATION_NOTES.md) for the "why we commit it" decision. |

---

## Top-Level Scripts

| Script | Purpose | When to use it |
|--------|---------|----------------|
| [`demo.py`](demo.py) | Three-segment screenshare demo: RAG retrieval → 2-incident pipeline → KB status | The live walkthrough. Pass `--open` to also regenerate and open the dashboard. |
| [`query_live.py`](query_live.py) | Free-text incident query CLI; runs RAG + LLM and prints the gate verdict | Ad-hoc "what would the loop do here?" exploration. Read-only; never modifies state. |
| [`run_demo_sequence.py`](run_demo_sequence.py) | Replays the canonical 10-query walkthrough, saves output to `demo_output.txt` | Reproducing the captured table in `presentation/slides_content.md`. Long-running (~5–7 min). |
| [`rag/populate_database.py`](rag/populate_database.py) | Rebuilds the ChromaDB store from every `.md` in `knowledge-base/` + `mock_data/incidents.json` | After editing any runbook or adding new incidents. Always safe to re-run. |
| [`rag/query.py`](rag/query.py) | One-shot CLI search; prints a rich table of the top-N matches | Sanity-checking the RAG index. |
| [`incident_pipeline/run_pipeline.py`](incident_pipeline/run_pipeline.py) | The end-to-end pipeline orchestrator | The "loop" itself. Env vars `INCIDENT_LIMIT`, `PRIORITY_FILTER`, `GENERATE_RUNBOOKS` shape the run. |
| [`dashboard/generate_dashboard.py`](dashboard/generate_dashboard.py) | Re-renders `dashboard/dashboard.html` | After any data change you want surfaced in the manager view. |
| [`dora/metrics.py`](dora/metrics.py) | Prints the four DORA headline numbers + trends | Standalone DORA inspection from the terminal. |

---

## Knowledge Base Layout

The `knowledge-base/` corpus is the inner ring of the architecture. Three
sibling directories, three different roles:

- [`knowledge-base/runbooks/`](knowledge-base/runbooks/) — handwritten,
  one file per tier-0 / tier-1 service, always the same section
  structure (Service Overview / Common Failure Modes / Diagnostic Steps
  / Remediation Steps / Escalation Path / Post-Incident Checklist).
  Editing one of these is the canonical way to teach the loop something.
- [`knowledge-base/systems/`](knowledge-base/systems/) — platform-level
  context that does not belong to any single service:
  [`ember-grid-architecture.md`](knowledge-base/systems/ember-grid-architecture.md)
  (cluster layout, CI/CD pipeline, observability stack) and
  [`service-map.md`](knowledge-base/systems/service-map.md) (the
  service-to-team-to-on-call mapping).
- [`knowledge-base/incidents/`](knowledge-base/incidents/) —
  auto-generated runbooks written by
  [`incident_pipeline/generate_runbook.py`](incident_pipeline/generate_runbook.py)
  after every resolved incident. This is what makes the loop
  "self-improving" — each one is committed to git, re-indexed by the
  next RAG ingest, and surfaced to the next matching query.

---

## Mock Mode vs Real Mode

Every external integration (ServiceNow, Rundeck, GitHub) has a
`MOCK_MODE` branch. The default is `MOCK_MODE=true` so the entire
pipeline runs offline with zero credentials.

- Flip to real mode by copying [`.env.example`](.env.example) to `.env`
  and setting `MOCK_MODE=false` plus the relevant credentials.
- The data shapes returned in mock mode match the real upstream APIs by
  design — see
  [`mock_data/IMPLEMENTATION_NOTES.md`](mock_data/IMPLEMENTATION_NOTES.md)
  for the "shape, not data, is the contract" rationale.
- Ollama is *always* local. Set `OLLAMA_HOST` and `OLLAMA_MODEL` to
  change which model is used; the prompt template is model-agnostic.

---

## Presentation Package

The canonical manager walkthrough lives entirely in `presentation/`:

- [`presentation/README.md`](presentation/README.md) — how to open the
  slide decks, how to rebuild PDFs from source, where the placeholders
  for "demo days" and "role name" are.
- [`presentation/slides_content.md`](presentation/slides_content.md) —
  the single source of truth for slide copy, the 10-query results table,
  and the three featured terminal captures (Q1, Q3, Q6).
- [`presentation/presentation.slides.html`](presentation/presentation.slides.html)
  — Reveal.js animated deck (recommended for live presenting).
- [`presentation/presentation.slides.vanilla.html`](presentation/presentation.slides.vanilla.html)
  — zero-dependency offline deck (double-click and go).

---

## Tests

- [`tests/test_confidence_gate.py`](tests/test_confidence_gate.py) — 14
  tests covering the global 0.70 confidence floor, per-job thresholds
  (`drain-and-cordon-node` at 0.90, `rotate-service-credentials` at
  0.85), the `human_review_required` flag (which blocks auto-execution
  at any confidence), and edge cases at 0.0 / 1.0.

Run the suite with:

```bash
python -m pytest tests/test_confidence_gate.py -v
```

---

## Where This Goes Next

The forward-looking roadmap is in the `SLIDE FUTURE` section of
[`presentation/slides_content.md`](presentation/slides_content.md) and
covers three extensions, each grounded in the current code:

- **Shadow Deployment Pipeline** — mirror live incidents without acting,
  promote to production once recommendations earn sufficient confidence.
- **Repository-Aware Context** — continuous indexing of service repos so
  the LLM has code-level context (config files, dependency changes,
  recent commits) when investigating root cause. Hook point:
  [`rag/populate_database.py`](rag/populate_database.py).
- **Living Organisational Memory** — automatic ingestion of JIRA,
  Confluence and equivalent KBs so the RAG corpus stays current with
  team decisions and post-mortems. Hook point:
  [`incident_pipeline/generate_runbook.py`](incident_pipeline/generate_runbook.py).

Section 8 of [`README.md`](README.md) ("Extension Points") covers the
nearer-term, single-PR hooks: Slack alerting, real ServiceNow, swapping
the LLM via `OLLAMA_MODEL`.

---

## Conventions a New Engineer Should Know

- **All external calls have `MOCK_MODE` branches.** The OPA PR check
  enforces this for any file under `incident_pipeline/` or `rag/` —
  see [`policies/pr_rules.rego`](policies/pr_rules.rego).
- **Commit messages** must match `[component] description — reasoning`
  (em-dash, not hyphen). Also enforced by OPA.
- **Runbook edits** require an `INC0000000`-style reference in the PR
  body. Same OPA rule file.
- **The vector store (`chroma_db/`) is committed to the repo.** Cloning
  the project gives you working semantic search after a single
  `pip install` — no separate index-build step.
- **`mock_data/incidents.json` is treated as read-only.** It's a
  pre-generated fixture; downstream code depends on its exact content.
