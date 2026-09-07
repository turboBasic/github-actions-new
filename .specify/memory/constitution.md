<!--
Sync Impact Report
Version: 0.1.0 → 0.2.0 (MINOR: four principles added, none redefined or removed)
Modified principles: none
Added principles:
  IV. What A Consumer Cannot Absorb Needs A New Line
  V. A Published Ref Cannot Be Withdrawn
  VI. Caller-Controlled Text Never Reaches A Command Line
  VII. A Required Gate Never Passes Without Judging
Added sections: none
Removed sections: none
Deferred TODOs: none
-->

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

### IV. What A Consumer Cannot Absorb Needs A New Line

A consumer names a ref and requires a check. Both are promises. A change a consumer cannot take by
resolving that ref alone — a renamed check, a moved call site, a renamed input, a permission it must
newly grant — is not a fix. It starts a new compatibility line, and the old line stays where it is.

The cost of getting this wrong is not paid here. A retired check name blocks every pull request in
every consumer until each ruleset is edited by hand. A newly demanded permission fails the whole run
before any job exists, with no log and no annotation to read, and no condition can skip past it. Both
are one-word edits that read as cosmetic in review, and neither can be diagnosed from the consumer's
side.

### V. A Published Ref Cannot Be Withdrawn

Every refusal runs before any ref exists, and the ref a consumer pins never crosses a break.

A version tag is immutable once published, so a wrong one cannot be deleted. A moving ref has already
been resolved by consumers by the time anyone reads where it points. Neither mistake has a revert.
Refusing before tagging is the only thing that makes a refusal mean anything, and the compatibility
boundary is not simply the major number: below `1.0.0` a break is signalled by the minor, so the
obvious test is the wrong one and the wrong one fails silently in the permissive direction.

### VI. Caller-Controlled Text Never Reaches A Command Line

A commit subject, a pull request title, a branch name, a task name, a path — each is text chosen
outside this repository. None of it is interpolated into a command line. It reaches the code that
uses it as an environment value or as a file.

An injection here runs with whatever token the job holds, and a token that has been used cannot be
un-used. The edit that opens the hole is the most ordinary-looking line in the file, which is the
whole reason this is a principle and not a review note.

### VII. A Required Gate Never Passes Without Judging

A check a consumer is told to require reports success only when it has judged the thing it names. A
gate that cannot do its work fails, or is absent. It does not report green.

A skipped job is reported as a successful one, so a gate reached from an event it does not handle
becomes a required check that passes without reading anything — and where a red check gets
investigated, a green one does not. What merged behind such a gate is not knowable afterwards, which
is why reverting does not undo it. A check advertised as advisory is not a required gate and is not
governed by this.

## Governance

This constitution supersedes convenience. A change to a principle is a design change: name the
principle, state concretely what breaks without it, offer the smallest alternative that meets the
underlying need, then stop and wait for a decision. Reporting the conflict is mandatory even when
eroding a principle would only be a side effect.

A new principle earns its place only if violating it is expensive to reverse and cheap to commit by
accident. Anything a reviewer would catch and a revert would fix is a convention.

Conventions are not governed here. Naming, file placement, how a test is organised — a request to
change one of those is just a request.

**Version**: 0.2.0 | **Ratified**: 2026-09-07 | **Last Amended**: 2026-09-07
