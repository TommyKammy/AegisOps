# ADR-0016: Phase 52.7.1 Namespace and Layout Inventory Contract

- **Status**: Accepted
- **Date**: 2026-05-02
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-6-closeout-evaluation.md`, `docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md`, `docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md`
- **Product**: AegisOps
- **Related Issues**: #1120, #1121
- **Depends On**: #1112
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Purpose

Phase 52.7.1 records the namespace and layout inventory that must exist before any public package rename, outer directory rename, retained-root owner relocation, facade relocation, docs move, script move, CI move, or supervisor-facing command change.

This contract is documentation and verification only. It does not move files, rewrite imports, delete shims, change packaging, alter CI behavior, change supervisor policy, start Wazuh profile work, start Shuffle profile work, or alter runtime behavior.

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Namespace bridges, filesystem layout, compatibility aliases, generated config, docs, verifier output, CI status, supervisor-facing issue text, UI cache, browser state, downstream receipts, Wazuh, Shuffle, tickets, assistant output, optional evidence, and demo data remain subordinate evidence or implementation context.

The namespace and layout inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, HTTP, CLI, deployment, Wazuh, Shuffle, ticket, CI, or durable-state behavior.

## 3. Inventory Scope

The inventory covers repo-owned references that a later namespace-normalization or root-owner-reduction issue would otherwise be tempted to infer from path shape, comments, issue text, or nearby metadata.

Every row below is a migration prerequisite, not migration approval. If caller evidence is missing, malformed, ambiguous, or only partially trusted, the current reference remains the supported reference and the proposed reference remains blocked.

## 4. Namespace And Layout Inventory

| Reference class | Current repo-owned reference | Proposed or next reference | Contract |
| --- | --- | --- | --- |
| `current filesystem path` | `control-plane/aegisops_control_plane/` | `control-plane/aegisops/control_plane/` | Current filesystem path remains authoritative for live package files until a later accepted ADR proves caller evidence, compatibility coverage, rollback path, and authority-boundary impact. |
| `current import package` | `aegisops_control_plane` | `aegisops.control_plane` | Current import package remains supported; proposed canonical namespace is documentation-only and not importable in this slice. |
| `proposed canonical namespace` | `aegisops_control_plane` | `aegisops.control_plane` | Later migration must preserve legacy imports or document explicit retained blockers before introducing the canonical namespace. |
| `packaging entrypoint` | `python3 control-plane/main.py` | `python3 control-plane/main.py` | Runtime entrypoint stays unchanged because this slice does not change packaging or CLI behavior. |
| `docs path` | `docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md` | `docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md` | This ADR is the contract source for this slice and must remain publishable with repo-relative paths. |
| `script path` | `scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh` | `scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh` | The verifier remains repo-relative and non-mutating. |
| `negative fixture test path` | `scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh` | `scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh` | The focused negative fixture test must prove missing current package rows, missing proposed namespace rows, and file movement rejection. |
| `CI path` | `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | Existing CI path is inventory only; this slice does not change workflow behavior. |
| `supervisor-facing path` | `node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>` | `node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>` | Supervisor-facing guidance must use placeholders, not workstation-local absolute paths. |

## 5. Compatibility And Blockers

The public Python package name `aegisops_control_plane` remains unchanged in Phase 52.7.1.

The proposed canonical namespace `aegisops.control_plane` is a future target only. It is not implemented, imported, packaged, or advertised as available by this slice.

The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.

`service.py` remains a retained compatibility blocker under ADR-0003, ADR-0010, ADR-0014, and the Phase 52.6 closeout evaluation.

Retained root owners remain physical files until a later owner-move issue proves identical behavior, caller compatibility, rollback path, and authority-boundary impact.

Legacy import aliases remain compatibility mechanisms only. They do not make compatibility state, summary text, generated config, CLI status, adapter state, assistant output, evidence snippets, DTOs, projections, alias rows, namespace rows, or operator-facing text authoritative workflow truth.

## 6. Movement Guard

Phase 52.7.1 rejects file movement. The current `control-plane/aegisops_control_plane/` package, `control-plane/main.py`, `.github/workflows/ci.yml`, this ADR, and the focused verifier scripts must remain at the inventory paths above.

The current package file manifest remains governed by ADR-0012 and the retained-root owner policy remains governed by ADR-0014. This ADR adds the namespace/layout row contract above those existing inventories; it does not replace them.

Any later move must name the exact current path, replacement path, caller evidence, deprecation window, focused regression coverage, rollback path, and authority-boundary impact before it can proceed.

## 7. Forbidden Claims

The verifier rejects this contract if it asserts any of these claims outside this section:

- This contract changes runtime behavior.
- The `aegisops.control_plane` namespace is importable now.
- The `aegisops_control_plane` package may be removed immediately.
- This contract implements Wazuh product profiles.
- This contract implements Shuffle product profiles.

## 8. Validation

Run `bash scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh`.

Run `bash scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.

Run `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1120 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>`.

## 9. Non-Goals

- No file is moved.
- No import is rewritten.
- No shim is deleted.
- No public package name is changed.
- No proposed canonical namespace is implemented.
- No packaging entrypoint is changed.
- No CI workflow behavior is changed.
- No supervisor policy is changed.
- No runtime behavior, HTTP behavior, CLI behavior, deployment behavior, Wazuh behavior, Shuffle behavior, ticket behavior, assistant behavior, evidence behavior, reporting behavior, backup behavior, restore behavior, readiness behavior, action-execution behavior, authorization behavior, provenance behavior, or durable-state side effect is changed.
