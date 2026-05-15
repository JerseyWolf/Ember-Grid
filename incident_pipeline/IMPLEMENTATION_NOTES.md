# Implementation Notes — incident_pipeline

## What Was Built

Five focused modules plus an orchestrator:
`fetch_incidents.py` (ServiceNow → pipeline contract),
`ai_remediation.py` (RAG + Ollama → recommendation with confidence),
`trigger_rundeck.py` (confidence-gated execution),
`close_incident.py` (write resolution + execution_id back to
ServiceNow), `generate_runbook.py` (auto-runbook + git commit), and
`run_pipeline.py` (the end-to-end orchestrator). Each module has a
`MOCK_MODE` branch and never crashes the caller on external failure.

## Key Design Decisions

- Decision: Model: qwen3:14b (upgraded from qwen2.5-coder:7b).
  Configurable via OLLAMA_MODEL env var. Default chosen for RTX 4090
  (24GB VRAM, Q8_0 fits with headroom for KV cache).
- Decision: Confidence gate enforced *both* by a global 0.70 floor in
  `trigger_rundeck.py` AND a per-job `confidence_threshold` in
  `mock_data/rundeck_jobs.json` — Reason: the global floor is the line
  no operator wants to cross; the per-job threshold lets us raise the
  bar for high-risk operations (`rotate-service-credentials` at 0.85,
  `drain-and-cordon-node` at 0.90) without changing code. Policy as
  data.
- Decision: `trigger_manual_fulfilment_retry` is flagged
  `human_review_required: true` so it can never auto-execute, even at
  100% confidence — Reason: two historical duplicate-shipment incidents
  at Ember Grid. The rule is encoded in data, not buried in code.
- Decision: rule-based fallback in `ai_remediation.py` returns
  `confidence=0.65` (below the 0.70 floor) — Reason: when Ollama is
  unreachable, the system should never auto-execute. The fallback
  guarantees we still produce a recommendation but route it for human
  review by construction.
- Decision: `generate_runbook.py` runs `git add` and `git commit` itself
  — Reason: the demo's "self-improving loop" claim requires the new
  runbook to be a real git object the reviewer can see. Auto-committing
  is what makes the loop visible.

## How It Fits the Architecture

This is the middle ring. It reads from the inner ring (`rag/`), writes
to the inner ring (`knowledge-base/incidents/`), reads from the outer
ring (`mock_data/rundeck_jobs.json`, ServiceNow), and writes to the
outer ring (Rundeck executions, ServiceNow closures). It is the only
place where the loop's "intelligence" lives, and it is intentionally
small — five modules, each one easy to read in a single sitting.

## How to Extend

- To add a new data source (e.g. PagerDuty alongside ServiceNow): write
  `fetch_pagerduty.py` mirroring the `fetch_incidents.py` shape and
  union the lists in `run_pipeline.py`. Don't fold them into one file.
- To swap the LLM: change `OLLAMA_MODEL` env var. The prompt template
  in `ai_remediation.py` is model-agnostic. Anything Ollama can serve
  will work; rule-based fallback covers any failure.

## Demo Talking Points

- "Five Python files, one orchestrator. The whole pipeline is under
  ~700 lines including docstrings."
- "If Ollama is unreachable, the pipeline does not crash and does not
  silently misbehave — it routes everything for human review. That is
  the entire safety story."

## Known Limitations (Honest)

- The small LLM (`qwen2.5-coder:7b`) occasionally picks an off-target
  Rundeck job at confidence 0.85. The per-job `confidence_threshold`
  for high-risk jobs catches the dangerous cases, but a larger model
  would reduce the rate of wrong (but safe) auto-executions. Plug in
  `qwen2.5-coder:32b` or a comparable model to see this go away.
- `generate_runbook.py` makes one commit per resolved incident, which
  is good for traceability but noisy on the git log. A real deployment
  might prefer to batch them into a single hourly commit.
