# Feature Specification: The Ruleset In The Tree

**Feature Branch**: `002-ruleset-in-tree`

**Created**: 2026-09-08

**Status**: Draft

**Input**: Issue #6 — "codify the branch ruleset so a retired check name cannot pass unnoticed"

## Derivation

Every statement below was read from one of: this repository's live `protect-default-branch` ruleset,
`.github/workflows/*.yml`, `tests/published_surface.toml`, `tests/capabilities.py`, `mise.toml`,
`.pre-commit-config.yaml`, or `docs/ai-instructions.md`.

The live ruleset, at the time of writing:

| Field | Value |
| --- | --- |
| target | `branch`, including `~DEFAULT_BRANCH`, excluding nothing |
| enforcement | `active` |
| rules | `deletion`, `non_fast_forward`, `required_linear_history`, `required_status_checks` |
| required contexts | `ci / python-ci`, `commits / pr-title`, `commits / commit-messages` |
| strict policy | off |
| bypass actors | repository role 5 (admin), `always` |

What composes a context is two halves. The second half is a called workflow's job name, which
`published_surface.toml` already owns as `check_name`. The first half is the calling job's name in one
of *this* repository's own workflows, falling back to its id — which nothing in the tree records at
all, and which no test reads.

The full set the tree currently composes:

| Composed context | Composed by | Safe to require |
| --- | --- | --- |
| `ci / python-ci` | `ci.yml` job `ci` | yes |
| `commits / pr-title` | `commit-messages.yml` job `commits` | yes |
| `commits / commit-messages` | `commit-messages.yml` job `commits` | yes |
| `advisory / prek-advisory` | `advisory.yml` job `advisory` | no — advertised as advisory |
| `describe / pr-description` | `describe-pr.yml` job `describe` | no — writes rather than judges |
| `verify / python-ci` | `release-on-merge.yml` job `verify` | no — never fires on a pull request |
| `release / tag-and-publish` | `release-on-merge.yml` job `release` | no — never fires on a pull request |
| `propose` | `release-proposal.yml` job `propose` | no — never fires on a pull request |

The gap this feature closes: renaming a calling job, retiring a workflow, or making a job conditional
changes what reports, and the ruleset goes on naming what no longer exists. A required context that
never reports blocks every pull request in the repository, produces no failure and no annotation, and
is diagnosable only by opening the ruleset in the UI. `e4507ed` wrote the instruction that the same
change must edit the ruleset; this feature is the gate, because the instruction was already there when
`001-consumer-contract` renamed `ci.yml`'s job and the ruleset kept requiring the old name for six
commits.

## Decisions

Settled before this spec was written, and recorded here rather than re-opened:

- **Applying runs on `workflow_dispatch` only.** Applying a ruleset is not reversible by revert: a
  wrong one blocks every pull request in the repository, including the one that would fix it. A human
  presses the button. What runs on every pull request is the offline gate.
- **A ruleset edited by hand is never silently overwritten.** Applying is a dry run unless asked
  otherwise: the dispatch prints what it would change to the live ruleset and writes nothing. Writing
  for real is a second dispatch with the dry run switched off, made after the difference has been read.
  An emergency edit in the UI is a deliberate act, and discarding it silently would be worse than the
  drift it caused.

  A refusal on any difference was considered and rejected: a difference is the only reason to apply, so
  such a refusal would fire on every run that did any work, and one that always fires stops being read.
  Attributing the difference instead — refusing only a difference a person made in the UI — needs the
  ruleset's edit history to name who made it, and this repository's history returns `actor` as `null`.
  What is left is to show the difference and make a person act on it, which is the dry run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The ruleset has one owner (Priority: P1)

A maintainer changes what the default branch requires by editing a file in the tree and opening a pull
request. After it merges, they dispatch the apply workflow and GitHub matches the tree.

**Why this priority**: Nothing else in this feature is legitimate without it. A committed copy of the
ruleset that GitHub is not applied from is two copies of one fact, which drift and afterwards neither
says which was current — the exact arrangement principle I forbids. The gate in Story 2 reads the
committed copy, so the committed copy has to be the one that governs.

**Independent Test**: Edit the committed ruleset, dispatch the apply workflow, then read the ruleset
back from GitHub and see the edit. Delivers a ruleset that is reviewable in a diff.

**Acceptance Scenarios**:

1. **Given** the committed ruleset and the live ruleset agree, **When** apply is dispatched, **Then**
   it reports that there was nothing to change and exits successfully, whether or not it is a dry run.
2. **Given** the committed ruleset has been edited on the default branch, **When** apply is dispatched
   at its default, **Then** it prints every field that differs, on both sides, and writes nothing.
3. **Given** that difference has been read, **When** apply is dispatched with the dry run switched off,
   **Then** the live ruleset afterwards matches the committed one in every field the committed file
   declares.
4. **Given** no ruleset of that name exists on the repository, **When** apply is dispatched with the dry
   run switched off, **Then** it creates one from the committed file.

---

### User Story 2 - A retired context fails the pull request (Priority: P2)

A maintainer renames a calling job, removes a workflow, or makes a job conditional. The pull request
that does it fails, naming the required context that would stop reporting and what to do about it.

**Why this priority**: This is why the issue was opened. It is P2 only because it reads what Story 1
commits.

**Independent Test**: On a branch, rename `ci.yml`'s job from `ci` to anything else and run the suite
offline. It fails naming `ci / python-ci`. Delivers the gate that makes the rename impossible to land
by accident.

**Acceptance Scenarios**:

1. **Given** every required context is composed by the tree, **When** the suite runs, **Then** it
   passes, with no network access.
2. **Given** a calling job has been renamed, **When** the suite runs, **Then** it fails naming the
   required context that no longer resolves, the workflow and job that used to compose it, and that the
   committed ruleset must be edited in the same change.
3. **Given** a required context names a called job that is not in `published_surface.toml`, **When** the
   suite runs, **Then** it fails — the two halves of the context are checked, not just the first.
4. **Given** the tree composes a context that the ruleset does not require, **When** the suite runs,
   **Then** it passes. Not every check is a gate, and requiring more is the maintainer's decision, not
   the gate's.

---

### User Story 3 - A gate that cannot judge is never required (Priority: P3)

A maintainer adds a context to the required list that would report green without judging anything. The
pull request fails.

**Why this priority**: Principle VII's failure mode, reachable by the same one-word edit this feature
exists to catch, and the required list is now the place where such an edit is visible. Separated from
Story 2 because Story 2's gate is useful without it.

**Independent Test**: Add `advisory / prek-advisory` to the committed required list and run the suite
offline. It fails. Delivers the half of the check that a resolvable name does not cover.

**Acceptance Scenarios**:

1. **Given** a required context whose called capability is marked `judges = false` — it goes green
   without a pass/fail verdict on what it names — **When** the suite runs, **Then** it fails, naming the
   capability.
2. **Given** a required context composed by a workflow that has no `pull_request` trigger, **When** the
   suite runs, **Then** it fails — it cannot report on the event the ruleset gates.
3. **Given** a required context composed by a job carrying an `if:`, **When** the suite runs, **Then**
   it fails.

---

### Edge Cases

- **The API returns fields nobody can set.** `id`, `node_id`, `created_at`, `updated_at`, `source`,
  `source_type`, `_links` and `current_user_can_bypass` come back on a read and are rejected or ignored
  on a write. The committed file holds only what a write accepts, and comparison is over that shape
  alone — otherwise every apply reports drift.
- **Field order and absent fields.** A ruleset read back may order rules differently and may fill
  defaults the committed file omits. Comparison is by meaning, not by byte, or the refusal fires on
  every dispatch and stops meaning anything.
- **Two rulesets share a name.** Names are not unique on the API. Applying must refuse rather than
  guess which one it meant.
- **The apply workflow's own context.** It never fires on a pull request, so it can never be required —
  and it must not appear in the committed required list. Story 3's second scenario already covers this.
- **A calling job that declares a `name:`.** The composed context uses the name, not the id. None do
  today; the gate must not assume it.
- **The ruleset is applied while a pull request is open.** Out of scope: GitHub re-evaluates on its own,
  and nothing here can order it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The branch ruleset MUST exist as committed configuration under `.github/rulesets/`, one
  file per ruleset, holding every field a write accepts.
- **FR-002**: A workflow MUST apply a committed ruleset to the repository, creating it when absent and
  updating it when present.
- **FR-003**: Applying MUST be reachable only by `workflow_dispatch`, and never by a push, a merge, a
  schedule or a pull request.
- **FR-004**: Applying MUST default to a dry run, and MUST write only when the dispatch switches the dry
  run off. One input governs this; there is no second one.
- **FR-005**: Applying MUST print every field in which the live ruleset differs from the committed one,
  showing both sides, before it writes and whether or not it writes.
- **FR-006**: Applying MUST report that there was nothing to change, and exit successfully, when the two
  already agree.
- **FR-007**: Applying MUST refuse when more than one ruleset on the repository carries the committed
  name.
- **FR-008**: The test suite MUST assert that every required context in every committed ruleset is
  composed by this repository's own workflows, resolving both halves — the calling job's name and the
  called capability's job name as `published_surface.toml` records it.
- **FR-009**: The test suite MUST assert that no required context is composed by a job that cannot
  produce a pass/fail verdict on what it names: one whose capability is marked `judges = false` in
  `published_surface.toml`, one carrying an `if:`, or one in a workflow with no `pull_request` trigger.
  A capability's `skips_under` entry records a narrower fact — that its job's own `if:` can skip it
  under some event — and does not by itself disqualify a context: whether that entry's event is ever
  reached depends on which workflow calls it.
- **FR-010**: A failure from FR-008 or FR-009 MUST name the context, where it is required, what
  composes it or fails to, and what a maintainer should change.
- **FR-011**: The test suite MUST reach both verdicts without network access.
- **FR-012**: A committed ruleset's shape MUST be asserted offline: exactly the fields a write accepts,
  a required-status-checks rule present, and a non-empty context list. A malformed file MUST fail rather
  than leave the FR-008 gate reading no contexts and passing.
- **FR-013**: The committed ruleset MUST reproduce the live one as read at the time of writing, so this
  feature changes what is enforced in no way at all.
- **FR-014**: The apply workflow MUST NOT be a published capability. Nothing outside this repository
  calls it.

### Key Entities

- **Committed ruleset**: a file under `.github/rulesets/` naming the branches it targets, its
  enforcement, its rules, its required contexts and its bypass actors. The single owner of what the
  default branch requires.
- **Composed context**: a check name a consumer or a ruleset can require, being a calling job's name
  and, where that job calls a capability, the called job's name after it.
- **Published surface**: `tests/published_surface.toml`, already the owner of every capability's
  `check_name` and `skips_under`. This feature reads it and adds nothing to it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Renaming any job that composes a required context fails the pull request that does it,
  before review.
- **SC-002**: What the default branch requires is answerable by reading one file in the tree, with no
  API call and no visit to the settings UI.
- **SC-003**: `mise run ci` reaches both verdicts with the network unavailable.
- **SC-004**: Bringing GitHub back into agreement with the tree is two dispatches and no hand edit in the
  UI — one that shows the difference, one that writes it.
- **SC-005**: A ruleset edited by hand is reported rather than lost: no dispatch at its defaults writes
  anything, so nothing is overwritten before a maintainer has read the difference.
- **SC-006**: The enforced ruleset is unchanged by this feature — the same contexts are required before
  and after.

## Assumptions

- `turbobasic-repo-automation` already holds `administration: write`, so no new token, App or secret is
  created. The apply workflow uses it.
- The `admin` bypass actor on the live ruleset stays. It is what let the retired context be diagnosed at
  all, and removing it is a separate decision.
- Only `protect-default-branch` is codified. This repository has one ruleset and organisation-level
  rulesets are not ours to write.
- `published_surface.toml` is authoritative for called job names and needs no new field. If the plan
  finds it does, that is a change to a file whose whole purpose is to arrive as a deliberate diff, and
  is called out there.
- `check-jsonschema` ships no builtin schema for a repository ruleset, and a `--schemafile <url>` would
  put the network in `mise run ci`. FR-012 therefore says what must be asserted rather than which tool
  asserts it. `.github/actionlint.yaml` is the standing precedent for a GitHub config file with no
  builtin schema, and the plan records why this one is not simply left the same way.
- Publishing this as a capability for consumers is explicitly out of scope. Every consumer has the same
  exposure, and the issue says so; this feature earns the right to that conversation by working here
  first.
- Required contexts on branches other than the default are out of scope, as the live ruleset targets
  only `~DEFAULT_BRANCH`.
