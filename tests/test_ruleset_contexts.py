from rulesets import shape_problem

from capabilities import Doc, composed_contexts, required_contexts, ruleset_docs, switched_off

# No check-jsonschema hook covers a committed ruleset: the tool ships no schema for one, and a
# `--schemafile <url>` would put the network in `mise run ci`. The shape is asserted here instead,
# because a mis-keyed required-status-checks block leaves the context gates below reading an empty set
# and passing on it. `shape_problem` is the one owner of that shape; the applier refuses on the same
# call, and test_ruleset_decisions.py holds what each refusal says.
#
# Every reader below is pre-flighted, by name against the tree or against a document it is given: a
# reader that silently stops matching reports green over a file full of retired names.


def test_every_committed_ruleset_is_a_shape_a_write_accepts() -> None:
    for name, doc in ruleset_docs().items():
        problem = shape_problem(doc)
        assert problem is None, f".github/rulesets/{name}.json: {problem}"


def test_required_contexts_finds_a_context_it_is_given() -> None:
    given: Doc = {
        "rules": [
            {
                "type": "required_status_checks",
                "parameters": {"required_status_checks": [{"context": "ci / python-ci"}]},
            }
        ]
    }
    assert required_contexts(given) == ["ci / python-ci"]


def test_required_contexts_returns_nothing_for_a_ruleset_with_no_such_rule() -> None:
    assert required_contexts({"rules": [{"type": "deletion"}]}) == []


def test_composed_contexts_finds_the_contexts_the_tree_actually_reports() -> None:
    # These four are confirmed against this repository's own reported check-run names, not guessed.
    contexts = {c.context for c in composed_contexts()}
    assert "ci / python-ci" in contexts
    assert "commits / pr-title" in contexts
    assert "commits / commit-messages" in contexts
    assert "propose" in contexts


def _unresolved(ruleset_name: str, context: str) -> str:
    # FR-010: names the context, where it is required, and what to do about it. A rename or a
    # retirement is the same fix either way — edit the committed ruleset in the same change.
    return (
        f"{ruleset_name} requires {context!r}, which nothing in the tree composes. A calling job "
        "was renamed or retired, or the called job's name in published_surface.toml no longer "
        f"matches. Edit .github/rulesets/{ruleset_name}.json in the same change"
    )


def test_every_required_context_is_composed_by_the_tree() -> None:
    composed = {c.context for c in composed_contexts()}
    for name, doc in ruleset_docs().items():
        for context in required_contexts(doc):
            assert context in composed, _unresolved(name, context)


def test_the_unresolved_message_names_the_ruleset_the_context_and_what_to_do() -> None:
    # FR-010, asserted on the message content rather than only the failure — an exit code alone is
    # not a result.
    message = _unresolved("protect-default-branch", "gates / python-ci")
    assert "protect-default-branch" in message
    assert "gates / python-ci" in message
    assert ".github/rulesets/protect-default-branch.json" in message


def test_cannot_judge_is_set_by_name_for_the_contexts_that_cannot_be_required() -> None:
    # One context per reason, so dropping any single reason fails here rather than only where it counts.
    by_context = {c.context: c.cannot_judge for c in composed_contexts()}
    assert by_context["advisory / prek-advisory"] is not None
    assert by_context["describe / pr-description"] is not None
    for context in ("verify / python-ci", "release / tag-and-publish", "propose"):
        reason = by_context[context]
        assert reason is not None
        assert "pull_request" in reason
    assert by_context["ci / python-ci"] is None


def _cannot_be_required(ruleset_name: str, context: str, reason: str) -> str:
    # FR-009, principle VII made structural. The reason is quoted rather than summarised, so the
    # message says which of the several causes applied.
    return (
        f"{ruleset_name} requires {context!r}, which cannot judge anything: {reason}. "
        f"Remove it from .github/rulesets/{ruleset_name}.json — a required gate never passes "
        "without judging"
    )


def test_a_call_that_switches_a_check_off_cannot_judge_the_context_it_composes() -> None:
    reason = switched_off(
        {"uses": "$/.github/workflows/conventional-commits.yml", "with": {"check-title": False}},
        "conventional-commits",
        "pr-title",
    )
    assert reason is not None
    assert "check-title" in reason
    assert "pr-title" in reason


def test_a_call_that_leaves_a_check_at_its_default_judges_normally() -> None:
    for given in ({}, {"check-title": True}, {"timeout-minutes": 5}):
        assert (
            switched_off(
                {"uses": "$/.github/workflows/conventional-commits.yml", "with": given},
                "conventional-commits",
                "pr-title",
            )
            is None
        )


def test_an_input_that_gates_no_job_switches_nothing_off() -> None:
    # `types` appears in no job's `if:`, so passing it changes nothing about whether the job judges.
    assert (
        switched_off(
            {"uses": "$/.github/workflows/conventional-commits.yml", "with": {"types": "feat"}},
            "conventional-commits",
            "pr-title",
        )
        is None
    )


def test_an_expression_valued_switch_is_refused_because_it_cannot_be_resolved_offline() -> None:
    reason = switched_off(
        {
            "uses": "$/.github/workflows/conventional-commits.yml",
            "with": {"check-commits": "${{ github.event_name == 'pull_request' }}"},
        },
        "conventional-commits",
        "commit-messages",
    )
    assert reason is not None


def test_no_required_context_can_skip_under_the_event_it_would_gate() -> None:
    cannot_judge = {c.context: c.cannot_judge for c in composed_contexts()}
    for name, doc in ruleset_docs().items():
        for context in required_contexts(doc):
            reason = cannot_judge.get(context)
            assert reason is None, _cannot_be_required(name, context, reason or "")


def test_the_cannot_be_required_message_quotes_the_reason() -> None:
    message = _cannot_be_required(
        "protect-default-branch", "advisory / prek-advisory", "it is advisory"
    )
    assert "protect-default-branch" in message
    assert "advisory / prek-advisory" in message
    assert "it is advisory" in message


def test_a_context_the_tree_composes_but_does_not_require_causes_no_failure() -> None:
    # Not every check is a gate: requiring more is a maintainer's decision, not this gate's.
    composed = {c.context for c in composed_contexts()}
    required = {context for doc in ruleset_docs().values() for context in required_contexts(doc)}
    assert "advisory / prek-advisory" in composed - required
