# turboBasic/github-actions

Reusable GitHub Actions workflows and composite actions for `turboBasic` repositories.

**Nothing ships yet, and this is not the repository consumers pin.** The work is staged at
[`turboBasic/github-actions-new`](https://github.com/turboBasic/github-actions-new) and replaces
[`turboBasic/github-actions`](https://github.com/turboBasic/github-actions) if it succeeds. Every name
in the tree is therefore already the destination one while every URL still carries the `-new` suffix,
because a URL has to resolve today. The suffix goes when the repository does.

The workflows and actions are being specified from the *functional behaviour* of the repository they
replace, rather than ported from its files. Until one appears under `.github/workflows/` with a
`workflow_call` trigger, there is nothing here for a consumer to call.

Once there is, this file is the contract: what each workflow does, its inputs and their defaults, a
call site that can be copied as-is, and which major tag is current.

## Working in this repository

`AGENTS.md` is the map — it names every artefact and what that artefact answers. Start there.

```console
mise run setup   # tools, dependencies, git hooks
mise run ci      # everything CI runs
```
