---
id: PRINCIPLES-CORE
title: Taurworks Working Principles
status: active
---

# Principles

1. **Explicit over implicit automation**
   - Prefer commands and generated files that users can inspect and run directly.
2. **Idempotent project lifecycle operations**
   - `refresh` should safely restore missing project components without destructive side effects.
3. **Local-first, filesystem-visible state**
   - Project setup state should live in predictable directories (`<workspace>/<project>/.taurworks`).
4. **Conservative behavior changes**
   - Preserve current CLI ergonomics and avoid hidden shell mutations.
5. **Inference discipline for planning artifacts**
   - Distinguish observed behavior from inferred roadmap direction.

## Grounding Notes
- These principles are grounded in current CLI verbs and manager behavior in `taurworks/cli.py` and `taurworks/manager.py`, plus existing LRH notes under `project/`.
