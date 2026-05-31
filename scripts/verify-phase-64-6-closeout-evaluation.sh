#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-64-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
phase51_gate_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
phase51_negative_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
phase63_closeout_path="${repo_root}/docs/phase-63-closeout-evaluation.md"
phase64_contract_path="${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
phase64_records_path="${repo_root}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
phase64_handoff_path="${repo_root}/docs/phase-64-5-phase66-limitation-handoff.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_markdown_text() {
  local file="$1"

  perl -0pe 's/<!--.*?-->//gs' "${file}"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_markdown_text "${file}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_section_phrase() {
  local section="$1"
  local phrase="$2"
  local description="$3"
  local visible_section

  visible_section="$(perl -0pe 's/<!--.*?-->//gs' <<<"${section}")"

  if ! grep -Fq -- "${phrase}" <<<"${visible_section}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

section_text() {
  local file="$1"
  local heading="$2"
  local next_heading="$3"

  awk -v heading="${heading}" -v next_heading="${next_heading}" '
    {
      line = $0
      sub(/^[[:space:]]+/, "", line)
    }
    line == heading { in_section = 1 }
    in_section {
      if (next_heading != "" && (line == next_heading || index(line, next_heading) == 1)) {
        exit
      }
      print
    }
  ' "${file}"
}

require_file "${absolute_doc_path}" "Phase 64 closeout evaluation"
require_file "${readme_path}" "README for Phase 64 closeout link check"
require_file "${phase51_gate_path}" "Phase 51.3 gate contract"
require_file "${phase51_negative_path}" "Phase 51.6 authority-boundary negative test policy"
require_file "${phase63_closeout_path}" "Phase 63 closeout evaluation"
require_file "${phase64_contract_path}" "Phase 64.1 known limitation ownership contract"
require_file "${phase64_records_path}" "Phase 64.1 reviewed limitation ownership records"
require_file "${phase64_handoff_path}" "Phase 64.5 Phase 66 limitation handoff"

require_phrase "${readme_path}" "- [Phase 64.6 closeout evaluation](docs/phase-64-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 64.6 closeout evaluation is defined by the [Phase 64.6 closeout evaluation](docs/phase-64-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 64 Closeout Evaluation
**Status**: Accepted as Limitation Ownership evidence before Phase 66 RC proof, Beta, RC, GA, and commercial replacement-readiness claims.
**Related Issues**: #1365, #1366, #1367, #1368, #1369, #1370, #1371
Phase 64 Limitation Ownership is accepted for known limitation ownership records, validation and projection boundaries, operator limitation ownership surfaces, limitation-aware advisory and readiness context, Phase 66 limitation handoff evidence, and closeout evidence.
AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.
Limitation ownership documents, operator UI surfaces, advisory summaries, readiness projections, Phase 66 handoff notes, verifier output, and issue-lint output remain subordinate review and planning evidence only. They cannot approve, execute, reconcile, close, gate, resolve limitations, satisfy support evidence, or claim readiness by themselves.
Phase 64 must reject missing child outcomes, missing verifier evidence, missing issue-lint evidence, missing Phase 66 handoff, workstation-local paths, production secrets, RC/GA readiness claims, commercial replacement readiness claims, limitation-resolution claims, support-bundle completion claims, verifier truth, issue-lint truth, UI truth, and AI truth.
This closeout does not claim Phase 64 resolves known limitations, completes support-bundle evidence, proves Beta readiness, proves RC readiness, proves GA readiness, proves self-service commercial readiness, proves commercial replacement readiness, or satisfies Phase 66 RC gates.
Focused Phase 64 and closeout verifiers that must pass:
Issue-lint evidence:
Each command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none` before Phase 64 is considered fully closed.
Issue-lint output is planning and metadata evidence only. It does not become release truth, closeout truth, workflow truth, limitation truth, gate truth, or readiness truth.
Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output.
Phase 66 can consume Phase 64 as one RC evidence input for known limitation ownership.
Phase 66 must treat `docs/phase-64-1-reviewed-limitation-ownership-records.md` and `docs/phase-64-5-phase66-limitation-handoff.md` as subordinate limitation ownership evidence only.
Phase 64 closeout is release and planning evidence only.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 64 closeout term in ${doc_path}"
done

child_issue_outcomes="$(section_text "${absolute_doc_path}" "## Child Issue Outcomes" "## Changed Files")"
required_child_rows=(
  "| #1365 | Epic: Phase 64 Limitation Ownership | Open until #1371 lands; accepted when this closeout, focused verifiers, focused backend/UI/advisory/readiness tests, authority-boundary checks, maintainability check, publishable path hygiene, and issue-lint pass. |"
  "| #1366 | Phase 64.1 known limitation ownership record contract | Closed. \`docs/phase-64-1-known-limitation-ownership-record-contract.md\`, validation notes, PostgreSQL schema, record-family registration, lifecycle history, and focused tests prove reviewed \`known_limitation_ownership\` records without limitation resolution, release truth, gate truth, verifier truth, or issue-lint truth. |"
  "| #1367 | Phase 64.2 limitation ownership validation projection | Closed. \`control-plane/aegisops/control_plane/inspection/limitation_ownership_projection.py\`, validator tightening, and focused backend tests prove current-review and projection boundaries for limitation ownership records while rejecting stale, malformed, missing, and authority-bearing context. |"
  "| #1368 | Phase 64.3 operator limitation ownership surface | Closed. \`apps/operator-ui/src/app/operatorConsolePages/limitationOwnershipPages.tsx\`, route wiring, data-provider readers, list validators, and focused UI/data-provider tests prove operator visibility from backend-bound limitation records without browser, cache, UI, or workflow truth. |"
  "| #1369 | Phase 64.4 limitation-aware advisory and readiness context | Closed. \`control-plane/aegisops/control_plane/assistant/cited_recommendation_draft.py\`, \`control-plane/aegisops/control_plane/runtime/restore_readiness_projection.py\`, and focused advisory/readiness tests prove limitation context can appear as directly linked subordinate advisory and readiness input without AI truth, readiness truth, or gate acceptance. |"
  "| #1370 | Phase 64.5 Phase 66 limitation handoff | Closed. \`docs/phase-64-5-phase66-limitation-handoff.md\`, reviewed limitation records, focused handoff verifier, and verifier self-test prove Phase 66 can consume limitation ownership records only as subordinate RC proof planning evidence. |"
  "| #1371 | Phase 64.6 Phase 64 closeout evaluation | Open until this document and focused closeout verifier land. |"
)

for row in "${required_child_rows[@]}"; do
  require_section_phrase "${child_issue_outcomes}" "${row}" "Phase 64 child issue outcome row in Child Issue Outcomes table"
done

verifier_evidence="$(section_text "${absolute_doc_path}" "## Verifier Evidence" "## Issue-Lint Summary")"
required_verifier_lines=(
  "- \`bash scripts/verify-phase-64-1-known-limitation-ownership-record-contract.sh\`"
  "- \`bash scripts/verify-phase-64-5-phase66-limitation-handoff.sh\`"
  "- \`bash scripts/test-verify-phase-64-5-phase66-limitation-handoff.sh\`"
  "- \`bash scripts/verify-phase-64-6-closeout-evaluation.sh\`"
  "- \`bash scripts/test-verify-phase-64-6-closeout-evaluation.sh\`"
  "- \`bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh\`"
  "- \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`"
  "- \`bash scripts/verify-maintainability-hotspots.sh\`"
  "- \`bash scripts/verify-publishable-path-hygiene.sh\`"
  "- \`python3 -m unittest control-plane.tests.test_phase64_known_limitation_ownership_contract\`"
  "- \`python3 -m unittest control-plane.tests.test_phase64_limitation_ownership_control_plane\`"
  "- \`python3 -m unittest control-plane.tests.test_phase60_6_cited_recommendation_draft_agent\`"
  "- \`python3 -m unittest control-plane.tests.test_service_readiness_projection\`"
  "- \`npm run test --workspace @aegisops/operator-ui -- OperatorRoutes.test.tsx\`"
  "- \`npm run test --workspace @aegisops/operator-ui -- dataProvider.test.ts\`"
  "- \`npm run typecheck --workspace @aegisops/operator-ui\`"
)

for line in "${required_verifier_lines[@]}"; do
  require_section_phrase "${verifier_evidence}" "${line}" "Phase 64 verifier evidence line in Verifier Evidence section"
done

issue_lint_evidence="$(section_text "${absolute_doc_path}" "Issue-lint evidence:" "Each command should report")"
for issue_number in 1365 1366 1367 1368 1369 1370 1371; do
  issue_lint_line="- \`node <codex-supervisor-root>/dist/index.js issue-lint ${issue_number} --config <supervisor-config-path>\`"
  require_section_phrase "${issue_lint_evidence}" "${issue_lint_line}" "Phase 64 issue-lint evidence line in Issue-lint evidence section"
done

accepted_limitations="$(section_text "${absolute_doc_path}" "## Accepted Limitations" "## Phase 66 Handoff")"
require_section_phrase "${accepted_limitations}" "Phase 64 does not resolve limitations, close known limitation records, satisfy support-bundle evidence, accept release gates, approve RC gates, execute gate acceptance, prove Phase 66 RC readiness, prove Phase 67 GA readiness, or replace the Phase 51.3 gate contract." "Phase 64 accepted limitations boundary"
require_section_phrase "${accepted_limitations}" "Phase 64 limitation ownership records, validation projections, operator UI surfaces, advisory context, readiness context, handoff notes, verifier output, and issue-lint output are context only; they do not replace authoritative AegisOps alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, or closeout records." "Phase 64 subordinate limitation context boundary"

phase66_handoff="$(section_text "${absolute_doc_path}" "## Phase 66 Handoff" "")"
require_section_phrase "${phase66_handoff}" "Phase 66 can consume Phase 64 as one RC evidence input for known limitation ownership." "Phase 66 handoff consumption note"
require_section_phrase "${phase66_handoff}" "Phase 66 must treat \`docs/phase-64-1-reviewed-limitation-ownership-records.md\` and \`docs/phase-64-5-phase66-limitation-handoff.md\` as subordinate limitation ownership evidence only." "Phase 66 subordinate handoff boundary"

forbidden_claims=(
  "phase 64 resolves known limitations"
  "known limitations are resolved"
  "support-bundle evidence is complete"
  "support bundle evidence is complete"
  "phase 64 proves beta readiness"
  "phase 64 proves rc readiness"
  "phase 64 proves ga readiness"
  "phase 64 proves commercial replacement readiness"
  "phase 64 satisfies phase 66 rc gates"
  "phase 66 rc gates are satisfied"
  "aegisops is beta"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "limitation ownership records are release truth"
  "limitation ownership records are gate truth"
  "limitation ownership records are readiness truth"
  "limitation ownership records resolve limitations"
  "operator ui is limitation truth"
  "ui display is limitation truth"
  "ai summary is limitation truth"
  "readiness projection is gate truth"
  "verifier output is release truth"
  "verifier output is readiness truth"
  "issue-lint output is release truth"
  "issue-lint output is readiness truth"
)

allowed_non_claim_line="This closeout does not claim Phase 64 resolves known limitations, completes support-bundle evidence, proves Beta readiness, proves RC readiness, proves GA readiness, proves self-service commercial readiness, proves commercial replacement readiness, or satisfies Phase 66 RC gates."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"
required_issue_lint_boundary_line="Issue-lint output is planning and metadata evidence only. It does not become release truth, closeout truth, workflow truth, limitation truth, gate truth, or readiness truth."
required_issue_lint_boundary_line_lower="$(printf '%s' "${required_issue_lint_boundary_line}" | tr '[:upper:]' '[:lower:]')"

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" == "${allowed_non_claim_line_lower}" || "${line_lower}" == "${required_issue_lint_boundary_line_lower}" ]]; then
    continue
  fi
  for claim in "${forbidden_claims[@]}"; do
    if [[ "${line_lower}" == *"${claim}"* ]]; then
      echo "Forbidden Phase 64 closeout evaluation claim: ${claim}" >&2
      exit 1
    fi
  done
done < "${absolute_doc_path}"

if grep -Eiq -- '(AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|password[[:space:]]*=[[:space:]]*[^<[:space:]]+|secret[[:space:]]*=[[:space:]]*[^<[:space:]]+)' "${absolute_doc_path}"; then
  echo "Forbidden Phase 64 closeout evaluation: production secret-looking value detected" >&2
  exit 1
fi

path_hygiene_stderr="${repo_root}/.tmp-phase64-6-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 64 closeout evaluation absolute path usage detected" >&2
  exit 1
fi

echo "Phase 64.6 closeout evaluation contract and focused negative checks pass."
