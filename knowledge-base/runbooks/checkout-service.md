# checkout-service — Runbook

## Service Overview

`checkout-service` owns Ember Grid's cart state, multi-step checkout flow and the
final order-submission handshake with `payment-processor` and `order-fulfilment`.
It is a Java 17 Spring Boot service running on GKE.

- **GKE namespaces:** `prod-eu-west`, `prod-uk` (active/active), `prod-eu-central` (warm standby)
- **Team owner:** `checkout-platform` (slack: `#checkout-oncall`)
- **On-call rotation:** PagerDuty schedule `checkout-platform-primary`
- **Tech stack:** Java 17 / Spring Boot 3.2 / Redis (session store) / Kafka (order events)
- **Critical SLO:** p99 latency < 800ms, error rate < 0.1% over rolling 5 minutes
- **Memory limits:** 512Mi request / 768Mi limit (deliberately conservative — see Failure Mode 1)
- **HPA:** min 3, max 12 replicas per namespace; CPU target 60%

## Failure Signatures

1. **OOM kills under load**: checkout-service pods hitting memory limits and being OOM-killed during traffic spikes or promotional events.
2. **Redis session-store latency**: session-store slowness causing checkout hang; p99 climbing above 2 s.
3. **Pricing-engine schema break**: NullPointerException in CartEnricher after a pricing-engine deployment.
4. **Kafka producer backpressure**: orders completing in the UI but not appearing downstream.
5. **mTLS certificate expiry**: 503s on the final payment step only; all other checkout steps healthy.

## Common Failure Modes

1. **OOM-killed during promotional events.** The single most common cause of
   `checkout-service` page-outs. Promotional traffic does not necessarily mean
   *more* requests — it means *heavier* requests. The `pricing-engine` injects
   bundled product recommendations into the cart session payload, which can
   triple the size of the per-session object (typical ~280KB → ~820KB). Memory
   limits at 512Mi/768Mi are sized for steady-state traffic and tip over within
   minutes. Symptom: pods cycle, `kubectl get pods -n prod-eu-west` shows
   `OOMKilled` in `lastState`, 502s spike on the ingress.

2. **Redis session-store latency spikes.** When the shared `redis-checkout`
   cluster slows down (network event, AZ degradation, or another tenant), every
   checkout step appears to hang for the customer. Symptom: p99 latency climbs
   past 2 seconds while error rate stays low. Dynatrace shows the slow span on
   `RedisCommands.get`.

3. **Stale deployment after pricing-engine breaking change.** `pricing-engine`
   occasionally ships a payload schema change without coordinating. Checkout
   silently 500s on a NullPointerException in `CartEnricher`. Symptom: sharp
   error-rate climb starting within minutes of a `pricing-engine` deploy.

4. **Kafka producer back-pressure on order events.** When the order-events
   Kafka cluster is degraded, the checkout's order submission step blocks.
   Symptom: orders complete in the UI but never appear downstream; alerts
   from `order-fulfilment` about missing events.

5. **TLS certificate rotation gap.** Internal mTLS cert for the
   `payment-processor` mesh route expires; checkout starts returning 503 on
   the final pay-now step only.

## Diagnostic Steps

1. Confirm scope and namespace:

       kubectl get pods -n prod-eu-west -l app=checkout-service
       kubectl get pods -n prod-uk      -l app=checkout-service

2. Look for `OOMKilled` in pod history:

       kubectl get pods -n prod-eu-west -l app=checkout-service \
         -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].lastState.terminated.reason}{"\n"}{end}'

3. Inspect recent restart logs (look for `OutOfMemoryError`,
   `NullPointerException`, or `RedisCommandTimeoutException`):

       kubectl logs -n prod-eu-west -l app=checkout-service --tail=200 --previous

4. Probe the ingress directly to distinguish network from application issues:

       curl -fsS -o /dev/null -w '%{http_code} %{time_total}\n' \
         https://checkout.prod-eu-west.ember-grid.internal/healthz

5. Check Redis session store health from a sidecar:

       kubectl exec -n prod-eu-west deploy/checkout-service -- \
         redis-cli -h redis-checkout PING

6. Check Dynatrace for problem cards tagged `checkout-service` in the last
   30 minutes. Look for correlated `pricing-engine` deploy events.

## Remediation Steps

1. **If OOMKilled and there is an active promotion**, run the memory-bump
   restart — this temporarily lifts the limit to 1.5Gi and bumps HPA min
   to 6 replicas. This is the standard promo fix:

       Rundeck job: `restart-service-with-memory-bump`
       Parameters:  service_name=checkout-service, namespace=prod-eu-west, memory_limit=1.5Gi

2. **If pods are healthy but latency is climbing**, scale out first while
   investigating Redis:

       Rundeck job: `scale-up-replicas`
       Parameters:  service_name=checkout-service, namespace=prod-eu-west, replicas=8

3. **If errors started immediately after a `pricing-engine` deploy**, roll
   back checkout to the last known-good image rather than chasing the
   incompatibility live:

       Rundeck job: `rollback-to-previous-version`
       Parameters:  service_name=checkout-service, namespace=prod-eu-west

4. **If Redis session store is slow but reachable**, clear the Redis cache
   to drop expired sessions and reduce working-set size:

       Rundeck job: `clear-redis-cache`
       Parameters:  cache_name=checkout-sessions

## Escalation Path

- **0–10 min:** primary on-call from `checkout-platform-primary`.
- **10–20 min:** if not converging, page secondary and engage `redis-platform`
  if Redis is in the picture, or `pricing-engine` on-call if a deploy correlates.
- **20+ min during promo:** open a comms bridge with retail-trading; revenue
  impact is approximately £4,000–£5,000 per minute on a UK promo.
- **PCI-touching path (final submission to `payment-processor`):** auto-page
  `security-oncall` if errors persist > 5 minutes on that span.

## Post-Incident Checklist

- [ ] All `checkout-service` pods `Ready` in all production namespaces.
- [ ] p99 latency back under 800ms for at least 10 minutes.
- [ ] Error rate back under 0.1% for at least 10 minutes.
- [ ] If memory limit was temporarily raised, file a follow-up ticket to
      either keep the change or revert it within 7 days.
- [ ] If HPA min was raised for a promo, schedule a revert for after the
      promotion window ends.
- [ ] Add the incident number, root cause and Rundeck job used to the
      auto-generated runbook in `knowledge-base/incidents/`.
- [ ] Confirm `order-fulfilment` has no orphaned events in flight.
