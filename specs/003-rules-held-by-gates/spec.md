# Feature Specification: Every rule held by a gate

**Feature Branch**: `003-rules-held-by-gates`

**Created**: 2026-09-12

**Status**: Draft

**Input**: User description: "Every rule this repository states about itself is held by a test that reads the tree and needs no network. Today several are stated and held by nothing, so prose is the only thing standing between a rule and its quiet reversal."

## User Scenarios & Testing *(mandatory)*

The reader throughout is a maintainer of this repository, or an automated dependency bot acting on its
behalf. Each story is a class of edit that today lands green and should not.

### User Story 1 - The release notes cannot silently change shape (Priority: P1)

A maintainer edits the release-notes configuration — retitles a section, reorders two, widens the tag
pattern, drops a commit type's destination — and the pull request goes green. The notes are the one
artefact this library publishes, and nothing in the tree reads their configuration, so the first sign
that the shape changed is a published release nobody can un-publish.

Two of the shapes that configuration currently produces are wrong, not merely unguarded. A commit
subject carrying a ref pin such as `@v5` renders into a release body as a live `@`-mention: GitHub
resolves it to whoever holds that login, credits them as a contributor on the release and notifies
them. And an item whose subject carries no pull request number renders with nothing identifying it, so
a reader cannot follow the line back to the change it describes.

**Why this priority**: It is the only story where the current tree is defective rather than only
unguarded, and the defect reaches a person outside this repository — a stranger notified and credited
on a release. A published release cannot be withdrawn (principle V), so every day this stands is a day the
mistake can become permanent.

**Independent Test**: Fixable and verifiable alone. Plant each violation in a throwaway repository, or
in a copy of the configuration, and confirm the suite reddens; then confirm the two rendering defects
produce the corrected output.

**Acceptance Scenarios**:

1. **Given** a commit type the commit grammar admits, **When** the notes configuration places it in no
   section and does not deliberately skip it, **Then** the suite fails, naming the type and both
   destinations available to it.
2. **Given** the notes configuration, **When** a section title is changed, two sections are reordered,
   or a seventh section is introduced, **Then** the suite fails, naming the expected title, position or
   count.
3. **Given** the notes configuration, **When** the tag pattern is widened to match a moving
   compatibility ref, **Then** the suite fails, naming the ref form that must not match.
4. **Given** a commit whose subject reads `ci: repin every call site to @v5 (#20)`, **When** the notes
   are rendered, **Then** the ref pin appears neutralized rather than as a live `@`-mention, and no
   email address elsewhere in a subject is broken mid-word.
5. **Given** a commit whose subject carries no `(#N)`, **When** the notes are rendered, **Then** the
   item carries its commit identifier; **and** an item that already carries `(#N)` is not given a
   second reference.

---

### User Story 2 - One grammar, judged by one binary (Priority: P2)

A maintainer writes a commit message, the local `commit-msg` hook accepts it, and CI rejects it — or
the reverse. Two things allow that today: the set of allowed types is written out in the reusable
grammar workflow independently of the set the commit tool itself ships, and the version of that commit
tool is stated in two places that agree only by coincidence. The workflow names a version literally;
the lockfile resolves one. Nothing holds them equal, so the first dependency bump that moves one and
not the other leaves the local verdict and the CI verdict judging with different binaries — on a
grammar neither of them reports.

**Why this priority**: The failure is confusing rather than destructive, and it wastes a maintainer's
time on every commit until someone notices which of the two spellings moved. It is also the cheapest
class of drift to introduce: a bot does it unattended.

**Independent Test**: Change the literal version in the workflow away from the locked one and confirm
the suite reddens; add a type to one declaration and not the other and confirm the same.

**Acceptance Scenarios**:

1. **Given** the reusable grammar workflow's default type list, **When** it differs in any member from
   the set the pinned commit tool ships, **Then** the suite fails, naming the types on each side.
2. **Given** the version of the commit tool named literally in the workflow, **When** it differs from
   the version the lockfile resolves, **Then** the suite fails, naming both and where each is written.

---

### User Story 3 - A tooling convention is held (Priority: P2)

Three conventions this repository states about its own tooling are held by prose alone:

- No tool version floats, so two machines on one commit resolve the same linters. A single `latest`
  entry undoes that for every machine at once and reads as a normal line in review.
- The vendored specification machinery matches the version pinned for the tool that vendors it. A bot
  can bump the pin but cannot run the re-sync, so between that merge and someone remembering, the
  tree's manifests describe a version nothing pins and ship an older version's files.
- The one silenced linter message exists only because two tools contradict each other about the same
  syntax. When the stale tool ships a fix, the silence has outlived its reason and nothing says so.

**Why this priority**: Each is a slow leak rather than a break, but the first two make a green local
run stop meaning anything, which is what the whole gate layer rests on.

**Independent Test**: Each is verifiable by editing the artefact it reads — set an entry to `latest`,
bump the pin without re-syncing, pretend the stale tool has shipped its fix.

**Acceptance Scenarios**:

1. **Given** the tool manifest, **When** any entry names `latest` or names no version at all, **Then**
   the suite fails, naming the entry.
2. **Given** the vendored specification manifests, **When** the version they record differs from the
   pinned version of the tool that vendors them, **Then** the suite fails, naming both and the re-sync
   task to run.
3. **Given** the vendored specification manifests, **When** any file they record is missing or no
   longer matches its recorded hash, **Then** the suite fails, naming the files and the re-sync task.
4. **Given** the silenced linter message and the reason recorded for it, **When** the tool whose
   verdict is silenced no longer produces that verdict, **Then** the suite fails, saying the ignore and
   its debt entry are now to be deleted.

---

### User Story 4 - A name that carries weight outside is held (Priority: P3)

Two naming rules carry weight outside this repository and neither is held.

A job name is half of the identifier a consumer types into a ruleset as a required check. A name that
departs from lowercase-kebab-case is a name every consumer has to copy exactly, oddities and all, and a
later tidy-up of it silently retires a required check in every consumer at once.

A workflow name is what a reader sees in the Actions sidebar. A workflow whose only trigger is a call
from elsewhere never has a run of its own, so its sidebar entry is permanently empty; a workflow with
triggers of its own does have a history. Today nothing distinguishes them, so a reader cannot tell an
empty entry from a broken one. The rule is that a name is a marker for its kind followed by its
filename stem — which also removes any drift between a workflow's name and its file.

**Why this priority**: The job-name rule holds today and only needs a gate — the value is preventing a
future rename, not fixing a present one. The workflow-name rule needs every name changed, but nothing
outside this repository reads a workflow name, so the change is safe to make in one pass.

**Independent Test**: Rename a job to `Python_CI` and confirm the suite reddens; give a workflow the
wrong marker for its trigger set, or a stem that is not its filename, and confirm the same.

**Acceptance Scenarios**:

1. **Given** every job in every workflow, **When** a job's name is not lowercase-kebab-case, **Then**
   the suite fails, naming the job, its workflow and that it composes a consumer's required check.
2. **Given** a workflow whose only trigger is `workflow_call`, **When** its name is not the reusable
   marker followed by its filename stem, **Then** the suite fails, naming what the name should read.
3. **Given** a workflow with triggers of its own, **When** its name is not the self-triggering marker
   followed by its filename stem, **Then** the suite fails, naming what the name should read.

---

### User Story 5 - A timeout input only where it is earned (Priority: P3)

An input is worth its place only where the caller can know something the callee cannot. A timeout is
that where the runtime is a function of the caller's tree: one capability runs the caller's own tasks
and cannot know how long they take, and one reads the caller's whole tree and cannot know how large it
is. The others expose a timeout without that justification — a knob nobody has a reason to turn, on a
published surface where every knob is a promise.

The partition has to become real before it can be asserted: a gate describing a division the tree does
not have is a gate that cannot pass. So the unjustified exposures go in this same change, and the
partition is then held by a test rather than by review, so a future capability cannot widen it quietly.

**Why this priority**: It is the only story that changes the published surface, which makes it the one
with a release consequence rather than only a suite consequence. It is last because nothing is
currently wrong for a consumer — the inputs work; they merely should not exist.

**Independent Test**: Add the input back to a capability that is not in the justified set and confirm
the suite reddens; remove it from one that is and confirm the same.

**Acceptance Scenarios**:

1. **Given** the published capabilities, **When** one outside the justified set declares a timeout
   input, **Then** the suite fails, naming the capability and the reason a timeout input needs.
2. **Given** the published capabilities, **When** one inside the justified set stops declaring a
   timeout input, **Then** the suite fails, so the justification and the tree cannot part company in
   either direction.
3. **Given** a capability that no longer takes the input, **When** it runs, **Then** its jobs still
   carry a fixed timeout, because a job with no timeout at all is what the existing schema gate
   refuses.
4. **Given** the two capabilities whose surface loses an input, **When** the change is released,
   **Then** it is released as a break under this repository's own versioning rules, because a caller
   passing the removed input fails the run.

---

### User Story 6 - No gate can rot into passing (Priority: P1)

A gate whose pattern has stopped matching anything is worse than no gate. It reports green, and a green
check is not investigated. So every gate is paired with a test that plants a violation and asserts the
gate catches it — the paired test is what makes silent rot impossible. This applies to gates already in
the tree that lack the pairing, not only to the gates this feature adds.

Gates also read a workflow or an action through the module that already owns how one is read. A second
reader is a second answer to what a workflow says, and the two answers drift the way any two copies of
a fact drift.

**Why this priority**: It is the property that makes every other story worth doing. A gate added
without it is a rule that will be un-held again without anybody seeing it happen.

**Independent Test**: For any gate, delete the rule's enforcement and confirm the suite reddens; then
break the gate's own reader and confirm the paired test reddens.

**Acceptance Scenarios**:

1. **Given** any gate this feature adds, **When** the rule it holds is broken, **Then** exactly that
   gate fails, and its message names what was read, what it was compared against, and what to change.
2. **Given** any gate this feature adds, **When** its reader or pattern is made to match nothing,
   **Then** its paired test fails.
3. **Given** the gates already in the tree that have no paired test, **When** this feature lands,
   **Then** each has one.
4. **Given** any gate that needs to know what a workflow or action says, **When** it reads one, **Then**
   it reads it through the existing single reader rather than parsing the file again.

---

### Edge Cases

- A commit type is added to the grammar but given no destination in the notes configuration — the
  type-coverage gate must fail rather than the notes silently dropping commits of that type.
- The notes configuration is valid but its pattern for neutralizing a ref pin matches nothing, or
  matches too much. Reading the configuration cannot tell the difference, so these are judged by
  rendering rather than by shape.
- A commit subject contains an email address. Neutralizing `@`-mentions must not break it mid-word.
- The commit tool's shipped type set changes between versions. The gate compares against the pinned
  version, so the bump and the declaration move together or the gate fails.
- The silenced linter message's own gate becomes the thing that fails when the upstream fix ships. That
  failure is the signal to delete both the ignore and its debt entry, and its message says so — a
  failure whose fix is a deletion still has to name the deletion.
- A workflow gains a second trigger alongside `workflow_call`. It stops being a pure reusable workflow,
  so its marker changes; the gate reads the trigger set rather than a list of names.
- A required check's context is composed from job names, not workflow names, so renaming every workflow
  changes no context. The existing context gate is what confirms that rather than a reviewer.

## Requirements *(mandatory)*

### Functional Requirements

Release notes:

- **FR-001**: Every commit type the commit grammar admits MUST be placed in a section by the notes
  configuration or deliberately skipped by it, and a type in neither state MUST fail the suite.
- **FR-002**: The sections MUST be fixed by a test to exactly six, titled and ordered
  `Added, Fixed, Performance, Changed, Reverted, Documentation`, so a retitle, a reorder, an added
  section or a removed one fails rather than shipping. A breaking change carries an inline marker on its
  own item and keeps its type's section; a seventh section for breaking changes is a change to the
  published shape and MUST fail.
- **FR-003**: The tag pattern MUST match exact version tags and MUST NOT match a moving compatibility
  ref, and a test MUST hold both halves.
- **FR-004**: A rendered item MUST carry a reference a reader can follow back to a commit: the pull
  request number where the subject has one, and the commit identifier where it does not. An item MUST
  NOT carry two references.
- **FR-005**: A ref pin appearing in a commit subject MUST NOT render as a live `@`-mention, and the
  neutralization MUST NOT alter text that merely contains an `@` inside a word, such as an email
  address.
- **FR-006**: FR-004 and FR-005 MUST be verified by rendering the notes, not by reading the
  configuration, because a pattern that has stopped matching leaves the configuration valid.

Commit grammar:

- **FR-007**: The set of commit types the grammar admits MUST be declared once and MUST equal the set
  the pinned commit tool ships, so a message the local hook accepts cannot fail in CI.
- **FR-008**: The version of the commit tool MUST be one fact: the version named in the workflow and
  the version the lockfile resolves MUST be held equal by a test that names both locations.

Tooling conventions:

- **FR-009**: Every entry in the tool manifest MUST name a concrete version; a test MUST fail on
  `latest` or on an entry with no version.
- **FR-010**: The vendored specification machinery MUST record the same version as the pin for the tool
  that vendors it, and every file it records MUST match its recorded hash. A failure MUST name the
  re-sync task to run and MUST NOT suggest upgrading the tool outside the pin.
- **FR-011**: The one silenced linter message MUST expire: when the tool whose verdict is silenced stops
  producing it, the suite MUST fail and MUST say that the ignore and its technical-debt entry are now
  to be deleted.

Names:

- **FR-012**: Every job name in every workflow MUST be lowercase-kebab-case, and the failure MUST say
  that the name is half of a consumer's required check context.
- **FR-013**: Every workflow name MUST be a marker followed by the workflow's filename stem. The marker
  MUST distinguish a workflow whose only trigger is `workflow_call` from one that has triggers of its
  own, and the gate MUST choose the expected marker by reading the trigger set.

Timeout partition:

- **FR-014**: A timeout input MUST be declared only by the capabilities whose runtime is a function of
  the caller's tree — the one that runs the caller's tasks and the one that reads the caller's whole
  tree — and MUST be removed from every other capability in this change.
- **FR-015**: The partition MUST be asserted in both directions: a capability outside the set declaring
  the input fails, and a capability inside the set no longer declaring it fails.
- **FR-016**: Every job in a capability that loses the input MUST retain a fixed timeout, so the
  existing requirement that no job runs without one continues to hold.
- **FR-017**: The published surface record MUST be updated to match the reduced input sets, and the
  removal MUST be treated as a break under this repository's versioning rules.

How every gate is built:

- **FR-018**: Every gate this feature adds MUST be paired with a test that plants a violation and
  asserts the gate catches it.
- **FR-019**: Every gate already in the tree that lacks such a pairing MUST gain one.
- **FR-020**: Every gate that needs to know what a workflow or an action says MUST read it through the
  existing single reader for workflows and actions, and MUST NOT parse the YAML a second time.
- **FR-021**: Every gate MUST fail with a message naming what was read, what it was compared against,
  and what a maintainer should change. An assertion with no message is not a result.
- **FR-022**: The whole suite MUST run offline. No gate this feature adds may require a network call or
  a token.

### Key Entities

- **Notes configuration**: the shape of the one artefact this library publishes — which commit types
  reach the notes, under which section titles, in which order, from which tag range, and how a
  rendered line references its commit.
- **Commit grammar declaration**: the set of allowed commit types, plus the pinned version of the tool
  that judges a message against them. Read by the local hook and by the reusable grammar workflow, and
  the two must reach the same verdict.
- **Tool manifest**: the single record of every tool version this repository resolves, including the
  pin for the tool that vendors the specification machinery.
- **Vendored specification manifests**: per-integration records of a vendored version and the hash of
  every file vendored at it.
- **Published surface record**: the frozen statement of every capability's kind, input names,
  permission demand and composed check names. Changes here are what a release is judged against.
- **Workflow and action reader**: the single module that answers what a workflow or action says. Every
  gate consults it rather than parsing YAML.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every rule listed in this specification has at least one test that fails when the rule is
  broken, and a second test proving the first can fail.
- **SC-002**: Deleting any single gate added by this feature reddens the suite — no gate is redundant
  with another, and none can be removed unnoticed.
- **SC-003**: The full local verification passes with no network access and no token available.
- **SC-004**: A commit subject containing a ref pin produces a release body that mentions nobody, and
  every rendered item can be traced to exactly one commit.
- **SC-005**: A maintainer whose commit message the local hook accepts is never rejected by CI for its
  grammar, and the reverse, because both judge with one type set and one tool version.
- **SC-006**: Every gate failure message is actionable without opening the test: it names the artefact
  read, the expected value, and the edit to make.
- **SC-007**: No gate reads a workflow or action except through the single existing reader — a count of
  independent YAML parsers over the workflow tree that is one.
- **SC-008**: Every capability's declared timeout input is accounted for by the stated justification,
  in both directions, with no exceptions recorded.

## Out of Scope

- **Anything that reaches the network.** The suite stays offline and local verification must not need a
  token. Gates asserting GitHub's own live state — this repository's visibility, whether a release is
  owed — belong to their own work, which introduces the marker that deselects them.
- **Every gate over the instruction layer itself**, and the gate that a cited principle number
  resolves. Those hold a layering whose content is about to be merged with another repository's, and
  the layering document is explicit that its checks come last: written against an uncleaned tree they
  fail on work in progress, written against a cleaned one they hold the cleaning in place. They belong
  to the change that does the merging. Building an owned-facts table now would mean building it against
  an artefact set half of which does not yet exist.
- Adding or removing a capability, changing any capability's behaviour, and every input change other
  than the timeout partition in FR-014.
- Linter and hook coverage that is not a test. A missing schema hook or an unpinned shell linter is a
  pull request of its own.
- The version line, the repository's identity and the consumer contract, all already ruled on in the
  decision records.

## Assumptions

- **Two capabilities keep the timeout input, so two lose it.** The description says three lose it, but
  it also names the two that keep it and why, and only four capabilities declare the input today. The
  two named justifications are taken as authoritative and the arithmetic as a slip; the removals are
  the other two. If three were meant, one of the named keepers loses it and the partition changes.
- **The markers for workflow names are the ones the repository being consolidated already used**: one
  glyph for a workflow whose only trigger is a call, another for a workflow with triggers of its own.
  The description names the rule but not the glyphs, and adopting the existing convention keeps a
  reader moving between the two trees reading one sidebar.
- **Renaming every workflow breaks no consumer.** A required check context is composed from job names,
  not workflow names, and the existing context gate is what confirms this rather than a reviewer.
- **Removing a published input is a break.** A caller passing an input the callee no longer declares
  fails the whole run before any job exists, so FR-014 starts a new compatibility line under this
  repository's own rules rather than shipping as a fix.
- **The two rendering assertions may run a local binary.** The renderer is already a pinned tool, and
  rendering into a throwaway repository needs no network, no tag and no state from this one — so this
  does not breach the offline rule.
- **The commit tool's shipped type set is read from the pinned installation** rather than restated in a
  test, since restating it would create the third copy the requirement exists to prevent.
- **The silenced linter message's expiry is judged by the tool's own behaviour**, which is what the
  recorded debt condition already names, rather than by comparing version numbers.
- Which existing gates lack a paired test is settled during planning by reading the suite, not asserted
  here.
