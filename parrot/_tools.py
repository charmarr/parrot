"""Tool registrations for parrot Theow instance."""

from __future__ import annotations

import subprocess
from pathlib import Path

from theow.tools import list_directory, read_file, run_command, write_file

from parrot._engine import parrot

_LINT_ALLOWED_CMDS = ("ruff ", "codespell ")
_STATIC_ALLOWED_CMDS = ("pyright ",)
_TEST_ALLOWED_CMDS = ("pytest ", "coverage ")


def _run_restricted_cmd(
    cmd: str, cwd: str | None, allowed_cmds: tuple[str, ...], timeout: int
) -> dict:
    if not any(cmd.startswith(prefix) for prefix in allowed_cmds):
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Blocked: '{cmd}' not allowed. Permitted: {', '.join(allowed_cmds)}",
        }
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


parrot.tool()(read_file)
parrot.tool()(write_file)
parrot.tool()(run_command)
parrot.tool()(list_directory)


@parrot.tool()
def write_charm_file(path: str, content: str) -> str:
    """Write content to a file in the charm workspace. PR review is the safety net."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written {len(content)} bytes to {path}"


@parrot.tool()
def run_lint_cmd(cmd: str, cwd: str | None = None) -> dict:
    """Run a lint command. Allows: ruff, codespell."""
    return _run_restricted_cmd(cmd, cwd, _LINT_ALLOWED_CMDS, timeout=120)


@parrot.tool()
def run_static_cmd(cmd: str, cwd: str | None = None) -> dict:
    """Run a static analysis command. Allows: pyright."""
    return _run_restricted_cmd(cmd, cwd, _STATIC_ALLOWED_CMDS, timeout=120)


@parrot.tool()
def run_test_cmd(cmd: str, cwd: str | None = None) -> dict:
    """Run a test command. Allows: pytest, coverage."""
    return _run_restricted_cmd(cmd, cwd, _TEST_ALLOWED_CMDS, timeout=300)


@parrot.tool()
def run_juju_cmd(cmd: str) -> dict:
    """Run any juju command against the test model."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=120
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@parrot.tool()
def run_kubectl_cmd(cmd: str) -> dict:
    """Run any kubectl command against the test cluster."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=120
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@parrot.tool()
def pack_charm(charm_path: str) -> dict:
    """Pack the charm to a separate build path (parrot-build/), not overwriting $CHARM_PATH."""
    build_dir = Path(charm_path).parent / "parrot-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["charmcraft", "pack", "--project-dir", charm_path, "--output-dir", str(build_dir)],
        capture_output=True, text=True, timeout=600,
    )
    charm_files = list(build_dir.glob("*.charm"))
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "charm_file": str(charm_files[0]) if charm_files else "",
    }


@parrot.tool()
def retry_test(suite: str, charm_path: str) -> dict:
    """Re-run a test against the existing model to check for transient failure."""
    result = subprocess.run(
        ["tox", "-e", "integration", "--", "-k", suite],
        cwd=charm_path, capture_output=True, text=True, timeout=600,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@parrot.tool()
def git_diff(cwd: str | None = None) -> str:
    """Show git diff of the current workspace changes."""
    result = subprocess.run(
        ["git", "diff"], cwd=cwd, capture_output=True, text=True, timeout=30
    )
    return result.stdout
