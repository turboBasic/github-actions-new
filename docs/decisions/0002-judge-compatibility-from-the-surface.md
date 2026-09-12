---
id: 0002
status: accepted
date: 2026-09-12
scope: release
---

# ADR 0002 — Compatibility is judged from the surface, not a consumer survey

## Decision

The consumer set is indefinite and is not recorded anywhere in this repository. Whether a change breaks
a consumer is read from the published surface itself — the capability files and the surface fixture that
freezes them — and never from which repositories are known to call what. Semantic versioning is the
whole of what this library promises; how it is used is the consumer's responsibility.

## Context

Sizing the consolidation meant surveying every repository within reach, which found four callers, two of
them on a major frozen years ago. That survey was then proposed as a standing artefact — a
`docs/consumers.md` answering "who breaks if I rename this job", on the grounds that nothing else can.

It was rejected on what the survey itself demonstrated. Two harness scenarios justified their existence
by naming a repository that had stopped consuming the library entirely, and both cited a
`docs/consumers.md` that existed in neither tree. The register meant to prevent that rot was the thing
that rotted. A public ref is resolvable by anyone, so no register is complete, and an incomplete one is
worse than none: it answers "nobody" for every consumer it cannot see, and that answer looks like
evidence.

## Options

### Judge from the published surface alone (SELECTED)

- Adopted because: a public ref is resolvable by anyone, so any register's "nobody breaks" is
  unfalsifiable rather than merely incomplete.
- Adopted because: it leaves the surface fixture as the single artefact a bump is read from, and a gate
  can hold a fixture where nothing can hold a survey.
- Adopted despite: nobody can answer "who breaks" before shipping — the answer arrives as somebody
  else's failing run.
- Adopted despite: the harness repository becomes the only caller we will ever test against, which makes
  its coverage load-bearing rather than supplementary.

### Maintain a consumer register

- Rejected because: unmaintainable by construction — the set it claims to enumerate is not enumerable.
- Rejected because: it trains the version decision onto a survey, which is the reasoning the surface
  fixture exists to replace.
- Rejected despite: it is the only thing that would have caught the stale justifications described
  above, and it was the recommendation before this ruling.

### Register consumers within the organisation only

- Rejected because: a partial register is the full register's failure with a narrower excuse, and it is
  the variant most likely to be mistaken for complete.
- Rejected despite: it is cheap, and it is where most callers actually are today.

## Consequences

A call count is no longer an argument about the interface. An input is removed because it does not belong
in the contract, never because nothing is observed to set it — which is what makes the surface fixture's
diff the whole of the review.

Nothing published may be deleted or narrowed on the grounds that no caller is known; ADR 0001's refusal
to delete a release tag rests on this. A harness scenario justifies itself by the input it exercises
rather than by a repository that sets one. And migration guidance for a new major is addressed to a
consumer in the consumer-facing reference, rather than written as a procedure this repository executes
across a set it cannot see.

Reopened if the library ever becomes private to one organisation, where the set becomes enumerable.

## Links

No issue — ruled in conversation while consolidating the two trees; the PR landing the tree carries the
evidence. ADR 0001 depends on this ruling.
