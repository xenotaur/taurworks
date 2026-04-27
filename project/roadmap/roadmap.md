---
id: ROADMAP-INIT
title: Conservative Initial Roadmap
status: active
confidence: medium
---

# Roadmap

## Horizon framing
This roadmap is intentionally conservative and evidence-bound. It records likely next sequencing without committing to dates.

## Phase 1 — Stabilize current lifecycle surface
- Validate consistency of `create`, `refresh`, `activate`, and `projects` behavior.
- Clarify and document environment-creation paths (`--python`, `--packages`, `--file`).
- Add/expand tests for CLI argument handling and manager side effects.

## Phase 2 — Improve observability and operator confidence
- Improve status reporting for project health beyond simple listing.
- Document expected project directory invariants and recovery behavior.
- Reduce ambiguity around naming conventions (`project_name` vs `camel_to_snake` repo directory behavior).

## Phase 3 — Evaluate extension boundaries (non-binding)
- Decide whether non-Conda backends are in scope.
- Decide whether formal per-project configuration schema is needed.
- Decide long-term relationship between legacy utility scripts and project lifecycle tooling.

## Not committed
- No schedule, release milestones, or ownership commitments are asserted in this bootstrap roadmap.
