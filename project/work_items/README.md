# Work Items

Work items are organized by status bucket directories:

- `active/`
- `proposed/`
- `resolved/`

Each work item Markdown file should include YAML frontmatter at the top.
At minimum:

```yaml
---
id: WI-EXAMPLE
status: proposed
---
```

Frontmatter metadata is authoritative; bucket directories are a human-friendly organization layer and should agree with `status`.

## Current active work

The active unified-command-model work item now tracks post-dogfood shell polish: concise `tw activate` UX, project-list status classification, a minimal read-only `taurworks dev ...` scaffold, and activation-extension design. Legacy `Admin/project-setup.source` projects should be classified for migration planning, not automatically sourced as an activation fallback.
