# Design Documents

This folder contains Taurworks control-plane design notes.

Current design priorities:

- keep `project_root` and relative `working_dir` semantics stable;
- preserve `taurworks project activate --print` as read-only activation guidance;
- treat `tw activate` as shell-mutating only when provided by the explicitly sourced `taurworks-shell.sh` function;
- classify legacy `Admin/project-setup.source` projects for migration planning rather than automatic fallback sourcing;
- introduce broader `taurworks dev ...` behavior only through small, safe, read-only scaffolds before workflow automation.

Key documents:

- `design.md` for the overall product/control-plane design;
- `unified_command_model.md` for command namespace intent;
- `config_model.md` for configuration and path semantics;
- `activation_extension.md` for deferred activation-extension design topics.
