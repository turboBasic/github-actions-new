# Specification Quality Checklist: Every rule held by a gate

**Purpose**: Validate specification completeness and quality before proceeding to planning

**Created**: 2026-09-12

**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Filenames, tool names and test names are deliberately absent: requirements name artefacts by what
  they answer — the notes configuration, the tool manifest, the vendored specification manifests, the
  single workflow reader — so planning chooses where each gate lives. The one exception is
  `workflow_call`, which is the trigger's actual name and the thing FR-013 partitions on; renaming it
  in prose would make the requirement unreadable.
- The subject of this feature is the repository's own gates, so the reader is a maintainer rather than
  an end user. "Non-technical stakeholder" is read as: someone who has not opened the files can still
  tell what breaks without each gate, and what a failure would tell them.
- Three defects rather than gaps are recorded: the two rendering faults in User Story 1 (FR-004,
  FR-005) and the timeout partition that does not yet exist (FR-014). Each is fixed in this feature
  because a gate asserting a state the tree does not have cannot pass.
- One arithmetic discrepancy in the input was resolved rather than raised as a question: the
  description says three capabilities lose the timeout input, but names the two that keep it and only
  four declare it. Resolved in favour of the named justifications; recorded in Assumptions, and
  reversible if the count was the intended fact.
- FR-017 carries a release consequence: the surface loses two inputs, which is a break under this
  repository's versioning rules rather than a fix.
