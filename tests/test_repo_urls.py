import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Every name in the tree is already `github-actions`, the destination one, while these URLs still
# carry the staging repository's `-new` suffix because a URL has to resolve today. GitHub redirects
# a renamed repository's URLs, so a stale one keeps working and nothing announces the drift — hence
# a gate rather than a note. The remote is the only offline authority on what this repository is
# called; CI's checkout sets it to the same thing.
URL_OWNER_REPO = re.compile(r"https://github\.com/(turboBasic/[A-Za-z0-9._-]+)")

# The README explains the mismatch and names both repositories on purpose; it is the artefact that
# answers what this repository is for.
EXEMPT: dict[str, str] = {
    "README.md": "states the staging arrangement, so it names the destination and the staging repo",
}


def current_slug() -> str:
    url = subprocess.run(
        ["git", "-C", str(REPO), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return url.removesuffix(".git").split("github.com/", 1)[1]


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def test_every_self_url_names_the_repository_this_clone_actually_is() -> None:
    slug = current_slug()
    stale: list[str] = []
    for path in tracked_files():
        if path in EXEMPT or path.startswith((".specify/", ".claude/skills/speckit-")):
            continue
        text = (REPO / path).read_text(encoding="utf-8", errors="ignore")
        stale += [f"{path}: {m}" for m in URL_OWNER_REPO.findall(text) if m != slug]
    assert stale == [], f"URL names a repository other than {slug}: {stale}"


def test_every_exemption_carries_a_reason() -> None:
    assert all(reason.strip() for reason in EXEMPT.values())
