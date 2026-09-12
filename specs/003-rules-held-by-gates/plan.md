# Implementation Plan: Every rule held by a gate

**Branch**: `003-rules-held-by-gates` | **Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-rules-held-by-gates/spec.md`

## Summary

Twelve rules this repository states about itself are held by prose alone. This feature gives each one a
test that reads the tree and needs no network, fixes the three places where the tree does not yet have
the state a gate would assert, and retro-fits the six existing gates whose steady state is an empty
result and which could therefore rot into reporting green.

The approach is deliberately unambitious: no new framework, no gate runner, no shared abstraction over
"a rule". Each gate is a `pytest` function in a module named for the artefact it reads, using the
libraries already in the dev group. Everything a gate needs to know about a workflow or an action it
asks `tests/capabilities.py`, which already owns that question.

Three defects are fixed because a gate cannot assert a state the tree does not have: the notes
configuration has no postprocessor and so publishes live `@`-mentions; a notes item whose subject
carries no pull request number references nothing; and the timeout-input partition FR-014 describes does
not yet exist.

## Technical Context

**Language/Version**: Python 3.14 — the only Python here exists to support the actions and assert
properties of the YAML.

**Primary Dependencies**: already in `[dependency-groups].dev` — `pytest`, `pyyaml`, `commitizen`
(imported by the grammar gate for its own shipped type set), plus `tomllib` from the standard library
for every TOML artefact. **No new dependency.** Two pinned binaries are invoked as subprocesses,
`git-cliff` for the rendering assertions and `actionlint` for the ignore-expiry probe; both are already
in `[tools]`.

**Storage**: N/A. Every gate reads committed files.

**Testing**: `pytest`, run by `mise run test` and reproduced with everything else by `mise run ci`.

**Target Platform**: a maintainer's machine and the CI runner, identically. No gate may behave
differently on the two.

**Project Type**: a library of reusable GitHub Actions workflows. This feature touches only its gates
and, in three named places, its published surface.

**Performance Goals**: the suite stays interactive. It runs in 1.8s today; the two subprocess-invoking
gates are the only ones that add measurable time and there are three of them in total.

**Constraints**: **offline, no token.** `mise run ci` must not need the network. Nothing may reach
GitHub's live state — the gates that would are explicitly out of scope. Every gate reads a workflow or
an action through `tests/capabilities.py` and never parses that YAML a second time. pyright strict
covers `tests/`, so every new signature is fully typed.

**Scale/Scope**: 12 rules gated, 3 defects fixed, 6 existing gates paired. Six new test modules or
module sections; two workflows and one fixture edited. No capability added, removed, or changed in
behaviour.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Bearing on this feature | Verdict |
| --- | --- | --- |
| I — One Owner Per Fact | The feature's whole purpose. Three facts are currently stated twice: the commit type set (workflow default vs. the tool's own), the commit tool version (workflow literal vs. lockfile), and the vendored specification version (manifest vs. pin). Each is reduced to one owner plus a gate, never to a third copy in a test. R5 rejects the literal type list in a test for exactly this reason. | **Pass** — the feature removes duplication rather than adding it. |
| II — Secrets Never Persist | No gate reads, writes or needs a secret. The offline constraint makes a token structurally unavailable. | **Pass** |
| III — Gates Are Never Loosened | Nothing is suppressed. One existing suppression is *narrowed in time*: FR-011 makes the actionlint ignore expire the day its reason does, which tightens it. No rule is disabled and no tool mode relaxed. | **Pass** |
| IV — What A Consumer Cannot Absorb Needs A New Line | **Engaged.** FR-014 removes `timeout-minutes` from two published capabilities. A caller passing an input the callee no longer declares fails the whole run before any job exists — precisely the failure this principle names. Renaming all twelve workflows does *not* engage it: R10 verified that every required context is composed from job names. | **Pass with a new line owed** — see below. |
| V — A Published Ref Cannot Be Withdrawn | The input removal must be released as a break, and below `1.0.0` a break is signalled by the minor, which is the test that fails silently in the permissive direction. The refusal has to run before the tag exists. The existing release-decision gates already hold this; FR-017 makes the surface fixture record the change so those gates see it. | **Pass** — no new mechanism needed, but see the sequencing note. |
| VI — Caller-Controlled Text Never Reaches A Command Line | No gate interpolates anything into a command line. The two subprocess gates pass fixed argument lists with `cwd` set, never a shell string. The planted probes are files written by the test, not text from outside. | **Pass** |
| VII — A Required Gate Never Passes Without Judging | The feature's second half *is* this principle applied to the suite: FR-018 and FR-019 exist because a gate that judges nothing and reports green is the failure mode being closed. FR-016 keeps every job that loses the input carrying a fixed timeout, so no job becomes unbounded. | **Pass** |

### The new line FR-014 owes

Removing a published input starts a new compatibility line. This is stated here rather than decided
here: the version, the tag and the ordering are the release path's to determine, and the existing
release-decision gates read the surface fixture to reach that verdict. What this plan commits to is
that the fixture edit lands in the same change as the workflow edit, so the verdict is reached from a
tree that tells the truth. **The input removal must not be released in a change that also claims to be
a fix.**

**Sequencing consequence**: FR-014 through FR-017 are the last work in the feature, and they are
separable. Every other requirement is gate-only and carries no release consequence, so the feature can
land its gates first and the surface change second — or the surface change can be split into its own
pull request entirely if the release timing is inconvenient. Nothing else depends on it.

### Deliberately not built

No gate abstraction, no rule registry, no table of "every rule and its gate". Each is a plain test
function beside the artefact it reads. A registry would be a second statement of which rules exist, and
the tests are already that statement — building one would breach principle I in the act of enforcing it.

## Project Structure

### Documentation (this feature)

```text
specs/003-rules-held-by-gates/
├── plan.md              # This file
├── research.md          # Phase 0: R1–R15, every finding verified against the tree
├── data-model.md        # Phase 1: the artefacts each gate reads, and what it asserts
├── quickstart.md        # Phase 1: how to verify every gate can fail
├── contracts/
│   └── published-surface-delta.md   # the only consumer-visible change in the feature
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
tests/
├── capabilities.py               # EXTENDED: a job-name accessor, a trigger-kind accessor
├── test_release_notes.py         # NEW: FR-001..006
├── test_commit_grammar.py        # NEW: FR-007, FR-008
├── test_tool_versions.py         # NEW: FR-009
├── test_speckit_vendoring.py     # NEW: FR-010 (ported from the tree being consolidated)
├── test_actionlint_ignore.py     # NEW: FR-011
├── test_names.py                 # NEW: FR-012, FR-013
├── test_workflow_properties.py   # EXTENDED: FR-014..016, and 4 of the 6 pairings
├── test_published_surface.py     # EXTENDED: 1 pairing
├── test_repo_urls.py             # EXTENDED: 1 pairing
└── published_surface.toml        # EDITED: two rows lose an input

cliff.toml                        # EDITED: ordering prefixes, postprocessors, reference fallback
.github/workflows/*.yml           # EDITED: all 12 names gain a marker; 2 lose an input
```

**Structure Decision**: one module per artefact read, which is what the suite already does — a module
is named for the thing it holds rather than for the requirement number, so a maintainer looking for
what guards the notes configuration finds `test_release_notes.py` without a map. Three requirement
groups have no module of their own because the artefact they read already has one:
the timeout partition and its pairings extend `test_workflow_properties.py`, which already owns
input-shape gates; the two remaining pairings extend the modules owning the readers they guard.

`tests/capabilities.py` gains two accessors and no more. Everything else each new module reads is read
by that module alone (R15), so no shared reader is introduced for a single caller.

## Complexity Tracking

> Filled only where the Constitution Check leaves something to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| FR-014 breaks the published surface (principle IV) | A gate asserting a partition the tree does not have cannot pass, and the partition is the rule being gated. Leaving the inputs in place would mean either no gate or a gate with two recorded exceptions, which is a dial rather than a rule. | Keeping the inputs and gating only "no *new* capability exposes one" was considered and rejected: it grandfathers the two cases the rule exists to describe, so the rule would no longer be true of the tree and the next reader could not tell which state was intended. |
| Two gates invoke a subprocess (`git-cliff`, `actionlint`) | Both hold facts that cannot be read from a file. A postprocessor pattern that has rotted leaves valid TOML and a body that reads correctly to everyone except the person notified (R2); the linter's acceptance of a syntax is only observable by asking it (R7). | Reading the configuration's shape instead was rejected under FR-006 — it is the exact failure the paired-test rule exists to prevent. Comparing the linter's version number instead was rejected because it fails early or late depending on which release carries the fix, and the debt entry already states the behavioural condition. |
