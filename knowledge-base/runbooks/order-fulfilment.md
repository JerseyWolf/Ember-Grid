# order-fulfilment — Runbook

## Service Overview

`order-fulfilment` integrates Ember Grid's checkout flow with three external
fulfilment partners: a national parcel carrier, a heavy-goods palletised
carrier, and a same-day local delivery partner. Each partner is contacted
over an idempotent webhook contract. **This service has a sharp edge:
its retry logic has produced duplicate physical shipments on two
historical occasions.** Webhook failures from partners must NOT trigger
automatic retries without a human in the loop.

- **GKE namespaces:** `prod-eu-west`, `prod-uk`
- **Team owner:** `fulfilment-platform` (slack: `#fulfilment-platform`)
- **On-call rotation:** `fulfilment-primary` (DAYTIME-WEIGHTED — incidents
  here are deliberately not auto-resolved out of hours, see below)
- **Tech stack:** Node 20 / TypeScript / Kafka consumer for inbound orders
  / outbound webhooks to partners / Postgres for order state
- **Critical SLO:** order-to-dispatch < 90 seconds for 99% of orders,
  no duplicates ever

## Common Failure Modes

1. **Partner webhook returns 500/timeout, our retry policy fires.** The
   partner often *did* receive the order on the failed call and recorded
   it. Our retry then submits the same order again. Result: duplicate
   shipment, duplicate charge to Ember Grid, customer receives two
   identical pallets of stock. This has happened twice and both times
   were expensive. The rule is: **retries on webhook failures require
   human review**, not autonomous remediation.

2. **Idempotency key collision.** The partner contract uses an
   idempotency key per order. If two distinct orders accidentally share
   a key (almost always due to a clock-skew issue on a worker pod),
   the partner rejects the second one as a duplicate. Symptom: orders
   marked dispatched on our side that never arrive.

3. **Kafka consumer lag building.** When the inbound orders topic backs
   up, dispatch latency climbs. This is a slow-burn problem that becomes
   a customer-experience issue around the 5-minute lag mark.

4. **Partner schema change without notice.** Partners occasionally change
   their webhook expected payload (e.g. a required new tracking field).
   Our calls 400; orders stack up unsent.

5. **Outbound network egress to partner saturated.** During Black Friday-
   scale events, our egress NAT can be saturated and webhooks to one
   partner time out preferentially.

## Diagnostic Steps

1. Confirm the symptom — is it duplicates (catastrophic) or missing
   dispatches (expensive but recoverable)?

       kubectl logs -n prod-uk -l app=order-fulfilment --tail=500 \
         | grep -E 'duplicate|retry|idempotency'

2. Inspect Kafka consumer lag — this is the most common signal:

       kubectl exec -n prod-uk deploy/order-fulfilment -- \
         kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
         --describe --group order-fulfilment-consumer

3. Look at the partner-specific failure rate:

       kubectl logs -n prod-uk -l app=order-fulfilment --tail=500 \
         | grep 'partner=' | awk -F'partner=' '{print $2}' \
         | awk '{print $1}' | sort | uniq -c

4. Confirm none of our worker pods has a clock drift:

       kubectl exec -n prod-uk deploy/order-fulfilment -- \
         date -u +%s
       date -u +%s   # compare against your own host

5. Probe each partner's webhook health endpoint (if they provide one;
   only carrier-1 currently does):

       kubectl run -n prod-uk fulfil-probe --rm -i --tty \
         --image=curlimages/curl --restart=Never -- \
         curl -fsS https://carrier-1.partner.example.com/health

6. Pull the last 50 failed-dispatch records from Postgres to see the
   distribution of errors:

       kubectl exec -n prod-uk deploy/order-fulfilment -- \
         psql -c "SELECT partner, error_code, COUNT(*) \
                  FROM dispatches WHERE state='failed' \
                  AND created_at > now() - interval '1 hour' \
                  GROUP BY 1,2 ORDER BY 3 DESC LIMIT 50;"

## Remediation Steps

> Important: every Rundeck job for `order-fulfilment` is configured with a
> higher confidence threshold than usual, and the `trigger-manual-fulfilment-retry`
> job specifically requires human review. This is by design — see the duplicate-
> shipment failure mode above.

1. **For Kafka consumer lag without dispatch failures**, a rolling
   restart of the consumers usually clears it. This is the safest first
   action:

       Rundeck job: `restart-service-rolling`
       Parameters:  service_name=order-fulfilment, namespace=prod-uk

2. **For partner-specific failures (one partner is degraded)**, do NOT
   trigger retries automatically. Open a comms thread with the partner
   first. If the partner has confirmed they did NOT receive the original
   call, you may then trigger a controlled retry of the queued orders.
   This requires explicit operator approval:

       Rundeck job: `trigger-manual-fulfilment-retry`
       Parameters:  partner=<carrier-name>, start_time=<ISO>, end_time=<ISO>
       Approval:    REQUIRED (human review)

3. **If a recently deployed change introduced the failure mode**, roll
   back rather than chase the bug live. Duplicates are too expensive to
   risk:

       Rundeck job: `rollback-to-previous-version`
       Parameters:  service_name=order-fulfilment, namespace=prod-uk

## Escalation Path

- **Any duplicate shipment, ever:** automatic P1; page
  `fulfilment-primary` AND the fulfilment-platform lead AND
  `finance-on-call` (because of partner billing).
- **Partner-side outage:** open a partner comms thread immediately. The
  contact list lives in `fulfilment-platform` Confluence space.
- **Backlog of unsent orders > 30 minutes:** notify
  `retail-customer-care` so they can begin proactive customer comms.
- **Cross-region failure (both prod-uk and prod-eu-west affected
  simultaneously):** treat as platform-level; engage
  `platform-eng-on-call`.

## Post-Incident Checklist

- [ ] All consumers caught up on Kafka lag (< 30 seconds).
- [ ] Dispatch success rate back above 99% for 30 minutes.
- [ ] **No duplicate shipments confirmed** (reconcile by idempotency
      key across our DB and the partner's confirmation receipts).
- [ ] If a manual retry was triggered, document the operator and the
      partner confirmation thread in the incident notes.
- [ ] If duplicates did occur, file the customer-impact report with
      `retail-customer-care` and the partner-billing reconciliation
      with `finance-on-call`.
- [ ] Auto-generated runbook in `knowledge-base/incidents/` is committed
      and explicitly captures the duplicate-shipment risk if relevant.
