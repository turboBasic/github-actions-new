import re

from capabilities import every_yaml, values_at

OWNER = "turboBasic"

# A tag is a moving target and a branch is anyone's to push to, so a third-party step is named by the
# commit it resolves to. `./` and `$/` name this repository's own tree at the caller's commit and
# carry no ref at all, so there is nothing to pin.
SAME_REPOSITORY = ("./", "$/")
SHA = re.compile(r"^[0-9a-f]{40}$")
MOVING_REF = re.compile(r"^v\d+(\.\d+)?$")

# Exactly one self-reference by owner and moving ref is permitted, and only because a reusable
# workflow runs its checkout against the caller's tree and cannot interpolate its own ref — so it can
# reach neither its own files nor the ref the consumer pinned. Nothing here is a preference, and
# nothing else earns it.
EXEMPT: dict[str, str] = {}


def references() -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for where, doc in every_yaml():
        found += [(where, path, uses) for path, uses in values_at(doc, "uses")]
    return found


def test_every_third_party_reference_is_pinned_to_a_full_sha() -> None:
    unpinned: list[str] = []
    for where, path, uses in references():
        if uses.startswith(SAME_REPOSITORY) or uses in EXEMPT:
            continue
        _, _, ref = uses.partition("@")
        if not SHA.match(ref):
            unpinned.append(f"{where} at {path}: {uses}")
    assert unpinned == [], (
        "reference not pinned to a full commit SHA: "
        + "; ".join(unpinned)
        + ". Pin it, or name it in EXEMPT with the reason it cannot be"
    )


def test_every_exemption_carries_a_reason() -> None:
    assert all(reason.strip() for reason in EXEMPT.values())


def test_the_self_reference_exemption_is_the_only_one() -> None:
    assert len(EXEMPT) <= 1, f"more than one unpinned reference is exempt: {sorted(EXEMPT)}"


def test_every_exemption_is_a_self_reference_by_owner_and_moving_ref() -> None:
    for uses in EXEMPT:
        slug, _, ref = uses.partition("@")
        assert slug.startswith(f"{OWNER}/"), f"{uses} is exempt but is not this owner's"
        assert MOVING_REF.match(ref), f"{uses} is exempt but names {ref!r} rather than a moving ref"
