# Design Documents

This folder contains Taurworks control-plane design notes.

Current design priorities:

- keep `project_root` and relative `working_dir` semantics stable;
- preserve `taurworks project activate --print` as read-only activation guidance;
- treat `tw activate` as shell-mutating only when provided by the explicitly sourced `taurworks-shell.sh` function;
- classify legacy `Admin/project-setup.source` projects for migration planning rather than automatic fallback sourcing;
- design and implement `taurworks legacy inspect`/`legacy migrate` as the remaining Phase 2 declarative-activation work (`[activation].message`, `[activation.environment] type = "conda"`, and `[activation.exports]` are already implemented), and separately design trusted hooks — a distinct future phase, not part of declarative activation — only after legacy inspect/migrate has been dogfooded, deferred behind explicit opt-in;
- introduce broader `taurworks dev ...` behavior only through small, safe steps beyond the current read-only scaffold (`dev where`, `dev status`) before workflow automation.

XDG-style global config, the explicit workspace root, and the global project registry described in `config_model.md` are implemented, not just documented.

Key documents:

- `design.md` for the overall product/control-plane design;
- `unified_command_model.md` for command namespace intent;
- `config_model.md` for configuration, global workspace/registry plans, and path semantics;
- `activation_extension.md` for the Phase 2 declarative activation config design, Conda-only initial environment plan, export safety rules, legacy migration path, and deferred explicit trusted-hook design topics.
- `shell_helper_refresh.md` for the proposed `tw shell refresh` command and passive staleness-detection design that fixes the stale-shell-helper problem (sourced `tw` silently running behavior from before the last package upgrade).
- `packaging_and_install.md` for the public-release packaging/install design: the proposed `taurworks setup` command, splitting `bin/`'s unrelated legacy dotfile material out of the repo, a Conda PATH-loss diagnostic in `tw`, and gating `manager.py`'s unconditional progress narration behind a `--debug`/`TAURWORKS_DEBUG` flag.
