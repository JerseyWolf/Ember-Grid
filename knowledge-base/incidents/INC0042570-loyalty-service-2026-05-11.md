# INC0042570 — loyalty-service (P2)

> Auto-generated runbook. Source: resolved ServiceNow incident.
> Generated: 2026-05-11 21:11 UTC

## Service Overview

`loyalty-service` in namespace `prod-uk`. See
[`knowledge-base/runbooks/loyalty-service.md`](../runbooks/loyalty-service.md) for the
canonical service-level runbook. This document captures one specific
incident and its resolution so future searches can surface it.

## Incident Summary

- Number: `INC0042570`
- Priority: P2
- Service / namespace: `loyalty-service` / `prod-uk`
- Tags: loyalty, audit-log, logging, gdpr, compliance, misconfiguration

**Short description:** loyalty-service audit trail missing for 3,200 point redemption transactions — logging misconfiguration

**Full description:**

Loyalty-service audit logging for point redemption events was silently disabled for 72 hours following a logging library configuration change that set the audit log level to OFF for the redemption event handler class. 3,200 transactions are unaudited. GDPR and internal compliance requirements mandate full audit trails for loyalty financial transactions.

## Common Failure Modes

This incident matches the failure pattern below. Future occurrences with
similar symptoms should be tried against the same remediation first.

- Symptom seen here: loyalty-service audit trail missing for 3,200 point redemption transactions — logging misconfiguration
- Likely class: see `knowledge-base/runbooks/loyalty-service.md` for the family.

## Diagnostic Steps

SECTION A — Diagnostic Steps

1. `kubectl logs <loyalty-service-pod-name> -n prod-uk` - Check the logs of the loyalty-service pod to confirm if the audit log level is set to OFF.
2. `curl -X GET "http://<loyalty-service-endpoint>/audit-log-level" -H "accept: application/json"` - Use a curl command to check the current audit log level configured in the service.
3. `kubectl describe deployment loyalty-service -n prod-uk` - Review the deployment details to understand if there are any recent changes or misconfigurations that could have caused this issue.

## Remediation Steps

1. Auto-remediation via Rundeck job 'rotate-service-credentials'. Confidence 0.85. The runbook context mentions a logging misconfiguration that may have affected service credentials, making 'rotate-service-credentials' the most relevant job for this incident.

Re-run the diagnostic steps above after remediation to confirm recovery.

## Escalation Path

Follow the escalation path in
[`knowledge-base/runbooks/loyalty-service.md`](../runbooks/loyalty-service.md). For
this incident class, the primary on-call team for `loyalty-service` is the
first responder.

## Post-Incident Checklist

- [ ] Service is healthy in all production namespaces.
- [ ] No related ServiceNow incidents open.
- [ ] Prevention items below have been triaged into the team's backlog.

## Prevention Notes

SECTION B — Prevention Notes

1. **Implement Robust Alerting**: Set up alerts for changes in logging levels and configurations within critical services. This will help detect such issues promptly.
2. **Regular Capacity Checks**: Ensure that the logging infrastructure can handle the expected load of audit logs. Regularly review and optimize logging resources to prevent similar issues.
3. **Validation and Review Processes**: Implement a rigorous code review process for any changes related to logging configurations. Automated tests should be run to validate that changes do not inadvertently disable critical logging features.
