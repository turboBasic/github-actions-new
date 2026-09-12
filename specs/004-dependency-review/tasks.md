---

description: "Task list for 004-dependency-review"
---

# Tasks: One check over what a change starts depending on

**Input**: Design documents from `/specs/004-dependency-review/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md),
[contracts/published-surface-delta.md](contracts/published-surface-delta.md), [research.md](research.md),
[quickstart.md](quickstart.md)

**Tests**: This feature's tests are the gates themselves (pytest, offline) — not a separate test-first
pass. Each implementation task below states the gate it must keep green or newly turn green. `.cspell/project.txt`
already carries `OpenSSF` and `ghsas` from Phase 0 research and needs no further edit.

## Phase 1: Setup

None. No new dependency, tool, or scaffolding is introduced; every file this feature touches already
exists in the tree.

## Phase 2: Foundational

None. The capability itself is User Story 1's deliverable — there is no shared infrastructure to stand
up before it.

---

## Phase 3: User Story 1 - An advisory is refused (Priority: P1) 🎯 MVP

**Goal**: Publish `.github/workflows/dependency-review.yml`, whose one job reads the pull request's
dependency-graph difference through the pinned `actions/dependency-review-action` and reddens on an
advisory at or above the severity floor.

**Independent Test**: Copy the call site into a repository whose dependency graph is on, open a pull
request adding a dependency version with a known advisory, and confirm the check fails naming the
advisory, package and version (Scenario 1.1); move to a clean version and confirm it passes (1.2); open
a pull request touching no manifest and confirm it passes on an empty difference (1.3). This is the
"Online" half of [quickstart.md](quickstart.md) — not part of `mise run ci`.

- [X] T001 [US1] Create `.github/workflows/dependency-review.yml`:
  `name: 🧩 dependency-review`; `on: workflow_call:` declaring exactly one input,
  `fail-on-severity` (`type: string`, `default: low`, with a description naming what it governs);
  workflow-level `permissions: {}`; one job `dependency-review` (`runs-on: ubuntu-latest`,
  `timeout-minutes: 5` as a literal — this capability takes no timeout input, per FR-005) with
  job-level `permissions: { contents: read }` and the reason on the same line (matches the
  `PERMISSION` regex in `tests/test_workflow_properties.py`, e.g.
  `contents: read # the difference is read from the API with this token`); one step, `id: review`,
  `uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0`, with
  `with:` carrying only `fail-on-severity: ${{ inputs.fail-on-severity }}`. No `actions/checkout`
  step, no `if:` yet (Phase 5/US3 adds the event pin and the diagnostic step in the same file).

- [X] T002 [US1] Add the `[dependency-review]` table to `tests/published_surface.toml`, positioned
  with the other capabilities: `kind = "workflow"`, `published = true`,
  `check_name = ["dependency-review"]`, `inputs = ["fail-on-severity"]`,
  `permissions = { contents = "read" }`, `tool_prerequisites = []`, `skips_under = []` (an empty list
  is truthful until T007's `if:` exists; T008 **replaces** this line with an array-of-tables entry,
  because TOML refuses a key defined both ways). Run
  `uv run pytest tests/test_published_surface.py` and confirm
  `test_every_capability_in_the_tree_is_in_the_fixture`,
  `test_every_published_input_name_set_matches_the_fixture` and
  `test_every_permission_demand_matches_the_fixture` pass.

- [X] T003 [P] [US1] In `tests/test_workflow_properties.py`, add a gate asserting the capability's only
  `uses:` is the pinned action (FR-002, FR-015): read the steps of job `dependency-review` in
  `dependency-review.yml` (reuse the existing `steps_of(name, job_id)` helper already in this file),
  collect every step's `uses:` value, and assert there is exactly one, whose slug — the part before
  `@` — is `actions/dependency-review-action`. **Do not name the digest.** The workflow owns the pin
  and `test_action_pins.py` owns whether it is a full SHA; repeating the digest here would make a pin
  bump two edits with the suite as the thing that reddens, which is the second owner the surface
  fixture refuses for defaults. The failure message must name what was found and that a checkout or a
  task-runner step is what FR-002/FR-015 forbid.

- [X] T003a [P] [US1] Beside T003's gate, add its pre-flight (FR-022): factor the slug-collecting
  logic into a helper taking a step list, and assert it refuses a synthetic list carrying an
  `actions/checkout@<sha>` step alongside the real one. The gate's steady state is a one-element set,
  so without this a change that stopped the collector finding anything would report green over a
  capability that checks the caller's tree out. Mirror the shape of
  `test_the_permission_reader_tells_an_explained_grant_from_a_bare_one` in this file.

**Checkpoint**: A pull request against a repository whose dependency graph is on and that calls this
file directly now reddens on an advisory and passes otherwise. `mise run ci` is green.

---

## Phase 4: User Story 2 - Adopting it costs one permission (Priority: P1)

**Goal**: Make the permission surface and the single input a property the suite asserts, not merely a
property of how `dependency-review.yml` happens to be written today.

**Independent Test**: Copy the published call site unchanged into a repository, grant `contents: read`
and nothing else, and confirm the run starts and the check reports (Scenario 2.1). Read the capability's
declared inputs and confirm there is exactly one, carrying a description and an explicit default
(Scenario 2.4).

- [X] T004 [P] [US2] In `tests/capabilities.py`, add a reader `declared_input_specs(doc: Doc) -> dict[str, Doc]`
  returning, for each name in a workflow's `workflow_call.inputs`, the input's own mapping (so a caller
  can check for `description` and `default` without a second YAML walk). Mirror the existing
  `declared_inputs` function immediately above it in structure and docstring style.

- [X] T005 [US2] In `tests/test_workflow_properties.py`, add a gate (FR-007, FR-008) asserting the
  `with:` block of `dependency-review.yml`'s `review` step carries exactly the key `fail-on-severity`
  and no other — refusing `comment-summary-in-pr`, `warn-only`, `allow-licenses`, or any other key the
  action declares. Include a pre-flight assertion on the same helper/logic using a synthetic `with:`
  dict containing `comment-summary-in-pr: always`, proving the gate would catch it, in the style of
  `test_the_permission_reader_tells_an_explained_grant_from_a_bare_one` elsewhere in this file. The
  failure message must name the keys found, the one key allowed, and — for `comment-summary-in-pr`
  specifically — that `always` or `on-failure` demands `pull-requests: write`, which every caller would
  then have to grant before any job exists (FR-024).

- [X] T006 [US2] In `tests/test_workflow_properties.py`, add a gate (FR-004) asserting every input
  declared by every *published* capability (read `fixture()` for `published == true` rows, `kind ==
  "workflow"`) carries both a non-empty `description` and an explicit `default` key in the real
  workflow YAML, via `declared_input_specs` from T004. Include a pre-flight test using a synthetic
  input mapping missing `description`, proving the gate would catch it. The failure message must name
  the capability, the input and which of the two keys is missing, and say that an input whose behaviour
  when unset is unwritten is a promise with nothing behind it (FR-024). This gate is generic — it also
  runs today against `python-ci`, `conventional-commits`,
  `pr-description`, `release` and `prek-advisory`'s inputs, all of which already pass.

**Checkpoint**: Granting only `contents: read` starts the run (already true from T001's job-level
block and the existing generic `test_every_permission_demand_matches_the_fixture`); the two new gates
now hold the single-input, no-extra-key shape as a property the suite defends rather than a fact that
happens to be true today.

---

## Phase 5: User Story 3 - Honest about what it does not judge (Priority: P2)

**Goal**: The job does no work under any event but `pull_request`, that skip is registered with its
reason, a run that fails because the *caller's* dependency graph is off says so and says this capability
cannot fix it, and the consumer-facing reference states all of this plus what only informs.

**Independent Test**: Read `README.md`'s new section against `dependency-review.yml`'s own YAML and
`tests/published_surface.toml`'s skip entry, and confirm the skip, its event and its reason agree
(Scenario 3.1, 3.2). Open a pull request against a repository whose dependency graph is off and confirm
the run fails naming the setting, the path to change it, and that this capability cannot change it
(Scenario 3.3 — the "Online" half of quickstart.md).

- [X] T007 [US3] In `.github/workflows/dependency-review.yml`, on the `dependency-review` job, add
  `if: github.event_name == 'pull_request'` (FR-010). Add one further step after `review`,
  `id: graph-off` — the id is what T009's gate finds it by, so the condition below stays owned by this
  file alone — gated `if: failure() && steps.review.outputs.dependency-changes == ''` (the
  discriminator research.md establishes: that output is set only once the comparison was actually
  read), with a `run:` block that
  interpolates nothing — building the settings path from `$GITHUB_SERVER_URL` and `$GITHUB_REPOSITORY`
  — and emits one `::error::` naming the dependency-graph setting, that path, and that this capability
  cannot switch it on for the caller (FR-011).

- [X] T008 [US3] In `tests/published_surface.toml`, **delete the `skips_under = []` line T002 wrote**
  under `[dependency-review]` and add in its place, after the table's other keys:

  ```toml
  [[dependency-review.skips_under]]
  jobs = ["dependency-review"]
  event = "any event but pull_request"
  reason = "there is no base and no head to difference, so there is nothing to judge"
  ```

  Deleting the line is not tidying: TOML refuses a key defined as both an empty array and an array of
  tables — `tomllib` raises `Cannot mutate immutable namespace ('dependency-review', 'skips_under')`,
  which is a collection error rather than a test failure, so every gate reading `fixture()` errors at
  once. The three rows that already carry skips — `conventional-commits`, `pr-description`,
  `prek-advisory` — carry no `skips_under = []` line for the same reason.
  Run `uv run pytest tests/test_workflow_properties.py::test_every_event_conditional_job_appears_in_the_skip_table_with_a_reason`
  and confirm it passes now that T007's `if:` and this entry agree.

- [X] T009 [US3] In `tests/test_workflow_properties.py`, add a gate (FR-011, FR-024) that finds the
  diagnostic step added in T007 **by its `id: graph-off`**, asserts it exists exactly once, and then
  asserts three things about the step as read from the file: that its `if:` names both `failure()` and
  `steps.review.outputs.dependency-changes`, so the diagnostic cannot fire on a run that read the
  difference and found a real advisory; and that its `run:` text names the dependency-graph setting and
  says this capability cannot enable it. Do not locate the step by retyping the condition — a reworded
  condition would then match nothing and the gate would report green over a missing diagnostic, which
  is the failure mode research.md rejected for message-matching. Include a pre-flight test that feeds
  the finder a synthetic step list with no `graph-off` id and asserts it reports the absence rather
  than passing. The failure message must name the step it looked for, what it read in it, and what a
  maintainer should add.

- [X] T010 [P] [US3] Add a `### dependency-review` section to `README.md`, positioned with the other
  capability sections (after `prek-advisory`, before `## Versioning`), carrying: a copyable call site
  (`uses: turboBasic/github-actions-new/.github/workflows/dependency-review.yml@v0.1`, granting
  `contents: read` and passing nothing); the composed context, `<your job id> / dependency-review`; that
  it may be required only under `pull_request`, and that requiring it under any other event gives a
  check that reports success without reading anything (FR-012); what reddens the check — an advisory at
  or above the floor — against what only appears in the run's output — a sub-floor finding, an OpenSSF
  Scorecard warning, an unlicensed dependency — and that with no policy configured a licence is
  reported and never refused, so refusing a named licence is a second input (FR-013); and that
  the calling repository's own dependency graph has to be switched on, which this capability cannot do
  for it. Delete the opening line's dependency on a capability count — replace "Five reusable GitHub
  Actions workflows" with prose that names no count (FR-016). No table in the new section may have a
  column headed anything matching `default` (case-insensitive) — `test_no_readme_table_names_a_default`
  already asserts this over the whole file.

**Checkpoint**: `mise run ci` is green with the skip registered and the diagnostic in place. A run
against a repository with its dependency graph off now fails naming the setting and this capability's
limit. The README is the one place a consumer learns the one event and the two-list distinction.

---

## Phase 6: User Story 4 - Called here, required nowhere (Priority: P3)

**Goal**: This repository calls the capability on its own pull requests at the commit under review, the
composed context reports, and the committed ruleset does not require it.

**Independent Test**: Open any pull request in this repository and confirm `guard / dependency-review`
appears in the check list and reports (Scenario 4.1); read `.github/rulesets/protect-default-branch.json`
and confirm that context is absent from `required_status_checks` (Scenario 4.2).

- [X] T011 [US4] Create `.github/workflows/dependency-guard.yml`: `name: 🌜 dependency-guard`;
  `on: pull_request:`; its own `concurrency:` group (`${{ github.workflow }}-${{ github.ref }}`,
  `cancel-in-progress: true`, matching `advisory.yml`'s and `ci.yml`'s shape); workflow-level
  `permissions: {}`; one job, `guard`, with job-level `permissions: { contents: read }` and the reason
  on the same line, and `uses: $/.github/workflows/dependency-review.yml` — no `@ref`, no `with:`
  (the default floor is fine for this repository's own consumer use). The composed context is
  `guard / dependency-review`; the job id `guard` shares no word with `dependency-review` (FR-019).

- [X] T012 [P] [US4] In `pyproject.toml`, add `".github/workflows/dependency-guard.yml"` to
  `[tool.turbobasic-release].exclude`, alongside the seven callers already listed. Do not touch
  `include` — the capability itself stays inside it.

- [X] T012a [US4] In `tests/test_workflow_properties.py`, add a gate holding T012, because nothing
  does today: read `[tool.turbobasic-release]` from `pyproject.toml` and assert that the set of
  `exclude` entries under `.github/workflows/` equals exactly the set of workflows that are **not**
  capabilities (`is_capability` is false — the `🌜` half of the tree). Set equality in both
  directions: a new caller missing from `exclude` fails, and an entry naming a workflow that has since
  become a capability fails too. The two sets are equal today at seven each, so the gate arrives green
  and T012 turns it green again. The message must name which workflows are on which side, and say that a
  caller left out of `exclude` makes a later edit to this repository's own call site count towards a
  break. This
  is the one fact this feature adds that only the release path reads, at release time — the failure
  mode is silence, which is what earns it a gate rather than a note.

- [X] T013 [US4] In `tests/test_ruleset_contexts.py`, extend
  `test_composed_contexts_finds_the_contexts_the_tree_actually_reports` with
  `assert "guard / dependency-review" in contexts` — and correct that test's own comment, which reads
  "These **four** are confirmed against this repository's own reported check-run names": a count in a
  comment over a list of assertions is the same drift T010 deletes from the README, so drop the number
  rather than raise it. Extend
  `test_a_context_the_tree_composes_but_does_not_require_causes_no_failure` with the same context
  joining `"advisory / prek-advisory"` in the composed-but-not-required assertion. Do not edit
  `.github/rulesets/protect-default-branch.json` — FR-020 requires it stay unchanged, and
  `test_every_required_context_is_composed_by_the_tree` plus the two extended assertions are what prove
  the absence is deliberate rather than accidental.

**Checkpoint**: This repository is a real consumer of its own capability. `guard / dependency-review`
reports on every pull request here and is absent from the required set.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T014 [P] Run `mise run ci` end to end (`mise run lint`, `mise run typecheck`, `mise run test`)
  with no network access and confirm it passes (SC-001). `mise run lint` must be clean on both new
  workflow files under actionlint, zizmor and the `check-workflow-timeouts` schema hook.

- [X] T015 Work the "Prove each new gate can fail" table in [quickstart.md](quickstart.md) by hand: plant
  each listed violation one at a time, confirm the named gate reddens with a message that names what to
  change, then revert. This is FR-022 exercised on the real files, over and above the pre-flights each
  gate carries in the suite.

- [X] T016 Work the "Online" section of [quickstart.md](quickstart.md) against a real repository: the
  failing case (SC-003), the passing cases, the floor at `fail-on-severity: high` (Scenario 1.4), the
  adoption cost with nothing granted (SC-002), the dependency-graph-off case (SC-007), and this
  repository as its own consumer (SC-008). Requires GitHub network access and is not part of
  `mise run ci`.

---

## Dependencies & Execution Order

### What lands in one pull request

Phases 3, 4 and 5 are **one change**, not three. plan.md's first landing step is the capability, its
fixture row *and* its README section together, and
[contracts/published-surface-delta.md](contracts/published-surface-delta.md) says the same from the
other side: a capability with no row fails the correspondence gate, a row with no capability fails it
too, and FR-014 requires the record to gain its skip entry in the same change as the skip. A merge
after Phase 4 would publish a callable workflow with no consumer-facing reference and a fixture whose
`skips_under` does not yet describe the job — truthful only because T007 has not landed either.

Phase 6 may land in that change or a later one: the caller and the release-surface exclusion are this
repository's own call site and promise nothing to anybody. Phase 7 runs before either merges.

The phase boundaries below are checkpoints on the branch — points where `mise run ci` is green and the
work so far is coherent — not merge points.

### Phase Dependencies

- **Setup, Foundational**: none — both are empty.
- **User Story 1 (Phase 3)**: no dependency. Can start immediately.
- **User Story 2 (Phase 4)**: depends on T001 (the file and its steps must exist for T003/T005/T006 to
  read). Independent of Phase 5 and Phase 6.
- **User Story 3 (Phase 5)**: depends on T001 and T002 (edits the same job and the same fixture row).
  Independent of Phase 4 and Phase 6.
- **User Story 4 (Phase 6)**: depends on T001 (the capability must exist for the caller to call and for
  the context to compose). Independent of Phase 4 and Phase 5.
- **Polish (Phase 7)**: depends on Phases 3–6 all being complete.

### Within Each User Story

- T001 before T002, T003 and T003a (US1). T003 before T003a — the pre-flight reads the helper the gate
  is factored into.
- T004 before T006 (US2) — the gate reads the reader. T005 has no dependency beyond T001.
- T007 before T008 and T009 (US3) — the fixture entry and the gate both read the `if:` and the step
  T007 adds.
- T011 before T013 (US4) — the gate names a context that must already be composed.
- T011 before T012, and both before T012a (US4). T012a's sets are equal today, so it would arrive green
  on its own; once T011 adds an eighth caller it stays green only with T012 done, which is the whole
  point of it.

### Parallel Opportunities

- T003 and T003a (US1's gate and its pre-flight) can run alongside T004–T006 (US2) and T011–T013 (US4)
  once T001 exists — different
  files, no ordering constraint between the stories themselves.
- T010 (README) and T012 (`pyproject.toml`) touch files no other task in this feature touches, so they
  are parallel-safe against everything except their own story's file-ordering above. T012a is not: it
  reads both `pyproject.toml` and the workflow tree, so it goes last within US4.
- T014 is parallel-safe with nothing — it is the checkpoint that everything else must precede.

---

## Parallel Example: after T001 lands

```bash
# US1's own gate, and the start of US2 and US4, all read the same file and no other:
Task: "Add the uses: gate and its pre-flight in tests/test_workflow_properties.py (T003, T003a)"
Task: "Add declared_input_specs in tests/capabilities.py (T004)"
Task: "Create .github/workflows/dependency-guard.yml (T011)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001–T003a. Point a test repository's `pull_request` workflow at `dependency-review.yml` directly
   (no ref needed within this repository's own checks) and confirm it reddens on a known advisory.
2. **STOP and VALIDATE** against quickstart.md's Online section before continuing. This is a
   checkpoint on the branch, not a merge — see *What lands in one pull request* above.

### Incremental Delivery

1. Phase 3 (US1) → the capability judges.
2. Phase 4 (US2) → the permission and input surface are gate-defended, not just true today.
3. Phase 5 (US3) → the skip is honest and registered; the dependency-graph-off failure names itself;
   the README tells a consumer the truth.
4. Phase 6 (US4) → this repository becomes a real consumer, deliberately not requiring the context.
5. Phase 7 → full offline proof, then the online proof that cannot run in `mise run ci`.

### Suggested MVP Scope

User Story 1 (T001–T003a) is the entire capability's value; Story 2 is a property of the file Story 1
adds rather than a second change, and Story 3 is what makes the capability honest about what it does
not judge and adoptable at all. So Phases 3–5 are one unit and one pull request, and Phase 6 is the
only part that may follow.
