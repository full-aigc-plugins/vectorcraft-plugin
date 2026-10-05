# VectorCraft Agent Plugin

Independent-skills-driven Editable vector brand assets and multi-artboard design.

[English](README.md) | [简体中文](README.zh-CN.md)

> This is a documentation and OpenSpec baseline, not an installable functional release. Plugin behavior and skill packages are not implemented or published.

## Positioning

Create logo and icon assets in .vectorcraft, SVG and PNG; change a brand color and update bound variants while preserving unrelated colors.

For creators who need editable native projects, repeatable revisions and reliable automation.

## At a glance

```text
Intent + assets
  -> independent Skills (planned)
  -> plugin Harness (planned)
  -> verified runtime / child adapter
  -> native project + preview + export + evidence
```
| Property | Value |
| :--- | :--- |
| Plugin ID | vectorcraft |
| Metadata version | 0.1.0-dev.0 |
| Stage | documentation-baseline |
| Skills source | vectorcraft-skills (planned) |
| Execution | Upstream CLI; ArtCraft uses child adapters |
| Host compatibility | NOT_RUN |
| License | Apache-2.0 (original repository content) |


## Capabilities and boundaries

| Capability | Behavioral boundary | Status |
| :--- | :--- | :--- |
| Paths, shapes and coordinates | Define artboard coordinates, units, control points, path closure and strokes; preview pixels are not vector path authority. | Planned |
| Grouping and boolean operations | Record operand IDs, boolean operation and result identity with a pre-operation checkpoint; failure must not destroy source objects. | Planned |
| Brand colors and text | Bind brand colors using explicit tokens instead of global color replacement; retain text and font dependencies and report editability loss when outlining. | Planned |
| Artboards and variants | Give each artboard a stable ID, name, size and output mapping; define preview ordering and export ranges without index-base ambiguity. | Planned |
| Interchange fidelity scope | Validate native .vectorcraft, SVG, PDF and PNG separately; report rasterized effects and keep native sources when interchange cannot preserve them. | Planned |
| Brand variant revision | Update related variants from token and asset dependencies and verify that unrelated object properties and outputs remain unchanged. | Planned |

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

The recorded result is 0.2.0. Plugin setup, skill installation and host installation instructions will ship after their tasks are implemented; no fictional installation command is provided now.

## Configuration and runtime

Target configuration includes CLI paths, allowed read/write roots, execution mode, budget, timeout and output directory; the configuration schema is not implemented yet. Empty skill-lock sources avoid claiming unpublished skills. Runtime lock hashes identify real official artifacts and establish only the recorded platform’s smoke evidence.

## Reliability and security

Planned safeguards include project write locks, revision preconditions, persisted intent, idempotency keys, outcome reconciliation, native checkpoints, artifact hashes and bounded revisions. Secrets are host-managed references; asset metadata is never an execution instruction.

## Verification and maturity

[Sanitized CLI evidence](docs/evidence/runtime-baseline.json)

| Layer | Status |
| :--- | :--- |
| Upstream CLI and read-only MCP | Observed on macOS arm64 only |
| Business skills and plugin harness | PLANNED |
| Native project and creative acceptance | NOT_RUN |
| Target host installation | NOT_RUN |


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
