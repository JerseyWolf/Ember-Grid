# Implementation Notes — knowledge-base

## What Was Built

Six handwritten Ember Grid runbooks (`checkout-service`, `payment-processor`,
`inventory-sync`, `store-pos-system`, `product-search`, `order-fulfilment`)
plus two systems-level documents (`ember-grid-architecture.md`,
`service-map.md`). The `incidents/` subdirectory receives auto-generated
runbooks produced by `incident_pipeline/generate_runbook.py` after every
resolved incident — three already exist from the first pipeline run.

## Key Design Decisions

- Decision: Same section structure for every handwritten runbook (Service
  Overview / Common Failure Modes / Diagnostic Steps / Remediation Steps /
  Escalation Path / Post-Incident Checklist) — Reason: chunked retrieval
  works much better when section headings are consistent; the LLM can
  cite "Remediation Steps from the X runbook" reliably.
- Decision: Auto-generated runbooks live in `incidents/`, separate from
  handwritten ones in `runbooks/` — Reason: lets us inspect provenance
  trivially with `git log -- knowledge-base/incidents/` and lets us
  rebuild the corpus from `runbooks/` alone if an auto-runbook turns out
  to be wrong.
- Decision: Reference Rundeck job names in backticks within Remediation
  Steps — Reason: gives the LLM a strong, well-bounded lexical signal
  to anchor against the job catalogue in `mock_data/rundeck_jobs.json`.

## How It Fits the Architecture

This directory is the inner ring. Nothing downstream works without it.
The middle ring (`rag/`) reads it and exposes semantic search. The
outer ring (Rundeck) acts on the recommendations grounded here.
Auto-runbooks close the loop: every incident the middle ring resolves
adds a new file here, and the next ingest cycle includes it.

## How to Extend

- To add a new data source: write a new `.md` file under
  `runbooks/` (or any subdirectory) matching the canonical section
  structure, then run `python rag/populate_database.py` to re-index.
- To swap the LLM: this directory has nothing to change — only the
  embedding model in `rag/populate_database.py` would change, and only
  if you wanted a different vectoriser. Generation-time models are
  decoupled and configured in `incident_pipeline/ai_remediation.py`.

## Demo Talking Points

- "Every runbook in `runbooks/` is something an actual Ember Grid on-call
  engineer would write — we did not generate them. Every runbook in
  `incidents/` is something the system wrote on its own after resolving
  a ticket."
- "The corpus is small on purpose. After 30 days of running the loop in
  production, `incidents/` would have hundreds of files and the RAG
  retrieval would be tuned to Ember Grid's actual failure patterns, not
  generic DevOps documentation."

## Known Limitations (Honest)

- Six handwritten runbooks is a starting set; the real Ember Grid estate
  has ~40 tier-0 services and would need a runbook per service before
  this is fully useful in production.
- The auto-runbook template is intentionally conservative; it does not
  yet ingest the actual Rundeck execution log into the runbook body.
  That would make the auto-generated content much more useful but
  requires the real Rundeck integration.
