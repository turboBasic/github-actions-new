# Implementation Plan: The Ruleset In The Tree

**Branch**: `002-ruleset-in-tree` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-ruleset-in-tree/spec.md`

## Summary

Move the one fact nothing in the tree can see — what the default branch requires — into the tree, and put
a gate on it.

`.github/rulesets/protect-default-branch.json` becomes the owner of the required contexts.
`tests/capabilities.py` learns to compose a check name from a calling job and a called capability, so a
new test can assert every required context both resolves and is capable of judging. A dispatch-only
workflow applies the file, dry by default, printing what it would change. The contents are unchanged from
what is enforced today, so the first real dispatch is a no-op.

## Technical Context

**Language/Version**: Python 3.14, standard library only for anything a workflow runs. YAML reading in the
suite uses `pyyaml`, already a dev dependency.

**Primary Dependencies**: none added. `gh` (on the runner) for the two API calls;
`actions/create-github-app-token` for the token, already used by `release-proposal.yml`.

**Storage**: files in the tree. `.github/rulesets/*.json` is the new one.

**Testing**: pytest, offline. The decision unit is imported and called; the ruleset and the workflows are
read as structures.

**Target Platform**: `ubuntu-latest` runners, and a maintainer's machine via `mise run ci`.

**Project Type**: a repository of reusable GitHub Actions capabilities. This feature adds internal surface
only — nothing here is published (FR-014).

**Performance Goals**: none. The gate reads a handful of files; the workflow makes two API calls.

**Constraints**: the suite must reach both verdicts with no network (FR-011). Applying must be reachable
only by dispatch (FR-003). The enforced ruleset must not change (FR-013).

**Scale/Scope**: one ruleset, eight composed contexts, three of them required.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Standing | Reading |
| --- | --- | --- |
| I — One owner per fact | **This feature exists to satisfy it** | The required contexts move from the settings UI into one file. The risk is introducing a *second* copy, which R1, R6 and R9 each turn down: the committed file holds only what a write accepts, the gate reads `published_surface.toml` rather than restating it, and no last-applied fingerprint is recorded. |
| II — Secrets never persist | Pass | The App token is minted in the run and written nowhere. No ruleset field holds a secret. |
| III — Gates are never loosened | **Watch** | R2 declines a `check-jsonschema` hook the conventions layer asks for. That is a convention, not a gate, and nothing is silenced: what the schema would have caught is asserted in the suite instead, and the departure is reported in R2 and in Complexity Tracking below. |
| IV — What a consumer cannot absorb needs a new line | Pass | Nothing published changes. `apply-ruleset.yml` has no `workflow_call` trigger and `ruleset-decisions` is named by no capability, so no consumer can resolve either. R7 keeps both out of the release surface so neither moves a version. |
| V — A published ref cannot be withdrawn | Pass | No tag, no ref, no release path touched. |
| VI — Caller-controlled text never reaches a command line | **Load-bearing** | A ruleset name and a check context are text from a file, and the workflow holds an `administration: write` token. Every value reaches `rulesets.py` as an environment value or a file path, and every `gh api` body goes in through `--input`, never as an interpolated argument. `test_no_interpolation.py` already reads the action tree; this action is added to what it covers by being there. |
| VII — A required gate never passes without judging | **This feature enforces it** | FR-009 is principle VII made structural: no context composed by a job that can skip may be required. The new test itself must not pass vacuously — hence FR-012, and hence the pre-flight below. |

### Two gates this plan owes its own gate

- **The composer must be pre-flighted.** A gate that reads a context out of a workflow reports green if it
  reads nothing. The conventions layer already states the rule — pre-flight the line out of the file,
  never a retyping of it — and `test_the_table_reader_finds_a_table_it_is_given` is the pattern to follow.
  The composer is asserted against `ci.yml` by name: it must produce `ci / python-ci`, or the gate is
  reading the wrong thing.
- **`ci.yml`'s own required context is now named in the tree twice** — once composed from the workflow,
  once required by the ruleset. That is the gate, not a duplication: one is derived, one is declared, and
  the whole point is that they are compared.

## Project Structure

### Documentation (this feature)

```text
specs/002-ruleset-in-tree/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ruleset-decisions.md   # the internal action's contract
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
.github/
├── rulesets/
│   └── protect-default-branch.json   # NEW — the owner of what the default branch requires
└── workflows/
    └── apply-ruleset.yml             # NEW — dispatch only, dry by default

actions/
└── ruleset-decisions/                # NEW — internal, unpublished, stdlib only
    ├── action.yml
    └── rulesets.py

tests/
├── capabilities.py                   # EDIT — gains context composition and skip reasons
├── conftest.py                       # EDIT — puts the new action on the path
├── published_surface.toml            # EDIT — a row for ruleset-decisions, published = false
├── test_ruleset_contexts.py          # NEW — FR-008, FR-009, FR-010, FR-012
└── test_ruleset_decisions.py         # NEW — FR-002, FR-004, FR-005, FR-006, FR-007

pyproject.toml                        # EDIT — pyright extraPaths, release exclude (R7)
.pre-commit-config.yaml               # EDIT — check-json, from the hook repo already pinned
docs/ai-instructions.md               # EDIT — the CI section's claim becomes false
AGENTS.md                             # EDIT — a new layer 3 artefact needs its row
README.md                             # CHECKED, no change expected — it describes what consumers
                                      #   resolve, and nothing here is published (FR-014)
```

**Structure Decision**: no new top-level directory and no new Python home. The decision unit goes in
`actions/`, which pyright, ruff, zizmor, `test_action_pins.py` and `test_no_interpolation.py` already
cover — see R3. `.github/rulesets/` is a new directory but not a new file type: JSON is already in the
tree, so `.editorconfig`, `.gitattributes` and `.gitignore` need nothing.

## Implementation shape

Sequenced so that each step is a green commit and the destructive one is last.

1. **The committed ruleset, and the shape assertion.** `.github/rulesets/protect-default-branch.json`
   reproducing the live ruleset field for field (R1, R10), plus the FR-012 assertions. Nothing reads the
   required contexts yet, so this commit changes no verdict.
2. **The composer.** `tests/capabilities.py` gains `composed_contexts()` and the skip reasons (R6), with
   the pre-flight against `ci.yml`. Standalone and useful: it makes the eight contexts readable.
3. **The gate.** `test_ruleset_contexts.py` — FR-008, FR-009, FR-010. This is the commit that would have
   caught the `gates`→`ci` rename. Verify by renaming `ci.yml`'s job on a scratch commit and watching the
   suite fail with the right message, then reverting.
4. **The decision unit.** `actions/ruleset-decisions/` plus `test_ruleset_decisions.py`, both offline. The
   unit answers `create` / `update` / `nothing` / `refuse`, renders the write body, and renders the
   field-by-field difference. Nothing invokes it yet.
5. **The applier.** `.github/workflows/apply-ruleset.yml`, plus the `published_surface.toml` row and the
   pyproject edits from R7. Verified by dispatch in dry run, which must report nothing to change.
6. **The documentation.** README, `docs/ai-instructions.md`, `AGENTS.md`. The instruction that a rename
   must edit the ruleset now names the file that holds it; leaving the old framing standing would be the
   stale-framing defect the conventions layer calls out.

The first non-dry dispatch is deliberately **not** part of this feature's verification. It is a no-op by
R10, and it is the one action here that no revert undoes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No `check-jsonschema` hook for a new GitHub config file, against the conventions layer | The tool ships no schema for a repository ruleset and a remote one would put the network in `mise run ci`. What a schema would catch is asserted in the suite instead, where it can also catch the vacuous-pass case a schema could not | A vendored schema would be a second owner of a shape the API owns, and could not be checked against the API offline. `.github/actionlint.yaml` already sets the precedent for this exact case. See R2 |
| A new composite action for logic one workflow calls | The conventions layer wants a decision callable rather than a `run:` block, and `actions/` is the only Python home this repository has wired | A `run:` block cannot be unit-tested offline; a new top-level directory would need two pyproject edits and would leave two Python homes. See R3 |
