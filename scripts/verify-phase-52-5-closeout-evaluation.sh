#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-52-5-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${file}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 52.5 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 52.5 closeout evaluation](docs/phase-52-5-closeout-evaluation.md)" "README Phase 52.5 closeout link"

required_phrases=(
  "# Phase 52.5 Closeout Evaluation"
  "**Status**: Accepted as control-plane package layout hardening; Phase 53 Wazuh product profile work can start after this closeout lands."
  "**Related Issues**: #1084, #1085, #1086, #1087, #1088, #1089, #1090, #1091, #1092, #1093, #1094"
  "Package layout, compatibility shims, import verifiers, layout guardrails, issue-lint output, and this document do not change runtime workflow truth."
  "This closeout does not claim that Wazuh product profiles are complete, Shuffle product profiles are complete, AegisOps is GA, RC, Beta, or self-service commercially ready, or that runtime behavior changed during Phase 52.5."
  '| #1084 | Epic: Phase 52.5 Control-Plane Package Layout Hardening | Open until #1094 lands; accepted when this closeout, verifiers, and issue-lint pass. |'
  '| #1085 | Phase 52.5.1 control-plane layout inventory and migration contract | Closed.'
  '| #1086 | Phase 52.5.2 package scaffolding and compatibility-shim policy | Closed.'
  '| #1087 | Phase 52.5.3 assistant and reporting package moves | Closed.'
  '| #1088 | Phase 52.5.4 action-review package moves | Closed.'
  '| #1089 | Phase 52.5.5 execution and action lifecycle package moves | Closed.'
  '| #1090 | Phase 52.5.6 runtime, readiness, restore, and API package moves | Closed.'
  '| #1091 | Phase 52.5.7 ingestion and external-evidence package moves | Closed.'
  '| #1092 | Phase 52.5.8 Phase 29 shadow-ML module rename | Closed.'
  '| #1093 | Phase 52.5.9 service facade freeze and internal import cleanup | Closed.'
  '| #1094 | Phase 52.5.10 closeout evaluation | Open until this closeout lands; accepted when this document and focused verifier pass. |'
  'Each moved implementation keeps a root compatibility shim unless a later accepted transition policy proves caller coverage and approves removal.'
  '| `aegisops_control_plane.ai_trace_lifecycle` | `aegisops_control_plane.assistant.ai_trace_lifecycle` |'
  '| `aegisops_control_plane.action_review_write_surface` | `aegisops_control_plane.actions.review.action_review_write_surface` |'
  '| `aegisops_control_plane.execution_coordinator_reconciliation` | `aegisops_control_plane.actions.execution_coordinator_reconciliation` |'
  '| `aegisops_control_plane.http_runtime_surface` | `aegisops_control_plane.api.http_runtime_surface` |'
  '| `aegisops_control_plane.external_evidence_endpoint` | `aegisops_control_plane.evidence.external_evidence_endpoint` |'
  '| `aegisops_control_plane.phase29_mlflow_shadow_model_registry` | `aegisops_control_plane.ml_shadow.mlflow_registry` |'
  '`bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`: classified 135 current Python files across 11 target package families.'
  '`bash scripts/verify-phase-52-5-2-import-compatibility.sh`: stable legacy imports and target imports are preserved for moved modules and the service/model baseline.'
  '`bash scripts/verify-phase-52-5-2-layout-guardrail.sh`: current classified baseline passes and new unclassified or phase-numbered production modules are rejected.'
  '`bash scripts/verify-phase-52-5-9-service-facade-freeze.sh`: `service.py` remains at 1393 lines, 1241 effective lines, and 95 `AegisOpsControlPlaneService` methods; domain package internals avoid legacy compatibility shims.'
  '`bash scripts/verify-publishable-path-hygiene.sh`: publishable tracked content does not contain workstation-local absolute paths.'
  '`bash scripts/verify-phase-52-5-closeout-evaluation.sh`: this closeout records child outcomes, moved modules, compatibility shim status, accepted limitations, verifier evidence, issue-lint summary, and bounded Phase 53 recommendation.'
  '`python3 -m unittest discover -s control-plane/tests -p '"'"'test_*.py'"'"'`: 934 broad control-plane tests passed.'
  "node <codex-supervisor-root>/dist/index.js issue-lint 1084 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1085 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1086 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1087 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1088 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1089 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1090 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1091 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1092 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1093 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1094 --config <supervisor-config-path>"
  "execution_ready=yes"
  "missing_required=none"
  "missing_recommended=none"
  "metadata_errors=none"
  "high_risk_blocking_ambiguity=none"
  'The public package name remains `aegisops_control_plane`; a rename requires a later accepted ADR, caller evidence, operator migration plan, focused regression tests, and rollback path.'
  'The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.'
  'Root compatibility shims remain until a later transition policy documents affected import paths, replacement imports, caller evidence, deprecation window, focused regression tests, and rollback path.'
  'Phase-numbered production filenames are rejected for new owner implementations by the layout guardrail, but existing Phase 29 root import paths remain as compatibility shims for ML shadow callers.'
  '`service.py` remains an ADR-governed facade hotspot at the accepted Phase 50.13.5 ceiling; Phase 52.5 freezes growth but does not complete all future facade decomposition.'
  "Phase 53 can start after #1094 lands and the closeout verifier remains green."
  "The recommendation is bounded to Wazuh product profile materialization."
  "Do not treat this recommendation as a claim that the Wazuh product profile is complete, Shuffle product profile work is complete, or Phase 52.5 changed runtime product behavior."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 52.5 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 52.5 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 52.5 proves GA readiness" \
  "Phase 52.5 proves RC readiness" \
  "Phase 52.5 proves Beta readiness" \
  "Phase 52.5 proves self-service commercial readiness" \
  "The Wazuh product profile is complete" \
  "The Shuffle product profile work is complete" \
  "Phase 52.5 proves runtime product behavior changed" \
  "Compatibility shims may be removed immediately" \
  "service.py can grow beyond the accepted facade ceiling" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 52.5 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 52.5 closeout evaluation records child outcomes, moved modules, compatibility shim status, accepted limitations, verifier evidence, issue-lint summary, and bounded Phase 53 recommendation."
