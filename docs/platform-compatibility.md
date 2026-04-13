# Platform Compatibility

## Goal

`woowa-mission-coach` must run on macOS, Linux, and Windows (including WSL).

## Principles

- The canonical entrypoint is a Python module or Python script, not a shell wrapper.
- `bin/` scripts are macOS/Linux convenience wrappers only.
- Agents should prefer the following forms when possible:

```bash
python3 -m scripts.workbench <command> ...
```

or

```bash
python3 scripts/workbench/cli.py <command> ...
```

## Current State

- `bin/` commands are bash-based.
- Core logic lives in Python modules and can run without shell wrappers.

## Recommendations

- Agent contracts and context JSON should store structured tool/action information rather than raw shell strings.
- Documentation examples should show both the `bin/` form and the Python entrypoint form.
