import ast
import sys
from pathlib import Path

ACTIONS = Path(__file__).parent.parent / "actions"


def imported_roots(source: str) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        # A relative import resolves against a package, and a hyphen in the directory beside the action
        # means there is none. It is reported as `.`, which no standard-library name matches.
        if isinstance(node, ast.ImportFrom):
            roots.add(node.module.split(".")[0] if node.level == 0 and node.module else ".")
    return roots


def test_every_module_a_composite_action_runs_imports_only_the_standard_library() -> None:
    modules = sorted(ACTIONS.glob("*/*.py"))
    assert modules, "no action module was read, so this gate holds no import at all"
    foreign = [
        f"{module.parent.name}/{module.name} imports {name}"
        for module in modules
        for name in sorted(imported_roots(module.read_text(encoding="utf-8")))
        if name not in sys.stdlib_module_names
    ]
    assert foreign == [], (
        f"an action module imports outside the standard library: {foreign}. Nothing installs a "
        "dependency before the module runs, and the interpreter is whichever `python3` the caller's own "
        "configuration left on the runner — so there is no resolution step to fail loudly here, only an "
        "ImportError in a consumer's job. Move the work to the suite, or into the action's own steps"
    )


def test_the_import_walk_reads_the_forms_it_is_given() -> None:
    # Pre-flight the walk, or a change that stops it finding imports reports green over a module
    # importing whatever it likes.
    assert imported_roots("import os\nimport a.b.c\n") == {"os", "a"}
    assert imported_roots("from collections.abc import Iterable\n") == {"collections"}
    assert imported_roots("def f() -> None:\n    import yaml\n") == {"yaml"}
    assert imported_roots("from . import sibling\n") == {"."}
    assert "." not in sys.stdlib_module_names
