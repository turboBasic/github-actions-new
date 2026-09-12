# Implementation Plan: One check over what a change starts depending on

**Branch**: `004-dependency-review` | **Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-dependency-review/spec.md`

## Summary

A sixth published capability: a call-only workflow that reads the dependency-graph difference between a
pull request's base and its head and reddens on an advisory at or above a severity floor. It is the only
thing in this library judging what a change starts depending on rather than what it says.

One published action does the judging — `actions/dependency-review-action`, pinned to a digest, its own
defaults left as the policy. The capability adds one input, demands one scope at read, checks nothing out,
handles one event, and adds one thing the action cannot know: that a called workflow cannot switch on its
caller's dependency graph. This repository becomes a real consumer of it at the commit under review, and
deliberately does not require the context it composes.

## Technical Context

**Language/Version**: GitHub Actions workflow YAML; Python 3.14 for the gates only

**Primary Dependencies**: `actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294`
(`v5.0.0`) — the sole runtime dependency, and the only one. The gates add none

**Storage**: N/A — `tests/published_surface.toml` is the committed surface record, not a store

**Testing**: pytest, offline. The advisory scenario is exercised by hand, per
[quickstart.md](quickstart.md)

**Target Platform**: `ubuntu-latest` GitHub-hosted runners

**Project Type**: library of reusable workflows. Nothing is published as an action

**Performance Goals**: N/A. The job is one API comparison, which is why it takes no timeout input
(FR-005) and fixes its own

**Constraints**: `contents: read` and nothing more, at every block (FR-003); no checkout and no working
tree read (FR-002); `mise run ci` never reaches the network (FR-023); no existing capability changes
(FR-017)

**Scale/Scope**: one new capability, one new caller, one fixture row, one README section, one new reader,
five new gates, two existing gates extended by name. The consumer set is indefinite and is not recorded —
compatibility is read from the surface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Re-checked after Phase 1: no
verdict changed.

| Principle | Verdict | How this design holds it |
| --- | --- | --- |
| I. One Owner Per Fact | pass | The action's defaults are the policy, so no severity table or licence list is restated here. The README carries no input list and no default — the existing README gate refuses a `Default` column. The prose count of capabilities is **deleted** rather than incremented, because a count over a list of sections is a second owner of what the sections hold |
| II. Secrets Never Persist | pass | No secret is named. `repo-token` defaults to `${{ github.token }}`, so no input carries it and nothing writes it anywhere |
| III. Gates Are Never Loosened | pass | Zero exemptions, zero exclusion-list entries, zero relaxed tool settings (SC-005). The `[tool.turbobasic-release].exclude` line is not one of these: it says a workflow is this repository's own caller rather than consumer surface, which is exactly what it says about the seven callers already listed. FR-019 gets no gate, and research.md says why adding one and then exempting `ci / python-ci` would be an exclusion list arriving by the back door |
| IV. What A Consumer Cannot Absorb Needs A New Line | pass | Surface is added and none moves. The fixture gate compares every other capability's inputs, defaults, permissions and check names on every run, so SC-006 is asserted rather than reviewed |
| V. A Published Ref Cannot Be Withdrawn | pass | Nothing is tagged here. The version follows the release path's own reading of the range and the surface; what this change owes it is a truthful fixture in the same commit as the workflow |
| VI. Caller-Controlled Text Never Reaches A Command Line | pass | The one `run:` block interpolates nothing at all — `$GITHUB_SERVER_URL` and `$GITHUB_REPOSITORY` are set by the runner. `test_no_interpolation.py` holds it |
| VII. A Required Gate Never Passes Without Judging | pass | The job pins `pull_request` and its skip is registered in the surface record with its reason, so the existing skip gate admits it with no exemption. The capability judges — `judges` is absent — so the composed context is required-eligible under that one event, and the README says requiring it under another gives a check that reports success without reading anything |

No violations, so **Complexity Tracking is empty** and stays deleted.

One thing this section is *not* recording: an objection. The spec's opening promise covers licences and
the shipped capability refuses none, because exposing a licence policy is out of the fixed interface. That
is the spec's own assumption rather than a conflict, and FR-013 already makes the reference say so.

## Project Structure

### Documentation (this feature)

```text
specs/004-dependency-review/
├── plan.md                              # This file
├── spec.md
├── research.md                          # Phase 0: the action's real surface, and what it contradicts
├── data-model.md                        # Phase 1: every artefact added or moved
├── quickstart.md                        # Phase 1: how to validate, offline and on a real pull request
├── contracts/
│   └── published-surface-delta.md       # Phase 1: the only consumer-visible change
├── checklists/
│   └── requirements.md
└── tasks.md                             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
.github/workflows/
├── dependency-review.yml     # new — the capability. 🧩, workflow_call only, one input, one job
└── dependency-guard.yml      # new — this repository's caller. 🌜, pull_request, job id `guard`

.github/rulesets/
└── protect-default-branch.json   # unchanged: the new context is composed and not required

tests/
├── capabilities.py               # + declared_input_specs, the one new reader
├── published_surface.toml        # + the [dependency-review] table and its skip entry
├── test_workflow_properties.py   # + four gates, each with its violation-planting check
└── test_ruleset_contexts.py      # two existing assertions gain the new context by name

README.md                         # + one capability section; the prose count deleted
pyproject.toml                    # [tool.turbobasic-release].exclude gains the new caller
.cspell/project.txt               # + OpenSSF, ghsas — already added, so this plan's own prose lints
```

**Structure Decision**: the layout is the repository's own and nothing about it is chosen here. A
published capability is one file in `.github/workflows/`; a caller of it is another, one per capability,
as `ci.yml`, `advisory.yml`, `commit-messages.yml` and `describe-pr.yml` already are. No `actions/`
entry, because nothing here needs a composite action. Gates go beside the other per-capability gates in
`test_workflow_properties.py` rather than into a new module — that file already holds the `python-ci`,
`release`, `apply-ruleset`, `pr-description` and `conventional-commits` gates, and a module per capability
would be a structure this repository does not have.

## Phase 0 — what was open, and what closed it

Full findings in [research.md](research.md). The four that changed the design:

1. **`fail-on-severity` defaults to `low` in the action's schema, not in its `action.yml`.** The
   capability declares `default: low` explicitly (FR-004) and that value is the action's own, so FR-008
   holds. Consequence the README owes: at the default floor nothing is below the floor, so scenario 1.4 is
   reachable only once a consumer raises it.
2. **With no policy configured a licence finding is reported and refuses nothing** — the spec's edge
   case is right. `unlicensed` is the one verdict reachable without an allow or deny list, and it is
   the one that never calls `setFailed`. What no policy buys is the refusal, not the finding.
3. **The action already names the setting and its URL on a 403.** Only the third clause of FR-011 is
   missing, so the capability adds one step rather than translating a message upstream owns.
4. **`dependency-changes` is set only once the comparison has been read**, which is the discriminator that
   keeps the diagnostic off runs that failed on a real advisory.

## Phase 1 — design

[data-model.md](data-model.md) is the artefact-by-artefact statement;
[contracts/published-surface-delta.md](contracts/published-surface-delta.md) is the contract, including
the six inputs the capability deliberately does not expose and why each stays unexposed.

The shape, in brief:

```yaml
# .github/workflows/dependency-review.yml
name: 🧩 dependency-review
on:
  workflow_call:
    inputs:
      fail-on-severity: { type: string, default: low }   # description on the real thing
permissions: {}
jobs:
  dependency-review:
    if: github.event_name == 'pull_request'
    timeout-minutes: <literal>
    permissions:
      contents: read # reason on the line
    steps:
      - id: review
        uses: actions/dependency-review-action@a1d282b… # v5.0.0
        with:
          fail-on-severity: ${{ inputs.fail-on-severity }}
      - if: failure() && steps.review.outputs.dependency-changes == ''
        run: echo "::error::…"
```

### Ordering, and what each step can land on its own

| # | Lands | Green on its own because |
| --- | --- | --- |
| 1 | the capability + its fixture row + the README section | the correspondence gate fails either half alone, and the README is what makes the capability adoptable |
| 2 | the four gates + the new reader | they read the capability from step 1; landing them first would be a suite asserting a partition the tree does not have |
| 3 | the caller + the two extended context assertions + the release-surface exclusion and the gate that holds it | the context has to exist before a gate can name it |

Steps 2 and 3 are independent of each other. Step 1 is P1 and P2 together — Story 2 is the permission
surface, which is a property of the file Story 1 adds, not a second change. Story 3 is the README half of
step 1 plus the fixture's skip entry. Story 4 is step 3.

## Complexity Tracking

No Constitution Check violation, so nothing is tracked here.
