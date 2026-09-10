---

description: "Task list for 002-ruleset-in-tree"
---

# Tasks: The Ruleset In The Tree

**Input**: Design documents from `/specs/002-ruleset-in-tree/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/ruleset-decisions.md](./contracts/ruleset-decisions.md)

**Tests**: included, and not optionally. The gate *is* the deliverable — FR-008 to FR-012 are all
assertions, and User Stories 2 and 3 have no product other than a failing suite.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependency on an unfinished task
- **[Story]**: US1, US2, US3 as numbered in [spec.md](./spec.md)
- Paths are repository-relative

## Path conventions

No `src/`. This repository's Python lives in `actions/<name>/` for anything a workflow runs and in
`tests/` for the suite — see [R3](./research.md#r3--where-the-apply-logic-lives). Nothing here introduces
a third location.

## Standing constraints

Every task below is subject to these. They are gates already in the tree, and each has bitten a change
of this shape before:

- **`test_no_run_block_interpolates_caller_controlled_text`** reads every `run:` in
  `.github/workflows/*.yml` **and** `actions/*/action.yml`, and forbids `inputs` among others. A `run:`
  in either file passes values through `env:`. An `if:` may read `inputs` — only `run:` is scanned.
- **`test_no_secret_reaches_anything_but_a_step_input`** allows `secrets.*` only inside a step's `with:`.
- **`test_every_permission_carries_its_reason_beside_it`** matches any line of the form
  `<lower-kebab>: read|write|none`, which includes `permission-administration: write` in a
  `create-github-app-token` `with:` block. Every such line carries `# reason` on the same line.
- **`custom.github-workflows-require-timeout`** requires `timeout-minutes` on every job.
- **`test_every_third_party_reference_is_pinned_to_a_full_sha`** — a full SHA with a `# vN` comment.
  `$/` names this repository and takes no ref.
- **No docstrings, no multi-line comment blocks.** Comments only where the WHY is non-obvious.
- Run `mise run ci` before each commit. Conventional Commits subject.

---

## Phase 1: Setup

**Purpose**: put the live ruleset in the tree, byte-checked, before anything reads it.

- [X] T001 Create `.github/rulesets/protect-default-branch.json` holding exactly the six writable fields
      from [R1](./research.md#r1--what-the-committed-file-holds) — `name`, `target`, `enforcement`,
      `conditions`, `rules`, `bypass_actors` — transcribed from the live ruleset, not retyped:

      ```bash
      GH_TOKEN=$(gh auth token -u turboBasic) gh api \
        repos/turboBasic/github-actions-new/rulesets/22481092 \
        | jq '{name, target, enforcement, conditions, rules, bypass_actors}' \
        > .github/rulesets/protect-default-branch.json
      ```

- [X] T002 Prove T001 is faithful: re-read the live ruleset, project it the same way, and diff against
      `.github/rulesets/protect-default-branch.json` with `jq -S`. A difference here means the
      transcription is wrong, and
      [FR-013](./spec.md#functional-requirements) and SC-006 both hang on it being exact.
- [X] T003 [P] Add `- id: check-json` to the `pre-commit/pre-commit-hooks` block in
      `.pre-commit-config.yaml` (rev `v6.0.0`, already pinned). Then run `mise exec -- prek run --all-files`
      and confirm it does not claim `.markdownlint-cli2.jsonc`; if `identify` tags JSONC as JSON, add an
      `exclude:` for it with the reason on the line above. This is syntax only, and deliberately not a
      schema — see T006.

**Checkpoint**: the ruleset is in the tree and reproducible from the API. Nothing reads it yet, so no
verdict has changed.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: the loader and the shape assertions. Both stories read the committed file, and a malformed
file would make each of their gates pass on an empty set — which is the very failure this feature exists
to prevent, reappearing inside it.

**⚠️ No user story work begins until this phase is complete.**

- [X] T004 In `tests/capabilities.py` — already the one owner of how a workflow is read — add
      `RULESET_DIR = REPO / ".github" / "rulesets"`, `ruleset_docs() -> dict[str, Doc]` keyed by file stem,
      `WRITABLE_FIELDS`, and `required_contexts(doc) -> list[str]` reading
      `rules[type == required_status_checks].parameters.required_status_checks[].context`. Full type hints;
      `json.loads`, not a new dependency.
- [X] T005 In `tests/test_ruleset_contexts.py` (new), the [FR-012](./spec.md#functional-requirements)
      assertions from [data-model.md](./data-model.md#validation-fr-012): the key set is exactly
      `WRITABLE_FIELDS`; exactly one rule is `required_status_checks`; its context list is non-empty and
      every entry has a non-empty `context`; `target` is `branch`.
- [X] T006 In the same file, record beside those assertions why there is no `check-jsonschema` hook —
      [R2](./research.md#r2--no-schema-hook) in two or three lines, stating the rule and not the history:
      the tool ships no ruleset schema, a remote one would put the network in `mise run ci`, and unlike
      `.github/actionlint.yaml` a mis-keyed field here fails *green* rather than safe. JSON carries no
      comments, so this is the only place the reason can live next to what enforces it.
- [X] T007 Pre-flight `required_contexts()` against a literal built in the test, per the conventions
      layer: a reader that silently stops matching reports green over a file full of retired names. Assert
      it finds a context it is given, and returns `[]` for a ruleset with no such rule.

**Checkpoint**: `mise run ci` green. A malformed ruleset now fails; a correct one asserts nothing yet.

---

## Phase 3: User Story 1 — The ruleset has one owner (Priority: P1)

**Goal**: what the default branch requires is edited in the tree and applied from it, so the committed
file is the fact rather than a copy of one.

**Independent Test**: edit the committed ruleset, dispatch in dry run, and see the difference printed with
nothing written; dispatch again with the dry run off and read the change back from GitHub.

### Implementation for User Story 1

- [X] T008 [US1] `actions/ruleset-decisions/rulesets.py` — the decision unit from
      [contracts/ruleset-decisions.md](./contracts/ruleset-decisions.md). Standard library only, every
      argument from the environment (`COMMITTED`, `LIVE`, `BODY_PATH`), nothing written outside
      `BODY_PATH`. Normalise per [R4](./research.md#r4--comparison-by-meaning); select the live match per
      [R5](./research.md#r5--finding-the-ruleset); emit `verdict`, `ruleset-id`, `difference`, `body`,
      `message` to `GITHUB_OUTPUT`. Mirror `actions/release-decisions/decisions.py` for shape.
- [X] T009 [US1] Every failure message names what was read, what it was compared against, and what to do
      about it — the four rows in
      [the contract's failure table](./contracts/ruleset-decisions.md#failure-messages). A malformed
      committed file is a `refuse` verdict, not a traceback.
- [X] T010 [P] [US1] `actions/ruleset-decisions/action.yml` — composite, inputs `committed`, `live`,
      `body-path`; outputs as above; one step passing every value through `env:` and running
      `python3 "$GITHUB_ACTION_PATH/rulesets.py"`. Copy the env-only discipline from
      `actions/release-decisions/action.yml` — principle VI, and `test_no_interpolation.py` reads this
      file.
- [X] T011 [P] [US1] `tests/conftest.py` — insert `actions/ruleset-decisions` on `sys.path` beside the
      existing entry, with the same reason it already carries: a hyphen in the directory name means it is
      not importable as a package.
- [X] T012 [US1] `pyproject.toml` — add `actions/ruleset-decisions` to `[tool.pyright].extraPaths`, and
      add `actions/ruleset-decisions` to `[tool.turbobasic-release].exclude` per
      [R7](./research.md#r7--release-relevance). The open question there is settled: `matches()` in
      `decisions.py` tries `fnmatch(path, f"{pattern}/*")`, so the bare directory covers both files and no
      glob is needed. Keep the exclude list sorted as it is.
- [X] T013 [US1] `tests/published_surface.toml` — a row for `ruleset-decisions`: `kind = "action"`,
      `published = false`, empty `inputs`, `permissions`, `tool_prerequisites` and `skips_under`, mirroring
      `release-decisions`. Without it `test_every_capability_in_the_tree_is_in_the_fixture` fails, which is
      the gate working.
- [X] T014 [US1] `tests/test_ruleset_decisions.py` — the four verdicts from
      [data-model.md](./data-model.md#apply-verdict): `create` when no live ruleset carries the name,
      `nothing` when the projection matches, `update` with a populated `difference` when it does not,
      `refuse` when two rulesets share the name ([FR-007](./spec.md#functional-requirements)). Plus: a live
      ruleset carrying `updated_at` and `_links` still reads as `nothing`, and reordered `rules` and
      `required_status_checks` still read as `nothing` — R4's whole point. Offline; the live side is a
      fixture built in the test.
- [X] T015 [US1] `.github/workflows/apply-ruleset.yml` — `workflow_dispatch` only
      ([FR-003](./spec.md#functional-requirements)), inputs `ruleset` and `dry-run` with `dry-run`
      defaulting to `true` (FR-004, [R9](./research.md#r9--why-there-is-no-drift-refusal)); one job with
      `timeout-minutes`; `contents: read` on the run's token for the checkout; an App token from
      `actions/create-github-app-token` narrowed to `permission-administration: write`
      ([R8](./research.md#r8--the-token)), following `release-proposal.yml`. Reads with
      `gh api repos/$GH_REPO/rulesets` into `$RUNNER_TEMP/live.json`, calls
      `uses: $/actions/ruleset-decisions`, prints the difference unconditionally (FR-005), and writes with
      `gh api --input "$body"` only when the verdict is `create` or `update` **and** the dry run is off.
      Never a body as an argument. Every permission line carries its reason.
- [X] T016 [US1] Add `.github/workflows/apply-ruleset.yml` to `[tool.turbobasic-release].exclude` in
      `pyproject.toml` — same reason as T012, and the same reason every other caller workflow of this
      repository is already listed there. (Already present from the proactive T012 edit; confirmed still
      correct once the workflow file existed.)
- [X] T017 [US1] Verify by dispatch, in dry run, after the branch has merged:
      `gh workflow run apply-ruleset.yml`. Expect **nothing to change**
      ([R10](./research.md#r10--what-the-first-apply-must-not-change)). A difference means T001 was
      transcribed wrong — read it and do not proceed to a real dispatch.

      Run `34533773004`: nothing to change, write skipped. The Assumption that the App already held
      `administration: write` was wrong; it was granted and accepted first.

      `create` and `update` were exercised afterwards, beyond this phase, against a `disabled` scratch
      ruleset targeting no existing branch — each verified field-for-field, then deleted.

**Checkpoint**: applying works and is a no-op. Nothing has been written to GitHub.

---

## Phase 4: User Story 2 — A retired context fails the pull request (Priority: P2)

**Goal**: renaming a calling job, retiring a workflow or making a job conditional fails the pull request
that does it, naming what would stop reporting.

**Independent Test**: rename `ci.yml`'s job and watch `tests/test_ruleset_contexts.py` fail naming
`ci / python-ci`; restore it and watch the suite pass.

### Implementation for User Story 2

- [X] T018 [US2] In `tests/capabilities.py`, add the composer from
      [R6](./research.md#r6--the-gates-two-halves): for every workflow under `.github/workflows`, for every
      job, the calling half is the job's `name` falling back to its id; where `uses:` names a capability in
      this repository, one context per `check_name` that capability records in `published_surface.toml`,
      spelled `<calling half> / <called job>`. A job calling nothing composes its own name alone. Return a
      `NamedTuple` carrying the fields in
      [data-model.md](./data-model.md#composed-context) so a failure can name provenance.
- [X] T019 [US2] Pre-flight the composer against the tree by name: it must produce `ci / python-ci` from
      `ci.yml`, both `commits / pr-title` and `commits / commit-messages` from `commit-messages.yml`, and
      `propose` from `release-proposal.yml`. This is the gate on the gate — a composer that stops reading
      `uses:` would otherwise report green over every retired name at once.
- [X] T020 [US2] In `tests/test_ruleset_contexts.py`, [FR-008](./spec.md#functional-requirements): every
      required context in every committed ruleset is composed by the tree. Both halves — a context naming a
      called job that `published_surface.toml` does not record fails too.
- [X] T021 [US2] [FR-010](./spec.md#functional-requirements): the failure names the context, where it is
      required, what composes it or fails to, and that the committed ruleset must be edited in the same
      change. Assert the message content, not only the failure — a gate whose message says nothing is an
      exit code, and the conventions layer says that is not a result.
- [X] T022 [US2] Assert the deliberate non-failure: a context the tree composes but the ruleset does not
      require passes. Requiring more is a maintainer's decision and not this gate's
      ([spec.md Story 2, scenario 4](./spec.md#user-story-2---a-retired-context-fails-the-pull-request-priority-p2)).
- [X] T023 [US2] Prove it can fail. Rename `ci.yml`'s job `ci` to `gates`, run
      `uv run pytest tests/test_ruleset_contexts.py`, read the message, restore the file. This is the exact
      change that went unnoticed for six commits in `001-consumer-contract`; if the suite passes, the gate
      is reading the wrong thing.

**Checkpoint**: the rename that opened issue #6 is now impossible to land.

---

## Phase 5: User Story 3 — A gate that cannot judge (Priority: P3)

**Goal**: a context that resolves but would report green without judging cannot be added to the required
list.

**Independent Test**: add `advisory / prek-advisory` to the committed required list and watch the suite
fail quoting that capability's own recorded skip reason.

### Implementation for User Story 3

- [X] T024 [US3] In `tests/capabilities.py`, add `cannot_judge` to the composed context, set by whichever
      of the three conditions in [data-model.md](./data-model.md#composed-context) holds, carrying the
      reason as text: a fixed sentence naming the capability when it is marked `judges = false` in
      `published_surface.toml`, the calling job's `if:` verbatim, or the events the calling workflow does
      declare. A capability's `skips_under` entry does not by itself disqualify a context — see
      [data-model.md](./data-model.md#composed-context) for why `commits / pr-title` and
      `commits / commit-messages` must stay unaffected by it.
- [X] T025 [US3] Pre-flight it against the tree by name: `advisory / prek-advisory` and
      `describe / pr-description` must come back with a reason, both `release-on-merge` contexts and
      `propose` must come back with the no-`pull_request` reason, and `ci / python-ci` must come back with
      none.
- [X] T026 [US3] [FR-009](./spec.md#functional-requirements): no required context may carry
      `cannot_judge`. One test, three reasons, and the failure quotes whichever reason applied — principle
      VII made structural rather than written down.
- [X] T027 [US3] Prove it can fail, three ways: add `advisory / prek-advisory` to the committed required
      list (`judges = false`), then `release / tag-and-publish` (no `pull_request` trigger), then
      `apply` (same — the applier's job calls no reusable workflow, so its composed context is its own
      job name with no prefix). Each must fail with its own reason. Restore the file after each.

**Checkpoint**: both halves of the gate hold. Every requirement in the spec is asserted by something that
can fail.

---

## Phase 6: Polish & documentation

**Purpose**: the tree now says something the documentation contradicts. Stale framing is a defect, not a
follow-up.

- [X] T028 `docs/ai-instructions.md`, the CI section's claim that **"nothing in the tree can see it"**
      (not "line 165" as originally written here — that line number named the section's opening
      sentence, not the false claim, which sits two lines below it; a citation that drifts with the
      first edit it prompts is the wrong kind of precision, so the fix is quoted by text instead). The
      claim is now false, and the instruction it justifies has become a gate. Rewritten to name
      `.github/rulesets/` as the owner and `tests/test_ruleset_contexts.py` as the gate that holds it.
      Dropped the "Two names are never required" list in the same edit: `published_surface.toml`'s
      `judges` field and the gate own that fact now, and a prose copy of it is the second owner
      principle I forbids.
- [X] T029 [P] `AGENTS.md`, the layer 3 table. Add a row for `.github/rulesets/` — "what the default
      branch requires, and what a consumer's ruleset would require of it". Nothing else in that table
      answers it.
- [X] T030 [P] Check `README.md` and expect no change: it describes what a consumer resolves, and neither
      the applier nor the action is published ([FR-014](./spec.md#functional-requirements)). Its existing
      statements about retiring a context are consumer-facing and stay true. Say so in the pull request
      rather than editing to prove the check happened.
- [X] T031 Check `docs/technical-debt.md` and expect no row. R2's departure from the schema convention is
      a settled decision with its reason recorded beside what enforces it (T006), not a shortcut nobody
      will fix — and the doc's own admission bar requires all three of its conditions.
- [X] T032 `mise run ci` with the network unavailable, confirming
      [SC-003](./spec.md#measurable-outcomes). Not "it passed on a machine with wifi".
- [X] T033 Walk [quickstart.md](./quickstart.md) end to end and correct anything it gets wrong about the
      code as built. The `composed_contexts()` snippet already matched the built composer; what had gone
      stale was the count (eight contexts → nine, once `apply-ruleset.yml` joined the tree), the
      `prek-advisory` proof's expected reason (it quoted a `skips_under` sentence; the actual reason now
      comes from `judges = false`, per the Phase 5 fix), and both `gh workflow run apply-ruleset.yml`
      examples, which omitted the now-required `ruleset` input.

---

## Dependencies & execution order

### Phase dependencies

- **Phase 1** — no dependencies.
- **Phase 2** — needs Phase 1. **Blocks every story**: both gates read the committed file, and a malformed
  one makes both pass on an empty set.
- **Phases 3, 4, 5** — each needs Phase 2 and none needs another. US1 writes to GitHub; US2 and US3 only
  read the tree.
- **Phase 6** — needs whichever stories landed.

### Recommended order, which is not the priority order

Land **Phase 4 and Phase 5 before Phase 3**, and in particular before T017.

US1 is P1 because the committed file has to be the fact before a gate reading it means anything — and
Phase 1 already delivers that half. What is left in Phase 3 is the applier, and applying is the one act
here that no revert undoes: a wrong ruleset blocks every pull request in the repository, including the one
that would fix it. The gate is what makes the committed file worth applying, so it goes first.

Nothing enforces this. It is the order to choose absent a reason not to.

### Within each story

- The pre-flight comes with the reader it checks, never after — T007 with T004, T019 with T018, T025 with
  T024. A reader committed without one is a gate nobody has seen fail.
- The proof-of-failure task closes each story: T023, T027. Reverting the scratch edit is part of the task.

### Parallel opportunities

- T003 alongside T001 and T002 — different file.
- T010, T011 alongside T008 and T009 — the action's YAML and the path wiring do not wait on the module.
- T029, T030, T031 with each other — three different files, three independent checks.
- Phases 4 and 5 in parallel with Phase 3, if two people are on it. They touch `capabilities.py` and
  `test_ruleset_contexts.py`; Phase 3 touches neither except `published_surface.toml`, which Phase 4 reads
  and does not write.

Phases 4 and 5 both edit `capabilities.py` and `test_ruleset_contexts.py`, so they are sequential with
each other.

---

## Implementation strategy

### The smallest thing worth landing

Phases 1, 2 and 4. That is the committed ruleset, its shape assertions, and the gate that fails on a
retired context — which is the whole of issue #6's complaint. The applier can follow; until it does, the
ruleset is applied by hand as it is today, and the committed file is a second copy for exactly as long as
that lasts. Do not stop there deliberately: [R1](./research.md#r1--what-the-committed-file-holds)'s second
copy is what principle I forbids, and this is a staging order rather than a shipping one.

### Incremental delivery

1. Phases 1 + 2 → the ruleset is in the tree and cannot be malformed.
2. Phase 4 → a retired context fails the pull request. **This is the issue closed.**
3. Phase 5 → a context that cannot judge cannot be required.
4. Phase 3 → the tree becomes the applied source, and the hand edit goes away.
5. Phase 6 → the documentation stops contradicting the tree.

### What this feature must not change

The enforced ruleset. Same three required contexts before and after
([FR-013](./spec.md#functional-requirements), SC-006). If the first real dispatch reports a change, stop
and read it — a wrong apply cannot be reverted, and being a no-op is the only reason this feature is safe
to land in one pull request.

---

## Notes

- One green commit per task or per logical group, Conventional Commits subject.
- `mise run ci` before each commit. Auto-fixing hooks are normal — re-stage and retry.
- Two tasks deliberately produce no diff: T030 and T031 are checks whose result is reported in the pull
  request. A check that quietly edits something to look productive is worse than the check.
- This feature's own required contexts do not change, so this repository's branch ruleset needs no edit to
  merge this work — the one time that is true of a change to what reports.
