"""generate_dashboard.py — generate self-contained HTML dashboard

Usage:
    python dashboard/generate_dashboard.py            # write only

Writes dashboard/dashboard.html — a single file with all CSS and JS inline.
No external dependencies except Google Fonts CDN. Opens in any browser offline.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rich.console import Console

from dora.metrics import calculate_dora_metrics
from rag.query import search_knowledge_base

REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_FILE = REPO_ROOT / "mock_data" / "incidents.json"
KNOWLEDGE_BASE = REPO_ROOT / "knowledge-base"
CHROMA_DB_PATH = REPO_ROOT / "chroma_db"
OUTPUT_FILE = REPO_ROOT / "dashboard" / "dashboard.html"
DASHBOARD_TEMPLATE_PATH = Path(__file__).with_name("template.html")

CONFIDENCE_THRESHOLD = 0.70

console = Console()


def _load_incidents() -> list[dict]:
    """Read the seeded Ember Grid incidents fixture."""
    return json.loads(INCIDENTS_FILE.read_text(encoding="utf-8"))


def _pipeline_summary_rows(incidents: list[dict], limit: int = 10) -> list[dict]:
    """Pick the most recent incidents and project them for the table view."""
    sorted_incidents = sorted(
        incidents, key=lambda x: x.get("opened_at", ""), reverse=True
    )[:limit]
    rows: list[dict] = []
    for inc in sorted_incidents:
        state = inc.get("state", "")
        priority = inc.get("priority", "")
        if state == "closed":
            status = "Closed"
        elif state == "open" and priority in ("P1", "P2"):
            status = "Pending Review"
        elif state == "open":
            status = "Auto-Resolved"
        else:
            status = "Failed"
        rows.append(
            {
                "incident": inc.get("number", ""),
                "service": inc.get("service", ""),
                "priority": priority,
                "rag_score": f"{inc.get('mttr_minutes', 0)} min MTTR" if state == "closed" else "—",
                "rundeck_action": inc.get("rundeck_job_used") or "—",
                "status": status,
            }
        )
    return rows


def _confidence_distribution(incidents: list[dict]) -> dict:
    """Estimate the auto-resolved vs pending split from the incident corpus."""
    total = max(1, len([i for i in incidents if i.get("state") == "closed"]))
    pending = len([i for i in incidents if i.get("state") == "open"])
    auto_resolved = total
    grand_total = auto_resolved + pending
    if grand_total == 0:
        return {"auto": 0, "pending": 0, "auto_pct": 0.0, "pending_pct": 0.0}
    return {
        "auto": auto_resolved,
        "pending": pending,
        "auto_pct": round(auto_resolved / grand_total * 100, 1),
        "pending_pct": round(pending / grand_total * 100, 1),
    }


def _rag_status() -> dict:
    """Inspect the knowledge base directory for live RAG status metadata."""
    md_files = sorted(KNOWLEDGE_BASE.rglob("*.md")) if KNOWLEDGE_BASE.exists() else []
    if CHROMA_DB_PATH.exists():
        mtime = max((p.stat().st_mtime for p in CHROMA_DB_PATH.rglob("*") if p.is_file()), default=0)
        last_indexed = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds")
    else:
        last_indexed = "never"
    recent = sorted(md_files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    recent_names = [str(p.relative_to(REPO_ROOT)) for p in recent]
    return {
        "total_documents": len(md_files),
        "last_indexed": last_indexed,
        "recent_files": recent_names,
    }


def _sparkline_svg(series: list[float], colour: str) -> str:
    """Build an inline SVG path for a 30-point sparkline."""
    if not series:
        return ""
    width = 220
    height = 50
    pad = 4
    lo = min(series)
    hi = max(series)
    span = (hi - lo) or 1.0
    step = (width - 2 * pad) / max(1, len(series) - 1)
    points: list[str] = []
    for i, value in enumerate(series):
        x = pad + i * step
        y = height - pad - ((value - lo) / span) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" class="sparkline">'
        f'<polyline fill="none" stroke="{colour}" stroke-width="1.6" points="{polyline}"/>'
        f"</svg>"
    )


def _trend_arrow(direction: str) -> tuple[str, str]:
    """Map a trend label to (glyph, css class)."""
    if direction == "improving":
        return ("▲", "trend-up")
    if direction == "degrading":
        return ("▼", "trend-down")
    return ("→", "trend-flat")


def _rag_live_sources(query: str = "recent incidents") -> list[dict]:
    """Run a live RAG query so the dashboard proves the index is responsive."""
    try:
        return search_knowledge_base(query, n_results=3)
    except Exception as exc:
        console.log(f"[yellow]RAG live query skipped: {exc}[/yellow]")
        return []


def _format_kpi(metrics: dict) -> list[dict]:
    """Project DORA output into the per-card view model for templating."""
    spec = [
        ("MTTR", "mttr_hours", "hours", "{:.1f}"),
        ("Change Failure Rate", "change_failure_rate", "%", "{:.1f}"),
        ("Deployment Frequency", "deployment_frequency", "per day", "{:.1f}"),
        ("Lead Time", "lead_time_hours", "hours", "{:.1f}"),
    ]
    cards: list[dict] = []
    for label, key, unit, fmt in spec:
        value = metrics[key]
        trend = metrics["trends"][key]
        delta = metrics["week_delta"][key]
        glyph, css_class = _trend_arrow(trend)
        cards.append(
            {
                "label": label,
                "value": fmt.format(value),
                "value_raw": float(value),
                "unit": unit,
                "trend_glyph": glyph,
                "trend_class": css_class,
                "delta_pct": f"{delta:+.1f}%",
                "sparkline_svg": _sparkline_svg(metrics["daily_series"][key], "#4f98a3"),
            }
        )
    return cards


def _row_class(status: str) -> str:
    """Map a pipeline status to its CSS row class."""
    return {
        "Closed": "row-success",
        "Auto-Resolved": "row-success",
        "Pending Review": "row-pending",
        "Failed": "row-failed",
    }.get(status, "")


def _render_pipeline_rows(rows: list[dict]) -> str:
    """Emit the HTML <tr> elements for the pipeline summary table."""
    out: list[str] = []
    for row in rows:
        out.append(
            f'<tr class="{_row_class(row["status"])}">'
            f'<td>{html.escape(row["incident"])}</td>'
            f'<td>{html.escape(row["service"])}</td>'
            f'<td>{html.escape(row["priority"])}</td>'
            f'<td>{html.escape(row["rag_score"])}</td>'
            f'<td><code>{html.escape(row["rundeck_action"])}</code></td>'
            f'<td><span class="status-badge status-{row["status"].lower().replace(" ", "-")}">'
            f'{html.escape(row["status"])}</span></td>'
            "</tr>"
        )
    return "\n".join(out)


def _render_kpi_cards(cards: list[dict]) -> str:
    """Emit the HTML for the four DORA KPI cards."""
    parts: list[str] = []
    for card in cards:
        parts.append(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{html.escape(card["label"])}</div>'
            f'<div class="kpi-value" data-target="{card["value_raw"]:.2f}">{html.escape(card["value"])}</div>'
            f'<div class="kpi-unit">{html.escape(card["unit"])}</div>'
            f'<div class="kpi-meta"><span class="trend {card["trend_class"]}">{card["trend_glyph"]}</span>'
            f' <span class="delta">{html.escape(card["delta_pct"])} vs last week</span></div>'
            f'<div class="sparkline-wrap">{card["sparkline_svg"]}</div>'
            f"</div>"
        )
    return "\n".join(parts)


def _render_rag_recent(items: list[str]) -> str:
    """Format the 'last indexed files' bullets in the RAG card."""
    if not items:
        return "<li>No documents indexed.</li>"
    return "\n".join(f"<li><code>{html.escape(item)}</code></li>" for item in items)


def _render_rag_live(items: list[dict]) -> str:
    """Format the live RAG sample results shown in the RAG card."""
    if not items:
        return '<p class="muted">RAG live query unavailable.</p>'
    parts = ["<ul class='rag-live'>"]
    for item in items:
        snippet = (item["text"] or "").replace("\n", " ").strip()
        if len(snippet) > 140:
            snippet = snippet[:140] + "…"
        parts.append(
            f'<li><code>{html.escape(item["source"])}</code> '
            f'<span class="muted">(score {item["score"]:.2f})</span><br>'
            f'<span class="snippet">{html.escape(snippet)}</span></li>'
        )
    parts.append("</ul>")
    return "\n".join(parts)


def build_dashboard_html() -> str:
    """Assemble the entire dashboard.html string."""
    metrics = calculate_dora_metrics()
    incidents = _load_incidents()
    pipeline_rows = _pipeline_summary_rows(incidents)
    rag = _rag_status()
    rag_live = _rag_live_sources()
    distribution = _confidence_distribution(incidents)
    cards = _format_kpi(metrics)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    template = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template
        .replace("{{generated_at}}", html.escape(generated_at))
        .replace("{{kpi_cards}}", _render_kpi_cards(cards))
        .replace("{{pipeline_rows}}", _render_pipeline_rows(pipeline_rows))
        .replace("{{rag_total}}", str(rag["total_documents"]))
        .replace("{{rag_last_indexed}}", html.escape(rag["last_indexed"]))
        .replace("{{rag_recent}}", _render_rag_recent(rag["recent_files"]))
        .replace("{{rag_live}}", _render_rag_live(rag_live))
        .replace("{{dist_auto}}", str(distribution["auto"]))
        .replace("{{dist_pending}}", str(distribution["pending"]))
        .replace("{{dist_auto_pct}}", f'{distribution["auto_pct"]:.1f}')
        .replace("{{dist_pending_pct}}", f'{distribution["pending_pct"]:.1f}')
        .replace("{{confidence_threshold}}", str(int(CONFIDENCE_THRESHOLD * 100)))
    )


def main() -> int:
    """Entry point: render and write dashboard.html."""
    if not DASHBOARD_TEMPLATE_PATH.exists():
        console.print(f"[red]Template not found: {DASHBOARD_TEMPLATE_PATH}[/red]")
        return 1
    rendered = build_dashboard_html()
    OUTPUT_FILE.write_text(rendered, encoding="utf-8")
    console.print(f"[green]✓[/green] Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
