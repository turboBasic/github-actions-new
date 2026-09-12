# Data model: the artefacts this feature adds and moves

There is no application and no store. The entities are files, and the relationships between them are
what the suite reads. Each entity below names the file that owns it, so nothing here is a second copy
of a fact the tree holds.

## The capability

`.github/workflows/dependency-review.yml`, new.

| Property | Value | Held by |
| --- | --- | --- |
| Workflow name | `🧩 dependency-review` | `tests/test_names.py` |
| Trigger | `workflow_call`, and nothing else | `is_call_only`, via the name gate |
| Job id and name | `dependency-review` | `tests/test_names.py` |
| Event handled | `pull_request`; the job's `if:` pins it | fixture `skips_under` + the skip gate |
| Declared inputs | exactly `fail-on-severity`, `type: string`, `default: low` | `tests/published_surface.toml` |
| Permission demand | `contents: read`, with its reason on the line | surface gate + the reason gate |
| Timeout | a literal on the job; no input | the timeout gates + the schema hook |
| Steps | the pinned action, then one diagnostic gated on failure | the new gates below |

The `permissions:` block is at job level only, and workflow level is `{}` — the shape `python-ci`
already uses, so a caller reading the diff sees the whole demand in one place.

## The published third-party action

One step, `id: review`:

```yaml
uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0
with:
  fail-on-severity: ${{ inputs.fail-on-severity }}
```

`with:` carries that key and no other. Every other input the action declares stays unset, so the
action's defaults are the policy: no licence lists, no denied packages, no allowed advisories, and
`comment-summary-in-pr` left at `never`.

## The diagnostic step

Gated on `failure() && steps.review.outputs.dependency-changes == ''` — a failure in which the
comparison was never read. Its `run:` block interpolates nothing and emits one `::error::` naming the
setting, the path a consumer changes it at (built from `$GITHUB_SERVER_URL` and `$GITHUB_REPOSITORY`),
and that this capability cannot switch it on for them.

## The caller in this repository

`.github/workflows/dependency-guard.yml`, new. `🌜 dependency-guard`, triggered on `pull_request`, its
own concurrency group, workflow-level `permissions: {}`, one job:

| Property | Value |
| --- | --- |
| Job id | `guard` |
| Permission | `contents: read`, with its reason |
| `uses:` | `$/.github/workflows/dependency-review.yml` — no ref, resolved at the commit under review |
| Composed context | `guard / dependency-review` |

## The published surface record

`tests/published_surface.toml` gains one table. It is the first capability to arrive since the record
existed, so this row is also the record's first use as what a new capability must arrive with:

```toml
[dependency-review]
kind = "workflow"
published = true
check_name = ["dependency-review"]
inputs = ["fail-on-severity"]
permissions = { contents = "read" }
tool_prerequisites = []

[[dependency-review.skips_under]]
jobs = ["dependency-review"]
event = "any event but pull_request"
reason = "…"
```

`judges` is absent, which means true: this capability's job reddens on a finding at or above the floor,
unlike `prek-advisory` and `pr-description`. That is what makes the composed context required-eligible
under `pull_request` — and this repository still does not require it.

## The committed branch ruleset

`.github/rulesets/protect-default-branch.json`, unchanged. Its three required contexts stay as they
are. `guard / dependency-review` is composed and not required, and the existing gate that says a context
the tree composes but does not require is no failure is extended to name it, so the absence is asserted
rather than merely true.

## The release surface declaration

`pyproject.toml`, `[tool.turbobasic-release].exclude` gains `.github/workflows/dependency-guard.yml`,
joining the seven callers already listed. The capability itself is consumer surface and stays inside
`include`.

## The consumer-facing reference

`README.md` gains one `### dependency-review` section, positioned with the other capabilities, carrying:

- a copyable call site pinning the moving ref, granting `contents: read` and passing nothing;
- the composed context, `<your job id> / dependency-review`;
- the one event the context may be required under, and that requiring it under another gives a check
  that reports success without reading anything;
- what reddens it, against what only appears in the output — sub-floor advisories, OpenSSF Scorecard
  warnings and unlicensed dependencies — and that a licence is reported and never refused;
- that the calling repository's dependency graph has to be on, and that this capability cannot switch it
  on.

The count in the opening line goes, rather than being incremented. No table in the section names a
default; the existing README gate refuses one.

## The gates

New assertions in `tests/test_workflow_properties.py`, beside the other per-capability gates, each
paired with a check that plants the violation:

| Gate | Refuses | Requirement |
| --- | --- | --- |
| the capability's `uses:` set is one step whose slug is the action — the digest stays the workflow's | a checkout, a task-runner step | FR-002, FR-015 |
| the action is given `fail-on-severity` and no other key | the pull request comment, a licence list | FR-007, FR-008 |
| the `graph-off` step exists, is gated on failure and on an unread difference, and names the setting and the limit | an exit code as a result | FR-011, FR-024 |
| every published input carries a description and an explicit default | an input whose behaviour when unset is unwritten | FR-004 |
| the workflows excluded from the release surface are exactly the non-capabilities | a caller counted as consumer surface, silently | FR-018 |

The last one is the only gate here that holds a fact outside the capability: `[tool.turbobasic-release]`
is read at release time and nowhere else, so a caller missing from `exclude` has no symptom until it
skews a version decision. The two sets are equal today, at seven each.

Two existing assertions in `tests/test_ruleset_contexts.py` gain the new context by name: the reader
pre-flight, and the composed-but-not-required case.

One new reader in `tests/capabilities.py`, `declared_input_specs`, so the description-and-default gate
reads the workflow through the suite's existing reader rather than parsing the YAML a second time.

## What does not move

Every other capability's file, check names, input names, defaults, permission demands and skip entries.
The surface gate compares all of them on every run, so SC-006 is asserted by the suite rather than by a
reviewer.
