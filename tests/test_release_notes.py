import re
import tomllib
from typing import Any, cast

from capabilities import REPO, allowed_commit_types

# Read by this module alone, so the path lives here rather than beside the workflow reader's.
CLIFF = REPO / "cliff.toml"

Table = dict[str, Any]

# What a parser routes a commit to when it does not name a group. Not a group name itself, so it
# cannot collide with one.
SKIP = "\0skip"


def config() -> Table:
    return tomllib.loads(CLIFF.read_text(encoding="utf-8"))


def parsers() -> list[Table]:
    return cast(list[Table], config()["git"]["commit_parsers"])


def destination(subject: str) -> str | None:
    # git-cliff takes the first parser that matches and stops, so a type's destination is that
    # parser's group, or the skip marker where it has one. None means the type reaches nothing and
    # every commit of it is dropped from the notes without a word.
    for parser in parsers():
        pattern = parser.get("message")
        if pattern is not None and re.search(str(pattern), subject):
            return SKIP if parser.get("skip") else str(parser.get("group"))
    return None


def test_every_parser_names_exactly_one_destination() -> None:
    found = parsers()
    assert found, f"{CLIFF.name} declares no commit parsers, so this gate places nothing"
    wrong = [
        parser for parser in found if (parser.get("group") is None) == (parser.get("skip") is None)
    ]
    assert wrong == [], (
        f"{CLIFF.name} has parsers naming both a group and a skip, or neither: {wrong}. Each routes a "
        "commit to one destination — give it `group` to place it in a section or `skip = true` to leave "
        "it out"
    )


def test_every_allowed_type_reaches_a_destination() -> None:
    types = allowed_commit_types()
    assert types, (
        "conventional-commits.yml declares no types, so this gate compares the notes against nothing"
    )
    homeless = sorted(kind for kind in types if destination(f"{kind}: a subject") is None)
    assert homeless == [], (
        f"the commit grammar admits {homeless} and {CLIFF.name} routes them nowhere, so every commit of "
        f"those types is dropped from the release notes silently. Give each one a `group` in "
        f"`commit_parsers` to place it in a section, or `skip = true` to leave it out deliberately"
    )


def test_the_destination_reader_places_a_type_it_is_given_and_reports_one_it_cannot() -> None:
    # Pre-flight the resolver, or a parser list that stops matching reports green while the notes
    # quietly drop everything.
    assert destination("feat: a subject") not in (None, SKIP)
    assert destination("chore: a subject") == SKIP
    assert destination("nonsense: a subject") is None
