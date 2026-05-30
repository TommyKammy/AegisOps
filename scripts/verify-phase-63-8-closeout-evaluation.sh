#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-63-closeout-evaluation.md"
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

section_text() {
  local file="$1"
  local heading="$2"
  local next_heading="$3"

  awk -v heading="${heading}" -v next_heading="${next_heading}" '
    $0 == heading { in_section = 1 }
    in_section {
      if (next_heading != "" && $0 == next_heading) {
        exit
      }
      print
    }
  ' "${file}"
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 63 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 63 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 63.8 closeout evaluation](docs/phase-63-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 63.8 closeout evaluation is defined by the [Phase 63.8 closeout evaluation](docs/phase-63-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=(
  "# Phase 63 Closeout Evaluation"
  "**Status**: Accepted as Evidence Expansion v1 before Phase 66 RC proof, Beta, RC, GA, and commercial replacement-readiness claims."
  "**Related Issues**: #1331, #1332, #1333, #1334, #1335, #1336, #1337, #1338, #1339"
  "Phase 63 is accepted as the Evidence Expansion v1 slice for bounded evidence source registration, reviewed evidence request records, osquery evidence packs, bounded enrichment evidence packs, freshness and provenance projection, evidence-pack UI visibility, AI grounding, and closeout evidence."
  "AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  "Evidence packs, osquery output, enrichment output, source-native state, freshness and confidence projections, operator UI state, browser state, AI output, verifier output, and issue-lint output remain subordinate context and cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, or claim readiness by themselves."
  "Phase 63 must reject missing child evidence, missing verifier output, missing issue-lint summary, missing authority-boundary statement, missing accepted limitations, missing Phase 66 handoff, workstation-local paths, production secrets, RC/GA readiness claims, endpoint remediation claims, broad evidence-source breadth claims, autonomous AI authority claims, source-native truth claims, and treating verifier or issue-lint output as release truth."
  "This closeout does not claim Phase 64 limitation ownership is complete, Phase 65 upgrade work is complete, Phase 66 RC proof is complete, Phase 67 GA proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."
  "Focused Phase 63 and closeout verifiers that must pass:"
  "Issue-lint evidence:"
  'Each command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none` before Phase 63 is considered fully closed.'
  "Issue-lint output is planning and metadata evidence only. It does not become release truth, closeout truth, workflow truth, evidence truth, or readiness truth."
  "Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."
  "Phase 66 can consume Phase 63 as one RC evidence input for Evidence Expansion v1."
  "Phase 63 closeout is release and planning evidence only."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 63 closeout term in ${doc_path}"
done

child_issue_outcomes="$(section_text "${absolute_doc_path}" "## Child Issue Outcomes" "## Changed Files")"
required_child_rows=(
  "| #1331 | Epic: Phase 63 Evidence Expansion v1 | Open until #1339 lands; accepted when this closeout, focused verifiers, backend/UI tests, authority-boundary checks, publishable path hygiene, and issue-lint pass. |"
  "| #1332 | Phase 63.1 evidence source registry v1 | Closed. \`docs/phase-63-1-evidence-source-registry-v1.md\`, validation notes, registry code, and focused tests prove the bounded \`osquery_host_state\` plus \`malwarebazaar_hash_reputation\` registry without broad source marketplace expansion or source-native authority. |"
  "| #1333 | Phase 63.2 reviewed evidence request records | Closed. \`docs/phase-63-2-reviewed-evidence-request-records.md\`, validation notes, request record code, and focused tests prove requester, target, source, expiry, custody, authorization, linked-case, duplicate, and durable binding checks before evidence output can be used. |"
  "| #1334 | Phase 63.3 osquery evidence adapter MVP | Closed. \`docs/phase-63-3-osquery-evidence-adapter.md\`, validation notes, adapter code, and focused tests prove reviewed osquery host-state evidence packs with query, collection timestamp, target host, custody, stale, unavailable, malformed, and no-remediation guardrails. |"
  "| #1335 | Phase 63.4 bounded enrichment adapter MVP | Closed. \`docs/phase-63-4-bounded-enrichment-adapter.md\`, validation notes, adapter code, and focused tests prove reviewed MalwareBazaar hash reputation evidence packs with hash, request, timestamp, digest, provenance, confidence, stale, conflict, unavailable, and no-authority guardrails. |"
  "| #1336 | Phase 63.5 evidence freshness and provenance projection | Closed. \`docs/phase-63-5-evidence-freshness-provenance-projection.md\`, validation notes, projection code, and focused tests prove freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, uncertainty, and projection-time revalidation for case workbench and AI-grounding consumers. |"
  "| #1337 | Phase 63.6 evidence-pack UI | Closed. \`apps/operator-ui/src/app/OperatorRoutes.casework.evidence-pack.test.tsx\`, \`apps/operator-ui/src/app/operatorConsolePages/caseDetailSurfaces.tsx\`, and \`apps/operator-ui/src/operatorDataProvider/detailReaders.ts\` prove linked evidence packs render only from verified backend case detail as subordinate context and fail closed on cache, browser, authority, readiness, source, custody, provenance, confidence, freshness, and field drift. |"
  "| #1338 | Phase 63.7 AI grounding adapter | Closed. \`docs/phase-63-7-ai-grounding-adapter.md\`, validation notes, adapter code, agent/tool registries, and focused tests prove cited advisory grounding from reviewed Phase 63 projections without autonomous AI authority, unsupported sources, untrusted payloads, prompt-pressure bypass, or authority-bearing metadata. |"
  "| #1339 | Phase 63.8 Phase 63 closeout evaluation | Open until this document and focused closeout verifier land. |"
)

for row in "${required_child_rows[@]}"; do
  if ! grep -Fq -- "${row}" <<<"${child_issue_outcomes}"; then
    echo "Missing Phase 63 child issue outcome row in Child Issue Outcomes table: ${row}" >&2
    exit 1
  fi
done

issue_lint_evidence="$(section_text "${absolute_doc_path}" "Issue-lint evidence:" "Each command should report")"
for issue_number in 1331 1332 1333 1334 1335 1336 1337 1338 1339; do
  issue_lint_line="- \`node <codex-supervisor-root>/dist/index.js issue-lint ${issue_number} --config <supervisor-config-path>\`"
  if ! grep -Fq -- "${issue_lint_line}" <<<"${issue_lint_evidence}"; then
    echo "Missing Phase 63 issue-lint evidence line in Issue-lint evidence section: ${issue_lint_line}" >&2
    exit 1
  fi
done

accepted_limitations="$(section_text "${absolute_doc_path}" "## Accepted Limitations" "## Phase 66 Handoff")"
if ! grep -Fq -- "Phase 63 does not implement Phase 64 limitation ownership, Phase 65 upgrade work, Phase 66 RC proof, Phase 67 GA proof, Beta readiness, RC readiness, GA readiness, self-service commercial readiness, or commercial replacement readiness." <<<"${accepted_limitations}"; then
  echo "Missing Phase 63 accepted limitations boundary" >&2
  exit 1
fi

forbidden_claims=(
  "phase 63 proves rc readiness"
  "phase 63 proves ga readiness"
  "phase 63 proves commercial replacement readiness"
  "phase 63 evidence expansion proves rc"
  "phase 66 rc proof is complete"
  "phase 67 ga proof is complete"
  "aegisops is beta"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "evidence packs are aegisops truth"
  "osquery output is aegisops truth"
  "enrichment output is aegisops truth"
  "source-native state is aegisops truth"
  "ai output is aegisops truth"
  "ui state approves evidence"
  "browser state closes cases"
  "verifier output is release truth"
  "issue-lint output is release truth"
  "endpoint remediation is implemented"
  "broad evidence-source marketplace is implemented"
  "autonomous ai authority is implemented"
  "controlled write is default enabled"
  "hard write is default enabled"
)

allowed_non_claim_line="This closeout does not claim Phase 64 limitation ownership is complete, Phase 65 upgrade work is complete, Phase 66 RC proof is complete, Phase 67 GA proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"
required_issue_lint_boundary_line="Issue-lint output is planning and metadata evidence only. It does not become release truth, closeout truth, workflow truth, evidence truth, or readiness truth."
required_issue_lint_boundary_line_lower="$(printf '%s' "${required_issue_lint_boundary_line}" | tr '[:upper:]' '[:lower:]')"

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" == "${allowed_non_claim_line_lower}" || "${line_lower}" == "${required_issue_lint_boundary_line_lower}" ]]; then
    continue
  fi
  for claim in "${forbidden_claims[@]}"; do
    if [[ "${line_lower}" == *"${claim}"* ]]; then
      echo "Forbidden Phase 63 closeout evaluation claim: ${claim}" >&2
      exit 1
    fi
  done
done < "${absolute_doc_path}"

if grep -Eiq -- '(AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|password[[:space:]]*=[[:space:]]*[^<[:space:]]+|secret[[:space:]]*=[[:space:]]*[^<[:space:]]+)' "${absolute_doc_path}"; then
  echo "Forbidden Phase 63 closeout evaluation: production secret-looking value detected" >&2
  exit 1
fi

path_hygiene_stderr="${repo_root}/.tmp-phase63-8-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63 closeout evaluation absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.8 closeout evaluation contract and focused negative checks pass."
