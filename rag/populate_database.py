"""populate_database.py — ingest Ember Grid knowledge base into ChromaDB

Usage:
    python rag/populate_database.py
    python rag/populate_database.py --reset   # explicitly drop + recreate before ingesting

Reads all .md files from knowledge-base/ recursively, chunks them using a
semantic, path-aware strategy, embeds with sentence-transformers
(all-MiniLM-L6-v2, offline, no API key), stores in ./chroma_db/ persistent
store.

Chunking strategies
-------------------
  header     knowledge-base/runbooks/ and knowledge-base/systems/
             Split on ## headings. Each ## section = one chunk.
             Min 100 chars; max 2000 chars (character fallback inside a
             section that overflows).
  whole_doc  knowledge-base/incidents/
             Entire file = one chunk. Incident write-ups are short and
             self-contained; splitting destroys context.
  character  Everything else (inc. CONTEXT.md, top-level notes)
             Original 500-char / 50-overlap sliding window — never removed.

Safe to re-run: existing data is replaced, not duplicated.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_PATH = Path(os.getenv("KNOWLEDGE_BASE_PATH", REPO_ROOT / "knowledge-base"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", REPO_ROOT / "chroma_db"))
INCIDENTS_FILE = Path(os.getenv("INCIDENTS_FILE", REPO_ROOT / "mock_data" / "incidents.json"))
COLLECTION_NAME = "ember-grid-knowledge-base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
HEADER_MAX_SIZE = 2000
HEADER_MIN_SIZE = 100

console = Console()


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Strategy C — fixed-size character window with overlap.

    Simple character-window chunking. Adequate for runbook-style markdown
    where headings and paragraphs are short. No tokenisation required.
    """
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    step = size - overlap
    while start < len(text):
        chunks.append(text[start : start + size])
        start += step
    return chunks


def _split_numbered_items(section: str, min_size: int) -> list[str]:
    """Split a ## section into one chunk per top-level numbered list item.

    The ## heading is prepended to every sub-chunk so each chunk is
    independently searchable with its section context intact.
    Returns [section] unchanged when the section has no numbered list or
    only a single item — avoids unnecessary fragmentation.
    """
    lines = section.splitlines()
    heading_lines: list[str] = []
    body_start: int = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            heading_lines.append(line)
            body_start = i + 1
        else:
            break

    heading = "\n".join(heading_lines)
    body = "\n".join(lines[body_start:]).strip()

    # Split at the start of each top-level numbered item ("1. ", "2. ", …)
    items: list[str] = [
        item.strip()
        for item in re.split(r"(?=^\d+\. )", body, flags=re.MULTILINE)
        if item.strip()
    ]

    if len(items) <= 1:
        return [section]

    result: list[str] = []
    for item in items:
        chunk = f"{heading}\n\n{item}" if heading else item
        if len(chunk) < min_size and result:
            # Too short alone — append to the previous chunk.
            result[-1] = result[-1] + "\n\n" + item
        else:
            result.append(chunk)

    return result if result else [section]


def chunk_text_header(
    text: str,
    max_size: int = HEADER_MAX_SIZE,
    min_size: int = HEADER_MIN_SIZE,
) -> list[str]:
    """Strategy A — split on ## headings, then on numbered list items within.

    Two-level splitting:
      1. Divide the document on ## heading boundaries.
      2. Within each ## section, further divide on top-level numbered list
         items (1. 2. 3. …) so that e.g. each failure mode gets its own
         focused chunk with the section heading prepended for context.

    Sections shorter than min_size are merged into the previous chunk.
    Sections longer than max_size fall back to character chunking.
    """
    # Split *before* every '## ' that starts a line, keeping the header.
    raw_sections: list[str] = re.split(r"(?=^## )", text, flags=re.MULTILINE)

    chunks: list[str] = []
    for section in raw_sections:
        section = section.strip()
        if not section:
            continue

        if len(section) < min_size:
            # Too small on its own — glue it to the previous chunk.
            if chunks:
                chunks[-1] = chunks[-1] + "\n\n" + section
            else:
                chunks.append(section)
        elif len(section) <= max_size:
            # Within-section numbered-item split for focused retrieval.
            sub = _split_numbered_items(section, min_size)
            chunks.extend(sub)
        else:
            # Section overflows max_size — apply character fallback.
            sub_chunks = chunk_text(section)
            chunks.extend(sub_chunks)

    return chunks


def chunk_text_whole_doc(text: str) -> list[str]:
    """Strategy B — entire document as a single chunk."""
    stripped = text.strip()
    return [stripped] if stripped else []


# ---------------------------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------------------------

def select_strategy(path: Path) -> str:
    """Return the chunking strategy name for a given file path.

    Rules (evaluated in order):
      1. Under knowledge-base/runbooks/ or knowledge-base/systems/ → "header"
      2. Under knowledge-base/incidents/                           → "whole_doc"
      3. Anything else                                             → "character"
    """
    try:
        rel = path.relative_to(KNOWLEDGE_BASE_PATH)
    except ValueError:
        return "character"

    top = rel.parts[0] if rel.parts else ""
    if top in ("runbooks", "systems"):
        return "header"
    if top == "incidents":
        return "whole_doc"
    return "character"


def apply_strategy(text: str, strategy: str) -> list[str]:
    """Dispatch to the correct chunker by strategy name."""
    if strategy == "header":
        return chunk_text_header(text)
    if strategy == "whole_doc":
        return chunk_text_whole_doc(text)
    return chunk_text(text)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def discover_markdown_files(root: Path) -> list[Path]:
    """Return every .md file under root, sorted for stable ordering."""
    if not root.exists():
        raise FileNotFoundError(f"Knowledge base path does not exist: {root}")
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def extract_service_name(path: Path) -> str:
    """Derive the service name from a runbook filename.

    `knowledge-base/runbooks/checkout-service.md` -> `checkout-service`.
    Files outside `runbooks/` get the filename stem unchanged.
    """
    return path.stem


def reset_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    """Drop and recreate the Ember Grid collection.

    Re-running is safe because we replace, not append.
    """
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_file(collection: chromadb.Collection, path: Path) -> int:
    """Chunk and ingest a single markdown file. Returns chunks written."""
    text = path.read_text(encoding="utf-8")
    strategy = select_strategy(path)
    chunks = apply_strategy(text, strategy)
    if not chunks:
        return 0
    service_name = extract_service_name(path)
    rel_source = str(path.relative_to(REPO_ROOT))
    ids = [f"{rel_source}::chunk-{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source_file": rel_source,
            "chunk_index": i,
            "service_name": service_name,
            "strategy": strategy,
        }
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def build_incident_document(incident: dict) -> str:
    """Format one incident as searchable text for the RAG corpus."""
    tags = ", ".join(str(tag) for tag in incident.get("tags", []))
    lines = [
        f"[{incident.get('number', '')}] {incident.get('short_description', '')}",
        (
            f"Service: {incident.get('service', '')}  "
            f"Namespace: {incident.get('namespace', '')}  "
            f"Priority: {incident.get('priority', '')}  "
            f"State: {incident.get('state', '')}"
        ),
        f"Tags: {tags}",
        str(incident.get("description", "")),
    ]
    if incident.get("state") == "closed":
        resolution = incident.get("resolution_notes")
        if resolution:
            lines.append(f"Resolution: {resolution}")
        rundeck_job = incident.get("rundeck_job_used")
        if rundeck_job:
            lines.append(f"Rundeck job used: {rundeck_job}")
        mttr = incident.get("mttr_minutes")
        if mttr is not None:
            lines.append(f"MTTR: {mttr} minutes")
    return "\n".join(line for line in lines if line)


def ingest_incidents(collection: chromadb.Collection, path: Path = INCIDENTS_FILE) -> int:
    """Ingest mock incidents as one searchable document per incident."""
    if not path.exists():
        raise FileNotFoundError(f"Incidents file does not exist: {path}")
    incidents = json.loads(path.read_text(encoding="utf-8"))
    if not incidents:
        return 0
    rel_source = str(path.relative_to(REPO_ROOT))
    ids = [f"{rel_source}::{incident.get('number', i)}" for i, incident in enumerate(incidents)]
    documents = [build_incident_document(incident) for incident in incidents]
    metadatas = [
        {
            "source_file": rel_source,
            "service_name": str(incident.get("service", "")),
            "number": str(incident.get("number", "")),
            "priority": str(incident.get("priority", "")),
            "state": str(incident.get("state", "")),
            "namespace": str(incident.get("namespace", "")),
            "category": str(incident.get("category", "")),
            "tags_csv": ",".join(str(tag) for tag in incident.get("tags", [])),
        }
        for incident in incidents
    ]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(incidents)


def print_summary(rows: list[tuple[str, int]], elapsed_s: float) -> None:
    """Render a rich summary table of files and chunks ingested."""
    table = Table(title="Ember Grid RAG ingest", header_style="bold cyan")
    table.add_column("Source file", overflow="fold")
    table.add_column("Chunks", justify="right")
    total = 0
    for source, count in rows:
        table.add_row(source, str(count))
        total += count
    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")
    console.print(table)
    console.print(
        f"[green]✓[/green] Ingested {len(rows)} files, "
        f"{total} chunks in {elapsed_s:.2f}s -> {CHROMA_DB_PATH}"
    )


def main() -> int:
    """Entry point: rebuild the Ember Grid RAG index from scratch."""
    parser = argparse.ArgumentParser(
        description="Populate the Ember Grid ChromaDB knowledge base.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the collection before ingesting (always performed; flag is accepted for explicitness).",
    )
    parser.parse_args()  # validates flags; --reset is the default behaviour

    started = time.perf_counter()
    console.rule("[bold]ops-knowledge-loop — RAG ingest[/bold]")
    console.print(f"Knowledge base: [cyan]{KNOWLEDGE_BASE_PATH}[/cyan]")
    console.print(f"Chroma store:   [cyan]{CHROMA_DB_PATH}[/cyan]")
    console.print(f"Embedding:      [cyan]{EMBEDDING_MODEL}[/cyan]")
    console.print(
        "Strategies:     [cyan]header[/cyan] (runbooks/systems)  "
        "[cyan]whole_doc[/cyan] (incidents)  "
        "[cyan]character[/cyan] (everything else)\n"
    )

    files = discover_markdown_files(KNOWLEDGE_BASE_PATH)
    if not files:
        console.print("[red]No .md files found under knowledge base[/red]")
        return 1

    CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = reset_collection(client)

    rows: list[tuple[str, int]] = []
    for path in files:
        count = ingest_file(collection, path)
        rows.append((str(path.relative_to(REPO_ROOT)), count))
    incident_count = ingest_incidents(collection)
    rows.append((str(INCIDENTS_FILE.relative_to(REPO_ROOT)), incident_count))

    elapsed = time.perf_counter() - started
    print_summary(rows, elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
