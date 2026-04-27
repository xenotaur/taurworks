# Agent Guardrails for Taurworks

## Do
- Prefer explicit, user-visible commands and files.
- Keep changes simple, inspectable, and reversible.
- Preserve conceptual separation between `taurworks project` and `taurworks dev`.
- Treat compatibility commands as in-scope until explicit migration guidance is documented.

## Do Not
- Do not install short global commands like `tw`, `td`, or `dev` by default.
- Do not silently mutate shell startup files.
- Do not silently publish packages, install hooks, delete files, or change environments.
- Do not turn `taurworks dev` into a replacement build/lint/test/package/release system.
- Do not remove or rename current commands before an explicit migration path exists.

## Shell activation guardrail
- Keep shell activation explicit and inspectable.
- Account for subprocess boundaries: command subprocesses cannot directly mutate the parent shell environment.

## Safety posture
- Use conservative defaults for destructive or environment-changing operations.
- Prefer dry-run, explain, and diagnostic-friendly behavior where practical.
