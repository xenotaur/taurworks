# Cost Guardrails

## Cost model (current)
- Primary costs are local developer time and machine resources (disk/network/CPU) during Conda environment creation.

## Guardrails
- Avoid adding heavyweight default dependencies without explicit opt-in.
- Prefer incremental improvements over broad rewrites.
- Keep bootstrap/project metadata docs concise and maintainable.

## Unknowns
- No formal budget, runtime SLA, or cost envelope is documented in the repository.
