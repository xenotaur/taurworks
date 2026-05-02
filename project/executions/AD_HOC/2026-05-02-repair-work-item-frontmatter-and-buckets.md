---
prompt_id: "PROMPT(AD_HOC:REPAIR_WORK_ITEM_FRONTMATTER_AND_BUCKETS)[2026-05-02T15:18:00-04:00]"
work_item: "AD_HOC"
slug: "repair-work-item-frontmatter-and-buckets"
status: "landed"
date: "2026-05-02"
---

# Summary
Repaired LRH work item metadata by adding missing YAML frontmatter, inferring conservative statuses, and organizing work items into status bucket directories under `project/work_items/`.

# Result
- Added frontmatter (`id`, `status`) to both existing work item files.
- Inferred `WI-BOOTSTRAP-0001` as `resolved` based on explicit `## Status` value `Done (initial scaffold)`.
- Inferred `WI-UNIFIED-COMMAND-MODEL-0001` as `active` based on explicit `## Status` value `In progress`.
- Moved work items from flat `project/work_items/` into `resolved/` and `active/` bucket directories.
- Updated one internal file path reference inside `WI-BOOTSTRAP-0001` so the listed artifact path matches its new location.
- Added `project/work_items/README.md` documenting expected bucket layout and required frontmatter.

# Validation
- Attempted `scripts/prompts/record-execution --prompt-id "PROMPT(AD_HOC:REPAIR_WORK_ITEM_FRONTMATTER_AND_BUCKETS)[2026-05-02T15:18:00-04:00]" --work-item AD_HOC --slug repair-work-item-frontmatter-and-buckets --status planned` (failed: script not present).
- Ran `lrh validate` (failed: `lrh` command not available in this environment).
- Ran `scripts/test` (pass).

# Follow-up
- Add `scripts/prompts/record-execution` (or equivalent documented LRH command path) so prompt execution records can be generated via the documented workflow instead of manual creation.
