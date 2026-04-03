#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/source-families/windows-security-and-endpoint/onboarding-package.md"
replay_root="${repo_root}/ingest/replay/windows-security-and-endpoint"
replay_readme="${replay_root}/README.md"

required_files=(
  "${doc_path}"
  "${replay_readme}"
  "${replay_root}/raw/privileged-group-addition.json"
  "${replay_root}/raw/audit-log-cleared.json"
  "${replay_root}/raw/local-user-created.json"
  "${replay_root}/raw/local-user-created-missing-actor.json"
  "${replay_root}/raw/audit-log-cleared-forwarded-time-anomaly.json"
  "${replay_root}/normalized/success.ndjson"
  "${replay_root}/normalized/edge.ndjson"
)

required_doc_headings=(
  "# Windows Security and Endpoint Telemetry Onboarding Package"
  "## 1. Family Scope and Readiness State"
  "## 2. Parser Ownership and Lifecycle Boundary"
  "## 3. Raw Payload References"
  "## 4. Normalization Mapping Summary"
  "## 5. Replay Fixture Plan"
  "## 6. Known Gaps and Non-Goals"
)

required_doc_phrases=(
  'Readiness state: `schema-reviewed`'
  "The selected telemetry family for the Phase 6 slice is Windows security and endpoint telemetry."
  "This package does not approve live source enrollment, credential onboarding, parser deployment, or detector activation."
  "Parser ownership remains with IT Operations, Information Systems Department."
  'Representative raw payload references are stored under `ingest/replay/windows-security-and-endpoint/raw/`.'
  'Replay fixtures are stored under `ingest/replay/windows-security-and-endpoint/normalized/`.'
  "The reviewed success-path references in this package cover privileged group membership change, audit log cleared, and new local user created records."
  "The reviewed edge-case references in this package cover missing actor identity and forwarded-event timestamp caveats."
)

required_replay_phrases=(
  "# Windows Security and Endpoint Replay Fixtures"
  "These fixtures are review artifacts only."
  "The normal fixture set preserves representative success-path records for the initial Phase 6 Windows use cases."
  "The edge fixture set preserves records with missing actor context or timestamp caveats that future parser validation must handle explicitly."
  "All fixtures in this directory are synthetic or redacted review examples and are not approvals for live source onboarding."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Windows source onboarding package: ${doc_path}" >&2
  exit 1
fi

for required_file in "${required_files[@]}"; do
  if [[ ! -f "${required_file}" ]]; then
    echo "Missing Windows onboarding asset: ${required_file}" >&2
    exit 1
  fi
done

for heading in "${required_doc_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing Windows onboarding package heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing Windows onboarding package statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${required_replay_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${replay_readme}"; then
    echo "Missing Windows replay fixture statement: ${phrase}" >&2
    exit 1
  fi
done

if ! grep -Fq '"event.code":"4732"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing privileged group membership success fixture with event.code 4732.' >&2
  exit 1
fi

if ! grep -Fq '"event.code":"1102"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing audit log cleared success fixture with event.code 1102.' >&2
  exit 1
fi

if ! grep -Fq '"event.code":"4720"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing local user created success fixture with event.code 4720.' >&2
  exit 1
fi

if ! grep -Fq '"aegisops.validation.case":"missing-actor"' "${replay_root}/normalized/edge.ndjson"; then
  echo 'Missing edge fixture tagged for missing actor handling.' >&2
  exit 1
fi

if ! grep -Fq '"aegisops.validation.case":"forwarded-time-anomaly"' "${replay_root}/normalized/edge.ndjson"; then
  echo 'Missing edge fixture tagged for forwarded timestamp handling.' >&2
  exit 1
fi

echo "Windows source onboarding assets and replay fixtures are present for the selected telemetry family."
