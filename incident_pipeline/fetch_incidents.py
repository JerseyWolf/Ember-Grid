"""fetch_incidents.py — pull open Ember Grid incidents from ServiceNow

Usage (import):
    from incident_pipeline.fetch_incidents import fetch_open_incidents
    incidents = fetch_open_incidents(priority="P1,P2", limit=10)

Usage (CLI):
    python incident_pipeline/fetch_incidents.py

MOCK_MODE=true (default): reads mock_data/incidents.json.
MOCK_MODE=false:          calls the ServiceNow table API.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_FILE = REPO_ROOT / "mock_data" / "incidents.json"

console = Console()


def _load_mock_incidents() -> list[dict]:
    """Read the pre-seeded Ember Grid incidents fixture."""
    if not INCIDENTS_FILE.exists():
        raise FileNotFoundError(f"Mock incidents file not found: {INCIDENTS_FILE}")
    return json.loads(INCIDENTS_FILE.read_text(encoding="utf-8"))


def _project_incident(record: dict) -> dict:
    """Reshape an incident record to the pipeline's canonical contract."""
    return {
        "number": record.get("number", ""),
        "short_description": record.get("short_description", ""),
        "priority": record.get("priority", ""),
        "service": record.get("service", ""),
        "namespace": record.get("namespace", ""),
        "opened_at": record.get("opened_at", ""),
        "state": record.get("state", ""),
        "description": record.get("description", ""),
        "tags": list(record.get("tags", [])),
    }


def _fetch_real_incidents(priority: str, limit: int) -> list[dict]:
    """Query the real ServiceNow table API using env-var credentials."""
    url = os.environ["SERVICENOW_URL"].rstrip("/") + "/api/now/table/incident"
    user = os.environ["SERVICENOW_USER"]
    password = os.environ["SERVICENOW_PASS"]
    priorities = ",".join(p.strip() for p in priority.split(","))
    params = {
        "sysparm_query": f"state=1^priorityIN{priorities}",
        "sysparm_limit": str(limit),
    }
    resp = requests.get(url, params=params, auth=(user, password), timeout=15)
    resp.raise_for_status()
    return [_project_incident(r) for r in resp.json().get("result", [])]


def fetch_open_incidents(priority: str = "P1,P2", limit: int = 10) -> list[dict]:
    """Fetch open incidents from ServiceNow.

    MOCK_MODE=true: reads mock_data/incidents.json, filters by priority and state=open.
    MOCK_MODE=false: GET request to ServiceNow table API using env vars
                     SERVICENOW_URL, SERVICENOW_USER, SERVICENOW_PASS.

    Args:
        priority: Comma-separated priority values to filter on, e.g. "P1,P2"
        limit: Maximum number of incidents to return

    Returns:
        List of dicts with keys: number, short_description, priority,
        service, namespace, opened_at, state, description, tags
    """
    wanted = {p.strip() for p in priority.split(",") if p.strip()}
    if MOCK_MODE:
        all_incidents = _load_mock_incidents()
        open_in_scope = [
            _project_incident(r)
            for r in all_incidents
            if r.get("state") == "open" and r.get("priority") in wanted
        ]
        return open_in_scope[:limit]
    try:
        return _fetch_real_incidents(priority, limit)
    except requests.RequestException as exc:
        console.print(f"[red]ServiceNow fetch failed: {exc}[/red]")
        return []


def _render_table(incidents: list[dict]) -> None:
    """Print a rich table of fetched incidents for CLI inspection."""
    table = Table(title="Open Ember Grid incidents", header_style="bold cyan")
    table.add_column("Number")
    table.add_column("Priority", justify="center")
    table.add_column("Service")
    table.add_column("Namespace")
    table.add_column("Short description", overflow="fold")
    for inc in incidents:
        table.add_row(
            inc["number"],
            inc["priority"],
            inc["service"],
            inc["namespace"],
            inc["short_description"],
        )
    console.print(table)


def main() -> int:
    """CLI entry: fetch and display open P1/P2 incidents."""
    incidents = fetch_open_incidents(priority="P1,P2", limit=10)
    if not incidents:
        console.print("[yellow]No open P1/P2 incidents.[/yellow]")
        return 0
    _render_table(incidents)
    return 0


if __name__ == "__main__":
    sys.exit(main())
