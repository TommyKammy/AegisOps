#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-14-identity-rich-source-expansion-ci-validation.md"
design_doc="${repo_root}/docs/phase-14-identity-rich-source-family-design.md"
github_onboarding_doc="${repo_root}/docs/source-families/github-audit/onboarding-package.md"
github_runbook_doc="${repo_root}/docs/source-families/github-audit/analyst-triage-runbook.md"
microsoft_onboarding_doc="${repo_root}/docs/source-families/microsoft-365-audit/onboarding-package.md"
microsoft_runbook_doc="${repo_root}/docs/source-families/microsoft-365-audit/analyst-triage-runbook.md"
entra_onboarding_doc="${repo_root}/docs/source-families/entra-id/onboarding-package.md"
entra_runbook_doc="${repo_root}/docs/source-families/entra-id/analyst-triage-runbook.md"
profile_tests="${repo_root}/control-plane/tests/test_phase14_identity_rich_source_profile_docs.py"
wazuh_tests="${repo_root}/control-plane/tests/test_wazuh_adapter.py"
service_tests="${repo_root}/control-plane/tests/test_service_persistence_ingest_case_lifecycle.py"
cli_tests="${repo_root}/control-plane/tests/test_cli_inspection.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

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

require_test_name() {
  local file_path="$1"
  local test_name="$2"
  local support_path
  support_path="$(dirname "${file_path}")/_service_persistence_support.py"

  if ! python3 - "${file_path}" "${support_path}" "${test_name}" <<'PY'
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


def class_index(path: pathlib.Path) -> dict[str, tuple[set[str], list[str]]]:
    if not path.is_file():
        return {}

    tree = ast.parse(path.read_text(encoding="utf-8"))
    index: dict[str, tuple[set[str], list[str]]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {
            child.name for child in node.body if isinstance(child, ast.FunctionDef)
        }
        bases = [name for base in node.bases if (name := base_name(base))]
        index[node.name] = (methods, bases)
    return index


def is_testcase_class(
    class_name: str,
    classes: dict[str, tuple[set[str], list[str]]],
    seen: set[str] | None = None,
) -> bool:
    if seen is None:
        seen = set()
    if class_name in seen:
        return False
    seen.add(class_name)

    class_def = classes.get(class_name)
    if class_def is None:
        return False

    _, bases = class_def
    for candidate in bases:
        if candidate == "unittest.TestCase":
            return True
        if candidate in classes and is_testcase_class(candidate, classes, seen):
            return True
        short_name = candidate.rsplit(".", 1)[-1]
        if short_name == "TestCase":
            return True
        if short_name in classes and is_testcase_class(short_name, classes, seen):
            return True
    return False


target_path = pathlib.Path(sys.argv[1])
support_path = pathlib.Path(sys.argv[2])
target_test = sys.argv[3]

classes = class_index(target_path)
classes.update(class_index(support_path))

for class_name, (methods, _) in class_index(target_path).items():
    if target_test in methods and is_testcase_class(class_name, classes):
        raise SystemExit(0)

raise SystemExit(1)
PY
  then
    echo "Missing required Phase 14 unittest-discoverable test in ${file_path}: ${test_name}" >&2
    exit 1
  fi
}

require_file "${validation_doc}" "Missing Phase 14 identity-rich source expansion CI validation record"
require_file "${design_doc}" "Missing Phase 14 identity-rich source family design document"
require_file "${github_onboarding_doc}" "Missing GitHub audit onboarding package"
require_file "${github_runbook_doc}" "Missing GitHub audit triage runbook"
require_file "${microsoft_onboarding_doc}" "Missing Microsoft 365 audit onboarding package"
require_file "${microsoft_runbook_doc}" "Missing Microsoft 365 audit triage runbook"
require_file "${entra_onboarding_doc}" "Missing Entra ID onboarding package"
require_file "${entra_runbook_doc}" "Missing Entra ID triage runbook"
require_file "${profile_tests}" "Missing Phase 14 source profile docs tests"
require_file "${wazuh_tests}" "Missing Wazuh adapter tests"
require_file "${service_tests}" "Missing control-plane service persistence tests"
require_file "${cli_tests}" "Missing control-plane CLI inspection tests"
require_file "${workflow_path}" "Missing CI workflow"
require_fixed_string "${workflow_path}" "      - name: Run Phase 14 identity-rich source family validation"
require_fixed_string "${workflow_path}" "      - name: Run Phase 14 identity-rich source expansion validation"
require_fixed_string "${workflow_path}" "      - name: Run Phase 14 workflow coverage guard"

validation_required_phrases=(
  "# Phase 14 Identity-Rich Source Expansion CI Validation"
  "- Validation date: 2026-04-09"
  "- Validation scope: Phase 14 review of the approved identity-rich source families, their reviewed source-profile assumptions, signal-quality and false-positive review coverage, ownership metadata, source-prerequisite checks, and CI wiring for the reviewed Phase 14 expansion path"
  "- Baseline references: \`docs/phase-14-identity-rich-source-family-design.md\`, \`docs/source-families/github-audit/onboarding-package.md\`, \`docs/source-families/github-audit/analyst-triage-runbook.md\`, \`docs/source-families/microsoft-365-audit/onboarding-package.md\`, \`docs/source-families/microsoft-365-audit/analyst-triage-runbook.md\`, \`docs/source-families/entra-id/onboarding-package.md\`, \`docs/source-families/entra-id/analyst-triage-runbook.md\`, \`control-plane/tests/test_phase14_identity_rich_source_profile_docs.py\`, \`control-plane/tests/test_wazuh_adapter.py\`, \`control-plane/tests/test_service_persistence_ingest_case_lifecycle.py\`, \`control-plane/tests/test_cli_inspection.py\`, \`.github/workflows/ci.yml\`"
  "- Verification commands: \`bash scripts/verify-phase-14-identity-rich-source-family-design.sh\`, \`python3 -m unittest control-plane.tests.test_phase14_identity_rich_source_profile_docs control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_cli_inspection\`, \`bash scripts/test-verify-ci-phase-14-workflow-coverage.sh\`, \`bash scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh\`"
  "- Validation status: PASS"
  "## Required Boundary Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the reviewed source-profile boundaries keep GitHub audit, Microsoft 365 audit, and Entra ID constrained to admitted family semantics rather than vendor-local actioning or generic network-wide coverage."
  "Confirmed the reviewed triage runbooks keep false-positive expectations, read-oriented evidence, and business-hours handling explicit for the approved families."
  "Confirmed the onboarding packages keep parser ownership and replay-fixture expectations explicit so source-prerequisite drift fails closed."
  "Confirmed the control-plane runtime and CLI tests continue to surface reviewed source profiles in alerts and cases rather than collapsing identity-rich families into undifferentiated Wazuh intake."
  "Confirmed CI now runs a dedicated Phase 14 validation step and workflow coverage guard so the reviewed Phase 14 path stays bounded to the approved families."
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/source-families/github-audit/onboarding-package.md"
  "docs/source-families/github-audit/analyst-triage-runbook.md"
  "docs/source-families/microsoft-365-audit/onboarding-package.md"
  "docs/source-families/microsoft-365-audit/analyst-triage-runbook.md"
  "docs/source-families/entra-id/onboarding-package.md"
  "docs/source-families/entra-id/analyst-triage-runbook.md"
  "control-plane/tests/test_phase14_identity_rich_source_profile_docs.py"
  "control-plane/tests/test_wazuh_adapter.py"
  "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py"
  "control-plane/tests/test_cli_inspection.py"
  ".github/workflows/ci.yml"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 14 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 14 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${github_onboarding_doc}" "Parser ownership remains with IT Operations, Information Systems Department."
require_fixed_string "${github_onboarding_doc}" "The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved."
require_fixed_string "${github_onboarding_doc}" "This package does not approve live GitHub API actioning, response automation, source-side credentials, or non-audit GitHub telemetry families."
require_fixed_string "${github_runbook_doc}" "The runbook keeps GitHub audit handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit."

require_fixed_string "${microsoft_onboarding_doc}" "Parser ownership remains with IT Operations, Information Systems Department."
require_fixed_string "${microsoft_onboarding_doc}" "The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved."
require_fixed_string "${microsoft_onboarding_doc}" "This package does not approve direct Microsoft 365 actioning, non-audit Microsoft 365 telemetry families, source-side credentials, or runtime automation."
require_fixed_string "${microsoft_runbook_doc}" "The runbook keeps Microsoft 365 audit handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit."

require_fixed_string "${entra_onboarding_doc}" "Parser ownership remains with IT Operations, Information Systems Department."
require_fixed_string "${entra_onboarding_doc}" "The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved."
require_fixed_string "${entra_onboarding_doc}" "This package does not approve direct Entra ID actioning, non-audit Entra ID telemetry families, source-side credentials, or runtime automation."
require_fixed_string "${entra_runbook_doc}" "The runbook keeps Entra ID handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit."

require_test_name "${profile_tests}" "test_phase14_onboarding_packages_define_reviewed_ownership_and_prerequisites"
require_test_name "${profile_tests}" "test_phase14_family_triage_runbooks_define_the_reviewed_posture"
require_test_name "${wazuh_tests}" "test_adapter_builds_reviewed_source_profile_for_github_audit_fixture"
require_test_name "${wazuh_tests}" "test_adapter_builds_reviewed_source_profile_for_microsoft_365_audit_fixture"
require_test_name "${wazuh_tests}" "test_adapter_builds_reviewed_source_profile_for_entra_id_fixture"
require_test_name "${service_tests}" "test_service_admits_github_audit_fixture_through_wazuh_source_profile"
require_test_name "${service_tests}" "test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile"
require_test_name "${service_tests}" "test_service_admits_entra_id_fixture_through_wazuh_source_profile"
require_test_name "${service_tests}" "test_service_exposes_reviewed_context_in_analyst_queue_for_identity_rich_alerts"
require_test_name "${cli_tests}" "test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context"

echo "Phase 14 identity-rich source expansion CI validation remains reviewable and fail closed."
