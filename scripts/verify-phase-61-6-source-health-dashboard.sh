#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_files=(
  "control-plane/aegisops/control_plane/models.py"
  "control-plane/aegisops/control_plane/record_validation.py"
  "control-plane/aegisops/control_plane/validation/phase61_record_validators.py"
  "apps/operator-ui/src/app/operatorConsolePages/sourceHealthDashboardPages.tsx"
  "apps/operator-ui/src/app/OperatorRoutes.sourceHealthDashboard.testSuite.tsx"
  "postgres/control-plane/migrations/0014_phase_61_source_health_records.sql"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "${repo_root}/${path}" ]]; then
    echo "Missing Phase 61.6 source-health dashboard artifact: ${path}" >&2
    exit 1
  fi
done

for expected in \
  "stale_source" \
  "missing_agent" \
  "parser_failure" \
  "volume_anomaly" \
  "credential_degraded" \
  "detector_drift" \
  "source_native_authority" \
  "display_state_authority" \
  "cache_sourced"; do
  if ! rg -q "${expected}" \
    "${repo_root}/control-plane/aegisops/control_plane/record_validation.py" \
    "${repo_root}/control-plane/aegisops/control_plane/validation/phase61_record_validators.py" \
    "${repo_root}/apps/operator-ui/src/operatorDataProvider/listSemantics.ts" \
    "${repo_root}/apps/operator-ui/src/app/operatorConsolePages/sourceHealthDashboardPages.tsx"; then
    echo "Missing Phase 61.6 source-health dashboard term: ${expected}" >&2
    exit 1
  fi
done

(cd "${repo_root}" && python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract)
(cd "${repo_root}" && npm --prefix apps/operator-ui test -- OperatorRoutes.test.tsx)

mac_profile_pattern="$(printf '/%s/' "Users")"
posix_home_pattern="$(printf '/%s/[^[:space:]]+' "home")"
windows_profile_pattern="$(printf 'C:%s%s%s%s' "\\" "\\" "Users" "\\\\")"
home_path_pattern="${mac_profile_pattern}|${posix_home_pattern}|${windows_profile_pattern}"
if rg -n "${home_path_pattern}" \
  "${repo_root}/control-plane/tests/test_phase61_detector_lifecycle_record_contract.py" \
  "${repo_root}/apps/operator-ui/src/app/OperatorRoutes.sourceHealthDashboard.testSuite.tsx" \
  "${repo_root}/scripts/verify-phase-61-6-source-health-dashboard.sh"; then
  echo "Forbidden Phase 61.6 source-health dashboard absolute path usage detected" >&2
  exit 1
fi

echo "Phase 61.6 source-health dashboard focused verification passed."
