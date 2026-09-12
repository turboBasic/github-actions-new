# Data Model: Every rule held by a gate

There is no stored data here. The entities are committed artefacts, and the model is which gate reads
which artefact, what it compares, and how it is kept from rotting into a pass. One row per gate.

## Artefacts read

| Artefact | Read as | Read by |
| --- | --- | --- |
| `cliff.toml` | TOML, plus a rendering from the pinned renderer | `test_release_notes.py` |
| `.github/workflows/conventional-commits.yml` | through `capabilities.py` | `test_commit_grammar.py`, `test_names.py` |
| the installed commit tool | `ConventionalCommitsCz(BaseConfig()).schema_pattern()` | `test_commit_grammar.py` |
| `uv.lock` | TOML | `test_commit_grammar.py` |
| `mise.toml` | TOML | `test_tool_versions.py`, `test_speckit_vendoring.py` |
| `.specify/integrations/*.manifest.json` | JSON, plus a SHA-256 of every file named | `test_speckit_vendoring.py` |
| `.github/actionlint.yaml` | YAML, plus a probe run of the pinned linter | `test_actionlint_ignore.py` |
| every `.github/workflows/*.yml` | through `capabilities.py` | `test_names.py`, `test_workflow_properties.py` |
| `tests/published_surface.toml` | TOML | `test_published_surface.py` (already) |

`capabilities.py` is the sole reader of workflow and action YAML (FR-020). Every other artefact is read
by exactly one module, so none gets a shared reader (R15).

## Gates

### The notes configuration — `test_release_notes.py`

| Gate | Reads | Asserts | Guarded against rot by |
| --- | --- | --- | --- |
| FR-001 | commit parsers, and the type set from R5 | each of the twelve types resolves to exactly one destination — a group or a skip | resolving to *exactly one* fails on zero, so a pattern neither engine can read cannot pass (R14) |
| FR-002 | the `<!--N-->` prefix on every group name | the six groups are `Added, Fixed, Performance, Changed, Reverted, Documentation` in that order, numbers unique, no seventh group | the expected sequence is written out literally, so a reader returning nothing cannot match it (research R1) |
| FR-003 | `tag_pattern` | matches `v1.2.3`; does not match `v1`, `v1.2`, or a suffixed tag | asserts both a positive and a negative match, so a pattern of `.*` or `^$` fails |
| FR-004 | a rendering over a planted repository | a numbered subject keeps its number and gains nothing; an unnumbered one gains its short id | rendering is the assertion; there is no shape to pass vacuously |
| FR-005 | the same rendering | `@v5` renders inert; an address in a subject is untouched | as above, and the untouched-address half is what catches an over-broad pattern |

FR-006 is the reason the last two rows render rather than read. All rendering happens in `tmp_path`
with the binary from `mise which git-cliff` and an explicit `--config`; the two hazards in R4 are what
that spelling avoids.

### The commit grammar — `test_commit_grammar.py`

| Gate | Compares | Guarded against rot by |
| --- | --- | --- |
| FR-007 | the workflow's `types` default against the alternation in the installed tool's own schema pattern | both sides are non-empty sets; an accessor returning nothing fails the equality |
| FR-008 | the workflow's `CZ_VERSION` literal against the version `uv.lock` resolves | both sides must parse to a non-empty version string before comparison |

Neither side is restated in the test. The lockfile is the tree's fact and the accessor is the tool's;
there is no third copy (R5, R6).

### Tooling conventions

| Gate | Module | Asserts | Guarded against rot by |
| --- | --- | --- | --- |
| FR-009 | `test_tool_versions.py` | every `[tools]` entry names a concrete version — refusing `latest`, an empty value and a non-string | the table must be non-empty, so an empty read fails |
| FR-010 | `test_speckit_vendoring.py` | each manifest's recorded version equals the `pipx:specify-cli` pin, and every file it records matches its recorded hash | the file map must be non-empty; a manifest recording nothing fails |
| FR-011 | `test_actionlint_ignore.py` | both planted `$/` forms still draw a verdict the committed ignore patterns match | the probe must produce a verdict at all; a clean run is the failure, which is the point |

FR-011 inverts the usual direction: the gate fails when the world gets *better*, and its message says
to delete the ignore and TD-001 together. A failure whose fix is a deletion still has to name the
deletion (FR-021).

### Names — `test_names.py`

| Gate | Asserts | Guarded against rot by |
| --- | --- | --- |
| FR-012 | every job name is lowercase-kebab-case, read through `check_names()` — the same function that composes a consumer's required context | the name list must be non-empty per workflow; the pairing plants `Python_CI` and asserts it is caught |
| FR-013 | every workflow name is its marker plus its filename stem, with the marker chosen by reading the trigger set | the expected name is derived from the file, so a workflow the reader misses has no name to compare and the count assertion fails |

FR-013's marker choice reads whether `workflow_call` is the *only* trigger, so a workflow gaining a
second trigger changes marker automatically rather than needing a list edited (R10).

### The timeout partition — `test_workflow_properties.py`

| Gate | Asserts |
| --- | --- |
| FR-014 / FR-015 | the set of capabilities declaring a timeout input equals `{python-ci, prek-advisory}` exactly — a capability joining the set fails, and one leaving it fails too |
| FR-016 | every job in the two capabilities that lose the input carries a literal `timeout-minutes` |

Asserting set equality rather than a subset is what makes FR-015 bidirectional in one assertion. The
justification for each member lives beside the assertion as a comment, because the reason a knob exists
is not derivable from the fact that it does.

## The six pairings — FR-019

Each guards a reader whose steady state is an empty result, which is why none is self-guarding today
(R13). Each lives beside the gate it guards.

| Reader | Module | Pairing plants |
| --- | --- | --- |
| `PERMISSION` line regex | `test_workflow_properties.py` | a permission line with a reason and one without, asserting the second is flagged |
| `WRITES_A_VERSION` markers | `test_workflow_properties.py` | a step whose `run:` authors a commit, asserting it is matched |
| `GOVERNS_A_CACHE` regex | `test_workflow_properties.py` | `cache-key` matched, `hook-stage` not |
| the grammar-job event gate | `test_workflow_properties.py` | that the workflow yields a non-empty job map, so the loop cannot pass over nothing |
| `blanket_permissions()` | `test_published_surface.py` | a document with `permissions: read-all`, asserting it is returned |
| `URL_OWNER_REPO` regex | `test_repo_urls.py` | a self URL matched, a foreign host not |

## Two additions to `capabilities.py`

Both because more than one gate needs them; nothing else is added (R15).

| Accessor | Answers | Callers |
| --- | --- | --- |
| a job-name accessor | every job's name in a document, id-fallback included | FR-012, and the grammar-job pairing |
| a trigger-kind accessor | whether `workflow_call` is a document's only trigger | FR-013, and available to FR-014's partition |

## What no gate does

- Reach the network, or need a token. Every artefact above is committed; the two subprocesses are pinned
  local binaries operating on planted files.
- Parse workflow or action YAML outside `capabilities.py`.
- Restate a fact it is comparing. Where two copies of a fact exist today, the gate holds them equal; it
  does not become a third.
- Assert anything about the instruction layers, or that a cited principle number resolves. Out of scope.
