import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = REPO / ".github" / "workflows"
ACTION_DIR = REPO / "actions"
FIXTURE = Path(__file__).parent / "published_surface.toml"

Doc = dict[Any, Any]

# A workflow's `on:` key is YAML 1.1's `true`, so a parser hands it back as the boolean and every
# lookup by the string finds nothing. Both spellings are read, because which one arrives depends on
# the parser rather than on the file.
ON_KEYS: tuple[Any, ...] = (True, "on")

LEVELS = {"none": 0, "read": 1, "write": 2}


def load(path: Path) -> Doc:
    return cast(Doc, yaml.safe_load(path.read_text(encoding="utf-8")))


def workflow_docs() -> dict[str, Doc]:
    return {path.stem: load(path) for path in sorted(WORKFLOW_DIR.glob("*.yml"))}


def action_docs() -> dict[str, Doc]:
    return {path.parent.name: load(path) for path in sorted(ACTION_DIR.glob("*/action.yml"))}


def workflow_paths() -> list[Path]:
    return sorted(WORKFLOW_DIR.glob("*.yml"))


def action_paths() -> list[Path]:
    return sorted(ACTION_DIR.glob("*/action.yml"))


def fixture() -> dict[str, Doc]:
    return cast(dict[str, Doc], tomllib.loads(FIXTURE.read_text(encoding="utf-8")))


def triggers(doc: Doc) -> Doc:
    for key in ON_KEYS:
        if key in doc:
            found: Any = doc[key]
            if isinstance(found, str):
                return {found: None}
            if isinstance(found, list):
                return dict.fromkeys(cast(list[Any], found))
            return cast(Doc, found)
    return {}


def is_capability(doc: Doc) -> bool:
    return "workflow_call" in triggers(doc)


def jobs(doc: Doc) -> Doc:
    return cast(Doc, doc.get("jobs", {}))


def check_names(doc: Doc) -> list[str]:
    # A consumer's required context is its own job id, then the called job's name. Where a job
    # declares no name GitHub falls back to its id, so that is what a consumer would have to require.
    return sorted(str(job.get("name", job_id)) for job_id, job in jobs(doc).items())


def declared_inputs(doc: Doc) -> set[str]:
    call: Any = triggers(doc).get("workflow_call") or {}
    return {str(name) for name in cast(Doc, call).get("inputs", {})}


def action_inputs(doc: Doc) -> set[str]:
    return {str(name) for name in cast(Doc, doc.get("inputs", {}))}


def permission_blocks(doc: Doc) -> Iterator[tuple[str, Any]]:
    if "permissions" in doc:
        yield "workflow", doc["permissions"]
    for job_id, job in jobs(doc).items():
        if isinstance(job, dict) and "permissions" in cast(Doc, job):
            yield str(job_id), cast(Doc, job)["permissions"]


def blanket_permissions(doc: Doc) -> list[str]:
    # `permissions: read-all` names no scope, so it would compare equal to a capability demanding
    # nothing and pass the surface gate while granting the run everything.
    return [where for where, block in permission_blocks(doc) if not isinstance(block, dict)]


def permission_demand(doc: Doc) -> dict[str, str]:
    # What a caller must grant for the run to start: the highest level any block asks for. A called
    # job cannot exceed its caller, so the union is the demand rather than any single block.
    demand: dict[str, str] = {}
    for _, block in permission_blocks(doc):
        if not isinstance(block, dict):
            continue
        for scope, level in cast(Doc, block).items():
            if LEVELS.get(str(level), -1) > LEVELS.get(demand.get(str(scope), "none"), 0):
                demand[str(scope)] = str(level)
    return {scope: level for scope, level in demand.items() if level != "none"}


def values_at(node: Any, key: str, path: str = "") -> Iterator[tuple[str, str]]:
    # One walker for both the interpolation gate and the pin gate: naming the key rather than the
    # place it may appear means a value nested somewhere new is still read.
    if isinstance(node, dict):
        for k, value in cast(Doc, node).items():
            here = f"{path}.{k}" if path else str(k)
            if k == key and isinstance(value, str):
                yield here, value
            else:
                yield from values_at(value, key, here)
    elif isinstance(node, list):
        for index, value in enumerate(cast(list[Any], node)):
            yield from values_at(value, key, f"{path}[{index}]")


def every_yaml() -> Iterator[tuple[str, Doc]]:
    for path in workflow_paths() + action_paths():
        yield str(path.relative_to(REPO)), load(path)
