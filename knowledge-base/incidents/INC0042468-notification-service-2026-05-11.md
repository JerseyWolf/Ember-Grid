# INC0042468 — notification-service (P2)

> Auto-generated runbook. Source: resolved ServiceNow incident.
> Generated: 2026-05-11 21:11 UTC

## Service Overview

`notification-service` in namespace `prod-eu-west`. See
[`knowledge-base/runbooks/notification-service.md`](../runbooks/notification-service.md) for the
canonical service-level runbook. This document captures one specific
incident and its resolution so future searches can surface it.

## Incident Summary

- Number: `INC0042468`
- Priority: P2
- Service / namespace: `notification-service` / `prod-eu-west`
- Tags: notification, email, unsubscribe, gdpr, broken-link, compliance

**Short description:** notification-service unsubscribe links broken in email templates after base URL change

**Full description:**

Following a domain configuration change, notification-service email templates were not updated with the new base URL. All email unsubscribe links in order confirmations, loyalty emails, and promotional messages are pointing to a 404 page. Compliance risk: broken unsubscribe links violate GDPR email requirements. Volume: approximately 120,000 emails sent since the URL change 4 days ago.

## Common Failure Modes

This incident matches the failure pattern below. Future occurrences with
similar symptoms should be tried against the same remediation first.

- Symptom seen here: notification-service unsubscribe links broken in email templates after base URL change
- Likely class: see `knowledge-base/runbooks/notification-service.md` for the family.

## Diagnostic Steps

SECTION A — Diagnostic Steps

1. `kubectl get pods -n prod-eu-west | grep notification-service`
2. `kubectl logs <pod-name> -n prod-eu-west | grep unsubscribe`
3. `curl -I http://<new-base-url>/unsubscribe`
4. `kubectl describe configmap notification-config -n prod-eu-west`
5. `kubectl get svc notification-service -n prod-eu-west`

## Remediation Steps

1. Auto-remediation via Rundeck job 'restart-service-with-memory-bump'. Confidence 0.85. The job 'restart-service-with-memory-bump' is suitable for this incident as it involves restarting services, which could help in updating the configuration and resolving issues related to broken unsubscribe links. The runbook context mentions that the issue might be due to a domain configuration change not being reflected in the email templates, suggesting a potential need for a service restart to apply the new settings.

Re-run the diagnostic steps above after remediation to confirm recovery.

## Escalation Path

Follow the escalation path in
[`knowledge-base/runbooks/notification-service.md`](../runbooks/notification-service.md). For
this incident class, the primary on-call team for `notification-service` is the
first responder.

## Post-Incident Checklist

- [ ] Service is healthy in all production namespaces.
- [ ] No related ServiceNow incidents open.
- [ ] Prevention items below have been triaged into the team's backlog.

## Prevention Notes

SECTION B — Prevention Notes

1. **Implement automated alerting for configuration changes**: Set up alerts to notify the on-call team when domain configurations are updated, ensuring that all relevant services and templates are promptly reviewed.
2. **Regularly validate email template updates**: Schedule a weekly or bi-weekly task to manually verify that all email templates in the `notification-service` namespace are correctly updated with the latest base URL.
3. **Increase capacity for configuration management**: Ensure that the configuration management system has sufficient resources and automation capabilities to handle domain changes efficiently, reducing the likelihood of human error during updates.
