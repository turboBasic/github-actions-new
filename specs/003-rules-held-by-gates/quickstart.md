# Quickstart: verifying every gate can fail

A gate that has never been seen to fail is a gate nobody has tested. This is how to see each one fail,
and how to confirm the whole feature holds. Nothing here needs the network or a token — if a step asks
for either, that is the defect.

## Prerequisites

```bash
mise run setup     # tools, dependencies, hooks
```

## The whole thing

```bash
mise run ci        # lint, typecheck, test — what CI runs
```

Expected: green, offline. To prove the offline claim rather than assume it, run it with the network
down; no gate in this feature is exempt, and no gate carries a marker deselecting it.

## Seeing each gate fail

Each row is a one-line edit, `mise run test`, then `git checkout` the file. The point is the message: it
must name what was read, what it was compared against, and the edit to make (FR-021). A failure you have
to open the test to understand is a defect in the gate, not a passing verification.

### The notes configuration

| Edit `cliff.toml` | Expect |
| --- | --- |
| delete a `commit_parsers` entry | FR-001 names the type now reaching no destination |
| swap two `<!--N-->` numbers | FR-002 names the section and its expected position |
| retitle a group, leaving its number | FR-002 names the expected title — and *not* a position change, which is the mechanism working |
| add a seventh group, or a separate breaking-changes section | FR-002 names the expected count; breaking is marked inline on the item |
| widen `tag_pattern` to `^v[0-9]+` | FR-003 names the moving-ref form that must not match |
| delete the `@`-mention postprocessor | FR-005 fails on the rendering, not the shape |
| delete the `<!--N-->`-stripping postprocessor | FR-002 or the rendering fails with the marker visible in the body |
| remove the `is not matching` conditional from the body | FR-004 names the item that references nothing |
| broaden the mention pattern by dropping its leading anchor | FR-005's address half fails — an address broken mid-word |

The last two are the ones that matter most: both leave valid TOML and a body that reads correctly at a
glance, which is why FR-006 renders rather than reads.

### The commit grammar

| Edit | Expect |
| --- | --- |
| add a type to the workflow's `types` default | FR-007 names the types on each side |
| remove one | the same, in the other direction |
| change `CZ_VERSION` to `4.17.0` | FR-008 names both versions and both locations |

To see FR-008 from the other side, bump commitizen in `pyproject.toml`, run `uv lock`, and leave the
workflow alone — which is exactly what an unattended dependency bump does.

### Tooling conventions

| Edit | Expect |
| --- | --- |
| set any `[tools]` entry to `latest` | FR-009 names the entry |
| bump `pipx:specify-cli` without running the re-sync | FR-010 names both versions and the re-sync task |
| change one byte of a vendored file | FR-010 names the file and the re-sync task |

FR-011 cannot be made to fail by editing this tree, because it fails when the outside world changes. To
see it, temporarily point the probe at a linter release that accepts `uses: $/…`; the message must say
to delete both the ignore and TD-001. Its healthy state is verified instead by confirming the probe
draws a verdict at all — see `research.md` R7 for the two exact messages.

### Names

| Edit | Expect |
| --- | --- |
| rename a job to `Python_CI` | FR-012 names the job and that it is half of a consumer's required check |
| drop a workflow's marker | FR-013 names what the name should read |
| give a `workflow_call`-only workflow the self-triggering marker | the same |
| add a `pull_request` trigger to a `workflow_call`-only workflow | FR-013 fails, because its marker is now wrong — the gate reads the trigger set, not a list |

The last row is the one worth doing: it confirms the marker follows the file's actual shape rather than
a table somebody has to remember to edit.

### The timeout partition

| Edit | Expect |
| --- | --- |
| add `timeout-minutes` back to `pr-description` | FR-014 names the capability and the reason a timeout input needs |
| remove it from `python-ci` | FR-015 fails — the partition is asserted in both directions |
| delete a job's literal `timeout-minutes` | the existing schema hook refuses it before the suite runs |

That third row is a reminder that FR-016 leans on a gate that already exists rather than restating it.

### The six pairings

Each pairing fails when its gate's reader stops matching, which an edit to the tree cannot cause — the
reader has to be broken directly. For each, replace the pattern with one matching nothing
(`re.compile(r"$^")`, or an empty marker tuple) and confirm **the pairing** reddens while its gate stays
green. That divergence is the whole point: the gate cannot tell, and the pairing can.

Readers to try it on, from `data-model.md`: `PERMISSION`, `WRITES_A_VERSION`, `GOVERNS_A_CACHE`, the
grammar-job event gate, `blanket_permissions()`, `URL_OWNER_REPO`.

## The completeness check

The feature's own success criterion (SC-002) is that deleting any single gate reddens the suite. To
confirm no gate is redundant with another:

```bash
# for each new test function: comment out its body, run the suite, restore it
mise run test
```

Every one must produce exactly one failure. A gate whose removal changes nothing is a gate to delete
rather than keep, and a gate whose removal reddens *two* tests means two gates hold one fact — which is
principle I inside the suite.

## What is deliberately not verifiable here

- This repository's visibility, and whether a release is owed. Both need GitHub's live state and are out
  of scope; they belong to the work that introduces the marker deselecting network tests.
- Anything about the instruction layers, or that a cited principle number resolves. Out of scope until
  the layering merges with the other tree's.
