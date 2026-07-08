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

`WI-UNIFIED-COMMAND-MODEL-0001` is resolved: global resolution (XDG-style global config, explicit workspace root, global project registry, workspace/registry-aware project listing and activation resolution) is implemented. The remaining active work item is `WI-ACTIVATION-CONFIG-0001`, which now tracks the remaining activation work: `taurworks legacy inspect`/`legacy migrate` for `Admin/project-setup.source` projects (the unimplemented declarative-activation slice) and future trusted hooks behind explicit opt-in (a separate, non-declarative future phase, not part of declarative activation). Activation messages, export payload separation, and Conda activation from that work item are already implemented. Legacy `Admin/project-setup.source` projects remain classified for migration planning and may be `cd`-only warning fallbacks, but must not be automatically sourced.
