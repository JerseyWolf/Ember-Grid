# INC0042536 — payment-processor (P2)

> Auto-generated runbook. Source: resolved ServiceNow incident.
> Generated: 2026-05-11 21:11 UTC

## Service Overview

`payment-processor` in namespace `prod-uk`. See
[`knowledge-base/runbooks/payment-processor.md`](../runbooks/payment-processor.md) for the
canonical service-level runbook. This document captures one specific
incident and its resolution so future searches can surface it.

## Incident Summary

- Number: `INC0042536`
- Priority: P2
- Service / namespace: `payment-processor` / `prod-uk`
- Tags: payment, pci, audit-log, cloudsql, disk-full, compliance

**Short description:** payment-processor audit log writes failing — CloudSQL disk at 95% capacity

**Full description:**

Payment-processor PCI audit log writes to CloudSQL began failing at 22:00 on May 10th due to the database disk reaching 95% capacity. The disk has been growing steadily since the audit log retention policy was changed from 90 days to 365 days in February without a corresponding disk resize. PCI compliance requires audit logs to be written successfully — current state is a compliance risk.

## Common Failure Modes

This incident matches the failure pattern below. Future occurrences with
similar symptoms should be tried against the same remediation first.

- Symptom seen here: payment-processor audit log writes failing — CloudSQL disk at 95% capacity
- Likely class: see `knowledge-base/runbooks/payment-processor.md` for the family.

## Diagnostic Steps

SECTION A — Diagnostic Steps

1. Check current disk usage of CloudSQL instance:
   ```bash
   kubectl exec -it <cloudsql-pod> -- df -h /var/lib/mysql
   ```

2. Verify the audit log retention policy:
   ```bash
   kubectl get configmap payment-processor-config -n prod-uk -o yaml | grep audit-log-retention
   ```

3. Check recent logs for disk-related errors:
   ```bash
   kubectl logs <payment-processor-pod> -n prod-uk --since=1h | grep -i disk
   ```

4. Inspect the Rundeck job 'restart-service-with-memory-bump' execution history:
   ```bash
   rundeck-cli job list-executions --jobId=<job-id>
   ```

5. Validate the current disk capacity and usage trend over time:
   ```bash
   kubectl exec -it <cloudsql-pod> -- cat /var/lib/mysql/ibdata1 | wc -c
   ```

## Remediation Steps

1. Auto-remediation via Rundeck job 'restart-service-with-memory-bump'. Confidence 0.85. The job 'restart-service-with-memory-bump' is suitable for this incident as it can help address potential memory issues that might be causing the audit log writes to fail due to disk space constraints. The runbook context mentions a growing disk usage and suggests checking disk usage, which aligns with the diagnostic steps in the runbook.

Re-run the diagnostic steps above after remediation to confirm recovery.

## Escalation Path

Follow the escalation path in
[`knowledge-base/runbooks/payment-processor.md`](../runbooks/payment-processor.md). For
this incident class, the primary on-call team for `payment-processor` is the
first responder.

## Post-Incident Checklist

- [ ] Service is healthy in all production namespaces.
- [ ] No related ServiceNow incidents open.
- [ ] Prevention items below have been triaged into the team's backlog.

## Prevention Notes

SECTION B — Prevention Notes

1. Implement automated alerting for CloudSQL disk usage above 80% to proactively address capacity issues.

2. Review and update the audit log retention policy regularly, ensuring that corresponding disk resizing is performed as needed.

3. Schedule regular maintenance windows to perform disk resizing and other resource management tasks.
