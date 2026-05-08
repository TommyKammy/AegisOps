#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-58-3-backup-command-contract.md"

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 58.3 backup command contract: ${doc_path}" >&2
  exit 1
fi

doc_text="$(<"${doc_path}")"

required_phrases=(
  "# Phase 58.3 Backup Command Contract"
  '`backup-authoritative-record-chain` emits the reviewed authoritative record-chain'
  "backup payload plus a product-facing backup manifest for custody and recovery"
  "evidence."
  "The backup manifest is subordinate evidence only."
  "the backup payload, source revision, deployment profile, timestamp, custody"
  "posture, and record-family counts, but it cannot close workflows, approve"
  "releases, prove restore success, complete restore execution, satisfy release"
  "gates, or replace authoritative AegisOps records."
  "- CLI: \`python3 control-plane/main.py backup-authoritative-record-chain\`"
  "- Restore input compatibility: the existing \`record_families\` and"
  "- \`manifest_schema_version\`: \`phase58.backup-command-manifest.v1\`."
  "- \`custody_metadata.source_revision\`: reviewed source revision from"
  "- \`custody_metadata.profile\`: reviewed deployment profile from"
  "- \`record_family_counts\`: copy of the authoritative \`record_counts\` values."
  "- \`total_record_count\`: sum of all record-family counts."
  "- \`redaction_expectations\`: explicit exclusion posture for sensitive material."
  "- \`authority_boundary\`: \`backup_manifest_is_custody_and_recovery_evidence_only\`."
  "The manifest must not contain plaintext secrets, DSNs, private keys,"
  "authorization headers, raw customer-private payloads, workstation-local absolute"
  "The manifest records redaction posture only; it does not certify that a restore"
  "Backup output and manifests are custody and recovery evidence only."
  "Phase 58.3 does not implement enterprise backup scheduling, live restore"
  "python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_backup_command_renders_manifest_custody_metadata_without_secrets"
  "python3 -m unittest control-plane.tests.test_service_restore_backup_codec"
  "bash scripts/verify-publishable-path-hygiene.sh"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1238 --config <supervisor-config-path>"
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_text}"; then
    echo "Missing Phase 58.3 backup command contract statement: ${phrase}" >&2
    exit 1
  fi
done

for forbidden in \
  "backup manifest is workflow truth" \
  "backup manifest proves restore success" \
  "backup manifest approves releases" \
  "enterprise backup scheduling platform" \
  "plaintext secrets are stored" \
  "customer-private raw payloads are exported" \
  "support bundle generation is implemented"; do
  if grep -Fqi -- "${forbidden}" <<<"${doc_text}"; then
    echo "Forbidden Phase 58.3 backup command contract claim: ${forbidden}" >&2
    exit 1
  fi
done

macos_home_pattern="/""Users/[^[:space:]]+"
linux_home_pattern="/""home/[^[:space:]]+"
windows_home_pattern="C:""\\\\Users\\\\"

if grep -Eq "${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern}" <<<"${doc_text}"; then
  echo "Forbidden Phase 58.3 backup command contract claim: workstation-local path" >&2
  exit 1
fi

echo "Phase 58.3 backup command contract defines manifest custody fields, redaction expectations, and subordinate authority boundaries."
