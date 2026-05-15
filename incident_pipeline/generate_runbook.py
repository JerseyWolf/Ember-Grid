"""generate_runbook.py — auto-generate a runbook from a resolved incident

Usage (import):
    from incident_pipeline.generate_runbook import generate_and_commit_runbook
    path = generate_and_commit_runbook(incident, resolution_notes)

The generated file lives under knowledge-base/incidents/ and is committed
to the repository with a self-documenting commit message. Re-running the
RAG ingest then includes this new runbook in future searches — that is
the self-improving loop.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import ollama
from rich.console import Console

REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_DIR = REPO_ROOT / "knowledge-base" / "incidents"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# Deliberately the smaller coder model, not qwen3:14b.
# Runbook generation is structured prose + code snippets — qwen2.5-coder is faster
# and equally capable here. qwen3:14b is reserved for the harder reasoning task in
# ai_remediation.py where job selection depends on semantic grounding against RAG context.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

console = Console()


def _safe_service(name: str) -> str:
    """Clean a service name for safe use in filenames."""
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", name or "unknown-service").strip("-")
    return cleaned or "unknown-service"


def _runbook_path(incident: dict) -> Path:
    """Build the destination path for an auto-generated runbook."""
    number = incident.get("number", "INC0000000")
    service = _safe_service(incident.get("service", "unknown-service"))
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return INCIDENTS_DIR / f"{number}-{service}-{date_str}.md"


def _enrich_with_ollama(incident: dict, resolution_notes: str) -> str | None:
    """Ask the local LLM for diagnostic steps and prevention notes. None on failure."""
    # The ---SPLIT--- separator is a reliable parse boundary — less fragile than asking
    # the model to use JSON or numbered headings, both of which it tends to ignore.
    prompt = f"""You are documenting a Ember Grid incident for the on-call
knowledge base. Produce TWO short markdown sections, no headings, no extra
commentary:

SECTION A — Diagnostic Steps (3-5 bullets, numbered): the specific kubectl,
curl or log commands an on-call engineer would run to confirm this failure
mode in future.

SECTION B — Prevention Notes (2-3 bullets): how to reduce the chance of this
recurring (alerting, capacity, schedule, validation, etc).

Separate the two sections with a line containing exactly: ---SPLIT---

INCIDENT
service: {incident.get('service', '?')}
namespace: {incident.get('namespace', '?')}
priority: {incident.get('priority', '?')}
short_description: {incident.get('short_description', '?')}
description: {incident.get('description', '')[:600]}
resolution_notes: {resolution_notes}
"""
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={"temperature": 0.2, "num_predict": 500},
        )
        return resp.get("response", "").strip() or None
    except Exception as exc:
        console.log(f"[yellow]Ollama enrichment skipped: {exc}[/yellow]")
        return None


def _split_enrichment(text: str) -> tuple[str, str]:
    """Split the LLM output into (diagnostics, prevention) sections."""
    if "---SPLIT---" in text:
        a, b = text.split("---SPLIT---", 1)
        return a.strip(), b.strip()
    return text.strip(), ""


def _build_runbook(incident: dict, resolution_notes: str, enrichment: str | None) -> str:
    """Assemble the final markdown runbook for the resolved incident."""
    number = incident.get("number", "")
    service = incident.get("service", "unknown-service")
    priority = incident.get("priority", "P?")
    namespace = incident.get("namespace", "?")
    short = incident.get("short_description", "")
    description = incident.get("description", "")
    tags = ", ".join(incident.get("tags", []) or [])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if enrichment:
        diagnostics, prevention = _split_enrichment(enrichment)
    else:
        diagnostics = (
            "1. `kubectl get pods -n " + namespace + " -l app=" + service + "`\n"
            "2. `kubectl logs -n " + namespace + " -l app=" + service + " --tail=200`\n"
            "3. Check Dynatrace for correlated problem cards in the last 30 minutes."
        )
        prevention = "- Review the relevant runbook in `knowledge-base/runbooks/` for service-specific guidance."

    return f"""# {number} — {service} ({priority})

> Auto-generated runbook. Source: resolved ServiceNow incident.
> Generated: {generated_at}

## Service Overview

`{service}` in namespace `{namespace}`. See
[`knowledge-base/runbooks/{service}.md`](../runbooks/{service}.md) for the
canonical service-level runbook. This document captures one specific
incident and its resolution so future searches can surface it.

## Incident Summary

- Number: `{number}`
- Priority: {priority}
- Service / namespace: `{service}` / `{namespace}`
- Tags: {tags or "(none)"}

**Short description:** {short}

**Full description:**

{description}

## Common Failure Modes

This incident matches the failure pattern below. Future occurrences with
similar symptoms should be tried against the same remediation first.

- Symptom seen here: {short}
- Likely class: see `knowledge-base/runbooks/{service}.md` for the family.

## Diagnostic Steps

{diagnostics}

## Remediation Steps

1. {resolution_notes}

Re-run the diagnostic steps above after remediation to confirm recovery.

## Escalation Path

Follow the escalation path in
[`knowledge-base/runbooks/{service}.md`](../runbooks/{service}.md). For
this incident class, the primary on-call team for `{service}` is the
first responder.

## Post-Incident Checklist

- [ ] Service is healthy in all production namespaces.
- [ ] No related ServiceNow incidents open.
- [ ] Prevention items below have been triaged into the team's backlog.

## Prevention Notes

{prevention or "- See parent runbook for service-specific prevention guidance."}
"""


def _git_commit(file_path: Path, incident: dict) -> None:
    """Stage and commit the new runbook. Logs but does not raise on failure.

    Best-effort only — the runbook is already written to disk. A git failure
    (no credentials, detached HEAD, nothing staged) must not roll back the incident
    resolution or crash the pipeline. The file will be picked up on the next manual commit.
    """
    short = incident.get("short_description", "")
    number = incident.get("number", "")
    message = f"[knowledge-base] auto-generated runbook for {number} — {short}"
    try:
        subprocess.run(
            ["git", "add", str(file_path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.log(
                f"[yellow]git commit returned {result.returncode}: "
                f"{result.stdout.strip() or result.stderr.strip()}[/yellow]"
            )
    except subprocess.CalledProcessError as exc:
        console.log(f"[yellow]git add failed: {exc}[/yellow]")


def generate_and_commit_runbook(incident: dict, resolution_notes: str) -> str:
    """Auto-generate a runbook from a resolved incident and commit it to the repo.

    Process:
    1. Build a structured Markdown runbook from incident data + resolution notes
    2. Use Ollama to enrich it if available (add diagnostic steps, prevention notes)
    3. Save to knowledge-base/incidents/INC{number}-{service}-{YYYY-MM-DD}.md
    4. Git add + commit with message:
       [knowledge-base] auto-generated runbook for {number} — {short_description}

    Args:
        incident: Incident dict
        resolution_notes: What fixed it

    Returns:
        File path of the new runbook (str)
    """
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    enrichment = _enrich_with_ollama(incident, resolution_notes)
    body = _build_runbook(incident, resolution_notes, enrichment)

    out_path = _runbook_path(incident)
    out_path.write_text(body, encoding="utf-8")
    console.log(f"[green]Wrote auto-runbook[/green] {out_path.relative_to(REPO_ROOT)}")
    _git_commit(out_path, incident)
    return str(out_path)
