# Design Backlog

Lightweight list of deferred ideas that are not yet ready for a formal
proposal or work item. Each entry should record what was noted, why it was
deferred, and where it came from so a future reader can act on it without
re-deriving context.

---

## Wire `scripts/audit-side-effects` into CI as an enforced gate

**Noted:** 2026-07-23, during a design discussion following the closeout of
[PR #80](https://github.com/xenotaur/taurworks/pull/80), prompted by
`project/audits/side_effects.md` follow-up recommendation #7.

**Idea:** `scripts/audit-side-effects` (a best-effort, non-destructive
scanner for 13 side-effect-sensitive patterns — `subprocess.run`,
`conda create`/`activate`, `eval`, `export`, `.mkdir(`, `rmtree(`, etc. —
across `src/`, `scripts/`, `tests/`, `README.md`, `project/design/`,
`project/audits/`) could be made an enforced CI gate: fail the build when a
new match appears against a committed baseline/allowlist, forcing an
explicit acknowledgment commit for any new side-effect-sensitive code.

**Status:** Deferred — the scanner's patterns match routinely-legitimate
code throughout this codebase (existing `eval` usage, including `eval`'d
generated export commands, in `taurworks-shell.sh`; existing gated
`conda create` in `manager.py`; plain `.mkdir(`/`write_text(` calls that are
unrelated to safety). A broad diff-against-baseline gate would mostly
manufacture friction on ordinary feature PRs rather than catch a recurring
class of real bugs: the one actual incident this audit ever found (legacy
`refresh`'s default Conda creation — see `project/audits/side_effects.md`'s
"Legacy top-level `taurworks refresh NAME`" command inventory entry,
Assessment) was already fixed by a targeted, specific mechanism
(`--create-env`, `WI-LEGACY-CONDA-GATING-0001`)
rather than a generic scanner, and no other pattern match in this codebase
has ever corresponded to a real bug. Every PR here already goes through a
diff-reading human/AI review protocol (`/lrh-review-response`,
`/lrh-confirm-fixes`); a regex gate doesn't add signal beyond that for a
single-maintainer project. Revisit if either: (a) a second real
side-effect incident occurs that a targeted fix wouldn't have caught but a
broad gate would have, or (b) this project gains outside contributors,
changing the review-coverage assumption this deferral rests on.

**Related:** `scripts/audit-side-effects`; `project/audits/side_effects.md`
follow-up recommendation #7 and its "Audit helper" section; the "General
principle" added to that file's Safety baseline (2026-07-23);
`WI-LEGACY-CONDA-GATING-0001`.

---

## Make legacy `taurworks refresh`/`create` fully metadata-only

**Noted:** 2026-07-23, same discussion as above, prompted by
`project/audits/side_effects.md` follow-up recommendation #1 (full form) and
`WI-LEGACY-CONDA-GATING-0001`'s Open Questions.

**Idea:** `taurworks create NAME` / `taurworks refresh NAME` (and therefore
`tw create`/`tw refresh`) still unconditionally create the workspace root,
project directory, `.taurworks/` metadata directory, and repository
directory (`src/taurworks/manager.py` `create_project`/`refresh_project`).
Conda environment creation is already gated behind `--create-env`
(`WI-LEGACY-CONDA-GATING-0001`); this would extend the same explicit-opt-in
pattern already established by `project init`/`project create
--create-working-dir` to the remaining directory-creation side effects, so
a repair-looking command never scaffolds a project tree without being
asked.

**Status:** Deferred — this is a real, not hypothetical, compatibility
risk: as of 2026-07-23 the maintainer confirmed they haven't yet needed to
exercise plain `taurworks create`/`refresh` for from-scratch project
scaffolding, but expects to need it occasionally (roughly once a month at
most) going forward, and flipping the default without a flag would silently
break that low-frequency but real usage. Not worth an active work item
while usage is this infrequent and the actually-dangerous side effect
(Conda creation) is already gated. Revisit if: (a) from-scratch
`taurworks create`/`refresh` usage becomes more frequent or automated
(e.g. scripted project setup), where an accidental unwanted directory tree
becomes more costly, or (b) this project gains outside contributors
unfamiliar with the current default behavior.

**Related:** `src/taurworks/manager.py` (`create_project`, `refresh_project`,
`_write_initial_project_config`); `project/audits/side_effects.md` follow-up
recommendation #1; `project/work_items/resolved/WI-LEGACY-CONDA-GATING-0001.md`
Open Questions.

---

## Make workspace-root resolution consistent across commands

**Noted:** 2026-11-13, while verifying behavior for the end-user
documentation pass ([PR #122](https://github.com/xenotaur/taurworks/pull/122)).

**Idea:** Commands disagree on which workspace they use. Name lookup
(`tw activate NAME`, `tw projects`, `project list`, `tw root`/`working`)
uses the configured `[workspace].root`, then `$TAURWORKS_WORKSPACE`, then
`~/Workspace` (`manager.workspace_path`). `taurworks project create NAME`
requires a configured root. Legacy top-level `taurworks create`/`refresh`
use the import-time `manager.TAURWORKS_WORKSPACE` constant
(`$TAURWORKS_WORKSPACE`, else `~/Workspace`) and ignore
`taurworks workspace set` entirely, so they can scaffold a project somewhere
`tw activate` then won't look. `taurworks workspace show` never
reports the `$TAURWORKS_WORKSPACE` tier that name lookup actually uses: with
no global config file it reports an existing `~/Workspace` as `inferred`
even when `$TAURWORKS_WORKSPACE` points elsewhere, and once the config file
exists without a `[workspace].root` (after `project register`, say) it
reports `none`/`unconfigured` while name lookup still falls back to
`$TAURWORKS_WORKSPACE` or `~/Workspace`. Candidate fix: route every
Python caller through one resolver and have `workspace show` report the
`$TAURWORKS_WORKSPACE` tier.

**Status:** Deferred — documented as-is in
`docs/reference/configuration.md` ("Which workspace does a command use?")
rather than changed in a docs-only PR. Only bites users whose workspace is
not `~/Workspace`. `tl` is deliberately excluded from any fix: it must not
depend on the `taurworks` executable or its config (`WI-TL-BREAKGLASS-0001`),
so its `$TAURWORKS_WORKSPACE`/`~/Workspace` lookup stays, and the documented
remedy (export `TAURWORKS_WORKSPACE` alongside `workspace set`) remains
necessary for it. Revisit when next touching `manager.py`'s legacy
commands, or on the first report of a project created in the wrong
workspace.

**Related:** `src/taurworks/manager.py` (`TAURWORKS_WORKSPACE`,
`workspace_path`, `create_project`, `refresh_project`);
`src/taurworks/global_config.py` (`gather_workspace_show_diagnostics`);
`src/taurworks/resources/sourceme/aliases.source`;
`docs/reference/configuration.md`; the "Make legacy `taurworks
refresh`/`create` fully metadata-only" entry above.

---

## Stop `taurworks project refresh PATH` creating a missing target directory

**Noted:** 2026-11-13, same documentation pass as above.

**Idea:** `taurworks project refresh PATH` creates `PATH` itself when it
does not exist, then scaffolds `.taurworks/` inside it. A typo in the path
silently produces a new directory tree. This sits awkwardly with the
AGENTS.md rule that a safe/idempotent-sounding command (`refresh`) must not
perform a mutating operation without an explicit flag, and it is
inconsistent with `project init`, which refuses a missing root. Candidate
fix: fail on a missing target and point at `project create`, or require an
explicit opt-in flag.

**Status:** Deferred — distinct from the legacy top-level `taurworks
refresh` entry above; this is the namespaced `project refresh`. Currently
intentional and documented behavior (the old README stated it, and
`docs/how-to/manage-projects.md` now carries a warning), and `project
create` delegates to the same refresh internals, so the fix needs care to
keep `create` working. Low observed harm: the created tree is empty apart
from Taurworks-owned metadata. Revisit alongside the legacy
`refresh`/`create` metadata-only item, since both are the same
"repair-looking command scaffolds a tree" concern.

**Related:** `src/taurworks/project_resolution.py`
(`gather_project_refresh_diagnostics`, `gather_project_create_diagnostics`);
`project/audits/side_effects.md` Safety baseline;
`docs/how-to/manage-projects.md` ("Repair project metadata").

---

## Fix legacy `create`/`refresh` help text claiming a setup script is created

**Noted:** 2026-11-13, same documentation pass as above.

**Idea:** The `--create-env` help for top-level `taurworks create` and
`taurworks refresh` says "directories and the setup script are still
created". No setup script is created: both commands write only
`.taurworks/config.toml` plus the project and working directories. Besides
being inaccurate, it implies `tl NAME` will work on a freshly created
project, and it does not (`tl: no setup script found`). Two possible
resolutions: (a) correct the help text, or (b) actually generate a
`.taurworks/project-setup.source` mirroring the declarative config so new
projects are `tl`-capable out of the box.

**Status:** Deferred — (a) is a two-line fix in `src/taurworks/cli.py` and
can ride along with any PR that touches that file; it was left out of PR
#122 only to keep that PR docs-only. (b) is a design question, not a typo:
a generated script would be a second source of truth that drifts from
`config.toml`, which is exactly the duplication the "retire a migrated
script" guidance warns about. `docs/how-to/use-tl-fallback.md` documents
writing the script by hand in the meantime. Do (a) opportunistically;
revisit (b) only if hand-writing `tl` scripts proves to be a recurring
chore.

**Related:** `src/taurworks/cli.py` (`parser_create`, `parser_refresh`
`--create-env` help); `src/taurworks/manager.py`
(`_write_initial_project_config`); `docs/how-to/use-tl-fallback.md` ("Make a
project work with `tl`"); `WI-TL-BREAKGLASS-0001`.

---

## Quiet the `tw activate` note for projects with no Conda environment

**Noted:** 2026-11-13, same documentation pass as above.

**Idea:** Every `tw activate` of an initialized project without
`[activation.environment]` prints, to stderr, `tw activate: note: Activation
guidance is ready, but no Conda activation environment is configured.
Inspect the command below, or run ...`. For a project that intentionally has
no Conda environment this is permanent noise that reads like a problem, and
"Inspect the command below" is `--print` wording that makes no sense in
`tw activate` output, where no command follows. Candidate fixes: drop the
note from the shell path entirely (keep it in `--print`), show it only with
`--verbose`, or add a per-project way to say "no environment, on purpose".

**Status:** Deferred — cosmetic; activation succeeds and exits 0. The
tutorial and `docs/how-to/activate-projects.md` explain the line so new
users are not alarmed. The right fix depends on a small design choice (is
"no environment" a state worth nudging about at all?), so it was not
changed in a docs-only PR. Revisit on the next change to `_tw_activate` or
to the activation guidance strings.

**Related:** `src/taurworks/resources/shell/taurworks-shell.sh`
(`_tw_activate`, the `environment_configured != True` branch);
`src/taurworks/project_resolution.py` (activation `guidance` text);
`docs/tutorials/getting-started.md`; `docs/how-to/activate-projects.md`.

---

## Have `tw shell refresh` also refresh `tl.source`

**Noted:** 2026-11-13, same documentation pass as above.

**Idea:** `taurworks setup` writes both `taurworks-shell.sh` and
`tl.source`, but `tw shell refresh` regenerates and re-sources only the
former. After an update, a user who follows the documented "reinstall, then
`tw shell refresh`" habit via plain `pipx` (not `scripts/install`, which
re-runs `taurworks setup`) keeps a stale `tl.source` on disk indefinitely.
Candidate fix: have `tw shell refresh` call `taurworks setup` for the file
writes, or add a `taurworks shell print-tl` and refresh both.

**Status:** Deferred — low impact by design: `tl` is feature-frozen
(`WI-INTERIM-TL-PIPX-0001`, `WI-TL-BREAKGLASS-0001`), so its packaged
source rarely changes, and `scripts/install` already refreshes it. Any fix
must not make `tl` depend on `tw` or on the installed package at use time;
refreshing its file from `tw` is fine, sourcing or delegating is not.
`docs/how-to/install-and-update.md` states the current behavior. Revisit if
`aliases.source` ever changes in a way users need promptly.

**Related:** `src/taurworks/resources/shell/taurworks-shell.sh`
(`_tw_shell_refresh`); `src/taurworks/setup_command.py`
(`gather_setup_diagnostics`); `project/design/shell_helper_refresh.md`;
`docs/how-to/install-and-update.md` ("Update").
