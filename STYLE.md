# Taurworks STYLE GUIDE

This document defines the coding, packaging, and contribution conventions for the Taurworks project.

Its purpose is to make the codebase easier to read, review, maintain, and extend, while keeping pull requests narrow and low-noise.

## TL;DR — The 10 Rules of Taurworks

1. **Keep changes small and scoped**
   Do not modify unrelated code.

2. **Prefer clarity over cleverness**
   Simple, explicit code wins.

3. **Import modules, not members**
   Use `from package import module`, then `module.function()`.

4. **Make behavior deterministic**
   Seed randomness; avoid time-dependent logic in tests.

5. **Write and pass tests**
   Use `unittest`; all tests must pass before merging.

6. **Pass lint and formatting**
   Code must pass `ruff` and `black`.

7. **Do not introduce noise in PRs**
   No drive-by refactors, formatting, or renaming.

8. **Keep scripts thin**
   No core logic in `scripts/`; use them as entry points only.

9. **Preserve structure and intent**
   Do not rewrite working code without a clear reason.

10. **When in doubt, be conservative**
    Prefer the smaller, clearer, more reviewable change.

## Order of Precedence

When there is any ambiguity or conflict, use the following order of precedence:

1. Project-specific Taurworks conventions in this document
2. Passing unit tests
3. Ruff lint compliance
4. Black formatting compliance
5. [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
6. [PEP 8](https://peps.python.org/pep-0008/) for issues not otherwise covered

The project-specific conventions in this document take precedence over more general style guidance.

## Philosophy

- Simple > clever
- Explicit > implicit
- Deterministic > stochastic
- Small diffs > large rewrites

In general, code and changes in Taurworks should favor:

- clarity and simplicity over cleverness
- explicitness over implicitness
- small, reviewable changes over broad rewrites
- consistency across the repository
- minimal semantic diffs
- readability over terseness
- deterministic over stochastic (especially in tests)

Contributors should avoid introducing unnecessary churn in files that are otherwise unrelated to the task at hand.

## Change Scope and Pull Request Discipline

Changes should be narrowly scoped to the task being performed.

Do not modify code that is unrelated to the change at hand merely to “clean it up,” “modernize it,” or “make it prettier.” This is especially important for AI-assisted edits.

Examples of changes that should generally be avoided unless they are directly required by the task:

- reformatting unrelated files
- changing imports in unrelated modules
- renaming unrelated variables or functions
- rewriting working code for stylistic reasons alone
- moving code between files without task-specific justification
- changing type annotation styles (e.g., `typing.Dict` → `dict`) unless required for consistency within the file


If a file must be touched for a real reason, keep unrelated edits in that file to an absolute minimum.

When a change would benefit from broader cleanup, that cleanup should usually be proposed as a separate follow-up change.

## Python Version and Environment

Taurworks should use a clearly documented Python version and a reproducible development setup.

Project tooling should work from the documented project root. Development dependencies should be installable in a standard way, preferably via `pyproject.toml`.

## Imports

### Core Import Policy

Taurworks prefers importing modules and submodules rather than importing individual members into the local namespace, inspired by the [Google Python Style Guide Imports section](https://google.github.io/styleguide/pyguide.html#s2.2-imports).

- Always use module-level imports:
  - `from package import module`
  - Then use: `module.function()`
- Do NOT import members directly unless unavoidable.
- Relative imports (`from . import module`) are NOT allowed unless required, and must include a comment explaining why.

Preferred:

```python
from taurworks import cli
from taurworks.utils import file_ops
```

Then refer to members through the imported module:

```python
cli.run_cli(...)
file_ops.atomic_write(...)
```

Generally disallowed:

```python
from taurworks.cli import run_cli
from taurworks.utils.file_ops import atomic_write
```

The goal is to keep symbol origins explicit and reduce namespace ambiguity.

### Relative Imports

Dot-relative imports such as the following are not allowed by default:

```python
from . import planner
from ..utils import file_ops
```

If a dot-relative import is truly necessary, it must be accompanied by a brief explanatory comment documenting why it is required.

This should be treated as an exception, not a normal practice.

### Import Grouping and Layout

Imports should follow standard grouping:

1. standard library imports
2. third-party imports
3. local package imports

Imports should normally appear at the top of the file.

Prefer one import per line unless a grouped import is clearly more readable and remains compliant with tooling.

### Allowed Common Exceptions

Common widely accepted alias imports are allowed where they improve readability, for example:

```python
import numpy as np
import pandas as pd
```

These should remain conventional and unsurprising.

Typing imports (e.g., `from typing import Any, Optional`) are allowed as a readability
exception, since qualifying all typing constructs with `typing.` may reduce clarity.


## Type Annotations

Taurworks targets Python 3.11. Type annotations should follow modern Python typing practices.

### Built-in Generic Types (Preferred)

Use built-in generic types for standard collections:

- `dict[str, int]` instead of `typing.Dict[str, int]`
- `list[str]` instead of `typing.List[str]`
- `tuple[int, str]` instead of `typing.Tuple[int, str]`
- `set[str]` instead of `typing.Set[str]`

Do NOT import container types from `typing` when a built-in generic is available.

Preferred:

```python
def load_index(path: pathlib.Path) -> dict[str, int]:
    ...
```

Disallowed:

```python
from typing import Dict

def load_index(path: pathlib.Path) -> Dict[str, int]:
    ...
```

### Typing Module Usage

The `typing` module should still be used for constructs that do not have built-in
equivalents, such as:

- `typing.Any`
- `typing.Optional`
- `typing.Union` (or `|` where appropriate)
- `typing.Protocol`
- `typing.TypedDict`
- `typing.TypeVar`
- `typing.TypeAlias`

### Import Style for Typing

The general rule “import modules, not members” applies, but **typing is a limited
exception** for readability.

Allowed:

```python
from typing import Any, Optional, Protocol
```

Also allowed:

```python
import typing
```

Then:

```python
def f(x: typing.Any) -> typing.Optional[int]:
    ...
```

Either style is acceptable. Prefer the one that improves readability in context.

### Modern Syntax

Where appropriate, prefer modern Python syntax:

- `int | None` instead of `Optional[int]`
- `str | int` instead of `Union[str, int]`

Example:

```python
def parse(x: str | None) -> int | None:
    ...
```

### Consistency Rule

Within a file, typing style should be consistent:

- Do not mix `Dict[...]` and `dict[...]`
- Do not mix `Optional[...]` and `| None` without reason

Prefer the modern style unless modifying legacy code where consistency would be broken.

## Naming and Readability

Use descriptive names. Avoid cryptic abbreviations unless they are standard in the domain.

Names should make code easier to understand without requiring the reader to inspect distant context.

Public names, internal helper names, test names, and script names should all favor clarity and consistency.

## Docstrings and Comments

Use docstrings for public modules, classes, and functions where helpful - particularly, following the [Google Python Style Guide format for functions](https://google.github.io/styleguide/pyguide.html#s3.8.3-functions-and-methods).

Comments should explain:

- why something is done
- assumptions
- constraints
- non-obvious behavior
- documented exceptions to normal project rules

Comments should not restate obvious code.

A special case where comments are expected is when using an exception to a normal project convention, such as a necessary dot-relative import.

## Testing

All substantive code changes should be covered by tests where practical.

- Use `unittest`
- All new functionality must include tests
- All tests must pass before merging

### Test Tree Layout

Tests should mirror the package module they cover. For a source module under
`src/taurworks/<package>/<module>.py`, prefer the matching test file:

```text
tests/<package>_tests/<module>_test.py
```

Examples:

- `src/taurworks/cli/taurworks.py` -> `tests/cli_tests/taurworks_test.py`
- `src/taurworks/config/config.py` -> `tests/config_tests/config_test.py`
- `src/taurworks/project/project.py` -> `tests/project_tests/project_test.py`

Avoid flattening package-specific tests into names such as
`cli_taurworks_test.py` or `config_config_test.py` at the root of `tests/`.
Prefer a package-specific test directory instead.

Exceptions are allowed for tests whose scope is intentionally broader than one
module, but their names should say so clearly. Use suffixes such as
`_integration.py` or `_smoke.py` for integration flows and smoke
coverage. Never end integration or smoke tests with `_test.py` so they are
not picked up as regular unit tests, and place smoke tests in `tests/smoke`.

### Testing Changes

At minimum:

- existing unit tests must pass
- new behavior should include tests when feasible
- bug fixes should include regression tests when feasible

Taurworks prefers predictable, automatable tests that can be run from the command line through the project’s scripts.

### Testing Principles

- Prefer real objects over heavy mocking
- Keep tests deterministic:
  - Seed randomness
  - Avoid time-dependent behavior
  - Ensure stable ordering

### Running Tests

The canonical project test entry point should be:

```bash
scripts/test
```

Run `scripts/develop` before the full test suite when preparing a local change.

If additional arguments or modes are supported, they should be documented in the scripts documentation.

## Code Style

- Follow Google Python Style Guide
- Use PEP 8 where not specified by Google
- Enforced by:
  - `ruff` (lint)
  - `black` (formatting)

## Linting

Taurworks uses Ruff for linting.

- All code must pass `ruff`
- Fix root causes, not suppressions
- Avoid adding ignores unless justified with comments

Code merged into the repository should pass Ruff lint checks.

The canonical project lint entry point should be:

```bash
scripts/lint
```

Lint fixes should generally be limited to code relevant to the task, unless the work is explicitly a lint cleanup change.

## Formatting

Taurworks uses Black for formatting.

- All code must pass `black`
- Do NOT manually format to fight the formatter

The canonical project formatting entry point should be:

```bash
scripts/format
```

Formatting-only changes should normally be kept separate from semantic code changes when practical.

Do not perform opportunistic formatting of unrelated files.

## Determinism

Where applicable:

- Seed all randomness
- Avoid time-dependent outputs
- Ensure stable ordering of collections

## Encoding

To avoid Unicode errors:

- Always use UTF-8 for file I/O
- Explicitly specify encoding when reading/writing files

## Tool Responsibilities

The intended division of labor is:

- tests verify correctness
- Ruff verifies lint and code-quality rules
- Black enforces formatting

Avoid overlapping or conflicting tool configurations when possible.

## Packaging and Project Structure

Taurworks should maintain a clear package structure and a reproducible installation path for development.

Where practical:

- package metadata and tool configuration should live in `pyproject.toml`
- development and test dependencies should be documented and installable
- scripts should provide stable entry points for common developer tasks

If the repository adopts CI workflows, they should use the same commands developers are expected to run locally.

## Scripts

The `scripts/` directory provides the standard developer entry points for common tasks.

At minimum, contributors should be able to run:

```bash
scripts/test
scripts/lint
scripts/format
```

These scripts should remain simple, reliable wrappers around the project’s canonical tooling.

They should be preferred over ad hoc local command variants when contributing to the repository.

### Requirements

Where feasible, scripts should be thin wrappers around library code.

- Avoid core logic in scripts
- Must support:
  - `--help`
  - `--check` (non-mutating validation)
  - `--dry-run` (preview changes)

## Continuous Integration

CI should enforce the same standards expected locally.

At minimum, CI should check:

- unit tests
- Ruff linting
- Black formatting checks

CI configuration should prefer explicit versions and reproducible commands to reduce local-versus-CI drift.

## Data & Schemas

Core data structures should:

- Be JSON-serializable
- Be human-readable
- Have stable structure
- Avoid implicit or hidden fields

Schema validation (e.g., Pydantic or JSON Schema) is encouraged.

## AI-Assisted Development Rules

AI tools such as Codex, ChatGPT, or similar systems may be used to help generate or edit code, but their output must follow this style guide.

When using AI tools (Codex, ChatGPT, etc.), AI-assisted changes must follow these additional rules:

Do NOT do the following:
- Do NOT modify code unrelated to the task
- Do NOT reformat entire files unnecessarily
- Do NOT create broad cleanup diffs unless explicitly asked
- Do NOT rewrite working code unnecessarily
- Do NOT introduce speculative refactors without justification
- Do NOT reword text for style unless asked to
- Do NOT change type annotation styles (e.g., `Dict` → `dict`, `Optional` → `| None`) unless:
  - the file is already being modified for a related reason, and
  - the change improves consistency within that file

Do the following:
- Preserve existing comments
- Produce minimal, targeted diffs
- Prefer small, reviewable changes
- Preserve existing behavior unless the task requires changing it
- Match the local style of the file being edited
- Generate drop-in compatible code
- When uncertain, report the issue rather than guessing

AI-generated pull requests should be especially careful to minimize noise.

## Pull Request Guidelines

PRs should be:

- Small and focused
- Easy to review
- Limited to a single concern

### Rules

- Separate style-only and functional changes into different commits or PRs
- Do not include drive-by refactors
- Ensure:
  - tests pass
  - lint passes
  - formatting passes

## Review Guidance

Reviewers should evaluate changes in this order:

1. Is the change in scope?
2. Does it preserve or improve correctness?
3. Do tests pass?
4. Does it follow Taurworks conventions?
5. Does it pass lint and formatting?
6. Is the diff readable and appropriately narrow?

A change may be technically correct but still require revision if it creates unnecessary review noise.

## Exceptions

Exceptions to this guide are allowed when justified by technical constraints, packaging realities, testing requirements, or other concrete reasons.

Exceptions should be:

- rare
- documented
- minimal
- local to the relevant code

Do not treat exceptions as precedent unless they are later incorporated into this document.

## Practical Developer Workflow

Before submitting changes, contributors should normally use the provided scripts:

```bash
scripts/test
scripts/lint
scripts/format
```

These define the source of truth for CI behavior.

If formatting changes are produced, review them to ensure they are limited to files relevant to the task.

Before opening a PR, contributors should confirm that:

- the change is scoped correctly
- tests pass
- lint passes
- formatting passes
- unrelated code was not modified unnecessarily

## CI Expectations

CI should enforce:

- unit tests
- linting (ruff)
- formatting (black)

## Using a prompt workflow

Tracking work in prompt-heavy workflows can become confusing, so Taurworks provides lightweight guidance and tooling to label meaningful prompts with unique IDs and record executions.

Use `scripts/prompts/label-prompt` to generate a prompt ID, and use `scripts/prompts/record-execution` to create an execution-record Markdown file.

Prompt IDs and execution records are encouraged for meaningful prompt-driven changes, especially for updates touching design, roadmap, work items, implementation, tests, or project-control artifacts.

Do not let prompt bookkeeping block small obvious fixes or exploratory work. Taurworks prefers traceability, but process should remain lightweight.

For detailed prompt metadata, rerun handling, and execution-record conventions, see `PROMPTS.md`.


## Summary

In Taurworks, we value:

- explicit module-oriented imports
- passing tests
- lint cleanliness
- consistent formatting
- small, low-noise diffs
- disciplined, reviewable pull requests

When in doubt, prefer the change that is clearer, narrower, and easier to review.

## Final Principle

If a change makes the codebase harder to understand, test, or review, it is not acceptable—even if technically correct.
