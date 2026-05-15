# incident_pipeline — end-to-end RAG-powered remediation loop

This directory is the middle ring's main script: fetch → recommend →
execute → close → learn. Five focused modules plus the orchestrator. Every
external call (ServiceNow, Rundeck, Ollama, GitHub) goes through a
`MOCK_MODE` branch so the whole pipeline runs offline by default.

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Debug an end-to-end run | `run_pipeline.py` | `generate_runbook.py` | Top-down orchestration. |
| Investigate why a job was not triggered | `trigger_rundeck.py` | `close_incident.py` | Confidence gate logic lives here. |
| Investigate a wrong job recommendation | `ai_remediation.py` | `trigger_rundeck.py` | LLM prompt + rule-based fallback. |
| Investigate why a runbook was not auto-generated | `generate_runbook.py` | `fetch_incidents.py` | Ollama enrichment + git commit. |
| Change the incident filter | `fetch_incidents.py`, `run_pipeline.py` | — | Priority and limit are env-var driven. |
| Connect to real ServiceNow | `fetch_incidents.py`, `close_incident.py` | — | Set `MOCK_MODE=false` and populate `.env`. |
| Connect to real Rundeck | `trigger_rundeck.py` | — | Set `MOCK_MODE=false`; `RUNDECK_URL` + `RUNDECK_TOKEN`. |

## Entry Point

    python incident_pipeline/run_pipeline.py

## Inputs

- `mock_data/incidents.json` (via `fetch_incidents.py`) when `MOCK_MODE=true`.
- ServiceNow REST API when `MOCK_MODE=false`.
- `mock_data/rundeck_jobs.json` (job catalogue + risk thresholds).
- The persisted Chroma store via `rag/query.py`.
- Ollama on `OLLAMA_HOST` (default `http://localhost:11434`).

## Outputs

- Mock Rundeck execution IDs (logged with rich) or real Rundeck executions.
- Mock or real ServiceNow incident closures.
- New auto-generated runbook files under `knowledge-base/incidents/`,
  each one committed to git with `[knowledge-base] auto-generated runbook for INC...` messages.
- A final rich status table summarising the run.

## Demo Talking Point

"One script reads from ServiceNow, asks the local LLM 'what would the
runbook do here?', enforces a 70% confidence gate, executes through
Rundeck, closes the ticket, and writes the resolution back into the
knowledge base as a new runbook — the next incident in the same family
benefits from it within minutes."
