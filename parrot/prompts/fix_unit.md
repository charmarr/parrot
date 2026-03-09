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

Fix the failing unit tests shown above.

## Strategy

1. Parse the pytest traceback to identify the failing test and assertion
2. Read the test file with `read_file` (path is in the traceback)
3. Read the source file being tested with `read_file` (path is in imports or traceback)
4. When you need to understand how a patched object works, what a base class
   provides, or how a dependency behaves — use `search_code` to find it.
   Charmarr charms inherit from shared base classes in charmarr-lib and the
   test may be failing because of a change in the interface.
5. Determine whether source or test is wrong:
   - Source changed, test outdated → fix the test
   - Source has a bug → fix the source
   - Both plausible → prefer fixing the test
6. Write fixed files with `write_charm_file`
7. Verify with `run_test_cmd("pytest {charm_path}/tests/unit -x")`
8. Review your changes with `git_diff`
9. Call `_done()` when all tests pass

## Tool Usage

- **`read_file`**: Use ONLY for files whose path you already know (from the
  traceback, imports, or patch targets). Do NOT read files speculatively.
- **`search_code`**: Use for ALL discovery — finding class definitions, method
  signatures, mock targets, fixture implementations, shared test helpers. This
  searches the entire codebase including charmarr-lib. Using `search_code`
  instead of reading random files saves tool calls and finds the right code faster.
- **GOOD**: test patches `src.charm.SomeClient` and you need its interface
  → `search_code("class SomeClient")` → read that specific file
- **BAD**: test patches something unfamiliar → read every file in `src/`
  hoping to find it

## Constraints

- `run_test_cmd` allows: `pytest`, `coverage`
- When in doubt, fix the test rather than the source
- Do NOT delete failing tests — fix them
- All commands must use `cwd="{charm_path}"`
- Make minimal changes — fix only the reported failures
- NEVER modify files under `lib/` — these are third-party charm libraries we do not own
- ONLY modify files under `{charm_path}` — never touch other charms or directories outside it

## Charmarr Patterns

- Unit tests use `pytest` with `unittest.mock`
- Charm tests patch `ops` framework objects (harness, events, etc.)
- Source code in `src/charm.py` and `src/` modules
- Tests in `tests/unit/`

## When to Give Up

If the failure requires understanding external services or Juju behavior
that can't be determined from the code, call `_give_up()` with a description
of what you observed and which test is failing.
