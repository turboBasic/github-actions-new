# Implementation Plan: The Consumer Contract

**Branch**: `001-consumer-contract` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-consumer-contract/spec.md`

## Summary

Ship the five published capabilities the specification defines — Python CI, commit grammar,
pull-request body, releasing, advisory whole-tree lint — plus the internal release decision unit they
depend on. Nothing exists yet: this repository currently ships its own CI and its instruction layers and
no `workflow_call` trigger anywhere, so every capability is greenfield rather than ported.

The approach the research settled on: this repository is its own first consumer. Its CI calls each
capability with `$/`, which resolves at the commit under review, so a defect fails the pull request that
introduces it. Everything decidable is decided in a callable Python unit rather than a `run:` block, so
it can be unit-tested offline; everything left in YAML is asserted as a property of the YAML. Two new
gates carry the two new principles that a diff cannot otherwise reveal: a committed surface fixture for
principle IV, and an event-skip table with asserted reasons for principle VII.

## Technical Context

**Language/Version**: Python 3.14 (the decision unit and the whole test suite); YAML for workflows and
actions; `bash` inside `run:` blocks, kept as thin as the decision boundary allows

**Primary Dependencies**: none at runtime — `[project].dependencies` stays empty, nothing is published.
Dev: pytest, pyright, ruff, yamllint, check-jsonschema, commitizen. Gates: actionlint, zizmor, cspell,
markdownlint-cli2, taplo, prek. Consumer-side tools (package manager, hook runner, notes renderer) are
the *consumer's* to pin and are pre-flighted, not provisioned

**Storage**: N/A. The one persistent artefact is the committed surface fixture, read by a test

**Testing**: pytest, offline, no marked exceptions needed. pyright strict

**Target Platform**: GitHub Actions, `ubuntu-latest` runners

**Project Type**: reusable CI component library. No application, no build, no publish — the ref is the
artifact

**Performance Goals**: none beyond the per-capability job timeouts the contract fixes. Not a
latency-sensitive domain

**Constraints**: `mise run ci` must never need the network. No secret written anywhere, ever. Third-party
actions SHA-pinned, with exactly one named self-reference exception (R2). Every workflow declares a
timeout. This repository is `github-actions-new` on GitHub while every internal name is already
`github-actions`, so a self-reference by slug would need updating on rename — `$/` avoids that for
workflows, and `test_repo_urls.py` already gates the rest

**Scale/Scope**: 5 published capabilities + 1 internal unit; 4 known consumer repositories, of which 2
must repin from a superseded major and 1 is deliberately out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Seven principles. Each gets a gate that can fail, or a statement of why it cannot be violated here.

| Principle | Gate | Pre-design | Post-design |
| --- | --- | --- | --- |
| I. One Owner Per Fact | No input's default is stated twice. The capability YAML owns inputs, defaults, permissions and check names; `README.md` carries a call site and prose only (R4). The `0.x` boundary has one statement, asserted | ⚠️ at risk | ✅ resolved |
| II. Secrets Never Persist | A test asserts no `secrets.*` reference reaches a `run:` body, a file, or an artifact — only `with:`/`env:` of the token-minting step. Release writes use a narrowed App installation token | ✅ | ✅ |
| III. Gates Are Never Loosened | No new suppression, no relaxed mode. Every existing lint entry keeps running, and each new config file gets a `check-jsonschema` hook and a `lint` task line | ✅ | ✅ |
| IV. What A Consumer Cannot Absorb Needs A New Line | Committed surface fixture vs. the tree: capability names, composed check names, input names, permission demands. A rename or an added permission becomes a deliberate diff instead of a silent one-word edit (R5) | ⚠️ no gate existed | ✅ designed |
| V. A Published Ref Cannot Be Withdrawn | Unit tests over the refusal ladder and the increment, including below `1.0.0`; an ordering assertion that no ref-creating step precedes any refusal; a totality test that the moving ref is never empty (R3) | ⚠️ no gate existed | ✅ designed |
| VI. Caller-Controlled Text Never Reaches A Command Line | A test over every `run:` block for `${{ }}` interpolation of event, input or commit-derived values, plus `zizmor --pedantic`. Values arrive through `env:` | ✅ | ✅ |
| VII. A Required Gate Never Passes Without Judging | Every event-conditional job `if:` appears in a table with a non-empty reason, asserted. Advisory checks are exempt by name, which is why the principle was written to exempt them | ⚠️ no gate existed | ✅ designed |

**Pre-design verdict**: PASS, with three principles holding no gate and one at risk. All four are met by
Phase 1 and none required a principle to bend.

**Post-design verdict**: PASS. Principle I's risk was the input tables — the old repository carried
defaults in both its README and its YAML, and the specification found four places where the two had
drifted into shipping a false promise. Resolved by removing the fork rather than policing it (R4), which
is why no "assert the docs match the YAML" gate appears above: that would have made drift detectable
instead of impossible.

No violation needs justifying, so *Complexity Tracking* is empty and omitted.

## Project Structure

### Documentation (this feature)

```text
specs/001-consumer-contract/
├── plan.md                          # This file
├── spec.md                          # The contract, and the rulings behind it
├── research.md                      # Phase 0 — five unknowns resolved, two findings raised
├── data-model.md                    # Phase 1 — surface records and release decision values
├── quickstart.md                    # Phase 1 — how to validate, at three scopes
├── contracts/
│   └── published-surface.md         # Phase 1 — the interface, as promises
├── checklists/
│   └── requirements.md              # Spec quality, 16/16
└── tasks.md                         # Phase 2 — /speckit-tasks, not created here
```

### Source Code (repository root)

```text
.github/workflows/
├── python-ci.yml                    # capability: workflow_call, composes `python-ci`
├── conventional-commits.yml         # capability: composes `pr-title` + `commit-messages`
├── pr-description.yml               # capability: composes `pr-description`
├── prek-advisory.yml                # capability: composes `prek-advisory`
├── release.yml                      # capability: workflow_call only, composes `tag-and-publish`
│
│   # …and this repository's own callers of them, each via `$/`, so a defect in a
│   # capability fails the pull request that introduces it:
├── ci.yml                           # exists — becomes a caller of `python-ci.yml`
├── commit-messages.yml              # calls `conventional-commits.yml`
├── describe-pr.yml                  # calls `pr-description.yml`, on `opened` only
├── advisory.yml                     # calls `prek-advisory.yml`
├── release-on-merge.yml             # verify, then call `release.yml`
└── release-proposal.yml             # own path; App token, never GITHUB_TOKEN

actions/release-decisions/
├── action.yml                       # internal unit; the one permitted self-reference target
└── decisions.py                     # pure, standard-library-only, no network

tests/
├── test_instruction_layers.py       # exists
├── test_repo_urls.py                # exists
├── test_published_surface.py        # principle IV gate, reads the fixture below
├── published_surface.toml           # the committed fixture
├── test_release_decisions.py        # the refusal ladder, the increment, the 0.x boundary
├── test_workflow_properties.py      # check names, triggers, timeouts, event-skip reasons
├── test_action_pins.py              # SHA pinning, and the single named exception
└── test_no_interpolation.py         # principle VI over every `run:` block

README.md                            # gains one copyable call site per capability; no input tables
docs/decisions/                      # a record only if a ruling clears the ADR bar
```

**Structure Decision**: Capabilities live in `.github/workflows/` because that is the only place GitHub
resolves a `workflow_call` from, and the one action lives in `actions/release-decisions/` because a
composite action cannot live under `.github/workflows/`. The layout is forced, not chosen.

Two consequences worth naming. First, `actionlint` does not look outside `.github/workflows/`, so
`zizmor` is what covers the action tree — the `lint` task must reach both, and adding the `actions/`
tree is a change to that task, not something inherited. Second, this repository's own callers are
separate workflows from the capabilities they call, so a refused release reddens the release workflow
rather than the one that answers for the code.

## Phasing

Four phases, ordered so each ends with a tree that is green and a capability that is real. The surface
fixture arrives with the first capability, not after the last, or it codifies whatever was built.

| Phase | Delivers | Why here |
| --- | --- | --- |
| 1 | The two gates that carry the new principles: the surface fixture and its test, the interpolation test, the pin test. Plus `README.md` restructured to hold call sites and no input tables | The gates exist before the thing they gate, so the first capability is born checked. Principle I's resolution lands before any input table can be written |
| 2 | `python-ci.yml` and `conventional-commits.yml`, each called by this repository's own CI via `$/`. The tool pre-flight | The two P1 capabilities, three consumers between them. Proves the dogfooding mechanism on the simplest surface |
| 3 | The release decision unit and `release.yml`, `release-on-merge.yml`, `release-proposal.yml`. Every refusal unit-tested including below `1.0.0` | Highest-risk, and the only irreversible one. Needs phase 1's gates and phase 2's CI to gate its own release |
| 4 | `pr-description.yml` and `prek-advisory.yml` | Both P2/P3, and both reshaped by rulings, so they benefit from the pattern the earlier phases settle |

Phase 3 is where principle V is either held or lost, and it is the phase to slow down in: a wrong tag
cannot be withdrawn. Nothing in phase 3 ships without a dry run first.

## Open decisions carried into implementation

Two, both from research, both changing published surface — so both are the specification's to settle
rather than the plan's. Neither blocks phase 1.

**Both are now settled, and neither was carried as far as the phase that held it.** The rulings are in
`spec.md` under *Rulings*: F1 cuts the action form, F2 deletes the input. Read the two entries below as
the questions, not as anything still open.

- **F1 — cut the advisory lint's composite-action form?** FR-049 publishes it as both a workflow and an
  action. No consumer has used the action form, and its existence is the only thing forcing the callable
  workflow to hold a moving self-reference. Cutting it makes that exception vanish. This decides whether
  `actions/` holds one directory or two, so it wants settling before phase 4.
- **F2 — keep `mise-version`?** Two capabilities declare it, no consumer sets it. Surface carried by
  inheritance. Harmless, and cheaper to drop now than after a consumer pins it.

OQ-011 is closed by R3 and needs nothing further: the guard was dead, and its intent becomes a totality
test rather than a branch.
