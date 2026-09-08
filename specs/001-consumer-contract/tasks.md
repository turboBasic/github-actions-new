---

description: "Task list for the consumer contract"
---

# Tasks: The Consumer Contract

**Input**: Design documents from `/specs/001-consumer-contract/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/published-surface.md](./contracts/published-surface.md)

**Tests**: Included, and not optional here. The plan's Constitution Check makes tests the gates that
carry principles IV, V, VI and VII — three of which had no gate at all before this feature. A capability
shipped without its gate is the feature half done.

**Organization**: By user story, in the order the plan phases them: the two P1 capabilities first, then
the irreversible one, then the two reshaped by rulings. The gates come before the capabilities they
gate, or they codify whatever was built.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: Which user story the task belongs to
- Paths are repository-relative, per the plan's Project Structure

**T077–T079 are numbered out of sequence on purpose.** They were added after a cross-artifact analysis
found three gaps, and renumbering would have invalidated every task ID already read and reasoned about.
Each carries the phase it belongs to and the task it executes before; run them in position, not in
numeric order.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Make the tree able to hold an `actions/` tree and a capability, and clear the one debt the
earlier phases left.

- [X] T001 Write the four conventions the constitution pass rejected as invariants into `docs/ai-instructions.md`: a failure names what to change; tool prerequisites are pre-flighted; consumer tool versions stay the consumer's; an input named for a stage governs that stage. Each is a convention because a reviewer catches it and a revert restores the world
- [X] T002 Add `actions/` to the linted trees: extend the `zizmor` line in `[tasks.lint]` in `mise.toml` to cover `actions/` as well as `.github/workflows`, since `actionlint` does not look outside `.github/workflows`
- [X] T003 [P] Add `actions` to `[tool.pyright].include` and `[tool.ruff].src` in `pyproject.toml`, so the decision unit is type-checked strictly and linted like the tests
- [X] T004 [P] Confirm `.editorconfig` and `.gitattributes` already cover `.py` and `.yml` under `actions/`, and extend them in this change if not

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The gates that carry the new principles, plus the resolution of principle I's risk. Every
capability after this is born checked.

**⚠️ CRITICAL**: No capability work begins until this phase is complete.

- [X] T005 Create `tests/published_surface.toml` holding the committed surface fixture, with the record shape from `data-model.md` and no capability rows yet — one table per capability, each with `kind`, `published`, `check_name`, `inputs`, `permissions`, `tool_prerequisites`, `skips_under`
- [X] T006 Create `tests/test_published_surface.py` asserting the tree matches the fixture: every `workflow_call` workflow and every `actions/*/action.yml` appears, its input name set matches, its permission demands match, and its composed check name matches. A missing or extra capability fails. This is principle IV's gate
- [X] T007 In `tests/test_published_surface.py`, assert the invariant from `data-model.md`: `check_name` is null for every action and non-null for every published workflow — a published workflow with no check name is a gate a consumer cannot require
- [X] T008 [P] Create `tests/test_no_interpolation.py` asserting no `run:` block in any workflow or action interpolates `${{ github.event.* }}`, `${{ inputs.* }}`, or any commit-derived value. Values reach code through `env:`. This is principle VI's gate
- [X] T009 [P] Create `tests/test_action_pins.py` asserting every third-party `uses:` is pinned to a full SHA, and that the one permitted self-reference by owner and moving ref is named in an exemption table with a reason, and is the only one
- [X] T010 [P] Create `tests/test_workflow_properties.py` with the event-skip table from `contracts/published-surface.md`: every event-conditional job-level `if:` appears in it with a non-empty reason, asserted. This is principle VII's gate
- [X] T011 In `tests/test_workflow_properties.py`, assert every job in every workflow declares `timeout-minutes`, that no capability declares a permission the fixture does not list, and that **every permission carries a reason beside it** — FR-004 makes the `permissions:` block its own documentation (R4), so an undocumented demand is the fact having no owner. Without this the gate is asymmetric: T010 already demands a reason for every event skip.
  **Two of the three clauses were dropped as second owners** (principle I): `check-jsonschema
  --builtin-schema custom.github-workflows-require-timeout` already asserts every job declares
  `timeout-minutes`, and it is named in both `[tasks.lint]` and `.pre-commit-config.yaml` — which is
  also where `quickstart.md` assigns that rule. And "no capability declares a permission the fixture
  does not list" is one direction of the equality T006 already asserts over the merged demand. Only
  the permission-reason clause was un-owned, so only it was written
- [X] T012 Add a principle I gate to `tests/test_workflow_properties.py`: no table in `README.md` has a header cell naming a default, so an input's default cannot acquire a second owner outside the capability YAML
- [X] T013 Restructure `README.md` to the shape R4 settled: one copyable call site per capability plus the prose saying what it is for and when not to reach for it, and no input tables. Leave a placeholder section per capability for the phases below to fill. **Rewrite the opening in this same change** — it currently says nothing ships yet and that this is not the repository consumers pin, and both become false the moment Phase 3 lands. Correcting it later would leave the tree carrying a false claim for four phases, and stale framing is a defect rather than a follow-up
- [X] T014 Add the new test modules to the tree's expectations — confirm `tests/test_instruction_layers.py` still passes with no new markdown outside an assigned layer, and add any new `docs/` file to its `LAYERS` map in the same change

**Checkpoint**: `mise run ci` green with four new gates that can fail and nothing yet to gate.

Two shapes settled here that the phases below inherit:

- **`skips_under` lives in the fixture, and `test_workflow_properties.py` reads it from there.** T010,
  T030 and T068 read as putting the event-skip table in the test module while T005 makes it a fixture
  field; holding both would be two owners of one table. Each entry is `{ jobs, event, reason }` — the
  `jobs` list extends `data-model.md`'s `(event, reason)` so the gate can be per-job as T010 requires,
  while one reason still covers several jobs skipping for it.
- **`check_name` is a list, and the fixture holds input names only.** `conventional-commits` composes
  two contexts, so a single string cannot hold what T024 asks for; and a default restated in the
  fixture would be the exact second owner R4 removed.

`tests/capabilities.py` is the one owner of how a workflow is read — the trigger key, the permission
merge, the capability test. Four gates over the same YAML would otherwise each carry their own copy,
including their own answer to `on:` being YAML 1.1's `true`.

---

## Phase 3: User Story 1 — A Python repository gets one CI check (P1)

**Goal**: A Python repository runs its own lint, typecheck and test tasks as one check by calling one
workflow with no inputs, granting only read access to contents.

**Independent test**: This repository's own CI calls it with no inputs and reports one green
`ci / python-ci`; breaking a task reddens exactly that check.

- [X] T015 [US1] Add the `python-ci` row to `tests/published_surface.toml`: check name `python-ci`, the nine inputs from `contracts/published-surface.md`, `contents: read`, and its tool prerequisites. Watch it fail — the capability does not exist yet
- [X] T016 [US1] Create `.github/workflows/python-ci.yml` with the `workflow_call` trigger and the nine declared inputs, each carrying its own description and default, and `contents: read`. Job named `python-ci` with `timeout-minutes` from the input
- [X] T017 [US1] Add the tool pre-flight step to `.github/workflows/python-ci.yml`: before invoking the package manager or the hook runner, check each is present and fail naming the tool, this capability, and where the consumer declares it (FR-009, OQ-005)
- [X] T018 [US1] Implement the lockfile check and the three stage steps in `.github/workflows/python-ci.yml`, task names reaching the runner through `env:` and never interpolated into a `run:` line
- [X] T019 [US1] Implement the changed-files lint path in `.github/workflows/python-ci.yml`, gated on the lint stage switch as well as on `lint-changed-only`, so switching lint off stops every kind of linting (FR-012a, OQ-008)
- [X] T020 [US1] Cache the hook environments unconditionally in `.github/workflows/python-ci.yml`, with no input governing it and no dependency on the changed-files option (FR-014a, OQ-007)
- [X] T021 [US1] Assert the capability's contract in `tests/test_workflow_properties.py`: no `cache-prek` input exists, the lockfile step precedes every stage, and the changed-files step carries the lint switch in its condition
- [X] T022 [US1] Rewrite `.github/workflows/ci.yml` to call `$/.github/workflows/python-ci.yml` for this repository's own gates, so the capability is exercised at the commit under review (R1)
- [X] T023 [US1] Fill the `python-ci` section of `README.md` with a copyable call site, the note that concurrency belongs to the caller, and the statement that the capability's scope is a Python project (FR-010a, OQ-004) — no input table. Include the two warnings the contract requires and prose is the only place to put: that the changed-files lint lets a pull request pass while the tree is broken, naming the capability that compensates (FR-014); and that a repository reserving its slow checks for a later hook stage must name that stage, or those checks silently stop running on pull requests (FR-015)

**Checkpoint**: US1 delivered and independently usable. `mise run ci` green; a pull request reports
`ci / python-ci`.

---

## Phase 4: User Story 2 — One commit grammar, title and commits (P1)

**Goal**: The pull request title and every commit message in the range are held to one Conventional
Commits grammar, by one workflow, with two check names a consumer can require.

**Independent test**: A pull request with a bad title fails `pr-title` while `commit-messages` passes,
and vice versa — the two checks are separable and neither can pass vacuously.

- [X] T024 [US2] Add the `conventional-commits` row to `tests/published_surface.toml`: two check names `pr-title` and `commit-messages`, four inputs, `contents: read` and `pull-requests: read`, no tool prerequisites
- [X] T025 [US2] Create `.github/workflows/conventional-commits.yml` with the `workflow_call` trigger, the four inputs, and two jobs named `pr-title` and `commit-messages`. Declare `pull-requests: read` at workflow and job level, since the title check reads the title from the API
- [X] T026 [US2] Implement the title check job in `.github/workflows/conventional-commits.yml`, judging against the `types` input and nothing else
- [X] T027 [US2] Implement the type-list validation in `.github/workflows/conventional-commits.yml`: a list holding anything but bare words fails the run naming the list, rather than being silently accepted (FR-021)
- [X] T028 [US2] Implement the commit-range check in `.github/workflows/conventional-commits.yml` using the same tool the local commit hook uses, judging against the compiled `types` list rather than the consumer's own commit-tool configuration, so the two jobs cannot disagree (FR-018)
- [X] T029 [US2] Provision the capability's own tooling in `.github/workflows/conventional-commits.yml` so a repository with no task-runner configuration can still use it (FR-022), and record its empty tool-prerequisite list in the fixture
- [X] T030 [US2] Register both jobs' event skips in `tests/test_workflow_properties.py`'s table with the reason from `contracts/published-surface.md`, and assert neither can be reached from `pull_request_target`
- [X] T031 [US2] Create `.github/workflows/commit-messages.yml` calling `$/.github/workflows/conventional-commits.yml`, subscribing to the title-edit activity type, with a job id chosen so the composed contexts read `commits / pr-title` and `commits / commit-messages`
- [X] T032 [US2] Fill the `conventional-commits` section of `README.md`: the call site, the instruction to spell out the activity types including edits, and why the event must not be `pull_request_target`. Add the instruction FR-023 requires: switching either check off means removing its context from the required checks **in the same change**, or the ruleset keeps naming a gate that no longer reports and blocks every pull request

**Checkpoint**: Both P1 capabilities delivered. Two consumers could adopt the repository at this point.

---

## Phase 5: US4 releasing (P2) and US6 the pin promise (P1)

**Goal**: Releasing is an act of approval; every refusal runs before any ref exists; the ref a consumer
pins never crosses a break.

**Independent test**: A dispatch with the dry-run switch on runs every refusal, renders the real notes,
and stops — leaving no tag and no release. Every refusal is separately unit-testable offline.

**⚠️ This is the phase where principle V is held or lost.** A version tag cannot be withdrawn. Nothing
here ships without a dry run first.

### The decision unit — tests before code

- [X] T033 [P] [US4] Create `tests/test_release_decisions.py` covering version parsing: exactly `N.N.N`, no pre-release, no build metadata, no leading `v`, and absence returned rather than raised
- [X] T034 [P] [US4] Add compatibility-line tests to `tests/test_release_decisions.py`: `(major,)` from `1.0.0` up, `(major, minor)` below it, and a test asserting this is the **only** place the boundary is decided (principle I, and what principle V turns on)
- [X] T035 [P] [US4] Add moving-ref tests to `tests/test_release_decisions.py`: `v0.1` below `1.0.0`, `v1` above, never `v0`, and **total — never empty for any version the refusals admit**. This replaces the dead guard rather than carrying it forward (R3, OQ-011)
- [X] T036 [P] [US4] Add increment tests to `tests/test_release_decisions.py` from the table in `data-model.md`, including the two the naive reading gets wrong: below `1.0.0` a break advances the minor, and a feature advances only the patch
- [X] T037 [P] [US4] Add refusal-ladder tests to `tests/test_release_decisions.py`: not on the default branch, a version that does not parse, not ahead of the highest release across every line, empty notes, and a break staying on a line that already has a release
- [X] T038 [P] [US4] Add three-way verdict tests to `tests/test_release_decisions.py`: a routine push declines with a notice, a dry run proceeds reporting what it would refuse, anything else refuses
- [X] T039 [P] [US4] Add surface-declaration tests to `tests/test_release_decisions.py`: the three distinguishable states, an unknown key refused rather than ignored, a non-list value refused rather than coerced, and a path that is empty or holds whitespace or begins with `-` refused
- [X] T040 [US4] Create `actions/release-decisions/decisions.py`: standard-library only, no network, pure functions for every value in `data-model.md` separated from the environment-in / output-out edge. Make T033–T039 pass
- [X] T041 [US4] Create `actions/release-decisions/action.yml` declaring the decision names and the per-question inputs, every value reaching the module through `env:`. Mark it internal in `tests/published_surface.toml` — `published = false`, no check name, inputs not compared (OQ-003)

### The release workflows

- [X] T042 [US4] Add the `release` row to `tests/published_surface.toml`: check name `tag-and-publish`, one input `dry-run`, `contents: write`
- [X] T043 [US4] Create `.github/workflows/release.yml` with a `workflow_call` trigger **and nothing else**, so a caller's dependency edge is the only route to the tagging step (FR-033). Serialise it so two releases cannot race the moving ref
- [X] T044 [US4] Implement the default-branch refusal in `.github/workflows/release.yml` reading the repository's actual default branch from the run, never comparing against a literal name, with no input for it (FR-037a, OQ-006)
- [X] T077 [US4] **Executes before T045.** Pin the notes renderer in `mise.toml`'s `[tools]` table at an exact version. This repository is its own consumer of the release capability, so the renderer must be present here for the same reason a consumer's configuration must pin it — and today `[tools]` names no renderer at all, so nothing in Phase 5 can render anything
- [X] T078 [US4] **Executes before T045.** Create this repository's notes configuration, mapping commit types to sections and matching version tags. Notes come from commit types, never from a label on a pull request (FR-042). Without it the empty-notes refusal cannot be exercised, which leaves one of principle V's gates untested rather than merely undocumented. The superseded repository's own notes configuration **may** be consulted for the type-to-section mapping: it decides rendered output, so it is behaviour rather than a conclusion. That permission extends to it alone — that repository's tests and its prose layers stay excluded, because this specification was derived from its behaviour precisely so that its conclusions could not arrive here as premises
- [X] T045 [US4] Wire the refusal ladder in `.github/workflows/release.yml` in the order `data-model.md` fixes, rendering the notes and every refusal **before any ref-creating step**
- [X] T046 [US4] Add two assertions to `tests/test_workflow_properties.py`. First: no ref-creating step in `.github/workflows/release.yml` precedes any refusal step — principle V's structural gate. Second: **no step in that workflow writes a version**, since the version released is what a merged change decided and the capability only tags it (FR-034). The proposal path writes versions; the release path must be gated against ever doing so
- [X] T047 [US4] Implement tag-and-publish in `.github/workflows/release.yml`: an annotated immutable version tag, the release published from the rendered notes, and the moving ref force-moved **last**, after the release exists
- [X] T048 [US4] Add the notes-renderer tool pre-flight to `.github/workflows/release.yml`, failing with the tool named and where the consumer declares it (FR-009)
- [X] T049 [US4] Create `.github/workflows/release-on-merge.yml` for this repository: verify via `$/.github/workflows/python-ci.yml`, then call `$/.github/workflows/release.yml` behind a dependency edge, with a manual dry-run entry point
- [X] T050 [US4] Create `.github/workflows/release-proposal.yml`: after a merge, open or refresh one pull request carrying the next version and the exact notes it would publish. A human's version on that branch outranks the computed one and survives every refresh; a range that has become empty closes the proposal (FR-044)
- [X] T051 [US4] Use a narrowed App installation token for every write in `.github/workflows/release-proposal.yml`, never the run's own token, and add a `tests/` assertion that no `secrets.*` reference reaches a `run:` body, a file or an artifact (principle II)
- [X] T052 [US6] Add `[tool.turbobasic-release]` to this repository's `pyproject.toml` declaring its own consumer surface, so its release is judged against its own layout rather than an inherited default (FR-038)
- [X] T053 [US6] Fill the `release` and versioning sections of `README.md`: the call site, the surface declaration a consumer writes in its own manifest, the moving-ref table for `0.x` and above, and the statement that this repository starts its own line and inherits no ref (FR-009a, OQ-009)
- [X] T054 [US6] Document the one SHA-pinning exception in `README.md` and assert in `tests/test_action_pins.py` that it is the only one: the release workflow names the internal decision unit by owner and moving ref, because a reusable workflow can reach neither its own tree nor its own ref (R2)

**Checkpoint**: US4 and US6 delivered. Dry-run the release before trusting it with a tag.

---

## Phase 6: User Story 3 — A pull request body is written from its commits (P2)

**Goal**: A pull request opens with a body rendered from its commits into the repository's own template,
and the consumer writes one `uses:` and one permission — nothing else.

**Independent test**: A pull request carrying one commit with a body and one without opens with both
subjects listed and the one body indented under its subject, with no checkout written by the caller.

- [ ] T055 [US3] Add the `pr-description` row to `tests/published_surface.toml`: check name `pr-description`, inputs `template-path` and `timeout-minutes` **only**, `contents: read` and `pull-requests: write`
- [ ] T056 [US3] Create `.github/workflows/pr-description.yml` as a callable workflow owning its own full-history checkout, reading the pull request, the repository and the commit range from the run rather than from inputs (FR-029a, OQ-010)
- [ ] T057 [US3] Assert in `tests/test_workflow_properties.py` that the capability declares no token, pull-request-number, repository or SHA input — the shallow-checkout failure mode is removed rather than documented, and a reintroduced identifying input is a regression
- [ ] T058 [US3] Implement the rendering in `.github/workflows/pr-description.yml`: subjects as a summary list, full messages as a change list, multi-paragraph bodies keeping their paragraph breaks inside their list item, and an empty range rendering invisible prompts rather than blank sections
- [ ] T059 [US3] Provision the rendering tooling inside the capability so the consumer needs no language or package-manager setup step, and record its empty tool-prerequisite list in the fixture (FR-029)
- [ ] T060 [US3] Create `.github/workflows/describe-pr.yml` calling `$/.github/workflows/pr-description.yml` on pull-request opening only, since rewriting the body on every push discards whatever a human typed
- [ ] T061 [US3] Fill the `pr-description` section of `README.md`: the call site, the two template substitution points, and why the trigger is `opened` alone

**Checkpoint**: US3 delivered. Both consumers of the old action form now write one `uses:`.

---

## Phase 7: User Story 5 — A whole-tree lint reports without blocking (P3)

**Goal**: A non-blocking whole-tree lint reported as one pull request comment, edited in place rather
than duplicated on later pushes.

**Independent test**: A lint finding outside the changed set produces one comment and a green check; a
second push edits that comment rather than adding another.

- [X] T062 [US5] Settle finding F1 from `research.md` before writing anything here: cut the composite-action form of this capability, or keep it. Cutting it removes the moving self-reference the callable workflow would otherwise need. This decides whether `actions/` holds one directory or two. **Settled early, before Phase 3: cut.** The ruling and its reasoning are in `spec.md` (F1, FR-049a, and FR-001 which no longer reads as requiring both kinds). `actions/` holds one directory. Nothing to build here — this capability is a callable workflow and there is no second form to write
- [ ] T063 [US5] Add the `prek-advisory` row to `tests/published_surface.toml`: check name `prek-advisory`, inputs `hook-stage` and `timeout-minutes` — no `cache-prek`, no `mise-version` — `contents: read` and `pull-requests: write`
- [ ] T064 [US5] Create `.github/workflows/prek-advisory.yml` as a separate capability precisely because of its write demand, so a consumer can take the CI capability without granting write access (FR-003)
- [ ] T079 [US5] **Executes before T065.** Add the tool pre-flight to `.github/workflows/prek-advisory.yml`, mirroring T017: `contracts/published-surface.md` lists this capability as needing both the package manager and the hook runner from the consumer's configuration, so both are checked before use and a missing one fails naming the tool, this capability, and where to declare it (FR-009). Omitting it here would leave the only capability that invokes consumer tools without a pre-flight
- [ ] T065 [US5] Implement the whole-tree lint in `.github/workflows/prek-advisory.yml` with the finding non-blocking but the capability's own setup — including the lockfile check — still failing the check, and say so in the README: a green check means the lint ran, not that it passed (FR-047)
- [ ] T066 [US5] Implement the idempotent comment in `.github/workflows/prek-advisory.yml`: one marked comment, found and edited if present, created if not, plus a job summary and a warning annotation
- [ ] T067 [US5] Cache the hook environments unconditionally, with no input governing it, matching the CI capability (FR-014a)
- [ ] T068 [US5] Register the event skip in `tests/test_workflow_properties.py`'s table, with the reason recording that this capability is advertised as advisory and so is exempt from principle VII by name
- [ ] T069 [US5] Create `.github/workflows/advisory.yml` calling `$/.github/workflows/prek-advisory.yml`, and turn on `lint-changed-only` in this repository's own `ci.yml` call so the compensating relationship between the two is exercised rather than described
- [ ] T070 [US5] Fill the `prek-advisory` section of `README.md`: the call site, the required write permission and why omitting it fails the run at startup with no job and no log, and the instruction to pass the same hook stage as to the CI capability

**Checkpoint**: All five published capabilities delivered.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T071 Settle finding F2 from `research.md`: keep or drop `mise-version`, which two capabilities declare and no consumer sets. Dropping it is cheaper now than after a consumer pins it. If dropped, remove it from both capabilities and from `tests/published_surface.toml` in one change. **Settled early, before Phase 3: drop.** The ruling and its reasoning are in `spec.md` (F2, FR-016a). Nothing to remove from `tests/published_surface.toml` — settling it ahead of Phase 3 means the input is never written into either capability, which is the whole point: doing this in Phase 8 as scheduled would have meant shipping it and then deleting it, and a deleted input is a new compatibility line
- [ ] T072 [P] Sweep `README.md` for framing that the finished feature has made false, now that every section is filled. The opening was corrected in T013, when it first became wrong; this is the closing read of the whole document against what the tree actually ships
- [ ] T073 [P] Add a `docs/technical-debt.md` row for the repository-rename debt if it still holds: every internal name is already the destination one while URLs carry the staging suffix, and the condition that clears it is the rename
- [ ] T074 Write a decision record in `docs/decisions/` only if a ruling here clears the ADR bar — the likely candidate is R2, the one permitted self-reference and why it is structural. If it clears, add its `scope:` value to `docs/ai-instructions.md` in the same change if `instructions` and `tooling` do not cover it, and delete the `.gitkeep`
- [ ] T075 Verify each capability against `quickstart.md` section 3 on a real pull request, including the one thing no gate can prove: that removing a permission demand from a call site fails the run at startup with no job and no log
- [ ] T076 Confirm `mise run ci` is green and needed no network at any point

---

## Dependencies

```text
Phase 1 (Setup) ─────────► Phase 2 (Gates) ─────────► Phase 3 (US1) ─┐
                                                                      ├─► Phase 5 (US4+US6)
                                                      Phase 4 (US2) ─┘        │
                                                                               ▼
                                                              Phase 6 (US3) ─┬─► Phase 8 (Polish)
                                                              Phase 7 (US5) ─┘
```

- **Phase 2 blocks everything.** The gates exist before the capabilities, or the fixture codifies
  whatever was built and principle IV's gate asserts the present rather than the promise.
- **US1 and US2 are independent of each other** and either could ship first. US1 is listed first only
  because it proves the `$/` dogfooding mechanism on the simplest surface.
- **Phase 5 depends on US1** — its release path verifies through the CI capability behind a dependency
  edge, which is the only verdict structurally true on the commit being tagged.
- **US3 and US5 are independent of each other and of Phase 5**, and could run in parallel.
- **T062 and T071 are settled** — both ticked ahead of Phase 3 rather than in the phases that hold
  them, which is what the closing note below argued for. Phase 7 knows its shape and Phase 3 knows its
  input list before either is written.

## Parallel opportunities

| Where | Tasks | Why safe |
| --- | --- | --- |
| Phase 1 | T003, T004 | Different files: `pyproject.toml` vs `.editorconfig` / `.gitattributes` |
| Phase 2 | T008, T009, T010 | Three new test modules, no shared file |
| Phase 5 | T033–T039 | Seven test groups in one new module; independent if written as separate functions first |
| Phase 5 | T077, T078 | `mise.toml` vs the notes configuration; both must precede T045 |
| Phase 8 | T072, T073 | `README.md` vs `docs/technical-debt.md` |
| Whole phases | Phase 6 and Phase 7 | Disjoint capabilities, disjoint files, neither depends on the other |

## Implementation strategy

**MVP is Phase 1 + Phase 2 + Phase 3.** That is one capability, born checked, exercised by this
repository's own CI at the commit under review — and `python-app-baseline` could adopt it that day.

Then increment: US2 makes the repository adoptable by the two consumers that only ever wanted commit
grammar. US4 is what lets any of it be released at all, and is the phase to slow down in. US3 and US5
are the reshaped ones and benefit from the pattern the earlier phases settle.

Two decisions were scheduled into the work rather than guessed at now: T062 before Phase 7, T071 in
Phase 8. Both change published surface, and after Phase 5 exists that means both cost a compatibility
line — which is the argument for settling them early, not the argument for guessing.

**Both were then settled before Phase 3, and the scheduling above is what changed.** Waiting until
Phase 8 to drop `mise-version` would have meant writing it into two capabilities, releasing them, and
deleting it afterwards; and a deleted input is exactly the compatibility line the paragraph above warns
about. Neither answer needed anything the tree could only learn by building — which is what made
settling them early free rather than a guess.
