# Safety Guardrails

## Safety constraints
- Do not silently mutate user shell profiles (`.bashrc`, `.bash_profile`, etc.).
- Keep activation explicit via printed `source <.../project-setup.source>` guidance.
- Prefer idempotent filesystem operations that avoid destructive deletes.
- Handle missing external tools (e.g., Conda) with clear operator feedback.

## Risk areas to watch
- Environment creation commands that may fail mid-flow.
- Divergence between `create` and `refresh` directory naming behavior.
- Assumptions about workspace path and permissions.
