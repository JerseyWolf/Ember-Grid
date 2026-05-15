# payment-processor — Runbook

## Service Overview

`payment-processor` mediates between Ember Grid's checkout flow and two payment
backends: Stripe (external) and Ember Grid's internal payment gateway used for
PayPoint, gift cards and store credit. It enforces PCI DSS scope, so every
function in this service is treated as PCI-touching.

- **GKE namespaces:** `prod-eu-west`, `prod-uk`, `prod-eu-central` (active in all three)
- **Team owner:** `payments-platform` (slack: `#payments-oncall`)
- **On-call rotation:** PagerDuty `payments-primary` + mandatory
  `security-oncall` secondary for any P1
- **Tech stack:** Go 1.21 / gRPC / Vault for secret material / mTLS via Istio
- **Critical SLO:** p99 latency < 1.2s end-to-end, auth-success > 99.5%
- **PCI scope:** YES. Any authentication-related failure is automatically P1.

## Common Failure Modes

1. **OAuth token expiry against internal payment gateway.** The single most
   dangerous failure mode because it can be silent: the gateway returns
   `200 OK` with an error body that older client versions parsed as a
   successful authorisation. The fix is to rotate the token and re-issue
   credentials. Look for the pattern: success rate flat but
   `payment_failure_unknown` counter climbing.

2. **Stripe upstream latency or outage.** Confirmed by checking Stripe's
   status page. Symptoms are p99 latency climbing past 3 seconds while
   error rates stay low (Stripe just goes slow before it fails). Trigger
   the circuit breaker to fail fast and route to internal gateway only.

3. **mTLS certificate rotation drift.** Istio rotates mesh certs every
   24 hours; if a sidecar misses the rotation window, the service returns
   `503 upstream connect error` for inbound calls from `checkout-service`.

4. **Database connection pool exhaustion.** During refund storms (e.g.
   after a faulty bulk-pricing change), the connection pool to the
   PCI-scoped Postgres saturates. Symptom: `pgx pool exhausted` in logs,
   request queue depth alerts firing.

5. **Vault sidecar unable to refresh secret lease.** Vault agent fails to
   renew leases on the payment-gateway secret; existing connections keep
   working briefly then everything 503s at once.

## Diagnostic Steps

1. Check whether this is upstream (Stripe) or us:

       curl -fsS https://status.stripe.com/api/v2/status.json | jq .status.indicator

2. Look for auth-related errors in the last 15 minutes:

       kubectl logs -n prod-uk -l app=payment-processor --tail=500 --since=15m \
         | grep -E 'auth|token|401|403|503' | tail -50

3. Confirm pod health and check for mTLS errors:

       kubectl get pods -n prod-uk -l app=payment-processor
       kubectl logs -n prod-uk -l app=payment-processor -c istio-proxy --tail=200 \
         | grep -i 'tls\|certificate'

4. Inspect Vault sidecar health:

       kubectl exec -n prod-uk deploy/payment-processor -c vault-agent -- \
         vault token lookup -format=json | jq .data.ttl

5. Check the database connection pool depth via the service's own
   diagnostic endpoint (PCI-restricted, only reachable from a jump host):

       kubectl exec -n prod-uk deploy/payment-processor -- \
         curl -s http://localhost:9090/debug/pool | jq .

6. Pull a single failing transaction trace from Dynatrace and confirm
   whether the failure is on the Stripe span or the internal gateway span.

## Remediation Steps

1. **If OAuth tokens are expired or about to expire**, rotate immediately
   (this is the canonical PCI-safe remediation):

       Rundeck job: `rotate-service-credentials`
       Parameters:  service_name=payment-processor, namespace=prod-uk

2. **If Stripe is degraded**, trip the circuit breaker so we fail fast and
   route business through the internal gateway:

       Rundeck job: `trigger-circuit-breaker`
       Parameters:  upstream=stripe, mode=open, duration_minutes=15

3. **If mTLS errors are dominant**, rolling restart picks up rotated certs:

       Rundeck job: `restart-service-rolling`
       Parameters:  service_name=payment-processor, namespace=prod-uk

4. **If the DB connection pool is exhausted**, restart the rolling deploy
   to drop stale connections; do NOT raise pool limits without DBA sign-off
   because the PCI-scoped Postgres has a hard cap.

       Rundeck job: `restart-service-rolling`
       Parameters:  service_name=payment-processor, namespace=prod-uk

## Escalation Path

- **Immediate:** primary `payments-primary` AND `security-oncall` (PCI rule).
- **Within 5 min if revenue-affecting:** open the incident bridge.
- **Within 15 min if not resolved:** page `payments-platform` lead and
  engage Stripe support via the dedicated TAM Slack channel
  (`#stripe-ember-grid-support`).
- **Any silent-failure pattern (200s that did not actually settle):**
  this is automatically a P1, regardless of customer count. Page
  `compliance-on-call` to file the PCI incident report.

## Post-Incident Checklist

- [ ] All `payment-processor` pods `Ready` in all three production namespaces.
- [ ] Stripe and internal-gateway auth success rates both > 99.5% for 15 min.
- [ ] If credentials were rotated, confirm old token is fully revoked.
- [ ] If silent failure was involved, reconcile transaction ledger against
      Stripe and internal-gateway reports for the affected window.
- [ ] File PCI incident summary with `compliance-on-call` within 24 hours.
- [ ] Schedule the next token rotation with a 48h pre-expiry alert.
- [ ] Verify auto-generated runbook in `knowledge-base/incidents/` is committed.
