#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-5-report-export-rc-proof.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
tmp_dir="$(mktemp -d)"
doc_visible_path="${tmp_dir}/phase-66-5-doc.visible.md"
readme_visible_path="${tmp_dir}/README.visible.md"
doc_visible_lower_path="${tmp_dir}/phase-66-5-doc.visible.lower.md"
trap 'rm -rf "${tmp_dir}"' EXIT

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/getting-started/first-user-demo-report-export.md"
  "docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-5-report-export-rc-proof.sh"
  "scripts/test-verify-phase-66-5-report-export-rc-proof.sh"
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
  if [[ "$#" -eq 1 && "$1" == "${absolute_doc_path}" && -s "${doc_visible_path}" ]]; then
    cat "${doc_visible_path}"
    return
  fi
  if [[ "$#" -eq 1 && "$1" == "${readme_path}" && -s "${readme_visible_path}" ]]; then
    cat "${readme_visible_path}"
    return
  fi
  perl -0pe 's/<!--.*?-->//gs' "$@"
}

lower_visible_text() {
  if [[ "$#" -eq 1 && "$1" == "${absolute_doc_path}" && -s "${doc_visible_lower_path}" ]]; then
    cat "${doc_visible_lower_path}"
    return
  fi
  visible_text "$@" | tr '[:upper:]' '[:lower:]'
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

require_file "${absolute_doc_path}" "Phase 66.5 report export RC proof"
require_file "${readme_path}" "README for Phase 66.5 link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.5 reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.5 verifier script ${verifier_script}"
done

perl -0pe 's/<!--.*?-->//gs' "${absolute_doc_path}" >"${doc_visible_path}"
perl -0pe 's/<!--.*?-->//gs' "${readme_path}" >"${readme_visible_path}"
tr '[:upper:]' '[:lower:]' <"${doc_visible_path}" >"${doc_visible_lower_path}"

require_phrase "${readme_path}" "- [Phase 66.5 report export RC proof](docs/phase-66-5-report-export-rc-proof.md) defines the reviewed report export proof surface for RC evidence while preserving AegisOps records as workflow authority and excluding compliance certification, production SLA reporting, customer portal readiness, GA, and commercial replacement claims." "README canonical Phase 66.5 boundary bullet"
require_phrase "${readme_path}" "The Phase 66.5 report export RC proof is defined by the [Phase 66.5 report export RC proof](docs/phase-66-5-report-export-rc-proof.md)." "README Product positioning Phase 66.5 reference"

required_phrases=(
  "# Phase 66.5 Report Export RC Proof"
  "**Status**: Accepted as the Phase 66.5 report export RC proof contract for release-candidate evidence planning only."
  "**Related Baseline**: \`docs/phase-66-1-clean-host-rc-e2e-harness.md\`, \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`, \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, \`docs/getting-started/first-user-demo-report-export.md\`, \`docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md\`, \`docs/phase-65-closeout-evaluation.md\`"
  "**Related Issues**: #1397, #1402"
  "This contract defines the Phase 66.5 report export RC proof surface."
  "The proof depends on the Phase 66.1 clean-host RC E2E harness."
  "This proof is RC evidence only."
  "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth."
  "Reports are repeatable evidence exports only."
  "The proof must reject missing report identity, missing source record references, missing case/action/reconciliation sections, missing RC labels, missing redaction posture, missing limitation references, report-as-truth claims, report-driven case closure, report-driven action execution, report-driven reconciliation, workstation-local paths, production secrets, customer-private data, compliance certification claims, customer portal readiness claims, production SLA reporting claims, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth."
  "Phase 66.5 records one reviewed report export path for RC evidence."
  "Later Phase 66 issues must still prove supportability, RC authority-boundary proof pack, and closeout evidence independently."
  'Run `bash scripts/verify-phase-66-5-report-export-rc-proof.sh`.'
  'Run `bash scripts/test-verify-phase-66-5-report-export-rc-proof.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1402 --config <supervisor-config-path>`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 66.5 report export proof term in ${doc_path}"
done

evidence_section="$(section_text "${absolute_doc_path}" "## 2. Report Export Evidence" "## 3. Export Binding And Redaction")"
evidence_rows=(
  "| \`journey_run_id\` | The Phase 66.1 run identifier that observed the export. | Missing or mismatched run identifiers fail the proof. |"
  "| \`repository_revision\` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |"
  "| \`report_export_id\` | Reviewed report export identifier, timestamp, operator, and export profile. | Missing export identity or placeholder export ids fail the proof. |"
  "| \`export_format\` | Bounded export format, file name pattern, and checksum or hash reference. | Unsupported or unspecified export formats fail the proof. |"
  "| \`source_record_references\` | Direct AegisOps references for source alert, case, evidence, approval, action request, execution receipt, and reconciliation records. | Report text, screenshots, browser state, or UI cache cannot create source-record truth. |"
  "| \`case_section_reference\` | Reviewed case section containing status, evidence links, owner, and limitation references. | Report sections cannot close cases or override case records. |"
  "| \`action_section_reference\` | Reviewed action section containing approval, delegated action request, execution receipt, and mismatch posture. | Report sections cannot approve, execute, or reconcile actions. |"
  "| \`reconciliation_section_reference\` | Reviewed reconciliation section binding receipt, outcome, mismatch state, follow-up owner, and linked record. | Report sections cannot become reconciliation truth. |"
  "| \`rc_label_set\` | Required labels \`rc-evidence\`, \`phase-66\`, \`report-export\`, and \`not-workflow-truth\`. | Missing RC labels or production-truth labels fail the proof. |"
  "| \`redaction_posture\` | Secret, credential, customer-private data, workstation-local path, and PII redaction posture. | Raw secrets, customer-private payloads, and workstation-local paths fail the proof. |"
  "| \`limitation_references\` | Known limitation ids, owner, decision date, and follow-up date when export evidence is incomplete. | Missing limitations cannot be hidden in report text. |"
)

for row in "${evidence_rows[@]}"; do
  require_section_phrase "${evidence_section}" "${row}" "Phase 66.5 report export evidence field"
done

binding_section="$(section_text "${absolute_doc_path}" "## 3. Export Binding And Redaction" "## 4. Authority Boundary")"
binding_terms=(
  "The proof must cite \`docs/phase-66-1-clean-host-rc-e2e-harness.md\`"
  "journey run id, immutable repository revision, export command or UI action reference, generated artifact identity, export format, checksum or hash reference, operator, timestamp, and reviewed storage posture"
  "The proof must cite \`docs/getting-started/first-user-demo-report-export.md\`"
  "report labels, source record references, case section, action section, reconciliation section, authority boundary, secret hygiene, and unavailable-reference follow-up posture"
  "The proof must cite \`docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md\`"
  "prior pilot report remains input evidence only and cannot satisfy Phase 66 RC report export by itself"
  "The proof must cite \`docs/phase-65-closeout-evaluation.md\`"
  "Report output, generated files, report metadata, browser state, UI cache, screenshots, verifier output, issue-lint output, and optional evidence remain subordinate evidence."
)

for term in "${binding_terms[@]}"; do
  require_section_phrase "${binding_section}" "${term}" "Phase 66.5 export binding or redaction term"
done

limitations_section="$(section_text "${absolute_doc_path}" "## 5. Accepted Limitations" "## 6. Verification")"
require_section_phrase "${limitations_section}" "It does not prove compliance certification, customer portal readiness, production SLA reporting, real design-partner export success, report authority over AegisOps records, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness." "Phase 66.5 accepted limitations boundary"

subordinate_subjects='(reports?|report[[:space:]]+(output|sections?|metadata|labels?|text|exports?|files?|artifacts?)|generated[[:space:]]+files?|export[[:space:]]+(metadata|artifacts?|output)|downloaded[[:space:]]+artifacts?|screenshots?|browser[[:space:]]+state|ui[[:space:]]+(state|cache)|optional[[:space:]]+evidence|verifier[[:space:]]+output|issue-lint[[:space:]]+output)'
authority_verbs='(approve[s]?|approved|execute[s]?|executed|reconcile[s]?|reconciled|close[s]?|closed|release[s]?|released|gate[s]?|gated|mutate[s]?|mutated|promote[s]?|promoted|override[s]?|overrode|overridden)'
authority_objects='(aegisops[[:space:]]+records?|case|cases|alert|record|workflow|release|gate|evidence|approval|action[[:space:]-]+requests?|execution[[:space:]-]+receipts?|reconciliation|audit|limitation|source[[:space:]-]+admission|closeout|actions?)'
missing_value='missing|mismatched|none|null|n/a|tbd|todo|unknown|unavailable|omitted|absent|blank|empty|withheld|placeholder|sample|not[[:space:]_-]*provided|not[[:space:]_-]*set|unsupported|unspecified'
required_fields='journey_run_id|repository_revision|report_export_id|export_format|source_record_references|case_section_reference|action_section_reference|reconciliation_section_reference|rc_label_set|redaction_posture|limitation_references'

repository_revision_value_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`[:space:],.;)]+|refs/remotes/[^`[:space:],.;)]+|remotes/[^`[:space:],.;)]+|origin/[^`[:space:],.;)]+|[^`[:space:],.;)]*branch)`?([[:space:].,;)]|$)'
repository_revision_assignment_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
repository_revision_mutable_suffix_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][^.[:cntrl:]]*[0-9a-f]{40}[^.[:cntrl:]]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)'
repository_revision_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?([^`|[:space:]]+)`?[[:space:]]*\|'
repository_revision_table_mutable_suffix_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?[^`|]*[0-9a-f]{40}[^`|]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)[^`|]*`?[[:space:]]*\|'
repository_revision_table_branch_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|.*\|[[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`|[:space:]]+|refs/remotes/[^`|[:space:]]+|remotes/[^`|[:space:]]+|origin/[^`|[:space:]]+|[^`|[:space:]]*branch)`?[[:space:]]*(\||$)'
source_record_shortcut_regex='(^|[[:space:]>*-])`?source_record_references`?[[:space:]]*[:=][^.[:cntrl:]]*(report[[:space:]_-]*(text|output|metadata|labels?|artifacts?)|generated[[:space:]_-]*files?|downloaded[[:space:]_-]*artifacts?|export[[:space:]_-]*(artifacts?|output)|screenshots?|browser[[:space:]_-]*state|ui[[:space:]_-]*(state|cache))'
source_record_shortcut_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?source_record_references`?[[:space:]]*\|[[:space:]]*`?[^`|]*(report[[:space:]_-]*(text|output|metadata|labels?|artifacts?)|generated[[:space:]_-]*files?|downloaded[[:space:]_-]*artifacts?|export[[:space:]_-]*(artifacts?|output)|screenshots?|browser[[:space:]_-]*state|ui[[:space:]_-]*(state|cache))[^`|]*`?[[:space:]]*\|'
section_authority_terms='(closed|case[[:space:]_-]*closed|case[[:space:]_-]*closure|approval|approved|execution|executed|reconciliation|reconciled|override|truth)'
section_authority_regex="(^|[[:space:]>*-])\`?(case_section_reference|action_section_reference|reconciliation_section_reference)\`?[[:space:]]*[:=][^.[:cntrl:]]*${section_authority_terms}"
section_authority_table_regex="(^|[[:space:]>*-])\|[[:space:]]*\`?(case_section_reference|action_section_reference|reconciliation_section_reference)\`?[[:space:]]*\|[[:space:]]*\`?[^\`|]*${section_authority_terms}[^\`|]*\`?[[:space:]]*\|"
label_missing_regex='(^|[[:space:]>*-])`?rc_label_set`?[[:space:]]*[:=][^.[:cntrl:]]*(missing|without|no[[:space:]_-]*labels?|production[[:space:]_-]*truth)'
label_missing_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?rc_label_set`?[[:space:]]*\|[[:space:]]*`?[^`|]*(missing|without|no[[:space:]_-]*labels?|production[[:space:]_-]*truth)[^`|]*`?[[:space:]]*\|'
rc_label_set_assignment_regex='(^|[[:space:]>*-])`?rc_label_set`?[[:space:]]*[:=][^.[:cntrl:]]+'
rc_label_set_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?rc_label_set`?[[:space:]]*\|[[:space:]]*`?([^`|]+)`?[[:space:]]*\|'
redaction_missing_regex='(^|[[:space:]>*-])`?redaction_posture`?[[:space:]]*[:=][^.[:cntrl:]]*(not[[:space:]_-]*needed|none|unredacted|raw[[:space:]_-]*secrets?|secrets?[[:space:]_-]*included|customer[-_ ]private[[:space:]_-]*payloads?|workstation[-_ ]local[[:space:]_-]*paths?[[:space:]_-]*included)'
redaction_missing_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?redaction_posture`?[[:space:]]*\|[[:space:]]*`?[^`|]*(not[[:space:]_-]*needed|none|unredacted|raw[[:space:]_-]*secrets?|secrets?[[:space:]_-]*included|customer[-_ ]private[[:space:]_-]*payloads?|workstation[-_ ]local[[:space:]_-]*paths?[[:space:]_-]*included)[^`|]*`?[[:space:]]*\|'
customer_private_prohibition_regex='((must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include|fail[s]?[[:space:]]+the[[:space:]]+proof)[^.[:cntrl:]]*customer[-_ ]private|customer[-_ ]private[^.[:cntrl:]]*fail[s]?[[:space:]]+the[[:space:]]+proof)'
customer_private_unsafe_regex='(includes|contains|embeds|carries|stores)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(examples?|tickets?|alerts?|logs?|chats?|payloads?|exports?)([[:space:].,;)]|[[:space:]]+(are|were|was|is)[[:space:]]+(stored|included|embedded|carried))|unredacted[[:space:]]+customer[[:space:]]+(tickets?|alerts?|logs?|chats?|payloads?|exports?|data)([[:space:].,;)]|$)'
canonical_source_record_references_row='| `source_record_references` | direct aegisops references for source alert, case, evidence, approval, action request, execution receipt, and reconciliation records. | report text, screenshots, browser state, or ui cache cannot create source-record truth. |'
canonical_case_section_reference_row='| `case_section_reference` | reviewed case section containing status, evidence links, owner, and limitation references. | report sections cannot close cases or override case records. |'
canonical_action_section_reference_row='| `action_section_reference` | reviewed action section containing approval, delegated action request, execution receipt, and mismatch posture. | report sections cannot approve, execute, or reconcile actions. |'
canonical_reconciliation_section_reference_row='| `reconciliation_section_reference` | reviewed reconciliation section binding receipt, outcome, mismatch state, follow-up owner, and linked record. | report sections cannot become reconciliation truth. |'

forbidden_patterns=(
  '(phase[[:space:]]+66\.5|this[[:space:]]+proof|proof)[^.[:cntrl:]]+(proves|satisfies|passes|accepts|grants|achieves|enables|validates|demonstrates|confirms|authorizes|establishes|guarantees|certif(y|ies))[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|ga[[:space:]-]+readiness|general[- ]availability|rc([[:space:][:punct:]]|$)|rc[[:space:]-]+gate|rc[[:space:]-]+readiness|rc[[:space:]-]+pass|release[- ]candidate[[:space:]-]+(readiness|pass)|supportability|closeout[[:space:]-]+evidence|compliance|compliance[[:space:]-]+certification|customer[[:space:]-]+portal|production[[:space:]-]+sla|production[[:space:]-]+reporting|commercial[[:space:]-]+replacement|real[[:space:]]+design[- ]partner|phase[[:space:]]+66[[:space:]]+closeout)'
  '(ga[[:space:]-]+readiness|rc[[:space:]-]+pass|compliance([[:space:]-]+certification)?)[^.[:cntrl:]]+(is|are|was|were|be|being|been|has[[:space:]]+been|have[[:space:]]+been|had[[:space:]]+been)[[:space:]]+(authorized|established|guaranteed|certified|proven|confirmed|validated|satisfied)[[:space:]]+by[[:space:]]+(phase[[:space:]]+66\.5|this[[:space:]]+proof|proof)'
  '(phase[[:space:]]+66\.5|this[[:space:]]+proof|proof|aegisops)([^.[:cntrl:]]+)?[[:space:]]+(is|becomes|serves[[:space:]]+as)[[:space:]]+(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?(ready[[:space:]]+for[[:space:]]+(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate|commercial[[:space:]]+replacement)|(ga|rc|release[- ]candidate|commercial[[:space:]]+replacement)[[:space:]-]+ready|compliance[[:space:]-]+certification|customer[[:space:]-]+portal[[:space:]-]+readiness|production[[:space:]-]+sla[[:space:]-]+reporting|real[[:space:]]+design[- ]partner[[:space:]]+export[[:space:]]+success|commercial[[:space:]-]+replacement[[:space:]-]+readiness)'
  "${subordinate_subjects}[^.[:cntrl:]]*[[:space:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as|creates?|created)[[:space:]]+[^.[:cntrl:]]*((source[[:space:]]+of[[:space:]]+truth)|(workflow|release|gate|readiness|case|action|reconciliation|source[[:space:]-]+record|evidence|approval|audit|limitation|source[[:space:]-]+admission|closeout)[[:space:]]+truth)"
  "${subordinate_subjects}[^.[:cntrl:]]*[[:space:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[[:space:]]+[^.[:cntrl:]]*(case[[:space:]-]+closure|action[[:space:]-]+execution|action[[:space:]-]+approval|reconciliation)"
  "${subordinate_subjects}([^.[:cntrl:]]+)?[[:space:]]+${authority_verbs}[[:space:]]+[^.[:cntrl:]]*${authority_objects}"
  "${authority_objects}[^.[:cntrl:]]+(is|are|was|were|be|being|been|has[[:space:]]+been|have[[:space:]]+been|had[[:space:]]+been|become|becomes)[[:space:]]+(approved|executed|reconciled|closed|released|gated|mutated|promoted|overridden)[[:space:]]+by[[:space:]]+[^.[:cntrl:]]*${subordinate_subjects}"
  "${subordinate_subjects}[^.[:cntrl:]]+(has|have|holds?|carries|grants?)[[:space:]]+[^.[:cntrl:]]*((workflow|release|gate|readiness|case|action|reconciliation|aegisops)[^.[:cntrl:]]+authority|authority[^.[:cntrl:]]*(workflow|release|gate|readiness|case|action|reconciliation|aegisops))"
  "${subordinate_subjects}[^.[:cntrl:]]+[[:space:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[[:space:]]+[^.[:cntrl:]]*((workflow|release|gate|readiness|case|action|reconciliation|aegisops)[^.[:cntrl:]]+authority|authority[^.[:cntrl:]]*(workflow|release|gate|readiness|case|action|reconciliation|aegisops))"
  "${subordinate_subjects}[^.[:cntrl:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]+authoritative[[:space:]]+(for|over|as)[^.[:cntrl:]]*${authority_objects}"
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as|proves|confirms|validates)[^.[:cntrl:]]*(readiness|release|gate|workflow|source)[[:space:]]+truth'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(proves|confirms|passes|satisfies|validates|demonstrates)[^.[:cntrl:]]*(ga[[:space:]-]+readiness|rc[[:space:]-]+readiness|rc[[:space:]-]+pass|release[- ]candidate[[:space:]-]+(readiness|pass)|release[[:space:]-]+readiness|gate[[:space:]-]+readiness)'
)

is_safe_forbidden_claim_line() {
  local line_lower="$1"
  local unsafe_clause_separator_regex='(^|[[:space:]])but[[:space:]]+'
  local unsafe_and_overclaim_regex='(^|[[:space:]])and[[:space:]]+[^.[:cntrl:]]*(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as|has|have|holds?|carries|grants?|proves|confirms|passes|satisfies|validates|demonstrates|authoritative)([[:space:]]|$)'
  local multi_sentence_safe_regex='\.[^.[:cntrl:]]*(without[[:space:]]+turning|cannot|does[[:space:]]+not[[:space:]]+prove|remain[s]?[[:space:]]+subordinate|reports[[:space:]]+are[[:space:]]+repeatable[[:space:]]+evidence[[:space:]]+exports[[:space:]]+only|aegisops[[:space:]]+records[[:space:]]+remain[[:space:]]+authoritative)'

  if [[ "${line_lower}" =~ ${unsafe_clause_separator_regex} ]] || [[ "${line_lower}" =~ \; ]]; then
    return 1
  fi
  if [[ "${line_lower}" =~ ^[[:space:]]*reports[[:space:]]+are[[:space:]]+repeatable[[:space:]]+evidence[[:space:]]+exports[[:space:]]+only\.[^.[:cntrl:]]+cannot ]]; then
    return 0
  fi
  if [[ "${line_lower}" =~ ${multi_sentence_safe_regex} ]]; then
    return 1
  fi
  if [[ "${line_lower}" =~ (without[[:space:]]+turning|cannot|does[[:space:]]+not[[:space:]]+prove|remain[s]?[[:space:]]+subordinate|reports[[:space:]]+are[[:space:]]+repeatable[[:space:]]+evidence[[:space:]]+exports[[:space:]]+only|aegisops[[:space:]]+records[[:space:]]+remain[[:space:]]+authoritative) ]] && [[ "${line_lower}" =~ ${unsafe_and_overclaim_regex} ]]; then
    return 1
  fi
  if [[ "${line_lower}" =~ (without[[:space:]]+turning|cannot) ]]; then
    return 0
  fi
  if [[ "${line_lower}" =~ (does[[:space:]]+not[[:space:]]+prove|remain[s]?[[:space:]]+subordinate|reports[[:space:]]+are[[:space:]]+repeatable[[:space:]]+evidence[[:space:]]+exports[[:space:]]+only|aegisops[[:space:]]+records[[:space:]]+remain[[:space:]]+authoritative) ]]; then
    return 0
  fi
  return 1
}

scan_forbidden_claims() {
  local file="$1"
  local description="$2"
  local scope="${3:-all}"
  local line_lower
  local forbidden_pattern

  while IFS= read -r line_lower; do
    if [[ "${scope}" == "phase66_5_readme" ]] && [[ ! "${line_lower}" =~ (phase[[:space:]]+66\.5|report[[:space:]]+export|rc[[:space:]]+proof) ]]; then
      continue
    fi
    if [[ "${line_lower}" == "${canonical_source_record_references_row}" ]] || [[ "${line_lower}" == "${canonical_case_section_reference_row}" ]] || [[ "${line_lower}" == "${canonical_action_section_reference_row}" ]] || [[ "${line_lower}" == "${canonical_reconciliation_section_reference_row}" ]]; then
      continue
    fi
    if is_safe_forbidden_claim_line "${line_lower}"; then
      continue
    fi
    for forbidden_pattern in "${forbidden_patterns[@]}"; do
      if [[ "${line_lower}" =~ ${forbidden_pattern} ]]; then
        echo "Forbidden Phase 66.5 ${description} claim matched" >&2
        exit 1
      fi
    done
  done < <(lower_visible_text "${file}")

  while IFS= read -r line_lower; do
    if [[ "${scope}" == "phase66_5_readme" ]] && [[ ! "${line_lower}" =~ (phase[[:space:]]+66\.5|report[[:space:]]+export|rc[[:space:]]+proof) ]]; then
      continue
    fi
    if is_safe_forbidden_claim_line "${line_lower}"; then
      continue
    fi
    for forbidden_pattern in "${forbidden_patterns[@]}"; do
      if [[ "${line_lower}" =~ ${forbidden_pattern} ]]; then
        echo "Forbidden Phase 66.5 ${description} claim matched" >&2
        exit 1
      fi
    done
  done < <(lower_visible_text "${file}" | awk '!/^[[:space:]]*\|/ && NF { paragraph = paragraph " " $0; next } paragraph != "" { print paragraph; paragraph = "" } END { if (paragraph != "") print paragraph }')
}

if perl -pe 's/(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?(redacted|masked|removed|omitted|not[[:space:]_-]*stored)`?([[:space:].,;)]|$)/redacted_credential_posture /ig' "${absolute_doc_path}" | grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*(bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|basic[[:space:]]+[A-Za-z0-9+/=]{12,})|(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}'; then
  echo "Forbidden Phase 66.5 report export RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(data|example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' < <(perl -0ne 'while (/<!--(.*?)-->/gs) { print "$1\n" }' "${absolute_doc_path}" | tr '[:upper:]' '[:lower:]'); then
  echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\`?(${required_fields})\`?[[:space:]]*[:=][^.[:cntrl:]]*(^|[[:space:]\`])(${missing_value})([[:space:]_.-]+[^.[:cntrl:]]*)?([[:space:].,;)]|$)" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if awk -v fields="${required_fields}" '
  BEGIN { pattern = "(^|[[:space:]>*-])`?(" fields ")`?[[:space:]]*[:=]" }
  {
    line = $0
    if (match(line, pattern)) {
      rest = substr(line, RSTART + RLENGTH)
      gsub(/`/, "", rest)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", rest)
      gsub(/^[.,;)]*/, "", rest)
      gsub(/[.,;)]*$/, "", rest)
      if (rest == "") {
        found = 1
      }
    }
  }
  END { exit found ? 0 : 1 }
' < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\|[[:space:]]*\`?(${required_fields})\`?[[:space:]]*\|[[:space:]]*\`?[^|]*(^|[[:space:]\`])(${missing_value})([[:space:]_.-]+[^|]*)?\|" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\|[[:space:]]*\`?(${required_fields})\`?[[:space:]]*\|[[:space:]]*\`?[[:space:]]*\`?[[:space:]]*\|" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- '(^|[[:space:]>*-])`?limitation_references`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]_-]+in[[:space:]_-]+report[[:space:]_-]+text|(^|[[:space:]>*-])\|[[:space:]]*`?limitation_references`?[[:space:]]*\|[^|]*hidden[[:space:]_-]+in[[:space:]_-]+report[[:space:]_-]+text[^|]*\|' < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

while IFS= read -r line_lower; do
  if [[ "${line_lower}" =~ ${repository_revision_value_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_mutable_suffix_regex} ]] || [[ "${line_lower}" =~ ${repository_revision_table_mutable_suffix_regex} ]] || [[ "${line_lower}" =~ ${repository_revision_table_branch_any_cell_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_assignment_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: non-immutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_table_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: non-immutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${source_record_shortcut_regex} ]] || [[ "${line_lower}" =~ ${source_record_shortcut_table_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid source record reference detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" != "${canonical_case_section_reference_row}" ]] && [[ "${line_lower}" != "${canonical_action_section_reference_row}" ]] && [[ "${line_lower}" != "${canonical_reconciliation_section_reference_row}" ]] && { [[ "${line_lower}" =~ ${section_authority_regex} ]] || [[ "${line_lower}" =~ ${section_authority_table_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: report section authority detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${label_missing_regex} ]] || [[ "${line_lower}" =~ ${label_missing_table_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${rc_label_set_assignment_regex} ]] || [[ "${line_lower}" =~ ${rc_label_set_table_regex} ]]; then
    for required_rc_label in rc-evidence phase-66 report-export not-workflow-truth; do
      if ! grep -Eq -- "(^|[[:space:]\`,|])${required_rc_label}([[:space:]\`,|.]|$)" <<<"${line_lower}"; then
        echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
        exit 1
      fi
    done
    label_line_without_required_negative="${line_lower//not-workflow-truth/}"
    if grep -Eq -- '(^|[[:space:]`,|])workflow[[:space:]_-]*truth([[:space:]`,|.]|$)' <<<"${label_line_without_required_negative}"; then
      echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
      exit 1
    fi
  fi
  if [[ "${line_lower}" =~ ${redaction_missing_regex} ]] || [[ "${line_lower}" =~ ${redaction_missing_table_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid redaction posture detected" >&2
    exit 1
  fi
  if grep -Eq -- 'customer[-_ ]private[-_ ]data[[:space:]]*[:=]' <<<"${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${customer_private_prohibition_regex} ]] && ! grep -Eq -- '(includes|contains|embeds|carries|stores|are[[:space:]]+stored|is[[:space:]]+stored|were[[:space:]]+stored|was[[:space:]]+stored)' <<<"${line_lower}"; then
    continue
  fi
  if grep -Eq -- "${customer_private_unsafe_regex}" <<<"${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${customer_private_prohibition_regex} ]]; then
    continue
  fi
  if grep -Eq -- '(includes|contains|embeds|carries|stores)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+data|unredacted[[:space:]]+customer[[:space:]]+data' <<<"${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
done < <(lower_visible_text "${absolute_doc_path}")

scan_forbidden_claims "${absolute_doc_path}" "report export RC proof"
scan_forbidden_claims "${readme_path}" "README" "phase66_5_readme"

if [[ "${PHASE66_5_SKIP_PATH_HYGIENE:-0}" != "1" ]]; then
  path_hygiene_stderr="${tmp_dir}/path-hygiene.err"
  if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
    cat "${path_hygiene_stderr}" >&2
    echo "Forbidden Phase 66.5 report export RC proof absolute path usage detected" >&2
    exit 1
  fi
fi

echo "Phase 66.5 report export RC proof contract and focused negative checks pass."
