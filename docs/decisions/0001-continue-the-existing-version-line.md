---
id: 0001
status: accepted
date: 2026-09-12
scope: release
---

# ADR 0001 — The library continues the existing repository's version line

## Decision

The library ships from `turboBasic/github-actions`, the repository it has always shipped from. The
first release of the re-specified tree is `5.0.0`, and consumers pin `@v5`. Every earlier release tag
— `v2`, `v3`, `v4` and their exact versions — stays published and keeps resolving. None is deleted,
and none is moved.

## Context

The tree being released was specified from the old repository's *functional behaviour* rather than
forked from its files, so almost nothing in it survives from `4.1.5`. That raises whether it is the
same project continuing or a new one, and the answer decides a number that cannot be withdrawn once
published.

Two things constrain it. The release path refuses any version not ahead of the highest release across
every compatibility line — `actions/release-decisions/decisions.py:227` — and `4.1.5` is published, so
no number below `5.0.0` is available here without deleting refs. And the consumer set is indefinite
(ADR 0002), so any published ref may be resolved by someone we cannot ask.

## Options

### Continue the existing repository's line (SELECTED)

- Adopted because: no published ref is deleted, so no caller we cannot enumerate is broken.
- Adopted because: the App installation, both release secrets and the branch ruleset are already here.
- Adopted because: `5.0.0` is accurate — this is the fifth interface generation of one library.
- Adopted despite: a tag's history is a poor guide to its contents across the `4` → `5` boundary.
- Adopted despite: a newcomer meets four frozen majors describing trees that no longer exist.

### Delete `v2`/`v3`/`v4` and release `1.0.0`

- Rejected because: a published ref may be resolved by a consumer we cannot enumerate, so deletion
  breaks callers silently.
- Rejected because: it requires dropping the immutable-release-tags ruleset — a gate loosened for
  cosmetics, which principle III forbids.
- Rejected despite: `1.0.0` would honestly describe a tree with no released predecessor.

### Rename the staging repository into the name, retiring the old one

- Rejected because: the name is freed only by deleting or renaming the old repository, and either
  breaks every caller pinned to `@v2` or `@v4`.
- Rejected because: it restarts the version line, discarding four majors of accurate history.
- Rejected despite: an App installation, its secrets and the ruleset all follow a rename, so nothing
  has to be set up again — this option costs less than it appears to.
- Rejected despite: it yields the tidier number and a history containing only this tree.

### Stay on the `0.x` line the re-specified tree started

- Rejected because: `0.x` promises a consumer that a break may arrive in any minor, which is the wrong
  promise from the library gating every other repository's CI.
- Rejected despite: the `0.x` apparatus is built and tested already.

## Consequences

The end state is **one** repository. The re-specified tree moves onto this one, and the staging
repository is retired once it has — two names for one library is not a resting place.

Deleting or moving a published release tag is now forbidden; the immutable-release-tags ruleset in
`.github/rulesets/` is where that is held, and this ruling is why it may not be dropped.

Every future release must clear the highest release across all lines rather than its own, which the
refusal cited above already enforces — including the `v0`/`v1` boundary logic, which stays in the code
serving callers that are themselves pre-1.0 rather than serving this repository. The harness repository
is what exercises that path now.

Reopened only if the library is split: the part that leaves takes a new repository and its own line.

## Links

No issue — ruled in conversation while consolidating the two trees; the PR landing the tree carries the
evidence. Sits beside ADR 0002, which supplies the indefinite-consumer constraint this turns on.
