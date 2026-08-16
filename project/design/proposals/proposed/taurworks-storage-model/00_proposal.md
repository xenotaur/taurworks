---
id: PROP-TAURWORKS-STORAGE-MODEL
type: design_proposal
title: Taurworks Storage Model — Workspace, Taurspace, and Storage Auditing
status: proposed
created_on: 2026-08-15
updated_on: 2026-08-16
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
default; selected project entries may instead be explicitly placed beneath a
local mirror-designated `Taurspace` root or in transient system storage while
remaining visible at their normal project paths through Taurworks-managed
mappings.

A mirror-designated root is a local filesystem placement target. Google Drive,
Dropbox, Syncthing, or another external mechanism may synchronize or protect
that root, but Taurworks does not equate placement beneath a mirrored root with
proof that any external provider is configured, reachable, healthy, complete,
or current. Storage placement and protection remain separate concerns.

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
build products, dependency trees, and caches contain hundreds of thousands of
filesystem entries. Conversely, moving the whole workspace out of synchronized
storage is not appropriate when project roots also contain durable
administrative and project documents that benefit from external mirroring.

The desired model is therefore not "sync the whole workspace" or "sync none of
it." Taurworks should preserve the familiar logical organization while making
physical storage class explicit where needed. This follows Taurworks' existing
preference for explicit configuration, inspectable path resolution, and
conservative handling of side effects.

Stable logical paths are also an interoperability contract. Humans, shell
history, scripts, Git tooling, IDEs, and resumable agent sessions may all retain
references such as `~/Workspace/Project/...`. Physical relocation should
therefore preserve logical Workspace paths where practical rather than forcing
every consumer to rediscover a project's physical location.

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

`Workspace` is where humans and tools normally go to work. A local
mirror-designated `Taurspace` root contains durable material intentionally
placed where an external synchronizer may protect it. Transient storage is
explicitly regenerable/disposable storage outside the persistent workspace.
Workspace is a materialized working namespace, not necessarily a permanent
inventory of every dormant project the user owns.

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
  Git, temporary-directory, and external synchronization primitives should
  remain delegated to their established tools; Taurworks provides placement
  policy, diagnostics, and orchestration.
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

- Keep `Workspace` inside externally mirrored storage and symlink high-churn
  paths outward.
- Move whole projects outside `Workspace` and rely on Taurworks registration.
- Keep `Workspace` local and point only selected entries outward to other
  storage classes.

**Chosen: keep `Workspace` local and use it as the stable logical namespace.**

This reverses the dependency on file-sync symlink behavior. An external
synchronizer sees ordinary physical directories under a mirror-designated
root; the compatibility mappings live outside the synchronizer's watched tree.
New repositories, caches, worktrees, dependency trees, and generated files
therefore remain local by default without any special exclusion rule.

Stable Workspace paths are part of the execution environment, not merely a
human convenience. Physical placement may change during recovery, migration,
backup-policy changes, or machine reconfiguration while logical project paths
should remain stable where practical.

Workspace should therefore be understood as the namespace of projects and
project material currently materialized for local work. Dormant projects may
legitimately exist only in another configured storage location until they are
reactivated; this does not introduce a fourth storage class or a formal archive
state in the initial design.

### Decision 2: Persistent-local is the default storage class

Taurworks defines three lifecycle/placement classes:

- `persistent`: survives reboot and lives in ordinary local project storage;
  this is the implicit default for normal files and directories under
  `Workspace`.
- `mirrored`: durable data physically located beneath a configured local root
  designated for external mirroring and normally exposed at its logical
  project path through a managed mapping.
- `transient`: regenerable/disposable data physically located beneath a
  Taurworks namespace in an OS-appropriate temporary root.

No separate physical persistent root is required in the initial design.
Keeping ordinary persistent data physically in `Workspace` minimizes
indirection and makes the common case require no metadata.

`mirrored` describes Taurworks placement intent. It does not by itself prove
that an external synchronizer is configured, reachable, healthy, complete, or
up to date. Backup/protection status is deliberately separate from storage
class. A persistent Git repository may be protected by a remote; a persistent
checkpoint may be protected by Time Machine; a persistent cache may be
reproducible and intentionally unbacked-up; a mirrored directory may be placed
correctly even while its external provider is temporarily paused or unhealthy.

#### Non-normative classification examples

The following examples preserve the motivating use cases without turning them
into automatic policy. They are guidance for a human or agent interpreting an
audit, not classification rules enforced by Taurworks:

| Example | Typical class | Rationale |
|---|---|---|
| Administrative and project documents | `mirrored` | Durable human-authored material benefits from external synchronization. |
| Local Git repository with no remote | `mirrored` candidate | Until another durable copy exists, mirroring may provide useful protection despite Git churn. |
| Remote-backed Git repository | `persistent` candidate | The live checkout can remain local while committed history is protected by its remote. |
| Agent clones and worktrees | `persistent` | High-churn development state should normally avoid file-sync services. |
| Corpora, checkpoints, and reusable caches | `persistent` | They must survive reboot but may be too large or noisy for mirroring. |
| Regenerable dependency/build trees and scratch output | `transient` candidate | Taurworks may discard them when their producing workflow can recreate them. |

These examples deliberately use words such as "typical" and "candidate."
Actual placement remains a user/project decision informed by audit facts,
backup requirements, reproducibility, cost, and workflow needs.

#### Non-normative lifecycle and migration examples

Storage class is distinct from whether a project is currently active. Two
migration strategies are both legitimate:

```text
active/high-churn project
    -> normalize earlier
    -> materialize in Workspace
    -> place only selected durable entries beneath mirror-designated storage

cold/low-churn project
    -> may be parked wholesale beneath mirror-designated storage
    -> defer descendant classification while inactive
    -> audit/classify/materialize in Workspace when reactivated
```

Whole-tree cold parking is a migration and lifecycle technique, not a fourth
storage class and not automatically Taurworks-managed topology. A parked tree
may later be decomposed into persistent, mirrored, and transient material when
real work resumes.

### Decision 3: Storage class, management ownership, and link topology are independent concepts

Taurworks must not treat arbitrary symlinks as something it "permits" or
"forbids." Projects may legitimately contain links to sibling projects,
shared datasets, external volumes, temporary recovery locations, or other
resources.

An audit therefore observes management ownership separately from link
topology:

- `managed_by_taurworks`: whether Taurworks owns and may reconcile the logical
  mapping;
- `relationship`: one of `none`, `internal`, `external`, or `broken`, describing
  the observed filesystem topology independently of ownership.

These dimensions may coexist. For example, a normal mirrored mapping is both
`managed_by_taurworks: true` and `relationship: external`; a missing or broken
managed mapping may be both managed and `relationship: broken`.

An unmanaged external symlink is informational by default, not an error. A
broken link is a finding because it is broken. A Taurworks-managed link whose
target disagrees with its declared storage mapping is a finding because the
managed state is inconsistent.

### Decision 4: Taurworks owns only explicitly managed, project-contained mappings

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
mapping. That grant is deliberately narrow: managed `path` values must be
normalized relative paths within the selected project. Absolute paths and
paths containing `..` are invalid. Existing parent components must not escape
through an unmanaged symlink; a path whose traversal leaves the logical
project root is not eligible for managed ownership. The derived physical
destination must likewise remain beneath the configured root for its declared
storage class.

The initial design does not provide an outside-project opt-in for managed
entries. Cross-project or external-volume relationships remain ordinary user
filesystem structure and can be described with `storage.annotations.*`
without granting Taurworks move/reconcile authority over them.

A `storage.annotations.*` declaration is descriptive only. An unannotated
external link remains valid and is simply reported without a message.

### Decision 5: Machine-specific placement roots live in global configuration

Physical storage locations are machine-specific and therefore belong in
Taurworks' XDG-style global configuration rather than portable project
metadata.

Illustrative initial shape:

```toml
[workspace]
root = "/Users/example/Workspace"

[storage.mirrored]
root = "/Users/example/Taurspace"

[storage.transient]
mode = "system-temp"
subdir = "Taurspace"
```

The mirrored root is an ordinary local filesystem path designated for external
mirroring. Taurworks does not require it to be physically owned by Google
Drive, Dropbox, or another provider. A synchronizer may be configured to watch
that local root, but provider configuration and provider health are outside the
initial placement contract.

The initial implementation may support one default mirrored root for
simplicity, but the data model must not make "exactly one mirror forever" an
architectural invariant. Different machines may intentionally materialize
different projects and may use different external providers. Future evidence
may justify named mirrored roots, for example one synchronized by Google Drive
and another by Dropbox. The initial TOML syntax need not commit to that future
shape before dogfooding establishes demand.

The transient root should be resolved through platform temporary-directory
conventions rather than hard-coding `/tmp` or a macOS-specific path. The
`Taurspace` name is intentionally reused as the Taurworks-owned namespace
beneath the default mirrored or transient physical roots: storage class is
established by the configured containing root, not by the basename of the
namespace itself.

For Workspace projects, managed destination paths should initially be derived
deterministically from the project path relative to the Workspace plus the
entry path. Registered projects outside the Workspace may be audited, but
managed relocation for arbitrary external project roots is deferred until a
collision/identity policy is explicitly designed.

#### Storage-root separation invariant

The configured Workspace root, every configured mirrored root, and the
resolved transient root must remain physically distinct enough that one
storage class cannot silently collapse into another. Taurworks should detect
and report configurations where these roots overlap in ways that defeat the
storage model, including at least:

- a mirrored root is equal to or nested beneath the Workspace root;
- the Workspace root is nested beneath a mirrored root;
- the transient root is equal to or nested beneath a mirrored root;
- two configured placement roots overlap in a way that makes ownership or
  storage class ambiguous; or
- another configured relationship would cause data classified into one class
  to be observed by the backend assigned to another class.

A read-only audit should surface this as a factual configuration finding such
as `STORAGE_ROOT_OVERLAP`. The initial implementation need not reject every
unusual nesting pattern categorically; it should report the resolved paths and
relationship so a human or agent can distinguish an intentional arrangement
from one that recreates the synchronization problem this design is intended to
avoid. Mutating storage commands, once implemented, should fail safely when an
overlap would make the requested operation ambiguous or unsafe.

### Decision 6: Project metadata remains physically local

`ProjectRoot/.taurworks/` remains a real local directory and is not itself a
managed storage mapping. Taurworks currently uses `.taurworks` to establish
project-root identity and deliberately refuses to write through symlinked
metadata/config paths. The storage model should preserve this safety boundary.

A wholly parked cold tree may therefore be a legacy or not-yet-normalized
storage state rather than a canonical active Taurworks project. When it is
reactivated and materialized in Workspace, its active `.taurworks/` metadata
should again be real local project metadata.

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

The public Stage 1 audit remains project-oriented. It should not acquire
arbitrary-filesystem support merely to satisfy hypothetical future use cases.
The default audit should be shallow and non-following: inspect direct project
children plus explicitly declared paths, use `lstat`/non-following filesystem
operations where appropriate, and never recursively traverse an external
symlink.

The audit may collect inexpensive facts such as:

- logical path and filesystem kind;
- `managed_by_taurworks` ownership state;
- symlink target and `none`/`internal`/`external`/`broken` relationship;
- managed declaration and expected target, if any;
- configured physical placement root associated with an entry, if any;
- Git-repository presence and configured remote metadata using offline Git
  inspection;
- annotations/messages; and
- deterministic findings.

It should not recursively calculate all sizes, enumerate every ignored file,
hash large trees, fetch Git remotes, perform network reachability checks, or
claim external mirror health by default. Expensive deep inspection and provider
health are separate future concerns.

### Decision 10: Findings report facts; agents and humans make contextual judgments

The deterministic layer should use stable factual findings such as:

- `BROKEN_SYMLINK`
- `MANAGED_LINK_MISSING`
- `MANAGED_TARGET_MISMATCH`
- `MANAGED_TARGET_OUTSIDE_ROOT`
- `STORAGE_ROOT_UNCONFIGURED`
- `STORAGE_ROOT_OVERLAP`
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
recommend a storage-class change. Likewise, being physically beneath a
mirror-designated root is a fact Taurworks can report; external provider health
is not implied by that fact.

### Decision 11: Human and JSON output share one typed audit model

The audit should construct one deterministic internal result and render it as
either human-readable Markdown/text or versioned JSON. The JSON output is a
first-class contract for agents and scripts, not a parser over CLI prose.

The first schema should avoid making exactly one mirrored root a permanent
contract. The initial implementation may expose only a default root, but the
shape should remain extensible to multiple named roots without conflating
provider identity with Taurworks placement semantics. An illustrative shape is:

```json
{
  "schema_version": "1.0",
  "project": {
    "name": "ExampleProject",
    "root": "/Users/example/Workspace/ExampleProject"
  },
  "storage": {
    "mirrored_roots": [
      {
        "name": "default",
        "root": "/Users/example/Taurspace"
      }
    ],
    "transient_root": "..."
  },
  "entries": [
    {
      "path": "Admin",
      "storage_class": "mirrored",
      "storage_root": "default",
      "managed_by_taurworks": true,
      "relationship": "external"
    }
  ],
  "findings": [],
  "summary": {}
}
```

This follows Taurworks' existing `gather_*_diagnostics` / formatter separation
and gives agent tooling a stable, low-ambiguity interface. The exact
configuration syntax for selecting a non-default mirror may remain deferred
until multiple roots are demonstrated, but the first machine-readable contract
should not gratuitously foreclose that extension.

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

### Decision 14: Manual migration and lazy normalization are valid dogfooding inputs

Taurworks does not need to have created a topology in order to audit it.
Manual or provider-assisted migration may therefore precede mutation support.
The storage subsystem should expect to encounter unmanaged compatibility
symlinks, parked cold trees, stale registrations, legacy layouts, and partially
normalized projects during migration and report their observable state rather
than assuming every tree already matches the final managed model.

This creates a deliberate feedback loop:

```text
manual migration
    -> real pre/post-migration evidence
    -> storage audit dogfooding
    -> refined plan/move/reconcile requirements
    -> later narrow automation
```

`taurworks storage move` is therefore not a prerequisite for the initial
Workspace/Taurspace migration. Active/high-churn projects may be normalized
earlier; cold/low-churn projects may be parked wholesale and normalized only
when reactivated.

### Decision 15: Preserve and evaluate broader applicability without implementing it

The initial storage subsystem is project-oriented, but its placement concepts
may prove useful for other heterogeneous filesystem trees. Implementation
should not add complexity solely to support hypothetical non-project use cases,
but it should avoid unnecessary assumptions that make such reuse impossible
when a comparably simple representation remains available.

The governing anti-foreclosure rule is:

```text
if two designs are comparably simple:
    prefer the one that does not gratuitously hard-code the current
    project/provider corpus

if generalization materially increases current complexity:
    implement the simpler project-oriented design and record the limitation
```

During dogfooding, maintainers should periodically compare the model against
representative non-project trees such as `~/Music` and `~/Pictures`. These are
evidence probes, not acceptance criteria for the project-storage MVP. A probe
may exercise an internal inspection library or a scratch harness rather than
requiring public arbitrary-path CLI support.

Useful probe questions include:

- Which filesystem/topology facts generalize unchanged?
- Which assumptions require `.taurworks/`, Workspace membership, project
  identity, Git metadata, or project-relative destination derivation?
- Which non-project use cases introduce new concepts such as live database
  packages, static/quiescent snapshots, or re-downloadable application data?
- Would preserving broader applicability require a small generalization, a
  reusable lower-level library, a sibling tool, or an inappropriate expansion
  of Taurworks itself?

The project-storage rollout should conclude with an explicit evidence/design/
cost-benefit review that returns `GO`, `NO-GO`, or `DEFER` on launching a
separate generalization effort. That review is part of project-storage
closeout; implementing the expansion is not.

## Non-Goals

- Does not move any existing user data as part of this proposal.
- Does not make Google Drive, Dropbox, Syncthing, Time Machine, GitHub, or
  another protection provider a required Taurworks dependency; they are
  examples of mechanisms orthogonal to storage placement.
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
- Does not implement general-purpose storage management for arbitrary
  filesystem trees such as media libraries, home-directory data, or other
  non-Taurworks project roots. Targeted applicability probes and the final
  generalization assessment remain in scope as evidence work.

## Implementation Plan

Implementation should proceed in separate reviewable stages. Adoption of this
proposal does not imply that later mutating stages must be implemented before
read-only dogfooding provides evidence that the model is correct.

### Stage 1 — Read-only storage foundation

Implement:

- global resolution for Workspace, the initial/default mirrored root, and the
  transient root, including storage-root overlap diagnostics;
- an internal representation that can evolve to multiple named mirrored roots
  without changing the meaning of `mirrored`;
- `taurworks storage show`;
- `taurworks storage audit [PROJECT]`;
- `--format md|json` with JSON `schema_version: "1.0"`;
- typed/structured audit results;
- separate managed-ownership and link-topology classification;
- shallow non-following topology classification;
- offline Git metadata inspection where useful; and
- focused filesystem and CLI tests.

Stage 1 remains project-oriented. Arbitrary-path audit support is not required
for completion.

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

After Stage 1/2 dogfooding provides a stable inspection core, conduct the first
non-project applicability probe against representative trees such as `~/Music`
or `~/Pictures`. Record reusable facts, project-specific assumptions, missing
concepts, and any accidental foreclosure found. Do not turn probe findings into
Stage 2 blockers unless they expose an equally simple representation that
avoids unnecessary lock-in.

### Stage 3 — Managed placement and planning

After audit evidence demonstrates correct topology understanding:

- add project-local managed storage declarations and descriptive annotations;
- validate managed paths as normalized project-relative paths, reject absolute
  paths and `..`, reject escape through unmanaged symlink parents, and verify
  each derived destination remains beneath its configured storage root;
- add default mirrored-root configuration setters as needed;
- defer non-default mirror-selection syntax until real multi-root demand is
  demonstrated, while preserving an extensible internal/JSON representation;
- implement `taurworks storage plan`;
- implement one-entry `taurworks storage move`; and
- implement `taurworks storage reconcile` for Taurworks-owned mappings only.

All mutating commands should be explicit, diagnostic, and dry-run/plan-first in
keeping with Taurworks guardrails.

After managed-placement dogfooding, revisit the applicability evidence to check
whether new representation choices unnecessarily foreclosed reuse. This is a
design checkpoint, not a requirement to implement non-project support.

### Stage 4 — Deferred lifecycle extras

Only after demonstrated demand:

- transient garbage collection;
- deep/size audits;
- Git bundle backup assistance;
- more detailed protection-status auditing;
- generalized Taurworks skill installation/rendering; and
- managed storage for registered projects outside the configured Workspace.

### Stage 5 — Project-storage closeout and generalization decision

After the Workspace/Taurspace migration and project-storage dogfooding are
substantially complete, create a final evidence/design/cost-benefit work item.
It should synthesize at least:

- active-project migration experience;
- cold-project parking/reactivation experience;
- Workspace/Taurspace migration evidence;
- audit/skill/mutation dogfooding;
- multi-machine or multi-provider evidence, if any;
- targeted `Music`/`Pictures` applicability probes; and
- implementation complexity accumulated in project-specific code.

The review should answer:

1. Which storage concepts generalized naturally?
2. Which assumptions are intrinsically Taurworks-project-specific?
3. What new requirements do non-project trees introduce?
4. Would reuse require a small generalization, a shared lower-level library, a
   sibling application, or a major architectural rewrite?
5. What implementation and maintenance cost would the expansion create?
6. What concrete benefit would it provide?
7. Does Taurworks remain the correct product boundary?

The outcome must be one of:

- `GO`: open a separate design proposal/effort for broader storage management;
- `NO-GO`: document why the project-storage model should remain project-only;
- `DEFER`: identify the missing evidence and a concrete revisit condition.

Stage 5 does not implement the expansion.

## Risks and Mitigations

### Risk: symlink topology becomes an implicit trust bypass

Mitigation: distinguish observation from Taurworks-managed trust. Unmanaged
external links are visible but do not automatically gain privileged path
resolution semantics, and managed entry paths may not escape the selected
project through `..`, absolute paths, or unmanaged symlink parents.

### Risk: storage roots accidentally collapse lifecycle boundaries

Mitigation: audit resolved Workspace, every configured mirrored root, and the
transient root for overlap and surface the relationship explicitly. Future
mutation commands fail safely when overlap makes the target storage class
ambiguous or unsafe.

### Risk: mirror placement is mistaken for provider health

Mitigation: define `mirrored` as local placement intent only. Taurworks may
report that content lies beneath a configured mirror-designated root without
claiming that Google Drive, Dropbox, or another external provider is configured,
healthy, current, or complete.

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

### Risk: broader-applicability evidence causes scope creep

Mitigation: keep non-project support outside implementation acceptance criteria.
Use a small number of explicit evidence checkpoints, prefer project-oriented
simplicity when generalization would materially increase present complexity,
and require a separate post-dogfood `GO` decision before starting expansion.

### Risk: project-specific implementation accidentally forecloses cheap reuse

Mitigation: apply the anti-foreclosure rule during schema/API review. When an
equally simple representation avoids hard-coding one provider, one mirror root,
or another incidental assumption, prefer it; otherwise record the limitation
and continue with the scoped project implementation.

## Open Questions

The following are intentionally deferred until audit dogfooding provides real
examples:

- What optional deep-audit flags are actually useful (`--sizes`, `--ignored`,
  or another vocabulary)?
- What verification level is appropriate for eventual cross-filesystem moves?
- Should protection status become a formal audit sub-model once Time Machine,
  Git remotes, bundles, or external synchronization workflows are exercised in
  practice?
- What evidence, if any, justifies multiple named mirrored roots and explicit
  per-entry mirror selection beyond the default root?
- Which parts of the storage model are intrinsically Taurworks-project-specific,
  and which may form a reusable lower-level storage-placement abstraction?
  Answer this through project dogfooding and targeted non-project applicability
  probes rather than expanding initial implementation scope.
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
  root and project declaration schemas while preserving the distinction
  between local placement and external protection;
- the roadmap should add the staged storage work, including the final
  evidence/design/cost-benefit generalization assessment;
- implementation work items should be derived from the stages above; and
- dogfooding evidence should include the staged Workspace/Taurspace migration,
  cold-project behavior, and targeted non-project applicability probes without
  making the latter an implementation requirement.

Until adoption, this document records a proposed direction only; existing
Taurworks behavior remains authoritative.
