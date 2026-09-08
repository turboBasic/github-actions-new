import sys
from pathlib import Path

# The decision unit lives beside the action that runs it, and a hyphen in that directory name means it
# is not importable as a package. pyright reaches it through `extraPaths` in pyproject.toml.
sys.path.insert(0, str(Path(__file__).parent.parent / "actions" / "release-decisions"))
