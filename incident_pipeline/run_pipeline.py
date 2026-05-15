"""run_pipeline.py — end-to-end incident remediation pipeline for Ember Grid

Usage:
    python incident_pipeline/run_pipeline.py

Fetches open P1/P2 incidents, generates RAG-powered Rundeck recommendations,
executes above the confidence threshold, flags below for human review,
closes resolved incidents, and commits auto-generated runbooks.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rich.console import Console
from rich.table import Table

from incident_pipeline.ai_remediation import generate_remediation
from incident_pipeline.close_incident import close_incident
from incident_pipeline.fetch_incidents import fetch_open_incidents
from incident_pipeline.generate_runbook import generate_and_commit_runbook
from incident_pipeline.trigger_rundeck import trigger_job

console = Console()

PRIORITY_FILTER = os.getenv("PRIORITY_FILTER", "P1,P2")
INCIDENT_LIMIT = int(os.getenv("INCIDENT_LIMIT", "10"))
GENERATE_RUNBOOKS = os.getenv("GENERATE_RUNBOOKS", "true").lower() == "true"


def _top_rag_score(remediation: dict) -> str:
    """Return a printable RAG score (first source only) for the status table."""
    sources = remediation.get("rag_sources") or []
    if not sources:
        return "—"
    return Path(sources[0]).name


def _status_cell(status: str) -> str:
    """Colour-code the per-row pipeline status for rich output."""
    if status == "executed_closed":
        return "[green]Closed[/green]"
    if status == "pending_approval":
        return "[yellow]Pending Review[/yellow]"
    return "[red]Failed[/red]"


def _process_incident(incident: dict) -> dict:
    """Run a single incident through the full pipeline and return its row record."""
    number = incident["number"]
    console.rule(f"[bold]{number} — {incident['service']}[/bold]")

    remediation = generate_remediation(incident)
    console.log(
        f"Recommendation: [cyan]{remediation['job_name']}[/cyan] "
        f"confidence={remediation['confidence']:.2f} "
        f"via {remediation['llm_used']}"
    )

    execution = trigger_job(
        job_uuid=remediation["job_uuid"],
        confidence=remediation["confidence"],
        incident_number=number,
    )
    console.log(f"Rundeck: {execution['status']} — {execution['message']}")

    row_status = "failed"
    if execution["status"] == "executed":
        resolution_notes = (
            f"Auto-remediation via Rundeck job {remediation['job_name']!r}. "
            f"Confidence {remediation['confidence']:.2f}. {remediation['reasoning']}"
        )
        closed = close_incident(number, resolution_notes, execution["execution_id"])
        if closed:
            row_status = "executed_closed"
            if GENERATE_RUNBOOKS:
                try:
                    generate_and_commit_runbook(incident, resolution_notes)
                except Exception as exc:
                    console.log(f"[yellow]Runbook generation failed: {exc}[/yellow]")
    elif execution["status"] == "pending_approval":
        row_status = "pending_approval"

    return {
        "incident": number,
        "service": incident["service"],
        "priority": incident["priority"],
        "rag_score": f"{remediation['confidence']:.2f}",
        "rundeck_action": remediation["job_name"],
        "status": row_status,
    }


def _render_status_table(rows: list[dict]) -> None:
    """Print the final pipeline status table with colour coding."""
    table = Table(title="Ember Grid incident pipeline — run summary", header_style="bold cyan")
    table.add_column("Incident")
    table.add_column("Service")
    table.add_column("Priority", justify="center")
    table.add_column("RAG Score")
    table.add_column("Rundeck Action")
    table.add_column("Status")
    for row in rows:
        table.add_row(
            row["incident"],
            row["service"],
            row["priority"],
            row["rag_score"],
            row["rundeck_action"],
            _status_cell(row["status"]),
        )
    console.print(table)


def main() -> int:
    """End-to-end orchestration."""
    console.rule("[bold]ops-knowledge-loop pipeline run[/bold]")
    incidents = fetch_open_incidents(priority=PRIORITY_FILTER, limit=INCIDENT_LIMIT)
    if not incidents:
        console.print(f"[yellow]No open incidents in scope ({PRIORITY_FILTER}).[/yellow]")
        return 0

    rows = [_process_incident(inc) for inc in incidents]
    _render_status_table(rows)

    auto = sum(1 for r in rows if r["status"] == "executed_closed")
    pending = sum(1 for r in rows if r["status"] == "pending_approval")
    failed = sum(1 for r in rows if r["status"] == "failed")
    console.print(
        f"Pipeline complete: {auto} auto-resolved, {pending} pending human review, {failed} errors"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
