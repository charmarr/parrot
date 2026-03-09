import subprocess

from theow import action


@action("codespell_fix")
def codespell_fix(charm_path: str) -> dict:
    """Run codespell --write-changes to auto-fix misspellings."""
    result = subprocess.run(
        ["uvx", "codespell", "--write-changes", charm_path],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return {"status": "ok", "message": "codespell auto-fix applied"}

    return {
        "status": "error",
        "message": "codespell auto-fix ran but issues may remain",
        "stderr": result.stderr,
    }
