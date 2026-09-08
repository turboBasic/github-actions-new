# Contract: The Published Surface

**Date**: 2026-09-07 | **Feature**: [spec.md](./spec.md) | **Model**: [data-model.md](../data-model.md)

The interface this repository exposes. Every row is a promise: a change to one that a consumer cannot
absorb by resolving its ref starts a new compatibility line (principle IV).

This document is the design-time statement of that surface. Implementation turns it into a committed
fixture the surface gate compares the tree against — so the fixture, not this file, is what a future
change edits. Nothing here is authoritative for shipped behaviour once the capabilities exist; the
capability YAML is (R4).

## Composed check names

A consumer's required context is its own job id, then the called job's name. This repository owns only
the second half. Retiring one blocks every pull request in every consumer until each ruleset is
hand-edited, which is why the name is surface and not a detail.

| Capability | Kind | Check name it composes |
| --- | --- | --- |
| `python-ci.yml` | workflow | `python-ci` |
| `conventional-commits.yml` | workflow | `pr-title` **and** `commit-messages` (two jobs, two contexts) |
| `pr-description.yml` | workflow | `pr-description` |
| `release.yml` | workflow | `tag-and-publish` |
| `prek-advisory.yml` | workflow | `prek-advisory` |
| `release-decisions` | action | none — internal, composes nothing (OQ-003) |

Every published capability is a callable workflow. `release-decisions` is the only action in the tree
and is not published, so `actions/` holds exactly one directory: the advisory lint's composite-action
form is cut rather than shipped alongside its workflow (FR-049a, F1).

## Inputs

Names, and which are required. **Defaults live in the capability YAML and are deliberately not repeated
here** (principle I, R4). The gate compares the *set of names*, since renaming or removing one breaks a
call site.

| Capability | Inputs |
| --- | --- |
| `python-ci.yml` | `run-lint`, `run-typecheck`, `run-tests`, `lint-task`, `typecheck-task`, `test-task`, `lint-changed-only`, `hook-stage`, `timeout-minutes` |
| `conventional-commits.yml` | `check-title`, `check-commits`, `types`, `timeout-minutes` |
| `pr-description.yml` | `template-path`, `timeout-minutes` |
| `release.yml` | `dry-run` |
| `prek-advisory.yml` | `hook-stage`, `timeout-minutes` |
| `release-decisions` | `decision` (required), plus the per-question inputs; internal, so not compared |

Deliberately absent, and each absence is a contract:

- **No `cache-prek`** on either capability that caches. Caching is unconditional (FR-014a, OQ-007).
- **No `mise-version`** on either capability that provisions the task runner. Six call sites could have
  set it and none did, and removing an input is a break where adding one is not (FR-016a, F2).
- **No `fail-on-severity`** anywhere. Dependency review is not a capability here (OQ-002).
- **No identifying inputs on `pr-description.yml`** — no token, pull request number, repository or SHA
  range. The workflow owns its checkout and reads all of it from the run (FR-029a, OQ-010).
- **No `default-branch` input on `release.yml`.** The default branch is read from the run (FR-037a,
  OQ-006). An input would be a value that can be set wrong, and wrong in either direction is severe.
- **No surface-filter input on `release.yml`.** The released repository declares it in its own manifest;
  an input would need a default, and one repository's layout fits another only by coincidence (FR-038).

## Permission demands

What a caller must grant for the run to **start**. Validated before any job exists, so a shortfall
produces no job, no log and no annotation, and no `if:` can skip past it. Adding one — or raising a
`read` to a `write` — is a new compatibility line.

| Capability | Demands |
| --- | --- |
| `python-ci.yml` | `contents: read` |
| `conventional-commits.yml` | `contents: read`, `pull-requests: read` — at **both** workflow and job level |
| `pr-description.yml` | `contents: read`, `pull-requests: write` |
| `release.yml` | `contents: write` |
| `prek-advisory.yml` | `contents: read`, `pull-requests: write` |

`prek-advisory.yml` is a capability of its own **because** of that write. A workflow declaring
`pull-requests: write` anywhere forces every caller to grant it, so keeping it separate is what lets a
consumer take the CI capability without granting write access (FR-003).

## Tool prerequisites

Tools each capability invokes that the consumer's own task-runner configuration must pin. Checked before
use, failing with the tool named, the capability named, and where to declare it (FR-009, OQ-005). These
stay the consumer's to pin — that is what makes a local verdict and a CI verdict agree.

| Capability | Consumer must pin |
| --- | --- |
| `python-ci.yml` | the package manager; the tasks named by `lint-task` / `typecheck-task` / `test-task`; the hook runner when `lint-changed-only` is on |
| `prek-advisory.yml` | the package manager, the hook runner |
| `release.yml` | the notes renderer |
| `conventional-commits.yml` | nothing — it provisions its own, so a repository with no task-runner config can still use it |
| `pr-description.yml` | nothing — it provisions its own |

## Event skips

Every event-conditional `if:` at job level, with the reason. The gate asserts each reason is present and
non-empty (principle VII).

| Capability | Skips under | Reason |
| --- | --- | --- |
| `conventional-commits.yml` | any event but `pull_request` | there is no title and no range to judge; a consumer must not require these contexts for another event |
| `prek-advisory.yml` | any event but `pull_request` | there is no pull request to comment on. Advisory, so not a required gate, so exempt from principle VII |
| `pr-description.yml` | any event but `pull_request` | there is no body to write |

`python-ci.yml` and `release.yml` carry no event-conditional job `if:` and so appear in no row here.
`release.yml` has no trigger of its own at all — a caller's dependency edge is the only route to it,
which is what keeps anything from reaching the tagging step around that edge (FR-033).

## Versioning

- This repository starts its own line and inherits no ref (FR-009a, OQ-009). A consumer adopting it
  repins once and re-checks its required contexts once.
- A consumer pins the moving ref: `v1` from `1.0.0` up, `v0.1` while below it. `v0` is never published.
- Exact release tags are immutable. The moving ref is force-moved to each release, last, after the
  release exists.
- One documented exception to SHA-pinning: the release workflow names the internal decision unit by
  owner, repository and moving ref, because a reusable workflow cannot reach its own tree or learn its
  own ref (R2). It is internal surface, so that ref moving is not a consumer-visible change. Third-party
  actions are SHA-pinned with no exception.
