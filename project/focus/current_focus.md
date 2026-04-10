---
updated: 2026-04-10
basis: repository_inspection
confidence: medium
---

# Current Focus (Appears)

Based on current code layout and commands, Taurworks appears focused on stabilizing a basic project lifecycle:
1. Create project scaffolding and environment.
2. Refresh/repair project setup.
3. Provide explicit activation instructions.
4. Surface project inventory and basic health via listing.

## Signals
- Manager logic centers on filesystem + Conda setup.
- CLI exposes lifecycle-oriented verbs (`create`, `refresh`, `projects`, `activate`).
- Activation is explicit (printed command), not automatic.

## Unclear from repository
- Whether plugin/extensibility is an active development track.
- Whether a formal configuration schema is planned for projects.
- Whether this lifecycle will remain Conda-only.
