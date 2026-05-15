"""trigger_rundeck.py — execute a Rundeck job, gated by confidence

Usage (import):
    from incident_pipeline.trigger_rundeck import trigger_job
    result = trigger_job(job_uuid, confidence, incident_number)

Confidence gate:
    confidence >= 0.70: execute the job automatically
    confidence <  0.70: flag for human approval, do NOT execute
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

import requests
from rich.console import Console

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
REPO_ROOT = Path(__file__).resolve().parent.parent
RUNDECK_JOBS_FILE = REPO_ROOT / "mock_data" / "rundeck_jobs.json"

CONFIDENCE_THRESHOLD = 0.70

console = Console()


def _load_rundeck_jobs() -> list[dict]:
    """Read the Rundeck job catalogue fixture."""
    return json.loads(RUNDECK_JOBS_FILE.read_text(encoding="utf-8"))


def _find_job(jobs: list[dict], job_uuid: str) -> dict | None:
    """Look up a job catalogue entry by UUID."""
    for job in jobs:
        if job["uuid"] == job_uuid:
            return job
    return None


def _mock_execute(job: dict, incident_number: str) -> dict:
    """Return a realistic mock Rundeck execution response."""
    duration = int(job.get("avg_duration_seconds", 180))
    time.sleep(0.5)
    execution_id = f"mock-{uuid.uuid4().hex[:12]}"
    return {
        "execution_id": execution_id,
        "status": "executed",
        "requires_approval": False,
        "message": (
            f"Executed Rundeck job {job['name']!r} (mock) for incident "
            f"{incident_number}; expected duration {duration}s."
        ),
        "duration_seconds": duration,
    }


def _real_execute(job_uuid: str, incident_number: str) -> dict:
    """POST to the real Rundeck API to start the job."""
    base = os.environ["RUNDECK_URL"].rstrip("/")
    token = os.environ["RUNDECK_TOKEN"]
    url = f"{base}/api/43/job/{job_uuid}/run"
    headers = {
        "X-Rundeck-Auth-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {"options": {"incident_number": incident_number}}
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return {
        "execution_id": str(payload.get("id", "unknown")),
        "status": "executed",
        "requires_approval": False,
        "message": f"Triggered Rundeck job {job_uuid} for incident {incident_number}.",
        "duration_seconds": int(payload.get("averageDuration", 0) / 1000) or 180,
    }


def trigger_job(job_uuid: str, confidence: float, incident_number: str) -> dict:
    """Trigger a Rundeck job, subject to the confidence gate.

    Confidence gate:
        confidence >= 0.70: execute the job automatically
        confidence < 0.70: set requires_approval=True, do NOT execute

    MOCK_MODE=true: simulate execution with realistic mock response.
                    Sleep 0.5s to simulate API latency.
    MOCK_MODE=false: POST to Rundeck API at RUNDECK_URL/api/43/job/{uuid}/run
                     with header X-Rundeck-Auth-Token: RUNDECK_TOKEN.

    Args:
        job_uuid: UUID from rundeck_jobs.json
        confidence: Float from ai_remediation output
        incident_number: e.g. "INC0042183" (for logging)

    Returns:
        Dict with keys:
        - execution_id: str
        - status: str ("executed", "pending_approval", "failed")
        - requires_approval: bool
        - message: str
        - duration_seconds: int (mock: from avg_duration_seconds in rundeck_jobs.json)
    """
    jobs = _load_rundeck_jobs()
    job = _find_job(jobs, job_uuid)
    if job is None:
        return {
            "execution_id": "",
            "status": "failed",
            "requires_approval": False,
            "message": f"Unknown Rundeck job UUID: {job_uuid}",
            "duration_seconds": 0,
        }

    job_threshold = float(job.get("confidence_threshold", CONFIDENCE_THRESHOLD))
    # Per-job thresholds can only raise the bar, never lower it below the global floor.
    # A job with confidence_threshold=0.90 requires 0.90; one with 0.50 still requires 0.70.
    effective_threshold = max(CONFIDENCE_THRESHOLD, job_threshold)
    # human_review_required overrides confidence entirely — no score can auto-fire these jobs.
    # Used for trigger-manual-fulfilment-retry (duplicate shipment risk).
    human_review = bool(job.get("human_review_required", False))

    if human_review or confidence < effective_threshold:
        return {
            "execution_id": "",
            "status": "pending_approval",
            "requires_approval": True,
            "message": (
                f"Confidence {confidence:.2f} below threshold {effective_threshold:.2f}"
                f" or job flagged for human review — incident {incident_number} pending."
            ),
            "duration_seconds": 0,
        }

    if MOCK_MODE:
        return _mock_execute(job, incident_number)
    try:
        return _real_execute(job_uuid, incident_number)
    except requests.RequestException as exc:
        return {
            "execution_id": "",
            "status": "failed",
            "requires_approval": False,
            "message": f"Rundeck API call failed: {exc}",
            "duration_seconds": 0,
        }
