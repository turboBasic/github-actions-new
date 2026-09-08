# Phase 1 Data Model: The Consumer Contract

**Date**: 2026-09-07 | **Feature**: [spec.md](./spec.md)

This repository stores nothing and serves no requests. Its "data" is of two kinds: the published
surface, which tests read as a structure so principle IV has something to hold; and the release
decision values, which are the only real domain types here. Both are described below as the shapes code
operates on, not as files to create — placement is the implementation's business.

## Published surface

Read by the surface gate (R5). One record per published capability.

### Capability

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | The file's own stem. Unique. Changing it moves a consumer's call site → new line |
| `kind` | `workflow` \| `action` | A workflow composes a check name; an action does not |
| `published` | bool | `false` marks internal surface with no stability promise (the decision unit) |
| `check_name` | string \| null | The called job's `name:`. Non-null exactly when `kind` is `workflow` and `published` |
| `inputs` | list of `Input` | Every declared input. Order irrelevant; the set is what is compared |
| `permissions` | list of `PermissionDemand` | What a caller must grant for the run to *start* |
| `tool_prerequisites` | list of string | Tools the capability invokes that the consumer's config must pin (FR-009) |
| `skips_under` | list of `EventSkip` | Every event-conditional job-level `if:`, each with a reason (principle VII) |

Invariant: `check_name` is null for every action and non-null for every published workflow. A published
workflow with no check name is a gate a consumer cannot require.

### Input

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | Unique within the capability. Renaming breaks a call site → new line |
| `required` | bool | A required input arriving absent is a caller error, not a default |
| `default` | string \| null | Null exactly when `required`. Owned by the YAML; not restated (R4) |

### PermissionDemand

| Field | Type | Rules |
| --- | --- | --- |
| `scope` | string | e.g. `contents`, `pull-requests` |
| `level` | `read` \| `write` | Adding one, or raising `read` to `write`, → new line |

Validated before any job exists, so a shortfall yields no job and no log. This is why the demand is part
of the compared surface and not merely documented.

### EventSkip

| Field | Type | Rules |
| --- | --- | --- |
| `event` | string | The event under which the job does not run |
| `reason` | string | Non-empty, asserted. An exemption list without reasons is a dial on the gate |

## Release decision values

The internal decision unit's types. Pure values; every one is derivable offline from a file and an
environment.

### Version

A plain `(major, minor, patch)` triple. Parsed from exactly `N.N.N` — no pre-release, no build
metadata, no leading `v`, because the `v` belongs to the tag and not to the version.

Parsing returns absence rather than raising, so the caller chooses the message.

### CompatibilityLine

The versions one moving ref may span: `(major,)` from `1.0.0` up, `(major, minor)` below it.

**This is the single statement of the 0.x boundary** (principle I, and the reason principle V names it).
The refusal, the increment and the ref name all derive from this one function; a test asserts it is the
only place the boundary is decided. Getting it from the major number alone is wrong below `1.0.0` and
wrong permissively — it would let a break move a ref consumers pin.

### MovingRef

`v` followed by the compatibility line joined on `.` — `v0.1` below `1.0.0`, `v1` above.

Invariant: **total and never empty** for every version the refusals admit (R3). Never `v0`, which would
span every pre-1.0 break and so defeat the ref's only purpose.

### Increment

Derived from two verdicts over the surface-filtered range:

| breaking | feature | Line owns the minor (0.x) | Line owns the major (≥1.0) |
| --- | --- | --- | --- |
| yes | — | minor + 1, patch 0 — starts the next line | major + 1, rest 0 — starts the next line |
| no | yes | patch + 1 | minor + 1, patch 0 |
| no | no | patch + 1 | patch + 1 |

A feature may only advance a component the line does not own: a consumer pinned to `v0.1` must be able
to receive it without crossing into `v0.2`. Which component the line owns is read from
`CompatibilityLine`, never from the version, so the boundary keeps its single owner.

### SurfaceDeclaration

The released repository's own statement of which paths a consumer of *it* resolves. Two optional path
lists, include and exclude.

Three distinguishable states, because they warrant different things being said:

| State | Refusal considers | Reported |
| --- | --- | --- |
| absent | every path | a notice naming the omission |
| declared | only what was declared | nothing |
| declared, both lists empty | every path | nothing — it was decided |

Rules:

- An unknown key is **refused**, not ignored. A misspelled key would otherwise read as an absent one,
  which is the *declared but empty* state — silently widening the surface to every path while looking
  configured.
- A non-list value is refused rather than coerced: iterating a string yields characters, so every letter
  would become a path and the filter would match nothing while looking configured.
- A path that is empty, holds whitespace, or begins with `-` is refused before any ref exists.
- There is no input to override any of this. An input would need a default, and one repository's layout
  is right for another only by coincidence.

### ReleaseVerdict

`(proceed, severity, message)`. One condition — "the declared version is not ahead of the highest
release" — carries three verdicts, because what it means depends on who asked:

| Asked by | Verdict |
| --- | --- |
| a routine push | decline with a notice; the default branch must not redden for doing nothing wrong |
| a dry run | proceed, reporting what it *would* have refused |
| anything else | refuse, naming the version read and the version compared against |

`severity` is `notice` or `error`. A non-zero exit is how a caller learns the answer without comparing a
string in shell.

### Refusal ordering

Not a type but an invariant on the sequence, and the one principle V turns on: **every refusal is
evaluated before any ref exists.** A refusal after a tag has been created is not a refusal, because the
version tag is immutable and cannot be withdrawn.

The refusals, in order:

1. The run is not on the repository's own default branch — read from the run, never a literal name
   (FR-037a). Softened by a dry run.
2. The declared version is not a plain semantic version.
3. The declared version is not ahead of the highest existing release, across every compatibility line —
   a frozen line is never backported, only left where it is.
4. The range renders no notes.
5. The range breaks the consumer surface while the declared version stays on a line that already has a
   release — measured against `CompatibilityLine`, not against the major number.
