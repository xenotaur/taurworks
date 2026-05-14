# Activation Extension Design Notes

## Purpose

This note records the activation-extension topics that should be designed after
successful `tw activate` dogfooding, without implementing them in the current
polish sequence.

The current safe boundary is:

```text
taurworks project activate --print
  read-only activation guidance

tw activate
  explicit shell-mutating wrapper

legacy Admin/project-setup.source
  migration/design topic, not automatic fallback
```

## Current activation baseline

The validated baseline is `cd`-only activation through an explicitly sourced
shell helper:

```bash
tw project create TestProject --working-dir test_repo --create-working-dir
tw activate TestProject
```

For this baseline, `taurworks project activate --print` remains the read-only
source of activation guidance, while `tw activate` is the explicit wrapper that
may mutate the current shell by changing directory.

## Extension topics to design before implementation

Future activation work should be designed as separate, reviewable slices:

1. **Readiness messages:** define concise success text such as “Ready for work
   on project X” after activation completes.
2. **Environment activation strategies:** describe how Conda, Python virtualenv,
   Docker/devcontainer, or other environment systems could be selected and
   invoked without hiding side effects.
3. **Trusted startup hooks:** define how per-project hooks would be declared,
   reviewed, trusted, and disabled before any project script is sourced or run.
4. **Legacy migration:** plan a migration path for projects that currently rely
   on `Admin/project-setup.source`, preferably through an explicit migration
   script or generated Taurworks configuration.
5. **Trust and safety boundaries:** document which actions are read-only, which
   mutate only shell working directory, and which execute project-controlled
   code.

## Deferred behavior

Automatic sourcing of legacy `Admin/project-setup.source` scripts is
intentionally deferred. Sourcing a project script executes project-controlled
code in the operator's current shell and therefore crosses a stronger trust
boundary than `cd`-only activation.

Until that boundary is designed, Taurworks should classify legacy-admin projects
for visibility but should not make them activation targets through fallback
sourcing.
