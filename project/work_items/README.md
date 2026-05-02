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
