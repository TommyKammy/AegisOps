#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
artifact_dir="${repo_root}/opensearch/detectors/windows-security-and-endpoint"
validation_doc="${repo_root}/docs/phase-6-opensearch-detector-artifact-validation.md"
slice_doc="${repo_root}/docs/phase-6-initial-telemetry-slice.md"
translation_doc="${repo_root}/docs/sigma-to-opensearch-translation-strategy.md"

verify_artifact() {
  local file_path="$1"
  local detector_name="$2"
  local sigma_rule_path="$3"
  local sigma_rule_id="$4"
  local severity="$5"
  local query="$6"

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing Phase 6 detector artifact: ${file_path}" >&2
    exit 1
  fi

  local required_phrases=(
    "artifact_kind: aegisops-opensearch-detector"
    "artifact_version: v1"
    "detector_name: ${detector_name}"
    "status: staging"
    "production_eligible: false"
    "source_family: windows-security-and-endpoint"
    "sigma_rule_path: ${sigma_rule_path}"
    "sigma_rule_id: ${sigma_rule_id}"
    "source_of_truth: sigma"
    "  - aegisops-logs-windows-*"
    "  - aegisops-logs-windows-staging-*"
    "severity: ${severity}"
    "query_language: lucene"
    "query: ${query}"
    "fallback_handling: No OpenSearch-native fallback is required for this supported single-event Sigma translation."
  )

  for phrase in "${required_phrases[@]}"; do
    if ! grep -Fq -- "${phrase}" "${file_path}"; then
      echo "Missing detector artifact statement in ${file_path}: ${phrase}" >&2
      exit 1
    fi
  done

  local deployment_scope_line
  deployment_scope_line="$(grep -E '^deployment_scope:' "${file_path}" || true)"
  if [[ "${deployment_scope_line}" != "deployment_scope: staging-only" ]]; then
    echo "Detector artifact must remain staging-only: ${file_path}" >&2
    exit 1
  fi
}

if [[ ! -f "${slice_doc}" ]]; then
  echo "Missing Phase 6 slice document required for detector verification: ${slice_doc}" >&2
  exit 1
fi

if [[ ! -f "${translation_doc}" ]]; then
  echo "Missing Sigma-to-OpenSearch translation strategy document required for detector verification: ${translation_doc}" >&2
  exit 1
fi

if [[ ! -d "${artifact_dir}" ]]; then
  echo "Missing Phase 6 detector artifact directory: ${artifact_dir}" >&2
  exit 1
fi

verify_artifact \
  "${artifact_dir}/privileged-group-membership-change-staging.yaml" \
  "aegisops-windows-privileged-group-membership-change-high" \
  "sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml" \
  "2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:(4728 OR 4732 OR 4756) AND group.name:(\"Administrators\" OR \"Domain Admins\" OR \"Enterprise Admins\")'"

verify_artifact \
  "${artifact_dir}/audit-log-cleared-staging.yaml" \
  "aegisops-windows-audit-log-cleared-high" \
  "sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml" \
  "4f5b2a71-91d4-4d75-85a1-c0fc12276fea" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:1102 AND event.action:\"audit-log-cleared\"'"

verify_artifact \
  "${artifact_dir}/new-local-user-created-staging.yaml" \
  "aegisops-windows-new-local-user-created-medium" \
  "sigma/curated/windows-security-and-endpoint/new-local-user-created.yml" \
  "91c9f67d-76f5-41f1-9ccf-66942a33df4f" \
  "medium" \
  "'event.dataset:\"windows.security\" AND event.code:4720 AND event.action:\"local-user-created\"'"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Phase 6 detector validation document: ${validation_doc}" >&2
  exit 1
fi

required_doc_phrases=(
  "# Phase 6 OpenSearch Detector Artifact Validation"
  "- Validation date: 2026-04-03"
  "- Validation status: PASS"
  "## Reviewed Artifacts"
  "## Review Result"
  "## Fallback Handling"
  "The reviewed detector artifacts remain staging-only, preserve the selected Sigma rule identities, and limit validation to Windows staging indexes."
  "No OpenSearch-native fallback is required for the selected Phase 6 slice because all three use cases remain within the approved single-event Sigma translation subset."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing Phase 6 detector validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

reviewed_artifacts=(
  "opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml"
  "opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml"
  "opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml"
)

for artifact in "${reviewed_artifacts[@]}"; do
  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Validation document must list reviewed detector artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 6 OpenSearch detector artifacts are present for the selected Sigma rules and remain staging-only."
