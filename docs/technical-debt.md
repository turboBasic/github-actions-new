# Technical debt

Deliberate shortcuts and known-wrong states accepted for now.

An entry belongs here when all three hold:

- It is a real defect or a corner deliberately cut, not a preference.
- It states a **condition this repository can answer** — a file, a version, a command's output — so a
  sweep can tell whether it still applies without asking anyone.
- Nobody is going to do it. Work someone will actually do is an issue; a plan's leftover task is a task
  in the next phase. Only what is knowingly left alone lands here.

An entry that stops holding is deleted rather than annotated — git remembers. An entry that turns into
work becomes an issue and the row goes.

| ID | What | Condition that clears it |
| --- | --- | --- |
| TD-001 | `.github/actionlint.yaml` ignores one actionlint message, because actionlint rejects the `$/` same-repository call form that GitHub recommends and zizmor's `self-repository` audit demands. Two gates contradict each other and the stale verdict is the one silenced | `actionlint --version` reports a release that accepts `uses: $/.github/workflows/x.yml`. Delete the `paths:` entry and the file with it |
