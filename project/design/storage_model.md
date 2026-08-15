---
id: PROP-TAURWORKS-STORAGE-MODEL
type: design_proposal
title: Taurworks Storage Model — Workspace, Taurspace, and Storage Auditing
status: proposed
created_on: 2026-08-15
updated_on: 2026-08-15
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/design.md
  - project/design/config_model.md
  - project/design/unified_command_model.md
  - project/guardrails/agent_guardrails.md
---

# Taurworks Storage Model — Workspace, Taurspace, and Storage Auditing

## Summary

This proposal introduces a Taurworks storage model that separates the stable,
human-facing project namespace from physical storage placement. `Workspace`
becomes a local logical working namespace; persistent-local storage is the
default; selected project entries may instead be explicitly placed in a
cloud-mirrored `Taurspace` or in transient system storage while remaining
visible at their normal project paths through Taurworks-managed mappings.

The proposal also introduces a read-only-first `taurworks storage ...` command
namespace and a single `taurworks-storage-audit` Agent Skill. The CLI and its
structured output are authoritative for filesystem facts; the skill interprets
those facts conversationally and does not duplicate storage logic.

## Background / Motivation

Taurworks manages projects under a configured workspace root, and its current
product model distinguishes project/workspace lifecycle operations from
repo-local development workflows. Real development work, however, mixes data
with very different lifecycle and synchronization needs: administrative files,
Git repositories, agent worktrees, model checkpoints, corpora and caches, and
regenerable build products.

A workspace synchronized wholesale by a general-purpose file synchronization
service creates unnecessary load when high-churn repositories, worktrees,
build products, and caches contain hundreds of thousands of filesystem
entries. Conversely, moving the whole workspace out of synchronized storage is
not appropriate when project roots also contain durable administrative and
project documents that benefit from cloud mirroring.

The desired model is therefore not "sync the whole workspace" or "sync none of
it." Taurworks should preserve the familiar logical organization while making
physical storage class explicit where needed. This follows Taurworks' existing
preference for explicit configuration, inspectable path resolution, and
conservative handling of side effects.

The motivating operational model is:

```text
~/Workspace/                         # local logical working namespace
    Project/
        .taurworks/                  # real local metadata
        Admin@  -------------------> <mirrored-root>/Project/Admin
        Build@  -------------------> <transient-root>/Project/Build
        Cache/                       # persistent-local by default
        Repo/                        # persistent-local by default
        Workstreams/                 # persistent-local by default
```

`Workspace` is where humans and tools go to work. `Taurspace` is the durable,
cloud-mirrored subset of project data. Transient storage is explicitly
regenerable/disposable storage outside the persistent workspace.

## Prior Art Check

### Duplication search

- In-repo: no existing Taurworks storage subsystem, storage-class model, or
  `taurworks storage` command was found. The closest related mechanisms are
  global workspace/project path configuration, project path resolution, and
  conservative symlink handling in project metadata.
- Sibling repos: Logical Robotics Harness has mature Agent Skills conventions,
  including canonical skill sources and target-aware installation. Prosoc has
  audit skills that explicitly orchestrate an authoritative underlying audit
  procedure rather than reimplementing it. These are useful patterns, not
  duplicate storage implementations.
- External libraries: no library is needed to own this policy. Filesystem,
  Git, and temporary-directory primitives should remain delegated to their
  established tools; Taurworks provides policy, diagnostics, and orchestration.
- Recommendation: proceed with a Taurworks-specific storage model, reusing the
  established skill and audit architectural patterns rather than creating a
  second independent agent-side implementation.

### Demand search

- Work items: no existing Taurworks work item was found requesting this
  capability.
- Proposals/design: no existing Taurworks design document defines this storage
  model.
- Backlog: no matching storage-model entry was found in
  `project/design/backlog.md`.
- Recommendation: introduce this proposal as new design scope and derive work
  items only after the proposal is reviewed.

## Design Decisions

### Decision 1: Workspace is a logical namespace, not a synchronization backend

Options considered:

- Keep `Workspace` inside cloud-mirrored storage and symlink high-churn paths
  outward.
- Move whole projects outside `Workspace` and rely on Taurworks registration.
- Keep `Workspace` local and point only selected entries outward to other
  storage classes.

**Chosen: keep `Workspace` local and use it as the stable logical namespace.**

This reverses the dependency on file-sync symlink behavior. A cloud provider
sees ordinary physical directories under the mirrored root; the compatibility
symlinks live outside the provider's watched tree. New repositories, caches,
worktrees, and generated files therefore remain local by default without any
special exclusion rule.

### Decision 2: Persistent-local is the default storage class

Taurworks defines three lifecycle/placement classes:

- `persistent`: survives reboot and lives in ordinary local project storage;
  this is the implicit default for normal files and directories under
  `Workspace`.
- `mirrored`: durable data physically located beneath a configured mirrored
  root and normally exposed at its logical project path through a managed
  mapping.
- `transient`: regenerable/disposable data physically located beneath a
  Taurworks namespace in an OS-appropriate temporary root.

No separate physical persistent root is required in the initial design.
Keeping ordinary persistent data physically in `Workspace` minimizes
indirection and makes the common case require no metadata.

Backup/protection status is deliberately separate from storage class. A
persistent Git repository may be protected by a remote; a persistent
checkpoint may be protected by Time Machine; a persistent cache may be
reproducible and intentionally unbacked-up.

### Decision 3: Storage class and link topology are independent concepts

Taurworks must not treat arbitrary symlinks as something it "permits" or
"forbids." Projects may legitimately contain links to sibling projects,
shared datasets, external volumes, or other resources.

An audit therefore observes a separate link relationship such as:

- `none`
- `managed`
- `internal`
- `external`
- `broken`

An unmanaged external symlink is informational by default, not an error. A
broken link is a finding because it is broken. A Taurworks-managed link whose
target disagrees with its declared storage mapping is a finding because the
managed state is inconsistent.

### Decision 4: Taurworks owns only explicitly managed mappings

Project-local storage declarations should distinguish between mappings
Taurworks may reconcile and annotations Taurworks merely explains.

Illustrative configuration:

```toml
[storage.entries.admin]
path = "Admin"
class = "mirrored"
message = "Administrative and durable project documents."

[storage.entries.build]
path = "Build"
class = "transient"
message = "Regenerable build products."

[storage.annotations.shared_dataset]
path = "Datasets"
relationship = "external"
message = "Shared dataset intentionally stored on another volume."
```

Stable entry IDs are used as TOML keys and filesystem paths remain values.
This avoids forcing arbitrary path syntax into Taurworks' deliberately small
TOML writer contract.

A `storage.entries.*` declaration grants Taurworks responsibility for that
mapping. A `storage.annotations.*` declaration is descriptive only. An
unannotated external link remains valid and is simply reported without a
message.

### Decision 5: Machine-specific storage roots live in global configuration

Physical storage locations are machine-specific and therefore belong in
Taurworks' XDG-style global configuration rather than portable project
metadata.

Illustrative shape:

```toml
[workspace]
root = "/Users/example/Workspace"

[storage.mirrored]
root = "/Users/example/Library/CloudStorage/.../Taurspace"

[storage.transient]
mode = "system-temp"
subdir = "Taurspace"
```

The mirrored root is explicit. The transient root should be resolved through
platform temporary-directory conventions rather than hard-coding `/tmp` or a
macOS-specific path.

For Workspace projects, managed destination paths should initially be derived
deterministically from the project path relative to the Workspace plus the
entry path. Registered projects outside the Workspace may be audited, but
managed relocation for arbitrary external project roots is deferred until a
collision/identity policy is explicitly designed.

### Decision 6: Project metadata remains physically local

`ProjectRoot/.taurworks/` remains a real local directory and is not itself a
managed storage mapping. Taurworks currently uses `.taurworks` to establish
project-root identity and deliberately refuses to write through symlinked
metadata/config paths. The storage model should preserve this safety boundary.

### Decision 7: Do not globally weaken working-directory path safety

The current working-directory resolver requires a relative path and rejects a
resolved target that escapes the project root. Arbitrary external symlinks
should remain observable filesystem structure, but that does not imply they
should automatically become trusted Taurworks working-directory escapes.

Future managed-storage integration may allow a configured working directory to
traverse a Taurworks-managed storage entry only when Taurworks can verify that:

1. the logical mapping is explicitly declared;
2. the observed symlink/mapping matches the declaration; and
3. the target lies beneath the configured physical root for the declared
   storage class.

This is a narrow, auditable exception rather than a global relaxation of path
safety.

### Decision 8: Introduce a distinct `taurworks storage` namespace

Storage policy is neither purely project lifecycle nor repo-local development
workflow. It has both machine-global configuration and per-project operations.

The product model should therefore evolve to:

```text
taurworks project ...    logical project lifecycle and activation
taurworks dev ...        repository-local development workflows
taurworks storage ...    physical placement, lifecycle, and diagnostics
```

All three namespaces should share existing resolution, configuration,
diagnostics, and path-normalization services.

### Decision 9: Audit is the first implementation slice and is read-only

The first useful capability is deterministic observation, not relocation.
Initial commands:

```text
taurworks storage show
taurworks storage audit [PROJECT] [--format md|json]
```

The default audit should be shallow and non-following: inspect direct project
children plus explicitly declared paths, use `lstat`/non-following filesystem
operations where appropriate, and never recursively traverse an external
symlink.

The audit may collect inexpensive facts such as:

- logical path and filesystem kind;
- symlink target and internal/external/broken relationship;
- managed declaration and expected target, if any;
- Git-repository presence and configured remote metadata using offline Git
  inspection;
- annotations/messages; and
- deterministic findings.

It should not recursively calculate all sizes, enumerate every ignored file,
hash large trees, fetch Git remotes, or perform network reachability checks by
default. Expensive deep inspection is deferred to explicit future modes.

### Decision 10: Findings report facts; agents and humans make contextual judgments

The deterministic layer should use stable factual findings such as:

- `BROKEN_SYMLINK`
- `MANAGED_LINK_MISSING`
- `MANAGED_TARGET_MISMATCH`
- `MANAGED_TARGET_OUTSIDE_ROOT`
- `STORAGE_ROOT_UNCONFIGURED`
- `ANNOTATION_RELATIONSHIP_MISMATCH`
- `EXTERNAL_SYMLINK`
- `INTERNAL_SYMLINK`
- `GIT_REPOSITORY`
- `GIT_REMOTE_PRESENT`
- `GIT_REMOTE_ABSENT`

It should not emit contextual policy decisions such as
`SHOULD_MOVE_TO_PERSISTENT` or `BAD_EXTERNAL_SYMLINK` as if they were
filesystem facts.

The human or agent can combine the factual audit with project intent to
recommend a storage-class change.

### Decision 11: Human and JSON output share one typed audit model

The audit should construct one deterministic internal result and render it as
either human-readable Markdown/text or versioned JSON. The JSON output is a
first-class contract for agents and scripts, not a parser over CLI prose.

Initial JSON shape should include a schema version from the first release:

```json
{
  "schema_version": "1.0",
  "project": {
    "name": "ExampleProject",
    "root": "/Users/example/Workspace/ExampleProject"
  },
  "storage": {
    "mirrored_root": "...",
    "transient_root": "..."
  },
  "entries": [],
  "findings": [],
  "summary": {}
}
```

This follows Taurworks' existing `gather_*_diagnostics` / formatter separation
and gives agent tooling a stable, low-ambiguity interface.

### Decision 12: Start with one Agent Skill, backed by the CLI

The first Agent Skill is:

```text
taurworks-storage-audit
```

Its responsibilities are to:

1. resolve which project the user means;
2. invoke `taurworks storage show` when configuration context matters;
3. invoke `taurworks storage audit PROJECT --format json`;
4. explain findings conversationally;
5. treat healthy unmanaged external symlinks as informational rather than
   defects;
6. ask about ambiguous storage intent;
7. suggest classifications or future CLI operations; and
8. never mutate storage itself.

The skill must not independently scan the filesystem or reproduce the audit
rules. The CLI/library implementation is authoritative for facts; the skill
is an orchestration and interpretation layer.

The skill should use agent-neutral `SKILL.md` prose and a canonical package
source, with repository-local target copies for supported agent environments.
The initial design does not add a generalized Taurworks skill installer solely
for one skill; that abstraction should be revisited when multiple Taurworks
skills create demonstrated demand.

### Decision 13: Mutation commands are narrow and staged after dogfooding

Future command vocabulary should favor explicit operations:

```text
taurworks storage plan [PROJECT]
taurworks storage move PATH --class CLASS
taurworks storage reconcile [PROJECT]
taurworks storage gc
```

There is intentionally no initial high-blast-radius `taurworks storage
organize` command.

`plan` should remain non-mutating. `move` changes one explicitly named entry.
`reconcile` repairs only Taurworks-managed mappings. `gc` may delete only
Taurworks-owned transient material and should be implemented last, after the
ownership model is proven.

Cross-filesystem movement must be designed as an interruption-safe operation
before it is enabled. A first mutation slice may deliberately refuse
cross-device apply rather than ship an unsafe copy/delete implementation.

## Non-Goals

- Does not move any existing user data as part of this proposal.
- Does not make Google Drive, Dropbox, Time Machine, or GitHub a required
  Taurworks dependency; they are examples of storage/protection mechanisms.
- Does not infer storage policy directly from `.gitignore`.
- Does not classify every unmanaged external symlink as a problem.
- Does not recursively scan arbitrary external symlink targets by default.
- Does not make `.taurworks/` relocatable through the storage subsystem.
- Does not weaken working-directory path safety for arbitrary symlinks.
- Does not implement generalized multi-repository management.
- Does not add a high-blast-radius automatic workspace organizer.
- Does not make an Agent Skill a second implementation of storage semantics.
- Does not design a complete backup taxonomy; backup/protection status is
  related audit context but independent of storage placement.

## Implementation Plan

Implementation should proceed in separate reviewable stages. Adoption of this
proposal does not imply that later mutating stages must be implemented before
read-only dogfooding provides evidence that the model is correct.

### Stage 1 — Read-only storage foundation

Implement:

- global resolution for mirrored and transient storage roots;
- `taurworks storage show`;
- `taurworks storage audit [PROJECT]`;
- `--format md|json` with JSON `schema_version: "1.0"`;
- typed/structured audit results;
- shallow non-following topology classification;
- offline Git metadata inspection where useful; and
- focused filesystem and CLI tests.

Recommended module shape for the first slice:

```text
src/taurworks/storage.py
tests/storage_test.py
```

Keep the first implementation cohesive; split audit and mutation modules only
when mutation actually arrives and the separation earns its cost.

### Stage 2 — `taurworks-storage-audit` skill

After the Stage 1 audit contract is dogfooded and stable:

- add canonical package skill source;
- add self-hosted project copies for supported agent targets;
- ensure the skill invokes the JSON audit contract rather than reimplementing
  filesystem checks;
- add trigger/behavior evaluations; and
- extend package data only as required to ship the canonical skill.

### Stage 3 — Managed placement and planning

After audit evidence demonstrates correct topology understanding:

- add project-local managed storage declarations and descriptive annotations;
- add mirrored-root configuration setters as needed;
- implement `taurworks storage plan`;
- implement one-entry `taurworks storage move`; and
- implement `taurworks storage reconcile` for Taurworks-owned mappings only.

All mutating commands should be explicit, diagnostic, and dry-run/plan-first in
keeping with Taurworks guardrails.

### Stage 4 — Deferred lifecycle extras

Only after demonstrated demand:

- transient garbage collection;
- deep/size audits;
- Git bundle backup assistance;
- more detailed protection-status auditing;
- generalized Taurworks skill installation/rendering; and
- managed storage for registered projects outside the configured Workspace.

## Risks and Mitigations

### Risk: symlink topology becomes an implicit trust bypass

Mitigation: distinguish observation from Taurworks-managed trust. Unmanaged
external links are visible but do not automatically gain privileged path
resolution semantics.

### Risk: audit itself becomes expensive on high-churn projects

Mitigation: default to shallow, non-following inspection. Make recursive size,
ignored-file, and hashing operations explicit future modes.

### Risk: human CLI and agent behavior drift

Mitigation: one typed audit model and one JSON contract. Skills consume the CLI
contract instead of recreating filesystem logic.

### Risk: relocation introduces data loss or partial state

Mitigation: ship audit first; stage mutation separately; require preflight and
recoverable state; refuse cross-device mutation until an interruption-safe
transaction design is implemented.

### Risk: storage declarations over-specify the common case

Mitigation: persistent-local remains implicit. Only exceptions and explanatory
annotations need project metadata.

## Open Questions

The following are intentionally deferred until audit dogfooding provides real
examples:

- What optional deep-audit flags are actually useful (`--sizes`, `--ignored`,
  or another vocabulary)?
- What verification level is appropriate for eventual cross-filesystem moves?
- Should protection status become a formal audit sub-model once Time Machine,
  Git remotes, or bundle workflows are exercised in practice?
- At what number of Taurworks skills does a generalized target-aware skill
  installer become justified?

## Cross-References

- `project/design/design.md` — current Taurworks product and command model.
- `project/design/config_model.md` — global config, workspace root, project
  registry, and portable project path semantics.
- `project/design/unified_command_model.md` — command namespace rationale.
- `project/guardrails/agent_guardrails.md` — explicit, reversible,
  diagnostic-first safety posture.
- Logical Robotics Harness `lrh-design` / `lrh-proposal` skills — proposal
  structure and prior-art/design-decision discipline used to author this
  document.
- Logical Robotics Harness target-aware skills design — precedent for
  canonical Agent Skill sources with environment-specific install targets.
- Prosoc audit skills — precedent for orchestration skills consuming an
  authoritative audit procedure rather than duplicating it.

## Adoption Consequences

If this proposal is adopted, follow-up changes should update the canonical
Taurworks design documents rather than treating this proposal as a substitute
for them. In particular:

- `project/design/design.md` should recognize `taurworks storage ...` as a
  third product namespace;
- `project/design/config_model.md` should define the adopted global storage
  root and project declaration schemas;
- the roadmap should add the staged storage work; and
- implementation work items should be derived from the stages above.

Until adoption, this document records a proposed direction only; existing
Taurworks behavior remains authoritative.
