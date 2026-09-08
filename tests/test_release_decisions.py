import ast
from pathlib import Path

import decisions
from decisions import (
    ALREADY_RELEASED,
    BAD_SURFACE,
    BREAKS_A_RELEASED_LINE,
    DELIBERATE,
    DRY_RUN,
    ERROR,
    MALFORMED_VERSION,
    NO_NOTES,
    NOTICE,
    OFF_DEFAULT_BRANCH,
    ROUTINE,
    Refusal,
    Request,
    Surface,
    compatibility_line,
    decide,
    increment,
    moving_ref,
    parse_version,
    read_surface,
    refusals,
    surface_notice,
    touches_surface,
)

SOURCE = Path(decisions.__file__).read_text(encoding="utf-8")

# A request that every refusal admits. Each test below changes exactly what it is about, so a failure
# names one cause rather than a combination.
ADMITTED = Request(
    version_text="0.2.0",
    branch="main",
    default_branch="main",
    occasion=DELIBERATE,
    existing=((0, 1, 0),),
    notes="- feat: something a consumer can see",
    breaking=False,
    feature=True,
    changed_paths=(".github/workflows/python-ci.yml",),
    surface=Surface(include=(), exclude=(), declared=True),
)


def test_a_plain_three_part_version_parses() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("0.1.0") == (0, 1, 0)
    assert parse_version("10.20.30") == (10, 20, 30)


def test_anything_but_three_plain_numbers_is_absent_rather_than_raised() -> None:
    # The `v` belongs to the tag and not to the version, and a pre-release or build metadata would
    # make the comparison against the highest release mean something nobody here decided. Absence is
    # returned rather than raised so the caller chooses the message.
    for text in [
        "v1.2.3",
        "1.2",
        "1.2.3.4",
        "1.2.3-rc1",
        "1.2.3+build",
        "1.2.x",
        "01.2.3",
        " 1.2.3",
        "1.2.3 ",
        "",
    ]:
        assert parse_version(text) is None, text


def test_the_line_is_the_major_from_the_first_stable_version_up() -> None:
    assert compatibility_line((1, 0, 0)) == (1,)
    assert compatibility_line((1, 4, 9)) == (1,)
    assert compatibility_line((2, 0, 0)) == (2,)


def test_the_line_is_the_major_and_the_minor_below_it() -> None:
    assert compatibility_line((0, 1, 0)) == (0, 1)
    assert compatibility_line((0, 1, 7)) == (0, 1)
    assert compatibility_line((0, 2, 0)) == (0, 2)


def test_exactly_one_function_reads_the_boundary() -> None:
    # Principle I, and the thing principle V turns on. Reading the boundary off the major number is
    # wrong below the first stable version and wrong permissively — it would let a break move a ref
    # consumers pin — so the refusal, the increment and the ref name all read the line instead.
    module = ast.parse(SOURCE)
    readers = sorted(
        node.name
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(inner, ast.Name) and inner.id == "FIRST_STABLE" for inner in ast.walk(node)
        )
    )
    assert readers == ["compatibility_line"], (
        f"{readers} read FIRST_STABLE. The boundary has one owner and everything else reads the line "
        "it returns"
    )


def test_the_moving_ref_below_the_boundary_spans_a_minor() -> None:
    assert moving_ref((0, 1, 0)) == "v0.1"
    assert moving_ref((0, 1, 9)) == "v0.1"
    assert moving_ref((0, 2, 0)) == "v0.2"


def test_the_moving_ref_above_the_boundary_spans_a_major() -> None:
    assert moving_ref((1, 0, 0)) == "v1"
    assert moving_ref((1, 9, 9)) == "v1"
    assert moving_ref((2, 0, 0)) == "v2"


def test_the_moving_ref_is_total_and_never_bare_v_zero() -> None:
    # This replaces the superseded repository's guard against an empty ref rather than reproducing it:
    # the ref has at least one component for every version, so that branch could not be reached. `v0`
    # would span every pre-1.0 break at once, which is the one thing a moving ref exists to prevent.
    for major in range(4):
        for minor in range(4):
            for patch in range(4):
                ref = moving_ref((major, minor, patch))
                assert ref.startswith("v") and len(ref) > 1, (major, minor, patch)
                assert ref != "v0", (major, minor, patch)


def test_below_the_boundary_a_break_advances_the_minor() -> None:
    assert increment((0, 1, 4), breaking=True, feature=False) == (0, 2, 0)
    assert increment((0, 1, 4), breaking=True, feature=True) == (0, 2, 0)


def test_below_the_boundary_a_feature_advances_only_the_patch() -> None:
    # The reading the naive version gets wrong. A consumer pinned to v0.1 has to be able to receive a
    # feature without crossing into v0.2, so a feature may only advance a component the line does not
    # own.
    assert increment((0, 1, 4), breaking=False, feature=True) == (0, 1, 5)


def test_above_the_boundary_a_break_advances_the_major_and_a_feature_the_minor() -> None:
    assert increment((1, 4, 2), breaking=True, feature=False) == (2, 0, 0)
    assert increment((1, 4, 2), breaking=True, feature=True) == (2, 0, 0)
    assert increment((1, 4, 2), breaking=False, feature=True) == (1, 5, 0)


def test_neither_a_break_nor_a_feature_advances_the_patch_on_either_side() -> None:
    assert increment((0, 1, 4), breaking=False, feature=False) == (0, 1, 5)
    assert increment((1, 4, 2), breaking=False, feature=False) == (1, 4, 3)


def keys(request: Request) -> list[str]:
    return [refusal.key for refusal in refusals(request)]


def test_a_request_every_refusal_admits_produces_none() -> None:
    assert refusals(ADMITTED) == []


def test_a_run_off_the_default_branch_is_refused_naming_both_branches() -> None:
    found = refusals(ADMITTED._replace(branch="topic"))
    assert [refusal.key for refusal in found] == [OFF_DEFAULT_BRANCH]
    assert "topic" in found[0].message and "main" in found[0].message


def test_a_version_that_does_not_parse_stops_the_ladder() -> None:
    # Nothing below the version can be decided without one, and a refusal derived from a version that
    # was never read would name a comparison nobody made.
    assert keys(ADMITTED._replace(version_text="v0.2", notes="")) == [MALFORMED_VERSION]


def test_a_version_not_ahead_of_the_highest_release_is_refused() -> None:
    assert ALREADY_RELEASED in keys(ADMITTED._replace(version_text="0.1.0", existing=((0, 1, 0),)))


def test_the_comparison_is_against_every_line_not_the_declared_one() -> None:
    # A frozen line is left where it is rather than backported, so a version behind a release on any
    # line is refused even when its own line has none.
    assert ALREADY_RELEASED in keys(ADMITTED._replace(version_text="0.3.0", existing=((1, 0, 0),)))


def test_a_range_rendering_no_notes_is_refused() -> None:
    for notes in ["", "   ", "\n\n"]:
        assert NO_NOTES in keys(ADMITTED._replace(notes=notes)), repr(notes)


def test_a_break_staying_on_a_line_that_already_has_a_release_is_refused() -> None:
    assert BREAKS_A_RELEASED_LINE in keys(
        ADMITTED._replace(version_text="0.1.5", breaking=True, existing=((0, 1, 0),))
    )


def test_a_break_that_starts_the_next_line_is_admitted() -> None:
    assert refusals(ADMITTED._replace(version_text="0.2.0", breaking=True)) == []


def test_a_break_outside_the_declared_surface_does_not_freeze_the_line() -> None:
    # The declaration narrows this refusal and nothing else.
    narrowed = ADMITTED._replace(
        version_text="0.1.5",
        breaking=True,
        surface=Surface(include=("actions",), exclude=(), declared=True),
        changed_paths=("README.md",),
    )
    assert BREAKS_A_RELEASED_LINE not in keys(narrowed)


def test_a_routine_push_declines_the_already_released_case_with_a_notice() -> None:
    # A default branch must not redden for doing nothing wrong: a merge that did not bump the version
    # is not a mistake.
    verdict = decide(ADMITTED._replace(occasion=ROUTINE, version_text="0.1.0"))
    assert verdict.proceed is False
    assert verdict.severity == NOTICE


def test_a_dry_run_proceeds_and_reports_what_it_would_have_refused() -> None:
    verdict = decide(ADMITTED._replace(occasion=DRY_RUN, branch="topic", version_text="0.1.0"))
    assert verdict.proceed is True
    assert verdict.severity == NOTICE
    assert "topic" in verdict.message and "0.1.0" in verdict.message


def test_anything_else_refuses_the_already_released_case_as_an_error() -> None:
    verdict = decide(ADMITTED._replace(occasion=DELIBERATE, version_text="0.1.0"))
    assert verdict.proceed is False
    assert verdict.severity == ERROR
    assert "0.1.0" in verdict.message


def test_a_routine_push_still_errors_on_any_other_refusal() -> None:
    # Only the already-released case is what a blameless merge looks like. An malformed version or
    # an empty range is a defect whichever event reached it.
    verdict = decide(ADMITTED._replace(occasion=ROUTINE, notes=""))
    assert verdict.proceed is False
    assert verdict.severity == ERROR


def test_a_request_every_refusal_admits_proceeds() -> None:
    assert decide(ADMITTED).proceed is True


def test_an_absent_declaration_considers_every_path_and_is_reported() -> None:
    surface = read_surface(None)
    assert isinstance(surface, Surface)
    assert surface.declared is False
    assert touches_surface(surface, ["anything/at/all.md"]) is True
    assert surface_notice(surface)


def test_a_declaration_with_both_lists_empty_considers_every_path_and_says_nothing() -> None:
    surface = read_surface({})
    assert isinstance(surface, Surface)
    assert surface.declared is True
    assert touches_surface(surface, ["anything/at/all.md"]) is True
    assert surface_notice(surface) is None


def test_a_declaration_narrows_to_what_it_declares() -> None:
    surface = read_surface(
        {"include": [".github/workflows"], "exclude": [".github/workflows/ci.yml"]}
    )
    assert isinstance(surface, Surface)
    assert touches_surface(surface, ["README.md"]) is False
    assert touches_surface(surface, [".github/workflows/python-ci.yml"]) is True
    assert touches_surface(surface, [".github/workflows/ci.yml"]) is False


def test_an_unknown_key_is_refused_rather_than_ignored() -> None:
    # A misspelled key would otherwise read as an absent one, which is the declared-but-empty state —
    # silently widening the surface to every path while looking configured.
    refused = read_surface({"includes": ["actions"]})
    assert isinstance(refused, Refusal)
    assert refused.key == BAD_SURFACE
    assert "includes" in refused.message


def test_a_non_list_value_is_refused_rather_than_coerced() -> None:
    # Iterating a string yields characters, so every letter would become a path and the filter would
    # match nothing while looking configured.
    assert isinstance(read_surface({"include": "actions"}), Refusal)
    assert isinstance(read_surface({"exclude": 3}), Refusal)


def test_a_declaration_that_is_not_a_table_is_refused() -> None:
    assert isinstance(read_surface(["actions"]), Refusal)
    assert isinstance(read_surface("actions"), Refusal)


def test_a_path_that_is_empty_or_holds_whitespace_or_begins_with_a_hyphen_is_refused() -> None:
    for path in ["", " ", "two words", "\tx", "-rf", "-"]:
        for key in ["include", "exclude"]:
            refused = read_surface({key: [path]})
            assert isinstance(refused, Refusal), (key, repr(path))
