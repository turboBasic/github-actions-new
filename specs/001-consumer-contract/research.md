# Phase 0 Research: The Consumer Contract

**Date**: 2026-09-07 | **Feature**: [spec.md](./spec.md)

Five unknowns blocked the design. Each is resolved below; none needed the old repository's tests.

## R1 — How a workflow reaches something in its own repository

**Decision**: This repository's own workflows call its capabilities with `$/.github/workflows/<file>`.
Its CI is therefore a real consumer, exercising each capability at the commit under review.

**Rationale**: GitHub supports two same-repository forms in `uses:` — `$/.github/workflows/x.yml` and
`./.github/workflows/x.yml`. Both resolve to the *caller's own commit*, so a defect introduced in a
capability fails the pull request that introduces it rather than reaching a consumer first. `$/` is the
documented preference and must carry no `@ref` suffix. Neither form names the repository, so neither is
affected by this repository's pending rename.

**Alternatives considered**: pinning a tag (`@v1`) in our own CI — rejected, it tests the last release
rather than the change; `workflow_run` — rejected, it is a high-severity dangerous trigger and its
branch filter matches a fork branch of the same name.

**Consequence**: a capability under review is verified by the same mechanism a consumer uses, so no
separate harness is needed for workflow-level behaviour.

## R2 — What a reusable workflow cannot reach, and the one exception it forces

**Decision**: One self-reference by owner/repo and moving ref is permitted, for the internal release
decision unit only. Every other capability does its work inline, and the advisory lint's
composite-action form is **not** carried forward (see *Findings* below).

**Rationale**: A reusable workflow runs `actions/checkout` against the *caller's* tree, so nothing of
ours is on disk and `./`-relative paths resolve into the consumer's repository. Anything a reusable
workflow needs from our tree must therefore be named by owner, repository and ref — and a reusable
workflow cannot interpolate its own ref, so that ref is a literal. This is structural, not a
preference: no arrangement of checkouts removes it, because the workflow cannot learn which of its own
refs the consumer pinned.

The cost is contained by having exactly one such reference instead of two. The release decision unit
earns it: its logic must be callable and unit-testable offline, which embedding Python in a `run:`
block would forfeit. It is also internal surface, so its ref moving is not a consumer-visible change.

**Alternatives considered**: checking our repository out at a path inside the reusable workflow —
rejected, it needs the same unknowable ref; embedding the decision logic in shell — rejected, it
forfeits offline unit tests, which is the whole reason the unit exists.

## R3 — OQ-011, the apparently unreachable release guard

**Decision**: The guard is dead code and is **not** carried forward. Its intent is met by construction,
plus one test.

**Rationale**: Read from the YAML and the module alone, the release workflow fails when the decision
unit reports no compatibility ref to move. That state cannot arise. The ref name is derived from a
parsed version and always has at least one component, so it is never empty for any version. And on the
failing path the decision unit exits before writing any output, which leaves the `proceed` gate unset,
which skips the tagging step — so the guard cannot be reached from there either.

Carrying a branch forward because its ancestor had one is how cement becomes a requirement. Instead:
the ref name is total over every version the refusals admit, and a test asserts exactly that.

**Alternatives considered**: reading the old repository's tests to learn what the guard was for —
excluded by the brief, and the reason for the exclusion applies precisely here: a test would have
frozen the dead branch as a requirement.

## R4 — Who owns an input's default, given principle I

**Decision**: The capability's own YAML is the sole owner of every input, its default, its description,
its permission demand and its check name. `README.md` carries one copyable call site per capability and
the prose that says what it is for and when not to reach for it. It does **not** restate defaults.

**Rationale**: Principle I is violated by a second statement of a fact, and an input table in the
README is exactly that — the old repository carried both and the specification found four places where
they had drifted apart, each of which had been shipping a false promise to consumers. Making the YAML
the owner removes the fork rather than policing it.

FR-004 requires each permission demand to be documented "at the capability", which the YAML satisfies
directly: a `permissions:` block with the reason beside it is both the declaration and the
documentation, and cannot drift from itself.

**Alternatives considered**: generating the README tables from the YAML — rejected, a generated file in
the tree is still a second copy and now also a build step; a test asserting the tables match the YAML —
rejected, it makes drift detectable rather than impossible, and principle I is about the fork existing.

**Consequence**: a consumer reads the workflow file for the full input list. Acceptable: the file is
public, and the call site in the README covers the common case without listing anything.

## R5 — How principles IV and VII are made into gates

**Decision**: A committed surface snapshot, plus an exemption table that carries reasons.

- **Principle IV** (a consumer cannot absorb it → new line): one committed fixture lists every
  published capability, its composed check name, its input names and its permission demands. A test
  asserts the tree matches the fixture. Renaming a job or adding a permission then cannot reach `main`
  as a silent one-word edit — it arrives as a deliberate diff to the fixture, which is the review
  prompt the failure mode currently lacks. See [contracts/published-surface.md](./contracts/published-surface.md).
- **Principle VII** (a required gate never passes without judging): a test asserts that every
  event-conditional `if:` at job level in a published capability appears in a table naming the events
  it skips under and why. This repository already uses exemptions-with-asserted-reasons twice, so the
  idiom is established rather than invented.

**Rationale**: Both principles describe failures that are invisible in a diff and expensive outside
this repository. A gate that makes the edit *visible* is the whole remedy — neither failure needs
preventing, it needs noticing.

**Alternatives considered**: relying on review — rejected, that is the assumption the principles exist
because it failed; relying on the consumer's CI to catch it — rejected, the cost has already been paid
by then.

## Findings for the specification

Not resolved here, because both change published surface and that is the specification's to decide.

- **F1 — The advisory lint's composite-action form should be cut.** FR-049 publishes the advisory lint
  as both a callable workflow and a composite action. No consumer has ever used the action form, and its
  existence is what forces the callable workflow to hold a moving self-reference (R2) — the old
  repository documented that as an exception to its own SHA-pinning rule. Cutting the action form makes
  the exception vanish: the workflow does the work inline. This is the same reasoning that cut the
  pull-request-body action under OQ-010, applied to the one place it was not.
- **F2 — `mise-version` has no evidenced consumer.** It appears on two capabilities, defaults to empty,
  and no call site in any consumer sets it. It is not harmful, but it is surface carried by inheritance.

Both are recorded rather than acted on. F1 in particular should be settled before implementation
begins, since it decides whether an `actions/` directory exists at all beyond the internal unit.
