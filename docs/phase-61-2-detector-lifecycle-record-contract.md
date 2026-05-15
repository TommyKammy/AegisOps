# AegisOps Phase 61.2 Detector Lifecycle Record Contract

## 1. Purpose

Phase 61.2 defines the reviewed AegisOps detector lifecycle record contract used to manage detector readiness, rollout, and rollback authority for bounded source families.

This contract is source-family-bound and cannot be used to grant source-native status or workflow truth. It is an AegisOps-authoritative control-plane record contract only.

## 2. Approved Detector Lifecycle States

Detector lifecycle records use this ordered state set:

- `candidate`
- `staging`
- `active`
- `disabled`
- `rollback`
- `review-overdue`

Invalid progression skips are rejected at transition boundaries.

`candidate → active` transitions are explicitly rejected.

## 3. Required Record Fields

Every detector lifecycle record requires:

- `owner`
- `source_family`
- `source_catalog_entry`
- `detector_identifier`
- `expected_signal_posture`
- `review_cadence`
- `rollback_owner`
- `disable_owner`
- `lifecycle_audit_references`

State-specific requirements:

- `disabled` requires `disabled_reason`.
- `rollback` requires `rollback_reason`.
- `review-overdue` requires `review_overdue_reason`.

## 4. Family and Catalog Binding

Detector lifecycle records are only accepted for bounded families and catalog entries from Phase 61.1.

- `wazuh_detection`  
  - `docs/phase-61-minimum-source-catalog-contract.md`
- `github_audit`  
  - `docs/source-families/github-audit/onboarding-package.md`
  - `docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md`
- `microsoft_365_audit`  
  - `docs/source-families/microsoft-365-audit/onboarding-package.md`
- `entra_id`  
  - `docs/source-families/entra-id/onboarding-package.md`
  - `docs/source-families/entra-id/detector-activation-candidates/privileged-role-assignment.md`
- `windows_security_endpoint`  
  - `docs/source-families/windows-security-and-endpoint/onboarding-package.md`

## 5. Authoritative and Boundary Rules

- These records are records only and do not become source truth.
- Source-native state and source-native status cannot replace AegisOps workflow truth.
- Missing owner, missing audit references, mismatched catalog binding, malformed source families, unreviewed path claims, and unsupported reason fields are rejected.
- Transition skips (including `candidate` → `active`) are rejected.
- `rollback` and `disabled` are explicit states only with reviewed reasons.

## 6. Validation

- `bash scripts/verify-phase-61-2-detector-lifecycle-record-contract.sh`
- `python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract`
- `bash scripts/verify-publishable-path-hygiene.sh`

## 7. Non-Goals

- No raw Wazuh replacement.
- No source-native workflow truth.
- No raw source status to close control-plane lifecycle truth.
- No production secrets or placeholder credentials in this contract.
