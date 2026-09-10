import sys
from pathlib import Path

# Each decision unit lives beside the action that runs it, and a hyphen in that directory name means
# neither is importable as a package. pyright reaches both through `extraPaths` in pyproject.toml.
ACTIONS = Path(__file__).parent.parent / "actions"
sys.path.insert(0, str(ACTIONS / "release-decisions"))
sys.path.insert(0, str(ACTIONS / "ruleset-decisions"))
