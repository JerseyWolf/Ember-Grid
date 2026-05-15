# ops-knowledge-loop — Engineering Proposal

**Ember Grid** · portfolio codebase and presentation package.

A self-improving RAG-powered incident remediation loop for Ember Grid's
DevOps platform. The canonical walkthrough evidence is
`presentation/slides_content.md` (10 live queries with captured results).
This repository is maintained for review and slides; runtime execution is
optional.

## 1. Problem

Ember Grid operates ~850 microservices across four GKE regions, ~40 of
them business-critical. During peak trading events the incident volume
climbs by 4–6x, but the resolution knowledge — which Rundeck job, which
namespace, which escalation path — lives in the heads of perhaps two
dozen on-call engineers. Generic LLM assistants do not know that
`payment-processor` is PCI-scoped, that `order-fulfilment` retries can
cause duplicate physical shipments, or that an `inventory-sync` job
exiting `0` with zero records written is the single most expensive
failure mode on the estate. DORA metrics are computed nightly but rarely
read by managers, and there is no closed feedback loop from a resolved
incident back into the system's future behaviour. Every incident is a
fresh investigation.

## 2. The Solution

`ops-knowledge-loop` is a closed loop. ServiceNow is the system of
record for incidents. A Python pipeline fetches open P1/P2 incidents,
asks a local LLM (Ollama, on-prem, zero per-request cost) "what would
the Ember Grid runbook do here?" — grounded by a ChromaDB index of our
actual runbooks — and produces a Rundeck job recommendation with a
confidence score. Above the global 70% floor, and any stricter per-job
thresholds, the job can run automatically and the incident is closed in
ServiceNow; below threshold or when a job requires review, it is flagged
with the full RAG context and LLM reasoning attached. Every closed
incident can generate a new runbook under `knowledge-base/incidents/`;
the pipeline attempts to commit it and the next RAG rebuild makes it
searchable. The next incident in the same family is cheaper than the
last. Copilot governance and OPA policies apply to the configured
Ember Grid repo fleet so the rules survive team rotation.

       ┌──────────────────────────────────────────────────────────┐
       │            OUTER RING — Governance + Execution           │
       │   Rundeck (audited) · OPA policies · Copilot rules       │
       │   ┌──────────────────────────────────────────────────┐   │
       │   │        MIDDLE RING — Python intelligence         │   │
       │   │   fetch · recommend · gate · execute · close     │   │
       │   │   ┌──────────────────────────────────────────┐   │   │
       │   │   │         INNER RING — Knowledge base      │   │   │
       │   │   │   Runbooks + auto-runbooks (ChromaDB)    │   │   │
       │   │   └──────────────────────────────────────────┘   │   │
       │   └──────────────────────────────────────────────────┘   │
       └──────────────────────────────────────────────────────────┘

## 3. DORA Impact

| Metric                | Before | Target (90 days) | How                            |
|-----------------------|--------|------------------|--------------------------------|
| MTTR                  | 3.8h   | 2.1h             | RAG surfaces resolution in 8s  |
| Change Failure Rate   | 11.4%  | 7%               | Pre-deployment health gate     |
| Deployment Frequency  | 4.2/d  | 4.2/d            | Maintained, not degraded       |
| Lead Time             | 17.6h  | 12h              | Automated runbook generation   |

The baseline numbers are Ember Grid's current actuals; the targets are
what the loop is designed to deliver in the first 90 days of operation.
Deployment frequency is deliberately not the metric we are trying to
improve — making it worse would be the only way `ops-knowledge-loop`
could hurt the team.

## 4. Quick Demo (exactly 4 commands, must work after git clone)

    git clone <repo>
    pip install -r requirements.txt
    python rag/populate_database.py && python incident_pipeline/run_pipeline.py
    python dashboard/generate_dashboard.py && xdg-open dashboard/dashboard.html

Everything is offline-first via `MOCK_MODE=true` (the default). No
credentials are required for the demo. The dashboard is a single
self-contained HTML file with inline CSS and JS.

Useful follow-up commands:

    python demo.py --open
    python query_live.py "checkout service throwing OOM kills under load"
    python run_demo_sequence.py
    python -m pytest tests/test_confidence_gate.py

## 5. How It Grows

The loop is self-improving by construction. Every resolved incident
produces a new markdown runbook in `knowledge-base/incidents/` that is
written with a best-effort git commit and re-indexed by
`rag/populate_database.py`. This checkout currently contains six
handwritten runbooks, four generated incident runbooks and an expanded
600-incident mock fixture. After 90 days of operation, the RAG retrieval
accuracy improves measurably because the corpus reflects Ember Grid's
actual failure patterns, not generic DevOps documentation. The system
gets cheaper to operate the longer it runs.

## 6. The Confidence Gate

The system never executes autonomously below 70% confidence. Below
threshold, the incident is flagged in the pipeline output with the full
RAG context and LLM reasoning attached, giving the on-call engineer
everything they need to make the decision in under 60 seconds instead
of 20 minutes. Riskier jobs such as `rotate-service-credentials` and
`drain-and-cordon-node` have higher confidence floors of 0.85 and 0.90
in `mock_data/rundeck_jobs.json`. The duplicate-shipment-risk job
`trigger-manual-fulfilment-retry` is explicitly flagged
`human_review_required: true` so it can never run without a person in
the loop. The gate is enforced in code
(`incident_pipeline/trigger_rundeck.py`) and the policy is enforced in
data (`mock_data/rundeck_jobs.json`).

## 7. Tech Stack

| Tool                   | Role                             | Why This Tool                                  |
|------------------------|----------------------------------|------------------------------------------------|
| ChromaDB               | Vector store                     | Embedded, no server, rebuilt locally from fixtures |
| sentence-transformers  | Embeddings                       | Offline, no API key, accurate for ops text     |
| Ollama + Qwen3/Qwen2.5 | Local LLM inference              | Configurable via `OLLAMA_MODEL`, data stays on-prem |
| ServiceNow             | Incident source + close loop     | Already the system of record                   |
| Rundeck                | Job execution with audit log     | RBAC, scheduling, ServiceNow plugin native     |
| OPA                    | PR policy enforcement            | Policy-as-code, runs in GitHub Actions         |
| rich                   | Terminal output                  | Readable pipeline status for on-call           |

## 8. Extension Points

- **To add Slack alerting:** add a `notify_slack()` call in
  `incident_pipeline/run_pipeline.py` after `trigger_job()`. The
  function should take the row dict and post to a webhook from
  `os.getenv("SLACK_WEBHOOK_URL")`. One commit, one screen of code.
- **To connect to real ServiceNow:** set `MOCK_MODE=false` and
  populate `.env` from `.env.example`. The code paths under
  `MOCK_MODE=false` in `fetch_incidents.py` and `close_incident.py` are
  already written against the real ServiceNow table API.
- **To use a different LLM:** change `OLLAMA_MODEL` env var. The prompt
  template in `incident_pipeline/ai_remediation.py` is model-agnostic.
  The recommendation path currently defaults to `qwen3:14b`; the
  runbook-enrichment path has its own default in
  `incident_pipeline/generate_runbook.py`. The rule-based fallback
  keeps the pipeline alive if Ollama is unavailable.
