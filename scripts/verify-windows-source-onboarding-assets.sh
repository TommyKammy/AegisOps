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
  "## 5. Field Coverage Verification"
  "## 6. Detection-Ready Blocker Inventory"
  "## 7. Replay Fixture Plan"
  "## 8. Known Gaps and Non-Goals"
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
  "The field coverage matrix below classifies the reviewed Windows semantic areas as required, optional, unavailable, intentionally deferred, or exception-path constrained without ambiguity."
  "| Event classification and timestamp semantics | Required |"
  "| Source provenance including event channel, provider, and collector or agent identity | Required |"
  "| Host identity and asset references | Required |"
  "| Actor identity and target identity when present | Required with exception path |"
  "| Logon session context, token or integrity details, and group references | Optional |"
  "| Process lineage and command-line context | Intentionally deferred |"
  "| Source and destination network context for remote access or lateral movement records | Unavailable |"
  "| Related user, host, IP, and process correlation fields | Required derived coverage |"
  "| AegisOps-specific provenance annotations under"
  "The missing-actor edge fixture documents that absent actor identity is a detection-ready blocker for actor-dependent detections but remains an allowed schema-reviewed exception path for fixture validation"
  "Windows security records in this narrow fixture set do not yet provide reviewed process lineage evidence, so broader process-context validation remains future work before detection-ready approval."
  "The reviewed administrative-security fixture set does not credibly supply remote network context and therefore cannot claim it without fabrication."
  "Detection-ready approval remains blocked for this family until the reviewed blockers below are resolved or a separately approved exception path states the bounded detector-use scope."
  "| Missing actor attribution for edge-case records | Blocks actor-dependent detections |"
  "| Process lineage and command-line gap | Blocks process-dependent detections |"
  "| Remote-network context gap | Blocks remote-access and lateral-movement detections |"
  "| Parser version and broader Windows event coverage evidence | Blocks source-family detection-ready promotion |"
  'Downstream detections must not depend on unresolved `user.*` actor fields, `process.*` lineage fields, `related.process`, `source.*`, `destination.*`, or `related.ip` coverage from this family until the blocker inventory is updated by review.'
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

if grep -Fqx 'Readiness state: `detection-ready`' "${doc_path}"; then
  echo "Windows security and endpoint must remain schema-reviewed unless blocker resolution or approved exception paths are documented." >&2
  exit 1
fi

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

for required_field in \
  '"@timestamp"' \
  '"event.created"' \
  '"event.ingested"' \
  '"event.action"' \
  '"event.provider"' \
  '"event.module":"windows"' \
  '"event.dataset":"windows.security"' \
  '"host.name"' \
  '"host.hostname"' \
  '"related.user"' \
  '"related.hosts"' \
  '"aegisops.provenance.ingest_path"' \
  '"aegisops.provenance.parser_version"'
do
  if ! grep -Fq "${required_field}" "${replay_root}/normalized/success.ndjson"; then
    echo "Missing required Windows success fixture field: ${required_field}" >&2
    exit 1
  fi
done

if ! grep -Fq '"user.name"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing Windows success fixture actor identity field: "user.name".' >&2
  exit 1
fi

if ! grep -Fq '"destination.user.name"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing Windows success fixture target identity field: "destination.user.name".' >&2
  exit 1
fi

if ! grep -Fq '"group.name"' "${replay_root}/normalized/success.ndjson"; then
  echo 'Missing Windows success fixture optional group reference field: "group.name".' >&2
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

for edge_field in \
  '"event.created"' \
  '"event.ingested"' \
  '"aegisops.validation.note"' \
  '"event.original"'
do
  if ! grep -Fq "${edge_field}" "${replay_root}/normalized/edge.ndjson"; then
    echo "Missing Windows edge fixture field: ${edge_field}" >&2
    exit 1
  fi
done

if ! grep -Fq '"aegisops.provenance.clock_quality":"forwarded-event-time-anomaly"' "${replay_root}/normalized/edge.ndjson"; then
  echo 'Missing forwarded timestamp caveat provenance marker in Windows edge fixtures.' >&2
  exit 1
fi

echo "Windows source onboarding assets and replay fixtures are present for the selected telemetry family."
