---
id: WI-CONFIG-WRITER-NEWLINE-0001
title: 'Escape control characters in the project-config writer so rewrites cannot corrupt config.toml'
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-CURRENT
related_roadmap:
  - ROADMAP-INIT
related_workstreams: []
related_design:
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - replace_safe_writer_with_toml_library
  - preserve_comments_or_formatting_on_rewrite
  - change_global_config_writer
  - add_support_for_array_float_or_date_values
acceptance:
  - "a project config whose string value contains a newline, tab, carriage return, or other control character is rewritten by `write_project_config` into valid TOML that parses back to the identical value"
  - "`taurworks project env set` on a project whose `[activation].message` contains a newline (written as `\\n` or as a `\"\"\"` multi-line string) exits 0, leaves a config that `tomllib` parses, and preserves the message value exactly"
  - "new unit tests round-trip strings containing `\\n`, `\\t`, `\\r`, a backslash, a double quote, another C0 control character, DEL, and non-ASCII text through the project-config writer"
  - "`docs/reference/configuration.md` (Hand-editing) no longer warns that newline strings corrupt the file, and states that a multi-line string is rewritten as a single-line escaped string"
  - "the backlog entry 'Project-config writer corrupts strings containing newlines' in `project/design/backlog.md` is marked resolved by this work item"
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - src/taurworks/project_internals.py
  - tests/project_internals_test.py
  - tests/cli_test.py
  - docs/reference/configuration.md
  - project/design/backlog.md
---

# WI-CONFIG-WRITER-NEWLINE-0001: Escape control characters in the project-config writer so rewrites cannot corrupt config.toml

## Summary

Make the project-config writer escape control characters in string values
per the TOML spec, so that a command which rewrites
`.taurworks/config.toml` can no longer turn a valid config into an
unparseable one while reporting success.

## Problem / Context

`_toml_quote` in `src/taurworks/project_internals.py` escapes only `\` and
`"`. Every command that rewrites a project config (`project env set`,
`project working-dir set`, `project init`, `project refresh`, `legacy
migrate --apply`) regenerates the file from its parsed contents, so a
string value containing a newline or other control character — a
hand-edited `[activation] message = "line1\nline2"`, or a `"""` multi-line
string — is written back with a raw line break inside a basic string. The
command prints `ok: True` and exits 0, but the file is now invalid TOML:
every later read fails and `tw activate` stops working for that project
until the file is repaired by hand.

This is silent corruption of user data by a command that reports success,
and `[activation].message` is the key the getting-started tutorial tells
users to hand-edit. It was found and reproduced by the second independent
review of PR #122, which could only document a workaround
(`docs/reference/configuration.md`, "Hand-editing") because that PR was
docs-only.

`src/taurworks/global_config.py` has its own `_toml_quote`, implemented
with `json.dumps(value, ensure_ascii=False)`, which already escapes control
characters; the global config is not affected.

### Duplication search
- In-repo: Related: `src/taurworks/global_config.py` `_toml_quote` (already escapes via `json.dumps`; a model for the fix, not a duplicate)
- Sibling repos: None identified
- External libraries: Consider: `tomli-w` / `tomlkit` — rejected here; the package has no runtime dependencies and the hand-written safe writer is deliberate
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: Found: "Project-config writer corrupts strings containing newlines" in `project/design/backlog.md` (will be satisfied)
- Recommendation: Mark the backlog entry resolved as part of the implementation

## Scope

- Fix string escaping in the project-config writer in
  `src/taurworks/project_internals.py`.
- Add round-trip tests at the writer level and one end-to-end CLI test.
- Update the Hand-editing documentation and the backlog entry to match.

## Required Changes

1. In `src/taurworks/project_internals.py`, change `_toml_quote` to emit a
   valid TOML basic string for any `str`: escape `\`, `"`, `\b`, `\t`,
   `\n`, `\f`, `\r`, and every other character in U+0000–U+001F and U+007F
   as `\uXXXX`. Non-ASCII text is written unescaped, as today.
2. In `tests/project_internals_test.py`, add tests that write a config
   containing each of those characters with `write_project_config`, parse
   the result with `tomllib`, and assert the value is unchanged.
3. In `tests/cli_test.py`, add a test that hand-writes a config with a
   multi-line `[activation].message`, runs `project env set`, and asserts
   exit 0, a parseable file, and an unchanged message.
4. In `docs/reference/configuration.md` ("Hand-editing"), replace the
   "Keep string values on one line" warning with a statement that
   multi-line strings are preserved in value but rewritten as a single-line
   escaped string.
5. In `project/design/backlog.md`, mark the entry resolved with a pointer
   to this work item.

## Non-Goals

- Do not replace the hand-written writer with a TOML library or add a
  runtime dependency.
- Do not preserve comments, formatting, or `"""` multi-line syntax across a
  rewrite; the value is preserved, the spelling is not.
- Do not add support for arrays, floats, dates, or non-bare keys.
- Do not change `src/taurworks/global_config.py`.
- Do not add a repair command for configs already corrupted by this bug.

## Acceptance Criteria

- A string value containing a newline, tab, carriage return, or other
  control character survives `write_project_config` as valid TOML with an
  identical parsed value.
- `taurworks project env set` on a project with a multi-line
  `[activation].message` exits 0, leaves a parseable config, and preserves
  the message exactly.
- New unit tests cover `\n`, `\t`, `\r`, backslash, double quote, another
  C0 control character, DEL, and non-ASCII text.
- The Hand-editing documentation no longer describes the corruption and
  describes the new rewrite behavior.
- The backlog entry is marked resolved.

## Validation

- `./scripts/format --check --diff`
- `./scripts/lint`
- `./scripts/test`
- `./scripts/test-portability`
- `lrh validate`

## Risk Notes

- Escaping must stay exact for backslash and double quote, which existing
  configs (Windows-style paths, quoted messages) already rely on; the
  round-trip tests must include both alongside the new cases.
- Configs already corrupted by the bug stay corrupted; the fix prevents
  new damage only.
- `tw activate` prints the message through the shell helper, so a preserved
  multi-line message will now actually reach it. `project activate --print`
  reports only `activation_message_configured`, not the message, so verify
  preservation through `project activate --shell` (which emits
  `TAURWORKS_ACTIVATION_MESSAGE`) or the sourced `tw activate` helper.
