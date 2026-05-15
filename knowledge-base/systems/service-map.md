# Ember Grid Service Map

Operational map of the services that the `ops-knowledge-loop` pipeline
routinely touches. Sorted by criticality tier, then alphabetically.

| Service              | Namespace(s)                         | Owning team           | Criticality | Rundeck job prefix              | On-call rotation             |
| -------------------- | ------------------------------------ | --------------------- | ----------- | ------------------------------- | -----------------------------|
| checkout-service     | prod-eu-west, prod-uk, prod-eu-central | checkout-platform    | tier-0      | `restart-service-`, `scale-up-`, `rollback-to-`, `clear-redis-`  | checkout-platform-primary    |
| payment-processor    | prod-eu-west, prod-uk, prod-eu-central | payments-platform    | tier-0      | `rotate-service-`, `restart-service-`, `trigger-circuit-`        | payments-primary + security  |
| store-pos-system     | prod-eu-west, prod-uk, prod-eu-central | retail-systems       | tier-0      | `restart-service-`, `force-consul-`, `drain-and-cordon-`         | retail-systems-primary       |
| order-fulfilment     | prod-eu-west, prod-uk                | fulfilment-platform   | tier-0      | `restart-service-`, `trigger-manual-fulfilment-`, `rollback-to-` | fulfilment-primary           |
| product-search       | prod-eu-west, prod-uk                | search-platform       | tier-1      | `reindex-`, `clear-search-`, `restart-service-`                  | search-platform-primary      |
| inventory-sync       | prod-eu-west                         | data-platform-team    | tier-1      | `force-inventory-`, `restart-sync-`, `clear-sync-`               | data-platform-primary        |
| pricing-engine       | prod-eu-west, prod-uk                | pricing-platform      | tier-1      | `restart-service-`, `rollback-to-`                               | pricing-primary              |
| notification-service | prod-eu-west, prod-uk                | comms-platform        | tier-2      | `restart-service-`, `clear-queue-`                               | comms-primary                |
| recommendations      | prod-eu-west, prod-uk                | data-science-platform | tier-2      | `restart-service-`, `rebuild-model-`                             | data-science-primary         |
| auth-service         | prod-eu-west, prod-uk, prod-eu-central | identity-platform    | tier-0      | `rotate-service-`, `restart-service-rolling`                     | identity-primary + security  |
| specialty-retail-pos | prod-uk, prod-eu-west           | retail-systems       | tier-1      | `restart-service-`, `apply-resource-limits-`              | retail-systems-primary       |
| product-configurator-api | prod-uk, prod-eu-west       | retail-systems       | tier-2      | `restart-service-`, `rollback-to-`                         | retail-systems-primary       |

## How to Read This Map

- **Criticality `tier-0`** services have direct customer-visible impact
  when they degrade. Auto-remediation is allowed only at high confidence
  (≥ 0.70) and only via low-risk Rundeck jobs. Anything destructive
  (drain a node, rotate credentials, rollback) must clear an even higher
  bar; the per-job confidence thresholds in
  [`rundeck_jobs.json`](../../mock_data/rundeck_jobs.json) reflect that.
- **`prefix`** columns list the families of Rundeck jobs commonly run
  against the service. The full catalogue is in
  [`rundeck_jobs.json`](../../mock_data/rundeck_jobs.json).
- **On-call rotation** is the PagerDuty schedule name. For PCI-touching
  services (`payment-processor`, `auth-service`) the security on-call is
  paged automatically alongside the primary.

## Notable Cross-Service Dependencies

- `checkout-service` → `payment-processor` (mTLS-only) → Stripe / internal gateway
- `checkout-service` → `pricing-engine` (cart enrichment; the most common
  source of breaking-change incidents into checkout)
- `product-search` → Elasticsearch cluster (independent of GKE service
  failures — but Elasticsearch RED is an incident in its own right)
- everything → `auth-service` (token validation hot path)
- `store-pos-system` → `inventory-sync`'s cache (read-only) — this is why
  a silent inventory-sync failure is felt by the tills before anyone
  else notices.

## Updating This Map

When a new tier-0 service is added, update this file and re-run
`python rag/populate_database.py` so the RAG index reflects the new
ownership and on-call data before repopulating the vector store.
