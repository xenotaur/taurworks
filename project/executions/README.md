# Execution Records

Execution records provide lightweight traceability for meaningful prompt-driven work.
They should be small, factual, and easy to scan during review.

## Layout

Records live under `project/executions/<WORK_ITEM_OR_AD_HOC>/`.

Use `AD_HOC` when no specific work item applies:

```text
project/executions/AD_HOC/<YYYY-MM-DD>-<slug>.md
```

Use the work-item ID when a prompt is tied to a work item:

```text
project/executions/<WORK_ITEM_ID>/<YYYY-MM-DD>-<slug>.md
```

## Front matter

Each record should start with YAML-style front matter:

```yaml
---
prompt_id: "PROMPT(AD_HOC:EXAMPLE)[2026-05-13]"
work_item: "AD_HOC"
slug: "example"
status: "landed"
date: "2026-05-13"
---
```

`status` should be one of:

- `planned`
- `in_progress`
- `landed`
- `failed`
- `reverted`
- `superseded`

For reruns, create a new record instead of overwriting history, and add `rerun_of` in front matter when the prior record is known.

## Body sections

Use these sections unless a prompt requires more detail:

```markdown
# Summary
Briefly describe what the prompt execution attempted.

# Result
List the meaningful changes or outcome.

# Validation
List commands run and whether they passed, failed, or were blocked by environment/repository limitations.

# Follow-up
List known follow-up work, or `None`.
```

Prefer `scripts/prompts/record-execution` when it is available. If the script is unavailable, create the record manually using this convention and note the missing script in the validation section.
