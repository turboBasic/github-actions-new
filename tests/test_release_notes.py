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


# A release the notes are cut for. The range runs from the last of these, so anything else matching
# would start it somewhere that is not a release.
EXACT_VERSIONS = ("v1.2.3", "v0.1.0", "v10.20.30")

# A moving compatibility ref is a tag too. Matching one would start the range at wherever the last
# release moved it to rather than at the last release, so the notes would repeat or lose commits.
NOT_A_RELEASE = ("v1", "v1.2", "v0", "v1.2.3-rc1", "v1.2.3.4", "latest", "1.2.3")


def test_the_tag_pattern_matches_an_exact_version_and_no_moving_ref() -> None:
    pattern = re.compile(str(config()["git"]["tag_pattern"]))
    missed = [tag for tag in EXACT_VERSIONS if not pattern.search(tag)]
    assert missed == [], (
        f"{CLIFF.name}'s tag_pattern does not match {missed}, which are exact version tags. The range "
        "would start before the last release, so the notes would repeat commits already published"
    )
    caught = [tag for tag in NOT_A_RELEASE if pattern.search(tag)]
    assert caught == [], (
        f"{CLIFF.name}'s tag_pattern matches {caught}, which are not releases — a moving compatibility "
        "ref among them would start the range at wherever the last release moved it to rather than at "
        "the last release. Anchor the pattern to exactly three numbers"
    )


def test_the_destination_reader_places_a_type_it_is_given_and_reports_one_it_cannot() -> None:
    # Pre-flight the resolver, or a parser list that stops matching reports green while the notes
    # quietly drop everything.
    assert destination("feat: a subject") not in (None, SKIP)
    assert destination("chore: a subject") == SKIP
    assert destination("nonsense: a subject") is None
