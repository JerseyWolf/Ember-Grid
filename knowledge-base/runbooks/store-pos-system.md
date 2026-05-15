# store-pos-system — Runbook

## Service Overview

`store-pos-system` is the REST API that serves Ember Grid's in-store
point-of-sale terminals. Every till in every store talks to this service
through the Consul service mesh. Any degradation here affects *every*
terminal in the affected region at the same time — there is no per-terminal
isolation. That blast radius makes this service one of the small handful
classified as `criticality: tier-0` on the service map.

- **GKE namespaces:** `prod-eu-west`, `prod-uk`, `prod-eu-central` (regional)
- **Team owner:** `retail-systems` (slack: `#retail-systems-oncall`)
- **On-call rotation:** `retail-systems-primary` with mandatory
  `store-operations-on-call` shadow for any P1
- **Tech stack:** Java 17 / Spring Boot / Consul service registry /
  Postgres for transaction logs
- **Service mesh:** Consul — terminals discover the service via Consul DNS,
  so health-check de-registration is what actually takes us out, not pod
  failure
- **Critical SLO:** p99 latency < 400ms, availability > 99.95% during
  trading hours (08:00–22:00 local)

## Common Failure Modes

1. **Consul health check de-registration after restart.** This is the
   default failure mode after any pod restart. Pods come back healthy on
   the Kubernetes side but Consul does not re-register the health check
   in time, and terminals continue routing to the now-dead old endpoint.
   Symptom: terminals fail with `connection refused` even though
   `kubectl get pods` shows everything `Ready`.

2. **Bad node in the pool affecting all terminals in a store.** When a
   single GKE node has a flaky NIC or kernel issue, all pods scheduled
   to it serve degraded traffic. Because the mesh routes by region,
   one node can pollute traffic for an entire region's stores at once.

3. **Postgres transaction-log write contention.** During end-of-day
   reconciliation runs, the transaction-log Postgres can lock for
   minutes. Terminals see writes time out; staff cannot process refunds
   or returns.

4. **Time-skew between terminals and the service.** Surprisingly common.
   In-store terminals run on hardware time; if NTP drifts more than 5
   minutes, signed payloads fail validation. Symptom: only some stores
   affected, geographically clustered.

5. **TLS cert pinned at terminal level expires.** Hardware terminals
   pin our service certificate; quarterly rotation needs a coordinated
   field update. Missed rotations cause cliff-edge outages.

## Diagnostic Steps

1. Confirm Kubernetes pod state and look for recent restarts:

       kubectl get pods -n prod-uk -l app=store-pos-system
       kubectl describe pod -n prod-uk -l app=store-pos-system \
         | grep -A2 'Last State'

2. Check Consul registration — this is the single most useful check:

       consul catalog services -node-meta=region=prod-uk \
         | grep store-pos-system
       consul health checks store-pos-system

3. From inside the cluster, hit the service the same way terminals do:

       kubectl run -n prod-uk pos-probe --rm -i --tty \
         --image=curlimages/curl --restart=Never -- \
         curl -fsS http://store-pos-system.service.consul/healthz

4. Identify any single GKE node concentrating the pods (blast radius
   check):

       kubectl get pods -n prod-uk -l app=store-pos-system \
         -o wide | awk '{print $7}' | sort | uniq -c

5. Check Postgres lock waits:

       kubectl exec -n prod-uk deploy/pos-postgres-proxy -- \
         psql -c "SELECT pid, state, wait_event FROM pg_stat_activity \
                  WHERE wait_event_type='Lock';"

6. Spot-check store-side connectivity via the
   `#retail-systems-oncall` Slack channel — store staff frequently report
   regional outages faster than monitoring detects them.

## Remediation Steps

1. **Most cases — restart the service rolling so pods cleanly re-register
   with Consul**:

       Rundeck job: `restart-service-rolling`
       Parameters:  service_name=store-pos-system, namespace=prod-uk

2. **If Consul health checks did NOT come back after a restart**, force
   re-registration explicitly (this is the canonical fix for the most
   common failure mode):

       Rundeck job: `force-consul-reregister`
       Parameters:  service_name=store-pos-system, namespace=prod-uk

3. **If a single node is degrading traffic for a region**, drain and
   cordon it so the scheduler rebalances pods off it. This is high-risk
   (it takes a node out of service) so the confidence gate is set high
   on the corresponding Rundeck job:

       Rundeck job: `drain-and-cordon-node`
       Parameters:  node_name=<from diagnostic step 4>, force=false

4. **If recently deployed and errors started immediately after**, roll
   back:

       Rundeck job: `rollback-to-previous-version`
       Parameters:  service_name=store-pos-system, namespace=prod-uk

## Escalation Path

- **Within 5 minutes of regional outage:** page `retail-systems-primary`
  AND notify `store-operations-on-call`. They own the comms to store
  managers.
- **Within 10 minutes if still degraded:** open the trading bridge and
  notify the on-call director. Regional POS outages have direct revenue
  impact (~£60–£90k per minute UK-wide during peak trading).
- **If multiple regions are affected:** treat as a platform-wide event;
  page `platform-eng-on-call` to confirm it is not a Consul-cluster issue.
- **Hardware terminal cert pinning issue:** field engineering team
  (`field-engineering-uk`) — they own the in-store hardware.

## Post-Incident Checklist

- [ ] All `store-pos-system` pods Ready in affected namespace.
- [ ] Consul `serfHealth` and the custom HTTP health check both passing
      for every instance.
- [ ] Synthetic probe from inside the cluster returns 200.
- [ ] Sample of 5 stores reports tills operational (via
      `store-operations-on-call`).
- [ ] If a node was drained, confirm it has been replaced or recovered
      before the next trading day.
- [ ] Auto-generated runbook for this incident is committed to
      `knowledge-base/incidents/`.
