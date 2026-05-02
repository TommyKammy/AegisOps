# ADR-0015: Phase 52.6.3 Legacy Import Alias Registry

- **Status**: Accepted
- **Date**: 2026-05-02
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md`
- **Product**: AegisOps
- **Related Issues**: #1105, #1108
- **Depends On**: #1107
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Purpose

Phase 52.6.3 adds a bounded legacy import alias registry so approved old module paths can survive without one physical shim file per legacy path.

The registry is import infrastructure only. It does not change workflow truth, authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, HTTP, CLI, deployment, Wazuh, Shuffle, ticket, ML, reporting, or durable-state behavior.

## 2. Registry Path

The registry lives at `control-plane/aegisops_control_plane/core/legacy_import_aliases.py`.

Package initialization calls `register_legacy_import_aliases()` before public package exports are assembled. Each alias row must include the legacy import path, target owner module, target family, and owner file.

## 3. Approved Alias List

| Legacy import path | Target owner import path | Target family | Owner file |
| --- | --- | --- | --- |
| `aegisops_control_plane.audit_export` | `aegisops_control_plane.reporting.audit_export` | `reporting` | `reporting/audit_export.py` |

The `audit_export.py` root shim is the only Phase 52.6.3 physical deletion. The old import path remains available through the registry and must resolve to the exact same module object as `aegisops_control_plane.reporting.audit_export`.

## 4. Retained Blockers

The following paths cannot safely move to the alias registry yet:

| Import path | Blocker |
| --- | --- |
| `aegisops_control_plane.service` | Public facade import path retained under ADR-0003 and ADR-0010. |
| `aegisops_control_plane.models` | Authoritative record model import path remains a root owner. |
| `aegisops_control_plane.phase29_shadow_dataset` | Phase29 adapter still needs adapter-specific caller evidence. |
| `aegisops_control_plane.phase29_shadow_scoring` | Phase29 adapter still needs adapter-specific caller evidence. |
| `aegisops_control_plane.phase29_evidently_drift_visibility` | Phase29 adapter still needs adapter-specific caller evidence. |
| `aegisops_control_plane.phase29_mlflow_shadow_model_registry` | Phase29 adapter still needs adapter-specific caller evidence. |

## 5. Fail-Closed Rules

Alias rows without an explicit target owner fail verification.

An approved legacy import path disappearing without an alias row or retained physical shim fails verification.

An alias must remain a narrow module identity alias. It must not make compatibility state, summary text, generated config, CLI status, adapter state, assistant output, evidence snippets, DTOs, projections, alias rows, or operator-facing text authoritative workflow truth.

## 6. Validation

Run `bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh`.

Run `bash scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh`.

Run `bash scripts/verify-phase-52-5-2-import-compatibility.sh`.

Run `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1108 --config <supervisor-config-path>`.

## 7. Non-Goals

- No broad shim set is deleted.
- No public package name is changed.
- No outer repository directory is changed.
- No public API, runtime endpoint, CLI command, operator UI behavior, deployment behavior, or durable-state side effect is changed.
- No subordinate source, projection, DTO, summary, helper-module output, alias row, or nearby metadata becomes authoritative workflow truth.
