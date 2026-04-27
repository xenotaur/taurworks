# Safety Guardrails

## Safety constraints
- Do not silently mutate user shell profiles (`.bashrc`, `.bash_profile`, etc.).
- Keep activation explicit via printed `source <.../project-setup.source>` guidance.
- Distinguish commands that print instructions from commands that modify state.
- Prefer idempotent filesystem operations that avoid destructive deletes.
- Handle missing external tools (e.g., Conda) with clear operator feedback.

## Shell-integration constraints
- Subprocess commands cannot directly mutate the parent shell environment; documentation should not imply otherwise.
- Commands that require shell-state changes should emit explicit instructions for the operator to run.
- Any command that writes files in user directories or config locations should be explicit, documented, and reversible.

## Risk areas to watch
- Environment creation commands that may fail mid-flow.
- Divergence between `create` and `refresh` directory naming behavior.
- Assumptions about workspace path and permissions.
- Repository discovery assumptions that could target the wrong working tree.
- Workflow commands that might execute destructive clean/reset behavior without explicit confirmation.
