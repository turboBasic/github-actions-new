import json
import os
import sys
from typing import Any, NamedTuple, cast

Doc = dict[str, Any]

# The six fields a write to the rulesets API accepts. tests/capabilities.py owns the same fact for the
# gate that reads the committed file from the tree; this module owns it for the workflow that writes it,
# and neither imports the other — the action ships alone, and the suite runs with no network.
WRITABLE_FIELDS = frozenset(
    {"name", "target", "enforcement", "conditions", "rules", "bypass_actors"}
)

NOTHING = "nothing"
CREATE = "create"
UPDATE = "update"
REFUSE = "refuse"


class Verdict(NamedTuple):
    verdict: str
    ruleset_id: str
    difference: str
    body: Doc | None
    message: str


def shape_problem(committed: Doc) -> str | None:
    unknown = sorted(set(committed) - WRITABLE_FIELDS)
    if unknown:
        return (
            f"the committed ruleset names {unknown}, and a write accepts only "
            f"{sorted(WRITABLE_FIELDS)}. A misspelled field reads as an absent one — fix the key"
        )
    missing = sorted(WRITABLE_FIELDS - set(committed))
    if missing:
        return f"the committed ruleset omits {missing}, which a write requires"
    if committed.get("target") != "branch":
        return f"the committed ruleset's target is {committed.get('target')!r}; only 'branch' is in scope"
    rules = cast(list[Doc], committed["rules"])
    rule_types = [str(rule.get("type")) for rule in rules]
    checks_rules = [rule for rule in rules if rule.get("type") == "required_status_checks"]
    if len(checks_rules) != 1:
        return (
            f"the committed ruleset's rule types are {rule_types}, and exactly one must be "
            "'required_status_checks' — a ruleset requiring nothing gates nothing"
        )
    contexts = cast(
        list[Doc], checks_rules[0].get("parameters", {}).get("required_status_checks", [])
    )
    if not contexts or any(not check.get("context") for check in contexts):
        return (
            "the committed ruleset's required-status-checks list is empty or carries an empty "
            "context; the context gate would pass on an empty set"
        )
    return None


def normalize(doc: Doc) -> Doc:
    # R4: a read orders lists as it pleases and fills defaults the file may omit. Sorting both sides
    # the same way, and comparing only the six writable fields, is what keeps a dispatch from reporting
    # drift it did not cause.
    projected: Doc = {field: doc.get(field) for field in WRITABLE_FIELDS}

    rules = sorted(
        cast(list[Doc], projected.get("rules") or []), key=lambda rule: str(rule.get("type"))
    )
    normalized_rules: list[Doc] = []
    for rule in rules:
        rule = dict(rule)
        if rule.get("type") == "required_status_checks":
            params = dict(cast(Doc, rule.get("parameters") or {}))
            params["required_status_checks"] = sorted(
                cast(list[Doc], params.get("required_status_checks") or []),
                key=lambda check: str(check.get("context")),
            )
            rule["parameters"] = params
        normalized_rules.append(rule)
    projected["rules"] = normalized_rules

    projected["bypass_actors"] = sorted(
        cast(list[Doc], projected.get("bypass_actors") or []),
        key=lambda actor: (str(actor.get("actor_type")), actor.get("actor_id")),
    )

    conditions = dict(cast(Doc, projected.get("conditions") or {}))
    ref_name = dict(cast(Doc, conditions.get("ref_name") or {}))
    ref_name["include"] = sorted(
        str(name) for name in cast(list[Any], ref_name.get("include") or [])
    )
    ref_name["exclude"] = sorted(
        str(name) for name in cast(list[Any], ref_name.get("exclude") or [])
    )
    conditions["ref_name"] = ref_name
    projected["conditions"] = conditions

    return projected


def render_difference(committed: Doc, live: Doc) -> str:
    lines = [
        f"{field}: committed={committed.get(field)!r} live={live.get(field)!r}"
        for field in sorted(WRITABLE_FIELDS)
        if committed.get(field) != live.get(field)
    ]
    return "\n".join(lines)


def decide(committed: Doc, live_list: list[Doc], detail: Doc | None) -> Verdict:
    problem = shape_problem(committed)
    if problem:
        return Verdict(REFUSE, "", "", None, problem)

    name = str(committed["name"])
    matches = [
        ruleset
        for ruleset in live_list
        if ruleset.get("source_type") == "Repository" and ruleset.get("name") == name
    ]

    if len(matches) > 1:
        ids = [str(ruleset.get("id")) for ruleset in matches]
        return Verdict(
            REFUSE,
            "",
            "",
            None,
            f"{len(matches)} rulesets named {name!r} exist on this repository, ids {ids} — the API "
            "does not make names unique. Resolve which one is meant before applying",
        )

    if not matches:
        body = {field: committed[field] for field in WRITABLE_FIELDS}
        return Verdict(
            CREATE,
            "",
            "",
            body,
            f"no ruleset named {name!r} exists on this repository; the committed file becomes a new one",
        )

    live_id = str(matches[0].get("id", ""))
    if detail is None:
        return Verdict(
            REFUSE,
            "",
            "",
            None,
            f"exactly one ruleset named {name!r} exists (id {live_id}), but its full detail was not "
            "read — the list endpoint carries no rules, conditions or bypass_actors to compare "
            "against. Fetch GET /repos/{owner}/{repo}/rulesets/{id} before deciding",
        )

    committed_norm = normalize(committed)
    live_norm = normalize(detail)
    if committed_norm == live_norm:
        return Verdict(
            NOTHING,
            live_id,
            "",
            None,
            f"{name!r} already matches the committed file; nothing to change",
        )

    body = {field: committed[field] for field in WRITABLE_FIELDS}
    difference = render_difference(committed_norm, live_norm)
    return Verdict(
        UPDATE,
        live_id,
        difference,
        body,
        f"{name!r} (id {live_id}) differs from the committed file; see the printed difference",
    )


def read_text(name: str) -> str:
    return os.environ.get(name, "")


def read_doc(path: str) -> Doc:
    with open(path, encoding="utf-8") as handle:
        return cast(Doc, json.load(handle))


def read_list(path: str) -> list[Doc]:
    with open(path, encoding="utf-8") as handle:
        return cast(list[Doc], json.load(handle))


def emit(values: dict[str, str]) -> None:
    path = read_text("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for name, value in values.items():
            # A value may hold newlines — the difference does — so every output uses the delimiter form.
            handle.write(f"{name}<<__RULESET_DECISIONS__\n{value}\n__RULESET_DECISIONS__\n")


def annotate(severity: str, message: str) -> None:
    print(f"::{severity}::{message}", file=sys.stderr if severity == "error" else sys.stdout)


def main() -> int:
    committed = read_doc(read_text("COMMITTED"))
    live_list = read_list(read_text("LIVE"))
    detail_path = read_text("DETAIL")
    detail = read_doc(detail_path) if detail_path else None

    verdict = decide(committed, live_list, detail)

    body_path = read_text("BODY_PATH")
    if verdict.body is not None and body_path:
        with open(body_path, "w", encoding="utf-8") as handle:
            json.dump(verdict.body, handle, indent=2)

    emit(
        {
            "verdict": verdict.verdict,
            "ruleset-id": verdict.ruleset_id,
            "difference": verdict.difference,
            "body": body_path if verdict.body is not None else "",
            "message": verdict.message,
        }
    )
    annotate("error" if verdict.verdict == REFUSE else "notice", verdict.message)
    return 1 if verdict.verdict == REFUSE else 0


if __name__ == "__main__":
    sys.exit(main())
