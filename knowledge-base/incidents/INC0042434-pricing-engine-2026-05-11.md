# INC0042434 — pricing-engine (P2)

> Auto-generated runbook. Source: resolved ServiceNow incident.
> Generated: 2026-05-11 21:11 UTC

## Service Overview

`pricing-engine` in namespace `prod-uk`. See
[`knowledge-base/runbooks/pricing-engine.md`](../runbooks/pricing-engine.md) for the
canonical service-level runbook. This document captures one specific
incident and its resolution so future searches can surface it.

## Incident Summary

- Number: `INC0042434`
- Priority: P2
- Service / namespace: `pricing-engine` / `prod-uk`
- Tags: pricing, promotional-schedule, rollover-bug, bank-holiday, customer-impact

**Short description:** pricing-engine prod-uk showing weekend promotional prices on Monday morning — schedule rollover bug

**Full description:**

Pricing-engine in prod-uk failed to roll off the weekend Bank Holiday promotional pricing at 00:00 on Monday. Customers shopping Monday morning continued to see Bank Holiday sale prices for 3 hours. The promotional schedule rollover job had silently failed due to a race condition in the price-schedule evaluator introduced in v4.2.1.

## Common Failure Modes

This incident matches the failure pattern below. Future occurrences with
similar symptoms should be tried against the same remediation first.

- Symptom seen here: pricing-engine prod-uk showing weekend promotional prices on Monday morning — schedule rollover bug
- Likely class: see `knowledge-base/runbooks/pricing-engine.md` for the family.

## Diagnostic Steps

SECTION A — Diagnostic Steps

1. `kubectl logs -n prod-uk pricing-engine-pod-name`
2. `curl -v http://pricing-engine-service/prod-uk/pricing-data`
3. `kubectl describe job -n prod-uk price-schedule-evaluator`

## Remediation Steps

1. Auto-remediation via Rundeck job 'restart-service-with-memory-bump'. Confidence 0.85. The incident involves a failure in a scheduled job that should have rolled off promotional prices. Restarting the service with a memory bump could help resolve any transient issues or race conditions that might be causing the problem.

Re-run the diagnostic steps above after remediation to confirm recovery.

## Escalation Path

Follow the escalation path in
[`knowledge-base/runbooks/pricing-engine.md`](../runbooks/pricing-engine.md). For
this incident class, the primary on-call team for `pricing-engine` is the
first responder.

## Post-Incident Checklist

- [ ] Service is healthy in all production namespaces.
- [ ] No related ServiceNow incidents open.
- [ ] Prevention items below have been triaged into the team's backlog.

## Prevention Notes

SECTION B — Prevention Notes

1. Implement robust alerting for scheduled jobs to notify on failures.
2. Increase capacity and resources during peak times to reduce the likelihood of race conditions.
3. Schedule maintenance windows for critical updates and ensure that all dependent services are tested before deployment.
