# Feature Specification: One check over what a change starts depending on

**Feature Branch**: `004-dependency-review`

**Created**: 2026-09-12

**Status**: Merged 2026-09-12, in no release yet

**Input**: User description: "A pull request that introduces a dependency carrying a known advisory, or a licence this project will not accept, is refused before it merges. Nothing in this library does that today."

## User Scenarios & Testing *(mandatory)*

Two readers. The **consumer** maintains another `turboBasic` repository, pins a ref of this one and
types check names into a ruleset; they never read this tree. The **maintainer** works here. Every
capability this library publishes today judges the code in a change; none judges what the change starts
depending on, and the update bots do not fill the gap — they propose upgrades for dependencies a
repository already has, on their own schedule, and say nothing about the one being added right now,
which is the moment the decision is cheapest to reverse and the only moment anybody is looking at it.

### User Story 1 - An advisory is refused before it merges (Priority: P1)

A consumer's pull request adds a package. The version it adds carries a published advisory. Today every
check on that pull request is green, because every check reads the diff's code and none reads what the
diff added to the dependency graph. The consumer wants one check that reads the difference between the
pull request's base and its head, judges it against the advisory database, and reddens.

**Why this priority**: It is the entire capability. Nothing else in this story set has value without
it, and no other capability here covers the gap.

**Independent Test**: Callable on its own. Open a pull request in a repository that calls it, adding a
dependency version with a known advisory, and confirm the check fails naming the advisory; move to a
version with none and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a repository calling the capability from a `pull_request` workflow, **When** the pull
   request adds a dependency version carrying an advisory at or above the severity floor, **Then** the
   check fails and the log names the advisory, the package and the version.
2. **Given** the same repository, **When** the pull request adds a dependency version carrying no
   advisory, **Then** the check passes.
3. **Given** a pull request touching no dependency manifest at all, **When** the check runs, **Then**
   it passes, having read a difference that is empty.
4. **Given** a pull request whose only finding is below the severity floor the call site set, **When**
   the check runs, **Then** it passes and the finding appears in the run's output rather than as a
   failure.

---

### User Story 2 - Adopting it costs one permission (Priority: P1)

A consumer copies one call site out of the consumer-facing reference, grants one permission, and has the
check reporting. They grant no write access to their pull requests, and they identify nothing — no
token, no pull request number, no repository, no commit range.

**Why this priority**: A called workflow's permission demand is validated before any job exists, so a
capability demanding more than it needs forces every caller to grant it, with no log and no annotation
if they do not. The permission surface is the adoption cost, and this story is what keeps it at one
scope at read. It ships with Story 1 or nobody can take the capability.

**Independent Test**: Copy the published call site into a repository unchanged, grant nothing beyond
what it names, and confirm the run starts and the check reports.

**Acceptance Scenarios**:

1. **Given** the call site as published, **When** a consumer grants `contents: read` and nothing else,
   **Then** the run starts and the check reports.
2. **Given** the capability, **When** its whole permission demand is read across every block it
   declares, **Then** it is exactly `contents: read`, and no block anywhere asks for write access to
   pull requests.
3. **Given** the capability, **When** its steps are read, **Then** none checks the repository out and
   none reads a working tree: the difference is read from the API.
4. **Given** the capability, **When** its declared inputs are read, **Then** there is exactly one — the
   severity floor at which a finding fails rather than informs — carrying a description and an explicit
   default.

---

### User Story 3 - It is honest about what it does not judge (Priority: P2)

A consumer reads the reference to decide whether to require the check in a ruleset. They learn the one
event it handles, that it reports success without reading anything under any other, what it fails on,
what it only reports, and that their repository's dependency graph has to be on. None of that is
something a first run teaches them.

**Why this priority**: A skipped job reports success, and a green check is the one nobody investigates
(principle VII). The capability is required-eligible under one event and misleading under every other,
and the difference has to be written down where the other capabilities' skip conditions are written
down. It is P2 rather than P1 because a consumer who copies the published call site verbatim is already
on the right event.

**Independent Test**: Read the published surface record and the consumer-facing section against the
capability's own YAML, and confirm the skip, its event and its reason are declared and agree.

**Acceptance Scenarios**:

1. **Given** the capability's job, **When** it is reached from any event but `pull_request`, **Then** it
   does no work — and that skip, its event and its reason are registered in the published surface
   record, so the existing gate over event-conditional jobs accepts it without an exemption.
2. **Given** the consumer-facing reference, **When** a consumer reads this capability's section,
   **Then** it says which event the composed context may be required under, and that requiring it under
   another gives a gate that passes without reading anything.
3. **Given** a calling repository whose dependency graph is switched off, **When** the check runs,
   **Then** the run fails and names the setting, where the consumer changes it, and that this capability
   cannot switch it on for them.
4. **Given** the consumer-facing reference, **When** a consumer reads what the check fails on, **Then**
   it distinguishes the finding that reddens the check from the finding that only appears in the run's
   output, and does not promise a refusal the capability does not make.

---

### User Story 4 - Called here, required nowhere (Priority: P3)

A dependency landing here gets the same look as a consumer's, so this repository calls the capability at
the commit under review. But an advisory nobody has triaged yet must not block a merge, so the composed
context reports and is not a required check, and the branch ruleset does not name it.

**Why this priority**: It is what makes this repository a real consumer of its own capability rather
than a describer of it, and it is the cheapest of the four to get wrong in the direction that hurts —
naming the context in the ruleset would let an upstream advisory nobody has read block every pull
request here. It ships last because Stories 1 to 3 are what a consumer receives.

**Independent Test**: Open any pull request here and confirm the context appears, reports, and is absent
from the required set; then confirm the suite passes with a context composed but not required.

**Acceptance Scenarios**:

1. **Given** a pull request in this repository, **When** the checks are listed, **Then** the composed
   context appears and reports.
2. **Given** the committed branch ruleset, **When** its required contexts are read, **Then** this
   context is not among them, and the suite passes with it composed but not required.
3. **Given** the calling job's identifier, **When** it is joined to the called job's name to compose
   the context, **Then** the two halves repeat no word.
4. **Given** the calling workflow, **When** its permissions are read, **Then** it grants exactly what
   the capability demands and nothing more.

---

### Edge Cases

- **The calling repository's dependency graph is off.** It is a repository setting, not something a
  call site can pass. The run cannot succeed, and the failure has to name the setting rather than
  surface as an unexplained API refusal.
- **The check is reached from an event other than `pull_request`.** There is no base and no head to
  difference, so there is nothing to judge and the job does no work — which reports success.
- **A consumer requires the context under an event the job skips.** The gate then passes without
  reading anything; the reference says so, and the skip is registered where every other capability's
  is.
- **A finding sits below the severity floor.** It informs and does not fail. A consumer wanting it to
  fail lowers the floor; nothing here re-ranks a finding.
- **The pull request is from a fork.** The difference is read from the API with the run's own token
  under `contents: read`; nothing about the fork's tree is checked out or executed.
- **A licence finding with no policy for the published action to read.** It appears in the run's output
  and fails nothing. This capability exposes no licence policy input and does not reinterpret the
  published action's defaults, so the reference must say which half of the promise holds.
- **The dependency graph has not finished computing for the head commit.** The published action's own
  behaviour governs; this capability neither retries nor suppresses, and a consumer sees the action's
  own message.
- **A consumer wants the summary posted as a pull request comment.** That needs write access to pull
  requests, which would force every caller to grant it. They fork this capability and ask for the
  permission in a workflow that says so.

## Requirements *(mandatory)*

### Functional Requirements

The capability:

- **FR-001**: A new capability MUST be published as a callable workflow whose only trigger is a
  workflow call, composing exactly one check name, so a consumer requires one context: their own job
  id, then that name.
- **FR-002**: It MUST read the dependency-graph difference between the pull request's base and its
  head, judged by a published third-party action. It MUST NOT check the repository out, and no step MUST
  read a working tree.
- **FR-003**: Its whole permission demand — the union of every block it declares — MUST be exactly
  `contents: read`, with the reason written beside the grant. No block MUST ask for any level of access
  to pull requests, and no future input MUST be able to raise the demand.
- **FR-004**: It MUST declare exactly one input: the severity floor at or above which a finding fails
  the check rather than informing. The input MUST carry a description and an explicit default.
- **FR-005**: It MUST NOT declare a timeout input, because its runtime is one API-driven action rather
  than a function of the caller's tree; its job MUST therefore fix its own timeout.
- **FR-006**: The published action MUST be pinned to a full commit digest with its version written
  beside the pin.
- **FR-007**: The published action's summary-commenting behaviour MUST NOT be enabled, and no input
  MUST expose it.
- **FR-008**: The capability MUST NOT wrap, filter, re-rank or reinterpret the published action's
  judgement. The action's own defaults are the policy.
- **FR-009**: Its workflow name MUST be the call-only marker followed by its filename stem, and its job
  name MUST be lowercase-kebab-case, so the existing name gates accept it unchanged.

Honesty about what it cannot judge:

- **FR-010**: Its job MUST do no work under any event but `pull_request`, and that skip, the event and
  the reason MUST be registered in the published surface record, so the existing gate over
  event-conditional jobs accepts it with no exemption (principle VII).
- **FR-011**: When the run cannot read the difference because the calling repository's dependency graph
  is off, the failure MUST name the setting, where the consumer changes it, and that this capability
  cannot change it for them. An exit code, or the API's own refusal alone, is not a result.
- **FR-012**: The consumer-facing reference MUST state the one event under which the composed context
  may be required, and MUST state that requiring it under another gives a check that reports success
  without reading anything.
- **FR-013**: The consumer-facing reference MUST distinguish what reddens the check — an advisory at or
  above the floor — from what only appears in the run's output, and MUST NOT promise a licence refusal
  this capability does not make.

Arriving on the published surface:

- **FR-014**: The published surface record MUST gain this capability's row in the same change: its kind,
  that it is published, the check name it composes, its one input name, its permission demand, its
  empty tool-prerequisite list, and its skip entry.
- **FR-015**: Its tool-prerequisite list MUST be empty and MUST be true: the capability MUST invoke no
  tool the consumer's own configuration has to pin, and MUST provision no task runner.
- **FR-016**: The consumer-facing reference MUST gain a section for it carrying a call site that can be
  copied as it stands, the context it composes, and the permission demand as prose rather than as a
  table naming a default. Any count or list of capabilities the reference states MUST be corrected in
  the same change.
- **FR-017**: No existing capability MUST change. No existing check name, input name, default,
  permission demand or skip entry MUST move, so a consumer resolving the ref they already pin absorbs
  this by resolving it alone (principle IV).

This repository as its own consumer:

- **FR-018**: A self-triggering caller workflow MUST call the capability on this repository's own pull
  requests, resolving at the commit under review, granting exactly the demanded permission and no more.
- **FR-019**: The calling job's identifier MUST be chosen so the composed context's two halves repeat no
  word.
- **FR-020**: The committed branch ruleset MUST NOT name the composed context. The context reports and
  is not a required check, and the suite MUST pass with a context composed but not required.

How every gate is held:

- **FR-021**: Every gate already in the suite that has an opinion about a published capability MUST
  have one about this capability, and MUST accept it with no exemption, no exclusion-list entry and no
  relaxed tool setting (principle III).
- **FR-022**: Any gate this feature adds MUST be paired with a check that plants the violation and
  asserts the gate catches it, and MUST read the workflow through the suite's existing reader rather
  than parsing the YAML a second time.
- **FR-023**: The suite MUST stay offline. No gate added or amended here MUST require a network call or
  a token.
- **FR-024**: Every gate message added or amended here MUST name what was read, what it was compared
  against, and what a maintainer should change.

### Key Entities

- **The capability**: a callable workflow that is the only thing in this library judging what a change
  starts depending on. One input, one permission scope, one composed check name, one handled event.
- **The published third-party action**: the thing that judges. Pinned to a digest, and its defaults are
  the policy — this capability adds no opinion of its own.
- **The published surface record**: the frozen statement of every capability's kind, inputs, permission
  demand, composed check names, tool prerequisites and skips. This is the first capability to arrive
  after it existed, so it is the first time the record is exercised as what a new capability must arrive
  with rather than as a description of what was already there.
- **The caller workflow in this repository**: makes this repository a real consumer at the commit under
  review, rather than a describer of the capability.
- **The committed branch ruleset**: what this repository requires of its own pull requests. It does not
  name this context, and that absence is deliberate.
- **The consumer-facing reference**: the one place a consumer reads a call site, the composed context,
  and what the check will and will not refuse.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full local gate run passes with no network access.
- **SC-002**: A consumer adopts the check with two edits and no third: one copied call site, one granted
  permission. Nothing else in their repository changes, and no value has to be filled in.
- **SC-003**: A pull request adding a dependency version with an advisory at or above the floor fails
  the check; the same pull request with the advisory below the floor, or with no advisory, passes.
- **SC-004**: The capability's permission demand is one scope at read. Raising any scope to write, at
  any block, fails the suite naming the demand and the record it disagrees with.
- **SC-005**: The number of exemptions, exclusion-list entries and relaxed tool settings added to admit
  this capability is zero.
- **SC-006**: Every other capability's check names, input names, permission demands and skip entries are
  byte-identical before and after this change.
- **SC-007**: A maintainer whose run failed because the dependency graph is off learns the setting to
  change from the run's own output, without opening this repository.
- **SC-008**: The composed context appears on this repository's pull requests and is absent from the
  required set of the committed ruleset.

## Assumptions

- **Licences are judged only as far as the published action judges them by default.** The brief fixes
  the interface at one input and puts reinterpreting the action's judgement out of scope, so no licence
  allow-list, deny-list or policy-file input is exposed. With no policy for the action to read, a
  licence finding appears in the run's output and fails nothing — which is why FR-013 makes the
  reference say so rather than repeat the opening promise. Making a licence refusal real is a second
  input and a separate request.
- **The severity floor keeps the published action's own input name and its own default.** Renaming it
  would be this capability holding a second name for a fact the action owns, and choosing a different
  default would be re-ranking a finding, which FR-008 forbids.
- **The dependency-graph failure is named after the fact, not pre-flighted.** A pre-flight would repeat
  the very API call the action makes, so the capability translates the failure it gets rather than
  predicting it. This is the honest thing it can detect, and FR-011 is written to the outcome so the
  plan may reach it another way.
- **This repository's own dependency graph is available.** It is public, so the difference is readable
  here and the caller in FR-018 reports rather than failing permanently.
- **Adding a capability is not a break.** It adds surface without moving any, so a consumer resolving
  the ref they already pin absorbs it by resolving it alone. The version this ships under follows this
  repository's existing versioning rules and is not decided here.
- **No dependency-update automation is in scope.** Proposing upgrades to dependencies a repository
  already has is a separate concern with separate tooling, and lands as its own change.
