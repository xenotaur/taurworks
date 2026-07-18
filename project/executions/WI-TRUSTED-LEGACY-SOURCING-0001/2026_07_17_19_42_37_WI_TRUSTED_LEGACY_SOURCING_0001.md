---
execution_id: 2026_07_17_19_42_37_WI_TRUSTED_LEGACY_SOURCING_0001
prompt_id: PROMPT(WI-TRUSTED-LEGACY-SOURCING-0001:WI_TRUSTED_LEGACY_SOURCING_0001)[2026-07-16T16:02:20-04:00]
work_item: WI-TRUSTED-LEGACY-SOURCING-0001
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/taurworks/pull/70
commit: dbf6ae3
created_at: 2026-07-17T19:42:37-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-TRUSTED-LEGACY-SOURCING-0001.md
session_transcript: claude-app:149f0939-369e-4d12-afa5-29a079bb476f
---

# Summary

Implement WI-TRUSTED-LEGACY-SOURCING-0001: two-tier trust-gated sourcing of
legacy `Admin/project-setup.source` scripts — a global off-by-default switch
(Tier 1), per-project sha256-verified trust records in the user-owned global
config (Tier 2), and a `tw activate` prompt/source flow — the last item in
the dogfood recovery plan.

**Scope decision (user-approved before implementation):** the WI as written
scoped this to `legacy-admin`-status projects only. Since
WI-LEGACY-BATCH-MIGRATION-0001 landed, all 11 real projects are now
`initialized`, so the literal scope would help zero real projects today. The
user chose to extend scope: trust-gated sourcing fires whenever a legacy
script exists on disk regardless of project status, running after the
existing declarative activation steps.

# Result

1. **Tier 1** (`src/taurworks/global_config.py`): `[activation]
   legacy_sourcing` boolean, surgical text-preserving TOML writer matching
   the existing `workspace.root` pattern. `taurworks config legacy-sourcing
   show/enable/disable`.
2. **Tier 2** (`global_config.py`): `[trust.NAME]` table (`path` + `digest`),
   deliberately separate from `[projects.NAME]` — the registry requires a
   non-empty `root` and iterates all entries
   (`project_registry._project_entry_root`), so a trust-only entry there
   would break registry handling. `taurworks project trust set/unset/list`
   (`project_resolution.py`, using the same registry-aware
   `resolve_global_activation_project` resolver as `env set/show`, per the
   PR #69 review lesson). `trust set` always overwrites (direnv-allow
   model).
3. **`tw activate` flow**: `--shell` payload extended with `project_name`
   and four legacy-trust fields, computed once in a new
   `_apply_legacy_trust_diagnostics` helper that runs unconditionally
   (correct for both status paths per the scope decision).
   `taurworks-shell.sh` gained `_tw_legacy_prompt_choice` (testable prompt
   parser), `_tw_source_legacy_script`, `_tw_offer_legacy_trust`
   (interactive consent flow showing `taurworks legacy inspect` output),
   and the decision block: trusted → silent source; `--legacy` → one-shot;
   TTY + untrusted → prompt; non-interactive → fail open with a note;
   `--no-legacy` → skip.
4. `--legacy`/`--no-legacy` flags added to `_tw_activate`'s arg parser
   (shell-side only, matching `--verbose`/`--debug`).
5. 49 new tests; `project/design/activation_extension.md`'s "User scripts
   and hooks" section rewritten from speculative future design to the
   implemented model.

**Verified live** (real conda, synthetic project, not the user's real
projects): full prompt → trust → source cycle via direct
`_tw_offer_legacy_trust` invocation; digest-mismatch (stale) detection
after editing a trusted script; the extended-scope case (already-initialized
project, trust-gated sourcing firing after declarative activation); and the
exact acceptance criterion — trusted sourcing switched `$CONDA_DEFAULT_ENV`,
changed directory to the script's own target, and exported a variable, all
live in a real shell with real conda.

# Validation

- Python 3.11.8, black 26.3.1, ruff 0.15.12
- `scripts/format --check --diff` — 27 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 269 tests OK (220 prior + 49 new)
- `lrh validate` — no new errors (4 known pre-existing `contributors.md`
  errors remain)
- Manual live-shell verification: prompt→trust→source→edit→re-prompt cycle
  and the real-conda env/cd/export proof (see Result)

**Not automatable:** there is no real TTY in this environment, so the outer
`[ -t 0 ] && [ -t 1 ]` gate in `_tw_activate` (genuine interactive-terminal
detection) cannot be exercised by a subprocess test — only the prompt logic
behind that gate is (via direct `_tw_offer_legacy_trust` invocation with
piped stdin). Verified manually instead; noted explicitly rather than
claiming automated coverage that doesn't exist.

# Follow-up

- On merge: closeout via /lrh-closeout (mark this record landed, resolve
  the work item).
- This is the last substantive item in the dogfood recovery plan (step 5 of
  6). Step 6 (retire `tl`) becomes viable once every project the owner
  activates in a normal week works via `tw activate` — worth revisiting
  after some real usage of trust-gated sourcing on the 11 real projects.
