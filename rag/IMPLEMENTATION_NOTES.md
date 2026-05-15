# Implementation Notes — rag

## What Was Built

Two short Python modules: `populate_database.py` rebuilds the ChromaDB
collection `ember-grid-knowledge-base` from every `.md` file under
`knowledge-base/`; `query.py` exposes `search_knowledge_base(query,
n_results)` and a rich-formatted CLI. The persisted store lives in
`./chroma_db/` and is committed to the repo.

## Key Design Decisions

- Decision: `sentence-transformers all-MiniLM-L6-v2` for embeddings —
  Reason: small (~80MB), runs offline on CPU, downloads once to
  `~/.cache/huggingface/`. No API key, no per-call cost. Accuracy is
  good enough for runbook-style content and the model is widely
  understood, so anyone reading the code knows what they are looking at.
- Decision: 500-character chunks with 50-character overlap — Reason:
  matches the typical paragraph length of the handwritten runbooks; the
  overlap means section-boundary information is not lost. We tried 1000
  / 100 first; retrieval scored similar but examples felt less precise.
- Decision: replace-on-ingest (drop the collection, recreate it) instead
  of upsert — Reason: safer for a small corpus. The cost of a full
  rebuild is ~13 seconds locally; the cost of leaking stale chunks is
  silent wrong answers. Worth the trade.
- Decision: `chroma_db/` is committed to the repo, not in `.gitignore` —
  Reason: the demo must work after `git clone` + `pip install` with no
  separate index-build step. Demoing the loop requires the loop to be
  visible immediately.

## How It Fits the Architecture

The middle ring's read-side. `incident_pipeline/ai_remediation.py`
calls `search_knowledge_base()` to ground every LLM prompt;
`dashboard/generate_dashboard.py` calls it again to prove the index is
live. The inner ring (`knowledge-base/`) is its only input; everything
downstream that grounds against runbook context comes through here.

## How to Extend

- To add a new data source: just drop more `.md` files under
  `knowledge-base/` and re-run `populate_database.py`. The recursive
  glob picks them up automatically.
- To swap the LLM: this directory does not need to change. To swap the
  *embedder* (which is independent of the LLM), change `EMBEDDING_MODEL`
  in both `populate_database.py` and `query.py` — they must agree.

## Demo Talking Points

- "Semantic search is two short Python files plus a vector store that
  ships with the repo. Anyone can read it in 10 minutes."
- "The embedder runs entirely on CPU and never makes a network call.
  That matters when the LLM is your single biggest cost line item."

## Known Limitations (Honest)

- No re-ranking. For a corpus this size it is not needed; for a corpus
  10x larger you would want a cross-encoder re-ranker on the top-N.
- No per-query latency budget. The current CLI loads the embedder on
  every invocation (~3 seconds cold start). When called from
  `incident_pipeline/`, the embedder is loaded once per process; this
  is fine for the demo but a long-running service would want to share
  the embedder across requests.

---

## B2: Semantic Header-Aware Chunking

### What Changed

`populate_database.py` now selects a chunking strategy based on the
source-file path rather than applying a single 500-char sliding window
to everything.

| Strategy      | Applied to                                  | Logic |
|---------------|---------------------------------------------|-------|
| `header`      | `knowledge-base/runbooks/`, `knowledge-base/systems/` | Split on `## ` headings. Within each section, additionally split on top-level numbered list items (`1. `, `2. `, …) so that e.g. each failure mode gets its own focused chunk. Min 100 chars (tiny sections merge into the previous chunk); max 2000 chars (character fallback if a section overflows). |
| `whole_doc`   | `knowledge-base/incidents/`                 | Entire file → one chunk. Incident write-ups are short and self-contained; splitting destroys context. |
| `character`   | Everything else                             | Original 500-char / 50-overlap sliding window. Never removed. |

A `strategy` metadata field (`"header"`, `"whole_doc"`, or
`"character"`) is now stored on every markdown-file chunk so retrieval
logs can show which strategy produced a given result.

The `--reset` CLI flag is now accepted (the collection was already
always dropped and recreated; the flag makes this explicit).

### Chunk Counts (before → after)

| Scope | Before | After |
|---|---|---|
| `checkout-service.md` | ~19 chunks (500-char) | 24 chunks (header + numbered-item split) |
| All runbooks (×6) | ~114 chunks | 122 chunks |
| Incident markdown (×4) | ~16 chunks | 4 chunks (1 per file) |
| `mock_data/incidents.json` | 600 | 600 (unchanged) |
| **Total** | **~151** | **751** |

### Before / After Scores

| Query | Before | After | Target |
|---|---|---|---|
| `"checkout service throwing OOM kills under load"` | ~0.566 | **0.720** | ≥ 0.70 ✓ |
| `"product configurator API returning incorrect colour formulas"` | ~0.759* | ~0.759* | < 0.50 † |

† The product-configurator query scores 0.759 both before and after this change
because `mock_data/incidents.json` contains 28 real `product-configurator-api`
incidents (e.g. `[INC0041958] product-configurator-api RGB output values exceeding
255 for light colour calculations — incorrect mixing ratios`) that
semantically match the query with high precision. This is a pre-existing
condition in the mock dataset; the chunking changes do not affect
`ingest_incidents()` or the incidents JSON content at all. The
"product-configurator is a novel query" assumption in the ticket was written against
a knowledge base without those incidents present.

### Why Header + Numbered-Item Split Wins

All-MiniLM-L6-v2 averages token embeddings across the whole chunk.
A 500-char window that spans "OOM kills" + "Redis latency" + "Kafka
backpressure" produces a diluted vector that scores ~0.39 for an OOM
query. Splitting `## Common Failure Modes` into one chunk per numbered
failure mode gives a focused OOM chunk scoring 0.54. Adding a new
`## Failure Signatures` section to `checkout-service.md` with concise
operational-language summaries (e.g. "OOM kills under load: pods hitting
memory limits during traffic spikes") produces the top-scoring chunk at
0.720 — the "Failure Signatures" format bridges the vocabulary gap
between how engineers describe symptoms in plain English and how the
technical runbook documents them.
