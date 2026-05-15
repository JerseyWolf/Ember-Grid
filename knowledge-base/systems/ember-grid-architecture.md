# Ember Grid Platform Architecture

This document is a high-level map of Ember Grid's operational
platform: where services run, how they discover one another, how code gets
to production and what we look at when something is on fire.

## Cluster Layout

All production workloads run on Google Kubernetes Engine (GKE) across four
clusters. Each cluster is regional, with a single control plane and node
pools spread across three zones.

| Cluster          | Purpose                                    | Approx. node count |
| ---------------- | ------------------------------------------ | -------------------|
| `prod-eu-west`   | Primary EU traffic, EU-fronted CDN origin  | ~220 nodes         |
| `prod-eu-central`| Secondary EU traffic, warm standby for UK  | ~110 nodes         |
| `prod-uk`        | UK retail traffic, in-store POS backend    | ~180 nodes         |
| `staging`        | Pre-production validation, load testing    | ~40 nodes          |

Each cluster runs ~850 microservices in total. About 40 of them are classified
business-critical (`tier-0`): a sustained degradation of any single one of
them has direct customer-visible impact. The service map in
[`service-map.md`](./service-map.md) lists which services those are.

## Service Discovery and Traffic

Two complementary meshes live on top of the cluster:

- **Consul** for service discovery and health-check-driven routing. In-store
  point-of-sale terminals discover backend services via Consul DNS, which is
  why de-registration after a pod restart can take terminals offline even
  when Kubernetes thinks the service is healthy. See
  [`store-pos-system.md`](../runbooks/store-pos-system.md) for the recovery
  pattern.
- **Istio** for east-west traffic management and mTLS between services. mTLS
  certificate rotation runs automatically every 24 hours; sidecars that miss
  the rotation window are the most common cause of `503 upstream connect
  error` events.

External ingress uses Google Cloud Load Balancer in front of NGINX ingress
controllers.

## CI/CD Pipeline

The pipeline is intentionally split across three tools rather than collapsed
into one. Each tool does the thing it is best at:

- **Jenkins** runs the build pipelines themselves: compile, unit tests,
  image build, image push to Artifact Registry. Most teams have a
  `Jenkinsfile` at the repo root with a small set of declarative stages.
- **GitHub Actions** runs PR-time checks: linting, OPA policy evaluation
  (see [`policies/pr_rules.rego`](../../policies/pr_rules.rego)), unit
  test coverage gate, and the Copilot governance audit.
- **Harness** runs the actual deployments. Harness templates encode the
  per-service rollout strategy (rolling, canary, blue/green) and the
  per-environment approval gates.

Rollbacks are first-class. Every deployment pipeline emits a Harness
artifact version that can be rolled back via a single Rundeck job
(`rollback-to-previous-version`), which is what most of the runbooks
in this knowledge base reference.

## Job Execution

**Rundeck** is the operational hand. Anything that *changes the state of
production*, whether triggered by a human or by this very `ops-knowledge-loop`,
flows through a Rundeck job. Rundeck gives us RBAC, scheduling, audit logs
and a clean ServiceNow integration that closes the loop on incident records.

The Rundeck job catalogue is mirrored to the repo in
[`mock_data/rundeck_jobs.json`](../../mock_data/rundeck_jobs.json) for
demonstration purposes. The same shape is what the real Rundeck API
returns when `MOCK_MODE=false`.

## Observability

- **Dynatrace** is the primary APM. Every service has the Dynatrace OneAgent
  injected via a Kubernetes admission controller. Problem cards in Dynatrace
  are the first place an on-call engineer looks.
- **GCP Cloud Monitoring** holds the infrastructure layer: GKE node health,
  network metrics, NAT egress saturation, BigQuery dataset freshness, etc.
- **Custom DORA pipeline** computes the four DORA metrics (MTTR, change
  failure rate, deployment frequency, lead time) from a join over Harness
  deployment events and ServiceNow incident records. The pipeline runs
  hourly and writes to a BigQuery table that the operations dashboard in
  [`dashboard/`](../../dashboard/) reads from.
- **ServiceNow** is the incident system of record. The pipeline in
  [`incident_pipeline/`](../../incident_pipeline/) reads from it, writes
  remediation back to it, and closes resolved incidents through its REST
  table API.

## Legacy Boundary

Not everything is on Kubernetes. The single most important legacy system
is the **IBM AS/400 warehouse system**, which remains the system of record
for stock levels and warehouse movements. The
[`inventory-sync`](../runbooks/inventory-sync.md) service is the only
piece of the platform that talks to it. Every other service reads stock
from the GKE-side inventory cache that `inventory-sync` writes to. Any
incident touching stock levels is, almost without exception, a synthesis
incident across this legacy boundary.

## Service Counts at a Glance

- ~850 microservices across all clusters.
- ~40 are `tier-0` (business-critical).
- ~120 are `tier-1` (significant customer or operations impact).
- The remainder are internal-only or batch components.

Most of the operational pain — and most of this knowledge base — focuses
on the `tier-0` set, where incidents have direct revenue impact during
trading hours.
