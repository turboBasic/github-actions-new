# Research: Every rule held by a gate

Every finding below was verified against the tree or by running a pinned tool, not reasoned from
documentation. Where prior art exists in the repository being consolidated it is cited, because the
gates this feature restores are the ones that lived there.

## R1 — The declared section order is not the rendered one

**Observed**: `commit_parsers` declares its groups in the order `Added, Fixed, Performance, Changed,
Reverted, Documentation`. Rendering over a throwaway repository holding one commit of each type produced
`Added, Changed, Documentation, Fixed, Performance, Reverted` — alphabetical. Tera's `group_by` sorts
groups by their string, so the declaration order expresses an intent the renderer silently discards, and
the visible order is a consequence of the titles.

**Decision**: fix the sections to **the declared order**, which is the shape this tree already means:

| # | Title | From |
| --- | --- | --- |
| 1 | Added | `^feat` |
| 2 | Fixed | `^fix` |
| 3 | Performance | `^perf` |
| 4 | Changed | `^refactor` |
| 5 | Reverted | `^revert` |
| 6 | Documentation | `^docs` |

Six plain groups and no seventh: a breaking change stays in its own type's section and is marked inline
on the item with `— **breaking**`. There is no separate breaking-changes section, and FR-002 fixes that
too — a seventh group appearing is a change to the published shape.

Position is stated by an `<!--N-->` prefix on each group name, which a postprocessor strips again, so the
number is the only statement of position anywhere and a retitle cannot move a section.

**This reorders the rendered output**, which is deliberate: the sections move to the order the
configuration has always declared. **Verified** by rendering the prefixed configuration — the six
sections came out in the table's order, the prefixes were stripped, and a `feat!` commit stayed under
`Added` carrying its inline marker.

**The gate holds a literal committed sequence**, not one derived from the parser declaration order. A
test that read its expectation out of the artefact under test would hold nothing — reordering the parsers
would simply move the sections and the test would follow. The six titles and their numbers are written
out in the test, and that is the point rather than a duplication to tidy away.

**Ceiling**: single-digit numbers sort lexicographically, so this mechanism holds to nine groups. A tenth
would sort `<!--10-->` before `<!--2-->`; zero-pad if that day comes.

**Prior art**: the repository being consolidated used the same mechanism —
`{ pattern = '<!--[0-9]+-->', replace = "" }`.

**Alternative rejected**: numbering the alphabetical order the tree renders today. It holds nothing worth
holding — the assertion and the titles would be the same fact, and it would freeze an accident.

## R2 — The `@`-mention defect and its exact fix

**Observed**: a commit subject `fix: repin call sites to @v5 (#8)` renders as
`- Repin call sites to @v5 (#8)`. GitHub resolves `@v5` in a release body to whoever holds that login,
credits them under Contributors and notifies them. The configuration has no `postprocessors` key at
all.

**Decision**: adopt the pattern the old tree already proved, anchored on a preceding space or bracket so
an address is left alone:

```toml
{ pattern = '(?m)(^|[\s(\[])@([A-Za-z0-9][A-Za-z0-9-]*)', replace = '${1}`@${2}`' }
```

Backticks make the mention inert and read correctly as a ref pin.

**Alternative rejected**: stripping the `@`. It changes what the subject says, and a reader cannot tell
`v5` from a version number.

## R3 — The missing-reference defect and its exact fix

**Observed**: a subject carrying no `(#N)` renders as `- No number here` — traceable to nothing. Subjects
without a number are not hypothetical; they arrive from rebase merges and from hand-edited squash
subjects, and this repository's own current unreleased range already contains one.

**Decision**: append the short commit id only where the subject has no number, using the Tera
conditional the old tree used:

```tera
{% if commit.message is not matching("\(#[0-9]+\)") %} ({{ commit.id | truncate(length=7, end="") }}){% endif %}
```

**Consequence for FR-006**: neither R2 nor R3 can be judged by reading the configuration. A pattern that
has rotted into matching nothing, or into matching everything, leaves valid TOML and a body that reads
correctly to everyone except the person notified. Both are asserted by rendering.

## R4 — Rendering assertions stay offline

**Verified**: the renderer is a pinned tool already in the tool manifest. Invoked as
`<pinned binary> --config <repo config> --unreleased` inside a `tmp_path` git repository, it needs no
tag, no remote, no token and no state from this repository. Two hazards found while confirming this,
both to avoid in the tests:

- `mise exec --cd <dir>` changes the renderer's working directory to that dir, so a test written that
  way renders *this* repository and passes regardless of the planted commits. Invoke the binary by bare
  name and set the subprocess `cwd` instead.
- The renderer discovers a configuration by name. Passing `--config` explicitly is what keeps a
  throwaway directory from picking up anything of its own.

**Verified**: both pinned binaries are already on `PATH` inside `mise run test`, so neither gate needs to
resolve one. What each does need is a `shutil.which` guard, so a suite run outside mise fails naming the
tool and the task to use rather than raising `FileNotFoundError` from inside a subprocess call — the same
courtesy the capabilities owe a consumer about a tool they must pin.

## R5 — The commit tool's shipped type set has a clean accessor

**Verified**: `ConventionalCommitsCz(BaseConfig()).schema_pattern()` returns
`(?s)(build|bump|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\(\S+\))?!?: …`. The first
capture group is the shipped set, and it equals the reusable workflow's `types` default today.

**Decision**: FR-007's gate extracts the alternation from that pattern and compares it to the workflow's
default. Nothing restates the twelve types, so no third copy is created.

**Rejected**: `ConventionalCommitsCz.schema_pattern(ConventionalCommitsCz)` — it happens to work because
the method ignores `self`, and would break the day it stops. Also rejected: a literal list in the test,
which is the third copy the requirement exists to prevent.

## R6 — The commit tool's version, and which two facts are compared

`.github/workflows/conventional-commits.yml` names `CZ_VERSION: "4.18.0"`. `uv.lock` resolves
commitizen `4.18.0`. They agree today by coincidence.

**Decision**: FR-008 compares the workflow's literal against **the lockfile**, read with `tomllib`, not
against the installed interpreter's environment. The lockfile is part of the tree; an installed version
is a property of the machine, and a gate that read it would pass or fail on whether someone had run the
sync. R5's accessor does read the installed tool, which is correct there and safe because this gate
holds the lockfile and the workflow together, and the sync holds the environment to the lockfile — the
chain closes.

## R7 — The silenced linter message can be expired offline

**Verified** with the pinned linter, on a planted probe outside this repository so the committed ignore
does not apply. Both halves still produce the silenced verdict:

| Planted | Verdict | Matches committed ignore |
| --- | --- | --- |
| `uses: $/.github/workflows/target.yml` | `reusable workflow call "$/…" … is not following the format` | `reusable workflow call "\$/` |
| `uses: $/actions/some-action` | `specifying action "$/…" in invalid format because ref is missing` | `specifying action "\$/` |

**Decision**: FR-011's gate plants both probes in `tmp_path`, runs the pinned linter with no
configuration, and asserts each still emits a message the committed ignore pattern matches. The day the
linter accepts the form, the probe exits clean, the gate fails, and its message says to delete the
ignore and TD-001 together. This tests the condition the debt entry already states rather than
comparing version numbers, which would fail a version early or late depending on when the fix landed.

## R8 — The tool manifest already holds; the gate is pure addition

Every `[tools]` entry names a concrete version today. FR-009 is a gate over a rule that is not currently
broken, and refuses three shapes: `latest`, an empty value, and a non-string.

## R9 — Vendored specification machinery: port the existing gate

The old tree's `tests/test_speckit_vendoring.py` (52 lines) holds exactly FR-010, in two parts: the
manifest's recorded version against the `pipx:specify-cli` pin, and every recorded file against its
recorded hash. Both halves are needed — the version catches an unaccompanied pin bump, the hashes catch
a re-sync that skipped a shared path, which the upgrade tool does silently. `.specify/integrations/`
holds the manifests; the pin and the manifests agree at `1.0.4` today.

**Decision**: port it. The failure message must name the re-sync task and must not suggest upgrading
outside the pin.

## R10 — The workflow-name markers come from the tree being consolidated

The old tree's names are `🧩 conventional-commits`, `🧩 python-ci`, `🧩 release` for
`workflow_call`-only workflows and `🌜 ci`, `🌜 commit-messages`, `🌜 release-proposal` for workflows
with triggers of their own. Adopting them keeps a reader moving between the two trees reading one
sidebar.

**Verified safe**: the committed ruleset requires `ci / python-ci`, `commits / pr-title` and
`commits / commit-messages` — every context is composed from job names. No workflow name appears in any
required context, so renaming all twelve breaks no consumer, and the existing context gate is what
confirms that rather than a reviewer.

## R11 — The job-name rule already holds

Every job name and id in the tree is already lowercase-kebab-case. FR-012 is a gate over a rule that is
not currently broken, and it reads names through `capabilities.check_names()` — the same function that
composes what a consumer requires, so the gate and the contract cannot disagree about what a name is.

## R12 — The timeout partition: what actually changes

Four capabilities declare the input. Two keep it under the stated justification:

| Capability | Verdict | Why |
| --- | --- | --- |
| `python-ci` | keeps | runs the caller's own tasks and cannot know how long they take |
| `prek-advisory` | keeps | reads the caller's whole tree and cannot know how large it is |
| `conventional-commits` | loses | judges a title and a range; runtime is its own |
| `pr-description` | loses | renders a body; runtime is its own |

The description said three lose it. Only four declare it and the two keepers are named with reasons, so
the count is a slip and the justifications are authoritative. Recorded in the spec's Assumptions and
reversible.

**What the edit touches**: two workflows lose an input and their jobs gain a fixed `timeout-minutes`;
two rows in the surface fixture lose an entry. The README names no timeout anywhere, so no documentation
follows. This is the whole surface delta — see `contracts/published-surface-delta.md`.

## R13 — Which existing gates lack a pairing

Most of the suite is already self-guarding: a gate compared against a fixture with real content fails
when its reader returns nothing, and a gate asserting a positive count or an index fails the same way.
Six do not, each because the steady state it holds is an empty result:

| Where | What can rot into matching nothing |
| --- | --- |
| `test_workflow_properties.py` | the `PERMISSION` line regex |
| `test_workflow_properties.py` | the `WRITES_A_VERSION` marker tuple |
| `test_workflow_properties.py` | the `GOVERNS_A_CACHE` regex |
| `test_workflow_properties.py` | `test_both_grammar_jobs_pin_the_event_they_can_judge`, which passes vacuously if the job map is empty |
| `test_published_surface.py` | `blanket_permissions()` |
| `test_repo_urls.py` | the `URL_OWNER_REPO` regex — its sibling `USES_SLUG` is paired, this one is not |

FR-019 is bounded at six pairings, each living beside the gate it guards.

## R14 — One accepted risk in FR-001

The renderer's commit parsers are Rust regular expressions; the gate evaluating "does this type reach a
group or a skip" runs them through Python's `re`. The patterns in question are anchored bare
alternations (`^feat`, `^(build|bump|chore|ci|style|test)`), which both engines read identically. Should
a parser ever use a Rust-only construct the gate would misreport, so the gate asserts every one of the
twelve types resolves to exactly one destination — a pattern Python cannot read leaves a type resolving
to none and fails rather than passing quietly.

## R15 — Where each new reader lives

`tests/capabilities.py` is the one owner of how a workflow or an action is read, and FR-020 binds every
new gate that needs one to it. The other artefacts this feature reads — the notes configuration, the
tool manifest, the lockfile, the vendored manifests — are each read by exactly one test module, so each
module reads its own and no shared reader is introduced. A second module needing one of them is the
signal to promote it, not now.

Two additions to `capabilities.py` are warranted, because more than one gate needs them: a job-name
accessor for FR-012 and a trigger-kind accessor for FR-013 — the latter is `is_capability()` plus
"declares nothing else", which FR-013 needs and no existing caller does.
