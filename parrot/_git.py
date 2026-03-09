"""Git and GitHub CLI subprocess operations."""

from __future__ import annotations

import secrets
import subprocess

from theow._core._logging import get_logger

logger = get_logger("parrot.git")


def git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        logger.warning("git failed", args=args, stderr=result.stderr.strip())
    return result


def stash_checkpoint(state: dict, charm_path: str, attempt: int) -> None:
    result = git(
        ["stash", "push", "--include-untracked", "-m", "parrot-recovery"],
        cwd=charm_path,
    )
    stash_created = "No local changes" not in result.stdout
    state["_stash_created"] = stash_created

    if stash_created:
        git(["stash", "apply"], cwd=charm_path)

    logger.debug("Stash checkpoint", attempt=attempt, stash_created=stash_created)


def stash_drop(charm_path: str) -> None:
    git(["stash", "drop"], cwd=charm_path)


def stash_restore(charm_path: str, dry_run: bool) -> None:
    if not dry_run:
        git(["checkout", "--", "."], cwd=charm_path)
        git(["clean", "-fd"], cwd=charm_path)


def create_fix_pr(charm_path: str) -> str | None:
    git(["config", "user.name", "parrot[bot]"], cwd=charm_path)
    git(["config", "user.email", "parrot-bot@charmarr.dev"], cwd=charm_path)

    base_branch = git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=charm_path
    ).stdout.strip()
    fix_branch = f"parrot/{base_branch}-{secrets.token_hex(4)}"

    git(["checkout", "-B", fix_branch], cwd=charm_path)
    git(["add", "-A"], cwd=charm_path)

    commit = git(["commit", "-m", "fix: auto-healed by parrot"], cwd=charm_path)
    if commit.returncode != 0:
        return None

    push = git(["push", "-u", "origin", fix_branch], cwd=charm_path)
    if push.returncode != 0:
        return None

    pr_result = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            "fix: auto-healed by parrot",
            "--body",
            "Automated fix by parrot CI auto-healing.",
            "--base",
            base_branch,
        ],
        cwd=charm_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if pr_result.returncode != 0:
        logger.warning("gh pr create failed", stderr=pr_result.stderr.strip())
        return None

    return pr_result.stdout.strip() or None


def post_observations(charm_path: str, observations: str) -> None:
    pr_number = find_pr_number(charm_path)
    if not pr_number:
        logger.warning("No PR found to post observations")
        return

    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body", observations],
        cwd=charm_path,
        capture_output=True,
        text=True,
        check=False,
    )


def find_pr_number(charm_path: str) -> str | None:
    result = subprocess.run(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        cwd=charm_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None
