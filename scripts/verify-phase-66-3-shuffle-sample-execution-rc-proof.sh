#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/deployment/shuffle-smb-single-node-profile-contract.md"
  "docs/deployment/shuffle-reviewed-workflow-template-contract.md"
  "docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
  "docs/deployment/shuffle-manual-fallback-contract.md"
  "docs/deployment/shuffle-authority-boundary-negative-tests.md"
  "docs/deployment/case-timeline-authority-projection-contract.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "scripts/verify-publishable-path-hygiene.sh"
)

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_text() {
  perl -0pe 's/<!--.*?-->//gs' "$@"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_text "${file}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_section_phrase() {
  local section="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(perl -0pe 's/<!--.*?-->//gs' <<<"${section}"); then
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
      if (next_heading != "" && line == next_heading) {
        exit
      }
      print
    }
  ' "${file}"
}

require_file "${absolute_doc_path}" "Phase 66.3 Shuffle sample execution RC proof"
require_file "${readme_path}" "README for Phase 66.3 link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.3 reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.3 verifier script ${verifier_script}"
done

require_phrase "${readme_path}" "- [Phase 66.3 Shuffle sample execution RC proof](docs/phase-66-3-shuffle-sample-execution-rc-proof.md) defines the reviewed Shuffle sample execution proof surface for RC evidence while preserving Shuffle as subordinate routine automation substrate and excluding broad SOAR marketplace coverage, autonomous remediation, production automation authority, GA, and commercial replacement claims." "README canonical Phase 66.3 boundary bullet"
require_phrase "${readme_path}" "The Phase 66.3 Shuffle sample execution RC proof is defined by the [Phase 66.3 Shuffle sample execution RC proof](docs/phase-66-3-shuffle-sample-execution-rc-proof.md)." "README Product positioning Phase 66.3 reference"

required_phrases=(
  "# Phase 66.3 Shuffle Sample Execution RC Proof"
  "**Status**: Accepted as the Phase 66.3 Shuffle sample execution RC proof contract for release-candidate evidence planning only."
  "**Related Baseline**: \`docs/phase-66-1-clean-host-rc-e2e-harness.md\`, \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`, \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, \`docs/deployment/shuffle-smb-single-node-profile-contract.md\`, \`docs/deployment/shuffle-reviewed-workflow-template-contract.md\`, \`docs/deployment/shuffle-notify-identity-owner-template-import-contract.md\`, \`docs/deployment/shuffle-manual-fallback-contract.md\`, \`docs/deployment/shuffle-authority-boundary-negative-tests.md\`, \`docs/deployment/case-timeline-authority-projection-contract.md\`, \`docs/phase-65-closeout-evaluation.md\`"
  "**Related Issues**: #1397, #1400"
  "This contract defines the Phase 66.3 Shuffle sample execution RC proof surface."
  "The proof depends on the Phase 66.1 clean-host RC E2E harness."
  "The Shuffle sample execution proof demonstrates that a reviewed low-risk action can move from AegisOps action request to approval, Shuffle delegation, normalized execution receipt, and reviewed reconciliation without turning Shuffle workflow state into approval truth, execution truth, reconciliation truth, case truth, release truth, gate truth, or workflow authority."
  "This proof is RC evidence only."
  "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth."
  "Shuffle remains a subordinate routine automation substrate."
  "The proof must reject missing approval, missing action request, missing delegation payload, missing execution receipt, missing reconciliation review, missing limitation references, direct-launch bypass, approval bypass, execution bypass, Shuffle-as-truth claims, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth."
  "Phase 66.3 records one reviewed Shuffle sample execution path for RC evidence."
  "Later Phase 66 issues must still prove AI-assisted triage, report export, supportability, RC authority-boundary proof pack, and closeout evidence independently."
  'Run `bash scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh`.'
  'Run `bash scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1400 --config <supervisor-config-path>`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 66.3 Shuffle sample execution proof term in ${doc_path}"
done

evidence_section="$(section_text "${absolute_doc_path}" "## 2. Sample Execution Evidence" "## 3. Delegation, Receipt, And Reconciliation")"
evidence_rows=(
  "| \`journey_run_id\` | The Phase 66.1 run identifier that observed the sample execution. | Missing or mismatched run identifiers fail the proof. |"
  "| \`repository_revision\` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |"
  "| \`shuffle_profile\` | \`smb-single-node\` Shuffle product profile reference. | Any other profile is out of scope. |"
  "| \`reviewed_template_id\` | Reviewed Shuffle template identifier and reviewed version. | Unreviewed, draft, sample, placeholder, TODO, or deprecated templates fail the proof. |"
  "| \`action_request_id\` | AegisOps action request identifier for the delegated work. | Request text, ticket text, or workflow names cannot create action-request truth. |"
  "| \`approval_decision_id\` | AegisOps approval decision identifier and approver role. | Approval cannot be inferred from comments, tickets, UI state, or Shuffle state. |"
  "| \`delegation_payload_reference\` | Reviewed delegation payload binding action request, approval, template version, callback, and idempotency key. | Direct or ad hoc Shuffle launch paths fail the proof. |"
  "| \`callback_binding_reference\` | Reviewed callback URL, callback secret custody reference, and correlation binding. | Raw forwarded headers or inferred callback identity fail the proof. |"
  "| \`execution_receipt_id\` | AegisOps normalized execution receipt linked to the Shuffle run. | Shuffle workflow success or callback payload alone cannot create execution receipt truth. |"
  "| \`reconciliation_review_id\` | AegisOps reconciliation review comparing approval, request, receipt, and result. | Shuffle success cannot become reconciliation truth. |"
  "| \`limitation_references\` | Known limitation ids, owner, decision date, and follow-up date when evidence is incomplete. | Missing limitations cannot be hidden in Shuffle execution text. |"
)

for row in "${evidence_rows[@]}"; do
  require_section_phrase "${evidence_section}" "${row}" "Phase 66.3 sample execution evidence field"
done

delegation_section="$(section_text "${absolute_doc_path}" "## 3. Delegation, Receipt, And Reconciliation" "## 4. Authority Boundary")"
delegation_terms=(
  "The proof must cite \`docs/deployment/shuffle-smb-single-node-profile-contract.md\`"
  "The proof must cite \`docs/deployment/shuffle-reviewed-workflow-template-contract.md\`"
  "The proof must cite \`docs/deployment/shuffle-notify-identity-owner-template-import-contract.md\`"
  "The proof must cite \`docs/deployment/case-timeline-authority-projection-contract.md\`"
  "frontend, backend, orborus, worker, OpenSearch, API, callback, credential custody, volume, port, and pinned-version posture"
  "template identity, template version, owner, review status, correlation id, action request id, approval decision id, execution receipt id, normalized receipt reference, callback URL, callback secret reference, and idempotency key"
  "approved request, Shuffle receipt, mismatch outcome, follow-up owner, and linked AegisOps record"
  "Shuffle workflow status, workflow success, workflow failure, callback payload, workflow canvas state, execution logs, generated config, ticket state, browser state, UI cache, verifier output, issue-lint output, and downstream receipts remain subordinate evidence."
)

for term in "${delegation_terms[@]}"; do
  require_section_phrase "${delegation_section}" "${term}" "Phase 66.3 delegation, receipt, or reconciliation term"
done

limitations_section="$(section_text "${absolute_doc_path}" "## 5. Accepted Limitations" "## 6. Verification")"
require_section_phrase "${limitations_section}" "It does not prove broad SOAR marketplace coverage, arbitrary connector import, autonomous remediation, Controlled Write readiness, Hard Write readiness, production customer workflow import, production automation authority, real design-partner success, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness." "Phase 66.3 accepted limitations boundary"

subordinate_authority_subjects='(shuffle([[:space:]]+(workflow|state|success|failure|status|retry|callback|payload|canvas|logs?|execution|api|template|metadata|ticket|receipt))?|workflow[[:space:]]+success|workflow[[:space:]]+status|workflow[[:space:]]+failure|callback[[:space:]]+payloads?|workflow[[:space:]]+canvas[[:space:]]+state|execution[[:space:]]+logs?|generated[[:space:]-]+config(uration)?|ticket[[:space:]]+state|tickets?|ai[[:space:]]+output|browser[[:space:]]+state|ui[[:space:]]+cache|verifier[[:space:]]+output|issue-lint[[:space:]]+output|downstream[[:space:]]+receipts?)'
authority_verbs='(approve[s]?|execute[s]?|reconcile[s]?|close[s]?|release[s]?|gate[s]?|mutate[s]?|promote[s]?)'
authority_objects='(aegisops[[:space:]]+records?|case|alert|record|workflow|release|gate|evidence|approval|action[[:space:]-]+requests?|execution[[:space:]-]+receipts?|reconciliation|audit|limitation|closeout)'

repository_revision_value_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`[:space:],.;)]+|refs/remotes/[^`[:space:],.;)]+|remotes/[^`[:space:],.;)]+|origin/[^`[:space:],.;)]+|[^`[:space:],.;)]*branch)`?([[:space:].,;)]|$)'
shuffle_profile_value_regex='(^|[[:space:]>*-])`?shuffle_profile`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
reviewed_template_value_regex='(^|[[:space:]>*-])`?reviewed_template_id`?[[:space:]]*[:=][^.[:cntrl:]]*(unreviewed|draft|sample|placeholder|todo|deprecated)'
direct_launch_value_regex='(^|[[:space:]>*-])`?(direct_shuffle_launch|launch_shuffle_directly|ad_hoc_shuffle_launch|approval_bypass|execution_bypass)`?[[:space:]]*[:=][[:space:]]*`?(true|allowed|yes|enabled)'

forbidden_patterns=(
  'phase[[:space:]]+66\.3[[:space:]]+(proves|satisfies|passes|accepts|grants)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|broad[[:space:]]+soar|soar[[:space:]]+marketplace|arbitrary[[:space:]]+connector|autonomous[[:space:]]+remediation|controlled[[:space:]]+write|hard[[:space:]]+write|production[[:space:]]+(customer[[:space:]]+)?workflow|production[[:space:]]+automation|commercial[[:space:]]+replacement|real[[:space:]]+design[- ]partner|phase[[:space:]]+66[[:space:]]+closeout)'
  'phase[[:space:]]+66\.3[[:space:]]+confirms[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|broad[[:space:]]+soar[[:space:]]+(coverage|parity|readiness)|soar[[:space:]]+marketplace[[:space:]]+(coverage|readiness)|production[[:space:]]+(customer[[:space:]]+)?workflow[[:space:]]+(import|coverage|readiness)|production[[:space:]]+automation[[:space:]]+(authority|readiness)|commercial[[:space:]]+replacement[[:space:]]+readiness|real[[:space:]]+design[- ]partner[[:space:]]+success|phase[[:space:]]+66[[:space:]]+closeout)'
  'phase[[:space:]]+66\.3[[:space:]]+(satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc([[:space:][:punct:]]|$)|release[- ]candidate)'
  'phase[[:space:]]+66\.3[[:space:]]+proves[^.[:cntrl:]]*(rc[- ]?(gate|readiness|pass)|release[- ]candidate[- ]?(gate|readiness|pass))'
  '(phase[[:space:]]+66\.3|this[[:space:]]+proof|proof|aegisops)[[:space:]]+(is|becomes|serves[[:space:]]+as)[[:space:]]+(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?ready[[:space:]]+for[[:space:]]+(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate)'
  '(this[[:space:]]+)?proof[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms|achieves)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate|readiness|broad[[:space:]]+soar|soar[[:space:]]+marketplace|production[[:space:]]+(customer[[:space:]]+)?workflow|production[[:space:]]+automation|commercial[[:space:]]+replacement)'
  'shuffle[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(approval|action[[:space:]-]+request|execution[[:space:]-]+receipt|reconciliation|case|workflow|release|gate|evidence|audit|limitation|closeout)[[:space:]]+truth'
  'shuffle[[:space:]]+(workflow|success|status|failure|callback|payload|receipt|logs?|canvas|execution)[^.[:cntrl:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(approval|action[[:space:]-]+request|execution[[:space:]-]+receipt|reconciliation|case|workflow|release|gate|evidence|audit|limitation|closeout)[[:space:]]+truth'
  "${subordinate_authority_subjects}[[:space:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(approval|action[[:space:]-]+request|execution[[:space:]-]+receipt|reconciliation|case|workflow|release|gate|evidence|audit|limitation|closeout)[[:space:]]+truth"
  "shuffle[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "${subordinate_authority_subjects}[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  '(direct|ad[[:space:]-]+hoc)[[:space:]]+shuffle[[:space:]-]+launch[^.[:cntrl:]]+(is[[:space:]]+)?(allowed|approved|valid|accepted)'
  '(approval|execution)[[:space:]-]+bypass[^.[:cntrl:]]+(is[[:space:]]+)?(allowed|approved|valid|accepted)'
  'shuffle[[:space:]]+workflow[[:space:]]+success[^.[:cntrl:]]+(proves|creates|establishes|supplies|satisfies)[^.[:cntrl:]]*reconciliation'
  'callback[[:space:]]+payload[^.[:cntrl:]]+(proves|creates|establishes|supplies|satisfies)[^.[:cntrl:]]*execution[[:space:]-]+receipt'
  '(workflow[[:space:]]+names?|ticket[[:space:]]+text|comments?|ui[[:space:]]+state|shuffle[[:space:]]+state)[^.[:cntrl:]]+(prove[s]?|create[s]?|establish(es)?|suppl(y|ies)|satisf(y|ies)|imply|implies)[^.[:cntrl:]]*(approval|action[[:space:]-]+request)'
  '(raw[[:space:]]+forwarded[[:space:]]+headers?|inferred[[:space:]]+callback[[:space:]]+identity)[^.[:cntrl:]]+(prove[s]?|create[s]?|establish(es)?|suppl(y|ies)|satisf(y|ies))[^.[:cntrl:]]*callback'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|commercial[[:space:]]+replacement|broad[[:space:]]+soar)'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate|workflow|source)[[:space:]]+truth'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(readiness|release|gate|workflow|source|rc([[:space:][:punct:]]|$)|ga([[:space:][:punct:]]|$))'
)

forbidden_regex="$(IFS='|'; printf '%s' "${forbidden_patterns[*]}")"

scan_forbidden_claims() {
  local file="$1"
  local description="$2"

  if grep -Eiv -- '(cannot|must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include|does[[:space:]]+not[[:space:]]+prove|do[[:space:]]+not[[:space:]]+prove|remains?[[:space:]]+out[[:space:]]+of[[:space:]]+scope)' < <(visible_text "${file}") | grep -Eiq -- "${forbidden_regex}"; then
    echo "Forbidden Phase 66.3 ${description} claim matched" >&2
    exit 1
  fi
}

scan_forbidden_claims "${absolute_doc_path}" "Shuffle sample execution RC proof"

if grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|(password|passwd|secret([_ -]?key)?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- '(^|[[:space:]>*-])`?(journey_run_id|repository_revision|reviewed_template_id|action_request_id|approval_decision_id|delegation_payload_reference|callback_binding_reference|execution_receipt_id|reconciliation_review_id|limitation_references)`?[[:space:]]*[:=][[:space:]]*`?(missing|none|null|n/a|tbd|todo|unknown|not[[:space:]_-]*provided|not[[:space:]_-]*set)`?([[:space:].,;)]|$)' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eiq -- '(^|[[:space:]>*-])`?limitation_references`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]-]+in[[:space:]-]+shuffle[[:space:]-]+execution[[:space:]-]+text' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: hidden limitation references detected" >&2
  exit 1
fi

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" =~ ${repository_revision_value_regex} ]]; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${shuffle_profile_value_regex} ]] && [[ "${BASH_REMATCH[2]}" != "smb-single-node" ]]; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: invalid Shuffle profile detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${reviewed_template_value_regex} ]]; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: invalid reviewed template detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${direct_launch_value_regex} ]]; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: bypass value detected" >&2
    exit 1
  fi
  if grep -Eiq -- 'customer[-_ ]private[[:space:]]+data[[:space:]]*[:=]' <<<"${line}"; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ (must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include) ]]; then
    continue
  fi
  if grep -Eiq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(data|example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line}"; then
    echo "Forbidden Phase 66.3 Shuffle sample execution RC proof: customer-private data detected" >&2
    exit 1
  fi
done < <(visible_text "${absolute_doc_path}")

path_hygiene_stderr="${repo_root}/.tmp-phase66-3-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 66.3 Shuffle sample execution RC proof absolute path usage detected" >&2
  exit 1
fi

echo "Phase 66.3 Shuffle sample execution RC proof contract and focused negative checks pass."
