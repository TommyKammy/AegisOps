# ADR-0017: Phase 52.7.2 Canonical Namespace Bridge

## Status

Accepted for Phase 52.7.2 implementation.

## Context

Phase 52.7.1 kept `aegisops.control_plane` as a proposed namespace only. Phase
52.7.2 introduces the smallest compatibility bridge needed to validate that
namespace before repo-owned callers are rewired.

The implementation package remains `aegisops_control_plane`. Legacy imports
must continue to work, and implementation modules are not physically relocated
in this slice.

## Decision

Add `control-plane/aegisops/control_plane/` as a bridge package.

The bridge imports the existing `aegisops_control_plane` package, re-exports its
approved root public surface, and installs a bounded import alias finder that
maps `aegisops.control_plane.*` submodule imports to the corresponding
`aegisops_control_plane.*` module.

The bridge is compatibility infrastructure only. AegisOps control-plane records
remain authoritative for runtime workflow truth. Namespace bridges, aliases,
docs, tests, verifiers, and generated output remain subordinate implementation
context.

## Compatibility Contract

The following behavior is required:

- `import aegisops_control_plane` continues to pass.
- `import aegisops.control_plane` passes through the bridge.
- `aegisops.control_plane.service` resolves to the same module object as
  `aegisops_control_plane.service`.
- `aegisops.control_plane.models` resolves to the same module object as
  `aegisops_control_plane.models`.
- Registry-backed legacy paths such as `aegisops.control_plane.audit_export`
  resolve to the same owner module as the corresponding
  `aegisops_control_plane` legacy import.

## Non-Goals

- Do not move implementation files out of `control-plane/aegisops_control_plane/`.
- Do not delete or deprecate `aegisops_control_plane` imports.
- Do not rewrite broad repo callers in this slice.
- Do not change runtime authority, persistence, HTTP API, CLI behavior, or
  product semantics.

## Verification

Run:

- `python3 -m unittest control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py`
- `bash scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh`
- `bash scripts/test-verify-phase-52-7-2-canonical-namespace-bridge.sh`

