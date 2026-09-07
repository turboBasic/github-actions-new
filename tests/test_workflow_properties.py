import re
from itertools import pairwise

from capabilities import (
    REPO,
    WORKFLOW_DIR,
    Doc,
    action_paths,
    declared_inputs,
    fixture,
    is_capability,
    jobs,
    load,
    workflow_docs,
    workflow_paths,
)

# A job gated on which event reached it. A skipped job reports success, so a required check reached
# from an event it does not handle passes without reading anything — and where a red check gets
# investigated, a green one does not.
EVENT_CONDITIONAL = re.compile(r"github\.event_name")

# The permission and its reason on one line. FR-004 makes the `permissions:` block its own
# documentation, which only works while the reason cannot drift from the demand it explains — so it
# sits beside it rather than a line above or a file away.
PERMISSION = re.compile(r"^\s*[a-z][a-z-]*:\s*(?:read|write|none)\s*(?:#(?P<reason>.*))?$")

TABLE_DELIMITER = re.compile(r"^\|[\s:|-]+\|$")
NAMES_A_DEFAULT = re.compile(r"default", re.IGNORECASE)

GOVERNS_A_CACHE = re.compile(r"cache", re.IGNORECASE)

# The steps of `python-ci` that judge the tree. Named by id rather than by the shape of their `run:`
# line, so the gate holds whatever the lines become.
STAGES = ("lint", "lint-changed", "typecheck", "tests")


def skipping_jobs(doc: Doc) -> set[str]:
    return {
        str(job_id)
        for job_id, job in jobs(doc).items()
        if EVENT_CONDITIONAL.search(str(job.get("if", "")))
    }


def test_every_event_conditional_job_appears_in_the_skip_table_with_a_reason() -> None:
    committed = fixture()
    for path in workflow_paths():
        doc = load(path)
        if not is_capability(doc):
            continue
        registered: set[str] = set()
        # A capability with no fixture row at all is the surface gate's failure to report, not this
        # one's; registering nothing here still fails below if it has a job that skips.
        for skip in committed.get(path.stem, {}).get("skips_under", []):
            assert skip["jobs"], f"{path.stem}: a skip entry naming no job asserts nothing"
            assert str(skip["event"]).strip(), f"{path.stem}: a skip entry naming no event"
            assert str(skip["reason"]).strip(), (
                f"{path.stem}: {skip['jobs']} skips under {skip['event']} with no reason. "
                "An exemption list without reasons is a dial on the gate"
            )
            registered |= {str(job) for job in skip["jobs"]}
        assert registered <= set(jobs(doc)), (
            f"{path.stem}: the skip table names {sorted(registered - set(jobs(doc)))}, "
            "which is not a job in the workflow"
        )
        assert registered == skipping_jobs(doc), (
            f"{path.stem}: jobs skipping on an event are {sorted(skipping_jobs(doc))}, "
            f"the skip table registers {sorted(registered)}. Every skip carries its reason or the "
            "gate reports green without judging"
        )


def test_every_permission_carries_its_reason_beside_it() -> None:
    unexplained: list[str] = []
    for path in workflow_paths() + action_paths():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = PERMISSION.match(line)
            if match and not (match.group("reason") or "").strip():
                unexplained.append(f"{path.relative_to(REPO)}:{number}: {line.strip()}")
    assert unexplained == [], (
        "permission demanded with no reason beside it: "
        + "; ".join(unexplained)
        + ". A shortfall fails the run before any job exists, so the block is the only place a "
        "consumer can read what it is for"
    )


def steps_of(name: str, job_id: str) -> list[Doc]:
    return list(jobs(load(WORKFLOW_DIR / f"{name}.yml"))[job_id]["steps"])


def test_no_capability_takes_an_input_governing_the_cache() -> None:
    # Hook environments are cached unconditionally. An input that silently did nothing unless a
    # second one was also set was worse than no input at all, and removing one is a break.
    for name, doc in workflow_docs().items():
        if not is_capability(doc):
            continue
        governing = sorted(
            input_ for input_ in declared_inputs(doc) if GOVERNS_A_CACHE.search(input_)
        )
        assert governing == [], (
            f"{name}: declares {governing}, but caching is not a call site's choice"
        )


def test_the_lockfile_check_precedes_every_stage_of_python_ci() -> None:
    ids = [str(step.get("id", "")) for step in steps_of("python-ci", "python-ci")]
    missing = [step_id for step_id in ("lockfile", *STAGES) if step_id not in ids]
    assert missing == [], f"python-ci names no step {missing}, so this gate places nothing"
    assert ids.index("lockfile") < min(ids.index(stage) for stage in STAGES), (
        "python-ci runs a stage before installing from the lockfile. A lockfile disagreeing with "
        "its manifest makes every stage a verdict about a tree the maintainer does not have"
    )


def test_the_changed_files_lint_is_gated_on_the_lint_stage_switch() -> None:
    condition = next(
        str(step.get("if", ""))
        for step in steps_of("python-ci", "python-ci")
        if step.get("id") == "lint-changed"
    )
    assert "inputs.run-lint" in condition, (
        f"python-ci lints the changed set under `if: {condition}`, which does not consult "
        "run-lint. An input named for a stage governs that stage entirely or it is misnamed"
    )


def table_headers(text: str) -> list[list[str]]:
    lines = text.splitlines()
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line, following in pairwise(lines)
        if line.lstrip().startswith("|") and TABLE_DELIMITER.match(following.strip())
    ]


def test_no_readme_table_names_a_default() -> None:
    # An input's default is owned by the capability YAML. A README column headed `Default` is a
    # second owner, and the two drift into shipping a promise the workflow does not keep.
    offending = [
        cell
        for header in table_headers((REPO / "README.md").read_text(encoding="utf-8"))
        for cell in header
        if NAMES_A_DEFAULT.search(cell)
    ]
    assert offending == [], (
        f"README.md has a table column headed {offending}. Defaults live in the capability YAML, "
        "which cannot drift from itself; the README carries a call site and prose"
    )


def test_the_table_reader_finds_a_table_it_is_given() -> None:
    # Pre-flight the reader, or a change that stops it matching anything reports green over a README
    # full of input tables.
    headers = table_headers("| Input | Default |\n| --- | --- |\n| a | b |\n")
    assert headers == [["Input", "Default"]]
    assert table_headers("| Input | Default |\nnot a table\n") == []
