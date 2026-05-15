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

The active unified-command-model work item now tracks global resolution design after dogfooding: XDG-style global config, explicit workspace root, global project registry, workspace/registry-aware project listing and activation resolution, declarative activation config planning, and future user-script support only behind explicit opt-in. Legacy `Admin/project-setup.source` projects should be classified for migration planning and may be `cd`-only warning fallbacks, but must not be automatically sourced.
