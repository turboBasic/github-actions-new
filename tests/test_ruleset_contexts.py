from capabilities import WRITABLE_FIELDS, Doc, required_contexts, ruleset_docs

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
