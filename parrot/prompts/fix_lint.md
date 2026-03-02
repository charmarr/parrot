## Context

Charm path: {charm_path}
Exit code: {exit_code}

### Tox stdout
```
{stdout}
```

### Tox stderr
```
{stderr}
```

## Before You Start

Call `_search_observations("{charm_path}")` and WAIT for the result before
doing anything else. If a previous attempt already failed with the same error,
call `_give_up()` with no reason. If a previous attempt has useful lessons,
apply them.

## Task

Fix the lint errors shown above. These are errors that the deterministic
ruff/codespell auto-fixers couldn't handle.

## Strategy

1. Parse the error output to identify failing files and line numbers
2. Read each failing file with `read_file`
3. Fix the issues in the code
4. Write fixed files with `write_charm_file`
5. Verify with `run_lint_cmd("ruff check {charm_path}")` and/or `run_lint_cmd("codespell {charm_path}")`
6. Review your changes with `git_diff`
7. Call `_done()` when all lint errors are resolved

## Constraints

- Fix the code to satisfy the linter — prefer fixing the code over suppressing rules
- `# noqa` or rule disables are a last resort, only when fixing the code is not possible
- `run_lint_cmd` allows: `ruff`, `codespell`
- All commands must use `cwd="{charm_path}"`
- Make minimal changes — fix only the reported errors

## When to Give Up

If the error requires an architectural change or the message is unclear,
call `_give_up()` with a description of what you observed.
