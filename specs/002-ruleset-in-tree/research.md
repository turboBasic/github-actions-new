# Research: The Ruleset In The Tree

Every decision below was reached against the tree as it stands, and each names the alternative it
rejected. Nothing here is a preference: where a choice was settled by reading something, what was read
is named.

## R1 — What the committed file holds

**Decision**: `.github/rulesets/protect-default-branch.json`, holding exactly the six fields a write
accepts: `name`, `target`, `enforcement`, `bypass_actors`, `conditions`, `rules`.

**Rationale**: `POST /repos/{owner}/{repo}/rulesets` and `PUT /repos/{owner}/{repo}/rulesets/{id}` take
that body and no more. `id`, `node_id`, `source`, `source_type`, `created_at`, `updated_at`, `_links` and
`current_user_can_bypass` come back on a read and are not settable. A file holding them would be a file
whose every field cannot be honoured, and comparison would report drift on `updated_at` at every
dispatch.

**Alternatives**: committing the whole `GET` response, rejected for that reason. Writing it as YAML,
rejected because the API speaks JSON and a translation layer would be a second owner of the shape.

## R2 — No schema hook

**Decision**: no `check-jsonschema` hook and no vendored schema. The committed ruleset's shape is
asserted by the test suite instead — exactly the fields R1 names, a `required_status_checks` rule
present, and a non-empty context list.

**Rationale**: `check-jsonschema` 0.33 lists 27 builtin schemas and none is a repository ruleset. A
`--schemafile <url>` would put the network into `mise run ci`, which the conventions layer forbids by
name. `.github/actionlint.yaml` already carries this exact situation, and its own comment records the
answer: no hook, reason in the file, because a mis-keyed entry there fails safe.

This file does **not** fail safe in the same direction. A `required_status_checks` block spelled wrong
would leave the FR-008 gate reading zero required contexts and passing on an empty set — a green gate
that judged nothing, which is principle VII's failure inside the very feature meant to prevent it. So the
shape is asserted where it can be, in the suite, and a hand-written schema would only restate what those
assertions already hold.

**Alternatives**: a vendored JSON Schema, rejected as a second owner of a shape the API owns and one this
repository could not validate against the API offline anyway. No assertion at all, rejected because the
vacuous pass above is the whole risk.

**Reported**: the conventions layer says a new GitHub config file gets a `check-jsonschema` hook and a
matching line in the `lint` task. This is a deliberate departure from that convention, on the precedent
the convention's own exception already set. It is a convention rather than an invariant, and this is the
report it asks for.

## R3 — Where the apply logic lives

**Decision**: `actions/ruleset-decisions/` — `action.yml` plus `rulesets.py`, composite, standard library
only, every argument read from the environment. It is a pure decision unit: given the committed file and
the live rulesets as JSON, it answers what to do and renders the body to write. All HTTP lives in
`.github/workflows/apply-ruleset.yml`, which reads with `gh api` and writes with `gh api`.

**Rationale**: this is the one pattern the repository already has for Python a workflow runs and pytest
tests — `actions/release-decisions/`. Reusing it costs nothing: `tests/conftest.py` and pyproject's
`[tool.pyright].extraPaths` already establish how such a module is reached, `[tool.ruff].src` already
names `actions`, and `zizmor --pedantic .github/workflows actions` already covers the tree. Keeping the
HTTP outside the unit is what makes the unit offline, which FR-011 requires.

**Alternatives**: a `run:` block in the workflow, rejected because the conventions layer says moving a
decision out of a `run:` block so it can be called is worth doing for that reason alone. A script under a
new top-level directory, rejected: two pyproject edits and a second home for Python, for no gain. Putting
it in `tests/`, rejected because apply logic is not test support.

## R4 — Comparison by meaning

**Decision**: normalise both sides, then compare. Project the live ruleset onto the fields R1 names; sort
`rules` by `type`; sort `required_status_checks.required_status_checks` by `context`; sort `bypass_actors`
by `(actor_type, actor_id)`; sort `conditions.ref_name.include` and `.exclude`. Report the difference
field by field rather than as one blob.

**Rationale**: a read orders lists as it pleases and fills defaults the file may omit. A byte comparison
would report a difference at every dispatch, and a report that always fires is one nobody reads.

**Alternatives**: comparing the serialised JSON, rejected for that reason.

## R5 — Finding the ruleset

**Decision**: match on `name` across `GET /repos/{owner}/{repo}/rulesets`, considering only entries whose
`source_type` is `Repository`. More than one match refuses. None creates.

**Rationale**: the API does not make names unique, and an organisation-level ruleset can carry the same
name while not being ours to write. Guessing which one was meant is a write to the wrong object.

## R6 — The gate's two halves

**Decision**: `tests/capabilities.py` gains the composition, because it is already the one owner of how a
workflow is read. For every workflow under `.github/workflows`, for every job: the calling half of the
context is the job's `name` falling back to its id, and where the job's `uses:` names a capability in this
repository, the context is `<calling half> / <check_name>` for each `check_name` that capability records
in `published_surface.toml`. A job that calls nothing composes its own name alone.

Alongside each context, why it cannot be required, where that applies: the called capability records a
`skips_under` entry covering the called job; the calling job carries an `if:`; or the calling workflow
declares no `pull_request` trigger.

**Rationale**: `published_surface.toml` already owns every called job name and every skip reason, and
this feature reads both and adds neither. The calling half is what nothing in the tree records today, and
it is read from the workflow rather than restated anywhere.

**Alternatives**: a second fixture listing composed contexts, rejected — it would be a third copy of a
fact the workflows and `published_surface.toml` already hold between them.

## R7 — Release relevance

**Decision**: `.github/workflows/apply-ruleset.yml` and `actions/ruleset-decisions/action.yml` join
`[tool.turbobasic-release].exclude` in `pyproject.toml`.

**Rationale**: `include` is `.github/workflows` and `actions`, so without this every edit to either would
read as a consumer-visible change and move a version for nobody's benefit. Nothing outside this repository
can call either — the workflow has no `workflow_call` trigger and the action is named by no capability.
This is the same reason every one of this repository's own caller workflows is already excluded.

**Open for the task list**: whether `matches()` in `decisions.py` needs a directory glob
(`actions/ruleset-decisions/*`) or the single `action.yml` path suffices. Read the matcher, do not assume.

## R8 — The token

**Decision**: the apply workflow mints an App installation token with
`actions/create-github-app-token`, narrowed to `permission-administration: write`, from the
`RELEASE_APP_CLIENT_ID` and `RELEASE_APP_PRIVATE_KEY` secrets — the pattern `release-proposal.yml` already
uses. The run's own `GITHUB_TOKEN` gets `contents: read`, for the checkout and nothing else.

**Rationale**: `GITHUB_TOKEN` cannot administer a ruleset at any permission level, so an App token is not
a preference here. Minting it narrowed means the run holds administration rights and nothing else.

**Verified as far as it can be**: those two secrets are the only App credentials on the repository. Whether
that App's installation actually grants `administration` could not be read from outside it — both
`/repos/{owner}/{repo}/installation` and `/users/{owner}/installations` require App authentication. The
mint itself is the check: `create-github-app-token` fails when the installation cannot grant a permission
it is asked for, and it fails before any write. If it does fail, the App's installed permissions are what
to widen, and the issue's claim that `turbobasic-repo-automation` holds `administration: write` is what to
re-read.

## R9 — Why there is no drift refusal

**Decision**: one dispatch input, the dry run, defaulting on. No second `force` input.

**Rationale**: two readings of the spec's own requirements collided. A refusal on any difference between
live and committed would fire on every dispatch that did any work, because a difference is the only reason
to dispatch — and a refusal that always fires is not read. Refusing only a difference a *person* made in
the UI would be the useful rule, and it needs the ruleset's history to name who made each edit.
`GET /repos/turboBasic/github-actions-new/rulesets/22481092/history` returns two versions and `actor` is
`null` on both. So attribution is not available, and what is left is to show the difference and require a
person to act on it.

That is the dry run, and it is the whole mechanism: nothing is written by a dispatch at its defaults, so
nothing is overwritten before the difference has been printed and read.

**Alternatives**: keeping both inputs, rejected above. Recording the last-applied state in the tree so
drift could be attributed, rejected as a second owner of the ruleset's state — principle I, and the exact
fork this feature exists to remove.

## R10 — What the first apply must not change

**Decision**: the committed file reproduces the live ruleset exactly as read on 2026-09-08, including the
`admin` bypass actor and the three required contexts. The first real dispatch is expected to report
nothing to change.

**Rationale**: FR-013 and SC-006. A feature that moved ownership and edited the contents in one change
would leave nobody able to say which half caused a later block, and applying is the one action here that
no revert undoes.
