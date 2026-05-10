#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-58-4-restore-dry-run-contract.md"

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 58.4 restore dry-run contract: ${doc_path}" >&2
  exit 1
fi

doc_text="$(<"${doc_path}")"

required_phrases=(
  "# Phase 58.4 Restore Dry-Run Contract"
  '`dry-run-authoritative-record-chain-restore` validates a reviewed'
  "Restore dry-run output is preflight evidence only."
  "It cannot prove live restore completion, close workflows, satisfy release"
  "- CLI: \`python3 control-plane/main.py dry-run-authoritative-record-chain-restore --input <authoritative-backup.json>\`."
  "- Optional source binding: \`--expected-source-revision <source-revision>\`."
  "- Optional profile binding: \`--expected-profile <deployment-profile>\`."
  "- Optional staleness policy: \`--max-age-hours <positive-hours>\`."
  "- Live restore command remains \`python3 control-plane/main.py restore-authoritative-record-chain --input <authoritative-backup.json>\`."
  "- \`backup_manifest.authority_boundary\`: must be \`backup_manifest_is_custody_and_recovery_evidence_only\`."
  "Missing provenance, unsupported record families, malformed record shapes,"
  "- \`dry_run_state\`: \`clean\`."
  "- \`authority_boundary\`: \`restore_dry_run_is_preflight_evidence_only\`."
  "- \`can_prove_live_restore_completion\`: \`false\`."
  "- \`mutates_authoritative_records\`: \`false\`."
  "The command returns a usage error instead of success for \`missing\`,"
  "| \`missing\` | Payload, \`record_families\`, \`record_counts\`, \`backup_manifest\`, custody metadata, or required links are absent. | Fail closed before any durable write. |"
  "| \`mismatched\` | Record counts, expected source revision, expected profile, lifecycle state, approval binding, execution binding, or reconciliation binding disagree. | Fail closed before any durable write. |"
  "| \`duplicate\` | Authoritative identifiers or execution run identifiers are duplicated. | Fail closed before any durable write. |"
  "| \`stale\` | \`--max-age-hours\` is set and \`created_at\` is older than the requested policy. | Fail closed before any durable write. |"
  "| \`unsafe\` | Restore target already contains authoritative records or the manifest boundary claims authority beyond custody evidence. | Fail closed before any durable write. |"
  "A dry-run never writes records, never performs live restore execution, and never"
  "Restore dry-run evidence must not be used as workflow truth, release truth,"
  "Phase 58.4 does not implement destructive restore, schema migration, backup"
  "python3 -m unittest control-plane.tests.test_service_restore_backup_codec"
  "bash scripts/verify-publishable-path-hygiene.sh"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1239 --config <supervisor-config-path>"
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_text}"; then
    echo "Missing Phase 58.4 restore dry-run contract statement: ${phrase}" >&2
    exit 1
  fi
done

for forbidden in \
  "dry-run proves live restore completion" \
  "dry-run completes restore" \
  "restore dry-run is workflow truth" \
  "restore dry-run satisfies release gates" \
  "destructive restore is implemented" \
  "customer-private raw payloads are exported" \
  "support bundle generation is implemented"; do
  if grep -Fqi -- "${forbidden}" <<<"${doc_text}"; then
    echo "Forbidden Phase 58.4 restore dry-run contract claim: ${forbidden}" >&2
    exit 1
  fi
done

macos_home_pattern="/""Users/[^[:space:]]+"
linux_home_pattern="/""home/[^[:space:]]+"
windows_home_pattern="C:""\\\\Users\\\\"

if grep -Eq "${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern}" <<<"${doc_text}"; then
  echo "Forbidden Phase 58.4 restore dry-run contract claim: workstation-local path" >&2
  exit 1
fi

echo "Phase 58.4 restore dry-run contract defines inputs, outputs, failure states, and subordinate authority boundaries."
