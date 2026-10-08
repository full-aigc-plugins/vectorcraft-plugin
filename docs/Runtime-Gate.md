# Runtime capability and isolated selection

This source candidate is not included in published plugin41. Selection applies to one Harness ledger; it does not manage external desktops or other ledgers and never installs or upgrades binaries.

Run `node src/cli.ts runtime-probe DATABASE REQUEST.json` for a read-only probe, `runtime-activate` for a fresh probe and selection, or `runtime-status` with an empty request object. Requests contain `skill`, `expectedSkillSha256`, `executable`, `platform`, `python`, `requirements`, and `stateSchemas` for activation. State compatibility is an explicit policy, not inferred migration support. The current ledger schema is2.

Requirements bind `mode` (headless or bridge), `commands` (ID to complete params signature) and `tools` (name to inputSchema). Missing capabilities and changed signatures fail separately. Fix expected schemas before probing; do not accept drift merely to pass. Bridge requires an explicit loopback connection and never substitutes headless. Controller currently executes headless only and refuses a bridge selection.

Activation and task claim share SQLite write transactions. Ready, running, reconciling or cancel_requested tasks and unconfirmed native groups block activation. An identical selection is idempotent and preserves rollback history. Previous probe records and binary directories are retained; no state migration runs, and incompatible rollback is refused. Live enabled checks remain in execution sessions.

[Candidate evidence](evidence/vectorcraft-runtime-gate-candidate-20261008.json):42 Node tests and9 native cases with the same pinned headless runtime passed. Different-version upgrades/rollback, desktop GUI and complete task2.6 remain open. Earlier execution reports retain their original bytes and are historical where implementation changed. The Chinese [flow diagram and details](Runtime-Gate.zh-CN.md) describe the same contract.

Default first-use workflows do not yet require schema probing; explicit activation is currently required. This implementation gap keeps task2.5 open. Activated Controller workflows verify the complete pinned command signatures and bind the capability fingerprint.
