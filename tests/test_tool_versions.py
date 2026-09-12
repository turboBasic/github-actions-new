import tomllib
from typing import Any, cast

from capabilities import REPO

MANIFEST = REPO / "mise.toml"

# A version mise resolves differently on two machines on one commit. `latest` is the obvious one; a
# bare table with no version and a range are the same failure spelled differently.
FLOATING = frozenset({"latest", "", "*"})


def tools() -> dict[str, Any]:
    manifest: dict[str, Any] = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return cast(dict[str, Any], manifest["tools"])


def floating(entry: Any) -> bool:
    # A table entry states its version under `version`; anything that is not a string or a table
    # naming one cannot be read as a version at all.
    if isinstance(entry, str):
        return entry.strip() in FLOATING
    if isinstance(entry, dict):
        return floating(cast(dict[str, Any], entry).get("version", ""))
    return True


def test_no_tool_version_floats() -> None:
    declared = tools()
    assert declared, (
        f"{MANIFEST.name} declares no [tools], so this gate is reading the wrong table and every "
        "version in it is free to float"
    )
    unpinned = sorted(name for name, entry in declared.items() if floating(entry))
    assert unpinned == [], (
        f"{MANIFEST.name} leaves {unpinned} without a concrete version. Two machines on one commit "
        "would then resolve different linters, so a green run locally says nothing about CI. Name the "
        "version each of those resolves to today"
    )


def test_the_floating_reader_tells_a_version_from_a_range() -> None:
    # Pre-flight the reader. Nothing floats today, which is the point, so the gate above can never show
    # that it would still notice one.
    assert floating("latest")
    assert floating("")
    assert floating({"version": "latest"})
    assert floating({})
    assert floating(None)
    assert not floating("1.7.12")
    assert not floating({"version": "1.7.12"})
