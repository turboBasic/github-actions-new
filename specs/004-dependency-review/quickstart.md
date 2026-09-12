# Quickstart: validating the dependency-review capability

Two halves. The first runs offline and is what CI runs; the second needs a real pull request, because a
published advisory is not something the suite may reach for (FR-023).

## Prerequisites

```console
mise run setup
```

## Offline: everything CI judges

```console
mise run ci
```

Passes with no network access (SC-001). What each part is asserting about this feature:

| Command | Holds |
| --- | --- |
| `mise run lint` | actionlint and zizmor over both new workflows; the schema hook that refuses a job with no timeout; cspell over the new prose |
| `mise run typecheck` | pyright strict over the new reader and the new gates |
| `mise run test` | every gate below |

### The gates to watch, and what each one is for

```console
uv run pytest tests/test_published_surface.py tests/test_workflow_properties.py \
              tests/test_ruleset_contexts.py tests/test_names.py tests/test_action_pins.py -v
```

- `test_every_capability_in_the_tree_is_in_the_fixture` — the capability and its row arrive together.
- `test_every_permission_demand_matches_the_fixture` — the demand is `contents: read` and stays it
  (SC-004).
- `test_every_event_conditional_job_appears_in_the_skip_table_with_a_reason` — the `pull_request` pin is
  registered with its reason, so principle VII's gate admits it with no exemption (SC-005).
- `test_composed_contexts_finds_the_contexts_the_tree_actually_reports` — `guard / dependency-review` is
  the context the tree really reports.
- `test_a_context_the_tree_composes_but_does_not_require_causes_no_failure` — it is composed and absent
  from the required set (SC-008).
- the new gates named in [data-model.md](data-model.md#the-gates), each beside the check that plants its
  violation.

### Prove each new gate can fail

A gate that has never been seen red is a gate nobody has read. Break one thing, run the suite, revert:

| Edit | Expected failure |
| --- | --- |
| add `comment-summary-in-pr: always` to the action's `with:` | the input gate, naming the permission every caller would then have to grant |
| add an `actions/checkout` step to the capability | the `uses:` gate, naming why the difference is read from the API |
| delete the diagnostic step | the diagnostic gate, saying a run that read nothing would fail with the API's own refusal |
| raise the permission to `pull-requests: write` | the surface gate, naming the demand and the record it disagrees with |
| drop `default: low` from the input | the description-and-default gate |
| remove `dependency-guard.yml` from `[tool.turbobasic-release].exclude` | the release-surface gate, naming the caller counted as consumer surface |
| rename the `graph-off` step's id | the diagnostic gate, naming the step it looked for — not a green run over a missing diagnostic |
| add `guard / dependency-review` to the committed ruleset | nothing — it judges, so it is required-eligible; FR-020 is a maintainer's choice, and the composed-but-not-required gate is what records it |

That last row is the one worth reading twice: the suite does not refuse a maintainer who later decides to
require this context. It records that today's tree does not.

## Online: the capability actually judging

Nothing here is automated and nothing here is in `mise run ci`.

### The failing case (Scenario 1.1, SC-003)

1. In a repository whose dependency graph is on, add the call site from the README.
2. Open a pull request adding a dependency version carrying a known advisory at or above `low`.
3. Expected: the check reddens, and the run's log and job summary name the advisory, the package and the
   version.

### The passing cases (Scenarios 1.2, 1.3)

- The same pull request moved to a version with no advisory → the check passes.
- A pull request touching no dependency manifest → the check passes, having read an empty difference. The
  log says `No Dependency Changes found`.

### The floor (Scenario 1.4)

At the default floor there is nothing below it — `low` is the lowest severity there is. To see a finding
inform rather than fail, pass `fail-on-severity: high` and open a pull request whose only finding is
`moderate`: the check passes and the finding appears in the job summary.

### Adoption cost (Story 2, SC-002)

Copy the call site unchanged, grant `contents: read`, change nothing else, fill in no value. The run
starts and the check reports. Granting nothing at all is the case worth trying once: the run fails before
any job exists, with no log and no annotation — which is why the demand is published rather than
discovered.

### The dependency graph switched off (Scenario 3.3, SC-007)

In a repository with the dependency graph off, open any pull request that calls the capability. Expected:
the run fails carrying two annotations — the action's own, naming the setting and its
`settings/security_analysis` path, and this capability's, saying it cannot switch it on for you. A
maintainer learns what to change without opening this repository.

### This repository as its own consumer (Story 4, SC-008)

Open any pull request here. Expected: `guard / dependency-review` appears in the check list, reports, and
is absent from the required set — so an upstream advisory nobody has triaged does not block a merge.
