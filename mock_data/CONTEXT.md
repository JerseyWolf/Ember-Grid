# mock_data — offline replicas of ServiceNow, Rundeck and incident sources

This directory is the test fabric that lets the entire `ops-knowledge-loop`
run end-to-end with no external credentials. Three files; one role each.
Every script with a `MOCK_MODE` branch reads from here when `MOCK_MODE=true`
(the default).

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Find an incident to demo against | `incidents.json` | rundeck_jobs.json | ~600 realistic Ember Grid incidents. **Pre-generated — never overwrite this file.** |
| Look up a Rundeck job catalogue entry | `rundeck_jobs.json` | incidents.json | 10 jobs covering every runbook's remediation steps. |
| Inspect raw ServiceNow API shape | `servicenow_responses.json` | rundeck_jobs.json | Matches the real ServiceNow table API envelope (result[], sys_id, etc). |
| Add a new Rundeck job | `rundeck_jobs.json` | — | Then reference the new job in the relevant runbook. |

## Entry Point

This directory is consumed, not run. The relevant entry points are in
`incident_pipeline/`:

    python incident_pipeline/run_pipeline.py

## Inputs

- None. These files are checked-in fixtures.

## Outputs

- `incidents.json`: consumed by `fetch_incidents.py` and the dashboard.
- `rundeck_jobs.json`: consumed by `ai_remediation.py` (rule-based fallback)
  and `trigger_rundeck.py` (duration + risk metadata).
- `servicenow_responses.json`: reference shape only. `fetch_incidents.py`
  uses `incidents.json` for the loop; this file exists to make the
  ServiceNow integration contract explicit for anyone reading the code.

## Demo Talking Point

"Everything in here mirrors the shape of the real upstream API. Flipping
`MOCK_MODE=false` does not change the pipeline code path — it changes the
data source, and that is the only difference."
