# product-search — Runbook

## Service Overview

`product-search` is the Elasticsearch-backed search service that powers every
product query across Ember Grid's website and mobile apps. A typical day sees
12–18 million queries against an index of ~3.2 million SKUs across
electronics, home goods, furniture and tools. The index is rebuilt from the
canonical product catalog every six hours; a full rebuild takes around 40
minutes during which search returns stale results — this is expected
behaviour, not a bug.

- **GKE namespaces:** `prod-eu-west`, `prod-uk` (active/active)
- **Team owner:** `search-platform` (slack: `#search-platform`)
- **On-call rotation:** `search-platform-primary`
- **Tech stack:** Java 17 service / Elasticsearch 8.13 cluster
  (5 data nodes per region) / Redis result cache
- **Critical SLO:** p99 latency < 250ms, error rate < 0.5%, results
  freshness < 6 hours

## Common Failure Modes

1. **False-positive alerts during scheduled index rebuilds.** This is the
   most common operational confusion. During a rebuild, p95 query latency
   climbs from ~80ms to ~180ms and a small percentage of queries return
   slightly stale documents. Monitoring fires `freshness drift` alerts
   even though everything is operating exactly to spec. The fix is to
   *not* alarm during the known rebuild windows.

2. **Cache invalidation thrash after a price change.** When Pricing
   pushes a large bulk update, every affected SKU's cached search-result
   payload is invalidated at once. The result cache hit rate drops from
   ~92% to ~40% for 5–15 minutes; the underlying Elasticsearch cluster
   spikes in CPU; queries get slower but do not fail.

3. **Elasticsearch shard relocation under load.** During a node restart
   or scaling event, shards relocate while serving production traffic.
   Search results can return inconsistent counts as relocated shards
   come back online. Symptom: faceted-search counts wobble.

4. **Index corruption from a bad ingest payload.** Rare, but when it
   happens it is silent until users notice obviously wrong results for
   common queries (e.g. "laptop" returning furniture). Requires a full
   reindex.

5. **Result-cache memory pressure.** The Redis result cache occasionally
   hits memory pressure during heavy promotional windows, evicting hot
   keys and causing latency spikes that look like Elasticsearch problems
   but are actually upstream cache misses.

## Diagnostic Steps

1. **First and most important:** check the scheduled-rebuild calendar
   before alarming. Rebuilds run at 00:00, 06:00, 12:00, 18:00 UTC:

       kubectl get cronjob -n prod-uk -l app=product-search-reindex
       kubectl get jobs   -n prod-uk -l app=product-search-reindex \
         --sort-by=.status.startTime | tail -5

2. Confirm Elasticsearch cluster health:

       kubectl exec -n prod-uk deploy/product-search -- \
         curl -fsS http://elasticsearch:9200/_cluster/health | jq .

3. Check cache hit rate:

       kubectl exec -n prod-uk deploy/product-search -- \
         curl -fsS http://localhost:9090/metrics | grep cache_hit_ratio

4. Sample a known-good query and confirm a sane result:

       kubectl exec -n prod-uk deploy/product-search -- \
         curl -fsS 'http://localhost:8080/search?q=wireless+headphones&limit=3' \
         | jq '.results | length'

5. Inspect the result cache for memory pressure:

       kubectl exec -n prod-uk deploy/redis-search-cache -- \
         redis-cli INFO memory | grep used_memory_human

6. Check Dynatrace for any correlated `pricing-engine` bulk-update
   events.

## Remediation Steps

1. **If alerts are firing during a known rebuild window**, do nothing —
   acknowledge the alert with a note pointing at the rebuild job ID.

2. **If the cache is thrashing after a pricing event**, the cleanest
   intervention is to flush the cache and let it warm with fresh data:

       Rundeck job: `clear-search-cache`
       Parameters:  cache_name=search-results, namespace=prod-uk

3. **If results are wrong (index corruption) and customers are
   reporting**, kick off a full reindex. This is a 40-minute job and is
   medium-risk — during the rebuild, results will be stale:

       Rundeck job: `reindex-elasticsearch`
       Parameters:  index=products, source=canonical-catalog,
                    mode=full, expected_duration_minutes=40

4. **If the service itself is wedged or unresponsive but Elasticsearch
   is healthy**, do a rolling restart:

       Rundeck job: `restart-service-rolling`
       Parameters:  service_name=product-search, namespace=prod-uk

## Escalation Path

- **Within 15 min for sustained latency > p99 1s or error rate > 2%:**
  page `search-platform-primary`.
- **If Elasticsearch cluster is RED (not YELLOW):** also page
  `elasticsearch-platform-on-call`. Cluster state recovery is theirs.
- **If a reindex is in flight and being blamed wrongly:** loop in
  `data-platform-team` who own the canonical catalog ingest.
- **Customer-visible wrong results:** notify `web-customer-experience`
  so they can decide whether to put up a banner.

## Post-Incident Checklist

- [ ] Elasticsearch cluster `status: green`.
- [ ] Cache hit rate back above 85%.
- [ ] p99 query latency back under 250ms for at least 30 minutes.
- [ ] Sample queries return expected results (use the canonical regression
      list: `laptop`, `office chair`, `kettle`, `hdmi cable`).
- [ ] If a reindex was triggered, confirm completion and freshness < 1h.
- [ ] If the incident was actually a false positive from a scheduled
      rebuild, update the alerting rules to suppress during known windows.
- [ ] Auto-generated runbook in `knowledge-base/incidents/` is committed.
