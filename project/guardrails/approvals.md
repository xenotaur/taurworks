# Approval Guardrails

## Default approval posture
- Documentation-only LRH artifact updates under `project/` may proceed with normal review.
- Any source-code changes outside `project/` require explicit maintainer review.

## Escalation triggers
- Changes that alter CLI behavior or command semantics.
- Changes that write to user shell startup files or alter activation behavior.
- Changes that broaden operational cost/risk (e.g., large environment installs by default).

## Evidence required for approvals
- Reproduction steps and expected/observed behavior.
- Clear scope statement and rollback strategy where relevant.
