"""close_incident.py — write resolution back to ServiceNow and close the ticket

Usage (import):
    from incident_pipeline.close_incident import close_incident
    ok = close_incident("INC0042183", "Rolling restart resolved OOM.", "exec-abc123")
"""

from __future__ import annotations

import os

import requests
from rich.console import Console

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
console = Console()


def _mock_close(incident_number: str, resolution_notes: str, execution_id: str) -> bool:
    """Print what would be written to ServiceNow and return True."""
    console.log(
        f"[green]MOCK ServiceNow update[/green] "
        f"{incident_number}: state=6 close_code='Solved (Permanently)' "
        f"execution_id={execution_id}"
    )
    console.log(f"  notes: {resolution_notes}")
    return True


def _real_close(incident_number: str, resolution_notes: str, execution_id: str) -> bool:
    """PATCH the ServiceNow incident record over the REST table API."""
    base = os.environ["SERVICENOW_URL"].rstrip("/")
    user = os.environ["SERVICENOW_USER"]
    password = os.environ["SERVICENOW_PASS"]
    url = f"{base}/api/now/table/incident/{incident_number}"
    body = {
        "state": "6",
        "close_code": "Solved (Permanently)",
        "resolution_notes": resolution_notes,
        "u_rundeck_execution_id": execution_id,
    }
    resp = requests.patch(url, json=body, auth=(user, password), timeout=15)
    resp.raise_for_status()
    return True


def close_incident(incident_number: str, resolution_notes: str, execution_id: str) -> bool:
    """Write resolution back to ServiceNow and close the incident.

    MOCK_MODE=true: print what would be written using rich, return True.
    MOCK_MODE=false: PATCH request to ServiceNow incident record.
                     Sets state=6 (Resolved), close_code="Solved (Permanently)",
                     resolution_notes=resolution_notes,
                     u_rundeck_execution_id=execution_id.

    Args:
        incident_number: e.g. "INC0042183"
        resolution_notes: Human-readable resolution summary
        execution_id: Rundeck execution ID to link in the ticket

    Returns:
        True if successful, False if failed
    """
    if MOCK_MODE:
        return _mock_close(incident_number, resolution_notes, execution_id)
    try:
        return _real_close(incident_number, resolution_notes, execution_id)
    except requests.RequestException as exc:
        console.print(f"[red]ServiceNow close failed for {incident_number}: {exc}[/red]")
        return False
