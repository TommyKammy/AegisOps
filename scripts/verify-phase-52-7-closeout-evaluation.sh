#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-52-7-closeout-evaluation.md"
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
  echo "Missing Phase 52.7 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 52.7 closeout evaluation](docs/phase-52-7-closeout-evaluation.md)" "README Phase 52.7 closeout link"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 52.7 Closeout Evaluation
**Status**: Accepted as control-plane namespace normalization and root owner reduction; Phase 53 Wazuh product profile work can start after #1127 lands.
**Related Issues**: #1120, #1121, #1122, #1123, #1124, #1125, #1126, #1127
Namespace bridges, filesystem layout, compatibility aliases, root owner inventories, verifier output, issue-lint output, and this document do not change runtime workflow truth.
This closeout does not claim that Phase 53 Wazuh product profile work was completed, Shuffle product profile work was completed, AegisOps is GA, RC, Beta, or self-service commercially ready, or that runtime product behavior changed during Phase 52.7.
| #1120 | Epic: Phase 52.7 Control-Plane Namespace Normalization and Root Owner Reduction | Open until #1127 lands; accepted when this closeout, verifiers, and issue-lint pass. |
| #1121 | Phase 52.7.1 namespace and layout inventory contract | Closed.
| #1122 | Phase 52.7.2 canonical namespace bridge | Closed.
| #1123 | Phase 52.7.3 repo-owned canonical namespace rewiring | Closed.
| #1124 | Phase 52.7.4 physical layout migration | Closed.
| #1125 | Phase 52.7.5 root shim reduction | Closed.
| #1126 | Phase 52.7.6 namespace/path packaging guardrails | Closed.
| #1127 | Phase 52.7.7 Phase 52.7 closeout evaluation | Open until this closeout lands; accepted when this document, focused verifier, all Phase 52.7 verifiers, issue-lint, and path hygiene pass. |
| Phase 52.6 accepted baseline before Phase 52.7 physical layout migration, under `control-plane/aegisops_control_plane/` | 37 |
| Phase 52.7.5 accepted canonical root baseline after namespace normalization, under `control-plane/aegisops/control_plane/` | 12 |
| Phase 52.7.4 accepted legacy compatibility package baseline after migration, under `control-plane/aegisops_control_plane/` | 1 |
| Implementation package path | `control-plane/aegisops_control_plane/` | `control-plane/aegisops/control_plane/` |
| Compatibility package path | `control-plane/aegisops_control_plane/` contained implementation files | `control-plane/aegisops_control_plane/__init__.py` only |
| Canonical import namespace | Proposed by ADR-0016, not yet the repo-owned implementation target | `aegisops.control_plane` |
| Legacy import namespace | `aegisops_control_plane` public package and implementation namespace | `aegisops_control_plane` retained as compatibility namespace only |
Legacy compatibility behavior is preserved, not removed.
`import aegisops_control_plane` continues to work through the compatibility package
Retained root owners are exactly `__init__.py`, `cli.py`, `config.py`, `models.py`, `operator_inspection.py`, `persistence_lifecycle.py`, `publishable_paths.py`, `record_validation.py`, `reviewed_slice_policy.py`, `service.py`, `service_composition.py`, and `structured_events.py`.
`service.py` remains a retained compatibility blocker under ADR-0003, ADR-0010, ADR-0014, ADR-0018, and the Phase 52.7 guardrail baseline.
`docs/phase-52-7-closeout-evaluation.md`
`scripts/verify-phase-52-7-closeout-evaluation.sh`
`scripts/test-verify-phase-52-7-closeout-evaluation.sh`
`bash scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh`: namespace and layout inventory records current references, proposed canonical namespace, compatibility blockers, movement guard, and supervisor placeholders.
`bash scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh`: canonical namespace bridge preserves root public exports and module identity for approved bridge paths.
`bash scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh`: repo-owned references use `aegisops.control_plane` except approved compatibility surfaces.
`bash scripts/verify-phase-52-7-4-physical-layout-migration.sh`: implementation files live under `control-plane/aegisops/control_plane/` and legacy imports preserve module identity.
`bash scripts/verify-phase-52-7-5-root-shim-reduction.sh`: 25 simple canonical root shims were removed, 12 retained canonical root files remain, and canonical plus legacy alias identity is preserved.
`bash scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh`: canonical implementation path, legacy shim boundary, retained root set, compatibility imports, and publishable guidance are pinned.
`bash scripts/verify-publishable-path-hygiene.sh`: publishable tracked content does not contain workstation-local absolute paths.
`bash scripts/verify-phase-52-7-closeout-evaluation.sh`: this closeout records child outcomes, compatibility behavior before/after, root file-count before/after, namespace/path before/after, changed files, verifier evidence, issue-lint summary, retained limitations, and bounded Phase 53 recommendation.
`bash scripts/test-verify-phase-52-7-closeout-evaluation.sh`: closeout negative fixtures reject missing retained legacy compatibility, Phase 53 completion overclaims, missing root file-count before/after, missing namespace/path before/after, and workstation-local absolute paths.
`python3 -m unittest control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py`: canonical namespace bridge compatibility passed.
`python3 -m unittest control-plane/tests/test_phase52_7_4_physical_layout_migration.py`: physical layout migration compatibility passed.
`python3 -m unittest control-plane/tests/test_phase52_7_5_root_shim_reduction.py`: canonical root shim reduction compatibility passed.
`python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`: broad control-plane tests passed after the namespace/path and root-owner changes.
node <codex-supervisor-root>/dist/index.js issue-lint 1120 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1122 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1123 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1124 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1125 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1126 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1127 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
The public compatibility namespace `aegisops_control_plane` remains supported; removing it requires a later accepted ADR, caller evidence, operator migration plan, focused regression tests, rollback path, and authority-boundary impact.
The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.
Phase 52.7 does not implement Wazuh product profiles, Shuffle product profiles, public compatibility namespace removal, outer directory rename, product behavior changes, deployment behavior changes, authorization changes, provenance changes, snapshot semantics changes, backup/restore changes, export changes, readiness changes, assistant behavior changes, evidence behavior changes, action-execution behavior changes, HTTP behavior changes, CLI behavior changes, or durable-state changes.
Phase 53 can start after #1127 lands and all Phase 52.7 verifiers remain green.
The recommendation is bounded to Wazuh product profile materialization.
Do not treat this recommendation as a claim that the Wazuh product profile is complete, Shuffle product profile work is complete, or Phase 52.7 changed runtime product behavior.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 52.7 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 52.7 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 52.7 proves GA readiness" \
  "Phase 52.7 proves RC readiness" \
  "Phase 52.7 proves Beta readiness" \
  "Phase 52.7 proves self-service commercial readiness" \
  "Phase 53 Wazuh product profile work is completed" \
  "The Wazuh product profile is complete" \
  "The Shuffle product profile work is complete" \
  "Phase 52.7 proves runtime product behavior changed" \
  "aegisops_control_plane may be removed immediately" \
  "Compatibility aliases may be removed immediately" \
  "service.py can grow beyond the accepted facade ceiling" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 52.7 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 52.7 closeout evaluation records child outcomes, compatibility behavior before/after, root file-count before/after, namespace/path before/after, changed files, verifier evidence, issue-lint summary, retained limitations, and bounded Phase 53 recommendation."
