"""Marked tox runner functions for each collection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from parrot._engine import parrot
from parrot._lifecycle import setup, setup_itest, teardown


def _tox_context(charm_path: str, exc: Exception, collection: str) -> dict:
    ctx: dict = {"collection": collection, "charm_path": charm_path}
    if isinstance(exc, subprocess.CalledProcessError):
        ctx["stdout"] = exc.stdout or ""
        ctx["stderr"] = exc.stderr or ""
        ctx["exit_code"] = exc.returncode
    return ctx


def _integration_context(
    charm_path: str, suite: str, exc: Exception, collection: str, model: str
) -> dict:
    ctx = _tox_context(charm_path, exc, collection)
    ctx["suite"] = suite
    ctx["model"] = model
    return ctx


def _run_tox(env: str, charm_path: str, extra_args: list[str] | None = None) -> None:
    cmd = ["uvx", "tox", "-e", env]
    if extra_args:
        cmd += ["--", *extra_args]
    proc = subprocess.Popen(
        cmd,
        cwd=charm_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: list[str] = []
    for line in proc.stdout:
        sys.stdout.write(line)
        lines.append(line)
    rc = proc.wait()
    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd, "".join(lines), "")


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
    context_from=lambda charm_path, suite, exc: _integration_context(
        charm_path,
        suite,
        exc,
        "integration",
        f"parrot-{Path(charm_path).name}-{Path(suite).stem}".replace("_", "-"),
    ),
    max_retries=3,
    tags=["integration", "juju"],
    fallback=True,
    explorable=False,
    collection="integration",
    setup=setup_itest,
    teardown=teardown,
)
def run_integration(charm_path: str, suite: str) -> None:
    model = f"parrot-{Path(charm_path).name}-{Path(suite).stem}".replace("_", "-")
    _run_tox(
        "integration",
        charm_path,
        extra_args=["-k", suite, "--keep-models", "--model", model],
    )
