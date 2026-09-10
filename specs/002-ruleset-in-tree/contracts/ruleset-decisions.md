# Contract: `actions/ruleset-decisions`

Internal surface. No stability promise, no check name, no consumer. `published = false` in
`tests/published_surface.toml`, and excluded from the release surface by R7 — nothing outside this
repository can name it, so nothing it does moves a version.

It answers one question and performs no write. Every HTTP call is the workflow's.

## Inputs

Read from the environment, declared in `action.yml`, never interpolated into a command line (principle
VI).

| Input | Environment | Required | Meaning |
| --- | --- | --- | --- |
| `committed` | `COMMITTED` | yes | Path to the committed ruleset JSON |
| `live` | `LIVE` | yes | Path to the JSON body of `GET /repos/{owner}/{repo}/rulesets`, as the workflow saved it |
| `body-path` | `BODY_PATH` | no | Where to write the body to send. Defaults under `RUNNER_TEMP` |

`live` is a path rather than a value: it is an API response of unbounded size, and a response is text
chosen outside this repository.

## Outputs

| Output | Meaning |
| --- | --- |
| `verdict` | `nothing`, `create`, `update` or `refuse` |
| `ruleset-id` | The live ruleset's id, for `update`. Empty otherwise |
| `difference` | Field by field, both sides. Empty only for `nothing` |
| `body` | Path to the JSON to send. Written for `create` and `update` |
| `message` | What was read, what it was compared against, and what to do about it |

## Behaviour

1. Load `committed`. Validate its shape against the rules in [data-model.md](../data-model.md#validation).
   A failure is a `refuse` naming the offending key, not an exception.
2. From `live`, keep only entries whose `source_type` is `Repository` and whose `name` equals the
   committed `name`. More than one is a `refuse` (FR-007). None is a `create`.
3. Project the one match onto the committed file's six fields, normalise both by R4's sort order, and
   compare.
4. Equal → `nothing`. Different → `update`, with `difference` rendered field by field and `body` written.

Nothing in this module reads the network, reads `GITHUB_TOKEN`, or writes outside `body-path`. That is
what makes it testable offline, which FR-011 requires of the suite that tests it.

## Failure messages

Every one names what was read, what it was compared against, and what a maintainer should do — the
conventions layer's rule for a capability, applied here because the failures are the product.

| Situation | Names |
| --- | --- |
| unknown key in the committed file | the key, the six accepted, and that a write rejects anything else |
| no `required_status_checks` rule | the rule types found, and that a ruleset requiring nothing gates nothing |
| empty context list | the file, and that the context gate would pass on an empty set |
| two rulesets share the name | both ids, both `source_type`s, and that the API does not make names unique |

## What the workflow does around it

`.github/workflows/apply-ruleset.yml`, dispatch only (FR-003), one job, `timeout-minutes` set, every
permission carrying its reason on the same line — `test_every_permission_carries_its_reason_beside_it`
reads the action tree and the workflow tree alike.

```text
inputs:
  ruleset   which committed file to apply
  dry-run   default true — the only input governing whether anything is written (FR-004, R9)

steps:
  checkout                              contents: read
  mint App token                        permission-administration: write   (R8)
  gh api  .../rulesets            ->    $RUNNER_TEMP/live.json
  uses: $/actions/ruleset-decisions
  print the difference                  always, whether or not it writes  (FR-005)
  refuse                                if verdict == refuse
  gh api --input "$body"                if verdict in (create, update) and dry-run is off
```

The body goes in through `--input`, never as an argument (principle VI). The token reaches `gh` as
`GH_TOKEN` in the step's `env`, and is written nowhere (principle II).

The workflow composes the context `apply-ruleset / apply`. It fires on no pull request, so it can never
report on one and must never appear in a committed required list — which
[FR-009](../spec.md#functional-requirements) enforces rather than merely asks.
