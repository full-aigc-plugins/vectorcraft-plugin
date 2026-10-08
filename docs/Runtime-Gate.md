# Runtime capability and isolated selection

This source candidate is not included in published plugin41. Selection applies to one Harness ledger; it does not manage external desktops or other ledgers and never installs or upgrades binaries.

Run `node src/cli.ts runtime-probe DATABASE REQUEST.json` for a read-only probe, `runtime-activate` for a fresh probe and selection, or `runtime-status` with an empty request object. Requests contain `skill`, `expectedSkillSha256`, `executable`, `platform`, `python`, `requirements`, and `stateSchemas` for activation. State compatibility is an explicit policy, not inferred migration support. The current ledger schema is2.

Requirements bind `mode` (headless or bridge), `commands` (ID to complete params signature) and `tools` (name to inputSchema). Missing capabilities and changed signatures fail separately. Fix expected schemas before probing; do not accept drift merely to pass. Bridge requires an explicit loopback connection and never substitutes headless. Controller currently executes headless only and refuses a bridge selection.

Activation and task claim share SQLite write transactions. Ready, running, reconciling or cancel_requested tasks and unconfirmed native groups block activation. An identical selection is idempotent and preserves rollback history. Previous probe records and binary directories are retained; no state migration runs, and incompatible rollback is refused. Live enabled checks remain in execution sessions.

[Candidate evidence](evidence/vectorcraft-runtime-gate-candidate-20261008.json):42 Node tests and9 native cases with the same pinned headless runtime passed. Different-version upgrades/rollback, desktop GUI and complete task2.6 remain open. Earlier execution reports retain their original bytes and are historical where implementation changed. The Chinese [flow diagram and details](Runtime-Gate.zh-CN.md) describe the same contract.

Controller now validates plans, installs the fixed version, probes live schemas and initializes selection before editing intent. A different selection is never implicitly upgraded; same-version concurrent tasks reuse it. Existing task keys inspect original receipts without probing or editing again. Legacy ready tasks without capability fingerprints require reconciliation instead of automatic migration. Explicit probe/activation commands remain available.

[Default-first-use evidence](evidence/vectorcraft-runtime-default-candidate-20261008.json):46 Node tests,5 actual cold/default/concurrent/refusal scenarios and8 structural regression cases passed. The independent readonly process group is bounded by the task deadline and180 seconds; editing is never retried. Different-version upgrades/rollback, desktop and migrations remain task2.6 acceptance gates.
