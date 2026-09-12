# Research: one check over what a change starts depending on

Every unknown the brief left open, answered from the published action's own source at the digest this
feature pins rather than from its documentation. Where the answer contradicts the spec, that is said
here and the requirement it affects is named.

## The published action

**Decision**: `actions/dependency-review-action`, pinned to
`a1d282b36b6f3519aa1f3fc636f609c47dddb294` — `v5.0.0`, the current release.

**Rationale**: It is GitHub's own action for exactly this comparison, and the only one that reads the
dependency-graph difference from the API rather than from a checked-out tree. FR-002's "no checkout"
follows from the action's design rather than being imposed on it.

**Alternatives considered**: A capability calling the comparison API itself. Rejected — it would be
this repository holding a second opinion about severity ranking and licence policy, which FR-008
forbids, and there is no third judgement to make.

## What the action reads and what it demands

| Question | Answer, read from the source at the pinned digest |
| --- | --- |
| Permission | `contents: read`. Every call site in the action's own README grants that and nothing else |
| Token | `repo-token` defaults to `${{ github.token }}`, so no input names it and no secret is passed |
| Refs | `base-ref` and `head-ref` default from the `pull_request` payload; nothing is read from a tree |
| Runtime | one API comparison and one summary render, so it is not a function of the caller's tree — FR-005 |

The permission is what makes the capability adoptable in one grant (Story 2). Nothing about the fork
case needs handling: the difference is read with the run's own read-scoped token and no fork content is
fetched or executed.

## The severity floor

**Decision**: declare one input, `fail-on-severity`, `type: string`, `default: low`.

**Rationale**: `low` is the action's own default — its `action.yml` deliberately declares no default so
that a configuration file cannot be overwritten, and the value lives in the action's schema as
`SeveritySchema = z.enum(SEVERITIES).default('low')`. Keeping the action's name and the action's value
is what makes FR-008 true rather than merely stated; a different default would be re-ranking a finding
and a different name would be a second owner of a fact the action owns.

**Consequence the reference has to carry**: at the default floor nothing is below the floor, because
`low` is the lowest severity there is. Scenario 1.4 — a finding that informs rather than fails — is
reachable only once a consumer raises the floor. The README says which way the input moves and what it
buys, instead of implying the default already sorts findings into two piles.

## Licences: the half of the opening promise that does not hold

**Finding**: `license_check` defaults to `true`, so the licence pass runs with no policy configured —
but of the three verdicts it can reach, only one is reachable without one.
`getInvalidLicenseChanges` classifies each change into `forbidden`, `unresolved` and `unlicensed`, and
with `allow` and `deny` both undefined the first two are unreachable: every branch that fills them is
guarded on one list or the other, and `forbidden` needs a cache entry only a policy comparison sets.
`unlicensed` is filled regardless — a dependency whose licence resolves to `NOASSERTION` or to nothing
at all.

Then in `printLicensesBlock`, `forbidden` and `unresolved` each call `core.setFailed`, while
`unlicensed` reaches `printNullLicenses` alone and never sets `issueFound`. So a licence finding
without a policy is real, appears in the log and the job summary, and **fails nothing** — exactly the
spec's edge case, and the reason FR-013 asks the reference to separate the two lists rather than to
deny the first one exists.

What no policy buys is the *refusal*: a licence this project will not accept cannot be named, so it
cannot be blocked. That is the half of the opening promise that does not hold, and it is narrower than
"no licence is judged". The README says an unlicensed dependency is reported and not refused, and that
refusing a named licence is a second input.

## What else only reports

`show-openssf-scorecard` defaults to true and `warn-on-openssf-scorecard-level` to `3` — declared with
no default in `action.yml` and defaulted in the schema, as `fail-on-severity` is, and spelled
`show_openssf_scorecard` and `warn_on_openssf_scorecard_level` there. A dependency with a low OpenSSF
Scorecard score produces a warning annotation and a summary row and fails nothing. FR-013 asks the
reference to separate what reddens the check from what only appears in the output; this belongs on the
second list beside sub-floor advisories and unlicensed dependencies, or the list is incomplete and a
consumer reads a warning as a refusal that did not happen.

## Naming the dependency-graph failure

**Decision**: the action's own message carries two of the three clauses FR-011 demands. On a 403 it
emits `Dependency review is not supported on this repository. Please ensure that Dependency graph is
enabled, see <server>/<owner>/<repo>/settings/security_analysis` — the setting and where to change it.
It cannot know the third clause, that a called workflow cannot change its caller's repository settings.
So the capability adds one step that says it.

**How the step knows**: `dependency-changes` is set only after the comparison has been read. A 403 or a
404 throws before it, so the output is never set. A run that failed with that output empty is a run
that judged nothing, and that is the honest discriminator — read from the action's own behaviour rather
than from a message string that upstream may reword.

```yaml
- if: failure() && steps.review.outputs.dependency-changes == ''
```

**Alternatives considered**:

- **Pre-flighting the API.** Rejected by the spec's own assumption, and it would repeat the very call
  the action makes.
- **Annotating on any failure.** Rejected: it would tell a maintainer to check a repository setting
  when what actually happened is that an advisory was found, which is worse than saying nothing.
- **Matching the action's message text.** Rejected: it pins this repository to a string upstream owns,
  and the failure mode is silence.

The step interpolates nothing. `$GITHUB_SERVER_URL` and `$GITHUB_REPOSITORY` are set by the runner, so
principle VI holds structurally rather than by review.

## Naming, so the composed context reads

**Decision**: capability `dependency-review.yml`, job `dependency-review`; caller
`dependency-guard.yml`, job `guard`. The composed context is `guard / dependency-review`.

**Rationale**: FR-009 fixes the workflow name as its marker and its stem, and FR-019 wants the two
halves of the context to repeat no word. `guard` names the caller's role, the way `ci`, `commits`,
`describe` and `advisory` already do, and shares nothing with `dependency` or `review`.

**Alternatives considered**: `deps / dependency-review` reads as a stutter even though the words
differ. Adding the job to the existing `advisory.yml` would have been one file fewer, but that file
means "reports and never fails" — `prek-advisory` is registered `judges = false` — and this capability
does judge. One caller per capability is the pattern already in the tree.

## FR-019 is a choice here, not a gate anywhere

A gate asserting no composed context repeats a word across its halves would fail on `ci / python-ci`,
which is shipped, required, and cannot be renamed without blocking every pull request that requires it
(principle IV). So FR-019 is held by the name chosen in this change and by review, and no gate is added
for it. Said here because the alternative reading — add the gate, then exempt the existing context — is
principle III's exclusion list arriving by the back door.

## Two things the spec does not name that this change owes

- **`[tool.turbobasic-release].exclude` gains the new caller.** That list is where this repository says
  which of its workflows are its own call sites rather than consumer surface; seven are already there.
  Omitting the eighth would make a later edit to it count towards a break. This is not a loosened gate:
  it is the same statement, for the same reason, as the seven beside it.
- **The README's "Five reusable GitHub Actions workflows" is deleted rather than corrected to six.** A
  count in prose over a list of sections is a second owner of a fact the sections already hold
  (principle I), and it has to be edited by hand every time a capability lands. Deleting it satisfies
  FR-016 with nothing left to drift and no gate to add.

## What this change does not owe

**No decision record.** The conventions layer sends versioning, permissions policy and pinning rules to
a record first. This feature decides none of them: it applies the pinning rule the tree already holds,
demands the permission scope four capabilities already demand, and leaves the version to the release
path. Nothing here is expensive to reverse.

**No technical-debt row.** The licence gap is a scope decision the spec records as an assumption and the
README states as a limit, and the debt ledger takes only what nobody is going to do. A licence policy
input is a separate request, which is an issue if anyone wants it.
