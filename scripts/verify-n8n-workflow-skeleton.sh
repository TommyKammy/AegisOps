#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
workflow_root="${repo_root}/n8n/workflows"

expected_categories=(
  "aegisops_alert_ingest"
  "aegisops_approve"
  "aegisops_enrich"
  "aegisops_notify"
  "aegisops_response"
)

required_workflow_assets=(
  "aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"
  "aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json"
)

allowed_node_types=(
  "n8n-nodes-base.manualTrigger"
  "n8n-nodes-base.set"
  "n8n-nodes-base.stickyNote"
  "n8n-nodes-base.switch"
)

if [[ ! -d "${workflow_root}" ]]; then
  echo "Missing n8n workflow skeleton directory: ${workflow_root}" >&2
  exit 1
fi

actual_categories=()
while IFS= read -r category; do
  actual_categories+=("${category}")
done < <(
  find "${workflow_root}" -mindepth 1 -maxdepth 1 -type d \
    | sed 's#.*/##' \
    | LC_ALL=C sort
)

expected_sorted=()
while IFS= read -r category; do
  expected_sorted+=("${category}")
done < <(
  printf '%s\n' "${expected_categories[@]}" | LC_ALL=C sort
)

for category in "${expected_categories[@]}"; do
  category_path="${workflow_root}/${category}"

  if [[ ! -d "${category_path}" ]]; then
    echo "Missing n8n workflow category placeholder: ${category_path}" >&2
    exit 1
  fi

  if [[ ! -f "${category_path}/.gitkeep" ]]; then
    echo "Missing placeholder file for n8n workflow category: ${category_path}/.gitkeep" >&2
    exit 1
  fi

  unexpected_entries=()
  while IFS= read -r path; do
    relative_path="${path#${workflow_root}/}"
    case "${relative_path}" in
      "${category}/.gitkeep"|\
      "aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"|\
      "aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json")
        ;;
      *)
        unexpected_entries+=("${path}")
        ;;
    esac
  done < <(
    find "${category_path}" -mindepth 1 | LC_ALL=C sort
  )

  if ((${#unexpected_entries[@]} > 0)); then
    echo "n8n workflow structure includes an unapproved workflow asset: ${category_path}" >&2
    printf 'Unexpected entries:\n' >&2
    printf '  %s\n' "${unexpected_entries[@]}" >&2
    exit 1
  fi
done

for asset in "${required_workflow_assets[@]}"; do
  asset_path="${workflow_root}/${asset}"

  if [[ ! -f "${asset_path}" ]]; then
    echo "Missing approved n8n workflow asset: ${asset_path}" >&2
    exit 1
  fi
done

enrich_workflow="${workflow_root}/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"
notify_workflow="${workflow_root}/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json"

enrich_required_phrases=(
  '"name": "aegisops_enrich_windows_selected_detector_outputs"'
  '"value": "privileged_group_membership_change"'
  '"value": "audit_log_cleared"'
  '"value": "new_local_user_created"'
  '"name": "read_only_boundary"'
  '"name": "notification_handoff_required"'
)

notify_required_phrases=(
  '"name": "aegisops_notify_windows_selected_detector_outputs"'
  '"name": "notify_only_boundary"'
  '"name": "downstream_mutation_allowed"'
  '"name": "selected_detector_outputs"'
)

for phrase in "${enrich_required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${enrich_workflow}"; then
    echo "Approved enrich workflow is missing required read-only structure text: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${notify_required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${notify_workflow}"; then
    echo "Approved notify workflow is missing required notify-only structure text: ${phrase}" >&2
    exit 1
  fi
done

for asset_path in "${enrich_workflow}" "${notify_workflow}"; do
  asset_name="${asset_path##*/}"
  workflow_node_types=()
  while IFS= read -r node_type; do
    workflow_node_types+=("${node_type}")
  done < <(
    grep -o 'n8n-nodes-base\.[^"]*' "${asset_path}" | LC_ALL=C sort -u
  )

  for node_type in "${workflow_node_types[@]}"; do
    is_allowed="false"
    for allowed_node_type in "${allowed_node_types[@]}"; do
      if [[ "${node_type}" == "${allowed_node_type}" ]]; then
        is_allowed="true"
        break
      fi
    done

    if [[ "${is_allowed}" != "true" ]]; then
      echo "Approved n8n workflow asset uses a non-read-only node type in ${asset_name}: ${node_type}" >&2
      exit 1
    fi
  done
done

if [[ "${actual_categories[*]}" != "${expected_sorted[*]}" ]]; then
  echo "Tracked n8n workflow categories do not match the approved placeholder skeleton." >&2
  echo "Expected categories:" >&2
  printf '  %s\n' "${expected_sorted[@]}" >&2
  echo "Actual categories:" >&2
  printf '  %s\n' "${actual_categories[@]}" >&2
  exit 1
fi

echo "n8n workflow structure matches the approved Phase 6 read-only enrich and notify asset boundaries."
