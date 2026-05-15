# inventory-sync — Runbook

## Service Overview

`inventory-sync` is the bridge between Ember Grid's GKE microservice estate and
the legacy IBM AS/400 warehouse system that remains the system of record for
stock levels. It runs as a batch CronJob, not a long-lived service. Twice a
day it pulls the current state of stock from the AS/400 and writes it to the
GKE-side inventory cache used by `product-search`, `checkout-service` and
the in-store POS terminals.

- **GKE namespace:** `prod-eu-west` (single namespace by design — the AS/400
  link is bound to one network egress)
- **Team owner:** `data-platform-team` (slack: `#data-platform`)
- **On-call rotation:** `data-platform-primary`
- **Tech stack:** Python 3.11 / CronJob on GKE / DB2 client library / SFTP
  fallback channel for the worst case
- **Schedule:** 02:00 UTC and 14:00 UTC daily
- **Critical input:** AS/400 IP allowlist must include the egress NAT IPs
- **Typical run duration:** 8–12 minutes for a full sync, ~3 minutes incremental

## Common Failure Modes

1. **Silent zero-record write.** The sync job exits 0 because the AS/400
   connection succeeded for the handshake but the result-set returned zero
   rows (because the AS/400 was mid-maintenance or had locked the source
   table). With no validation, the inventory cache is overwritten with an
   empty set. Stores show wildly wrong stock numbers within hours. This is
   the single most expensive failure mode for retail trading. Prevention is
   record-count validation in the job itself.

2. **AS/400 maintenance window overrun.** The AS/400 has a nightly
   maintenance window that occasionally runs over and collides with the
   02:00 sync. The job times out connecting; cache is not updated; next
   morning's stock levels are stale by hours.

3. **AS/400 schema drift.** Warehouse team adds a new column to a source
   table without coordinating. The Python sync job throws `KeyError` on
   the missing-column lookup. Symptom: job exits non-zero, alert fires.
   This is the *good* failure mode — loud, not silent.

4. **GKE-side cache (Redis) write failure.** Source pull succeeded, but the
   write to Redis fails mid-stream. Partial writes leave the cache in a
   half-fresh, half-stale state. Symptom: a small percentage of SKUs show
   the wrong stock level.

5. **DNS resolution failure to internal AS/400 hostname.** Rare but
   recurring after subnet reconfigurations.

## Diagnostic Steps

1. Find the most recent sync job and its status:

       kubectl get jobs -n prod-eu-west -l app=inventory-sync \
         --sort-by=.status.startTime | tail -5

2. Confirm exit code and look for the magic line `wrote N records to cache`:

       kubectl logs -n prod-eu-west job/inventory-sync-<timestamp> --tail=200 \
         | grep -E 'wrote|ERROR|TIMEOUT|connection'

3. Compare the record count to the previous successful run:

       kubectl logs -n prod-eu-west job/inventory-sync-<timestamp> \
         | grep 'wrote .* records to cache'

4. Probe AS/400 reachability from inside the cluster:

       kubectl run -n prod-eu-west as400-probe --rm -i --tty \
         --image=registry.ember-grid.internal/utils/db2-client \
         --restart=Never -- db2 connect to AS400PROD

5. Check Redis-side stock cache freshness for a known-good SKU:

       kubectl exec -n prod-eu-west deploy/inventory-cache -- \
         redis-cli HGET stock:sku:DECK-COMPOSITE-001 last_updated

6. Confirm whether the AS/400 maintenance window overran by checking the
   warehouse team's status channel `#warehouse-as400-status`.

## Remediation Steps

1. **If the last sync wrote zero or near-zero records and the AS/400 is
   now reachable**, kick off a manual sync immediately — this is the
   standard fix for the most common failure:

       Rundeck job: `force-inventory-sync`
       Parameters:  source=as400, mode=full, validation=strict

2. **If the sync service itself is wedged**, restart it cleanly:

       Rundeck job: `restart-sync-service`
       Parameters:  service_name=inventory-sync, namespace=prod-eu-west

3. **If the inventory cache itself is corrupt (partial writes)**, clear it
   before re-syncing so we do not leave stale fragments mixed with fresh
   data:

       Rundeck job: `clear-sync-cache`
       Parameters:  cache_name=inventory-cache, namespace=prod-eu-west

       Then re-run:

       Rundeck job: `force-inventory-sync`
       Parameters:  source=as400, mode=full, validation=strict

## Escalation Path

- **Within 30 min of detection:** `data-platform-primary`.
- **If AS/400 is the blocker:** engage `warehouse-systems-team` via
  Slack `#warehouse-systems`. They own the AS/400 maintenance schedule.
- **If stock levels are visibly wrong in-store (POS staff reporting):**
  page `retail-trading-on-call`; product pages may need to be soft-
  unlisted to prevent over-selling. Revenue impact decisions are theirs,
  not ours.
- **Negative stock shown anywhere:** automatic P1.

## Post-Incident Checklist

- [ ] Last successful sync wrote a non-zero, plausible number of records
      (compare against last 7 days' average).
- [ ] No in-store POS terminals reporting impossible stock values.
- [ ] AS/400 maintenance window times reviewed and our sync schedule
      adjusted if there is a recurring collision.
- [ ] If the silent-zero-records failure occurred, confirm the validation
      gate (fails the job if fewer than 100 records written) is enabled.
- [ ] Auto-generated runbook for this incident exists in
      `knowledge-base/incidents/` and is committed.
