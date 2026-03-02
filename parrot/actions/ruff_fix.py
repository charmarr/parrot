import subprocess

from theow import action


@action("ruff_fix")
def ruff_fix(charm_path: str) -> dict:
    """Run ruff check --fix and ruff format to auto-fix lint violations."""
    check = subprocess.run(
        ["ruff", "check", "--fix", charm_path],
        capture_output=True, text=True,
    )
    fmt = subprocess.run(
        ["ruff", "format", charm_path],
        capture_output=True, text=True,
    )

    if check.returncode == 0 and fmt.returncode == 0:
        return {"status": "ok", "message": "ruff auto-fix applied"}

    return {
        "status": "error",
        "message": "ruff auto-fix ran but issues may remain",
        "check_stderr": check.stderr,
        "format_stderr": fmt.stderr,
    }
