# ADR-0018: Phase 52.7.6 Namespace, Path, And Packaging Guardrails

## Status

Accepted for Phase 52.7.6 validation.

## Context

Phase 52.7.4 moved implementation ownership to `control-plane/aegisops/control_plane/`.
Phase 52.7.5 reduced the canonical package root to the explicit retained root
files and preserved legacy import compatibility through the alias registry and
the `control-plane/aegisops_control_plane/__init__.py` compatibility shim.

This contract pins that accepted state so stale path guidance, duplicate legacy
namespace guidance, unclassified root files, and publishable workstation-local
paths do not return.

## Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence,
approval, action request, execution receipt, reconciliation, audit, limitation,
release, gate, and closeout truth. Namespace bridges, filesystem layout,
compatibility aliases, generated config, docs, verifier output, CI status,
supervisor-facing issue text, UI cache, browser state, downstream receipts,
Wazuh, Shuffle, tickets, assistant output, optional evidence, and demo data
remain subordinate evidence or implementation context.

## Pinned State

| Class | Required state |
| --- | --- |
| Canonical implementation package | `control-plane/aegisops/control_plane/` |
| Legacy compatibility package | `control-plane/aegisops_control_plane/__init__.py` only |
| Canonical import namespace | `aegisops.control_plane` |
| Legacy compatibility namespace | `aegisops_control_plane` remains importable only as a compatibility surface |
| Packaging entrypoint | `python3 control-plane/main.py` |
| Supervisor command guidance | `node <codex-supervisor-root>/dist/index.js issue-lint 1126 --config <supervisor-config-path>` |
| Publishable path guidance | Repo-relative paths, documented env vars, and explicit placeholders only |

## Guardrail Rules

- New guidance that points implementation ownership at `control-plane/aegisops_control_plane/` is rejected unless the file is an approved compatibility note, compatibility verifier, or negative fixture.
- New repo-owned Python imports must use `aegisops.control_plane` unless the file is an approved compatibility shim or compatibility regression test.
- The legacy compatibility package must not contain implementation files beyond `__init__.py`.
- New direct canonical root Python files fail verification unless the retained-root file set is intentionally updated by policy.
- Workstation-local absolute paths in publishable tracked content fail verification.
- Packaging and supervisor command examples must use repo-relative paths or placeholders, not host-specific absolute paths.

## Verification

Run:

- `bash scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh`
- `bash scripts/test-verify-phase-52-7-6-namespace-path-packaging-guardrails.sh`
- `bash scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh`
- `bash scripts/verify-phase-52-7-5-root-shim-reduction.sh`
- `bash scripts/verify-phase-52-6-6-root-package-guardrails.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `bash scripts/verify-phase-52-5-2-import-compatibility.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1126 --config <supervisor-config-path>`

## Non-Goals

- Do not change runtime behavior, HTTP API behavior, CLI behavior, persistence
  semantics, authorization semantics, operator UI behavior, Wazuh profile
  behavior, Shuffle profile behavior, or product readiness claims.
- Do not remove legacy import compatibility.
