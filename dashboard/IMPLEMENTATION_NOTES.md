# Implementation Notes — dashboard

## What Was Built

`generate_dashboard.py` reads from `dora/metrics.py`, `rag/query.py`
and `mock_data/incidents.json`, then renders `dashboard/template.html`
into a single self-contained `dashboard.html`. Inline CSS, inline SVG
sparklines, inline JS for the animated counters and the dark/light
toggle. Only external resource is the Google Fonts CDN link.

## Key Design Decisions

- Decision: `{{placeholder}}` string replacement instead of Jinja2 —
  Reason: the template has fewer than 20 placeholders and no real
  control flow; one dependency saved and one less moving piece. The
  `replace()` calls in `build_dashboard_html()` are obvious at a glance.
- Decision: Sparklines as inline SVG generated in Python — Reason: no
  charting library, no client-side data load, no flash of empty
  content. The SVG embeds the literal data points directly into the
  HTML so it works offline forever.
- Decision: The dashboard is committed as a generated artifact — Reason:
  the demo claim is "the dashboard opens in a browser without
  anything pre-installed". Committing the rendered HTML makes that
  literally true at clone time.

## How It Fits the Architecture

The visible surface of the whole system. Inner ring (RAG) status,
middle ring (pipeline) outcomes and DORA metrics are all surfaced here.
This is what a manager looks at; this is the manager-facing artifact
of the loop.

## How to Extend

- To add a new data source: import its reader at the top of
  `generate_dashboard.py`, add a placeholder in `template.html`,
  and add a `replace()` call in `build_dashboard_html()`. Keep both
  files small enough to read at one sitting.
- To swap the LLM: this directory has nothing to change. The dashboard
  renders whatever `rag/query.py` returns.

## Demo Talking Points

- "One self-contained HTML file. No frontend build, no server, no
  external runtime. It works on an air-gapped laptop."
- "The sparklines are inline SVG paths generated from the same
  `daily_series` data the API returns — what you see on the dashboard
  is exactly what the API returned, no transformations in the browser."

## Known Limitations (Honest)

- The dashboard is static — generated once, served as a file. There is
  no live refresh; re-running `generate_dashboard.py` is the way to
  update it. For the demo this is desirable (the file is shareable);
  for a live ops dashboard a small Flask wrapper around the same
  function would suffice.
- Animated counters and the theme toggle are intentionally tiny vanilla
  JS. Anything more interactive would justify a real frontend stack
  that this project deliberately avoids.
