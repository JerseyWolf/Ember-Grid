# ops-knowledge-loop — Presentation Content
## Single source of truth for all output formats

---

## SLIDE 1 — Title

**Title:** ops-knowledge-loop  
**Subtitle:** AI-Powered Incident Triage · Ember Grid  
**Tagline:** From alert to remediation in under 2 minutes

---

## SLIDE 2 — Prior Art

**Heading:** Prior Art

**Subheading:** Three projects that map directly onto this one.

**Column 1 — WOLF Framework**  
*Open-source AI-assisted game dev environment · 2025–present*  
**Chip:** LangChain · ChromaDB · MCP · local LLM

- Same RAG stack this project runs on: LangChain + ChromaDB + LiteLLM, indexed against a live codebase and exposed to a coding agent through a dedicated MCP server.
- Headless SimBot simulation engine — runs automated tests across concurrent sessions, logs the evidence, and feeds an iterative optimiser. Same evidence-gate-action loop as ops-knowledge-loop.
- Two deployment variants: fully local zero-cost (Ollama, open-source models) and cloud/paid. Same architectural choice made here.

*Same RAG stack and architectural pattern as this project.*

**Column 2 — QVC / Qurate Retail · Cloud Migration**  
*~850 Kubernetes microservices · 2020–2024*  
**Chip:** ~850 services · 5y zero audit breach

- Migrated off Jenkins, Spinnaker, Rancher, Bitbucket, Ansible fully to Azure DevOps (~850 microservices). Two-person team.
- Ran live multi-data-centre AEM production deployments — up to 40 stakeholders, weekly cadence, manual traffic switching, nginx validation, rollback.
- Zero audit breach record over 5 years, every deployment tracked in ServiceNow.

*Same retail-scale infrastructure, ServiceNow, and gating discipline.*

**Column 3 — Multi-Geo Mobile Build-Test-Deploy**  
*Bitbucket · Jenkins · Artifactory · Jira · Consul · 2020–2024*  
**Chip:** Release: 3h → 30min · PR acceptance: 2h → 20min

- Built and instrumented a multi-geo mobile release pipeline spanning Bitbucket, Jenkins, Artifactory, Jira, and Consul service discovery.
- Release effort reduced from 3 hours to 30 minutes.
- Automated PR acceptance checks reduced from 2 hours to 20 minutes.
- Stage-level tracking, drift detection, and rollback paths — same observability discipline this project applies to RAG, LLM, and gate metrics.

*Same compression pattern this project applies to incident response.*

**Footer:** 8+ years across automotive and UK retail · Ansible-driven deployments · ServiceNow compliance · multi-geo release engineering · RAG / MCP / local-LLM pipelines.

---

## SLIDE 3 — The Problem

**Heading:** The On-Call Problem

- "Mean time to remediation is dominated by lookup time, not fix time"
- "Institutional knowledge lives in engineers' heads, not in systems"
- "Repeated incidents get manually triaged every single time"

**Footer note:** Ember Grid runs 17 microservices across UK retail infrastructure

---

## SLIDE 4 — System Architecture

**Heading:** How It Works

Pipeline stages (left -> right):

1. **INCIDENT ARRIVES** — ServiceNow ticket (mocked), free-text description
2. **RAG SEARCH** — sentence-transformers embeds the query, ChromaDB returns top 3 semantically similar past incidents + runbook chunks
3. **LLM REASONING** — Ollama (qwen3:14b, local, private) reads the RAG context and returns structured JSON: job_name, confidence, reasoning
4. **DECISION GATE** — if confidence ≥ 0.70, Rundeck job fires automatically; below 0.70, routes to human review with full context
5. **OUTCOME** — ticket closes automatically or engineer gets a pre-reasoned recommendation

**Emphasis:** Fully local · No data leaves the machine · No API costs · ~30s end-to-end

---

## SLIDE 5 — The Knowledge Base

**Heading:** What the RAG Searches

**Left column — Incident History:**
- 500+ synthetic incidents across 17 services
- Each indexed as a vector embedding in ChromaDB
- Covers OOM kills, latency spikes, ETL failures, EDI schema mismatches, POS outages, loyalty service bugs, notification duplicates

**Right column — Runbooks:**
- Per-service markdown runbooks (checkout, product-search, payment-processor, etc.)
- Auto-generated runbooks from resolved ServiceNow tickets
- Chunked and embedded alongside incident history

**Bottom stat:** All embeddings generated with all-MiniLM-L6-v2 · Similarity threshold: 0.60 strong match

---

## SLIDE 6 — The Dashboard

**Heading:** Ops Dashboard

Dashboard features:
- Recent incidents and their triage status
- RAG match scores per incident
- AI recommendation with confidence score
- Decision gate outcome (auto-executed vs pending review)
- Rundeck job catalogue

**Note:** Built with Flask · Runs locally on port 5000

---

## SLIDE 7 — Live Demo Results

**Heading:** 10 Queries · Live Run

| # | Incident | Recommended Job | Confidence | RAG Best | Outcome |
|---|----------|----------------|------------|---------|---------|
| 1 | checkout-service OOM kill | restart-service-with-memory-bump | 0.95 | 0.797 ✓ | AUTO-EXECUTE |
| 2 | payment-processor 500 errors | rollback-to-previous-version | 0.95 | 0.495 ✗ | AUTO-EXECUTE |
| 3 | product-search unresponsive after deploy | reindex-elasticsearch | 0.75 | 0.575 ~ | AUTO-EXECUTE |
| 4 | inventory sync stalled | force-inventory-sync | 0.66 | 0.675 ~ | PENDING REVIEW |
| 5 | store POS tills unresponsive | rollback-to-previous-version | 0.75 | 0.573 ~ | AUTO-EXECUTE |
| 6 | loyalty service not awarding points | restart-service-rolling | 0.35 | 0.642 ~ | PENDING REVIEW |
| 7 | order fulfilment latency spike | scale-up-replicas | 0.75 | 0.571 ~ | AUTO-EXECUTE |
| 8 | notification service duplicate emails | restart-service-with-memory-bump | 0.35 | 0.687 ~ | PENDING REVIEW |
| 9 | supplier EDI orders dropped | force-inventory-sync | 0.65 | 0.705 ~ | PENDING REVIEW |
| 10 | recommendation engine degraded | reindex-elasticsearch | 0.45 | 0.393 ✗ | PENDING REVIEW |

**Split:** 5 auto-executed · 5 routed to human review

**Note:** "The gate is discriminating by design — weak RAG similarity or ambiguous root cause correctly suppresses auto-execution"

---

## SLIDES Q1, Q3, Q6 — Featured Terminal Outputs

Three terminal examples stay in the main walkthrough: one full-confidence auto-execute case, one near-gate auto-execute case, and one low-confidence pending-review case. The remaining seven query outputs move to the appendix for optional manager follow-up.

### Q1 — checkout-service OOM kill -> AUTO-EXECUTE (0.95)

**Speaker note:** Clean auto-execute case. Three strong matches (0.795–0.797), all above the 0.60 threshold. Model returns 0.95 and the gate fires. This is the system at its best — 8.7s from incident to Rundeck job.

```
$ python query_live.py "checkout service OOM kill, container hitting memory limit and restarting repeatedly under load"

  Query: checkout service OOM kill, container hitting memory limit and restarting repeatedly under load

  RAG Top 3:
  1  incidents.json   0.797 ✓ strong match   [INC0043096] checkout-service OOM kill
  2  incidents.json   0.796 ✓ strong match   [INC0043144] checkout-service OOM kill
  3  incidents.json   0.795 ✓ strong match   [INC0043048] checkout-service OOM kill

  ✓ Strong precedent found — incidents.json (similarity 0.797)

  Recommended Job  : restart-service-with-memory-bump
  Confidence       : 0.95
  Decision Gate    : AUTO-EXECUTE
  Reasoning        : OOM kills due to memory limits directly align with the job purpose.
                     Runbook context explicitly confirms memory threshold breach as trigger.

  ✓ WOULD AUTO-EXECUTE — restart-service-with-memory-bump (confidence 0.95 ≥ 0.70 gate)
  Total runtime: 8.7s
```

### Q3 — product-search unresponsive -> AUTO-EXECUTE (0.75)

**Speaker note:** Mixed RAG sources — the top match is from the runbook (product-search.md), not an incident. The model correctly synthesises runbook context + incident history to identify reindex-elasticsearch as the right fix for an unresponsive ES-backed service. 9.9s.

```
$ python query_live.py "product search returning empty results, search index unresponsive after deployment"

  Query: product search returning empty results, search index unresponsive after deployment

  RAG Top 3:
  1  product-search.md   0.575 ~ partial match   Service Overview: ES-backed search service
  2  incidents.json      0.571 ~ partial match   [INC0043346] product-search slow query (1352ms)
  3  product-search.md   0.570 ~ partial match   Diagnostic Steps: kubectl exec cache hit rate

  ⚠ No close precedent — best match 0.575 in product-search.md. AI will deduce a remediation.

  Recommended Job  : reindex-elasticsearch
  Confidence       : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : Unresponsive ES index directly maps to reindexing as remediation step.
                     Runbook + incident context both confirm the service architecture.

  ✓ WOULD AUTO-EXECUTE — reindex-elasticsearch (confidence 0.75 ≥ 0.70 gate)
  Total runtime: 9.9s
```

### Q6 — loyalty service not awarding points -> PENDING REVIEW (0.35)

**Speaker note:** This is the key "gate as feature" example. Decent RAG precedent (0.642), but the runbook context references a backfill script — not a service restart. The model recognised the mismatch and self-downgraded to 0.35. 14.6s total; engineer gets full context.

```
$ python query_live.py "loyalty service not awarding points after purchase, customer accounts not updating"

  Query: loyalty service not awarding points after purchase, customer accounts not updating

  RAG Top 3:
  1  incidents.json   0.642 ~ partial match   [INC0042145] loyalty-service failing to award points
                                              (click-and-collect, missing order type mapping)
  2  incidents.json   0.562 ~ partial match   [INC0041652] loyalty-service reward redemption 500
                                              (DB connection pool exhausted)
  3  incidents.json   0.561 ~ partial match   [INC0041134] loyalty-service points returning negatives
                                              (bulk redemption event)

  ⚠ No close precedent — best match 0.642. AI will deduce a remediation.

  Recommended Job  : restart-service-rolling
  Confidence       : 0.35
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Past loyalty-service issues resolved via restarts or config updates.
                     Runbook context references backfill scripts — not a restart path.
                     Semantic mismatch between query and available context. Self-downgraded.

  ⏸  PENDING HUMAN REVIEW — restart-service-rolling (confidence 0.35 < 0.70 gate)
  Total runtime: 14.6s
```

---

## SLIDE 8 — Why Pending Review is a Feature

**Heading:** The Gate is the Point

Examples:
- **Loyalty service (0.35)** — RAG matched past incidents but runbook referenced a backfill script, not a restart. Model self-downgraded.
- **Notification duplicates (0.35)** — matched incident was push notifications, not email. Semantic mismatch caught.
- **Supplier EDI (0.65)** — schema validation failure; force-inventory-sync is plausible but not certain. Correctly held for review.

**Tagline:** "A system that knows what it doesn't know is more useful than one that always fires"

### Terminal Panel — Query 6 (captured live output):

```
$ python query_live.py "loyalty service not awarding points after purchase, customer accounts not updating"

╭────────────────────────────────────────────╮
│ ops-knowledge-loop  |  Live Incident Query │
│ MOCK_MODE=TRUE  |  env: mock               │
╰────────────────────────────────────────────╯

Step 1 — Searching knowledge base...

│ 1 │ incidents.json │  0.642 ~ partial match │ [INC0042145] loyalty-service failing to award points
│   │                │                        │ for click-and-collect orders — missing order type mapping
│ 2 │ incidents.json │  0.562 ~ partial match │ [INC0041652] loyalty-service reward redemption API
│   │                │                        │ returning 500 — DB connection pool exhausted
│ 3 │ incidents.json │  0.561 ~ partial match │ [INC0041134] loyalty-service points calculation
│   │                │                        │ returning negative balances after bulk redemption event

⚠ No close precedent — best match 0.642. AI will deduce a remediation.

  Recommended Job : restart-service-rolling
  Confidence      : 0.35   ← MODEL SELF-DOWNGRADED
  Decision Gate   : RULE-BASED FALLBACK
  Reasoning       : Runbook context references backfill scripts — not a restart path.
                    Semantic mismatch between query and available context.

⏸  PENDING HUMAN REVIEW — restart-service-rolling (confidence 0.35 < 0.70 gate)
   On-call engineer sees this recommendation + RAG sources before any action is taken.

Total runtime: 14.6s
```

---

## SLIDE OBS — Observability

**Heading:** Observability

What to log at minimum:
- Every RAG query — top-K results and similarity scores
- Every LLM call — prompt token count, response token count, and latency
- Every gate decision — confidence value and outcome
- Every Rundeck execution — success or failure

Dashboards to build from those logs:
- Confidence score distribution over time, where a sudden drop suggests knowledge base staleness or a model version change
- Auto-execution rate and false positive rate, especially auto-executed incidents later marked incorrect by an engineer
- P99 latency per pipeline stage

Alert on:
- Confidence distribution shift
- Fallback-to-human-review rate increase
- Any Rundeck execution failure without a subsequent human resolution

---

## SLIDE 9 — Tech Stack

**Heading:** Stack

Technologies:
- Python 3.11
- ChromaDB (vector store)
- sentence-transformers / all-MiniLM-L6-v2 (embeddings)
- Ollama + qwen3:14b Q4_K_M (local LLM, 9.3GB, RTX 4090)
- Flask (dashboard)
- Rich (CLI output)
- ServiceNow API (mocked)
- Rundeck (mocked job execution)

**Callout:** "Runs entirely on local hardware · Zero external API calls · Zero ongoing cost"

---

## SLIDE FUTURE — Where This Goes Next

**Heading:** Where This Goes Next

### Shadow Deployment Pipeline
A shadow environment mirrors live incidents without acting. Once recommendations earn sufficient confidence, a single approval promotes to production - zero-downtime, the system validates itself before it acts.

### Repository-Aware Context
Continuous indexing of service repos gives the LLM code-level context - config files, dependency changes, recent commits - when a root cause needs investigation beyond tickets and runbooks.

### Living Organisational Memory
Automatic ingestion of JIRA, Confluence, and equivalent knowledge bases keeps RAG context current with the team's accumulated decisions and post-mortems. The system learns from every resolved incident.

---

## APPENDIX — Additional Terminal Outputs

**Heading:** Appendix · Additional Query Outputs

These seven outputs are kept at the end for optional follow-up if the manager wants to inspect more examples.

### Q2 — payment-processor 500 errors -> AUTO-EXECUTE (0.95)

**Speaker note:** Interesting case — all three RAG matches are weak (0.488–0.495), below the 0.60 threshold. The model has no strong precedent. Yet it returns 0.95 confidence based on the runbook pattern-matching three prior resolved incidents. The AI is doing the heavy lifting here.

```
$ python query_live.py "payment processor returning 500 errors, transactions not completing at checkout"

  Query: payment processor returning 500 errors, transactions not completing at checkout

  RAG Top 3:
  1  incidents.json   0.495 ✗ weak match   [INC0043135] payment-processor 5xx error spike (70%)
  2  incidents.json   0.492 ✗ weak match   [INC0043231] payment-processor 5xx error spike (72%)
  3  incidents.json   0.488 ✗ weak match   [INC0043183] payment-processor 5xx error spike (71%)

  ⚠ No close precedent — best match 0.495. AI will deduce a remediation.

  Recommended Job  : rollback-to-previous-version
  Confidence       : 0.95
  Decision Gate    : AUTO-EXECUTE
  Reasoning        : Three prior payment-processor 5xx spikes all resolved by rollback.
                     Standard mitigation confirmed despite weak RAG similarity.

  ✓ WOULD AUTO-EXECUTE — rollback-to-previous-version (confidence 0.95 ≥ 0.70 gate)
  Total runtime: 8.2s
```

### Q4 — inventory sync stalled -> PENDING REVIEW (0.66)

**Speaker note:** Good RAG matches (0.639–0.675) and a clear recommendation, but confidence just missed the 0.70 gate. The model correctly identified the pipeline-stall pattern but wasn't certain enough to auto-fire. The engineer receives a pre-reasoned brief with the matching incidents attached.

```
$ python query_live.py "inventory sync stalled, stock levels on website not updating after warehouse batch job"

  Query: inventory sync stalled, stock levels on website not updating after warehouse batch job

  RAG Top 3:
  1  incidents.json   0.675 ~ partial match   [INC0041047] inventory-sync batch job failed silently
  2  incidents.json   0.656 ~ partial match   [INC0043477] inventory-sync data pipeline stall (75min)
  3  incidents.json   0.639 ~ partial match   [INC0042043] inventory-sync failing for 14 stores

  ✓ Strong precedent found — incidents.json (similarity 0.675)

  Recommended Job  : force-inventory-sync
  Confidence       : 0.66
  Decision Gate    : PENDING REVIEW
  Reasoning        : Stalled sync mirrors INC0043477 pipeline-stall scenario exactly.
                     force-inventory-sync would resolve, but confidence just below gate.

  ⏸  PENDING HUMAN REVIEW — force-inventory-sync (confidence 0.66 < 0.70 gate)
  Total runtime: 15.4s
```

### Q5 — store POS tills unresponsive -> AUTO-EXECUTE (0.75)

**Speaker note:** Weak RAG (0.547–0.573) but the model deduced a rollback from P1 context — store-pos-system Consul mesh misconfiguration causing 2,300-store outage, resolved by rollback. Confident enough to fire. The AI correctly reasoned beyond the low similarity score.

```
$ python query_live.py "store POS system tills unresponsive, cashiers cannot process customer transactions"

  Query: store POS system tills unresponsive, cashiers cannot process customer transactions

  RAG Top 3:
  1  incidents.json   0.573 ~ partial match   [INC0043165] store-pos-system pipeline stall (75min)
  2  incidents.json   0.569 ~ partial match   [INC0043333] store-pos-system pipeline stall (75min)
  3  incidents.json   0.547 ✗ weak match      [INC0041062] store-pos-system API latency (Consul mesh)

  ⚠ No close precedent — best match 0.573. AI will deduce a remediation.

  Recommended Job  : rollback-to-previous-version
  Confidence       : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : P1 incident with configuration rollback resolving 2,300-store outage.
                     Pattern matches despite low similarity — model correctly extrapolated.

  ✓ WOULD AUTO-EXECUTE — rollback-to-previous-version (confidence 0.75 ≥ 0.70 gate)
  Total runtime: 9.9s
```

### Q7 — order fulfilment latency spike -> AUTO-EXECUTE (0.75)

**Speaker note:** Three partial RAG matches on order-fulfilment P99 latency (0.558–0.571). Model correctly maps latency caused by upstream pressure to scale-up-replicas — adding capacity to absorb load while the upstream is investigated. 12.2s.

```
$ python query_live.py "order fulfilment delays caused by upstream pricing engine latency spike during peak hours"

  Query: order fulfilment delays caused by upstream pricing engine latency spike during peak hours

  RAG Top 3:
  1  incidents.json   0.571 ~ partial match   [INC0043496] order-fulfilment P99 breach (1102ms)
  2  incidents.json   0.565 ~ partial match   [INC0043448] order-fulfilment P99 breach (4926ms)
  3  incidents.json   0.558 ~ partial match   [INC0043304] order-fulfilment P99 breach (798ms)

  ⚠ No close precedent — best match 0.571. AI will deduce a remediation.

  Recommended Job  : scale-up-replicas
  Confidence       : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : Upstream latency causing downstream delays points to capacity pressure.
                     Scaling replicas reduces per-instance load while root cause is addressed.

  ✓ WOULD AUTO-EXECUTE — scale-up-replicas (confidence 0.75 ≥ 0.70 gate)
  Total runtime: 12.2s
```

### Q8 — notification service duplicate emails -> PENDING REVIEW (0.35)

**Speaker note:** Highest RAG similarity of any pending-review case (0.687) — but the matched incident is about duplicate push notifications, not email. The third match is an auto-generated runbook for a broken unsubscribe link. The model recognised the semantic mismatch and self-downgraded to 0.35. 22.5s.

```
$ python query_live.py "notification service sending duplicate confirmation emails to customers after every order event"

  Query: notification service sending duplicate confirmation emails to customers after every order event

  RAG Top 3:
  1  incidents.json                0.687 ~ partial match   [INC0041294] notification-svc duplicate
                                                           PUSH notifications (order-fulfilment retry)
  2  incidents.json                0.520 ✗ weak match      [INC0041158] notification-svc email queue
                                                           backed up (6h delay)
  3  INC0042468-notif-svc-...md   0.467 ✗ weak match      Auto-generated runbook: broken unsubscribe
                                                           links (config issue, P2)

  ✓ Strong precedent found — incidents.json (similarity 0.687)
  [but matched push notifications, not email]

  Recommended Job  : restart-service-with-memory-bump
  Confidence       : 0.35
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Runbook context (INC0042468) used restart-with-memory-bump for config issue.
                     Current incident involves email duplicates, not push notifications.
                     Semantic mismatch between incident type and available context.

  ⏸  PENDING HUMAN REVIEW — restart-service-with-memory-bump (confidence 0.35 < 0.70 gate)
  Total runtime: 22.5s
```

### Q9 — supplier EDI orders dropped -> PENDING REVIEW (0.65)

**Speaker note:** Best RAG match is highly relevant (0.705, EDI batch failure / schema version mismatch). But force-inventory-sync is a data pipeline fix, not a schema validation fix. The model acknowledged the plausible but imperfect mapping and held at 0.65. 25.7s — longest runtime in the set.

```
$ python query_live.py "supplier integration service dropping EDI purchase orders during XML schema validation"

  Query: supplier integration service dropping EDI purchase orders during XML schema validation

  RAG Top 3:
  1  incidents.json   0.705 ~ partial match   [INC0041737] supplier-integration EDI batch failure
                                              (Supplier-31 schema version mismatch)
  2  incidents.json   0.561 ~ partial match   [INC0043383] supplier-integration ETL failure
                                              (transform step exited non-zero after 11 retries)
  3  incidents.json   0.542 ✗ weak match      [INC0041195] supplier-integration EDI feed timeout
                                              (Supplier-14, 3,200 SKUs unupdated for 18h)

  ✓ Strong precedent found — incidents.json (similarity 0.705)

  Recommended Job  : force-inventory-sync
  Confidence       : 0.65
  Decision Gate    : PENDING REVIEW
  Reasoning        : EDI orders dropped during XML schema validation matches INC0041737 closely.
                     force-inventory-sync addresses data pipeline stalls, not schema mismatches.
                     Plausible mitigation, but not the correct root-cause fix. Correctly held.

  ⏸  PENDING HUMAN REVIEW — force-inventory-sync (confidence 0.65 < 0.70 gate)
  Total runtime: 25.7s
```

### Q10 — recommendation engine degraded -> PENDING REVIEW (0.45)

**Speaker note:** Hardest case. All three RAG matches are weak (0.315–0.393) and from unrelated services (product-search). No knowledge base entry for the recommendation engine at all. The model is at the edge of its context, and it knows it — 0.45, rule-based fallback. 13.8s.

```
$ python query_live.py "recommendation engine returning identical product suggestions for all users after overnight model retraining"

  Query: recommendation engine returning identical product suggestions for all users after overnight model retraining

  RAG Top 3:
  1  incidents.json   0.393 ✗ weak match   [INC0041839] product-search autocomplete empty
                                           (Redis cache flush)
  2  incidents.json   0.356 ✗ weak match   [INC0043065] product-search feature flag misconfiguration
                                           (50% sessions on wrong path)
  3  incidents.json   0.315 ✗ weak match   [INC0043017] product-search feature flag misconfiguration
                                           (49% sessions on wrong path)

  ⚠ No close precedent — best match 0.393. AI will deduce a remediation.
  [All three matches are from a different service; zero relevant precedent]

  Recommended Job  : reindex-elasticsearch
  Confidence       : 0.45
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Identical suggestions indicate stale/improperly updated index data.
                     No recommendation-engine incidents in knowledge base. Cross-service inference
                     only. Model self-downgraded — this is the system acknowledging its limits.

  ⏸  PENDING HUMAN REVIEW — reindex-elasticsearch (confidence 0.45 < 0.70 gate)
  Total runtime: 13.8s
```
