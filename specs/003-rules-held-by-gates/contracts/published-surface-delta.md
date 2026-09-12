# Contract: the published surface delta

The only consumer-visible change in this feature. Everything else it does is a gate, and a gate promises
nothing to anybody outside this repository.

This repository's interface is its capabilities: a reusable workflow's declared inputs, the permissions
it demands, and the check names it composes. `tests/published_surface.toml` is the committed statement
of all three, and `tests/test_published_surface.py` holds the tree to it. That fixture is the contract
document; this file records what changes in it and why.

## What changes

Two published capabilities stop declaring `timeout-minutes`.

| Capability | Before | After | Break? |
| --- | --- | --- | --- |
| `conventional-commits` | `check-commits`, `check-title`, `timeout-minutes`, `types` | `check-commits`, `check-title`, `types` | **yes** |
| `pr-description` | `template-path`, `timeout-minutes` | `template-path` | **yes** |

Unchanged: every permission demand, every composed check name, every other input, and both capabilities'
behaviour. The jobs keep a timeout; it becomes a literal in the workflow instead of a value a caller
supplies (FR-016).

## What does not change

| Considered | Verdict |
| --- | --- |
| `python-ci` | keeps `timeout-minutes` — it runs the caller's own tasks and cannot know how long they take |
| `prek-advisory` | keeps `timeout-minutes` — it reads the caller's whole tree and cannot know how large it is |
| every workflow's `name:` | changes, but composes no context — see below |

**Renaming all twelve workflows is not a surface change.** A consumer's required check is composed from
the calling job's name and the called job's name. The committed ruleset requires `ci / python-ci`,
`commits / pr-title` and `commits / commit-messages`; no workflow name appears in any of them. The
existing context gate is what confirms this in the change itself rather than a reviewer.

## Why this is a break

A caller passing an input the callee does not declare fails the whole run before any job exists — no
log, no annotation, and no condition can skip past it. That is the failure principle IV names, and it is
not diagnosable from the consumer's side. So the removal starts a new compatibility line; it is not a
fix.

The obvious version test is the wrong one below `1.0.0`, where a break is signalled by the minor rather
than the major, and the wrong test fails silently in the permissive direction. The release path already
holds this — what this change owes it is a truthful fixture.

## Why remove them rather than keep them

An input is worth its place only where the caller can know something the callee cannot. Neither
capability's runtime is a function of the caller's tree: one judges a title and a commit range, the other
renders a body. A timeout on either is a knob with no reason to be turned, on a surface where every knob
is a promise that cannot be withdrawn.

Keeping them and gating only "no *new* capability exposes one" was rejected: it grandfathers the two
cases the rule exists to exclude, so the rule stops being true of the tree and the next reader cannot
tell which state was intended.

## Sequencing

The fixture edit and the workflow edit land in the same change, so the release decision is reached from
a tree that tells the truth.

Nothing in the rest of the feature depends on this, and this depends on nothing in it. If the release
timing is inconvenient, it splits into its own pull request and the gates ship without it — with FR-014
and FR-015 going with it, since a gate asserting a partition the tree does not have cannot pass.
