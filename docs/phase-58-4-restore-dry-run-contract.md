# Phase 58.4 Restore Dry-Run Contract

## Purpose

`dry-run-authoritative-record-chain-restore` validates a reviewed
authoritative record-chain backup payload before any live restore operation is
allowed.

Restore dry-run output is preflight evidence only. It can show that the backup
payload parsed, matched expected custody metadata, passed restore validation,
was not stale under the requested age policy, and targeted an empty restore
store. It cannot prove live restore completion, close workflows, satisfy release
gates, approve operations, replace a restore drill, or mutate authoritative
AegisOps records.

## Runtime Surface

- CLI: `python3 control-plane/main.py dry-run-authoritative-record-chain-restore --input <authoritative-backup.json>`.
- Optional source binding: `--expected-source-revision <source-revision>`.
- Optional profile binding: `--expected-profile <deployment-profile>`.
- Optional staleness policy: `--max-age-hours <positive-hours>`.
- Output format: JSON.
- Live restore command remains `python3 control-plane/main.py restore-authoritative-record-chain --input <authoritative-backup.json>`.

## Inputs

The dry-run input is the Phase 58.3 authoritative backup command output:

- `backup_schema_version`: reviewed authoritative record-chain schema version.
- `created_at`: ISO 8601 backup timestamp used when stale checking is requested.
- `record_families`: authoritative record-chain records grouped by family.
- `record_counts`: declared record count for each family.
- `backup_manifest`: custody and recovery evidence manifest.
- `backup_manifest.authority_boundary`: must be `backup_manifest_is_custody_and_recovery_evidence_only`.
- `backup_manifest.custody_metadata.source_revision`: compared with `--expected-source-revision` when provided.
- `backup_manifest.custody_metadata.profile`: compared with `--expected-profile` when provided.

Missing provenance, unsupported record families, malformed record shapes,
missing required links, mismatched record counts, duplicate identifiers, stale
timestamps, and non-empty restore targets fail closed.

## Outputs

A clean dry-run returns:

- `read_only`: `true`.
- `dry_run_state`: `clean`.
- `record_counts`: validated record-family counts.
- `sample_record_ids`: bounded sample of parsed record identifiers by family.
- `backup_created_at`: parsed backup timestamp.
- `authority_boundary`: `restore_dry_run_is_preflight_evidence_only`.
- `can_prove_live_restore_completion`: `false`.
- `mutates_authoritative_records`: `false`.

The command returns a usage error instead of success for `missing`,
`mismatched`, `duplicate`, `stale`, and `unsafe` snapshots.

## Failure States

| State | Rejected condition | Required behavior |
| --- | --- | --- |
| `missing` | Payload, `record_families`, `record_counts`, `backup_manifest`, custody metadata, or required links are absent. | Fail closed before any durable write. |
| `mismatched` | Record counts, expected source revision, expected profile, lifecycle state, approval binding, execution binding, or reconciliation binding disagree. | Fail closed before any durable write. |
| `duplicate` | Authoritative identifiers or execution run identifiers are duplicated. | Fail closed before any durable write. |
| `stale` | `--max-age-hours` is set and `created_at` is older than the requested policy. | Fail closed before any durable write. |
| `unsafe` | Restore target already contains authoritative records or the manifest boundary claims authority beyond custody evidence. | Fail closed before any durable write. |

## Authority Boundary

A dry-run never writes records, never performs live restore execution, and never
marks restore success. Restore acceptance still requires the reviewed live
restore path, restore drill, clean-state validation, and authoritative
AegisOps record-chain checks after the restore.

Restore dry-run evidence must not be used as workflow truth, release truth,
gate truth, approval truth, execution truth, reconciliation truth, restore
completion truth, or customer support truth.

## Non-Goals

Phase 58.4 does not implement destructive restore, schema migration, backup
scheduling, release-gate automation, support bundle generation, customer-private
payload export, direct database mutation bypasses, or restore dry-run output as
restore completion evidence.

## Validation

Run:

- `python3 -m unittest control-plane.tests.test_service_restore_backup_codec`
- `python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_restore_dry_run_command_renders_preflight_evidence_without_mutation`
- `python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_restore_dry_run_command_reports_usage_error_on_failed_preflight`
- `bash scripts/verify-phase-58-4-restore-dry-run-contract.sh`
- `bash scripts/test-verify-phase-58-4-restore-dry-run-contract.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1239 --config <supervisor-config-path>`
