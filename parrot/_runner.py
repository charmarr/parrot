"""Marked tox runner functions for each collection."""

from __future__ import annotations

import subprocess
from pathlib import Path

from parrot._engine import parrot, setup, setup_itest, teardown


def _tox_context(charm_path: str, exc: Exception, collection: str) -> dict:
    ctx: dict = {"collection": collection, "charm_path": charm_path}
    if isinstance(exc, subprocess.CalledProcessError):
        ctx["stdout"] = exc.stdout or ""
        ctx["stderr"] = exc.stderr or ""
        ctx["exit_code"] = exc.returncode
    return ctx


def _itest_context(
    charm_path: str, suite: str, exc: Exception, collection: str, model: str
) -> dict:
    ctx = _tox_context(charm_path, exc, collection)
    ctx["suite"] = suite
    ctx["model"] = model
    return ctx


def _run_tox(env: str, charm_path: str, extra_args: list[str] | None = None) -> None:
    cmd = ["tox", "-e", env]
    if extra_args:
        cmd += ["--", *extra_args]
    subprocess.run(cmd, cwd=charm_path, check=True, capture_output=True, text=True)


@parrot.mark(
    context_from=lambda charm_path, exc: _tox_context(charm_path, exc, "lint"),
    max_retries=3,
    tags=["lint", "ruff", "codespell"],
    fallback=True,
    explorable=False,
    collection="lint",
    setup=setup,
    teardown=teardown,
)
def run_lint(charm_path: str) -> None:
    _run_tox("lint", charm_path)


@parrot.mark(
    context_from=lambda charm_path, exc: _tox_context(charm_path, exc, "static"),
    max_retries=3,
    tags=["static", "pyright"],
    fallback=True,
    explorable=False,
    collection="static",
    setup=setup,
    teardown=teardown,
)
def run_static(charm_path: str) -> None:
    _run_tox("static", charm_path)


@parrot.mark(
    context_from=lambda charm_path, exc: _tox_context(charm_path, exc, "unit"),
    max_retries=3,
    tags=["unit", "pytest"],
    fallback=True,
    explorable=False,
    collection="unit",
    setup=setup,
    teardown=teardown,
)
def run_unit(charm_path: str) -> None:
    _run_tox("unit", charm_path)


@parrot.mark(
    context_from=lambda charm_path, suite, exc: _itest_context(
        charm_path, suite, exc, "itest",
        f"parrot-{Path(charm_path).name}-{Path(suite).stem}",
    ),
    max_retries=3,
    tags=["itest", "integration", "juju"],
    fallback=True,
    explorable=False,
    collection="itest",
    setup=setup_itest,
    teardown=teardown,
)
def run_itest(charm_path: str, suite: str) -> None:
    model = f"parrot-{Path(charm_path).name}-{Path(suite).stem}"
    _run_tox(
        "integration", charm_path,
        extra_args=["-k", suite, "--keep-models", "--model", model],
    )
