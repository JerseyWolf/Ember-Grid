# policies — OPA-as-PR-gate for Ember Grid repos

This directory holds the OPA (Rego) policies that gate every pull
request in any Ember Grid repo subscribed to the `ops-knowledge-loop`
governance layer. Three rules, deliberately narrow.

## Routing Table

| Task | Read | Skip | Notes |
|------|------|------|-------|
| Add a new deny rule | `pr_rules.rego` | — | Append a new `deny` rule; tests live alongside. |
| Investigate a failing PR check | `pr_rules.rego` + `.github/workflows/pr-policy-check.yml` | — | The workflow comments deny messages on the PR. |
| Loosen a rule for a specific path | `pr_rules.rego` | — | Add a `not startswith(...)` branch — review carefully. |

## Entry Point

OPA runs in CI. To reproduce locally:

    opa eval --input input.json --data policies/pr_rules.rego \
        "data.ember_grid.pr.deny"

## Inputs

- `input.commits[_].message` — commit messages
- `input.files[_].filename` and `.patch` — changed files and their diffs
- `input.pull_request.body` — the PR description text

## Outputs

- Array of human-readable deny messages. Non-empty = PR check fails.

## Demo Talking Point

"Three Rego rules: every commit message must match
`[component] description — reasoning`; every pipeline-code change must
reference `MOCK_MODE`; every runbook edit must cite an `INC*` number.
Self-documenting governance, enforced in CI, not by tribal knowledge."
