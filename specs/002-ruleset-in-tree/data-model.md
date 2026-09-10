# Data Model: The Ruleset In The Tree

Three structures, one of them new to the tree. Each field below is owned by exactly one of them; a field
appearing twice is named as derived from the other.

## Committed ruleset

`.github/rulesets/<name>.json`. The owner of what the default branch requires.

Holds exactly the fields a write accepts (R1). Any other key is a validation failure, not an ignored one —
a misspelled field would otherwise read as an absent one, and an absent one asserts nothing.

| Field | Shape | Rule |
| --- | --- | --- |
| `name` | string | Non-empty. Matched against live rulesets to find the one to write (R5). |
| `target` | string | `branch`. Nothing else is in scope. |
| `enforcement` | string | `active`, `evaluate` or `disabled`. |
| `conditions` | object | `ref_name.include` and `ref_name.exclude`, both lists. Today `["~DEFAULT_BRANCH"]` and `[]`. |
| `rules` | list of objects | Each has a `type`; some have `parameters`. Unique by `type`. |
| `bypass_actors` | list of objects | Each has `actor_id`, `actor_type`, `bypass_mode`. |

### Validation (FR-012)

- The key set is exactly the six above.
- Exactly one rule has `type: required_status_checks`.
- That rule's `parameters.required_status_checks` is a non-empty list, each entry an object with a
  non-empty `context` string.
- `target` is `branch`.

The non-emptiness matters more than it looks: a file whose required-checks block is spelled wrong would
leave the context gate iterating an empty list and passing, which is the green-without-judging failure
this whole feature exists to prevent.

### Not held

`id`, `node_id`, `source`, `source_type`, `created_at`, `updated_at`, `_links`,
`current_user_can_bypass`. All read-only. The live ruleset is projected onto the six writable fields
before any comparison (R4).

## Composed context

Derived, never stored. What a ruleset or a consumer can require, computed by `tests/capabilities.py` from
the workflows plus `published_surface.toml` (R6).

| Field | Derived from |
| --- | --- |
| `context` | the calling job's `name` falling back to its id; then, where the job `uses:` a capability, ` / ` and that capability's `check_name` |
| `workflow` | the workflow file the calling job is in |
| `job` | the calling job's id |
| `calls` | the capability the job calls, or none |
| `cannot_judge` | why this context must not be required, or none |

`cannot_judge` is set by whichever of these holds, and carries the reason as text (FR-010):

| Condition | Reason carried |
| --- | --- |
| the called capability records a `skips_under` entry covering the called job | that entry's own `reason`, quoted |
| the calling job carries an `if:` | the condition, verbatim |
| the calling workflow declares no `pull_request` trigger | the events it does declare |

A context with `cannot_judge` set may exist and may be advertised. It may not be required (FR-009).

### The set today

Eight contexts, three of them safe to require. The table in [spec.md](./spec.md#derivation) is the current reading; it
is evidence, not a fixture, and no test asserts it — asserting it would be a fourth copy of what the
workflows already say.

## Apply verdict

Produced by `actions/ruleset-decisions`, consumed by `.github/workflows/apply-ruleset.yml`. Never stored.

| Field | Shape | Meaning |
| --- | --- | --- |
| `verdict` | `nothing` \| `create` \| `update` \| `refuse` | What the workflow should do next |
| `ruleset-id` | string | The live ruleset to write to. Empty for `create` and `refuse`. |
| `difference` | string | Field by field, both sides. Empty only for `nothing`. |
| `body` | file path | The JSON to send. Written for `create` and `update`, absent otherwise. |
| `message` | string | What was read, what it was compared against, what to do |

State transitions, given a committed ruleset and the live rulesets:

| Live state | Verdict |
| --- | --- |
| no ruleset carries the committed name | `create` |
| exactly one does, and the projection matches | `nothing` |
| exactly one does, and the projection differs | `update`, with `difference` populated |
| more than one does | `refuse` (FR-007) |

`update` is not permission to write: the workflow writes only when the dispatch has switched the dry run
off (FR-004). A dry run reaching `update` prints the difference and stops, which is the whole of FR-005
and R9.
