#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-57-closeout-evaluation.md"
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
  echo "Missing Phase 57.R closeout evaluation: ${doc_path}" >&2
  exit 1
fi

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
## Phase 57.R Supportability Pre-Refactor Closeout Addendum
- **Status**: Accepted as behavior-preserving supportability pre-refactor closeout evidence for Phase 58 handoff; Phase 58 supportability is not complete.
- **Related Issues**: #1224, #1225, #1226, #1227, #1228, #1229
Phase 57.R is accepted only as a supportability pre-refactor baseline that preserves Phase 57 admin behavior, restore/readiness semantics, public facade compatibility, CLI/API behavior, persistence, approval, execution, reconciliation, and AI boundaries.
This addendum does not claim Phase 58 supportability, doctor completeness, support bundles, backup/restore support operations, break-glass support operations, Beta, RC, GA, or commercial replacement readiness.
| #1224 | Epic: Phase 57.R Supportability pre-refactor before Phase 58 | Closed by the ordered #1225 through #1229 evidence packet. |
| #1225 | Phase 57.R.1 Add supportability refactor boundary ADR and inventory | Closed. Added ADR-0019 and its focused verifier without runtime behavior changes. |
| #1226 | Phase 57.R.2 Split Phase 57 admin UI pages and posture data | Closed. Split the monolithic admin page into page modules and shared posture/display data while preserving rendered admin behavior and route gates. |
| #1227 | Phase 57.R.3 Extract backup / restore payload codec and validation boundaries | Closed. Extracted backup codec and restore validation helpers while preserving restore validation, fail-closed behavior, public facade compatibility, and durable-state cleanliness expectations. |
| #1228 | Phase 57.R.4 Shard restore and readiness tests into focused suites | Closed. Split restore/readiness coverage into focused test modules without deleting negative coverage or weakening assertions. |
| #1229 | Phase 57.R.5 Phase 57.R closeout evaluation and maintainability guard refresh | Closed when this addendum, focused closeout verifier, hotspot verifier, path hygiene, focused tests, and issue-lint evidence pass. |
`docs/adr/0019-phase-57-r-supportability-pre-refactor-boundary.md`
`apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/UserRoleAdminPage.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/SourceProfileAdministrationPage.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/ActionPolicyAdministrationPage.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/RetentionPolicyAdministrationPage.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/AuditExportAdministrationPage.tsx`
`apps/operator-ui/src/app/operatorConsolePages/adminPages/adminPostureData.ts`
`control-plane/aegisops/control_plane/runtime/restore_backup_codec.py`
`control-plane/aegisops/control_plane/runtime/restore_backup_validation.py`
`control-plane/aegisops/control_plane/runtime/restore_readiness_backup_restore.py`
`control-plane/tests/test_service_restore_backup_codec.py`
`control-plane/tests/test_service_restore_drill_transactions.py`
`control-plane/tests/test_service_restore_readiness_boundaries.py`
`control-plane/tests/test_service_restore_runtime_visibility.py`
`control-plane/tests/test_service_restore_validation.py`
`control-plane/tests/test_service_readiness_projection.py`
`control-plane/tests/test_cli_inspection_restore_readiness.py`
| Admin UI page split | `adminPages.tsx` | 802 lines | 877 lines across the extracted admin page, posture data, display helper, and structure test files; `adminPages.tsx` is now a 1-line compatibility re-export. |
| Restore backup / validation runtime split | `restore_readiness_backup_restore.py` | 1,494 lines | 1,562 lines across `restore_readiness_backup_restore.py`, `restore_backup_codec.py`, and `restore_backup_validation.py`; the original module is down to 495 lines. |
| Restore/readiness persistence tests | `test_service_persistence_restore_readiness.py` | 6,272 lines | 6,472 lines across the sharded restore/readiness persistence, projection, backup codec, drill transaction, boundary, runtime visibility, and validation suites, plus shared support; the original module is now a 5-line compatibility re-export. |
| CLI restore/readiness tests | `test_cli_inspection_runtime_surface.py` | 1,436 lines | 1,450 lines across runtime-surface and restore/readiness CLI suites; restore/readiness CLI coverage now lives in `test_cli_inspection_restore_readiness.py`. |
`npm test --workspace apps/operator-ui -- --run src/app/operatorConsolePages/adminPages/adminPagesStructure.test.ts src/app/OperatorRoutes.test.tsx src/app/OperatorRoutes.authAndShell.testSuite.tsx src/auth/roleMatrix.test.ts src/auth/session.test.ts src/app/optionalExtensionVisibility.test.tsx`
`python3 -m unittest control-plane/tests/test_service_restore_backup_codec.py control-plane/tests/test_service_restore_drill_transactions.py control-plane/tests/test_service_restore_readiness_boundaries.py control-plane/tests/test_service_restore_runtime_visibility.py control-plane/tests/test_service_restore_validation.py control-plane/tests/test_service_readiness_projection.py control-plane/tests/test_cli_inspection_restore_readiness.py control-plane/tests/test_service_persistence_restore_readiness.py`
`bash scripts/verify-maintainability-hotspots.sh`
Known maintainability hotspot baseline remains present: `control-plane/aegisops/control_plane/service.py` lines=1393, effective_lines=1241, AegisOpsControlPlaneService methods=95, signals=7.
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-57-r-closeout-evaluation.sh`
`node <codex-supervisor-root>/dist/index.js issue-lint 1224 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1225 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1226 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1227 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1228 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1229 --config <supervisor-config-path>`
The maintainability hotspot baseline is unchanged because measured evidence shows no new hotspot and no accepted ceiling regression.
Phase 58 can consume the extracted admin modules, restore backup codec, restore validation helper, restore/readiness test shards, ADR-0019 inventory, and unchanged maintainability guard as a reviewed pre-refactor baseline.
Phase 58 must still implement doctor output, support bundle behavior, customer-safe diagnostics, backup/restore support operations, break-glass support workflows, escalation evidence, and supportability acceptance tests.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${phrase}" "Phase 57.R closeout evidence"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}"; then
  echo "Forbidden Phase 57.R closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

is_allowed_negated_forbidden_claim() {
  local forbidden="$1"
  local claim_line="$2"
  local phase58_incomplete_claim_line="This closeout does not claim Phase 58 supportability is complete, Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

  case "${forbidden}" in
    "Phase 58 supportability is complete")
      [[ "${claim_line}" == "${phase58_incomplete_claim_line}" ]]
      ;;
    *)
      return 1
      ;;
  esac
}

for forbidden in \
  "Phase 57.R implements Phase 58 supportability" \
  "Phase 58 supportability is complete" \
  "Phase 57.R proves Beta readiness" \
  "Phase 57.R proves RC readiness" \
  "Phase 57.R proves GA readiness" \
  "Phase 57.R proves commercial replacement readiness" \
  "Phase 57.R changes runtime behavior" \
  "Phase 57.R changes public service facade behavior" \
  "Phase 57.R changes CLI/API behavior" \
  "Phase 57.R weakens restore validation" \
  "Phase 57.R changes persistence or schema" \
  "Phase 57.R changes approval, execution, reconciliation, or AI behavior" \
  "Maintainability baseline was raised to hide a new hotspot"; do
  while IFS= read -r claim_line; do
    if ! is_allowed_negated_forbidden_claim "${forbidden}" "${claim_line}"; then
      echo "Forbidden Phase 57.R closeout evaluation claim: ${forbidden}" >&2
      exit 1
    fi
  done < <(grep -F -- "${forbidden}" "${absolute_doc_path}" || true)
done

echo "Phase 57.R closeout evaluation records refactor child outcomes, measurements, verifier evidence, accepted limits, and Phase 58 handoff."
