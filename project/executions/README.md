# Execution Records

Execution records track meaningful prompt-driven changes.

Use:

```bash
scripts/prompts/record-execution "<prompt-id>" <status> "<notes>"
```

Status values are repository-defined; recommended values include:
- `in_progress`
- `landed`
- `failed`
- `reverted`
- `superseded`
