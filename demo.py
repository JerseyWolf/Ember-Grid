"""demo.py — optional live demo runner for ops-knowledge-loop (Ember Grid)

The saved 10-query results in presentation/slides_content.md are the
primary walkthrough artefact. Use this script only if you need a live replay.

Usage:
    python demo.py            # run the three demo segments and print next-step hint
    python demo.py --open     # also generate-then-open the dashboard at the end

Three short segments designed for a screen-share:
  1. RAG retrieval over the Ember Grid runbooks.
  2. The confidence-gated incident pipeline, scoped to the first 2 incidents.
  3. Knowledge-base status + a one-line "next step" pointer to the dashboard.

Total runtime targets under 30 seconds. Every external call (Ollama, RAG,
ServiceNow, Rundeck) is wrapped so the demo never crashes mid-screen-share.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ.setdefault("MOCK_MODE", "true")
os.environ.setdefault("OLLAMA_MODEL", "qwen3:14b")
os.environ["INCIDENT_LIMIT"] = "2"
os.environ["GENERATE_RUNBOOKS"] = "false"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from incident_pipeline.run_pipeline import main as run_pipeline_main
from rag.query import search_knowledge_base

console = Console()
KB_DIR = REPO_ROOT / "knowledge-base"
INCIDENTS_DIR = KB_DIR / "incidents"
DASHBOARD_FILE = REPO_ROOT / "dashboard" / "dashboard.html"
RAG_QUERY = "checkout service OOM kill"


def open_in_browser(filepath: str) -> None:
    """Open a file in the default browser, cross-platform."""
    abs_path = os.path.abspath(filepath)
    if sys.platform == "win32":
        os.startfile(abs_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", abs_path])
    else:
        subprocess.run(["xdg-open", abs_path])


def _print_header() -> None:
    """Print the dramatic green banner that opens the demo."""
    title = "  ops-knowledge-loop — Ember Grid  "
    console.print()
    console.print(Panel.fit(title, style="bold green", border_style="green"))


def _render_rag_results(results: list[dict]) -> None:
    """Render the top-N RAG results as a compact rich table."""
    table = Table(header_style="bold cyan", show_lines=False)
    table.add_column("#", justify="right", width=2)
    table.add_column("Source", overflow="fold")
    table.add_column("Service")
    table.add_column("Score", justify="right")
    table.add_column("Preview", overflow="fold")
    for i, item in enumerate(results, start=1):
        preview = item["text"].replace("\n", " ").strip()
        if len(preview) > 140:
            preview = preview[:140] + "…"
        table.add_row(
            str(i),
            item["source"],
            item["service"],
            f"{item['score']:.3f}",
            preview,
        )
    console.print(table)


def _rag_demo() -> None:
    """Show that RAG retrieval is live and grounded in the runbooks."""
    console.print("\n[bold cyan]RAG retrieval — 3 most relevant runbook chunks:[/bold cyan]")
    console.print(f"[dim]$ python rag/query.py {RAG_QUERY!r}[/dim]")
    try:
        results = search_knowledge_base(RAG_QUERY, n_results=3)
    except Exception as exc:
        console.print(f"[yellow]RAG unavailable — {exc}[/yellow]")
        return
    if results:
        _render_rag_results(results)
    else:
        console.print("[yellow]RAG returned no results.[/yellow]")


def _pipeline_demo() -> None:
    """Show the confidence-gated pipeline running end-to-end on two incidents."""
    console.print("\n[bold cyan]Incident pipeline — 2 incidents processed:[/bold cyan]")
    console.print("[dim]$ INCIDENT_LIMIT=2 python incident_pipeline/run_pipeline.py[/dim]")
    try:
        run_pipeline_main()
    except Exception as exc:
        console.print(f"[yellow]Pipeline encountered an issue — {exc}[/yellow]")


def _kb_status() -> None:
    """Print the knowledge-base totals + the latest auto-generated runbook."""
    md_files = list(KB_DIR.rglob("*.md")) if KB_DIR.exists() else []
    incident_files = (
        sorted(INCIDENTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if INCIDENTS_DIR.exists() else []
    )
    last = incident_files[0].name if incident_files else "(none yet)"
    console.print()
    console.print(
        f"[bold]Knowledge base:[/bold] {len(md_files)} documents indexed. "
        f"Last runbook committed: [cyan]{last}[/cyan]"
    )


def _next_step() -> None:
    """Direct the viewer to the dashboard for the full picture."""
    console.print(
        "[bold]Full dashboard:[/bold] python dashboard/generate_dashboard.py"
    )


def _open_dashboard() -> None:
    """Regenerate the dashboard and open it in the default browser."""
    try:
        from dashboard.generate_dashboard import main as generate_dashboard_main
        generate_dashboard_main()
    except Exception as exc:
        console.print(f"[yellow]Dashboard regeneration skipped: {exc}[/yellow]")
    if not DASHBOARD_FILE.exists():
        console.print(f"[yellow]No dashboard file at {DASHBOARD_FILE} — skipping open.[/yellow]")
        return
    try:
        open_in_browser(str(DASHBOARD_FILE))
        console.print(f"[green]✓[/green] Opened {DASHBOARD_FILE.name} in default browser")
    except Exception as exc:
        console.print(f"[yellow]Could not open browser automatically: {exc}[/yellow]")


def main() -> int:
    """Run the three demo segments in order, never crashing the caller."""
    started = time.perf_counter()
    should_open = "--open" in sys.argv[1:]
    try:
        _print_header()
        _rag_demo()
        time.sleep(1)
        _pipeline_demo()
        _kb_status()
        _next_step()
        if should_open:
            _open_dashboard()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")
        return 130
    elapsed = time.perf_counter() - started
    console.print(f"[dim](demo runtime {elapsed:.1f}s)[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
