from typing import Any

from rulesets import (
    CREATE,
    NOTHING,
    REFUSE,
    UPDATE,
    Doc,
    decide,
    normalize,
    render_difference,
    shape_problem,
)

# A ruleset that admits every check below. Each test changes exactly what it is about.
COMMITTED: Doc = {
    "name": "protect-default-branch",
    "target": "branch",
    "enforcement": "active",
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "rules": [
        {"type": "deletion"},
        {
            "type": "required_status_checks",
            "parameters": {"required_status_checks": [{"context": "ci / python-ci"}]},
        },
    ],
    "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}],
}

LIVE_SUMMARY: Doc = {
    "id": 1,
    "name": "protect-default-branch",
    "source_type": "Repository",
    "target": "branch",
    "enforcement": "active",
}


def _detail(**overrides: Any) -> Doc:
    detail: Doc = {
        **COMMITTED,
        "id": 1,
        "node_id": "n1",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "_links": {"self": {"href": "..."}},
        "current_user_can_bypass": "always",
    }
    detail.update(overrides)
    return detail


def test_shape_problem_names_an_unknown_field() -> None:
    bad: Doc = {**COMMITTED, "id": 1}
    message = shape_problem(bad)
    assert message is not None
    assert "['id']" in message


def test_shape_problem_names_a_missing_field() -> None:
    bad = dict(COMMITTED)
    del bad["bypass_actors"]
    message = shape_problem(bad)
    assert message is not None
    assert "bypass_actors" in message


def test_shape_problem_names_a_target_that_is_not_branch() -> None:
    message = shape_problem({**COMMITTED, "target": "tag"})
    assert message is not None
    assert "'tag'" in message


def test_shape_problem_names_the_absent_required_status_checks_rule() -> None:
    bad = {**COMMITTED, "rules": [{"type": "deletion"}]}
    message = shape_problem(bad)
    assert message is not None
    assert "['deletion']" in message


def test_shape_problem_names_an_empty_context_list() -> None:
    bad: Doc = {
        **COMMITTED,
        "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": []}}],
    }
    message = shape_problem(bad)
    assert message is not None
    assert "empty set" in message


def test_shape_problem_is_none_for_a_well_formed_ruleset() -> None:
    assert shape_problem(COMMITTED) is None


def test_a_malformed_committed_file_refuses_before_any_live_ruleset_is_read() -> None:
    bad = {**COMMITTED, "target": "tag"}
    verdict = decide(bad, [], None)
    assert verdict.verdict == REFUSE
    assert "tag" in verdict.message


def test_no_matching_name_creates() -> None:
    verdict = decide(COMMITTED, [], None)
    assert verdict.verdict == CREATE
    assert verdict.body == COMMITTED


def test_a_match_whose_source_type_is_not_repository_is_not_a_match() -> None:
    organization_owned = {**LIVE_SUMMARY, "source_type": "Organization"}
    verdict = decide(COMMITTED, [organization_owned], None)
    assert verdict.verdict == CREATE


def test_two_rulesets_sharing_the_name_refuse() -> None:
    verdict = decide(COMMITTED, [LIVE_SUMMARY, {**LIVE_SUMMARY, "id": 2}], None)
    assert verdict.verdict == REFUSE
    assert "2 rulesets" in verdict.message
    assert "'1'" in verdict.message
    assert "'2'" in verdict.message


def test_exactly_one_match_with_no_detail_refuses_rather_than_guesses() -> None:
    verdict = decide(COMMITTED, [LIVE_SUMMARY], None)
    assert verdict.verdict == REFUSE
    assert "detail was not read" in verdict.message


def test_a_matching_detail_reads_as_nothing_to_change() -> None:
    verdict = decide(COMMITTED, [LIVE_SUMMARY], _detail())
    assert verdict.verdict == NOTHING
    assert verdict.ruleset_id == "1"
    assert verdict.difference == ""
    assert verdict.body is None


def test_read_only_fields_do_not_cause_a_reported_difference() -> None:
    # R4: id, node_id, created_at, updated_at, _links and current_user_can_bypass come back on a read
    # and are not settable. A byte comparison would report drift on updated_at at every dispatch.
    detail = _detail(updated_at="2099-01-01T00:00:00Z", current_user_can_bypass="never")
    assert decide(COMMITTED, [LIVE_SUMMARY], detail).verdict == NOTHING


def test_reordered_rules_and_contexts_still_read_as_nothing_to_change() -> None:
    reordered = _detail(
        rules=[
            {
                "type": "required_status_checks",
                "parameters": {"required_status_checks": [{"context": "ci / python-ci"}]},
            },
            {"type": "deletion"},
        ]
    )
    assert decide(COMMITTED, [LIVE_SUMMARY], reordered).verdict == NOTHING


def test_a_real_difference_updates_with_the_difference_rendered_both_sides() -> None:
    detail = _detail(enforcement="evaluate")
    verdict = decide(COMMITTED, [LIVE_SUMMARY], detail)
    assert verdict.verdict == UPDATE
    assert verdict.ruleset_id == "1"
    assert verdict.body == COMMITTED
    assert "enforcement" in verdict.difference
    assert "active" in verdict.difference
    assert "evaluate" in verdict.difference


def test_render_difference_names_both_sides_for_every_differing_field() -> None:
    difference = render_difference(normalize(COMMITTED), normalize(_detail(target="tag")))
    assert "target: committed='branch' live='tag'" in difference


def test_normalize_drops_everything_but_the_six_writable_fields() -> None:
    assert set(normalize(_detail())) == {
        "name",
        "target",
        "enforcement",
        "conditions",
        "rules",
        "bypass_actors",
    }
