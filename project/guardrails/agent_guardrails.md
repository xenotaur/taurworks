# Agent Guardrails for Taurworks

## Do
- Prefer explicit, user-visible commands and files.
- Preserve cross-platform behavior for macOS/Linux.
- Keep changes simple and inspectable.
- Treat CLI behavior in `taurworks/cli.py` and `taurworks/manager.py` as primary signals.

## Do Not
- Do not auto-activate environments in user shells.
- Do not silently mutate shell startup files.
- Do not introduce hidden state outside declared project directories.
- Do not assume features (plugins, schema, status APIs) that are not present.
- Do not overfit to one OS-specific workaround.

## Inference discipline
- Label inferred statements with wording such as "Appears to", "Likely", or "Unclear from repository".
- If conflicting signals appear, document both interpretations instead of silently choosing one.
