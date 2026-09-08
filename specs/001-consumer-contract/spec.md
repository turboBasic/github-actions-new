# Feature Specification: The Consumer Contract

**Feature Branch**: `001-consumer-contract`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Specify the consumer contract this repository is to provide: reusable GitHub Actions workflows and composite actions for turboBasic repositories. Derive it from the functional behaviour of ../github-actions, read only from .github/workflows/*.yml, actions/*/action.yml and the Python those actions run, plus README.md as the advertised contract."

## Derivation

Every statement below was read from one of: `../github-actions/.github/workflows/*.yml`,
`../github-actions/actions/*/action.yml`, the Python those actions run, `../github-actions/README.md`,
or a live call site. The YAML is the authority on behaviour; the README is the advertised promise, and
where the two disagree both are recorded and the disagreement is an open question rather than a
resolved fact. Nothing was taken from the old repository's prose conventions, its decision history or
its tests.

Call sites read, and what they evidence:

| Consumer | Calls | Pinned |
| --- | --- | --- |
| `github-actions-test` | `python-ci` ×2, `conventional-commits`, `prek-advisory`, `release`, `populate-pr-description` | `@v4` |
| `python-app-baseline` | `python-ci`, `conventional-commits` — both at every default | `@v4` |
| `PopulationCircles2026` | `conventional-commits` only; **declined `python-ci` and inlined its own** | `@v2` |
| `repo-factory` | `populate-pr-description` | `@v2` |

Nothing outside the providing repository calls `dependency-review` or `release-decisions`.

## Clarifications

### Session 2026-09-07

- Q: What does the new repository owe a consumer that is already pinned somewhere? (OQ-009) → A:
  Fresh start, one migration — the new repository starts its own version line, and every consumer
  repins and re-checks its required contexts once, deliberately.
- Q: How should a capability handle a tool it invokes that the consumer's task-runner config must
  pin? (OQ-005) → A: Pre-flight and name it — check before use, and fail naming the tool, the
  capability, and where the consumer declares it.
- Q: What should "releases are cut from the default branch" be measured against? (OQ-006) → A: The
  repository's real default branch, taken from the run rather than a literal. No input.
- Q: What form should the pull-request-body capability take? (OQ-010) → A: A callable workflow only,
  owning its own checkout. The composite-action form is not carried forward.
- Q: Are the two CI inputs that do not match their documentation defects or intended? (OQ-007,
  OQ-008) → A: Defects. `run-lint: false` stops all linting, and the cache input is deleted — caching
  becomes unconditional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A Python repository gets one CI check (Priority: P1)

A maintainer of a `turboBasic` Python repository wants lint, typecheck and test to run on every pull
request and on every push to the default branch, and wants the verdict CI reaches to be the same
verdict they get locally. They add one job to one workflow, granting read access to the repository
contents, and get a single check whose name they can require in a branch ruleset.

**Why this priority**: Three of the four consumers call it, and two of them call it at every default.
It is the only capability with more than one caller outside the providing repository's own test
consumer.

**Independent Test**: A repository with a lockfile and named tasks calls the workflow with no inputs;
a pull request reports exactly one check, which fails when a task fails and passes when all pass.

**Acceptance Scenarios**:

1. **Given** a repository whose task runner declares lint, typecheck and test tasks and whose
   lockfile is current, **When** a pull request opens, **Then** one check reports and it passes only
   if all three tasks pass.
2. **Given** a repository whose lockfile disagrees with its manifest, **When** the workflow runs,
   **Then** the check fails before any task runs.
3. **Given** a repository with no typecheck task, **When** the caller switches that stage off,
   **Then** the check reports on the remaining two stages and does not fail for the missing one.
4. **Given** a repository whose tasks are named differently, **When** the caller names them,
   **Then** those tasks run instead of the defaults.
5. **Given** a caller that grants only read access to contents, **When** the run starts, **Then** it
   starts — the capability never demands a write permission.

---

### User Story 2 - One commit grammar, title and commits (Priority: P1)

A maintainer wants the text that will land on the default branch to be Conventional Commits,
whichever merge method is used: a squash merge takes the pull request title, a rebase merge keeps the
commits. They want one workflow that checks both, agreeing with the local commit hook, and two check
names they can require.

**Why this priority**: Three of the four consumers call it, and it is the only capability every
consumer that calls anything at all calls. It requires no task runner and no lockfile, so it is
available to a repository that can use nothing else here.

**Independent Test**: A pull request whose title is invalid fails the title check; a pull request
whose title is valid but which carries one invalid commit fails the commit check.

**Acceptance Scenarios**:

1. **Given** a pull request titled with an allowed type, **When** the title check runs, **Then** it
   passes.
2. **Given** a rejected title that a maintainer corrects with no push, **When** the caller subscribes
   to title edits, **Then** the check re-runs and passes.
3. **Given** a pull request carrying a commit whose message uses no allowed type, **When** the commit
   check runs, **Then** it fails and names the offending message.
4. **Given** a caller that declares its own allowed type list, **When** both checks run, **Then**
   both judge against that one list and cannot reach different verdicts.
5. **Given** a caller that declares a type containing a character other than a letter, digit,
   underscore or hyphen, **When** the workflow runs, **Then** it fails naming the bad list rather
   than silently accepting anything.
6. **Given** an event other than a pull request, **When** the workflow is reached, **Then** both
   checks report as skipped rather than as passed-without-checking.

---

### User Story 3 - A pull request body is written from its commits (Priority: P2)

A maintainer wants a pull request opened with a body already filled in from the commits it carries:
the subjects as a summary list, the full messages as a change list, dropped into the repository's own
pull request template.

**Why this priority**: Two consumers use it, and both hand-write the same job around it — a checkout
with full history, then the step. The capability is proven; the boilerplate around it was the
observable gap, and closing it is what makes the call site one `uses:` like every other capability.

**Independent Test**: A pull request carrying two commits, one with a body and one without, opens with
a rendered body containing both subjects and the one body, indented under its subject.

**Acceptance Scenarios**:

1. **Given** a pull request carrying commits and a template with the two substitution points,
   **When** the capability runs, **Then** the body is the rendered template.
2. **Given** a commit with a multi-paragraph body, **When** the body renders, **Then** the paragraph
   breaks survive and every paragraph stays inside its list item.
3. **Given** a pull request carrying no commits in range, **When** the body renders, **Then** the two
   substitution points become invisible prompts rather than empty space.
4. **Given** a repository whose template lives elsewhere, **When** the caller names the path,
   **Then** that template renders.
5. **Given** a consumer that writes only a `uses:` and one permission, **When** a pull request opens,
   **Then** the body renders — the consumer never writes a checkout, so it cannot get the history
   depth wrong.

---

### User Story 4 - A release is cut by merging an approval (Priority: P2)

A maintainer wants releasing to be an act of approval, not of typing: after a merge to the default
branch a proposal appears carrying the next version and the exact notes it would publish, and merging
that proposal tags the commit, publishes the release from those notes, and moves the ref consumers
pin. They want the machinery to refuse rather than publish anything it cannot justify, and to refuse
before any tag exists.

**Why this priority**: One consumer exercises it and no consumer depends on it, but it is the
capability that makes every other one deliverable — the moving ref is the whole distribution
mechanism, and a wrong tag is the one outcome here that cannot be reverted.

**Independent Test**: A dispatch with the dry-run switch on runs every refusal and renders the real
notes, then stops, leaving no tag and no release.

**Acceptance Scenarios**:

1. **Given** a merge whose declared version is already released, **When** the capability runs,
   **Then** it declines with a notice and does not fail the run.
2. **Given** a declared version not ahead of the highest existing release, and a run that is not a
   push, **When** the capability runs, **Then** it fails and says which version it read and which it
   compared against.
3. **Given** a range that renders no notes, **When** the capability runs, **Then** it refuses before
   creating any tag.
4. **Given** a range that breaks the consumer surface under a version staying on the same
   compatibility line, **When** the capability runs, **Then** it refuses, names the version it would
   accept instead, and creates no tag.
5. **Given** a release at `0.y.z`, **When** the capability publishes, **Then** the moving ref spans
   only the minor, a breaking change advances the minor, and a feature advances only the patch.
6. **Given** a successful publish, **When** the moving ref is updated, **Then** it is updated last —
   a failure before that point leaves consumers resolving the previous release.
7. **Given** a repository declaring no consumer surface, **When** the capability runs, **Then** it
   says so and treats every path as consumer-facing, refusing more often rather than less.
8. **Given** a repository declaring a misspelled surface key, **When** the capability runs, **Then**
   it refuses rather than silently widening the surface.

---

### User Story 5 - A whole-tree lint reports without blocking (Priority: P3)

A maintainer on a large tree wants the fast per-pull-request lint to cover only what changed, and
wants a second, non-blocking read of the whole tree reported as one pull request comment that is
updated in place rather than duplicated on each push.

**Why this priority**: One consumer, and only as the compensating control for a fast-lint option that
same consumer turns on. It has no value without that option, and no consumer uses either in anger.

**Independent Test**: A pull request whose unchanged files carry a lint finding gets one comment and a
green check; a second push updates that comment rather than adding one.

**Acceptance Scenarios**:

1. **Given** a lint finding outside the changed set, **When** the capability runs, **Then** a comment
   appears, a warning annotation appears, and the check still passes.
2. **Given** a second push with the finding unfixed, **When** the capability runs again, **Then** the
   existing comment is edited and no second comment appears.
3. **Given** a caller granting only read access to pull requests, **When** the run starts, **Then**
   the whole run fails at startup with no job and no diagnostic — so the capability must live where
   only callers wanting the comment grant the write.
4. **Given** a repository whose lockfile is broken, **When** the capability runs, **Then** the check
   fails — a green check here means the lint ran, not that it passed.

---

### User Story 6 - A consumer pins one ref and receives fixes (Priority: P1)

A maintainer wants to name one ref at each call site and stop thinking about it: fixes and features
arrive by resolving that ref on the next run, with no pull request in their repository, and nothing
they cannot absorb that way arrives without a new ref to move to deliberately.

**Why this priority**: It is the promise that makes every other story cheap to consume, and the one
whose breach is most expensive — a retired check name blocks every pull request in every consumer
until each one is edited by hand.

**Independent Test**: A consumer pinned to the compatibility ref receives a fix released after it
pinned, without editing its own workflow.

**Acceptance Scenarios**:

1. **Given** a consumer pinned to the compatibility ref, **When** a fix is released, **Then** the
   next run resolves it with no change at the call site.
2. **Given** a consumer pinned to an exact release, **When** later releases happen, **Then** that
   consumer keeps resolving exactly what it pinned.
3. **Given** a change a consumer cannot absorb by resolving the ref alone — a moved call site, a
   retired check name, a newly demanded permission — **When** it ships, **Then** it ships on a new
   compatibility ref and the old one stays where it is.
4. **Given** a consumer still pinned to a superseded ref, **When** it runs, **Then** it keeps working
   against what that ref froze.
5. **Given** a consumer pinned at the old repository, **When** it adopts this one, **Then** it repins
   and re-checks its required contexts exactly once, and nothing here promises its old pin will keep
   resolving.

---

### Edge Cases

- A caller grants less than a called job declares. The run fails at startup with no job, no log and
  no annotation, because job permissions are validated before any condition can skip the job. Every
  capability's permission demand is therefore part of its published contract, not a runtime detail.
- A caller reaches a capability from an event it does not handle. Every job here is gated on the
  pull-request event, and a skipped job reports success — so a required check reached from the wrong
  event passes without checking anything.
- A caller uses the fork-safe pull-request event. The gates skip, the check passes vacuously, and a
  checkout resolves the base rather than the commits under review.
- A caller turns a check off and leaves its name in a required-checks list. The list keeps naming a
  gate that no longer reports, which blocks every pull request.
- A repository's default branch is not named `main`. It releases exactly like one that is: the
  refusal is measured against the repository's own default branch, not a literal name.
- Two releases race. Serialisation is required: two runs moving one compatibility ref would leave it
  pointing anywhere.
- A release proposal has been edited by a human. Their version outranks the computed one and survives
  every later refresh.
- A release range becomes empty after a proposal was opened. The proposal is closed rather than left
  describing nothing.
- A commit subject reaches a shell line. A subject is a merged pull request title, which is
  attacker-influenceable text; no capability may place caller-controlled text into a command line.
- A repository has no task runner configuration at all. Only the commit-grammar capability is usable.

## Requirements *(mandatory)*

### Functional Requirements

#### The shape of the offering

- **FR-001**: Every published capability MUST be one of two kinds of thing a consumer names in its own
  workflow: a callable workflow, which a consumer calls as a whole job and which owns its own runner,
  checkout and tool provisioning; or a composite action, which a consumer places as a step inside a
  job it owns. Which kinds are in use is decided per capability by what the capability needs, not by a
  requirement that both be represented — and as settled by F1, the published set today is callable
  workflows alone.
- **FR-002**: Every published capability MUST be resolvable by ref from a consumer repository, and
  MUST NOT require the consumer to vendor, copy or fork anything to use it.
- **FR-003**: A capability MUST NOT require the consumer to grant any permission it does not use.
  Where a capability needs a write permission, it MUST be separately callable from the capabilities
  that do not, so that only consumers wanting that behaviour grant the write.
- **FR-004**: Every permission a consumer must grant MUST be documented at the capability, because a
  shortfall is unobservable at runtime: the run fails before any job exists.
- **FR-005**: Every check name a capability composes MUST be documented, because those names are what
  consumers name in branch rulesets and a retired name blocks every pull request in every consumer.
  A consumer's check name is its own job identifier and the called job's name, joined; the capability
  owns only the second half.
- **FR-006**: A capability that only makes sense on a pull request MUST report as skipped rather than
  as passed on any other event, and MUST document that a skipped job reports success.
- **FR-007**: Concurrency grouping MUST remain the consumer's to declare, since a called workflow
  cannot set its caller's group.
- **FR-008**: No capability may place caller-controlled text — a commit subject, a pull request title,
  a task name, a path — into a command line by interpolation. Such values reach the code that uses
  them by other means.
- **FR-009**: Where a capability invokes a tool that must come from the consumer's own task-runner
  configuration, that tool stays the consumer's to pin — which is what makes a local verdict and a CI
  verdict agree — and the capability MUST check for it before invoking it, failing with a message
  naming the tool, the capability that needs it, and where the consumer declares it (ruling, OQ-005).
  Failing with `command not found` is not an acceptable contract, and neither is a capability quietly
  pinning a version the consumer does not control.
- **FR-009b**: Each capability's tool prerequisites MUST be published alongside its file
  prerequisites, so a consumer can satisfy them before its first run rather than by reading a failure.
- **FR-009a**: This repository starts its own version line and inherits no ref from the repository it
  supersedes (ruling, OQ-009). Adopting it is one deliberate migration per consumer: repin the call
  site, re-check the required contexts. No old pin is promised to keep resolving, and the contract
  carries no compatibility surface for one. Consumers MUST therefore be given, once, the list of what
  changes at a call site and which check names to require.

#### CI over a Python project

- **FR-010**: A consumer MUST be able to run its own lint, typecheck and test tasks as one check by
  calling one workflow with no inputs, needing only read access to repository contents.
- **FR-010a**: This capability's scope is a **Python project**, and its name and documentation MUST
  say so (ruling, OQ-004). A current Python lockfile is an unconditional prerequisite, not a stage a
  consumer can switch off, and a repository without one is out of scope rather than badly served. The
  three stage switches exist for a Python repository missing one of the three stages — they are not a
  route to using this capability without Python.
- **FR-011**: The tasks run MUST be the consumer's own named tasks, so that the verdict CI reaches
  and the verdict a maintainer reaches locally cannot diverge.
- **FR-012**: Each of the three stages MUST be individually switchable off, and each stage's task
  name MUST be individually overridable.
- **FR-013**: The workflow MUST fail if the consumer's lockfile disagrees with its manifest, before
  any stage runs.
- **FR-012a**: Switching the lint stage off MUST stop every kind of linting this capability performs,
  including the changed-files lint (ruling, OQ-008). An input named for a stage governs that stage
  entirely or it is misnamed.
- **FR-014**: A consumer MUST be able to substitute a changed-files lint for the full lint task, and
  MUST be told, at the point of that option, that a pull request can then pass while the tree is
  broken and which capability compensates for it.
- **FR-014a**: Hook environments MUST be cached unconditionally, with no input governing it (ruling,
  OQ-007). No consumer has ever wanted the cache off, and an input that silently did nothing unless a
  second input was also set was worse than no input at all.
- **FR-015**: A consumer whose slow checks are reserved for a later hook stage MUST be able to name
  that stage, and MUST be told that without it those checks silently stop running.
- **FR-016**: Contract:

  | Input | Default | What the consumer gets |
  | --- | --- | --- |
  | `run-lint` | `true` | Runs the lint stage |
  | `run-typecheck` | `true` | Runs the typecheck stage |
  | `run-tests` | `true` | Runs the test stage |
  | `lint-task` | `lint` | Names the lint task |
  | `typecheck-task` | `typecheck` | Names the typecheck task |
  | `test-task` | `test` | Names the test task |
  | `lint-changed-only` | `false` | Lints the changed set instead of running the lint task, on a pull request only |
  | `hook-stage` | `""` | Hook stage for the changed-files lint; empty is the default stage |
  | `timeout-minutes` | `20` | Job timeout |

  Outputs: none. Permissions the consumer grants: read access to contents. Check name composed:
  `python-ci`. Prerequisites in the consumer's tree: a task-runner configuration declaring the tasks
  being run and pinning the tools they need, and a current lockfile.

- **FR-016a**: No capability takes an input pinning the task-runner's own release (ruling, F2). No
  call site in any consumer set the one that existed, this repository's own CI does not set it either,
  and its default did nothing — so its only effect anywhere was to be surface that could be depended
  on. The same deletion applies to the advisory lint, which declared it for the same reason and with
  the same evidence. Removing an input is a breaking change and adding one is not, so the absence is
  the reversible choice: if a task-runner release ever breaks every consumer at once, the input comes
  back on the same compatibility line and no call site has to change.

#### Commit and title grammar

- **FR-017**: A consumer MUST be able to hold both the pull request title and every commit message in
  the pull request range to one Conventional Commits grammar, by calling one workflow.
- **FR-018**: Both checks MUST judge against one authoritative type list, so they cannot reach
  different verdicts about the same word. That list MUST NOT be read from the consumer's own commit
  tooling configuration, since that would let the two checks disagree.
- **FR-019**: The default type list MUST be the one the local commit hook enforces, so a message
  accepted locally cannot fail here.
- **FR-020**: The commit check MUST use the same tool as the local commit hook, so local and CI
  verdicts cannot disagree.
- **FR-021**: A malformed type list MUST fail the run naming the list, rather than being silently
  accepted. Types are bare words.
- **FR-022**: The capability MUST be usable by a repository with no task-runner configuration at all.
- **FR-023**: Either check MUST be individually switchable off, and the consumer MUST be told to
  retire the corresponding required check name in the same change.
- **FR-024**: The consumer MUST be told to subscribe to title edits explicitly, because the default
  activity types omit them and a corrected title is an edit rather than a push.
- **FR-025**: Contract:

  | Input | Default | What the consumer gets |
  | --- | --- | --- |
  | `check-title` | `true` | Validates the pull request title |
  | `check-commits` | `true` | Validates every commit message in the range |
  | `types` | the local hook's own set | Newline-separated allowed types, authoritative for both checks |
  | `timeout-minutes` | `5` | Job timeout |

  Outputs: none. Permissions the consumer grants: read access to contents, and read access to pull
  requests — at both the workflow and the job level, because the title check reads the title from the
  API. Check names composed: `pr-title` and `commit-messages`. Prerequisites in the consumer's tree:
  none.

#### Pull request body from commits

- **FR-026**: A consumer MUST be able to have a pull request body rendered from the commits in range
  into its own pull request template, with the commit subjects available as a summary and the full
  messages as a change list.
- **FR-027**: Multi-paragraph commit bodies MUST render with their paragraph breaks intact and each
  paragraph inside its own list item.
- **FR-028**: An empty range MUST render invisible prompts rather than blank sections.
- **FR-029**: The capability MUST provision the tooling it needs itself, so a consumer needs no
  language or package-manager setup step of its own.
- **FR-029a**: It MUST be a callable workflow owning its own checkout, not a step a consumer places in
  a job it built (ruling, OQ-010). The consumer therefore identifies nothing — not the pull request,
  not the repository, not the commit range, not a token — because all of it is already in the run. The
  shallow-checkout failure mode is removed rather than documented: no consumer writes the checkout, so
  no consumer can get its depth wrong.
- **FR-030**: The template location MUST be overridable.
- **FR-031**: Contract:

  | Input | Default | What the consumer gets |
  | --- | --- | --- |
  | `template-path` | `.github/PULL_REQUEST_TEMPLATE.md` | Which template renders |
  | `timeout-minutes` | `5` | Job timeout |

  Outputs: none. Permissions the consumer grants: read access to contents, and write access to pull
  requests. Check name composed: `pr-description`. Prerequisites in the consumer's tree: a pull
  request template containing the two substitution points. The consumer owns only its trigger — and
  should trigger on a pull request opening, since rewriting the body on every push discards whatever a
  human typed.

#### Releasing

- **FR-032**: A consumer MUST be able to cut its own releases the same way this repository cuts its
  own, by calling one workflow after its own CI verdict.
- **FR-033**: The capability MUST have no trigger of its own, so a caller's dependency edge is the
  only route to it and nothing can reach the tagging step around that edge.
- **FR-034**: The version released MUST be the one the consumer's manifest declares, decided by a
  merged change rather than computed at release time. The capability MUST NOT write a version.
- **FR-035**: The capability MUST refuse, and MUST refuse before creating any ref, when: the declared
  version is not ahead of the highest existing release across every compatibility line; the range
  renders no notes; or the range breaks the consumer surface while the declared version stays on a
  compatibility line that already has a release.
- **FR-036**: The already-released case reached from a routine merge MUST decline with a notice
  rather than fail, so a consumer's default branch does not redden for doing nothing wrong.
- **FR-037**: A consumer MUST be able to run every refusal and render the real notes without creating
  anything, from a branch.
- **FR-037a**: A release MUST be cut only from the repository's default branch, and "default branch"
  MUST mean whatever that repository's default branch actually is, read from the run rather than
  compared against a literal name (ruling, OQ-006). There is no input for it: a consumer has nothing
  to configure and nothing to set wrong. A run from anywhere else is refused unless it is a dry run,
  and the refusal names the branch the run is on and the branch it expected.
- **FR-038**: The consumer MUST declare, in its own manifest, which paths a consumer of *it*
  resolves; that declaration narrows the breaking-change refusal only. An absent declaration MUST
  mean every path counts — refusing more often rather than less — and MUST be reported. A misspelled
  key MUST refuse rather than silently widen the surface. There MUST be no input to override this,
  because one repository's layout is right for another only by coincidence.
- **FR-039**: A declared path that is empty, holds whitespace, or begins with a hyphen MUST be
  refused before any ref exists.
- **FR-040**: The version tag MUST be immutable and annotated. The compatibility ref MUST be moved
  last, after the release exists, so an earlier failure leaves consumers on the previous release.
- **FR-041**: Below `1.0.0` the compatibility boundary is the minor: the moving ref spans a minor, a
  breaking change advances the minor, a feature advances only the patch, and no ref spanning every
  pre-1.0 release is ever published. Above it the moving ref spans a major and a feature advances the
  minor. This boundary MUST have exactly one statement, which the refusal, the increment and the ref
  name all read.
- **FR-042**: Notes MUST come from commit types, never from a label on a pull request.
- **FR-043**: Contract:

  | Input | Default | What the consumer gets |
  | --- | --- | --- |
  | `dry-run` | `false` | Runs every refusal and renders the real notes, then stops before any ref |

  Outputs: none. Permissions the consumer grants: write access to contents. Check name composed:
  `tag-and-publish`. Prerequisites in the consumer's tree: a manifest declaring the version, a notes
  configuration, and a task-runner configuration pinning the notes renderer (see Open Question 5).

- **FR-044**: Releasing this repository MUST itself be an act of approval: after a merge to the
  default branch, a proposal carrying the next version and the exact notes it would publish is opened
  or refreshed, and merging it releases. A human's version on that proposal MUST outrank the computed
  one and survive every refresh. A proposal whose range has become empty MUST be closed.
- **FR-045**: The proposal's writes MUST use an identity that can open a pull request without the
  repository allowing its own automation to create pull requests.

#### Advisory whole-tree lint

- **FR-046**: A consumer MUST be able to get a non-blocking whole-tree lint reported as one pull
  request comment, updated in place rather than duplicated on later pushes, plus a job summary and a
  warning annotation.
- **FR-047**: Non-blocking MUST cover the lint verdict only. The capability's own setup — including
  the lockfile check — still fails the check, so a green check means the lint ran, not that it passed.
  The consumer MUST be told this.
- **FR-048**: The hook stage MUST be nameable, and the consumer MUST be told to pass the same stage
  here as to the CI capability, or the two runs disagree about which checks apply.
- **FR-049**: Contract, as a callable workflow:

  | Input | Default | What the consumer gets |
  | --- | --- | --- |
  | `hook-stage` | `""` | Hook stage; empty is the default stage |
  | `timeout-minutes` | `20` | Job timeout |

  Outputs: none. Permissions the consumer grants: read access to contents and **write access to pull
  requests**. Check name composed: `prek-advisory`.

- **FR-049a**: This capability MUST be a callable workflow and nothing else (ruling, F1). It is not
  also published as a composite action a consumer places in a job it already owns. That form was never
  called, it would have put the write permission back inside the consumer's own job — which is the one
  thing separating this capability from the CI one buys — and its existence is what would force the
  callable workflow to name this repository by a moving ref.

#### Release decisions — internal, not consumer surface

- **FR-050**: The release refusals, the version increment, the compatibility-line boundary and the
  surface filter MUST be callable code rather than shell embedded in a workflow, and MUST do no
  network access, so every decision is answerable offline from a file and an environment. This is the
  obligation; the shape it takes is not consumer contract, and its inputs and outputs carry no
  stability promise to anyone outside the release path (ruling, OQ-003).
- **FR-051**: It MUST answer exactly one named question per invocation, write its answers where the
  release path can read them, its reasoning as annotations a maintainer reads, and signal by exit
  status — not by a string a caller must compare — that the caller should not proceed.
- **FR-052**: The questions it answers are: is this version releasable at all; do these notes say
  anything and do they break the surface; what is the next version; what version is declared; and
  what does the declared consumer surface narrow to. It composes no check name and declares no
  permission.

### Key Entities

- **Capability**: one thing a consumer can call. Either a callable workflow (owns a runner, composes
  a check name) or a composite action (a step in the consumer's job, composes nothing).
- **Check name**: the second half of what a consumer requires in a ruleset. Owned by the capability,
  named by the consumer's job identifier in front of it. Retiring one is a breaking change.
- **Permission demand**: what a caller must grant for a capability's run to start at all. Validated
  before any job exists, so it cannot be discovered by running.
- **Compatibility ref**: the moving ref a consumer pins. Spans a major from `1.0.0` up, a minor below
  it. Carries fixes and features, never a break.
- **Consumer surface declaration**: the path list, in the released repository's own manifest, saying
  which paths a consumer of *it* resolves. Narrows the breaking-change refusal only.
- **Release proposal**: a pull request carrying the next version and the exact notes it would
  publish. Merging it is the approval.
- **Release refusal**: a named reason not to publish, each evaluated before any ref exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new Python repository reaches a green CI check by adding one job of five lines and
  granting one read permission — no capability requires a second file to be written to be used.
- **SC-002**: Every permission a consumer must grant, and every check name a consumer must require,
  is discoverable without running anything.
- **SC-003**: A repository that can use no other capability here — no task runner, no lockfile — can
  still have its commit grammar checked.
- **SC-004**: A consumer pinned to a compatibility ref absorbs 100% of fixes with zero changes at its
  call sites, and is never presented with a change it cannot absorb that way on that ref.
- **SC-005**: A refused release leaves zero refs, zero releases and zero published artifacts behind.
- **SC-006**: A release that would move a compatibility ref onto a broken contract is refused in
  100% of cases, including below `1.0.0`, where the naive major-number test is wrong.
- **SC-007**: Every release decision — each refusal, the increment, the compatibility boundary, the
  surface filter — is answerable offline.
- **SC-008**: A run that fails does so with a message naming what it read, what it compared against,
  and what a maintainer should change; no capability fails with only an exit code.
- **SC-009**: No capability places caller-controlled text into a command line.
- **SC-010**: A consumer's local verdict and its CI verdict agree, for both the code checks and the
  commit grammar, because both run the same tool over the same configuration.

## Assumptions

- Consumers are repositories under one owner, sharing a trust boundary with this one. This is why a
  moving ref is an acceptable pin here and would not be for a third party.
- The tooling ecosystem a consumer brings — its task runner, its lockfile, its hook runner, its notes
  renderer — is assumed rather than specified: the capabilities call the consumer's own named tasks
  rather than replacing them, and that is the whole reason local and CI verdicts agree.
- "What a consumer observes" includes the shape of its own call site, the permissions it grants, the
  check names it requires, and the ref it pins. All four are contract; none is implementation.
- The published set is five capabilities: Python CI, commit grammar, pull-request body, releasing, and
  the advisory whole-tree lint. Dependency review is cut (ruling, OQ-002) and release decisions are
  internal (ruling, OQ-003).
- Nothing is built or published from this repository. The ref is the artifact.
- Priorities are assigned from call-site evidence, not from perceived sophistication: a capability two
  consumers call at every default outranks one no consumer calls.

## Rulings

Decided by the maintainer. Recorded here because each removes something the observed behaviour would
otherwise have carried forward by default.

- **OQ-002 — Dependency review is cut from the published surface.** No consumer has ever called it,
  and the providing repository declined to require its context on its own pull requests. It is not a
  capability of this repository. If this repository wants the gate on its own pull requests, that is
  its own CI configuration and not part of any contract. This also retires the divergence that would
  otherwise have needed resolving: the workflow's input description said an empty severity threshold
  **fails on any severity** while the README said it **uses the underlying action's own default** —
  two different contracts for the value every caller got by default.
- **OQ-003 — Release decisions are internal.** The obligation is that every release decision is
  answerable offline from a file and an environment; the unit that answers them promises nothing to
  anyone outside the release path, and changing its inputs or outputs is not a breaking change. See
  FR-050 through FR-052.
- **OQ-004 — Python CI is Python CI.** The unconditional lockfile sync is intended, not a defect. The
  capability's scope is a Python project and its name and documentation must say so; the three stage
  switches serve a Python repository missing a stage, and are not a route to using it without Python.
  `PopulationCircles2026` is correctly out of scope, and its inlined CI is not a fork to be reclaimed.
  See FR-010a.
- **OQ-005 — Tool prerequisites are pre-flighted, not just documented.** The old README stated each
  capability's *file* prerequisites but not its *tool* ones: the consumer's task-runner configuration
  must also pin the package manager the CI and advisory capabilities invoke, and the notes renderer the
  release capability invokes. Those tools stay the consumer's to pin, and each capability checks for
  them before use and fails naming what is missing and where to declare it. See FR-009 and FR-009b.
- **OQ-006 — The default branch is read, not assumed.** The old refusal ladder compared the run's ref
  against the literal `refs/heads/main`, undocumented, so a consumer whose default branch is named
  anything else could not release and would read the failure as being about a branch it does not have.
  The refusal is measured against the repository's actual default branch instead, with no input to set
  wrong. See FR-037a.
- **OQ-007, OQ-008 — Two CI inputs were defects, not undocumented features.** Hook-environment caching
  silently did nothing unless the changed-files lint was *also* on, and switching the lint stage off did
  not stop the changed-files lint. Both are fixed rather than documented: the lint switch governs every
  kind of linting, and caching becomes unconditional with the input deleted, since no consumer has ever
  wanted it off. The cache input is dropped from the advisory lint capability too, on the same
  reasoning — one capability keeping it would be surface that exists only by inheritance. See FR-012a
  and FR-014a.
- **OQ-009 — A fresh version line, and one migration.** The advertised pin and the pins in use
  disagreed: the README said to pin `@v4` and that the two preceding majors were frozen, while
  `PopulationCircles2026` and `repo-factory` were both still pinned to `@v2`. Rather than resolve
  which reading was true, this repository inherits neither: it starts its own version line, and each
  consumer repins and re-checks its required contexts once. No compatibility surface is carried for an
  old pin. See FR-009a.
- **OQ-010 — The pull-request body is a callable workflow, not an action.** Both consumers of the old
  action hand-wrote the same job around it: a full-history checkout, then the step. It becomes a
  callable workflow owning that checkout, so the call site is one `uses:` and one permission, and the
  five identifying inputs disappear along with the shallow-checkout trap. The composite-action form is
  not carried forward. See FR-029a and FR-031.
- **F1 — The advisory lint is a callable workflow only.** Raised by the planning research rather than
  by a disagreement between the observed behaviour and the advertised contract, and settled here
  because it changes what is published. The action form was never called by anyone. It would have put
  the `pull-requests: write` demand back inside a job the consumer owns, which cancels the one thing
  FR-003 separates this capability out to achieve. And it is what would force the callable workflow to
  name this repository by a moving ref, so cutting it leaves exactly one such reference in the tree
  instead of two. This is OQ-010's reasoning applied to the one place it had not been. The published
  set is therefore five callable workflows and no composite action, which is why FR-001 no longer reads
  as requiring both kinds. Re-adding an action later would be a new capability rather than a change to
  this one, so nothing about this decision is expensive to revisit. See FR-001 and FR-049a.
- **F2 — `mise-version` is not an input.** Two capabilities declared it, six call sites could have set
  it — the four consumers, plus this repository's own CI on each of the two capabilities — and none
  did. Its default did nothing, so at every real call site its effect was to exist. That is the shape
  OQ-007 already ruled on: an input no consumer sets, doing nothing at the value everyone gets, is
  worse than no input. What decides the timing rather than the answer is that **removing an input is a
  breaking change and adding one is not**: deleting it now costs nothing and cannot be got wrong,
  whereas keeping it becomes irreversible the moment a consumer names it. The one thing genuinely lost
  is the only escape hatch a consumer has if a task-runner release breaks every repository at once —
  and that hatch can be restored additively, on the same compatibility line, the day it is wanted. See
  FR-016a.

## Open Questions

Each is a place where the observed behaviour and the advertised contract disagree. Both readings are
recorded; none is resolved here.

- **OQ-011 — One refusal appears to be unreachable.** The release capability fails if the decision
  unit reports no compatibility ref to move, with a message describing a release cut before the ref
  caught up. The decision unit's ref name is derived from the version and is never empty for any
  version that got past the earlier refusals. Either the guard is defensive against a state the
  contract forbids, or there is a path here the YAML alone does not show. Recording rather than
  resolving, because the providing repository's tests were deliberately not read.
