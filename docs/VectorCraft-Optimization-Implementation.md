# VectorCraft optimization implementation and acceptance

This increment implements section9 and its dependencies. Plugin source is dev.43 and continues to pin published skill source dev.37. Full task2.6 remains open until public plugin43 fixed-install validation. Independent skill source is unchanged; historical candidate reports retain their execution identities.

## Implemented modules

| Repository | Module | Evidence boundary |
| :--- | :--- | :--- |
| vectorcraft-skills | Consistent strict JSON and error classification in workflow, commands and mcp_session | Red/green units; native post-save faults and reopen checks separately |
| vectorcraft-skills | Field-level brand allowlist, requested values, palette and consumers | Refuse path/text/geometry/non-target changes; native RGB cases and unit semantics for other authoring models/tints |
| vectorcraft-skills | Thirteen operation contracts, use implicit routing and explicit specialized invocation | Deterministic generation and standalone entry checks; actual host dispatch separately |
| vectorcraft-plugin | current_identity and evidence_index | Pinned versions and report/dependency digests; historical levels and NOT_RUN preserved |
| vectorcraft-plugin | SQLite Ledger and Controller | Durable intent, resource ownership, epochs, budgets, cancellation state and pinned skill execution; full failure/host acceptance remains separate |
| vectorcraft-plugin | ReviewStore, domain schemas and vector rubric | Single-round requests/receipts, stale/duplicate rejection, technical gates and scoped revision proposals |

## Local entry

Node.js24 executes TypeScript with native type stripping; no npm dependencies are installed. Python execution remains in the self-contained skill. Plugin modules do not call external models or automatically start another round.

```bash
npm test
python3 -I -B scripts/current_identity.py --check
python3 -I -B scripts/evidence_index.py --check
node src/cli.ts run STATE.sqlite REQUEST.json
node src/cli.ts review-request REVIEWS.sqlite INPUT.json
node src/cli.ts review-import REVIEWS.sqlite RECEIPT.json
node src/cli.ts revision REVIEWS.sqlite CHANGES.json
```

A run request supplies key, skill, expectedSkillSha256, plan, output, runtimeHome, estimatedBytes and authorization, plus source for a revision. Authorization records objects, fields, an absolute deadline, maxAttempts, maxBytes, optional shared budgetId, readRoots and writeRoots. Whole-skill hashing matches scripts/vendor/skill_vendor.py. Use the fixed plugin skill-lock digest, not a floating main branch.

Controller coordinates public workflow plans. Complete-command plans retain the independent commands entry. Verified files reach review_ready; unknown execution retains ownership and original files without replay. Parent exit does not prove native child termination. Cancellation confirmation and reconciliation observations require actual native inspection; API booleans are not field evidence.

## Single-round review

Requests bind source revision, runtime, editable native file, candidate previews/exports, targets and rubric digests. A target is the actual goal; judge-reference is review-only. At least one target is required. Technical PASS/FAIL/NOT_RUN remains separate from visual scores.

Domain schemas live in schemas; docs/vector-review-rubric.json defines five0–4 dimensions. Receipts name the reviewer and context origin and locate issues by object/field. Until host context evidence is verified, independent remains false; self-declarations do not establish independence. Human or current-host model review must disclose shared context and remaining uncertainty.

Revision generates a proposal after rechecking current fingerprints, valid authorization and assessed issues. It does not execute arbitrary model commands. Full budget, cancellation, plateau and restart contracts remain subject to sections3/6; storage tests do not establish a complete automatic loop.

## Release and evidence

Both repositories have local equivalents of their CI gates. Source candidate, actual GitHub CI, immutable public release, installed copy, host dispatch, GUI and model evidence remain separate. Plugin skills retain the old fixed snapshot until a published source is vendored. Generic Skills CLI, Art bundled updates, full GUI/model, exhaustive commands and V1 retain their own acceptance gates.

## Current acceptance and remaining gates

The source candidate passed129 of159 default regressions;30 conditional native/GUI tests were explicitly skipped and are not passes. Separate opt-in runs passed13 independent cold starts,10 native scene creation/revision cases,8 real consumer/non-consumer mutation faults across two entry routes,6 post-save protocol faults, and three-board/nine-export preservation. Default regression and opt-in native proof remain distinct.

The plugin passed28 Python regressions and11 Node tests. Native single-round exchange/revision used the supplied current-conversation receipt and records independent=false. Review fingerprints include exchange loss; rejection reasons persist. Controller persists plan and rechecked skill snapshots before execution and verifies cached manifests against original receipts. Calls sharing budgetId atomically consume one budget; child exit is not proof that native execution stopped.

Reproduce the bounded brand fixture with `node scripts/acceptance/single_round.ts CONFIG.json`. CONFIG supplies skill/source/runtimeHome/output/receipt/python/brief/targetColor/authorization/changes. This driver handles the Brand Primary fixture only. Scores come from the supplied receipt; it never calls a reviewer or starts another round.

Tasks9.3,9.6,9.9 and9.18 still require new immutable public releases, installed snapshots and host acceptance. Task9.21 has native single-round evidence, but full cancellation/recovery/authorization execution/plateau contracts in sections3/6 remain open. Fixed plugin skills still use source dev.33; dev.34 candidate proof does not establish an installation update. GitHub CI was not run in this increment. Nothing was committed, pushed, tagged or published.


## Managed execution increment (2026-10-08)

The source candidate checks cancellation, deadline, epoch, original project digest and accumulated output budget before each native request, and fsyncs its intent first. Native children have a file-size limit. Managed local revisions check actual object and field authorization, including every global-swatch consumer; unclassified edits fail closed. Native save timestamps are checked separately from protected document properties.

The plugin records owned PID/PGID/start-time/task identity before releasing its launch gate. Parent exit is followed by process-group observation; TERM-ignoring owned descendants may receive KILL. Cancellation retains writer occupation. Reconciliation requires actual native stop, original directory identity and file digests, plus read-only native reopen and dependency checks. It produces cancelled or interrupted_verified, never successful delivery from partial files, and quarantines receipts from an older epoch.

Use `node src/cli.ts cancel STATE.sqlite TASK.json` or `node src/cli.ts reconcile STATE.sqlite TASK.json`; TASK contains taskId and epoch. Native opt-in driver: `node scripts/acceptance/managed_cancel.ts CONFIG.json`, using the explicit single-round brand fixture configuration. The fixed dev.33 skills lack execution_control, so managed execution rejects them until the new source is published and fixed separately.

Current source regression:162 tests,132 passed,30 conditionally skipped; plugin Node regression:15 passed. Native candidate proof covers authorized revision, real saved-checkpoint cancellation, registry restart, original-file/dependency inspection and epoch fencing. Tasks3.1/3.2/3.4/3.5/3.7/3.8 are checked; complete acceptance3.3/3.6/3.9 remains open. Full task table:81 completed,46 open. This is not fixed-install, full sections3/6 or V1 acceptance.

Plugin42 adds readonly pre-migration snapshots, schema3 and explicit mode bindings; the actual previous reader rejects the new schema. See [runtime gates](Runtime-Gate.md) for bounded native evidence and the still-open complete2.6 gate. Skill source remains pinned to dev.37.
