"""
query_live.py — live free-text incident query CLI for ops-knowledge-loop.

Usage:
    python query_live.py "describe the incident here"
    python query_live.py "checkout service is throwing OOM kills under load"

Purpose:
    Accept a natural-language incident description, search the committed RAG
    knowledge base for the top 3 similar past incidents/runbook chunks, and
    pass the synthetic in-memory incident to AI remediation for a recommended
    Rundeck job plus confidence-gate verdict.

Governance status:
    Permitted as a safe demo command. This command is read-only, has no side
    effects, never modifies incidents.json or chroma_db, and never forces
    MOCK_MODE off.

Runtime behavior:
    With Ollama available, remediation uses the configured local model grounded
    by RAG context. Without Ollama, the remediation layer degrades to its
    rule-based fallback so the demo still completes offline.
"""

import os
import sys
import time

# Suppress ChromaDB telemetry noise before any chromadb import
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Default MOCK_MODE to true — never crashes without credentials
MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    print("ERROR: rich is not installed. Run: pip install rich")
    sys.exit(1)

console = Console()


def _import_rag():
    """Import search_knowledge_base — fail with a clear message if RAG not ready."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from rag.query import search_knowledge_base
        return search_knowledge_base
    except ImportError as exc:
        console.print(f"[red]RAG import failed:[/red] {exc}")
        console.print("[yellow]Hint:[/yellow] Run [bold]python rag/populate_database.py[/bold] first.")
        sys.exit(1)


def _import_remediation():
    """Import generate_remediation from the incident pipeline."""
    try:
        from incident_pipeline.ai_remediation import generate_remediation
        return generate_remediation
    except ImportError as exc:
        console.print(f"[red]Remediation import failed:[/red] {exc}")
        sys.exit(1)


def _build_synthetic_incident(description: str) -> dict:
    """
    Wrap the free-text description in a minimal incident envelope
    compatible with ai_remediation.py expectations.
    Not written to incidents.json — ephemeral, in-memory only.
    """
    return {
        "incident_id": "LIVE-QUERY",
        "title": description,
        "short_description": description,
        "description": description,
        "service": "unknown",
        "priority": "P1",
        "status": "open",
    }


def _confidence_label(score: float) -> tuple[str, str]:
    """Return (colour, label) for a confidence score."""
    if score >= 0.85:
        return "green", "AUTO-EXECUTE"
    if score >= 0.70:
        return "yellow", "ABOVE GATE"
    if score >= 0.50:
        return "orange3", "PENDING REVIEW"
    return "red", "RULE-BASED FALLBACK"


def _rag_score_label(score: float) -> str:
    """Human-readable similarity band."""
    if score >= 0.75:
        return f"[green]{score:.3f}[/green] ✓ strong match"
    if score >= 0.55:
        return f"[yellow]{score:.3f}[/yellow] ~ partial match"
    return f"[red]{score:.3f}[/red] ✗ weak match"


def run_live_query(description: str) -> None:
    """Full pipeline: RAG search → AI remediation → rich output."""

    t_start = time.time()

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]ops-knowledge-loop[/bold cyan]  |  [bold]Live Incident Query[/bold]\n"
        f"[dim]MOCK_MODE={str(MOCK_MODE).upper()}  |  env: {'Ubuntu/LLM' if not MOCK_MODE else 'mock'}[/dim]",
        border_style="cyan",
    ))
    console.print()
    console.print(f"[bold]Query:[/bold] [italic]{description}[/italic]")
    console.print()

    # ── Step 1: RAG knowledge base search ──────────────────────────────────
    console.print("[bold cyan]Step 1 — Searching knowledge base...[/bold cyan]")
    search_knowledge_base = _import_rag()

    try:
        results = search_knowledge_base(description, n_results=3)
    except Exception as exc:
        console.print(f"[red]RAG search error:[/red] {exc}")
        sys.exit(1)

    if not results:
        console.print("[yellow]No results returned from knowledge base.[/yellow]")
        console.print("[dim]Hint: rebuild ChromaDB with python rag/populate_database.py[/dim]")
        sys.exit(1)

    # search_knowledge_base returns list[dict] with keys: source, service, score, text
    rag_table = Table(
        title="[bold]RAG Knowledge Base — Top 3 Matches[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        border_style="cyan",
    )
    rag_table.add_column("#", style="dim", width=3)
    rag_table.add_column("Source", style="bold", max_width=35)
    rag_table.add_column("Similarity", justify="center", width=24)
    rag_table.add_column("Excerpt", max_width=60)

    for idx, item in enumerate(results, start=1):
        filename = os.path.basename(item.get("source", "unknown")) or "unknown"
        sim = item.get("score", 0.0)
        doc = item.get("text", "")
        excerpt = doc[:120].replace("\n", " ").strip() + ("…" if len(doc) > 120 else "")
        rag_table.add_row(
            str(idx),
            filename,
            _rag_score_label(sim),
            f"[dim]{excerpt}[/dim]",
        )

    console.print(rag_table)
    console.print()

    top_similarity = results[0].get("score", 0.0) if results else 0.0
    top_source = os.path.basename(results[0].get("source", "unknown")) if results else "unknown"

    if top_similarity >= 0.65:
        console.print(
            f"[green]✓ Strong precedent found[/green] — "
            f"[bold]{top_source}[/bold] (similarity {top_similarity:.3f})"
        )
    else:
        console.print(
            f"[yellow]⚠ No close precedent[/yellow] — "
            f"best match {top_similarity:.3f} in [bold]{top_source}[/bold]. "
            f"AI will deduce a remediation."
        )
    console.print()

    # ── Step 2: AI remediation ──────────────────────────────────────────────
    console.print("[bold cyan]Step 2 — Requesting AI remediation recommendation...[/bold cyan]")
    get_remediation = _import_remediation()
    incident = _build_synthetic_incident(description)

    try:
        remediation = get_remediation(incident)
    except Exception as exc:
        console.print(f"[red]Remediation error:[/red] {exc}")
        sys.exit(1)

    job_id = remediation.get("job_name", "unknown")
    confidence = remediation.get("confidence", 0.0)
    reasoning = remediation.get("reasoning", "No reasoning provided.")
    source_label = remediation.get("llm_used", "unknown")
    rag_sources = remediation.get("rag_sources", [])

    colour, gate_label = _confidence_label(confidence)

    rem_table = Table(
        title="[bold]AI Remediation Recommendation[/bold]",
        box=box.ROUNDED,
        border_style="magenta",
    )
    rem_table.add_column("Field", style="bold", width=22)
    rem_table.add_column("Value")

    rem_table.add_row("Recommended Job", f"[bold]{job_id}[/bold]")
    rem_table.add_row("Confidence", f"[{colour}]{confidence:.2f}[/{colour}]")
    rem_table.add_row("Decision Gate", f"[{colour}]{gate_label}[/{colour}]")
    rem_table.add_row("AI Source", source_label)
    rem_table.add_row("Reasoning", reasoning[:200] + ("…" if len(reasoning) > 200 else ""))
    if rag_sources:
        rem_table.add_row("RAG Sources", ", ".join(os.path.basename(s) for s in rag_sources[:3]))

    console.print(rem_table)
    console.print()

    # ── Step 3: Gate verdict ────────────────────────────────────────────────
    if confidence >= 0.70:
        console.print(Panel(
            f"[green bold]✓ WOULD AUTO-EXECUTE[/green bold]  —  "
            f"[bold]{job_id}[/bold] (confidence {confidence:.2f} ≥ 0.70 gate)\n"
            f"[dim]In a live environment this Rundeck job would fire and the ticket would close.[/dim]",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[yellow bold]⏸  PENDING HUMAN REVIEW[/yellow bold]  —  "
            f"[bold]{job_id}[/bold] (confidence {confidence:.2f} < 0.70 gate)\n"
            f"[dim]On-call engineer sees this recommendation + RAG sources before any action is taken.[/dim]",
            border_style="yellow",
        ))

    elapsed = time.time() - t_start
    console.print()
    console.print(f"[dim]Total runtime: {elapsed:.1f}s[/dim]")
    console.print()


def main() -> None:
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] python query_live.py [italic]\"describe the incident\"[/italic]")
        console.print()
        console.print("[dim]Examples:[/dim]")
        console.print('  python query_live.py "checkout service throwing OOM kills under load"')
        console.print('  python query_live.py "payment processor timeouts at peak hour"')
        console.print('  python query_live.py "inventory sync falling behind after overnight batch"')
        console.print('  python query_live.py "store POS system unable to connect to loyalty service"')
        sys.exit(0)

    description = " ".join(sys.argv[1:]).strip()
    if not description:
        console.print("[red]Error:[/red] Incident description cannot be empty.")
        sys.exit(1)

    run_live_query(description)


if __name__ == "__main__":
    main()
