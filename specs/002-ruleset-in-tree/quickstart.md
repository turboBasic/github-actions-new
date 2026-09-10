# Quickstart: The Ruleset In The Tree

How to prove the feature works, and how to use it afterwards. Everything but the last section runs
offline.

## Prerequisites

```bash
mise run setup
```

## Read what the default branch requires

One file, no API call, no visit to the settings UI — this is SC-002.

```bash
cat .github/rulesets/protect-default-branch.json
```

## Read what the tree composes

Three of them are safe to require. The composer is in `tests/capabilities.py`
([R6](./research.md#r6--the-gates-two-halves)).

```bash
uv run python -c '
import sys; sys.path.insert(0, "tests")
from capabilities import composed_contexts
for c in composed_contexts():
    print(f"{c.context:36} {c.workflow:24} {c.cannot_judge or \"may be required\"}")
'
```

## The gate, and proving it can fail

`mise run ci` reaches every verdict with the network unavailable — SC-003.

```bash
mise run ci
```

Now prove the gate is not passing vacuously. Rename the job that composes a required context and watch it
fail, which is exactly the change that went unnoticed in `001-consumer-contract`:

```bash
sed -i 's/^  ci:$/  gates:/' .github/workflows/ci.yml
uv run pytest tests/test_ruleset_contexts.py
git restore .github/workflows/ci.yml
```

Expected: a failure naming `ci / python-ci`, the workflow and job that no longer compose it, and that
`.github/rulesets/protect-default-branch.json` must be edited in the same change. An exit code alone is
not a result.

Then prove the other half — a context that resolves but cannot judge (FR-009, principle VII):

```bash
# add "advisory / prek-advisory" to the required list, then:
uv run pytest tests/test_ruleset_contexts.py
```

Expected: a failure whose reason is `prek-advisory never judges what it names; the run may report
success without checking anything` — set by `judges = false` in `tests/published_surface.toml`, not by
its `skips_under` entry. Undo the edit.

## The decision unit

Offline, no token, no network.

```bash
uv run pytest tests/test_ruleset_decisions.py
```

See [contracts/ruleset-decisions.md](./contracts/ruleset-decisions.md) for the inputs, outputs and the
four verdicts.

## Applying it

Two dispatches, and the first writes nothing — SC-004, SC-005.

```bash
# 1. See what would change. Writes nothing.
GH_TOKEN=$(gh auth token -u turboBasic) gh workflow run apply-ruleset.yml \
  --repo turboBasic/github-actions-new -f ruleset=protect-default-branch

# 2. Having read the difference, write it.
GH_TOKEN=$(gh auth token -u turboBasic) gh workflow run apply-ruleset.yml \
  --repo turboBasic/github-actions-new -f ruleset=protect-default-branch -f dry-run=false
```

On this feature's own first dispatch, expect **nothing to change** — the committed file reproduces the live
ruleset field for field ([R10](./research.md#r10--what-the-first-apply-must-not-change)), which is FR-013
and SC-006. A difference on the first dispatch means the committed file was transcribed wrong; read it
before running step 2.

## When GitHub stops matching the tree

The same workflow runs on a weekly schedule over every file in `.github/rulesets/`. It reads and never
writes — the write step is reachable from `workflow_dispatch` alone — and it fails on any difference,
which is the alarm a hand edit in the UI would otherwise never raise. The fix is a dispatch: read the
difference, then apply.

A dispatch, by contrast, exits successfully on a difference. A difference is the reason to dispatch.

## Compare against the live ruleset by hand

If a dispatch reports something you did not expect, this is what it compared against:

```bash
GH_TOKEN=$(gh auth token -u turboBasic) gh api \
  repos/turboBasic/github-actions-new/rulesets \
  --jq '.[] | select(.name == "protect-default-branch") | .id' \
  | xargs -I{} env GH_TOKEN=$(gh auth token -u turboBasic) gh api \
      repos/turboBasic/github-actions-new/rulesets/{} \
  | jq '{name, target, enforcement, conditions, rules, bypass_actors}'
```

The `jq` projection is the same six fields the comparison uses
([R1](./research.md#r1--what-the-committed-file-holds)); everything else the API returns is read-only.

## When a job is renamed

The whole point of the feature. The rename and the ruleset edit are one change:

1. Rename the calling job in `.github/workflows/*.yml`.
2. Edit the context in `.github/rulesets/protect-default-branch.json`.
3. The suite passes, so the pull request can merge.
4. After it merges, dispatch apply — dry first — so GitHub stops requiring the retired name.

Step 4 is still a human action. Nothing here applies on merge, because applying a wrong ruleset blocks
every pull request in the repository including the one that would fix it
([R9](./research.md#r9--why-there-is-no-drift-refusal), FR-003).
