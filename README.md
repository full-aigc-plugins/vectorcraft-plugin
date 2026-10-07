# VectorCraft Agent Plugin

Create Logo, icon and brand assets as `.vectorcraft` with applicable SVG, PDF and PNG exports.

Current plugin: `0.1.0-dev.33`; skill source: `0.1.0-dev.31`; 13 independent skills.

Verified first-use platform: macOS arm64 and Python 3.11+. Pinned runtimes install into the user data directory; skill files stay in their host-loaded directory. These are development releases; complete V1 acceptance and generic Skills CLI installation remain open.

Maintainer source validation rejects symbolic links, incomplete locks and version-named branches, and checks all declared sources before replacing any managed skill. Published skill/runtime identities remain unchanged. [Snapshot preflight architecture](docs/Skill-Snapshot-Self-Contained.md).

## First use

Invoke **`vectorcraft-use`** in your host. For direct CLI use, set `SKILL_DIR` to the absolute directory of the `SKILL.md` actually loaded by that host. It may be under user/project `.agents/skills`, the plugin, or a host cache; use the actual path. Each entry below installs/verifies its locked runtime before invoking it.

<!-- CRAFT_FIRST_USE_START -->
```bash
: "${SKILL_DIR:?Set to the actual loaded skill directory}"
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- --version
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- commands
```
<!-- CRAFT_FIRST_USE_END -->

Read the [editable workflow](skills/vectorcraft-use/references/workflow.md) for inputs, native projects and targeted revisions. [Setup and skill entry](skills/vectorcraft-use/SKILL.md) · [version-bound history](RELEASE-HISTORY.md). Command/version queries verify installation and discovery; they do not constitute creative completion.

[First-use navigation evidence](docs/evidence/craft-readme-first-use-navigation-20261007.json).

Fixed installed path acceptance: standalone skills and Art mixed work pass native creation/reopen, targeted revision and export under Chinese-and-space paths; Art also verifies moved delivery. Skills/runtime identities stay unchanged. This is bounded macOS arm64 first-use evidence. [Path acceptance evidence](docs/evidence/craft-fixed-unicode-path-first-use-20261007.json).

Historical source candidate before the fixed release: structurally invalid runtime/Node locks now return local setup diagnostics before runtime writes/downloads. Five candidate native first-use checks pass; published plugin snapshots remain unchanged until separate immutable release acceptance. [Lock diagnostics candidate](docs/VectorCraft-Lock-Shape-Architecture.md).

---

Fixed native first-use and complete-command recovery acceptance passed:58 standalone cold installations, ten Art all-domain cold installations, four partial-download SSL EOF recoveries,72 post-save faults, four healthy command revisions and mixed HD revision/recovery/moved delivery. Installed identities remain unchanged. Only domain2.10/8.11 and Art4.10 close; exhaustive2639-command, GUI, model, generic Skills CLI and fullV1 gates remain open. [Version-bound evidence](docs/evidence/codex-native-download-first-use-20261007.json).

Historical release record: Current plugin: `0.1.0-dev.21`; skill source: `0.1.0-dev.19`; gradient/appearance recipes included; 12 fixed installed cold appearance cases pass; Art distribution update pending; full V1 remains open.

Historical candidate observation before fixed acceptance: Native download recovery candidate: up to three read-only attempts discard partial archives. Earlier fixed cold installs failed on SSL EOF; new fixed installed acceptance remains open.

Previous version-bound plugin: `0.1.0-dev.18`; skill source: `0.1.0-dev.16`; complete-command inner JSON fix is published, fixed installed acceptance pending.

Previous version-bound failed-stage acceptance: plugin dev.17, standalone source dev.15. All58 independent CLI cold starts,24 original-stage native fault cases and37 native scene tests plus6 contracts pass. Art77 bundle upgrade remains open. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).

Fixed domain-client first use: Film plugin dev.16 / source dev.15; Effect/Photo/Vector plugin dev.15 / source dev.14. Codex discovers 58 skills without errors. Actual installed copies pass 24 post-save faults and four healthy public workflows; the published Art engine with the installed Vector client passes six faults. All58 installed identities remain unchanged. Art dev.75 still bundles earlier domain sources; exhaustive command/GUI/model acceptance remains open. [Version-bound evidence](docs/evidence/codex-public-workflow-session-first-use-20261007.json).
Previous version-bound protocol recovery acceptance passed: 288 cases across 48 standalone source skills, 24 cases in actual installed copies, four healthy revision cases, and 58 unchanged installed skill identities. See [fixed evidence](docs/evidence/codex-protocol-fault-first-use-20261007.json). Exhaustive command/GUI acceptance and the Art domain-bundle upgrade remain open.

Protocol fault repair candidate: all 12 independently copied skills pass separate empty public-runtime installation and six faulty replies after real native save (72 cases; zero skips). Requests are not replayed; unknown receipts, saved-project reopening and delivery/skill preservation are checked. [Evidence](docs/evidence/protocol-fault-first-use-20261007.json). Fixed installed release and Art bundle upgrade remain separate gates.

Fixed plugin 0.1.0-dev.13 / skills 0.1.0-dev.12 installed revision acceptance passes: isolated Codex discovers all 58 skills without loading errors; this installed domain skill completes the documented cold creation/revision plans, saved-project reopening and non-target preservation. All58 installed digests remain unchanged; current fixed release CI passes. [Fixed revision evidence](docs/evidence/codex-complete-command-revision-first-use-20261007.json). Full command/GUI/model acceptance remains open.

All 12 domain skills pass the paired revision plans when copied alone and installed from separate empty public runtimes (79.101 seconds; zero skips). [Revision evidence](docs/evidence/complete-command-revision-first-use-20261007.json). Fixed installation of the updated snapshot remains a separate gate.

The complete-command entry now includes paired executable creation/revision recipes, explicit selection prerequisites after reopening, and native persisted-state/non-target checks. Each standalone skill includes both JSON plans. [Usage](skills/vectorcraft-use/references/command-usage.md#7-可执行局部返工--executable-targeted-revision). Full per-command and GUI acceptance remains open.

Previous version-bound release first use passed: isolated Codex 0.153.4 discovers all 58 skills without loading errors; every installed skill independently cold-installs its public locked runtime (385.234 seconds); installed domain command samples and Art 1080p mixed revision/recovery/package checks pass. All installed skill digests remain unchanged; fixed CI and five-bundle rebuild pass. [Version-bound evidence](docs/evidence/codex-complete-command-first-use-20261007.json). Generic Skills CLI installation, full command/GUI and creative acceptance remain open.

## Complete native command entry

All 12 standalone skills now pass separate empty-runtime installation from locked public CLI archives, followed by native creation, save/reopen, domain assertions and rendered image checks (74.946 seconds; zero skips). [Cold-first-use evidence](docs/evidence/complete-commands-cold-first-use-20261007.json). This verifies this complete-command sample in every skill; exhaustive command/GUI and actual host installation remain separate.

Published development snapshot: skills dev.11 / plugin dev.12; bounded fixed-host first use passed.

All 585 commands now have verbatim parameters, skill routing, and same-session invocation through `commands.py list / describe / check / run`. Live enabled state is checked; the existing 27-operation delivery workflow remains bounded. GUI commands require explicit bridge mode. Complete registry coverage does not establish full command acceptance.

[Architecture and usage](docs/VectorCraft-Complete-Commands-Architecture.md) · [Complete reference](skills/vectorcraft-use/references/command-reference.md) · [Runnable example](skills/vectorcraft-use/examples/commands-advanced.json)

Independent-skills-driven Editable vector brand assets and multi-artboard design.

[English](README.md) | [简体中文](README.zh-CN.md)

## Current release and reproducible host checks

Previously verified plugin/skill suite: `0.1.0-dev.3`. Codex 0.147.0 and 0.153.4 installed five fixed public releases and discovered all 58 enabled namespaced skills with zero loading errors and matching source digests. Five representative workflows passed through installed task-skill entrypoints on 0.147.0, including native projects, targeted revisions and the mixed ArtCraft online workflow. Model dispatch, desktop GUI, final creative review and full interchange fidelity remain unverified.

[Host verification design](docs/VectorCraft-Host-Verification-Architecture.md) · [Version-bound evidence](docs/evidence/codex-skill-suite.json). Historical milestones below retain their original scope; the current manifest and locks own version identity.

> Development release. Fixed-tag Codex installation, skill discovery and representative native workflows have passed; complete product and creative acceptance remain open.

Implementation has started in the independent skills package. The isolated first-use installer is tested on macOS arm64; complete creative workflows and plugin host acceptance remain pending. [Evidence](docs/evidence/bootstrap-tests.json)

The independent skill now includes a native workflow helper: shapes and paths, Boolean union, editable text, two artboards, SVG/PNG/PDF exports and targeted recoloring were exercised. It preserves unbound objects and exports in the fixture. This does not prove full plugin acceptance. [Workflow evidence](docs/evidence/vector-workflow-tests.json)

## Positioning

Create logo and icon assets in .vectorcraft, SVG and PNG; change a brand color and update bound variants while preserving unrelated colors.

For creators who need editable native projects, repeatable revisions and reliable automation.

## At a glance

```text
Intent + assets
  -> independent Skills (pinned development release)
  -> public skill workflow / ArtCraft adapter
  -> verified runtime / child adapter
  -> native project + preview + export + evidence
```
| Property | Value |
| :--- | :--- |
| Plugin ID | vectorcraft |
| Metadata version | 0.1.0-dev.33 |
| Stage | implementation-in-progress |
| Skills source | vectorcraft-skills / v0.1.0-dev.31 |
| Execution | Upstream CLI; ArtCraft uses child adapters |
| Host compatibility | Codex development install/discovery pass; GUI and other hosts pending |
| License | Apache-2.0 (original repository content) |


## Capabilities and boundaries

| Capability | Behavioral boundary | Status |
| :--- | :--- | :--- |
| Paths, shapes and coordinates | Define artboard coordinates, units, control points, path closure and strokes; preview pixels are not vector path authority. | Full scope pending |
| Grouping and boolean operations | Record operand IDs, boolean operation and result identity with a pre-operation checkpoint; failure must not destroy source objects. | Full scope pending |
| Brand colors and text | Bind brand colors using explicit tokens instead of global color replacement; retain text and font dependencies and report editability loss when outlining. | Full scope pending |
| Artboards and variants | Give each artboard a stable ID, name, size and output mapping; define preview ordering and export ranges without index-base ambiguity. | Full scope pending |
| Interchange fidelity scope | Validate native .vectorcraft, SVG, PDF and PNG separately; report rasterized effects and keep native sources when interchange cannot preserve them. | Full scope pending |
| Brand variant revision | Update related variants from token and asset dependencies and verify that unrelated object properties and outputs remain unchanged. | Full scope pending |

Does not rewrite upstream editors, silently change native deliverable formats, or claim GUI/cross-platform acceptance.

## Architecture and documentation

- [Complete runtime architecture](docs/VectorCraft-Runtime-Architecture.md)
- [Technical plan and roadmap](product-docs/VectorCraft/en/5%E3%80%81VectorCraft-Technical-Plan.md)
- [V1 PRD and requirement mapping](product-docs/VectorCraft/en/V1/5%E3%80%81VectorCraft-PRD-V1.md)
- [Complete documentation index](docs/README.md)
- [OpenSpec proposal](openspec/changes/establish-v1-plugin/proposal.md)
- [OpenSpec tasks](openspec/changes/establish-v1-plugin/tasks.md)

- [Domain technical design](docs/VectorCraft-Domain-Design.md)

## Currently executable quick start

```bash
python3 scripts/validate_docs.py
openspec validate establish-v1-plugin --strict --no-interactive
```
These commands validate documentation and specifications, not product workflows. OpenSpec validation uses 1.13.1; this repository does not install tools automatically.

After installing the official CLI, perform a basic check:

```bash
vectorcraft-cli --version
```

The recorded result is 0.2.0. The public independent-skill bootstrap and workflow are development entry points; plugin-host installation remains unverified.

## Configuration and runtime

Target configuration includes CLI paths, allowed read/write roots, execution mode, budget, timeout and output directory; the configuration schema is not implemented yet. The skills lock pins the published source commit and whole-skill digest. Runtime lock hashes identify real official artifacts and establish only the recorded platform’s smoke evidence.

## Reliability and security

Planned safeguards include project write locks, revision preconditions, persisted intent, idempotency keys, outcome reconciliation, native checkpoints, artifact hashes and bounded revisions. Secrets are host-managed references; asset metadata is never an execution instruction.

## Verification and maturity

[Sanitized CLI evidence](docs/evidence/runtime-baseline.json)

| Layer | Status |
| :--- | :--- |
| Upstream CLI and read-only MCP | Observed on macOS arm64 only |
| Independent skill and adapter | Technical workflow tested; full harness pending |
| Native project and creative acceptance | Native technical cases pass; creative acceptance pending |
| Target host installation | Codex controlled install/discovery pass; full host acceptance pending |


## Roadmap and contribution

| Phase | Deliverable | Exit evidence |
| :--- | :--- | :--- |
| D0 | Bilingual documentation and OpenSpec baseline | Document, link and spec validation; implementation tasks remain open |
| M1 | Independent skills and runtime adapter | Clean installation, checksums and real MCP invocation |
| M2 | Complete domain workflow | Representative task, native reopen, decode and targeted revision |
| M3 | ArtCraft cross-plugin collaboration | Version propagation, selective invalidation and interruption recovery |
| M4 | Host and release acceptance | Actual host installation, platform evidence and synchronized catalogs |

Change OpenSpec before behavior; check a task only after actual acceptance. Maintain both document languages. See CONTRIBUTING.md and AGENTS.md.

## License and upstream

Original content uses [Apache-2.0](LICENSE). This is a third-party integration design, not upstream endorsement. Treat the four apps’ code licenses separately from ArtCraft/Services restrictions; do not copy restricted source or brand assets.

[Upstream VectorCraft](https://github.com/storytold/vectorcraft) · [Issues](https://github.com/full-aigc-plugins/vectorcraft-plugin/issues)

Independent skills are pinned at the current published development tag `v0.1.0-dev.4`, including the exact source commit and whole-skill digest in `skills.lock.json`. Verify using `python3 scripts/vendor/skill_vendor.py check`. These source snapshots do not establish plugin-host acceptance or production readiness.

## Development skill installation and use

Install the independent skill: `npx skills add full-aigc-skills/vectorcraft-skills --skill vectorcraft-use`. Run the public entry from the actual installed directory; this plugin snapshot includes the same skill.

```bash
python3 -I -B skills/vectorcraft-use/scripts/bootstrap.py
python3 -I -B skills/vectorcraft-use/scripts/workflow.py --help
```

First use installs the pinned official CLI into user-level storage. Requires macOS arm64 and Python 3.11+. Use the bundled example with real input assets; consult SKILL.md for delivery and revision contracts. [Source verification](docs/evidence/skill-publication.json).

## Codex development host checks

All five plugins installed from public tags into an isolated Codex configuration. App-server discovered their namespaced skills without loading errors; the installed ArtCraft entry produced four native projects. [Host evidence](docs/evidence/codex-installation.json). These controlled development checks do not establish desktop GUI, other hosts, complete creative or production marketplace acceptance.

Development version `0.1.0-dev.1` pins the independent skill install-lock fix: bounded coordination for concurrent installation/reuse, with no native task replay.

The current development milestone adds hash-bound exchange loss reports to native deliveries. lost, observed and unknown are separate; derivatives never substitute for native projects. Font/effect/mask fidelity across editors remains unverified, so full exchange acceptance stays open.

## CLI and task skill suite

The source suite contains 12 independently installable skills with setup, public CLI operations and focused tasks. [Architecture and catalogue](docs/VectorCraft-Skill-Suite-Architecture.md). Runtime and plugin versions are separate; prior host evidence retains its original version scope.

Previous version-bound plugin: `0.1.0-dev.5`; skill suite: `0.1.0-dev.4`. The corrected examples resolve scripts from the actual host-loaded `SKILL.md` directory. All skills passed isolated entry-point checks in user, project and plugin layouts with spaces. [Path evidence](docs/evidence/installed-skill-paths.json). Earlier host evidence above covers its recorded release; existing installations require an update.

Plugin `0.1.0-dev.5` corrects the whole-skill digests by fetching the immutable public source tag, without local Python caches. Plugin tag `v0.1.0-dev.4` is superseded and must not be installed because its source digests included ignored development caches.

Current plugin `0.1.0-dev.6` pins skill suite `0.1.0-dev.5`. Nine task skills each cold-installed and performed real native edits; selection, image embedding, symbol reuse and unaffected boards are verified. Full regression: 38 passed, no skips. [Evidence](docs/evidence/task-skill-first-use.json). Full creative/GUI/model acceptance remains pending.

Current fixed-release host verification (2026-10-06): Codex 0.153.4 installs all five current pinned plugins and discovers all 58 skills with exact content identity. This plugin’s representative native workflow runs from its actual installed skill path with a fresh native runtime; creation/reopening/revision checks pass. All 58 installed skill hashes remain unchanged after the five workflows. [Evidence](docs/evidence/codex-current-release-20261006.json). The shared explicit-tag generator belongs to ArtCraft. Model dispatch awaits authorization; GUI, creative and full host acceptance remain pending. This QA maintenance changes no published skill/runtime content or release tags.

The fixed FilmCraft dev.6 / EffectCraft dev.7 / PhotoCraft dev.6 / VectorCraft dev.6 / ArtCraft dev.17 matrix passed isolated Codex discovery of 58 skills and representative native workflows from installed skill content. All installed skill digests remained unchanged afterward. [Installed native evidence](docs/evidence/codex-release17-native-20261006.json). Model dispatch, GUI and complete creative acceptance remain unverified.

Additional installed-skill brand export verification passed: changing selected logo/wordmark objects updates both SVG color and decoded PNG pixels; unrelated icon properties and the second artboard PNG stay unchanged. This used existing verified runtime caches, not a new cold install. It does not prove automatic token dependency inference. [Evidence](docs/evidence/brand-export-color.json). Plugin and skill release tags are unchanged.

The native RGB global brand-swatch workflow passed a first-use public cold install from one copied appearance skill, including its own script and example. Linked SVG/PNG variants update while the unrelated icon and original project stay unchanged. Skill source v0.1.0-dev.6 is published; plugin v0.1.0-dev.7 is published. Actual host-installed single-skill public cold native acceptance also passes (6.487 seconds); all 58 installed skill hashes remain unchanged. Actual npx independent installation and model dispatch remain unverified. See [architecture](docs/VectorCraft-Brand-Tokens-Architecture.md) and [evidence](docs/evidence/native-brand-token-first-use.json).

Native Chinese text revision now has a single-skill cold test: explicit object edit keeps the first style, unrelated footer and original project; missing fonts stop delivery and successful font dependencies are recorded. Skill source dev.7 and plugin dev.8 are published. Actual installed single-skill public cold native testing passes in 8.275 seconds; all 58 installed hashes remain unchanged. [Architecture](docs/VectorCraft-Chinese-Text-Architecture.md), [evidence](docs/evidence/native-chinese-text.json).

Earlier skill source dev.7 full native regression passes all 42 tests with zero skips (111.204 seconds), including nine separately copied task scenes, brand swatches and Chinese text. Native task scenes use fresh public caches; CLI discovery and baseline native workflow explicitly reuse verified caches. [Evidence](docs/evidence/dev7-full-native-suite.json).

Installed plugin dev.8 / skill source dev.7 supplementary acceptance now checks four rectangular boolean operations, native compound-hole winding, independently decoded SVG/PNG/PDF, original delivery preservation and invalid selection rejection. This does not expand support to arbitrary geometry or editor round trips. [Acceptance](docs/VectorCraft-Boolean-Geometry-Acceptance.md).

Historical fixed dev.8 first-use gap, resolved by dev.9: an unrelated artboard SVG retains off-board brand paths and changes after a brand-token revision, although its PNG/PDF remain unchanged. A maintained native runtime is published; the repaired immutable skill/plugin snapshot is pending. [Reproduction and design boundary](docs/VectorCraft-Artboard-Export-Gap.md).

A local maintained CLI candidate `0.2.0-craft.1` now passes 954 engine tests, 12 CLI integration tests and the three-artboard isolated archive-install task, including byte-identical unrelated SVG/PNG/PDF after a brand-color edit. Twelve source skill installers support its maintained version identity and provenance. This paragraph records the earlier local candidate stage; the maintained runtime is now published, with fixed skill/plugin acceptance pending. [Candidate evidence](docs/evidence/native-artboard-svg-candidate-20261006.json).

The published maintained native runtime passed working-tree single-skill HTTPS cold first use (4.970 seconds). Immutable skill/plugin release and ArtCraft integration remain pending. [Evidence](docs/evidence/public-artboard-svg-runtime-20261006.json).

Plugin dev.9 vendors immutable skill source dev.8 and maintained native CLI 0.2.0-craft.1. The source native suite passes 46 tests without skips; fixed dev.9 host first use and the ArtCraft bundle update are the remaining integration gates. [Source native regression](docs/evidence/maintained-full-native-suite-20261006.json).

Fixed public plugin dev.9 / skill source dev.8 now passes actual Codex discovery of 58 skills and installed single-export-skill public cold native acceptance (4.985 seconds). All 58 installed skill hashes remain unchanged. OpenSpec 4.22 is verified at this domain scope; the ArtCraft bundle update and complete V1 acceptance remain pending. [Fixed installed evidence](docs/evidence/codex-vectorcraft9-artboard-first-use-20261006.json).

Plugin dev.10 vendors immutable skill source dev.9 and maintained CLI craft.2. Stable PDF creation dates and hash-bound date records pass the 49-test native source suite; fixed new host and ArtCraft mixed acceptance remain pending. [Date architecture](docs/VectorCraft-PDF-Date-Architecture.md), [native tests](docs/evidence/craft2-full-native-suite-20261006.json).

Fixed ArtCraft dev.50 / VectorCraft dev.10 first use passes in isolated Codex 0.153.4: five plugins, 58 skills and zero loading errors; one cold native export test with cross-second revision passes (8.108s), two mixed brand tests pass (51.409s), and all installed skill hashes remain unchanged. [Release-bound evidence](docs/evidence/codex-release50-vector10-stable-export-first-use-20261006.json). Generic Skills CLI installation, model/GUI, complete domain and creative acceptance remain open.

All 22 updated skills pass individual public cold first use (159.811s): each is copied alone to .agents/skills and installs into an independent empty runtime, checks exact version and command contracts, and preserves its files and all host-installed hashes. This does not establish generic Skills CLI installation or every creative scenario.

Registered-asset source candidate: linked PNG, embedded SVG, JPEG/SVG replacement, native dependency collection and relocation are implemented in the independent skill workflow. [Architecture](docs/VectorCraft-Asset-Handoff-Architecture.md). The existing fixed plugin snapshot is unchanged; new release and installed-host acceptance remain pending.

Plugin dev.11 vendors immutable skill source dev.10, adding registered PNG/SVG placement and JPEG/SVG replacement with native dependency collection. Installed-host acceptance for this release and the ArtCraft distribution upgrade are separate steps; full V1 acceptance remains open.

Fixed plugin dev.11 / skill source dev.10 has passed actual Codex 0.153.4 public-tag installation and discovery: 58 skills, zero loading errors. Installed single asset/export skills passed two native cold-start tests without skips (4.855s and 6.743s); 12 VectorCraft skills separately cold-installed in 56.275s. Linked/embedded PNG, SVG, JPEG/SVG replacement, direct relocated native reopening and unrelated artboard preservation were checked. All 58 installed hashes stayed unchanged. [Fixed evidence](docs/evidence/codex-vectorcraft11-assets-first-use-20261006.json). ArtCraft still consumes the older Vector bundle; its distribution upgrade and mixed first use remain open.

Current fixed-release domain task matrix: 37 native scenarios and 6 contract checks passed with zero skips across FilmCraft dev.10, EffectCraft dev.9, PhotoCraft dev.10 and VectorCraft dev.11. Each task copied only its selected installed skill and installed the native CLI into a fresh runtime directory from the default public archive. Native projects, actual pixels/audio and targeted preservation were checked; all 58 installed skill identities remained unchanged. [Version-bound evidence](docs/evidence/codex-current-domain-task-matrix-20261006.json). This does not close full V1, generic Skills CLI installation, model dispatch, GUI or creative acceptance.

Public-workflow reply validation is synchronized in the domain source candidates and has bounded native/Art protocol evidence. Fixed updated domain and Art distributions are still pending. [Candidate architecture](docs/VectorCraft-Complete-Commands-Architecture.md) · [Evidence](docs/evidence/public-workflow-session-candidate-20261007.json).

Failed-stage candidate: public workflows retain original native staging paths, dependency hashes, last submitted requests and completed receipts; replay is prohibited. Fixed releases and installed-host acceptance remain open. [Architecture](docs/VectorCraft-Failed-Stage-Architecture.md).

Fixed domain failed-stage first use passes: Film plugin18/source16 and other domain plugins17/source15; five plugins/58 skills without loading errors; all58 independent empty-runtime CLI starts (417.646s); actual installed24 post-save faults reopen product-retained original projects and dependencies; four healthy native creation/revision cases pass. All installed identities and16 fixed plugin CI runs pass. Source repositories have no CI runs, only local regression. Only domain OpenSpec3.12 closes; Art77 bundles older domain sources, task4.9 and fullV1 remain open. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).

Fixed installed scene matrix passes37 native scenarios and6 contract checks with zero skips. The Photo fixture now resolves the maintained native version from the installed skill lock; the CLI and installed skills are unchanged. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).


Candidate complete-command inner JSON fix: nonfinite values, overflow and duplicate keys now retain unknown receipts before binding results. All nine real post-save fault classes pass with original reopen; this is candidate-source evidence, fixed releases and installed-copy acceptance are pending. Complete per-command/GUI acceptance stays open.

Gradient and multiple appearance: source-candidate cold native creation/revision passes for 12 standalone skills; fixed installation and Art distribution are pending. [Architecture](docs/VectorCraft-Appearance-Gradient-Architecture.md).

Fixed installed gradient/multiple appearance: 12 skills pass, with control objects and original delivery preserved; updated Art distribution remains open. [Evidence](docs/evidence/codex-vectorcraft-gradient-first-use-20261007.json).

## Desktop installation component (source candidate)

The 48 standalone domain skills now have their own pinned official desktop installers. See the [installation architecture](docs/Craft-Desktop-First-Use-Architecture.md) and [48-skill installation evidence](docs/evidence/craft-desktop-source48-first-use-20261007.json). Existing release-tag skill copies do not yet contain this candidate component. Desktop startup, GUI edits/save/reopen and complete command execution remain open acceptance gates.

Source candidate now includes owned standalone desktop startup: 48/48 single-skill cold GUI save/reopen and cleanup cases passed. See [runtime evidence](docs/evidence/craft-owned-desktop-first-use-20261007.json). Fixed-release installation and complete command execution remain open.

Command-plan JSON source candidate: duplicate keys are rejected before installation and output creation. All 13 domain skills pass standalone-copy rejection and valid-plan checks. Three focused tests pass; fixed-plugin publication and installed acceptance remain NOT_RUN. [Evidence](docs/evidence/command-plan-json-candidate-20261007.json).

Fixed strict-plan installed verification passes: 64 CLI probes, 324 duplicate-key rejections across54 independently copied installed domain skills, 54 unique-plan structure checks and four cold native save/reopen/render samples. All64 installed skill hashes remain unchanged. Only the bounded strict-plan publication gate closes; generic Skills CLI, Art domain-bundle upgrade, exhaustive contexts and fullV1 remain open. [Evidence](docs/evidence/command-plan-json-fixed-first-use-20261007.json).

Scenario installation examples now name the loaded skill itself. Source paths/layout checks pass; fixed installed runtime acceptance is recorded separately. [Architecture / 架构](docs/Scenario-Own-Path-Architecture.md).
