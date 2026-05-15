# rag — ChromaDB semantic search over Ember Grid knowledge base

This directory is the middle ring's gateway to the inner ring. It owns
the embedding pipeline and the query API. Two scripts, one job: turn
plain-English incident descriptions into the most relevant runbook
chunks.

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Rebuild the index after editing a runbook | `populate_database.py` | `query.py` | Safe to re-run — replaces, never duplicates. |
| Run a one-off search from the terminal | `query.py` | `populate_database.py` | CLI accepts free-text after the script name. |
| Use RAG from another Python script | `query.py` (import `search_knowledge_base`) | — | Returns list[dict] with source, service, score, text. |
| Change the embedding model | `populate_database.py` and `query.py` | — | Must change BOTH — they must agree on the embedder. |
| Investigate stale results | `populate_database.py` | — | Re-run ingest; the script wipes and rebuilds the collection. |

## Entry Point

    python rag/populate_database.py     # one-off ingest
    python rag/query.py "search text"   # CLI search

## Inputs

- All `.md` files under `knowledge-base/` (recursive).
- `KNOWLEDGE_BASE_PATH` and `CHROMA_DB_PATH` environment variables (default
  to repo-relative paths).
- The `all-MiniLM-L6-v2` model from `sentence-transformers` — fetched
  once, cached in `~/.cache/huggingface/`.

## Outputs

- `./chroma_db/` — the persistent ChromaDB store, committed to the repo.
- For `query.py`, a JSON-shaped result list (when imported) or a rich
  table (when run as CLI).

## Demo Talking Point

"The vector store is committed to the repo, so cloning this project gives
you working semantic search after a single `pip install` — no separate
infra to spin up, no API keys, nothing leaves the machine."
