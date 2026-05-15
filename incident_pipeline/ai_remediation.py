"""ai_remediation.py — RAG-grounded Rundeck job recommendation via local LLM

Usage (import):
    from incident_pipeline.ai_remediation import generate_remediation
    rec = generate_remediation(incident)

Process:
1. Pull the top 3 RAG hits from the Ember Grid knowledge base.
2. Build a constrained prompt and ask the local Ollama model for a job
   recommendation and a confidence score.
3. If Ollama is unavailable for any reason, fall back to deterministic
   rule-based matching against mock_data/rundeck_jobs.json.

This module is the only place where the LLM is contacted. It never
crashes the caller; failures degrade to the rule-based path.
"""

from __future__ import annotations

import difflib
import json
import os
import re
from pathlib import Path

import ollama
from rich.console import Console

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNDECK_JOBS_FILE = REPO_ROOT / "mock_data" / "rundeck_jobs.json"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:14b")

console = Console()


def _load_rundeck_jobs() -> list[dict]:
    """Read the Rundeck job catalogue fixture."""
    return json.loads(RUNDECK_JOBS_FILE.read_text(encoding="utf-8"))


def _rag_context(query: str, n_results: int = 3) -> list[dict]:
    """Pull top-N runbook chunks via the project's RAG layer."""
    from rag.query import search_knowledge_base
    return search_knowledge_base(query, n_results=n_results)


def _build_prompt(incident: dict, rag_results: list[dict], jobs: list[dict]) -> str:
    """Assemble the LLM prompt: RAG context + incident + job menu."""
    rag_block = "\n\n".join(
        f"[Source: {r['source']} | service={r['service']} | score={r['score']:.2f}]\n{r['text']}"
        for r in rag_results
    )
    job_menu = "\n".join(
        f"- {j['name']} (risk={j['risk_level']}, services={','.join(j['target_services'])})"
        for j in jobs
    )
    job_names = "\n".join(f"  {j['name']}" for j in jobs)
    return f"""You are Ember Grid's incident remediation assistant. Pick exactly ONE
Rundeck job from the catalogue below that best matches the incident, using
the runbook context as grounding.

INCIDENT
number:  {incident.get('number', '?')}
service: {incident.get('service', '?')}
namespace: {incident.get('namespace', '?')}
priority: {incident.get('priority', '?')}
short_description: {incident.get('short_description', '?')}
description: {incident.get('description', '')[:600]}

RUNBOOK CONTEXT (top {len(rag_results)} chunks)
{rag_block}

RUNDECK JOB CATALOGUE
{job_menu}

VALID JOB NAMES (copy one of these EXACTLY into job_name — do not invent new names):
{job_names}

Respond with ONLY a JSON object, no commentary, with these keys:
  job_name      - MUST be copied verbatim from the VALID JOB NAMES list above
  confidence    - a float between 0.0 and 1.0 reflecting how well the runbook context supports this job for this incident
  reasoning     - 2-3 sentences explaining the choice, referencing the runbook context where relevant
"""


def _parse_llm_json(text: str) -> dict | None:
    """Extract a JSON object from a possibly chatty LLM response.

    Handles qwen3 <think>...</think> blocks and truncated responses by
    scanning for the first syntactically valid JSON object using raw_decode.
    """
    # qwen3 emits its chain-of-thought inside <think> tags before the actual answer.
    # These must be stripped first or raw_decode picks up JSON fragments inside the
    # reasoning text (qwen3 often reasons by writing example JSON, which breaks parsing).
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|thinking\|>.*?<\|/thinking\|>", "", text, flags=re.DOTALL).strip()

    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            # raw_decode(text, i) attempts to parse a JSON value starting at index i.
            # Scanning forward from each '{' handles models that prefix the JSON with
            # prose like "Here is my recommendation:" before the actual object.
            obj, _ = decoder.raw_decode(text, i)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _job_by_name(jobs: list[dict], name: str) -> dict | None:
    """Look up a Rundeck job by exact name, falling back to closest fuzzy match.

    The LLM occasionally returns a plausible-sounding but non-existent job
    name when no catalogue entry directly targets the incident's service.
    difflib catches near-misses (e.g. 'trigger-supplier-resync' → the best
    available job) so we degrade gracefully instead of hard-failing.

    cutoff=0.4 is intentionally permissive — better to pick a plausible job and
    let the confidence gate reject it than to hard-fail and skip remediation entirely.
    """
    normalised = name.strip().lower()
    for job in jobs:
        if job["name"].lower() == normalised:
            return job

    job_names = [j["name"] for j in jobs]
    matches = difflib.get_close_matches(name, job_names, n=1, cutoff=0.4)
    if matches:
        console.log(
            f"[yellow]Job name {name!r} not found; using closest match {matches[0]!r}[/yellow]"
        )
        return _job_by_name(jobs, matches[0])
    return None


def _rule_based_match(incident: dict, jobs: list[dict]) -> dict:
    """Deterministic fallback: pick the first job whose target_services includes the incident's service."""
    service = incident.get("service", "")
    for job in jobs:
        if service in job.get("target_services", []):
            return {
                "job_name": job["name"],
                "job_uuid": job["uuid"],
                "confidence": 0.65,
                "reasoning": "Rule-based match on service name — Ollama unavailable.",
                "rag_sources": [],
                "llm_used": "rule-based-fallback",
            }
    fallback = jobs[0]
    return {
        "job_name": fallback["name"],
        "job_uuid": fallback["uuid"],
        "confidence": 0.50,
        "reasoning": "No job targets this service directly; defaulting to safest catalogue entry.",
        "rag_sources": [],
        "llm_used": "rule-based-fallback",
    }


def _call_ollama(prompt: str) -> str:
    """Send the prompt to the local Ollama server and return raw text."""
    # NOTE (forward-looking): the local Ollama path keeps incident data on-prem
    # at zero per-request cost — the deliberate choice for the demo. A future
    # variant (see "Where This Goes Next" in presentation/slides_content.md)
    # could swap this function for a thin GitHub Copilot agents / Copilot
    # Workspace API call without changing the surrounding RAG context build or
    # the JSON contract enforced by _parse_llm_json / _job_by_name. The model
    # stays interchangeable; only this client function and OLLAMA_MODEL/host
    # env vars would need to move.
    client = ollama.Client(host=OLLAMA_HOST)
    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        # /no_think suppresses qwen3's extended reasoning mode. Without it qwen3 spends
        # ~700-900 tokens on internal deliberation before producing the JSON, often hitting
        # num_predict and truncating the closing brace — producing unparseable output.
        system="/no_think",
        # temperature=0.1: near-deterministic output. We want the same job recommended for
        # the same incident — not creative variation. Slightly above 0 to avoid degenerate
        # repetition loops that some quantised models exhibit at temperature=0.
        options={"temperature": 0.1, "num_predict": 2048},
        # Keep model loaded for 10 minutes after last request to avoid the 9s cold-load
        # penalty on back-to-back incidents during a pipeline run.
        keep_alive="10m",
    )
    return response.get("response", "")


def generate_remediation(incident: dict) -> dict:
    """Generate a Rundeck job recommendation using RAG context and a local LLM.

    Process:
    1. Call search_knowledge_base(incident["short_description"]) from rag/query.py
    2. Build a prompt combining: top 3 RAG results + incident details
    3. Send prompt to Ollama (model from OLLAMA_MODEL env var)
    4. Parse response to extract job recommendation and confidence score
    5. If Ollama is unavailable: fall back to rule-based matching against
       mock_data/rundeck_jobs.json using service name matching

    Args:
        incident: Incident dict from fetch_incidents

    Returns:
        Dict with keys:
        - job_name: str (Rundeck job name)
        - job_uuid: str (from rundeck_jobs.json)
        - confidence: float (0.0-1.0)
        - reasoning: str (2-3 sentence explanation)
        - rag_sources: list[str] (source files used)
        - llm_used: str ("ollama:<model>" or "rule-based-fallback")
    """
    jobs = _load_rundeck_jobs()
    rag_results = _rag_context(incident.get("short_description", ""))
    rag_sources = [r["source"] for r in rag_results]

    prompt = _build_prompt(incident, rag_results, jobs)
    try:
        raw = _call_ollama(prompt)
        parsed = _parse_llm_json(raw)
        if not parsed or "job_name" not in parsed:
            raise ValueError("LLM did not return a parseable job recommendation")
        chosen = _job_by_name(jobs, parsed["job_name"])
        if chosen is None:
            raise ValueError(f"LLM picked unknown job: {parsed.get('job_name')!r}")
        confidence = float(parsed.get("confidence", 0.6))
        confidence = max(0.0, min(1.0, confidence))
        return {
            "job_name": chosen["name"],
            "job_uuid": chosen["uuid"],
            "confidence": round(confidence, 3),
            "reasoning": str(parsed.get("reasoning", "")).strip(),
            "rag_sources": rag_sources,
            "llm_used": f"ollama:{OLLAMA_MODEL}",
        }
    except Exception as exc:
        console.log(
            f"[yellow]Ollama unavailable, falling back to rule-based match: {exc}[/yellow]"
        )
        result = _rule_based_match(incident, jobs)
        result["rag_sources"] = rag_sources
        return result
