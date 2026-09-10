from capabilities import WRITABLE_FIELDS, Doc, composed_contexts, required_contexts, ruleset_docs

# No check-jsonschema hook covers this file: the tool ships no schema for a repository ruleset, and
# a `--schemafile <url>` would put the network in `mise run ci`. A mis-keyed required-status-checks
# block would otherwise leave this gate reading zero required contexts and passing on an empty set —
# a green gate that judged nothing — so the shape is asserted here instead, where that failure mode
# is exactly what is being guarded against.


def test_a_committed_ruleset_holds_exactly_the_writable_fields() -> None:
    for name, doc in ruleset_docs().items():
        unknown = set(doc) - WRITABLE_FIELDS
        assert unknown == set(), (
            f"{name}: unknown field {sorted(unknown)}, a write rejects anything but {sorted(WRITABLE_FIELDS)}"
        )
        missing = WRITABLE_FIELDS - set(doc)
        assert missing == set(), f"{name}: missing field {sorted(missing)}"


def test_a_committed_ruleset_targets_branches() -> None:
    for name, doc in ruleset_docs().items():
        assert doc["target"] == "branch", f"{name}: target {doc['target']!r}, expected 'branch'"


def test_a_committed_ruleset_carries_exactly_one_required_status_checks_rule() -> None:
    for name, doc in ruleset_docs().items():
        types = [rule.get("type") for rule in doc["rules"]]
        found = [t for t in types if t == "required_status_checks"]
        assert len(found) == 1, (
            f"{name}: rule types {types}, a ruleset requiring nothing gates nothing and the "
            "context gate below would iterate an empty set"
        )


def test_a_committed_ruleset_requires_at_least_one_context() -> None:
    for name, doc in ruleset_docs().items():
        contexts = required_contexts(doc)
        assert contexts != [], (
            f"{name}: empty required-context list, the context gate would pass on an empty set"
        )
        for context in contexts:
            assert context, f"{name}: a required-status-checks entry carries an empty context"


def test_required_contexts_finds_a_context_it_is_given() -> None:
    # Pre-flight the reader, or a change that stops it matching reports green over a file full of
    # retired names — the conventions layer's rule for a table reader, applied to this one.
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
    # Pre-flight the composer against the tree by name, per the conventions layer: a composer that
    # stops reading `uses:` would otherwise report green over every retired name at once. These four
    # are confirmed against this repository's own reported check-run names, not guessed.
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


def test_a_context_the_tree_composes_but_does_not_require_causes_no_failure() -> None:
    # Not every check is a gate. Requiring more is a maintainer's decision, not this gate's —
    # spec.md Story 2, scenario 4. `advisory / prek-advisory` is composed and, deliberately, is not
    # in the eight becoming three: its presence here asserts nothing failed above it.
    composed = {c.context for c in composed_contexts()}
    required = {context for doc in ruleset_docs().values() for context in required_contexts(doc)}
    assert "advisory / prek-advisory" in composed - required
