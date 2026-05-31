#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-63-closeout-evaluation.md"
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
  echo "Missing Phase 63.R closeout evaluation: ${doc_path}" >&2
  exit 1
fi

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
## Phase 63.R Maintainability Refactor Closeout Addendum
- **Status**: Accepted as behavior-preserving maintainability refactor closeout evidence; Phase 63 Evidence Expansion v1 authority and readiness boundaries are unchanged.
- **Related Issues**: #1348, #1349, #1350, #1351, #1352, #1353, #1354
Phase 63.R is accepted only as a maintainability refactor closeout that preserves Phase 63 evidence registry, evidence-pack projection, operator UI evidence-pack visibility, AI grounding, authority boundaries, and readiness limits.
This addendum does not claim new product behavior, evidence-source breadth, workflow authority, AI authority, UI authority, verifier authority, issue-lint authority, Phase 66 RC proof, Beta, RC, GA, or commercial replacement readiness.
| #1348 | Epic: Phase 63.R maintainability refactor | Closed by the ordered #1349 through #1354 evidence packet. |
| #1349 | 63.R.1 Extract evidence pack inspection projection helper | Closed. Extracted `evidence_pack_projection.py` from `operator_inspection.py` while preserving case-detail evidence-pack projection behavior and subordinate evidence posture. |
| #1350 | 63.R.2 Extract linked evidence pack validator | Closed. Extracted `linkedEvidencePackValidator.ts` and focused extraction tests while preserving backend-authoritative detail-reader validation and fail-closed UI data boundaries. |
| #1351 | 63.R.3 Split case evidence pack review section | Closed. Extracted `caseDetailEvidencePackSection.tsx` while preserving rendered case-detail evidence-pack review behavior, route behavior, and subordinate UI posture. |
| #1352 | 63.R.4 Decompose AI grounding adapter seams | Closed. Extracted AI grounding payload, prompt-validation, and validation helpers while preserving cited advisory grounding and no-authority behavior. |
| #1353 | 63.R.5 Split evidence source registry catalogs | Closed. Extracted evidence source registry data and validation catalog helpers while preserving the bounded Phase 63 source registry and no-source-native-authority posture. |
| #1354 | 63.R.6 Phase 63.R maintainability refactor closeout | Closed when this addendum, focused closeout verifier, hotspot verifier, path hygiene, focused backend/UI/AI tests, registry verifier, and issue-lint evidence pass. |
`control-plane/aegisops/control_plane/inspection/evidence_pack_projection.py`
`control-plane/aegisops/control_plane/operator_inspection.py`
`apps/operator-ui/src/operatorDataProvider/linkedEvidencePackValidator.ts`
`apps/operator-ui/src/operatorDataProvider/detailReaders.ts`
`apps/operator-ui/src/operatorDataProvider/detailReaders.evidence-pack-extraction.test.ts`
`apps/operator-ui/src/app/operatorConsolePages/caseDetailEvidencePackSection.tsx`
`apps/operator-ui/src/app/operatorConsolePages/caseDetailSurfaces.tsx`
`apps/operator-ui/src/app/OperatorRoutes.casework.evidence-pack.test.tsx`
`control-plane/aegisops/control_plane/assistant/ai_grounding_payload.py`
`control-plane/aegisops/control_plane/assistant/ai_grounding_prompt_validation.py`
`control-plane/aegisops/control_plane/assistant/ai_grounding_validation.py`
`control-plane/aegisops/control_plane/assistant/ai_grounding_adapter.py`
`control-plane/aegisops/control_plane/evidence/evidence_source_registry_data.py`
`control-plane/aegisops/control_plane/evidence/evidence_source_validation_catalog.py`
`control-plane/aegisops/control_plane/evidence/evidence_source_registry.py`
| Evidence-pack inspection projection | `operator_inspection.py` | Projection assembly lived in the operator inspection module. | Projection assembly lives in `evidence_pack_projection.py`; `operator_inspection.py` delegates while preserving case-detail output semantics. |
| Linked evidence-pack validation | `detailReaders.ts` | Detail-reader validation and linked evidence-pack rules lived together. | Evidence-pack validation lives in `linkedEvidencePackValidator.ts`; `detailReaders.ts` remains the backend-detail reader boundary. |
| Case evidence-pack UI section | `caseDetailSurfaces.tsx` | Evidence-pack review rendering lived inside the broader case detail surface. | Evidence-pack review rendering lives in `caseDetailEvidencePackSection.tsx`; the case detail surface composes it without changing route behavior. |
| AI grounding adapter validation | `ai_grounding_adapter.py` | Payload shaping, prompt validation, and authority checks lived in one adapter module. | Payload, prompt-validation, and grounding-validation helpers are split while preserving cited advisory and no-authority checks. |
| Evidence source registry catalogs | `evidence_source_registry.py` | Registry data and validation catalog rules lived with registry entrypoints. | Registry data and validation catalog helpers are split while preserving the bounded `osquery_host_state` and `malwarebazaar_hash_reputation` registry. |
`python3 -m unittest control-plane.tests.test_phase63_5_evidence_freshness_provenance_projection`
`python3 -m unittest control-plane.tests.test_phase63_7_ai_grounding_adapter`
`python3 -m unittest control-plane.tests.test_phase63_evidence_source_registry`
`npm run test --workspace @aegisops/operator-ui -- detailReaders.evidence-pack-extraction.test.ts OperatorRoutes.casework.evidence-pack.test.tsx`
`npm run typecheck --workspace @aegisops/operator-ui`
`bash scripts/verify-phase-63-1-evidence-source-registry-v1.sh`
`bash scripts/verify-maintainability-hotspots.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-63-r-closeout-evaluation.sh`
`bash scripts/test-verify-phase-63-r-closeout-evaluation.sh`
`node <codex-supervisor-root>/dist/index.js issue-lint 1348 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1349 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1350 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1351 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1352 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1353 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1354 --config <supervisor-config-path>`
Each Phase 63.R issue-lint command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none`.
The maintainability hotspot verifier remains unchanged and continues to report only the reviewed `service.py` baseline rather than hiding a new Phase 63.R hotspot.
Phase 63.R does not add product behavior, evidence-source breadth, new evidence collection, case truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, readiness truth, AI authority, UI authority, browser authority, source-native authority, verifier authority, issue-lint authority, Controlled Write, or Hard Write.
Phase 63.R does not claim Phase 66 RC proof, Phase 67 GA proof, Beta readiness, RC readiness, GA readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 64, Phase 65, and Phase 66 may consume the split modules, focused extraction tests, registry verifier evidence, unchanged maintainability guard, and explicit non-expansion posture as reviewed maintainability evidence only.
Future phases must still prove limitation ownership, upgrade work, RC evidence, support-bundle evidence, rollout operational hygiene, backup/restore evidence, SIEM/SOAR breadth, and real gate acceptance outside Phase 63.R.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${phrase}" "Phase 63.R closeout evidence"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}"; then
  echo "Forbidden Phase 63.R closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 63.R adds product behavior" \
  "Phase 63.R expands evidence-source breadth" \
  "Phase 63.R changes workflow authority" \
  "Phase 63.R changes AI authority" \
  "Phase 63.R changes UI authority" \
  "Phase 63.R proves Beta readiness" \
  "Phase 63.R proves RC readiness" \
  "Phase 63.R proves GA readiness" \
  "Phase 63.R proves commercial replacement readiness" \
  "Phase 63.R implements Controlled Write" \
  "Phase 63.R implements Hard Write" \
  "Verifier output is Phase 63.R release truth" \
  "Issue-lint output is Phase 63.R release truth" \
  "Maintainability baseline was raised to hide a new Phase 63.R hotspot"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 63.R closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 63.R closeout evaluation records refactor child outcomes, behavior preservation, verifier evidence, authority limits, and handoff boundaries."
