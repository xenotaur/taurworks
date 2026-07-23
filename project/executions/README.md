# Execution Records

Execution records provide lightweight traceability for meaningful prompt-driven work.
They should be small, factual, and easy to scan during review.

## Layout

Records live under `project/executions/<WORK_ITEM_OR_AD_HOC>/`.

Use `AD_HOC` when no specific work item applies:

```text
project/executions/AD_HOC/<execution_id>.md
```

Use the work-item ID when a prompt is tied to a work item:

```text
project/executions/<WORK_ITEM_ID>/<execution_id>.md
```

`<execution_id>` has the shape
`<YYYY_MM_DD_HH_MM_SS>_<SLUG_UPPER_UNDERSCORE>`, for example
`2026_07_08_13_37_09_WI_LEGACY_CONDA_GATING` — the `.md` extension belongs
to the filename, not the ID itself. It is minted by `lrh prompt
record-execution` when the record is actually created, not by `lrh prompt
label`: `label`'s own timestamp only seeds a *suggested* filename, which
may carry an earlier timestamp than the real `execution_id` if time passes
before `record-execution` runs.

## Creating and closing out a record

Prefer the `lrh` CLI over hand-authoring:

```bash
# 1. Mint a prompt ID and check there's no prior execution of the same prompt
lrh prompt label --slug <slug> [--work-item <WI-ID>]
lrh prompt check-execution --prompt-id "<prompt_id>" --project-root .

# 2. Create the record once work starts
lrh prompt record-execution \
  --prompt-id "<prompt_id>" \
  --work-item <WI-ID-or-AD_HOC> \
  --slug <slug> \
  --status in_progress \
  --project-root .

# 3. Flip it to landed once the PR merges
lrh prompt update-execution \
  --execution-id <execution_id> \
  --status landed \
  --pr <pr-url> \
  --commit <merge-commit-sha> \
  --session-transcript <claude-app:uuid-or-pending> \
  --project-root .
```

If the `lrh` CLI is unavailable, create the record manually using the front
matter and body shape below, and note the missing tool in the Validation
section.

## Front matter

```yaml
---
execution_id: 2026_07_08_13_37_09_WI_LEGACY_CONDA_GATING
prompt_id: PROMPT(WI-LEGACY-CONDA-GATING-0001:WI_LEGACY_CONDA_GATING)[2026-07-08T13:17:50-04:00]
work_item: WI-LEGACY-CONDA-GATING-0001
status: landed
rerun_of:
pr: https://github.com/xenotaur/taurworks/pull/63
commit: e9c9bf6dc43af620813662fc10fb3fe896e41a37
created_at: 2026-07-08T13:37:09-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LEGACY-CONDA-GATING-0001.md
session_transcript: claude-app:8d50d14e-57c6-4894-b351-2d95ae102df3
---
```

Required: `execution_id`, `prompt_id`, `work_item`, `status`, `created_at`.
`rerun_of`, `pr`, `commit` are populated as they become known — leave blank
until then. `agent`, `instruction_source`, `session_transcript` are optional
but recommended when the executing agent can populate them.

`status` should be one of:

- `planned`
- `in_progress`
- `landed`
- `failed`
- `reverted`
- `superseded`

`lrh prompt update-execution` only drives the `in_progress → landed`
transition (the common closeout path); other transitions are edited by hand.

For reruns, create a new record instead of overwriting history, and set
`rerun_of` to the prior record's `execution_id` when known.

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

## Legacy records

Records created before roughly mid-May 2026 predate the `lrh` CLI and use a
simpler front matter (`prompt_id`, `work_item`, `slug`, `status`, `date`,
filed as `AD_HOC/<YYYY-MM-DD>-<slug>.md`), written by hand because
`scripts/prompts/record-execution` — the tool those records reference — was
never built; the `lrh` CLI superseded that plan entirely. Leave those
records in their original schema rather than migrating them field-by-field,
but keep `status` accurate (e.g. flip to `landed` once the described work is
confirmed present) since it's a real field read by tooling, not free text.
