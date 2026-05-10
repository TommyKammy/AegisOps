# Phase 58.3 Backup Command Contract

## Purpose

`backup-authoritative-record-chain` emits the reviewed authoritative record-chain
backup payload plus a product-facing backup manifest for custody and recovery
evidence.

The backup manifest is subordinate evidence only. It can help operators identify
the backup payload, source revision, deployment profile, timestamp, custody
posture, and record-family counts, but it cannot close workflows, approve
releases, prove restore success, complete restore execution, satisfy release
gates, or replace authoritative AegisOps records.

## Runtime Surface

- CLI: `python3 control-plane/main.py backup-authoritative-record-chain`
- Output format: JSON.
- Restore input compatibility: the existing `record_families` and
  `record_counts` payload remains the authoritative restore input.

## Manifest Fields

The backup output includes `backup_manifest` with:

- `manifest_schema_version`: `phase58.backup-command-manifest.v1`.
- `generated_at`: ISO 8601 UTC timestamp for the command output.
- `backup_schema_version`: authoritative record-chain backup schema.
- `custody_metadata`: custody and recovery metadata.
- `custody_metadata.purpose`: `custody_and_recovery_evidence`.
- `custody_metadata.source_revision`: reviewed source revision from
  `AEGISOPS_CONTROL_PLANE_SOURCE_REVISION`, or `unknown` when not provided.
- `custody_metadata.profile`: reviewed deployment profile from
  `AEGISOPS_CONTROL_PLANE_DEPLOYMENT_PROFILE`, or `unreviewed` when not provided.
- `custody_metadata.timestamp`: manifest timestamp.
- `custody_metadata.persistence_mode`: current persistence mode.
- `record_family_counts`: copy of the authoritative `record_counts` values.
- `total_record_count`: sum of all record-family counts.
- `redaction_expectations`: explicit exclusion posture for sensitive material.
- `authority_boundary`: `backup_manifest_is_custody_and_recovery_evidence_only`.
- `non_authority_uses`: forbidden uses the manifest cannot satisfy.

## Redaction Expectations

The manifest must not contain plaintext secrets, DSNs, private keys,
authorization headers, raw customer-private payloads, workstation-local absolute
paths, placeholder credentials treated as valid credentials, or unreviewed
customer evidence.

The manifest records redaction posture only; it does not certify that a restore
has succeeded. Restore success remains proven by the reviewed restore path,
clean-state validation, and authoritative AegisOps record-chain checks.

## Authority Boundary

AegisOps alert, case, evidence, approval, action-request, execution,
reconciliation, audit, release, gate, limitation, and closeout records remain
authoritative.

Backup output and manifests are custody and recovery evidence only. They do not
become workflow truth, restore truth, release truth, gate truth, approval truth,
execution truth, reconciliation truth, or support-bundle truth.

## Non-Goals

Phase 58.3 does not implement enterprise backup scheduling, live restore
execution, support bundle generation, new release gates, new workflow truth,
customer-private raw payload export, plaintext secret storage, or multi-customer
backup administration.

## Validation

Run:

- `python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_backup_command_renders_manifest_custody_metadata_without_secrets`
- `python3 -m unittest control-plane.tests.test_service_restore_backup_codec`
- `bash scripts/verify-phase-58-3-backup-command-contract.sh`
- `bash scripts/test-verify-phase-58-3-backup-command-contract.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1238 --config <supervisor-config-path>`
