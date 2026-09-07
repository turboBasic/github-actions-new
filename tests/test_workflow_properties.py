import re
from itertools import pairwise

from capabilities import (
    REPO,
    Doc,
    action_paths,
    fixture,
    is_capability,
    jobs,
    load,
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
