#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md"
baseline_path="${repo_root}/docs/maintainability-hotspot-baseline.txt"
closeout_path="${repo_root}/docs/phase-50-maintainability-closeout.md"

required_headings=(
  "# ADR-0005: Phase 50.8 Residual Service Hotspot Migration Contract"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Residual Hotspot Map"
  "## 4. Migration Order"
  "## 5. Measurement Guard"
  "## 6. Validation"
  "## 7. Non-Goals"
  "## 8. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-29"
  "- **Related Issues**: #961, #962"
  "ADR-0004 remains authoritative for the Phase 50 hotspot ordering decision."
  "ADR-0003 remains authoritative for the public facade-preservation exception."
  "Phase 50.7 recorded the current residual service ceiling in \`docs/maintainability-hotspot-baseline.txt\`."
  "This ADR does not refresh the baseline because implementation evidence does not exist yet."
  "The residual Phase 50.8 \`service.py\` helper clusters are:"
  "- readiness helper cluster"
  "- action-review helper cluster"
  "- intake/lifecycle helper cluster"
  "- action-policy helper cluster"
  "The Phase 50.8 migration order is:"
  "1. readiness helper cluster"
  "2. action-review helper cluster"
  "3. intake/lifecycle helper cluster"
  "4. action-policy helper cluster"
  "Readiness helpers must move before action-review helpers that consume readiness projections."
  "Action-review helpers must move before action-policy helpers so review-state projections stay anchored to authoritative action records."
  "Intake/lifecycle helpers must move before action-policy helpers so action policy does not infer case, alert, lifecycle, or evidence linkage from names, paths, comments, or neighboring records."
  "The current Phase 50.7 ceiling remains:"
  "- \`max_lines=5660\`"
  "- \`max_effective_lines=5250\`"
  "- \`max_facade_methods=203\`"
  "The Phase 50.8 implementation target is:"
  "- \`max_lines <= 5200\`"
  "- \`max_effective_lines <= 4850\`"
  "- \`max_facade_methods <= 175\`"
  "A Phase 50.8 closeout may record an exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.7 ceiling."
  "Any baseline refresh before implementation evidence exists is forbidden."
  "Public service entrypoints, runtime behavior, configuration shape, authority semantics, and durable-state side effects remain unchanged."
  "AegisOps control-plane records remain authoritative workflow truth."
  "Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context."
  "Run \`bash scripts/verify-phase-50-8-residual-service-hotspot-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-50-8-residual-service-hotspot-contract.sh\`."
  "Run \`bash scripts/verify-maintainability-hotspots.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 962 --config <supervisor-config-path>\`."
  "No production code extraction is approved by this ADR."
  "No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, or operator authority behavior is changed."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 50.8 residual service hotspot contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${baseline_path}" ]]; then
  echo "Missing maintainability hotspot baseline: ${baseline_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 50.8 residual service hotspot contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 50.8 residual service hotspot contract statement: ${phrase}" >&2
    exit 1
  fi
done

phase50_7_baseline_entry="control-plane/aegisops_control_plane/service.py max_lines=5660 max_effective_lines=5250 max_facade_methods=203 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.7 issue=#953"
baseline_entry="$(grep -E '^control-plane/aegisops_control_plane/service.py[[:space:]]' "${baseline_path}" || true)"
baseline_entry_count="$(printf '%s\n' "${baseline_entry}" | sed '/^$/d' | wc -l | tr -d ' ')"
if [[ "${baseline_entry_count}" -eq 0 ]]; then
  echo "Phase 50.8 contract requires a service.py hotspot baseline entry." >&2
  exit 1
fi
if [[ "${baseline_entry_count}" -ne 1 ]]; then
  echo "Phase 50.8 contract requires exactly one service.py hotspot baseline entry." >&2
  exit 1
fi

if [[ "${baseline_entry}" == "${phase50_7_baseline_entry}" ]]; then
  echo "Phase 50.8 residual service hotspot contract fixes clusters, migration order, measurement guard, non-goals, and validation commands."
  exit 0
fi

metadata_value() {
  local key="$1"
  awk -v key="${key}" '
    {
      for (field_index = 2; field_index <= NF; field_index++) {
        split($field_index, item, "=")
        if (item[1] == key) {
          print item[2]
          exit
        }
      }
    }
  ' <<<"${baseline_entry}"
}

max_lines="$(metadata_value max_lines)"
max_effective_lines="$(metadata_value max_effective_lines)"
max_facade_methods="$(metadata_value max_facade_methods)"
facade_class="$(metadata_value facade_class)"
adr_exception="$(metadata_value adr_exception)"
phase="$(metadata_value phase)"
issue="$(metadata_value issue)"

if [[
  "${facade_class}" != "AegisOpsControlPlaneService" ||
  "${adr_exception}" != "ADR-0003"
]]; then
  echo "Phase 50.8 contract requires the Phase 50.7 service.py ceiling to remain unchanged until implementation evidence exists. After implementation evidence exists, it requires either the final Phase 50.8.6 closeout baseline for #967 or the lower superseding Phase 50.9.6 closeout baseline for #980." >&2
  exit 1
fi

if [[
  -z "${max_lines}" ||
  -z "${max_effective_lines}" ||
  -z "${max_facade_methods}" ||
  "${max_lines}" -ge 5660 ||
  "${max_effective_lines}" -ge 5250 ||
  "${max_facade_methods}" -ge 203
]]; then
  echo "Phase 50.8 final closeout baseline must remain lower than the Phase 50.7 ceiling." >&2
  exit 1
fi

if [[ ! -f "${closeout_path}" ]]; then
  echo "Phase 50.8 final baseline refresh requires closeout evidence: ${closeout_path}" >&2
  exit 1
fi

if [[ "${phase}" == "50.8.6" && "${issue}" == "#967" ]]; then
  closeout_required_phrases=(
    "Phase 50.8.6"
    "#967"
    "\`max_lines=${max_lines}\`"
    "\`max_effective_lines=${max_effective_lines}\`"
    "\`max_facade_methods=${max_facade_methods}\`"
    "action review projection and visibility helper cluster"
    "intake and authoritative-state guard helpers"
    "silent re-growth"
    "another decomposition decision"
  )
elif [[ "${phase}" == "50.9.6" && "${issue}" == "#980" ]]; then
  if [[
    "${max_lines}" -gt 3158 ||
    "${max_effective_lines}" -gt 2853 ||
    "${max_facade_methods}" -gt 173
  ]]; then
    echo "Phase 50.9 superseding closeout baseline must remain at or below the accepted #980 ceiling." >&2
    exit 1
  fi
  closeout_required_phrases=(
    "Phase 50.9.6"
    "#980"
    "\`max_lines=${max_lines}\`"
    "\`max_effective_lines=${max_effective_lines}\`"
    "\`max_facade_methods=${max_facade_methods}\`"
    "facade dispatch and authority-boundary guard helpers"
    "projection split does not require a baseline entry"
    "silent re-growth"
    "another decomposition decision"
  )
else
  echo "Phase 50.8 contract requires a final Phase 50.8.6 closeout baseline for #967 or a lower superseding Phase 50.9.6 closeout baseline for #980." >&2
  exit 1
fi

for phrase in "${closeout_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${closeout_path}"; then
    echo "Phase 50.8 final closeout evidence is missing: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 50.8 residual service hotspot contract fixes clusters, migration order, measurement guard, non-goals, and validation commands."
