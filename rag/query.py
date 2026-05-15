"""query.py — semantic search over Ember Grid knowledge base

Usage (CLI):
    python rag/query.py "checkout service returning 503 errors"

Usage (import):
    from rag.query import search_knowledge_base
    results = search_knowledge_base("checkout OOM kill")
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", REPO_ROOT / "chroma_db"))
COLLECTION_NAME = "ember-grid-knowledge-base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

console = Console()


def _open_collection() -> chromadb.Collection:
    """Open the persisted Ember Grid collection with the same embedder used at ingest."""
    if not CHROMA_DB_PATH.exists():
        raise FileNotFoundError(
            f"Chroma store not found at {CHROMA_DB_PATH}. "
            "Run `python rag/populate_database.py` first."
        )
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)


def search_knowledge_base(query: str, n_results: int = 3) -> list[dict]:
    """Query ChromaDB for the most relevant runbook chunks.

    Args:
        query: Natural language description of the incident or topic
        n_results: Number of results to return (default 3)

    Returns:
        List of dicts, each containing:
        - source: str (file path)
        - service: str (service name)
        - score: float (similarity, 0.0-1.0, higher is better)
        - text: str (the matched chunk)
    """
    if not query or not query.strip():
        return []
    collection = _open_collection()
    raw = collection.query(query_texts=[query], n_results=n_results)

    documents = (raw.get("documents") or [[]])[0]
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]

    results: list[dict] = []
    for text, meta, distance in zip(documents, metadatas, distances):
        score = max(0.0, 1.0 - float(distance))
        results.append(
            {
                "source": str(meta.get("source_file", "")),
                "service": str(meta.get("service_name", "")),
                "score": round(score, 4),
                "text": text,
            }
        )
    return results


def _render_table(query: str, results: list[dict]) -> None:
    """Print results in a readable rich table."""
    table = Table(title=f"RAG results for: {query!r}", header_style="bold cyan")
    table.add_column("#", justify="right")
    table.add_column("Source", overflow="fold")
    table.add_column("Service")
    table.add_column("Score", justify="right")
    table.add_column("Preview", overflow="fold")
    for i, item in enumerate(results, start=1):
        preview = item["text"].replace("\n", " ").strip()
        if len(preview) > 200:
            preview = preview[:200] + "…"
        table.add_row(str(i), item["source"], item["service"], f"{item['score']:.3f}", preview)
    console.print(table)


def main(argv: list[str]) -> int:
    """CLI entry point."""
    if len(argv) < 2:
        console.print("[red]Usage: python rag/query.py \"<query text>\"[/red]")
        return 2
    query = " ".join(argv[1:])
    try:
        results = search_knowledge_base(query, n_results=3)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        return 1
    if not results:
        console.print("[yellow]No results.[/yellow]")
        return 0
    _render_table(query, results)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
