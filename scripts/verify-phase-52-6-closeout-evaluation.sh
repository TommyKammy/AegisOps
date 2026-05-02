#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-52-6-closeout-evaluation.md"
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
  echo "Missing Phase 52.6 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 52.6 closeout evaluation](docs/phase-52-6-closeout-evaluation.md)" "README Phase 52.6 closeout link"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 52.6 Closeout Evaluation
**Status**: Accepted as compatibility shim deprecation and root package reduction; Phase 53 Wazuh product profile work can start after #1112 lands.
**Related Issues**: #1105, #1106, #1107, #1108, #1109, #1110, #1111, #1112
Compatibility import aliases, root shim inventory, verifier output, issue-lint output, and this document do not change runtime workflow truth.
This closeout does not claim that Wazuh product profiles are complete, Shuffle product profiles are complete, AegisOps is GA, RC, Beta, or self-service commercially ready, or that runtime behavior changed during Phase 52.6.
| #1105 | Epic: Phase 52.6 Compatibility Shim Deprecation and Root Package Reduction | Open until #1112 lands; accepted when this closeout, verifiers, and issue-lint pass. |
| #1106 | Phase 52.6.1 root shim inventory and deprecation contract | Closed.
| #1107 | Phase 52.6.2 canonical domain import rewiring | Closed.
| #1108 | Phase 52.6.3 legacy import alias registry and compatibility tests | Closed.
| #1109 | Phase 52.6.4 remove simple physical root shims covered by alias registry | Closed.
| #1110 | Phase 52.6.5 retire Phase29 root filenames safely | Closed.
| #1111 | Phase 52.6.6 tighten root package guardrails and retained-root owner policy | Closed.
| #1112 | Phase 52.6.7 Phase 52.6 closeout evaluation | Open until this closeout lands; accepted when this document, focused verifier, all Phase 52.6 verifiers, issue-lint, and path hygiene pass. |
| Phase 52.5 baseline before Phase 52.6 deletions | 63 |
| Phase 52.6.5 and Phase 52.6.6 accepted baseline after approved shim and Phase29 filename deletion | 37 |
Phase 52.6.3 deleted `audit_export.py` as the proof-of-pattern physical root shim removal
Phase 52.6.4 deleted these 21 simple physical root shims
Phase 52.6.5 deleted these four Phase29 root filenames
`phase29_shadow_dataset.py`, `phase29_shadow_scoring.py`, `phase29_evidently_drift_visibility.py`, and `phase29_mlflow_shadow_model_registry.py`.
Retained root owners are exactly `__init__.py`, `config.py`, `models.py`, `operator_inspection.py`, `persistence_lifecycle.py`, `publishable_paths.py`, `record_validation.py`, `reviewed_slice_policy.py`, `service_composition.py`, and `structured_events.py`.
The retained compatibility blocker is `service.py`
Phase29 root filename status: no direct root Python filename begins with `phaseNN` or `phaseNN_` after Phase 52.6.6.
Compatibility import status: approved legacy import paths deleted from the physical root remain registered aliases to explicit owner modules.
`bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`: root shim inventory records the Phase 52.5 root file baseline, accepted deletion sets, retained blockers, and root count baseline.
`bash scripts/verify-phase-52-6-2-canonical-domain-imports.sh`: internal callers use canonical domain imports; approved legacy compatibility usage remains bounded.
`bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh`: approved aliases preserve module identity or compatibility behavior, target owner metadata, and retained blockers.
`python3 -m unittest control-plane/tests/test_phase52_6_4_root_shim_alias_removal.py`: deleted simple root shims are registry aliases and retained physical blockers remain present.
`bash scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh`: Phase29 root filenames are retired, `ml_shadow` remains the owner, and legacy import compatibility is explicitly registered.
`python3 -m unittest control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py`: Phase29 legacy imports resolve through registered aliases and preserve the required compatibility surface.
`bash scripts/verify-phase-52-6-6-root-package-guardrails.sh`: 37 root Python files remain, retained-owner set is pinned, phase-numbered root filenames are rejected, and `service.py` stays under retained compatibility-blocker policy.
`bash scripts/verify-publishable-path-hygiene.sh`: publishable tracked content does not contain workstation-local absolute paths.
`bash scripts/verify-phase-52-6-closeout-evaluation.sh`: this closeout records child outcomes, root file-count before/after, deleted shims, retained owners, retained blockers, Phase29 filename status, compatibility status, verifier evidence, issue-lint summary, accepted limitations, and bounded Phase 53 recommendation.
`bash scripts/test-verify-phase-52-6-closeout-evaluation.sh`: closeout negative fixtures reject Wazuh/Shuffle completion overclaims, missing retained compatibility blockers, missing Phase29 root filename status, and workstation-local absolute paths.
`python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`: 939 broad control-plane tests passed after the import-alias and root package guardrail changes.
node <codex-supervisor-root>/dist/index.js issue-lint 1105 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1106 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1107 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1108 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1109 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1110 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1111 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1112 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
The public package name remains `aegisops_control_plane`; a rename requires a later accepted ADR, caller evidence, operator migration plan, focused regression tests, and rollback path.
The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.
`service.py` remains a retained compatibility blocker under ADR-0003 and ADR-0010; Phase 52.6 does not complete all future facade decomposition.
Phase 53 can start after #1112 lands and all Phase 52.6 verifiers remain green. No additional shim cleanup is required before starting the bounded Wazuh product profile implementation.
The recommendation is bounded to Wazuh product profile materialization.
Do not treat this recommendation as a claim that the Wazuh product profile is complete, Shuffle product profile work is complete, or Phase 52.6 changed runtime product behavior.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 52.6 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 52.6 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 52.6 proves GA readiness" \
  "Phase 52.6 proves RC readiness" \
  "Phase 52.6 proves Beta readiness" \
  "Phase 52.6 proves self-service commercial readiness" \
  "The Wazuh product profile is complete" \
  "The Shuffle product profile work is complete" \
  "Phase 52.6 proves runtime product behavior changed" \
  "Compatibility shims may be removed immediately" \
  "service.py can grow beyond the accepted facade ceiling" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 52.6 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 52.6 closeout evaluation records child outcomes, root file-count before/after, deleted shims, retained owners, retained blockers, Phase29 status, compatibility status, verifier evidence, issue-lint summary, accepted limitations, and bounded Phase 53 recommendation."
