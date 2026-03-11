"""Git and GitHub CLI subprocess operations."""

from __future__ import annotations

import os
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


def create_fix_pr(charm_path: str, state: dict) -> str | None:
    git(["config", "user.name", "charmarr-parrot[bot]"], cwd=charm_path)
    git(
        [
            "config",
            "user.email",
            "266865120+charmarr-parrot[bot]@users.noreply.github.com",
        ],
        cwd=charm_path,
    )

    source_branch = (
        os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=charm_path).stdout.strip()
    )
    target_branch = source_branch
    hex_id = secrets.token_hex(4)
    fix_branch = f"parrot/{source_branch}-{hex_id}"

    fn_name = state.get("_fn_name", "")
    collection = fn_name.removeprefix("run_") if fn_name else "unknown"
    title = f"fix({collection}): auto-healed by parrot [{hex_id}]"

    observation = state.get("_observation")
    reason = getattr(observation, "reason", "") if observation else ""
    rule = getattr(observation, "rule", "") if observation else ""
    body = f"Automated fix by parrot CI auto-healing.\n\n**Collection:** `{collection}`"
    if rule:
        body += f"\n**Rule:** `{rule}`"
    if reason:
        body += f"\n\n**What was fixed:**\n{reason}"

    git(["add", "."], cwd=charm_path)
    git(["stash", "push", "--include-untracked", "-m", "parrot-fix"], cwd=charm_path)
    git(["fetch", "origin", source_branch], cwd=charm_path)
    git(["checkout", "-B", fix_branch, f"origin/{source_branch}"], cwd=charm_path)

    stash_pop = git(["stash", "pop"], cwd=charm_path)
    if stash_pop.returncode != 0:
        logger.warning("Could not apply fix to feature branch — conflict likely")
        return None
    git(["add", "."], cwd=charm_path)

    commit = git(["commit", "-m", f"{title} [skip ci]"], cwd=charm_path)
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
            title,
            "--body",
            body,
            "--base",
            target_branch,
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


def comment_on_pr(charm_path: str, pr_number: str, body: str) -> None:
    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body", body],
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
