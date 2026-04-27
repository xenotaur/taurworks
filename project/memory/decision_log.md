# Decision Log

## 2026-04-27 — Adopt unified Taurworks command model

### Decision
Adopt one primary `taurworks` executable with two namespaces:

- `taurworks project ...`
- `taurworks dev ...`

### Rationale
- Avoid duplicated init/config behavior.
- Keep workspace activation responsibilities separate from repo workflow orchestration.
- Avoid global short-command collisions.
- Support XDG-style global config plus visible project-local and repo-local configuration.

### Consequences
- Existing top-level commands remain compatibility commands for now.
- `taurworks dev` should delegate to standard tools and project scripts.
- Implementation should proceed in small, reviewable phases.

## 2026-04-10 — LRH bootstrap initialization

### Inputs reviewed
- `README.md`
- `taurworks/cli.py`
- `taurworks/manager.py`
- `setup.py`
- Top-level repository file/directory layout

### Assumptions made
1. The authoritative project lifecycle behavior is encoded in `taurworks/cli.py` and `taurworks/manager.py`.
2. README's "suite of Unix utilities" framing remains valid, even as lifecycle tooling expands.
3. Minimal additive documentation is preferred over speculative architecture documents.

### Uncertainties recorded
- Unclear from repository how fast/fully the repo will converge from utility-suite roots to a project-system-centric product.
- Unclear whether non-Conda environment backends are intended.
- Unclear whether naming mismatch in repo directory creation (`camel_to_snake` in refresh vs raw project name in create) is intentional or transitional.

### Reasoning steps
1. Identify explicit behavior from CLI and manager source.
2. Separate direct facts from inferred direction.
3. Create only required `project/` files.
4. Encode uncertainty explicitly rather than resolve by speculation.
