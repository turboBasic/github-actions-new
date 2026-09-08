import re

from capabilities import every_yaml, values_at

# A tag is a moving target and a branch is anyone's to push to, so a third-party step is named by the
# commit it resolves to. There is no exemption and no mechanism for one: `./` and `$/` name this
# repository's own tree and carry no ref, and `$/` is resolved from the repository owning the file
# rather than from the workspace — so even a reusable workflow running against a caller's checkout
# reaches its own actions without naming a ref. Nothing else needs to.
SAME_REPOSITORY = ("./", "$/")
SHA = re.compile(r"^[0-9a-f]{40}$")


def references() -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for where, doc in every_yaml():
        found += [(where, path, uses) for path, uses in values_at(doc, "uses")]
    return found


def test_every_third_party_reference_is_pinned_to_a_full_sha() -> None:
    unpinned: list[str] = []
    for where, path, uses in references():
        if uses.startswith(SAME_REPOSITORY):
            continue
        _, _, ref = uses.partition("@")
        if not SHA.match(ref):
            unpinned.append(f"{where} at {path}: {uses}")
    assert unpinned == [], (
        "reference not pinned to a full commit SHA: "
        + "; ".join(unpinned)
        + ". Pin it. Reaching something of this repository's own is `$/`, which needs no ref"
    )


def test_the_reader_finds_a_reference_it_is_given() -> None:
    # Pre-flight the walker, or a change that stops it finding anything reports green over a tree of
    # unpinned actions.
    assert any(uses.startswith("actions/checkout@") for _, _, uses in references())
