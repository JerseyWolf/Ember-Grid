# Implementation Notes — policies

## What Was Built

A single `pr_rules.rego` file under `package ember_grid.pr` with three
`deny` rules: commit message format, MOCK_MODE coverage in pipeline
code, and runbook-edit-requires-incident-reference. Paired with the
GitHub Actions workflow at `.github/workflows/pr-policy-check.yml`,
which builds the OPA input from GitHub event context, evaluates the
rules, comments deny messages on the PR, and fails the job on
non-empty deny.

## Key Design Decisions

- Decision: Use the modern Rego `deny contains msg if { ... }` syntax —
  Reason: it expresses partial sets cleanly and is the form OPA 1.x
  documentation uses. Older `deny[msg]` syntax still works but reads
  less naturally to engineers new to Rego.
- Decision: Match commit messages with a specific regex
  `^\[[a-z-]+\] .+ — .+$` — Reason: the em-dash is a deliberate
  forcing function. Engineers paste plain ASCII messages and the OPA
  check catches them; the format anomaly is itself a learning moment.
- Decision: The pipeline-code rule checks the *patch* text for the
  string `MOCK_MODE` (not the whole file) — Reason: it forces every
  change to pipeline code to *retain* or *add* the variable;
  unrelated touches that drop `MOCK_MODE` from a file accidentally
  are caught immediately.

## How It Fits the Architecture

The other half of the outer ring. While `governance/` *distributes*
the rules, `policies/` *enforces* them at PR time. Together they keep
the Ember Grid engineering culture from drifting.

## How to Extend

- To add a new data source: add a new `deny` rule with a different
  input field. The GitHub Actions workflow constructs the full input
  from the PR event so most things you might want are already
  available.
- To swap the LLM: this directory has nothing to change. OPA evaluates
  policy, never invokes a model.

## Demo Talking Points

- "Three Rego rules, all human-readable, all enforced in CI. The PR
  bot comments the rule name and the specific violation, so the
  feedback loop for a developer is seconds, not days."
- "Policy as code means the rules can be reviewed, reverted and
  tested like anything else. Loosening a rule is a pull request."

## Known Limitations (Honest)

- No unit tests for the Rego itself. The OPA `test` runner is built in
  and small `*_test.rego` files would be straightforward to add — a
  follow-up.
- The runbook-edit rule trusts the PR body. A more rigorous check
  would correlate the linked incident number against ServiceNow via a
  workflow step before the OPA eval.
