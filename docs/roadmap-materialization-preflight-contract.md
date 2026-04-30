# Roadmap Materialization Preflight Contract

## 1. Purpose and Scope

This contract defines the repo-owned design and data contract for the roadmap materialization preflight. The preflight decides whether a later AegisOps phase may be created, scheduled, or executed from the GitHub issue graph and repo-local validation facts without rereading large Obsidian roadmap notes at runtime.

The contract is automation validation only. It does not implement the full GitHub issue graph preflight, create Phase 49.0, Phase 49, Phase 52, or later issues, change AegisOps runtime behavior, or change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, or optional-evidence authority.

AegisOps control-plane records remain authoritative workflow truth. GitHub issues and codex-supervisor issue bodies are execution input and safety-boundary material for automation scheduling only. tickets, assistant output, ML output, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context.

## 2. Required Inputs

The preflight input set is a phase graph snapshot. It must be assembled from repo-local roadmap configuration, GitHub issue graph facts, and codex-supervisor lint output. A mixed snapshot must be rejected instead of stitched together from partially refreshed records.

| Field | Required for | Contract |
| --- | --- | --- |
| `phase_id` | Every phase record | Stable phase identifier, for example `48.7`, `49.0`, or `49`. |
| `phase_title` | Every phase record | Human-readable phase name for diagnostics only. |
| `phase_status` | Every phase record | One of `planned`, `materialized`, `in_progress`, `merged`, `evaluated`, `explicitly_deferred`, or `done`. |
| `phase_completion_state` | Every phase record | Authoritative lifecycle state for whether implementation work is complete. |
| `phase_evaluation_state` | Every phase record | Authoritative lifecycle state for review or evaluation closure. |
| `predecessor_phase_ids` | Every phase with prerequisites | Explicit predecessor list. Do not infer predecessors from numbering, issue titles, labels, or comments. |
| `epic_issue_number` | Each materialized phase | GitHub Epic issue number. Missing or malformed values classify the phase as `missing`. |
| `child_issue_numbers` | Each materialized phase | Complete child issue list expected for the phase. Empty or incomplete lists classify the phase as `missing` unless the phase is explicitly deferred. |
| `issue_number` | Epic and child issue records | GitHub issue number used for lint and dependency checks. |
| `issue_state` | Epic and child issue records | GitHub lifecycle state, for example open, closed, explicitly accepted, or unknown. Unknown and open states fail closed for dependent scheduling. |
| `Part of:` | Child issue metadata | Required codex-supervisor parent binding. It must explicitly point to the authoritative Epic issue. |
| `Depends on:` | Epic and child issue metadata | Required dependency field. Placeholder values, TODO text, sample issue numbers, and ambiguous prose are invalid. |
| `Parallelizable:` | Epic and child issue metadata | Required scheduling field. Missing or malformed values are invalid. |
| `Execution order` | Epic and child issue metadata | Required scheduling field. Missing, duplicate, or non-monotonic ordering within the same phase is invalid unless explicitly documented by the phase contract. |
| `issue-lint` | Epic and child issue records | codex-supervisor lint result for the exact issue body being scheduled. |
| `execution_ready` | `issue-lint` output | Must be `yes` before an issue can be considered execution-ready. |
| `missing_required` | `issue-lint` output | Must be `none`. |
| `metadata_errors` | `issue-lint` output | Must be `none`. |
| `missing_recommended` | `issue-lint` output | Must be `none` for normal scheduling. Any non-`none` value requires explicit operator deferral or issue-body repair before later phases start. |
| `high_risk_blocking_ambiguity` | `issue-lint` output | Must be `none`. |

## 3. Phase-State Classifications

The preflight must classify each phase from authoritative lifecycle fields, issue graph facts, and lint output. Later phases cannot redefine predecessor truth from summary text, labels, display ordering, badges, or convenience booleans.

| Classification | Meaning | Safe action |
| --- | --- | --- |
| `missing` | The phase lacks an Epic issue, lacks required child issues, or has no authoritative phase graph binding. | Create or repair the missing Epic or child issue records before scheduling dependent phases. |
| `materialized_open` | Epic and child issues exist, but at least one required issue remains open or not yet execution-ready. | Continue the materialized phase; do not start dependent Phase 49.0/49 or Phase 52+ work. |
| `blocked` | Required metadata is missing, malformed, placeholder-like, non-lint-clean, or points outside the authoritative phase graph. | Repair the issue body or graph binding and rerun lint. |
| `execution_ready` | Epic and child issues are lint-clean and schedulable, but the phase is not complete or evaluated. | Allow work on that phase only; dependent phases remain blocked. |
| `merge_or_evaluation_needed` | Implementation appears merged or complete, but required evaluation, closure, or explicit deferral is absent. | Run or record the evaluation gate before scheduling dependent phases. |
| `done` | Required issues are materialized, lint-clean, complete, and evaluated, or the phase is explicitly deferred by an authoritative phase record. | Allow the next phase gate to evaluate. |

Unknown, partially trusted, or conflicting input must classify as `blocked` with a concrete `invalid_field`. The preflight must fail closed instead of inferring success from naming conventions, issue labels, nearby comments, or operator-facing summaries.

## 4. Required Outputs

The preflight output must be deterministic and machine-readable.

| Field | Values | Contract |
| --- | --- | --- |
| `pass` | boolean | `true` only when every predecessor gate required by the requested phase is `done` or explicitly deferred. |
| `fail` | boolean | `true` when the requested phase cannot safely start. `pass` and `fail` must not both be true. |
| `phase_classification` | classification map | Map from `phase_id` to one of the phase-state classifications. |
| `invalid_phase_id` | string or null | Exact phase id that failed, for example `48.7`. |
| `invalid_field` | string or null | Exact missing or invalid field, for example `child_issue_numbers`, `Depends on:`, `metadata_errors`, or `phase_evaluation_state`. |
| `invalid_issue_number` | number or null | Exact issue number when the failure belongs to one issue. |
| `suggested_next_safe_action` | string | Specific next action, for example create a child issue, replace a placeholder dependency, rerun issue-lint, or record evaluation closure. |
| `evidence` | object | Snapshot identifier, lint command references, issue numbers read, and phase graph source. |

The canonical lint command form for diagnostics is:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint <issue-number> --config <supervisor-config-path>
```

Do not publish workstation-local absolute paths in validation plans or durable docs. Use `<codex-supervisor-root>`, `<supervisor-config-path>`, `CODEX_SUPERVISOR_CONFIG`, or repo-relative command forms.

## 5. Phase 48.7 Gate for Phase 49.0/49

Phase 48.7 protects Phase 49.0 and Phase 49 from starting before earlier roadmap gates are materialized and reviewed. Phase 49.0 is the behavior-preserving `AegisOpsControlPlaneService` decomposition phase. Phase 49 commercial-readiness work remains downstream of the earlier automation, evidence, and evaluation gates.

Phase 49.0/49 must not start before Phase 48, Phase 48.5, Phase 48.6, and Phase 48.7 gates are materialized, lint-clean, and evaluated or explicitly deferred.

For Phase 49.0 or Phase 49 scheduling, the preflight must:

1. Resolve predecessor phases from explicit phase graph records.
2. Confirm every predecessor Epic and child issue is materialized.
3. Confirm every predecessor issue has valid `Part of:`, `Depends on:`, `Parallelizable:`, and `Execution order` metadata.
4. Confirm codex-supervisor `issue-lint` reports `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, `missing_recommended=none`, and `high_risk_blocking_ambiguity=none`.
5. Confirm predecessor phase completion and evaluation state are authoritative, closed, and not derived from summary text.
6. Reject placeholder dependencies, missing child issue lists, non-lint-clean issue bodies, and missing evaluation closure.

## 6. Post-Phase50 Gate for Phase 52+

Phase 51 protects the Phase 52+ replacement-readiness waves from starting before the replacement thesis, gate vocabulary, personas, competitive framing, negative-test policy, materialization guard, and closeout evaluation are materialized as real GitHub issue records.

Phase 52+ must not be created, scheduled, or executed until the Phase 51 Epic and child issue set are materialized, lint-clean, and closed or explicitly accepted by the owner.

The authoritative Phase 51 binding is:

- Phase 51 Epic #1041
- Phase 51 child issues #1042, #1043, #1044, #1045, #1046, #1047, #1048, and #1049

For Phase 52+ scheduling, the preflight must:

1. Resolve Phase 51 from explicit phase graph records, not phase numbering, issue titles, roadmap prose, or comments.
2. Confirm the Phase 51 Epic and every expected child issue are present in one issue graph snapshot.
3. Child issues need real `Part of:` issue numbers that point to the authoritative Epic.
4. Confirm `Depends on:` must contain true scheduler blockers only. Narrative, historical, or roadmap-context relationships must not be encoded as live blockers.
5. Confirm every Phase 51 Epic and child issue is lint-clean with `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, `missing_recommended=none`, and `high_risk_blocking_ambiguity=none`.
6. Confirm every Phase 51 Epic and child issue is closed or explicitly accepted by the owner before Phase 52+ materialization proceeds.
7. Reject missing Epic, missing child, missing `Part of:`, missing `Depends on:`, missing `Execution order`, non-lint-clean, open, and placeholder-dependency issue sets.

## 7. Example Outcomes

| Example | Input facts | Classification | Output |
| --- | --- | --- | --- |
| Complete phase | Phase 48 has an Epic, all child issues are listed, metadata is valid, `issue-lint` reports `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, and evaluation is closed. | `done` | `pass=true`, `invalid_field=null`, `suggested_next_safe_action="evaluate next phase gate"` |
| Missing Epic issue | Phase 48.7 has no `epic_issue_number` binding, or the bound Epic issue record cannot be read from the same issue graph snapshot. | `missing` | `fail=true`, `invalid_phase_id="48.7"`, `invalid_field="epic_issue_number"`, `suggested_next_safe_action="create or bind the missing Epic issue before scheduling dependent phases"` |
| Missing child issue | Phase 48.7 has an Epic, but `child_issue_numbers` omits a required child from the phase graph. | `missing` | `fail=true`, `invalid_field="child_issue_numbers"`, `suggested_next_safe_action="create or bind the missing child issue before scheduling dependent phases"` |
| Missing Part of | A Phase 51 child issue lacks a real `Part of:` binding to #1041. | `blocked` | `fail=true`, `invalid_field="Part of:"`, `suggested_next_safe_action="replace the placeholder parent binding with the authoritative Epic issue number and rerun issue-lint"` |
| Missing Depends on | A Phase 51 child issue lacks `Depends on:` metadata. | `blocked` | `fail=true`, `invalid_field="Depends on:"`, `suggested_next_safe_action="replace the placeholder dependency and rerun issue-lint"` |
| Missing execution order | A Phase 51 child issue lacks an `Execution order` section. | `blocked` | `fail=true`, `invalid_field="Execution order"`, `suggested_next_safe_action="add the required execution-order metadata and rerun issue-lint"` |
| Placeholder or non-real dependency | A child issue has `Depends on: TBD`, a sample issue number, or an issue number outside the authoritative phase graph instead of an explicit authoritative dependency or `none`. | `blocked` | `fail=true`, `invalid_phase_id="48.7"`, `invalid_field="Depends on:"`, `suggested_next_safe_action="replace the placeholder dependency and rerun issue-lint"` |
| Non-lint-clean issue | `issue-lint` reports `execution_ready=no` or `metadata_errors` is not `none` for a required Epic or child issue. | `blocked` | `fail=true`, `invalid_field="metadata_errors"`, `invalid_issue_number=<issue-number>`, `suggested_next_safe_action="repair the issue body and rerun issue-lint"` |
| Open predecessor issue | A Phase 51 child issue is still open and has no explicit owner acceptance. | `materialized_open` | `fail=true`, `invalid_field="issue_state"`, `suggested_next_safe_action="close or explicitly accept every predecessor Epic and child issue before dependent scheduling"` |
| Evaluation still needed | Required issues are closed or merged, but `phase_evaluation_state` is missing or still open. | `merge_or_evaluation_needed` | `fail=true`, `invalid_field="phase_evaluation_state"`, `suggested_next_safe_action="record evaluation closure or explicit deferral before dependent scheduling"` |

## 8. Repo-Owned Preflight Invocation

The repo-owned Phase 48.7.2 preflight command is:

```sh
bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 49.0 --issue-source github
```

The repo-owned post-Phase50 preflight command for later Phase 52+ waves is:

```sh
bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 52 --issue-source github
```

For live GitHub issue graph reads, the command uses `gh issue view` and runs `issue-lint` through the configured codex-supervisor checkout. Export the supervisor locations with placeholders rather than workstation-local paths in durable instructions:

```sh
CODEX_SUPERVISOR_ROOT=<codex-supervisor-root> \
CODEX_SUPERVISOR_CONFIG=<supervisor-config-path> \
bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 49.0 --issue-source github
```

The preflight emits deterministic JSON. A blocked current Phase 48.7 predecessor is reported in this shape:

```json
{
  "pass": false,
  "fail": true,
  "target_phase_id": "49.0",
  "phase_classification": {
    "48.7": "materialized_open"
  },
  "invalid_phase_id": "48.7",
  "invalid_field": "phase_completion_state",
  "invalid_issue_number": null,
  "suggested_next_safe_action": "complete and evaluate the materialized predecessor phase before dependent scheduling"
}
```

The positive fixture smoke path is:

```sh
bash scripts/test-verify-roadmap-materialization-preflight.sh
```

The repo-local phase graph binding is `docs/automation/roadmap-materialization-phase-graph.json`. That graph is the explicit input for the preflight and currently binds Phase 48.7 to Epic `#911` with child issues `#912`, `#913`, and `#914` before Phase 49.0/49 scheduling can proceed. It also binds Phase 51 to Epic `#1041` with child issues `#1042`, `#1043`, `#1044`, `#1045`, `#1046`, `#1047`, `#1048`, and `#1049` before Phase 52+ scheduling can proceed.

## 9. Validation

Focused validation for this contract and implementation:

```sh
bash scripts/verify-roadmap-materialization-preflight-contract.sh
bash scripts/test-verify-roadmap-materialization-preflight-contract.sh
bash scripts/test-verify-roadmap-materialization-preflight.sh
node <codex-supervisor-root>/dist/index.js issue-lint 913 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1048 --config <supervisor-config-path>
```

This validation is documentation and automation-contract focused. It does not authorize production writes, runtime behavior changes, issue creation for Phase 49.0/49, Phase 52+, or any authority shift away from AegisOps control-plane records.
