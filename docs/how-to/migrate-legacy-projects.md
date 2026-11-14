# Migrate a legacy `Admin/project-setup.source` project

Older Taurworks projects are activated by a hand-written shell script at
`Admin/project-setup.source`. They show up as `legacy-admin` in
`tw projects`. This guide moves such a project to declarative
`.taurworks/config.toml` activation, and covers the stop-gap of letting
`tw activate` source the old script while you get there.

Until you do either, `tw activate NAME` on a legacy project only changes to
the project root and warns that the script was not sourced.
[`tl NAME`](use-tl-fallback.md) sources it directly.

## Migrate to declarative config

### 1. Inspect the script

```bash
taurworks legacy inspect NAME
```

Taurworks reads the script — it never runs it — and classifies each line.
Four patterns are understood:

| Script line | Becomes |
|---|---|
| `conda activate NAME` | `[activation.environment]` |
| `export VAR=literal` | `[activation.exports]` |
| `cd PATH` | `[paths].working_dir` |
| `echo ...` / `printf ...` | `[activation].message` |

Everything else, and any of the above whose value is not a plain literal
(contains `$`, backticks, pipes, globs, and so on), is reported as
unsupported and needs manual review. Export values are always redacted in the
output.

### 2. Preview the migration

```bash
taurworks legacy migrate NAME
```

This is a dry run. It lists what would be written, what would be skipped, and
what needs manual review.

### 3. Apply it

```bash
taurworks legacy migrate NAME --apply
```

This writes the proposed fields to `.taurworks/config.toml`. Values already
present in the config are never overwritten. The legacy script is left in
place, unchanged.

### 4. Handle what could not be migrated

For each line reported as needing manual review, decide whether to express it
in `config.toml` by hand, drop it, or keep relying on the script. A common
case is an export computed by command substitution, which a literal
`[activation.exports]` value cannot represent.

### 5. Check

```bash
tw activate NAME
```

Compare the result with what the script did.

## Retire the old script

Once `config.toml` covers everything, the script in `Admin/` is redundant.
While legacy sourcing is enabled, `tw activate` will also keep prompting or
printing a note about it, and a trusted script would be sourced on top of the
migrated config. Move it to the location that only `tl` uses, and revoke any
trust recorded for it:

```bash
mv Admin/project-setup.source .taurworks/project-setup.source
```

```bash
taurworks project trust unset NAME
```

Before moving it:

- **Confirm coverage is complete.** If any line was left for manual review and
  not handled, retiring the script silently loses that behavior.
- **Check for location-dependent lines.** A script that finds files relative
  to itself (`${BASH_SOURCE[0]}`, `dirname "$0"`) resolves differently from
  `.taurworks/` than from `Admin/`. Fix those references first, or the script
  can fail under `tl`.

Why each step:

- **Move, do not copy**, so there are never two copies to drift apart.
  `tw activate` only looks at `Admin/project-setup.source`, so the move
  silences it; `tl` checks `.taurworks/project-setup.source` second, so it
  keeps working.
- **Unset trust** because a trust record is keyed on the script's content and
  stored in your global config, not in the project. If the old file is ever
  restored unchanged — a `git checkout`, for instance — a leftover record
  would match and `tw activate` would start sourcing it again on top of the
  migrated config. If the project was never trusted, `trust unset` says so
  and exits non-zero; that is harmless.

## Stop-gap: let `tw activate` source the legacy script

If you cannot migrate yet, `tw activate` can source the script for you. This
is off by default and takes two deliberate steps, because it means running
arbitrary shell code from a project directory.

### 1. Turn on legacy sourcing

```bash
taurworks config legacy-sourcing enable
```

This is a global switch. On its own it sources nothing.

### 2. Choose per activation, or trust the script

With the switch on and an untrusted script present, an interactive
`tw activate NAME` shows what `taurworks legacy inspect` found and asks:

```text
tw activate: [s]ource once, [t]rust and source, or anything else to skip this time?
```

Or decide without the prompt:

| Goal | Command |
|---|---|
| Source it this once | `tw activate NAME --legacy` |
| Trust it, so every activation sources it | `taurworks project trust set NAME` |
| Skip it this once, even if trusted | `tw activate NAME --no-legacy` |
| Stop trusting it | `taurworks project trust unset NAME` |
| See what is trusted | `taurworks project trust list` |

In a non-interactive shell there is no prompt; `tw activate` prints a note
telling you about `--legacy` and `trust set` instead.

Trust applies to the exact content of the script. If the script is edited,
the trust no longer matches and `tw activate` treats it as untrusted again
(the interactive prompt says the script has changed since it was trusted;
`taurworks project trust list` shows `digest_matches: False`). Review it and
run `taurworks project trust set NAME` again.

The legacy script is sourced *after* the normal activation steps, so with
both a `config.toml` and a trusted script, both take effect. That is fine
mid-migration, and the reason to retire the script once migration is
complete.

### Turn it back off

```bash
taurworks config legacy-sourcing disable
```

With the switch off, no script is sourced and nothing prompts, whatever trust
records exist.
