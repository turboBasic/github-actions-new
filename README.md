# turboBasic/github-actions

Reusable GitHub Actions workflows and composite actions for `turboBasic` repositories.

The work is staged at
[`turboBasic/github-actions-new`](https://github.com/turboBasic/github-actions-new) and replaces
[`turboBasic/github-actions`](https://github.com/turboBasic/github-actions) if it succeeds. Every name
in the tree is therefore already the destination one while every URL still carries the `-new` suffix,
because a URL has to resolve today. The suffix goes when the repository does.

The workflows and actions are specified from the *functional behaviour* of the repository they
replace, rather than ported from its files.

## Capabilities

One section each, carrying a call site to copy, what the capability is for, and when not to reach for
it.

**A capability's inputs, its defaults, the permissions a caller must grant and the check names it
composes are declared in its own workflow file, and are deliberately not restated here.** Two
statements of one default drift apart, and afterwards nothing in the tree says which of them was ever
authoritative — so the file being called is the only place any of it is written. Open it for the full
list.

Two things a call site cannot show, and which apply to every capability below:

- **Concurrency grouping stays the caller's.** A called workflow cannot set its caller's group.
- **A permission a caller does not grant fails the whole run before any job exists**, with no log, no
  annotation, and no condition able to skip past it. That is why each capability's demand is part of
  what it publishes rather than something a first run teaches you.

### `python-ci`

Not shipped yet.

### `conventional-commits`

Not shipped yet.

### `pr-description`

Not shipped yet.

### `release`

Not shipped yet.

### `prek-advisory`

Not shipped yet.

## Versioning

Not shipped yet. What is already settled: this repository starts its own version line and inherits no
ref from the one it supersedes, so adopting it is one deliberate migration — repin the call site and
re-check the required contexts, once.

## Working in this repository

`AGENTS.md` is the map — it names every artefact and what that artefact answers. Start there.

```console
mise run setup   # tools, dependencies, git hooks
mise run ci      # everything CI runs
```
