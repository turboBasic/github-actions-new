# Quickstart: Validating the Consumer Contract

**Date**: 2026-09-07 | **Feature**: [spec.md](./spec.md)

How to prove a capability works, at three widening scopes. The first two are offline and are the ones a
change must pass; the third needs GitHub and is what a release depends on.

## Prerequisites

```console
mise run setup     # tools, dependencies, git hooks
```

## 1. Offline — the gates

```console
mise run ci        # lint, typecheck, test
```

This must never need the network. It is the whole verdict for anything the tree can answer:

| What it proves | How |
| --- | --- |
| Every release decision is right, including below `1.0.0` | unit tests over the decision unit — the refusals, the increment, the `0.x` boundary, the surface filter |
| The `0.x` boundary has exactly one statement | a test asserting no second place decides it |
| The moving ref is never empty for a version the refusals admit | a totality test, replacing the dead guard (R3) |
| No published surface changed unnoticed | the surface gate, comparing the tree against the committed fixture |
| Every event skip carries a reason | the skip table's reasons are asserted non-empty |
| No caller-controlled text reaches a command line | a test over every `run:` block, plus `zizmor --pedantic` |
| Third-party actions are SHA-pinned | a pin test; the one self-reference exception is named and asserted to be the only one |
| Every workflow declares a timeout | `check-jsonschema` against the repository's own schema |

A failure here names what it read and what to change — a bare exit code is not an acceptable result
(SC-008).

## 2. Offline — a capability against its own contract

Workflow-level behaviour that no unit test reaches is asserted as properties of the YAML: that
`conventional-commits.yml` declares two jobs whose names are the two published check names, that
`release.yml` has `workflow_call` and nothing else, that `prek-advisory.yml` is the only capability
demanding `pull-requests: write` besides `pr-description.yml`.

Where a decision can be moved out of a `run:` block so it can be *called* instead of asserted, that is
the better test and worth the move for that reason alone.

## 3. On GitHub — this repository as its own consumer

This repository's CI calls each capability with `$/.github/workflows/<file>`, which resolves at the
commit under review (R1). So a capability is exercised by the same mechanism a consumer uses, and a
defect fails the pull request that introduces it rather than reaching a consumer first.

Open a pull request and read the checks. Expected:

| Check | Proves |
| --- | --- |
| `ci / python-ci` | the CI capability runs this repository's own tasks and passes |
| `commits / pr-title`, `commits / commit-messages` | both grammar contexts report, and are named as published |
| `describe / pr-description` | the body renders from the range, with no checkout written by the caller |
| `advisory / prek-advisory` | the comment appears once and is edited, not duplicated, on a second push |

What cannot be proved this way, and must be checked deliberately:

- **A permission shortfall.** Removing a demand from a call site fails the run at startup with no job and
  no log. It has to be tried on a scratch branch to be seen; it cannot be asserted from the tree,
  because the tree is the side that is correct.
- **A release.** Dispatch the release path with the dry-run switch on: every refusal runs and the real
  notes render, then it stops before creating any ref. This is the only safe way to exercise it, since a
  version tag cannot be withdrawn once published (principle V).

## What a consumer runs to validate adoption

After repinning (one migration, FR-009a):

1. Open a pull request. Confirm the check names that appear match what is required in the ruleset —
   repinning and re-requiring are one change, or the ruleset keeps naming a gate that no longer reports.
2. Confirm the capability's tool prerequisites are pinned in the task-runner configuration. If not, the
   run fails naming the tool and where to declare it rather than with a missing command (FR-009).
3. For the release capability only: dispatch with dry-run before trusting it with a real tag.
