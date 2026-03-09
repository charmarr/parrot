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

Fix the pyright type errors shown above.

## Strategy

1. Parse pyright output — each error shows `file:line:col: error message`
2. Read the failing files with `read_file` (you know the exact paths from the output)
3. When the error references a type, base class, interface, or symbol you don't
   have the definition for — use `search_code` to find it. This is critical:
   charmarr charms import from `charmarr-lib` and `ops`, and type definitions
   are spread across packages. `search_code` finds them instantly.
4. Fix type annotations, imports, or signatures
5. Write fixed files with `write_charm_file`
6. Verify with `run_static_cmd("pyright {charm_path}")`
7. Review your changes with `git_diff`
8. Call `_done()` when all type errors are resolved

## Tool Usage

- **`read_file`**: Use ONLY for files whose path you already know (from error
  output or imports). Do NOT read files speculatively to "explore" the codebase.
- **`search_code`**: Use for ALL discovery — finding type definitions, base
  classes, function signatures, module structure, related code. This searches
  the entire codebase including charmarr-lib. Using `search_code` instead of
  reading random files saves tool calls and finds the right code faster.
- **GOOD**: error says `Argument of type "X" cannot be assigned to parameter of type "Y"`
  → `search_code("class Y")` to find the definition → read that file → fix
- **BAD**: error mentions an unknown type → read `__init__.py`, then `models.py`,
  then `types.py` hoping to stumble on it

## Constraints

- Fix type annotations, do NOT change program logic
- Prefer proper types over `Any` — use specific types, unions, or protocols
- `# type: ignore` is a last resort, only when the error is a false positive
- All commands must use `cwd="{charm_path}"`
- Make minimal changes — fix only the reported errors
- NEVER modify files under `lib/` — these are third-party charm libraries we do not own
- ONLY modify files under `{charm_path}` — never touch other charms or directories outside it

## When to Give Up

If the type error originates from an upstream dependency or requires changes
to charmarr-lib, call `_give_up()` with a description of the type error and
which module it comes from.
