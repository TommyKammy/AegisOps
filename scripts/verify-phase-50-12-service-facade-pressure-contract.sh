#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0009-phase-50-12-service-facade-pressure-contract.md"
baseline_path="${repo_root}/docs/maintainability-hotspot-baseline.txt"
closeout_path="${repo_root}/docs/phase-50-maintainability-closeout.md"

required_headings=(
  "# ADR-0009: Phase 50.12 Service Facade Pressure Contract"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Starting Measurements"
  "## 4. Extraction Scope"
  "## 5. Migration Order"
  "## 6. Validation"
  "## 7. Non-Goals"
  "## 8. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-30"
  "- **Related Issues**: #1015, #1016"
  "- **Depends On**: #1007"
  "Phase 50.11.7 closed #1007 and recorded the accepted residual \`service.py\` ceiling in \`docs/maintainability-hotspot-baseline.txt\`."
  "ADR-0003 remains authoritative for the public facade-preservation exception."
  "ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule."
  "ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence."
  "ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard."
  "ADR-0007 remains authoritative for the Phase 50.10 facade floor and external-evidence guard."
  "ADR-0008 remains authoritative for the Phase 50.11 residual DTO/helper extraction order and closeout validation."
  "\`docs/maintainability-decomposition-thresholds.md\` remains the governing hotspot trigger policy."
  "Phase 50.12 needs a repo-owned contract before final facade-pressure implementation slices start so the sub-1500 target, unchanged behavior boundaries, and verification commands are fixed before code moves."
  "This ADR does not refresh the baseline because Phase 50.12 implementation evidence does not exist yet and follow-on implementation slices remain."
  "Phase 50.12 will reduce the residual \`service.py\` facade pressure by extracting or fencing directly linked service facade helper clusters in a fixed, behavior-preserving order."
  "The Phase 50.12 residual extraction clusters are:"
  "- constructor/composition wiring cluster"
  "- action request/approval cluster"
  "- casework write delegate cluster"
  "- assistant residual helper cluster"
  "- detection/action residual helper cluster"
  "Public service entrypoints, runtime behavior, configuration shape, authority semantics, response semantics, and durable-state side effects remain unchanged."
  "AegisOps control-plane records remain authoritative workflow truth."
  "Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context."
  "The Phase 50.11.7 starting ceiling for \`control-plane/aegisops_control_plane/service.py\` is:"
  "- \`max_lines=1812\`"
  "- \`max_effective_lines=1632\`"
  "- \`max_facade_methods=125\`"
  "- \`facade_class=AegisOpsControlPlaneService\`"
  "- \`phase=50.11.7\`"
  "- \`issue=#1007\`"
  "- \`physical_lines=1812\`"
  "- \`effective_lines=1632\`"
  "- \`AegisOpsControlPlaneService methods=125\`"
  "The Phase 50.12 implementation target for \`control-plane/aegisops_control_plane/service.py\` is:"
  "- \`max_lines <= 1500\`"
  "- \`max_effective_lines <= 1350\`"
  "- \`max_facade_methods <= 95\`"
  "The sub-1500 target is a pressure-reduction target, not permission to change behavior."
  "A Phase 50.12 closeout may record a lower exception only if it names the unresolved residual cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.11.7 ceiling."
  "If the sub-1500 target cannot be reached safely, the fallback is to preserve behavior, keep the public \`AegisOpsControlPlaneService\` facade, record the blocker cluster explicitly, and require the next contract to lower or fence that exact residual cluster instead of claiming long-term completion."
  "Any \`service.py\` baseline refresh before Phase 50.12 implementation evidence exists is forbidden."
  "The constructor/composition wiring cluster owns internal collaborator construction, dependency binding, and facade composition routing that can move behind explicit internal builders without changing public initialization semantics."
  "The action request/approval cluster owns internal helper code for action request creation, approval decisions, delegation binding, reconciliation routing, mismatch handling, and receipt linkage while preserving authoritative action-review records as the source of truth."
  "The casework write delegate cluster owns bounded case mutation delegates for observations, leads, recommendations, handoff, disposition, and linked case lifecycle writes while preserving authoritative case records as workflow truth."
  "The assistant residual helper cluster owns remaining assistant context, advisory, recommendation, citation, draft, and live-assistant helper code that is directly linked to the anchored service request."
  "The detection/action residual helper cluster owns remaining detection intake, case linkage, external-evidence admission, action-review inspection, and action lifecycle helper code that still sits in the service facade."
  "No extracted helper may infer tenant, repository, account, issue, case, alert, host, environment, approval, execution, reconciliation, assistant, detection, action, or evidence linkage from naming conventions, path shape, comments, nearby metadata, sibling records, or operator-facing summaries alone."
  "The Phase 50.12 migration order is:"
  "1. constructor/composition wiring cluster"
  "2. action request/approval cluster"
  "3. casework write delegate cluster"
  "4. assistant residual helper cluster"
  "5. detection/action residual helper cluster"
  "6. closeout and hotspot-baseline guard cluster"
  "Constructor/composition wiring must move first so later slices depend on explicit collaborator ownership instead of adding more facade-local construction pressure."
  "Action request/approval helpers must move before casework write delegates so write-path mutations keep using authoritative approval, delegation, reconciliation, and receipt records."
  "Casework write delegates must move before assistant residual helpers so advisory surfaces continue to attach to directly linked authoritative case records."
  "Assistant residual helpers must move before detection/action residual helpers so recommendation and citation context cannot broaden evidence, case, or action linkage by sibling or same-parent inference."
  "Detection/action residual helpers must move before closeout so any residual \`service.py\` baseline decision is based on implementation evidence rather than a desired target."
  "Run \`bash scripts/verify-phase-50-12-service-facade-pressure-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh\`."
  "Run \`bash scripts/verify-maintainability-hotspots.sh\`."
  "Run \`bash scripts/test-verify-maintainability-hotspots.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1016 --config <supervisor-config-path>\`."
  "For the Phase 50.12 Epic, run the same issue-lint command for each Phase 50.12 child issue before allowing implementation slices to proceed."
  "- No production code extraction is approved by this ADR."
  "- No constructor, composition, action request, approval, casework write, assistant, detection, action, or external-evidence module split is approved by this ADR."
  "- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed."
  "- No baseline refresh is approved before Phase 50.12 implementation evidence exists."
  "- No subordinate source, operator-facing projection, summary, badge, counter, snapshot, DTO, recommendation, evidence snippet, reconciliation note, or helper-module output becomes authoritative workflow truth."
  "- No exception may raise the Phase 50.11.7 ceiling."
  "- No long-term 50-method completion claim is approved unless later child issues prove it safely."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 50.12 service facade pressure contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${baseline_path}" ]]; then
  echo "Missing maintainability hotspot baseline: ${baseline_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 50.12 service facade pressure contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 50.12 service facade pressure contract statement: ${phrase}" >&2
    exit 1
  fi
done

starting_service_baseline_entry="control-plane/aegisops_control_plane/service.py max_lines=1812 max_effective_lines=1632 max_facade_methods=125 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.11.7 issue=#1007"
phase50_12_4_service_baseline_entry="control-plane/aegisops_control_plane/service.py max_lines=1619 max_effective_lines=1445 max_facade_methods=117 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.12.4 issue=#1019"
service_entry="$(grep -Fx -- "${starting_service_baseline_entry}" "${baseline_path}" || true)"
phase50_12_4_service_entry="$(grep -Fx -- "${phase50_12_4_service_baseline_entry}" "${baseline_path}" || true)"
service_entry_count="$(printf '%s\n' "${service_entry}" | sed '/^$/d' | wc -l | tr -d ' ')"
phase50_12_4_service_entry_count="$(printf '%s\n' "${phase50_12_4_service_entry}" | sed '/^$/d' | wc -l | tr -d ' ')"
service_path_entry_count="$(
  awk -v prefix="control-plane/aegisops_control_plane/service.py " \
    'index($0, prefix) == 1 { count += 1 } END { print count + 0 }' \
    "${baseline_path}"
)"
if [[ "${service_path_entry_count}" -ne 1 ]]; then
  echo "Phase 50.12 contract requires exactly one service.py hotspot baseline entry." >&2
  exit 1
fi
if [[ "${service_entry_count}" -eq 1 ]]; then
  echo "Phase 50.12 service facade pressure contract fixes residual clusters, starting measurements, sub-1500 target ceilings, fallback rules, authority non-goals, migration order, and validation commands."
  exit 0
fi
if [[ "${phase50_12_4_service_entry_count}" -eq 1 ]]; then
  if [[ ! -f "${closeout_path}" ]]; then
    echo "Phase 50.12.4 baseline requires docs/phase-50-maintainability-closeout.md evidence." >&2
    exit 1
  fi
  phase50_12_4_closeout_phrases=(
    "Phase 50.12.4 then moved the casework write compatibility delegates out of \`AegisOpsControlPlaneService\` and into \`control-plane/aegisops_control_plane/case_workflow.py\`, preserving the public facade entrypoints for observation, lead, recommendation, handoff, and disposition writes."
    "- \`max_lines=1619\`"
    "- \`max_effective_lines=1445\`"
    "- \`max_facade_methods=117\`"
    "- \`phase=50.12.4\`"
    "- \`issue=#1019\`"
  )
  for phrase in "${phase50_12_4_closeout_phrases[@]}"; do
    if ! grep -Fq -- "${phrase}" "${closeout_path}"; then
      echo "Phase 50.12.4 baseline requires closeout evidence: ${phrase}" >&2
      exit 1
    fi
  done
  echo "Phase 50.12 service facade pressure contract fixes residual clusters, starting measurements, sub-1500 target ceilings, fallback rules, authority non-goals, migration order, and validation commands."
  exit 0
fi
if [[ "${service_entry_count}" -eq 0 ]]; then
  if [[ "${service_path_entry_count}" -ne 0 ]]; then
    echo "Phase 50.12 contract forbids refreshing the service.py hotspot baseline before implementation evidence exists." >&2
    exit 1
  fi
  echo "Phase 50.12 contract requires the accepted Phase 50.11.7 service.py hotspot baseline entry." >&2
  exit 1
fi
if [[ "${service_entry}" != "${starting_service_baseline_entry}" ]]; then
  echo "Phase 50.12 contract forbids refreshing the service.py hotspot baseline before implementation evidence exists." >&2
  exit 1
fi

echo "Phase 50.12 service facade pressure contract fixes residual clusters, starting measurements, sub-1500 target ceilings, fallback rules, authority non-goals, migration order, and validation commands."
