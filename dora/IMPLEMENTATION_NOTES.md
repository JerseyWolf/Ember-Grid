# Implementation Notes — dora

## What Was Built

A single `metrics.py` module exposing `calculate_dora_metrics(days=30)`,
which returns headline values for MTTR, change failure rate, deployment
frequency and lead time plus a 30-point daily time series for each.
Trend labels (`improving` / `degrading` / `stable`) and week-over-week
deltas are derived from the series, not hardcoded.

## Key Design Decisions

- Decision: Mock series is a deterministic noisy linear progression
  from `start` to `end` over `days` samples — Reason: it produces a
  trend the dashboard can plot as a sparkline, and the `DORA_SEED` env
  var makes the dashboard reproducible across runs.
- Decision: Baselines live in a top-level `BASELINES` dict — Reason:
  one place to change the demo story (e.g. raise MTTR target from 2.1h
  to 1.8h) without touching any logic.
- Decision: `_fetch_real_metrics` raises `NotImplementedError` by
  design — Reason: lying about real-mode behaviour is worse than
  failing loudly. When the BigQuery DORA join is wired up, this is
  where it goes.

## How It Fits the Architecture

A read-only sidecar to the middle ring. It does not interact with
incidents or runbooks directly; it produces the numbers the dashboard
needs to show a manager whether the loop is working. The right way to
read it is: pipeline behaviour (incident_pipeline/) is the cause; DORA
metrics here are the effect.

## How to Extend

- To add a new data source: extend the `_fetch_real_metrics` branch to
  read from BigQuery / Dynatrace / Snowflake / whichever joins
  deployment events to incident records.
- To swap the LLM: this directory has nothing to change.

## Demo Talking Points

- "Four numbers, one chart per number, one trend label per number.
  The minimum a manager needs to see whether `ops-knowledge-loop` is
  working."
- "Deployment frequency is flat by design. If the loop made that
  number worse, it would have failed — making it better was never the
  goal."

## Known Limitations (Honest)

- The metrics are mock-only. A real pipeline implementing the BigQuery
  join over Harness deployment events × ServiceNow incident records
  is the obvious next step.
- No confidence intervals or anomaly flags. The trend labels are
  simple delta-based; a production-grade version would want
  statistical anomaly detection on each series.
