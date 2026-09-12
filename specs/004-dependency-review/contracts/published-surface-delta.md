# Contract: the published surface delta

The only consumer-visible change in this feature. Everything else it does is a gate or a caller of its
own, and neither promises anything to anybody outside this repository.

This repository's interface is its capabilities: a reusable workflow's declared inputs, the permissions
it demands, and the check names it composes. `tests/published_surface.toml` is the committed statement
of all three and `tests/test_published_surface.py` holds the tree to it. That fixture is the contract
document; this file records what changes in it and why.

## What changes

One capability arrives. Nothing else on the surface moves.

| Capability | Kind | Inputs | Permission demand | Composed context | Break? |
| --- | --- | --- | --- | --- | --- |
| `dependency-review` | workflow, published | `fail-on-severity` | `contents: read` | `<caller job id> / dependency-review` | no |

Its `tool_prerequisites` list is empty, and empty is true: it provisions no task runner and invokes no
tool a consumer's own configuration has to pin. Its `skips_under` carries one entry — the job does no
work under any event but `pull_request`.

`judges` is absent, so true. This is the third published workflow whose context a consumer may require,
alongside `python-ci` and `conventional-commits`, and it is required under `pull_request` or not at all.

## What does not change

| Considered | Verdict |
| --- | --- |
| every other capability's inputs, defaults, permissions and check names | byte-identical — the surface gate compares all of them on every run |
| the committed branch ruleset's required contexts | unchanged; the new context is composed and not required |
| `[tool.turbobasic-release].include` | unchanged; the capability is consumer surface and already inside it |

## Why this is not a break

A consumer resolving the ref they already pin gets a file they do not call. Nothing they name is
renamed, no default they rely on moves, and no permission they must grant is raised — the three edits
principle IV says a consumer cannot absorb. Adding surface is absorbed by resolving the ref alone.

The version this ships under is the release path's to decide from the range and the surface, not this
feature's. What this change owes it is a truthful fixture in the same commit as the workflow, so the
decision is reached from a tree that tells the truth.

## What the capability deliberately does not publish

Each of these is an input the published action declares and this capability does not pass on. Listed
because a surface is also what it refuses to expose, and because every one of them is a thing somebody
will eventually ask for.

| Not exposed | Why |
| --- | --- |
| `allow-licenses`, `deny-licenses`, `config-file` | a licence policy is a second input and a separate request; with none configured an unlicensed dependency is reported and no licence can be refused |
| `comment-summary-in-pr` | `always` or `on-failure` demands `pull-requests: write`, which every caller would then have to grant before any job exists |
| `warn-only` | a capability that always reports success is a required gate that never judges (principle VII) |
| `allow-ghsas`, `deny-packages`, `deny-groups` | re-ranking or overriding the action's judgement, which this capability does not do |
| `base-ref`, `head-ref`, `repo-token` | a consumer identifies nothing; all three are already in the run |
| `timeout-minutes` | the runtime is one API comparison, not a function of the caller's tree — the job fixes its own |

An input added here later is a surface addition and absorbable. Removing one is not, which is why the
list starts at one.

## Sequencing

The fixture row, the workflow and the README section land together: a capability without its row fails
the correspondence gate, and a row without its capability fails it from the other side. The caller and
the release-surface exclusion can land in the same change or a later one — they are this repository's own
call site and promise nothing to anybody.
