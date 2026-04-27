#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-pilot-go-no-go-decision-packet.sh [<repo-root>] [--packet <pilot-go-no-go-packet.md>]

Validates a redacted single-customer pilot go/no-go decision packet. The packet
must bind release handoff, detector activation, known limitations, retention,
Zammad/non-authority posture, assistant limitation posture, owner, and next
health review evidence to one release identifier.
EOF
}

repo_root=""
packet_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --packet)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      packet_path="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -n "${repo_root}" ]]; then
        usage
        exit 2
      fi
      repo_root="$1"
      shift
      ;;
  esac
done

if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [[ -z "${packet_path}" ]]; then
  packet_path="${repo_root}/docs/deployment/pilot-go-no-go-decision-packet.single-customer-pilot.example.md"
fi

checklist_path="${repo_root}/docs/deployment/pilot-readiness-checklist.md"
runbook_path="${repo_root}/docs/runbook.md"
verifier_test_path="${repo_root}/scripts/test-verify-pilot-go-no-go-decision-packet.sh"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_workstation_paths() {
  local description="$1"
  shift

  local macos_home_pattern linux_home_pattern windows_home_pattern workstation_local_path_pattern
  macos_home_pattern='/'"Users"'/[^[:space:])>]+'
  linux_home_pattern='/'"home"'/[^[:space:])>]+'
  windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

reject_secret_looking_values() {
  local path="$1"
  local description="$2"

  if grep -Eiq '(secret|token|password|passwd|api[_-]?key|access[_-]?key|private[_-]?key)[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]*|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer[[:space:]]+[A-Za-z0-9._~+/-]+' "${path}"; then
    echo "Secret-looking ${description} value detected: ${path}" >&2
    exit 1
  fi
}

extract_release_identifier() {
  local path="$1"

  grep -Eo 'aegisops-single-customer-[A-Za-z0-9_-]+' "${path}" | LC_ALL=C sort -u
}

require_label_contains_release() {
  local label="$1"
  local description="$2"

  if ! grep -F -- "${label}" "${packet_path}" | grep -F -- "${release_identifier}" >/dev/null; then
    echo "Missing ${description}: ${label} must reference ${release_identifier}" >&2
    exit 1
  fi
}

require_file "${packet_path}" "pilot go/no-go decision packet"
require_file "${checklist_path}" "pilot readiness checklist"
require_file "${runbook_path}" "runbook"
require_file "${verifier_test_path}" "pilot go/no-go decision packet verifier tests"

release_identifiers=()
while IFS= read -r release_identifier_entry; do
  release_identifiers+=("${release_identifier_entry}")
done < <(extract_release_identifier "${packet_path}")
if [[ "${#release_identifiers[@]}" -eq 0 ]]; then
  echo "Missing pilot go/no-go release identifier: expected aegisops-single-customer-<repository-revision> or reviewed tag-bound equivalent" >&2
  exit 1
fi

if [[ "${#release_identifiers[@]}" -gt 1 ]]; then
  echo "Mixed pilot go/no-go release identifiers: ${release_identifiers[*]}" >&2
  exit 1
fi

release_identifier="${release_identifiers[0]}"

required_packet_phrases=(
  "# Pilot Go/No-Go Decision Packet - Filled Redacted Single-Customer Pilot Example"
  "This packet is the reviewed pilot go/no-go decision surface for one single-customer release."
  "Decision status: go-with-explicit-limitations"
  "Pilot customer scope: redacted single-customer pilot environment"
  "Pilot owner:"
  "Release handoff evidence:"
  "Detector activation evidence:"
  "Known limitations review:"
  "Retention decision:"
  "Zammad/non-authority posture:"
  "Assistant limitation posture:"
  "Evidence handoff owner:"
  "Next health review:"
  "Refused evidence:"
  "Verification:"
  "Authority boundary: AegisOps control-plane records remain authoritative for approval, evidence, execution, reconciliation, readiness, release, pilot entry, and go/no-go truth."
)

for phrase in "${required_packet_phrases[@]}"; do
  require_phrase "${packet_path}" "${phrase}" "pilot go/no-go decision packet entry"
done

require_label_contains_release "Release identifier:" "pilot release identifier"
require_label_contains_release "Release handoff evidence:" "release handoff evidence"
require_label_contains_release "Detector activation evidence:" "detector activation evidence"
require_label_contains_release "Known limitations review:" "known limitations review"
require_label_contains_release "Retention decision:" "retention decision"
require_label_contains_release "Zammad/non-authority posture:" "Zammad non-authority posture"
require_label_contains_release "Assistant limitation posture:" "assistant limitation posture"
require_label_contains_release "Next health review:" "next health review"

required_reference_phrases=(
  "docs/deployment/release-handoff-evidence-manifest.single-customer-pilot.example.md"
  "docs/deployment/detector-activation-evidence.single-customer-pilot.example.md"
  "docs/deployment/known-limitations-retention-decision-template.md"
  "docs/deployment/pilot-readiness-checklist.md"
  "scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>"
  "scripts/verify-detector-activation-evidence-handoff.sh"
  "scripts/verify-pilot-readiness-checklist.sh"
)

for phrase in "${required_reference_phrases[@]}"; do
  require_phrase "${packet_path}" "${phrase}" "pilot go/no-go decision packet reference"
done

for forbidden in \
  "ticket system is authoritative" \
  "Zammad is authoritative" \
  "assistant may approve" \
  "assistant may execute" \
  "assistant may reconcile" \
  "detector status is authoritative" \
  "compliance certification is complete" \
  "multi-customer rollout is approved" \
  "24x7 support is promised" \
  "SLA is promised" \
  "unlimited retention is approved"; do
  reject_phrase "${packet_path}" "${forbidden}" "pilot go/no-go decision packet statement"
done

reject_workstation_paths "pilot go/no-go decision packet" "${packet_path}"
reject_secret_looking_values "${packet_path}" "pilot go/no-go decision packet"

require_phrase "${checklist_path}" 'Verify a retained pilot go/no-go decision packet with `scripts/verify-pilot-go-no-go-decision-packet.sh --packet <pilot-go-no-go-packet.md>`.' "pilot readiness checklist go/no-go verifier link"
require_phrase "${checklist_path}" 'Negative validation for the go/no-go packet verifier is `scripts/test-verify-pilot-go-no-go-decision-packet.sh`.' "pilot readiness checklist go/no-go verifier test link"
require_phrase "${runbook_path}" 'Before a pilot launch decision is treated as reviewed, verify the retained go/no-go packet with `scripts/verify-pilot-go-no-go-decision-packet.sh --packet <pilot-go-no-go-packet.md>` so release handoff, detector activation, known limitations, retention, Zammad/non-authority posture, assistant limitations, owner, and next health review evidence bind to one release identifier.' "runbook pilot go/no-go verifier link"

reject_workstation_paths "pilot go/no-go verifier guidance" "${checklist_path}" "${runbook_path}"

echo "Pilot go/no-go decision packet is complete, redacted, bounded, and bound to ${release_identifier}."
