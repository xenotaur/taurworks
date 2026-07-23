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
