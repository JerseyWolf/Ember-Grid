# dashboard — single-file HTML dashboard for the demo

This directory turns the data produced by `dora/` and the pipeline into
one self-contained `dashboard.html`. No frontend build, no server, no
external runtime dependencies beyond a Google Fonts link. The file opens
straight in any browser and is committed to the repository so a reviewer
can open it instantly.

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Regenerate the dashboard | `generate_dashboard.py` | `template.html` (read only when changing layout) | Idempotent — overwrites `dashboard.html`. |
| Change layout, colours or KPI cards | `template.html` | `generate_dashboard.py` | Pure HTML/CSS/JS; placeholders are `{{name}}`. |
| Adjust which incidents show in the run summary | `_pipeline_summary_rows` in `generate_dashboard.py` | template.html | Sort/limit logic lives in the renderer. |
| Wire up to live pipeline output | `generate_dashboard.py` | dora/metrics.py | Replace `_pipeline_summary_rows` with the pipeline's status table. |

## Entry Point

    python dashboard/generate_dashboard.py
    xdg-open dashboard/dashboard.html

## Inputs

- `dora.metrics.calculate_dora_metrics()`
- `rag.query.search_knowledge_base("recent incidents")`
- `mock_data/incidents.json`
- `template.html` (placeholder-driven layout)

## Outputs

- `dashboard.html` — a single self-contained file with inline CSS, inline
  SVG sparklines, and inline JS for the theme toggle and counter animation.

## Demo Talking Point

"The dashboard is the only artifact a manager needs to see — KPIs at the
top, the actual pipeline runs in the middle, and the closed-loop diagram
at the bottom showing exactly how the next incident gets cheaper."
