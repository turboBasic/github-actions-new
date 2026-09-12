---

description: "Task list for feature implementation"
---

# Tasks: Every rule held by a gate

**Input**: Design documents from `/specs/003-rules-held-by-gates/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are the deliverable. This feature adds no runtime behaviour — every task below either
writes a gate, writes the pairing that proves a gate can fail, or changes the tree so a gate can pass.
The template's optional-tests note does not apply.

**Organization**: grouped by user story, each story shippable on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — different files, no dependency on incomplete work
- **[Story]**: US1–US6, mapping to the user stories in `spec.md`
- Every task names its exact file path

## Conventions binding every task below

- **One green commit per task.** `mise run ci` passes at every task boundary; a task that cannot leave
  the suite green is two tasks.
- **Every new gate lands with its pairing in the same commit** (FR-018). A gate committed without one is
  the exact defect this feature exists to remove, so the pairing is not a follow-up task.
- **Every gate reads a workflow or an action through `tests/capabilities.py`** (FR-020) and parses that
  YAML nowhere else.
- **Every failure message names what was read, what it was compared against, and the edit to make**
  (FR-021). Verify by reading the message, not by seeing red.
- **No new dependency.** `pytest`, `pyyaml`, `commitizen`, `tomllib`, `hashlib`, `subprocess`.
- Full type hints on every signature, tests included; no docstrings; comments only where the WHY is
  non-obvious.

---

## Phase 1: Setup

**Purpose**: establish the baseline every later task is measured against.

- [X] T001 Record the baseline in `tmp/`: `mise run ci` green, and the current test count from
  `mise run test`, so every later task can assert it added gates without removing any

**Already applied during planning** (present in the working tree, uncommitted): `Tera` and
`postprocessors` added to `.cspell/project.txt`. No task needed; verify they are still there when the
first `cliff.toml` comment lands.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the two accessors more than one story needs. Nothing else is shared (research R15).

**⚠️ CRITICAL**: T002 blocks US4; T003 blocks US4 and US5.

- [X] T002 Add a job-name accessor to `tests/capabilities.py` returning every job's name with the id
  fallback, reusing the fallback rule `check_names()` already encodes rather than restating it
- [X] T003 Add a trigger-kind accessor to `tests/capabilities.py` answering whether `workflow_call` is a
  document's only trigger, built on the existing `triggers()` reader

**Checkpoint**: `mise run ci` green with two unused accessors. pyright strict covers both.

---

## Phase 3: US1 — Release notes cannot change shape (P1) 🎯 MVP

**Goal**: the shape of the one artefact this library publishes becomes unable to change silently, and
the two ways it currently renders wrongly are fixed.

**Independent Test**: make each edit in the `quickstart.md` notes table and confirm the named gate
fails; then render a range containing a ref pin and an unnumbered subject and read the output.

### Gates that pass on the current tree

Written first, and expected **green** immediately — the rules already hold and only lacked a gate. A red
result here means the gate reads the wrong thing.

- [X] T004 [US1] Create `tests/test_release_notes.py` with FR-001: every one of the twelve types the
  grammar admits resolves through `cliff.toml`'s `commit_parsers` to exactly one destination, a group or
  a skip. Read the type set via US2's accessor if T018 has landed, otherwise from the workflow default.
  Assert *exactly one*, so a pattern Python cannot read fails rather than passing (research R14)
- [X] T005 [US1] Add FR-003 to `tests/test_release_notes.py`: `tag_pattern` matches `v1.2.3` and does
  not match `v1`, `v1.2`, or a suffixed tag. Both a positive and a negative assertion, so `.*` and `^$`
  both fail

### Gates that fail until the tree is fixed

Written before their fix, and expected **red**. **A gate and the tree change that turns it green are
one commit**, not two — the one-green-commit-per-task convention above overrides the task boundary here,
so T006+T007 landed together and T008+T009+T010 landed together.

- [X] T006 [US1] Add FR-002 to `tests/test_release_notes.py`: the six groups are exactly
  `Added, Fixed, Performance, Changed, Reverted, Documentation` in that order, each carrying a unique
  `<!--N-->` prefix, and there is no seventh group — a breaking change is marked inline on its item, not
  given a section. Write the six titles and numbers out literally; deriving them from the parser order
  would hold nothing (research R1). Fails now — no group has a prefix
- [X] T007 [US1] Add the ordering prefixes to `cliff.toml` group names and the stripping postprocessor
  `{ pattern = '<!--[0-9]+-->', replace = "" }`, numbered in the declared order —
  `1 Added, 2 Fixed, 3 Performance, 4 Changed, 5 Reverted, 6 Documentation` (research R1). T006 goes
  green. **The rendered order changes**, from the alphabetical sequence Tera was producing to the one the
  configuration has always declared; that is the intent, not a side effect
- [X] T008 [US1] Add FR-004 and FR-005 to `tests/test_release_notes.py` as rendering assertions: plant a
  git repository in `tmp_path` with a numbered subject, an unnumbered subject, a subject carrying `@v5`,
  and a subject carrying an email address; run `git-cliff --config <repo cliff.toml> --unreleased` with
  `cwd` set to the planted repository. Guard on `shutil.which("git-cliff")` with a message naming
  `mise run test`. Never `mise exec --cd`, which renders this repository instead (research R4). Fails now
  on three of the four subjects
- [X] T009 [US1] Add the `@`-mention postprocessor to `cliff.toml`:
  `{ pattern = '(?m)(^|[\s(\[])@([A-Za-z0-9][A-Za-z0-9-]*)', replace = '${1}`@${2}`' }`. The leading
  anchor is what leaves an address alone, and T008's address subject is what holds it there
- [X] T010 [US1] Add the reference fallback to `cliff.toml`'s body template:
  `{% if commit.message is not matching("\(#[0-9]+\)") %} ({{ commit.id | truncate(length=7, end="") }}){% endif %}`.
  T008 goes fully green — an unnumbered item gains its short id and a numbered one gains nothing
- [X] T011 [US1] Update `cliff.toml`'s header comment to state what now holds it: the ordering numbers as
  the only statement of position, and that FR-004 and FR-005 are held by rendering because a rotted
  pattern leaves valid TOML. State the rule, not the incident

**Checkpoint**: releasing this repository can no longer mention a stranger, and every rendered item
traces to one commit. US1 is complete and shippable alone.

---

## Phase 4: User Story 6 — No gate can rot into passing (Priority: P1)

**Goal**: the six existing gates whose steady state is an empty result gain the pairing that makes
silent rot impossible (FR-019). Independent of every other story and of each other.

**Independent Test**: for each, replace the reader's pattern with one matching nothing and confirm the
pairing reddens while its gate stays green. That divergence is the whole point.

**⚠️ File contention**: T012–T015 all edit `tests/test_workflow_properties.py`, so they are sequential
with each other and with US5's T031. T016 and T017 are free.

- [X] T012 [US6] Pair the `PERMISSION` line regex in `tests/test_workflow_properties.py`: assert a
  permission line with a reason is not flagged and one without a reason is
- [X] T013 [US6] Pair the `WRITES_A_VERSION` marker tuple in `tests/test_workflow_properties.py`: assert
  a planted `run:` authoring a commit is matched by at least one marker
- [X] T014 [US6] Pair the `GOVERNS_A_CACHE` regex in `tests/test_workflow_properties.py`: `cache-key`
  matched, `hook-stage` not
- [X] T015 [US6] Close the vacuous pass in `test_both_grammar_jobs_pin_the_event_they_can_judge` in
  `tests/test_workflow_properties.py`: assert the workflow yields a non-empty job map before the loop, so
  an empty map fails rather than iterating over nothing
- [X] T016 [P] [US6] Pair `blanket_permissions()` in `tests/test_published_surface.py`: assert a document
  with `permissions: read-all` is returned by it
- [X] T017 [P] [US6] Pair the `URL_OWNER_REPO` regex in `tests/test_repo_urls.py`: a self URL matched, a
  foreign host not. Mirror `USES_SLUG`'s existing pairing, and keep this module's self-exclusion in mind —
  the counter-examples must not read as drift

**Landed as two commits rather than six**: the four pairings in one file, then the two in the others.
Each is four lines guarding one reader; splitting them further would have been ceremony, not atomicity.

**Checkpoint**: no gate in the suite can rot into reporting green unnoticed.

---

## Phase 5: User Story 2 — One grammar, judged by one binary (Priority: P2)

**Goal**: the allowed commit types are one fact and the tool that judges them is one version, so a
message the local hook accepts cannot fail in CI.

**Independent Test**: change `CZ_VERSION` away from the locked version and confirm the gate names both
locations; add a type to one declaration only and confirm the same.

- [X] T018 [US2] Create `tests/test_commit_grammar.py` with FR-007: read the shipped type set from
  `ConventionalCommitsCz(BaseConfig()).schema_pattern()`, extract its first alternation group, and assert
  it equals the `types` default declared in `.github/workflows/conventional-commits.yml` read through
  `tests/capabilities.py`. Never `ConventionalCommitsCz.schema_pattern(ConventionalCommitsCz)`, and never
  a literal list — that is the third copy the requirement removes (research R5)
- [X] T019 [US2] Add its pairing: assert the extracted set is non-empty and contains a known member, so
  an accessor returning nothing fails rather than comparing two empty sets
- [X] T020 [US2] Add FR-008 to `tests/test_commit_grammar.py`: assert `CZ_VERSION` in
  `.github/workflows/conventional-commits.yml` equals the commitizen version `uv.lock` resolves, read
  with `tomllib`. Compare against the lockfile, not the installed environment — an installed version is a
  property of the machine (research R6). The message names both values and both file paths
- [X] T021 [US2] Add its pairing: assert both readers return a non-empty version string, so a lockfile
  format change that stops the reader finding commitizen fails here rather than comparing two absences

**Checkpoint**: an unattended dependency bump that moves one spelling and not the other now fails CI.

---

## Phase 6: User Story 3 — A tooling convention is held (Priority: P2)

**Goal**: three conventions about this repository's own tooling stop being held by prose. Each task is
independent of the others.

**Independent Test**: set a tool entry to `latest`; bump the specification pin without re-syncing; alter
one byte of a vendored file. Each names the artefact and the edit.

- [X] T022 [P] [US3] Create `tests/test_tool_versions.py` with FR-009: every `mise.toml` `[tools]` entry
  names a concrete version, refusing `latest`, an empty value and a non-string. Assert the table is
  non-empty first, so an empty read fails
- [X] T023 [P] [US3] Add its pairing: assert the check flags a planted `latest` entry and passes a
  planted concrete one
- [X] T024 [P] [US3] Create `tests/test_speckit_vendoring.py` with FR-010, ported from the tree being
  consolidated (research R9): each `.specify/integrations/*.manifest.json` records the version
  `mise.toml` pins for `pipx:specify-cli`, and every file it records exists and matches its recorded
  SHA-256. The message names the re-sync task and must not suggest upgrading outside the pin
- [X] T025 [P] [US3] Add its pairing: assert each manifest's file map is non-empty, so a manifest
  recording nothing fails instead of vacuously matching
- [X] T026 [P] [US3] Create `tests/test_actionlint_ignore.py` with FR-011: plant both `$/` forms in
  `tmp_path` — a job-level reusable-workflow `uses:` and a step-level action `uses:` — run `actionlint`
  there with no configuration, and assert each still produces a message matching the corresponding
  ignore pattern committed in `.github/actionlint.yaml`. Guard on `shutil.which("actionlint")`. The
  message says to delete the `paths:` entry, the file, and TD-001 together (research R7)
- [X] T027 [P] [US3] Add its pairing: assert the probe produces a verdict at all and that the committed
  ignore patterns are the ones being matched against, read from `.github/actionlint.yaml` rather than
  restated — otherwise the gate holds the test's copy of the pattern and not the file's

**Checkpoint**: no tool version can float, a pin cannot outrun its re-sync, and the one silenced message
expires on the day its reason does.

---

## Phase 7: US4 — A name that carries weight outside (P3)

**Goal**: job names stay usable as required-check identifiers, and workflow names say from the sidebar
which entries can ever have a run history.

**Independent Test**: rename a job to `Python_CI`; drop a workflow's marker; add a second trigger to a
`workflow_call`-only workflow and confirm its expected marker changes without any list being edited.

**Depends on**: T002, T003.

- [X] T028 [US4] Create `tests/test_names.py` with FR-012: every job name in every workflow is
  lowercase-kebab-case, read through `check_names()` so the gate and the consumer contract cannot
  disagree about what a name is. Expected green — the rule already holds (research R11). Include the
  pairing: `Python_CI` and `pr title` are refused, `pr-title` accepted
- [X] T029 [US4] Add FR-013 to `tests/test_names.py`: every workflow's `name:` is its marker plus its
  filename stem, with the marker chosen by T003's accessor — `🧩` where `workflow_call` is the only
  trigger, `🌜` where the workflow has triggers of its own (research R10). Derive the expected name from
  the file so a workflow the reader misses has no name to compare, and assert the workflow count is
  non-empty. Fails now on all twelve
- [X] T030 [US4] Rename all twelve `.github/workflows/*.yml` `name:` values to carry their marker. T029
  goes green. Verify in the same commit that `mise run test` shows no change in
  `tests/test_ruleset_contexts.py` — every required context is composed from job names, so this breaks no
  consumer (research R10), and that gate is what says so rather than a reviewer

**Checkpoint**: a reader can tell an always-empty sidebar entry from a broken one, and no job can be
renamed into a shape a consumer has to copy oddly.

---

## Phase 8: User Story 5 — A timeout input only where it is earned (Priority: P3)

**Goal**: a timeout input exists only where the caller knows something the callee cannot, and the
partition is asserted rather than reviewed.

**Independent Test**: add the input back to `pr-description`; remove it from `python-ci`. Both fail — the
partition is bidirectional.

**⚠️ This is the only story with a release consequence.** It removes two published inputs, which starts a
new compatibility line (principle IV). Read `contracts/published-surface-delta.md` before starting. It
depends on nothing else in the feature and nothing depends on it, so it can be deferred or split into its
own pull request without touching any other story.

**Depends on**: T003. **Contends with**: T012–T015 for `tests/test_workflow_properties.py`.

- [ ] T031 [US5] Add FR-014 and FR-015 to `tests/test_workflow_properties.py`: the set of capabilities
  declaring a timeout input equals `{python-ci, prek-advisory}` exactly. Set equality, not a subset, is
  what makes it fail in both directions in one assertion. Record each member's justification beside it —
  the reason a knob exists is not derivable from the fact that it does. Fails now on two capabilities
- [ ] T032 [US5] Remove the `timeout-minutes` input from `.github/workflows/conventional-commits.yml`
  and give both its jobs a literal `timeout-minutes`, satisfying FR-016 through the schema hook that
  already refuses a job without one
- [ ] T033 [US5] Remove the `timeout-minutes` input from `.github/workflows/pr-description.yml` and give
  its job a literal `timeout-minutes`. T031 goes green
- [ ] T034 [US5] Drop `timeout-minutes` from the `conventional-commits` and `pr-description` rows in
  `tests/published_surface.toml`, in the same change as T032 and T033 so the release verdict is reached
  from a tree that tells the truth (FR-017). `test_published_surface.py` is what fails if either half is
  missing

**Checkpoint**: the partition is real and held. **The release carrying this is a break, not a fix** —
below `1.0.0` that is signalled by the minor, and the obvious test is the wrong one.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T035 Read every new failure message against FR-021 by making each gate fail once: it names the
  artefact read, the expected value, and the edit to make. A message needing the test opened to
  understand is a defect in the gate
- [ ] T036 Run the SC-002 completeness sweep from `quickstart.md`: comment out each new gate's body in
  turn and confirm exactly one failure. Two failures means two gates hold one fact — principle I inside
  the suite. No failure means the gate is redundant and goes
- [ ] T037 Confirm `mise run ci` passes with the network down, and that no gate added by this feature
  carries a deselecting marker (FR-022)
- [ ] T038 [P] Check the documentation this change affects and correct it in the same change: whether
  `docs/technical-debt.md` TD-001's condition wording still matches what T026 asserts, and whether
  `README.md` says anything about a workflow name or a timeout input that T030 or T032–T033 has made
  stale. Stale framing is a defect, not a follow-up
- [ ] T039 Record the new test count against T001's baseline and confirm no pre-existing test was removed

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: after Setup. Blocks US4 and US5 only — US1, US2, US3 and US6 need neither
  accessor and can start immediately
- **Phase 3+ (stories)**: see per-story notes
- **Phase 9 (Polish)**: after every story that is being taken

### Story dependencies

| Story | Depends on | Blocks | Notes |
| --- | --- | --- | --- |
| US1 (P1) | nothing | nothing | may read US2's type-set accessor if T018 has landed; falls back to the workflow default if not |
| US6 (P1) | nothing | nothing | fully independent; contends with US5 for one file |
| US2 (P2) | nothing | nothing | |
| US3 (P2) | nothing | nothing | its three gates are independent of each other too |
| US4 (P3) | T002, T003 | nothing | |
| US5 (P3) | T003 | nothing | **release consequence** — separable into its own pull request |

No story depends on another. The only ordering constraints beyond Phase 2 are file contention.

### File contention — where [P] is unsafe

| File | Claimed by |
| --- | --- |
| `tests/test_workflow_properties.py` | T012, T013, T014, T015, T031 — sequential |
| `tests/capabilities.py` | T002, T003 — sequential |
| `tests/test_release_notes.py` | T004–T008 — sequential |
| `cliff.toml` | T007, T009, T010, T011 — sequential |
| `tests/test_commit_grammar.py` | T018–T021 — sequential |
| `tests/test_names.py` | T028, T029 — sequential |
| `.github/workflows/conventional-commits.yml` | T030 (rename), T032 (input) — sequential |
| `.github/workflows/pr-description.yml` | T030 (rename), T033 (input) — sequential |

### Parallel opportunities

- US3's three gates: T022, T024, T026 touch three different new files and can be written together
- T016 and T017 touch different existing files from each other and from T012–T015
- US1, US2, US3 and US6 can proceed simultaneously across people; only US4 and US5 wait on Phase 2

---

## Parallel Example: User Story 3

```bash
# Three independent gates, three new files, no shared reader:
Task: "Create tests/test_tool_versions.py with FR-009 (T022)"
Task: "Create tests/test_speckit_vendoring.py with FR-010 (T024)"
Task: "Create tests/test_actionlint_ignore.py with FR-011 (T026)"
```

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 — baseline
2. Phase 3 — US1
3. **Stop and validate**: render a range containing a ref pin and confirm nobody is mentioned

Phase 2 is skippable for the MVP: US1 needs neither accessor. That is the whole MVP — it closes the one
defect in this feature that reaches a person outside this repository, and it ships alone.

### Recommended order

1. **US1** — the only defect with an outside blast radius, and a published release cannot be withdrawn
2. **US6** — six small commits that make every later gate impossible to rot, and cheap to land
3. **US2**, **US3** — in either order, or together; independent
4. Phase 2, then **US4**
5. **US5 last, and only deliberately** — it is the one release decision in the feature

### Incremental delivery

Every story is shippable alone and every task leaves `mise run ci` green, so there is no point at which
the tree is half-migrated. US5 is the single exception worth planning around: its gate and its tree
change must land together, because a gate asserting a partition the tree does not have cannot pass.

---

## Notes

- `[P]` means a different file and no dependency on incomplete work — check the contention table before
  trusting one
- A gate and its pairing are one commit, never two
- The three tasks that fix the tree rather than gate it are T009, T010 and T032–T033. Everything else
  adds a gate over a rule that already holds, or a pairing over a gate that already exists
- Nothing here touches the instruction layers, or asserts that a cited principle number resolves. Both
  are out of scope until the layering merges with the other tree's
