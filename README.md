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

Nothing is released yet, so the ref every call site below pins does not resolve. Versioning says what
will be there to pin.

### `python-ci`

One check over a **Python project**: its own lint, typecheck and test tasks, run by its own task
runner, after installing from its own lockfile.

```yaml
jobs:
  ci:
    permissions:
      contents: read
    uses: turboBasic/github-actions-new/.github/workflows/python-ci.yml@v0.1
```

Required context: `ci / python-ci` — your own job id, then the called job's name.

Reach for it when the repository has a `pyproject.toml` and a current `uv.lock`. A repository without
a lockfile is out of scope rather than badly served: the lockfile check is not a stage that can be
switched off, because a verdict from a tree whose lockfile disagrees with its manifest is a verdict
about neither. The three stage switches are for a Python repository genuinely missing a stage, not a
route to using this without Python.

It needs, from `mise.toml` in the calling repository: the tasks it is asked to run, `uv`, and `prek`
if the changed-files lint is on. Those stay yours to pin — that is the only reason a local verdict and
this one agree — and a missing one fails the run naming the tool and where to declare it, rather than
with `command not found`.

Two things worth knowing before setting an input, and prose is the only place either fits:

- **The changed-files lint lets a pull request pass while the tree is broken.** It reads the pull
  request's own diff, so a finding in a file the pull request did not touch is never looked for.
  `prek-advisory` is what compensates — it lints the whole tree on the same pull request and reports
  in a comment rather than a check.
- **A repository holding its slow hooks back for a later stage has to name that stage**, or the
  changed-files lint fires the default stage and those hooks silently stop running on pull requests.
  Pass `prek-advisory` the same stage.

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
