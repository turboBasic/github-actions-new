# turboBasic/github-actions Constitution

What must always be true of this repository. Each principle is a gate a spec, plan or PR can fail
against.

This file names no other artefact. Read it for *what may never be violated* — the entry point says
where every other kind of instruction lives, and the conventions layer owns the concrete rules behind
each principle here.

## Core Principles

### I. One Owner Per Fact

Every rule, setting and claim in this repository is stated in exactly one place. A second copy is not
redundancy but a fork: the copies drift, and afterwards nothing in the tree says which of them is
current. Duplication is cheap to commit by accident and expensive to unwind, because unwinding it
means deciding which copy was ever authoritative.

### II. Secrets Never Persist

No secret is written to a file, a log, an artifact, or this repository — in any form, at any point.

### III. Gates Are Never Loosened

No blanket suppression, no relaxed tool mode, no silenced finding, no rule disabled to make a run
pass. A rule that genuinely has to go is turned off in the linter's own config, with the reason
written down, and reported.

## Governance

This constitution supersedes convenience. A change to a principle is a design change: name the
principle, state concretely what breaks without it, offer the smallest alternative that meets the
underlying need, then stop and wait for a decision. Reporting the conflict is mandatory even when
eroding a principle would only be a side effect.

A new principle earns its place only if violating it is expensive to reverse and cheap to commit by
accident. Anything a reviewer would catch and a revert would fix is a convention.

Conventions are not governed here. Naming, file placement, how a test is organised — a request to
change one of those is just a request.

**Version**: 0.1.0 | **Ratified**: 2026-09-07 | **Last Amended**: 2026-09-07
