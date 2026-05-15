package ember_grid.pr

# Ember Grid PR policy. Three deny rules.
#
# Input shape (built by the GitHub Actions workflow):
#   input.commits[_].message       - commit message text
#   input.files[_].filename        - changed file path
#   input.files[_].patch           - the diff hunk for that file (may be empty)
#   input.pull_request.body        - the PR description text

# Rule 1 — commit message format: [word] description — reasoning
deny contains msg if {
    some i
    commit_msg := input.commits[i].message
    not regex.match(`^\[[a-z-]+\] .+ — .+$`, commit_msg)
    msg := sprintf(
        "commit message does not match `[component] description — reasoning`: %q",
        [commit_msg],
    )
}

# Rule 2 — MOCK_MODE coverage in pipeline-touching Python files
deny contains msg if {
    some i
    file := input.files[i]
    endswith(file.filename, ".py")
    is_pipeline_path(file.filename)
    not contains(file.patch, "MOCK_MODE")
    msg := sprintf(
        "%s touches pipeline code but does not reference MOCK_MODE",
        [file.filename],
    )
}

is_pipeline_path(filename) if {
    startswith(filename, "incident_pipeline/")
}

is_pipeline_path(filename) if {
    startswith(filename, "rag/")
}

# Rule 3 — runbook edits require an incident reference (INC0000000) in the PR body
deny contains msg if {
    some i
    file := input.files[i]
    startswith(file.filename, "knowledge-base/runbooks/")
    not regex.match(`INC[0-9]{7}`, input.pull_request.body)
    msg := sprintf(
        "%s is a runbook change but the PR body has no INC0000000-style reference",
        [file.filename],
    )
}
