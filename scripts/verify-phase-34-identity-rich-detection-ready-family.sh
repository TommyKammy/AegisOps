#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

entra_onboarding_doc="${repo_root}/docs/source-families/entra-id/onboarding-package.md"
entra_runbook_doc="${repo_root}/docs/source-families/entra-id/analyst-triage-runbook.md"
github_onboarding_doc="${repo_root}/docs/source-families/github-audit/onboarding-package.md"
microsoft_onboarding_doc="${repo_root}/docs/source-families/microsoft-365-audit/onboarding-package.md"
profile_tests="${repo_root}/control-plane/tests/test_phase14_identity_rich_source_profile_docs.py"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_contains() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fq -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required text in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_test_name() {
  local file_path="$1"
  local test_name="$2"

  if ! python3 - "${file_path}" "${test_name}" <<'PY'
from __future__ import annotations

import ast
import pathlib
import sys


def base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = base_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None


target_path = pathlib.Path(sys.argv[1])
target_test = sys.argv[2]
tree = ast.parse(target_path.read_text(encoding="utf-8"))

for node in tree.body:
    if not isinstance(node, ast.ClassDef):
        continue
    bases = {name for base in node.bases if (name := base_name(base))}
    if "unittest.TestCase" not in bases:
        continue
    if any(
        isinstance(child, ast.FunctionDef) and child.name == target_test
        for child in node.body
    ):
        raise SystemExit(0)

raise SystemExit(1)
PY
  then
    echo "Missing required Phase 34 unittest-discoverable test in ${file_path}: ${test_name}" >&2
    exit 1
  fi
}

require_file "${entra_onboarding_doc}" "Missing Entra ID onboarding package"
require_file "${entra_runbook_doc}" "Missing Entra ID triage runbook"
require_file "${github_onboarding_doc}" "Missing GitHub audit onboarding package"
require_file "${microsoft_onboarding_doc}" "Missing Microsoft 365 audit onboarding package"
require_file "${profile_tests}" "Missing identity-rich source profile docs tests"

require_fixed_string "${github_onboarding_doc}" 'Readiness state: `detection-ready`'
require_fixed_string "${entra_onboarding_doc}" 'Readiness state: `detection-ready`'
require_fixed_string "${microsoft_onboarding_doc}" 'Readiness state: `schema-reviewed`'

if grep -Fqx -- 'Readiness state: `detection-ready`' "${microsoft_onboarding_doc}" >/dev/null; then
  echo "Microsoft 365 audit must not be silently uplifted to detection-ready in Phase 34." >&2
  exit 1
fi

required_onboarding_text=(
  "Phase 34 selects Entra ID as the second detection-ready family because it already has the clearer reviewed multi-source evidence path from the approved Entra ID case-admission slice."
  "Reviewed detection-ready scope: Entra ID audit records admitted through the reviewed Wazuh-backed intake boundary for tenant, directory, authentication, and privilege-change review signals."
  "Reviewed parser evidence source: Wazuh \`entra_id\` decoder evidence represented by \`decoder.name\`, Wazuh rule metadata, the reviewed \`entra-id-alert.json\` fixture, the Phase 25 reviewed Entra ID case-admission slice, and the parser ownership boundary in this package."
  "Provenance Evidence: Entra ID records remain detection-ready only when the Wazuh intake boundary preserves \`rule.id\`, \`rule.level\`, \`rule.description\`, \`decoder.name\`, \`location\`, \`timestamp\`, \`manager.name\`, and the Entra ID \`data.request_id\` or \`data.correlation_id\` source request context when present."
  "Detector-Use Approval and Limits: Entra ID is approved as a detection-ready source family only for future detection content whose source prerequisites fit the reviewed tenant, directory, authentication, and privilege-change audit scope documented here."
  "Detector activation still requires separate rule review, rollout review, and Wazuh rule lifecycle validation."
)

for expected in "${required_onboarding_text[@]}"; do
  require_fixed_string "${entra_onboarding_doc}" "${expected}"
done

required_runbook_text=(
  "Entra ID may support detector review only within the approved detection-ready scope in the onboarding package."
  "Analysts must treat Entra ID as source evidence for AegisOps review, not as Entra ID-owned workflow truth or direct action authority."
  "If accountable source identity, actor identity, target identity, tenant context, timestamp quality, parser evidence, or Wazuh provenance is missing or malformed, the analyst keeps the item out of detector-ready handling until the prerequisite is repaired or a documented exception path applies."
  "Family-specific false-positive review must remain visible in each triage record and each future detector review that depends on Entra ID."
)

for expected in "${required_runbook_text[@]}"; do
  require_fixed_string "${entra_runbook_doc}" "${expected}"
done

require_contains "${microsoft_onboarding_doc}" "This package remains \`schema-reviewed\` rather than \`detection-ready\` because parser version evidence, broader Microsoft 365 audit field coverage, and explicit detector-use approval remain future work."
require_test_name "${profile_tests}" "test_phase34_entra_id_is_the_only_second_detection_ready_family"

echo "Phase 34 identity-rich detection-ready source family validation remains reviewable and fail closed."
