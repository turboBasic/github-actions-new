import re

from capabilities import every_yaml, values_at

# Every context whose value is chosen outside this repository, with why. An injection here runs with
# whatever token the job holds, and a token that has been used cannot be un-used. These reach the
# code that uses them through `env:`, where the shell reads them as data.
FORBIDDEN: dict[str, str] = {
    "github.event": "the event payload carries the commit subject, the pull request title and the body, all written by whoever opened it",
    "inputs": "a caller names its own tasks, paths, hook stages and type lists, and every one of those is text this repository never sees",
    "github.head_ref": "a branch name, chosen by whoever opened the pull request",
    "github.base_ref": "a branch name, and a fork chooses which one it points at",
    "github.ref_name": "a branch or tag name, so text from outside this repository",
}

INTERPOLATION = re.compile(r"\$\{\{(.+?)\}\}", re.DOTALL)
# A context ends at anything that cannot continue an identifier path, so `inputs` does not match
# `inputs_of_our_own` and `github.event` does not match `github.eventual`.
BOUNDARY = re.compile(r"[^A-Za-z0-9_.\[\]'\"-]")


def contexts(script: str) -> list[str]:
    return [" ".join(m.group(1).split()) for m in INTERPOLATION.finditer(script)]


def offences(expression: str) -> list[str]:
    padded = BOUNDARY.sub(" ", f" {expression} ")
    return [name for name in FORBIDDEN if f" {name}." in padded or f" {name} " in padded]


def test_no_run_block_interpolates_caller_controlled_text() -> None:
    found: list[str] = []
    for where, doc in every_yaml():
        for path, script in values_at(doc, "run"):
            for expression in contexts(script):
                found += [
                    f"{where} at {path}: ${{{{ {expression} }}}} — {FORBIDDEN[name]}"
                    for name in offences(expression)
                ]
    assert found == [], "caller-controlled text interpolated into a command line: " + "; ".join(
        found
    )


def test_every_forbidden_context_carries_a_reason() -> None:
    assert all(reason.strip() for reason in FORBIDDEN.values())


def test_the_gate_reads_an_interpolation_it_is_given() -> None:
    # Pre-flight the matcher, or a change to it that stops matching anything reports green over a
    # tree full of injections.
    assert offences("github.event.pull_request.title") == ["github.event"]
    assert offences("format('{0}', inputs.lint-task)") == ["inputs"]
    assert offences("github.head_ref") == ["github.head_ref"]
    assert offences("github.workflow") == []
    assert offences("env.LINT_TASK") == []
    assert contexts("mise run ${{ inputs.lint-task }}\n") == ["inputs.lint-task"]
