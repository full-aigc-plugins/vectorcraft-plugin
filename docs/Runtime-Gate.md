# Runtime capability and isolated selection

Plugin42 includes this entry point. Selection applies to one Harness ledger; it does not manage external desktops or other ledgers and never installs or upgrades binaries.

Run `node src/cli.ts runtime-probe DATABASE REQUEST.json` for a read-only probe, `runtime-activate` for a fresh probe and selection, or `runtime-status` with an empty request object. Requests contain `skill`, `expectedSkillSha256`, `executable`, `platform`, `python`, `requirements`, and `stateSchemas` for activation. State compatibility is an explicit policy, not inferred migration support. The current ledger schema is3.

Requirements bind `mode` (headless or bridge), `commands` (ID to complete params signature) and `tools` (name to inputSchema). Missing capabilities and changed signatures fail separately. Fix expected schemas before probing; do not accept drift merely to pass. Bridge requires an explicit loopback connection and never substitutes headless. Controller currently executes headless only and refuses a bridge selection.

Activation and task claim share SQLite write transactions. Ready, running, reconciling or cancel_requested tasks and unconfirmed native groups block activation. An identical selection is idempotent and preserves rollback history. Previous probe records and binary directories are retained; incompatible rollback is refused. Live enabled checks remain in execution sessions.

[Candidate evidence](evidence/vectorcraft-runtime-gate-candidate-20261008.json):42 Node tests and9 native cases with the same pinned headless runtime passed. Different-version upgrades/rollback, desktop GUI and complete task2.6 remain open. Earlier execution reports retain their original bytes and are historical where implementation changed. The Chinese [flow diagram and details](Runtime-Gate.zh-CN.md) describe the same contract.

Controller now validates plans, installs the fixed version, probes live schemas and initializes selection before editing intent. A different selection is never implicitly upgraded; same-version concurrent tasks reuse it. Existing task keys inspect original receipts without probing or editing again. Legacy ready tasks without capability fingerprints require reconciliation instead of automatic migration. Explicit probe/activation commands remain available.

[Default-first-use evidence](evidence/vectorcraft-runtime-default-artifacts-candidate-20261008.json):46 Node tests,5 actual cold/default/concurrent/refusal scenarios and8 structural regression cases passed. The independent readonly process group is bounded by the task deadline and180 seconds; editing is never retried. Different-version upgrades/rollback, desktop and migrations remain task2.6 acceptance gates.

Opening schema1/2 with plugin42 first creates a consistent VACUUM INTO snapshot including committed WAL in state-schema-backups, marks it readonly and records schemas and SHA256. Backup failure prevents migration. DDL and schema3 commit atomically. The actual previous schema2 reader rejects schema3. Existing selections lacking schema3 support must drain before reactivation. Ledger accepts explicit executionMode=bridge bindings; the default remains headless and Controller still executes headless only.

[Cross-version candidate evidence](evidence/vectorcraft-runtime-boundaries-candidate-20261008.json) covers actual CLI0.2.0/0.2.0-craft.2 drain, version retention, upgrade/rollback reopen and schema-drift refusal, plus an independent owned signed desktop bridge probe/save/reopen. Complete task2.6 remains open: registered live bridge-session drain, the full install/upgrade matrix and other platforms are not accepted.

Plugin43 adds the database selected_runtime_writer trigger: connections opened before migration must also satisfy selected mode, digest and state schema when inserting tasks. A real previous reader reproduced the bypass before the fix; the write is now refused while original WAL snapshots, selections, tasks and consumed budgets remain preserved. Task2.6 awaits fixed plugin43 acceptance.

[Plugin43 candidate / 插件43候选证据](evidence/vectorcraft-open-reader-candidate-20261008.json).
