#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="docs/adr/0019-phase-57-r-supportability-pre-refactor-boundary.md"
absolute_doc_path="${repo_root}/${doc_path}"

require_phrase() {
  local phrase="$1"
  local description="$2"

  if ! grep -Fq -- "${phrase}" "${absolute_doc_path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 57.R supportability pre-refactor boundary ADR: ${doc_path}" >&2
  exit 1
fi

required_headings=(
  "# ADR-0019: Phase 57.R Supportability Pre-Refactor Boundary And Inventory"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Input References"
  "## 4. Refactor Inventory"
  "## 5. Extraction Order"
  "## 6. Retained Public Behavior"
  "## 7. Forbidden Claims"
  "## 8. Verification"
  "## 9. Non-Goals"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${heading}" "Phase 57.R ADR heading"
done

required_phrases=(
  "- **Status**: Accepted for Phase 57.R.1 planning and review."
  "- **Date**: 2026-05-04"
  "- **Related Issues**: #1224, #1225, #1226, #1227, #1228, #1229"
  "- **Depends On**: #1215"
  "This ADR is documentation and verification only. It does not move implementation code, change runtime behavior, change public service facade behavior, change CLI/API behavior, change restore validation semantics, change admin behavior, change RBAC behavior, change persistence, change schema, change approval, change execution, change reconciliation, change AI behavior, or implement Phase 58 supportability features."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event truth, limitation, release, gate, restore validation, and closeout truth."
  "This ADR, extracted helpers, UI posture data, supportability projections, test fixtures, verifier output, issue-lint output, browser state, local cache, admin configuration, role matrix documents, and operator-facing summaries remain subordinate planning, implementation, policy, or validation evidence."
  "If provenance, scope, auth context, record linkage, snapshot consistency, or restore-validation signals are missing, malformed, ambiguous, or only partially trusted, Phase 57.R work must fail closed and preserve the current guard instead of inferring success."
  "That path is not present in this checkout, so this repo-owned ADR uses the tracked Phase 55-57 closeout handoff text and the tracked persona/gate/supportability docs as the local verification source."
  '`apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx`'
  '`apps/operator-ui/src/auth/roleMatrix.ts`'
  '`control-plane/aegisops/control_plane/runtime/restore_readiness.py`'
  '`control-plane/aegisops/control_plane/runtime/restore_readiness_backup_restore.py`'
  '`control-plane/aegisops/control_plane/runtime/restore_readiness_projection.py`'
  '`control-plane/aegisops/control_plane/runtime/runtime_restore_readiness_diagnostics.py`'
  '`control-plane/aegisops/control_plane/runtime/readiness_operability.py`'
  '`control-plane/aegisops/control_plane/service.py`'
  '`control-plane/tests/test_service_restore_backup_codec.py`, `control-plane/tests/test_service_restore_drill_transactions.py`, `control-plane/tests/test_service_readiness_projection.py`, `control-plane/tests/test_service_restore_validation.py`, `control-plane/tests/test_cli_inspection_restore_readiness.py`'
  '`docs/maintainability-hotspot-baseline.txt`'
  "| 57.R.1 | #1225 Add supportability refactor boundary ADR and inventory | Decision record and inventory only. | #1215 |"
  "| 57.R.2 | #1226 Split Phase 57 admin UI pages and posture data | UI and static posture extraction only. | #1225 |"
  "| 57.R.3 | #1227 Extract backup / restore payload codec and validation boundaries | Runtime extraction only. | #1225 |"
  "| 57.R.4 | #1228 Shard restore and readiness tests into focused suites | Test structure only. | #1227 |"
  "| 57.R.5 | #1229 Phase 57.R closeout evaluation and maintainability guard refresh | Closeout evidence and guard refresh only. | #1226, #1227, #1228 |"
  "Revert this ADR and verifier only; no runtime rollback is needed because no runtime files change."
  'Revert the UI module split while keeping the original `adminPages.tsx` rendered behavior and route gates intact.'
  "Revert the extracted codec and validation modules to the current restore/readiness runtime files without changing public facade or persisted records."
  "Revert test sharding only; do not delete negative coverage or weaken assertions to preserve a split."
  "Revert closeout or guard updates if they overclaim supportability completion, hide hotspot regrowth, or conflict with the accepted behavior-preserving evidence."
  "public service facade behavior and method compatibility;"
  "restore validation semantics, rejected restore behavior, snapshot consistency expectations, and durable-state cleanliness after failed restore paths;"
  "admin UI rendered surfaces, role restrictions, and RBAC posture;"
  '`bash scripts/verify-phase-57-r-supportability-pre-refactor-boundary.sh`'
  '`bash scripts/test-verify-phase-57-r-supportability-pre-refactor-boundary.sh`'
  '`bash scripts/verify-publishable-path-hygiene.sh`'
  '`node <codex-supervisor-root>/dist/index.js issue-lint 1224 --config <supervisor-config-path>`'
  '`node <codex-supervisor-root>/dist/index.js issue-lint 1225 --config <supervisor-config-path>`'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${phrase}" "Phase 57.R ADR statement"
done

required_files=(
  "docs/phase-57-closeout-evaluation.md"
  "docs/maintainability-decomposition-thresholds.md"
  "docs/maintainability-hotspot-baseline.txt"
  "docs/phase-50-maintainability-closeout.md"
  "docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
  "docs/deployment/support-playbook-break-glass-rehearsal.md"
  "docs/phase-51-4-smb-personas-jobs-to-be-done.md"
  "apps/operator-ui/src/app/OperatorRoutes.tsx"
  "apps/operator-ui/src/app/OperatorShell.tsx"
  "apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx"
  "apps/operator-ui/src/auth/roleMatrix.ts"
  "apps/operator-ui/src/auth/session.ts"
  "apps/operator-ui/src/auth/navigation.ts"
  "apps/operator-ui/src/app/OperatorRoutes.authAndShell.testSuite.tsx"
  "apps/operator-ui/src/app/OperatorRoutes.test.tsx"
  "apps/operator-ui/src/auth/roleMatrix.test.ts"
  "apps/operator-ui/src/auth/session.test.ts"
  "apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx"
  "control-plane/aegisops/control_plane/runtime/restore_readiness.py"
  "control-plane/aegisops/control_plane/runtime/restore_readiness_backup_restore.py"
  "control-plane/aegisops/control_plane/runtime/restore_readiness_projection.py"
  "control-plane/aegisops/control_plane/runtime/runtime_restore_readiness_diagnostics.py"
  "control-plane/aegisops/control_plane/runtime/readiness_operability.py"
  "control-plane/aegisops/control_plane/runtime/readiness_contracts.py"
  "control-plane/aegisops/control_plane/runtime/runtime_boundary.py"
  "control-plane/aegisops/control_plane/service.py"
  "control-plane/aegisops/control_plane/service_composition.py"
  "control-plane/aegisops/control_plane/api/http_runtime_surface.py"
  "control-plane/aegisops/control_plane/api/entrypoint_support.py"
  "control-plane/tests/test_service_restore_backup_codec.py"
  "control-plane/tests/test_service_restore_drill_transactions.py"
  "control-plane/tests/test_service_readiness_projection.py"
  "control-plane/tests/test_service_restore_validation.py"
  "control-plane/tests/test_cli_inspection_restore_readiness.py"
  "control-plane/tests/test_phase37_reviewed_record_chain_rehearsal.py"
  "control-plane/tests/test_phase57_7_ai_enablement_admin_toggle.py"
  "control-plane/tests/test_service_boundary_refactor_regression_validation.py"
  "control-plane/tests/test_support_package.py"
  "scripts/verify-maintainability-hotspots.sh"
  "scripts/test-verify-maintainability-hotspots.sh"
)

for required_file in "${required_files[@]}"; do
  require_phrase "\`${required_file}\`" "Phase 57.R ADR inventory path"

  if [[ ! -e "${repo_root}/${required_file}" ]]; then
    echo "Phase 57.R ADR inventory references missing file: ${required_file}" >&2
    exit 1
  fi
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}"; then
  echo "Forbidden Phase 57.R ADR: workstation-local absolute path detected" >&2
  exit 1
fi

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN {
      claim_lower = tolower(claim)
      gsub(/[[:space:]]+/, " ", claim_lower)
      text = ""
    }
    /^## 7\. Forbidden Claims$/ { in_forbidden = 1; next }
    /^## / && in_forbidden { in_forbidden = 0 }
    !in_forbidden {
      line = tolower($0)
      gsub(/[[:space:]]+/, " ", line)
      text = text " " line
    }
    END {
      gsub(/[[:space:]]+/, " ", text)
      exit(index(text, claim_lower) ? 0 : 1)
    }
  ' "${absolute_doc_path}"
}

for forbidden in \
  "Phase 57.R implements Phase 58 supportability" \
  "Phase 58 supportability is complete" \
  "This refactor changes runtime behavior" \
  "This refactor changes public service facade behavior" \
  "This refactor changes CLI/API behavior" \
  "This refactor weakens restore validation" \
  "This refactor approves admin CRUD expansion" \
  "This refactor changes RBAC behavior" \
  "This refactor changes persistence or schema" \
  "This refactor changes approval, execution, reconciliation, or AI behavior" \
  "Verifier output is authoritative workflow truth" \
  "UI cache is authoritative workflow truth" \
  "Supportability projections are authoritative restore truth"; do
  if contains_forbidden_outside_forbidden_section "${forbidden}"; then
    echo "Forbidden Phase 57.R ADR claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 57.R supportability pre-refactor boundary ADR names inventory, extraction order, rollback paths, retained behavior, and authority limits."
