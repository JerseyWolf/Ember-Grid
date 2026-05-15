# dora — DORA metrics calculation

This directory owns the four DORA metrics for Ember Grid (MTTR, change
failure rate, deployment frequency, lead time) plus the supporting daily
time-series the dashboard renders. Single module today; place for the
BigQuery join when `MOCK_MODE=false` is wired up.

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Inspect the headline DORA numbers | `metrics.py` (function `calculate_dora_metrics`) | — | Returns a single dict. |
| Tune the demo baseline (start/end) | `BASELINES` dict in `metrics.py` | — | Change one number; the trend story updates. |
| Connect to real BigQuery | `_fetch_real_metrics` in `metrics.py` | — | Currently raises NotImplementedError by design. |
| Render the metrics on the dashboard | `dashboard/generate_dashboard.py` | — | Imports `calculate_dora_metrics`. |

## Entry Point

    python dora/metrics.py     # CLI summary table

## Inputs

- `MOCK_MODE` env var (default `true`).
- `DORA_SEED` env var (default `42`) — deterministic mock series.

## Outputs

- Dict with headline values, trend labels, per-week deltas and 30-point
  daily series. Used by `dashboard/generate_dashboard.py`.

## Demo Talking Point

"This is the manager view: every metric is plotted alongside its trend
and a sparkline, so a non-engineer can see the impact of the loop after
30 days at a glance."
