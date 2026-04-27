# LRH Prompt Workflow

This guide defines a lightweight prompt workflow for meaningful prompt-driven changes.

## Why prompt IDs and execution records exist

Prompt IDs and execution records make prompt-driven work easier to trace, search, and review.
They help answer:

- what prompt drove a change
- whether a prompt has already been executed
- what happened during the execution

This workflow is intentionally lightweight and should not become process overhead.

## When to use this workflow

Use prompt IDs and execution records for meaningful prompt-driven changes, especially when changes affect:

- design
- roadmap
- work items
- implementation
- tests
- project-control artifacts

## When not to use this workflow

Do not require prompt records for:

- casual discussion
- exploratory analysis
- small obvious fixes

If traceability helps anyway, you may still create one record.

## Prompt ID format

Use this shape:

```text
PROMPT(<WORK_ITEM_OR_AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601_TIMESTAMP_WITH_OFFSET>]
```

Examples:

```text
PROMPT(WI-META-CLI-MVP:REGISTER_IMPLEMENTATION)[2026-04-24T16:24:13-04:00]
PROMPT(AD_HOC:REGISTER_AUDIT)[2026-04-24T16:30:00-04:00]
```

## Execution record format

Execution records live under `project/executions/` and include YAML-style front matter plus brief sections:

- Summary
- Result
- Validation
- Follow-up

See `project/executions/README.md` for canonical layout and schema guidance.

## Rerun, revert, and supersession handling

Use status values from `project/executions/README.md`: `planned`, `in_progress`, `landed`, `failed`, `reverted`, `superseded`.

When rerunning a prompt, create a new execution record and link prior execution via `rerun_of`.

If work is reverted or superseded, preserve prior records and set status accordingly rather than deleting history.

## Soft idempotence before execution

Before starting prompt-driven PR work, search `project/executions/` for the prompt ID.

If a prior record exists:

- `landed` or `in_progress`: stop and report unless prompt explicitly requests rerun.
- `failed`, `reverted`, or `superseded`: summarize prior run and continue only if prompt is a rerun or follow-up.
- unknown or ambiguous status: stop and report ambiguity.

## Codex Cloud prompt requirements

For meaningful prompt-driven implementation in Codex Cloud:

1. include an explicit prompt ID in the prompt text
2. keep work-item linkage optional (`AD_HOC` is valid)
3. generate one execution record per meaningful prompt run
4. keep process lightweight and non-blocking for tiny fixes

## Work-item to Codex prompt flow

For work-item-driven implementation, use this sequence:

```text
Work item Markdown
  -> lrh request codex-prompt-from-work-item
  -> Codex Cloud prompt
  -> PR
  -> execution record
```

Suggested command flow:

```bash
lrh request codex-prompt-from-work-item \
  --work-item project/work_items/active/WI-EXAMPLE.md \
  --slug implement-wi-example \
  --out /tmp/codex_prompt.md

# Submit /tmp/codex_prompt.md to Codex Cloud and open a PR.

scripts/prompts/record-execution \
  --prompt-id "PROMPT(WI-EXAMPLE:IMPLEMENT_WI_EXAMPLE)[2026-04-24T20:15:00-04:00]" \
  --work-item WI-EXAMPLE \
  --slug implement-wi-example \
  --status in_progress
```

Notes:

- `codex-prompt-from-work-item` is the preferred structured command for work-item input.
- Pass `--work-item <WORK_ITEM_ID>` to `record-execution` for work-item-driven
  runs so records are written under that work-item directory instead of the
  `AD_HOC` default.
- Record execution after generating the PR so the record can include final PR/commit references.
- Keep this workflow lightweight: skip extra ceremony for tiny exploratory edits.

## Helper scripts

### `scripts/prompts/label-prompt`

Generates a prompt ID and suggested execution record path.

```bash
scripts/prompts/label-prompt --work-item WI-META-CLI-MVP --slug register-implementation
scripts/prompts/label-prompt --slug register-audit
```

Outputs include:

- `prompt_id`
- `execution_dir`
- `suggested_execution_file`

`--work-item` must be a safe ID (letters/numbers plus `_` or `-`) so paths stay scoped to execution-record directories.

### `scripts/prompts/record-execution`

Generates an execution-record Markdown file.

```bash
scripts/prompts/record-execution \
  --prompt-id "PROMPT(WI-META-CLI-MVP:REGISTER_IMPLEMENTATION)[2026-04-24T16:24:13-04:00]" \
  --work-item WI-META-CLI-MVP \
  --slug register-implementation \
  --status planned
```

Use `--dry-run` to preview output without writing files.
