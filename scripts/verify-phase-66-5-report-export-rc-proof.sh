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
require_section_phrase "${evidence_section}" 'For Phase 66.5, the bounded `export_format` values are `pdf`, `csv`, and `json`; any other format requires an explicit contract revision before it can satisfy this proof.' "Phase 66.5 bounded export formats"

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

subordinate_subjects='(reports?|report[[:space:]]+(output|sections?|metadata|labels?|text|exports?|files?|artifacts?)|generated[[:space:]]+(files?|artifacts?)|export[[:space:]]+(metadata|artifacts?|output)|downloaded[[:space:]]+artifacts?|screenshots?|browser[[:space:]]+state|ui[[:space:]]+(state|cache)|optional[[:space:]]+evidence|verifier[[:space:]]+output|issue-lint[[:space:]]+output)'
readiness_claim_subjects="(phase[[:space:]]+66\\.5|this[[:space:]]+proof|proof|report[[:space:]-]+exports?|${subordinate_subjects})"
claim_provider_verbs='(provid(e|es|ed)|offer(s|ed)?|deliver(s|ed)?)'
readiness_claim_verbs="(prove(s|d)?|satisf(y|ies|ied)|passes|passed|accept(s|ed)?|grant(s|ed)?|achieve(s|d)?|enable(s|d)?|validate(s|d)?|demonstrate(s|d)?|confirm(s|ed)?|authorize(s|d)?|establish(es|ed)?|guarantee(s|d)?|certif(y|ies|ied)|infer(s|red|ring)?|impl(y|ies|ied)|indicat(e|es|ed)|conclud(e|es|ed)|${claim_provider_verbs})"
readiness_passive_claim_verbs='(authorized|established|guaranteed|certified|proven|proved|confirmed|validated|satisfied|demonstrated|inferred|implied|indicated|concluded)'
readiness_qualified_outcomes='(ga[[:space:]-]+(readiness|pass)|general[- ]availability([[:space:]-]+(readiness|pass))?|rc[[:space:]-]+(gate|readiness|pass)|release[- ]candidate[[:space:]-]+(gate|readiness|pass)|supportability|closeout[[:space:]-]+evidence|compliance([[:space:]-]+certification)?|customer[[:space:]-]+portal[[:space:]-]+(readiness|ready)|production[[:space:]-]+(sla[[:space:]-]+reporting|reporting)|commercial[[:space:]-]+replacement[[:space:]-]+readiness|real[[:space:]]+design[- ]partner[[:space:]-]+export[[:space:]-]+success|phase[[:space:]]+66[[:space:]-]+closeout)'
readiness_claim_outcomes="${readiness_qualified_outcomes}"
readiness_terminal_outcomes='(ga|rc)'
readiness_identity_outcomes="(ready[[:space:]]+for[[:space:]]+(ga|general[- ]availability|rc|release[- ]candidate|customer[[:space:]-]+portal|commercial[[:space:]-]+replacement)|(ga|rc|release[- ]candidate|customer[[:space:]-]+portal|commercial[[:space:]-]+replacement)[[:space:]-]+ready|${readiness_qualified_outcomes})"
readiness_claim_bridge='([[:space:]]+[^[:space:].,;]+){0,6}[[:space:]]+'
claim_identity_verbs='(is|are|was|were|be|being|been|become|becomes|became|(serve(s|d)?|act(s|ed)?|function(s|ed)?|operate(s|d)?)[[:space:]]+as|constitute(s|d)?|represent(s|ed)?)'
authority_provider_verbs="(has|have|had|holds?|held|carr(y|ies|ied)|grants?|granted|${claim_provider_verbs}|confer(s|red)?|convey(s|ed)?|bestow(s|ed)?|delegate(s|d)?)"
authority_verbs='(approve[s]?|approved|authoriz(e|es|ed)|permit[s]?|permitted|determine[s]?|determined|create[s]?|created|complete[s]?|completed|mark[s]?|marked|trigger[s]?|triggered|execute[s]?|executed|reconcile[s]?|reconciled|close[s]?|closed|release[s]?|released|gate[s]?|gated|mutate[s]?|mutated|promote[s]?|promoted|override[s]?|overrode|overridden|update[s]?|updated|change[s]?|changed|write[s]?|wrote|written|modif(y|ies|ied)|alter[s]?|altered|delete[s]?|deleted|set[s]?|transition[s]?|transitioned|replace[s]?|replaced)'
authority_passive_verbs='(approved|authorized|permitted|determined|created|completed|marked([[:space:]]+(closed|complete|completed|ready|resolved))?|triggered|executed|reconciled|closed|released|gated|mutated|promoted|overridden|updated|changed|written|modified|altered|deleted|set|transitioned|replaced)'
authority_objects='(aegisops[[:space:]]+records?|cases?|case[[:space:]-]+closure|case[[:space:]-]+closed|alerts?|records?|workflows?|releases?|gates?|evidence|approvals?|action[[:space:]-]+requests?|action[[:space:]-]+execution|execution[[:space:]-]+receipts?|reconciliation|audits?|limitations?|source[[:space:]-]+admission|closeout|actions?)'
authority_targets='(workflow|release|gate|readiness|case|action|reconciliation|evidence|approval|audit|limitation|source[[:space:]-]+admission|closeout|aegisops)'
truth_targets='((source[[:space:]]+of[[:space:]]+truth)|(workflow|release|gate|readiness|case|action|reconciliation|source[[:space:]-]+record|evidence|approval|audit|limitation|source[[:space:]-]+admission|closeout)[[:space:]]+truth)'
passive_auxiliaries='(is|are|was|were|be|being|been|has[[:space:]]+been|have[[:space:]]+been|had[[:space:]]+been|become|becomes)'
passive_connectors='(by|from|through|using|via|based[[:space:]]+on|on[[:space:]]+the[[:space:]]+basis[[:space:]]+of|according[[:space:]]+to)'
passive_subject_determiner='((the|a|an)[[:space:]]+)?'
positive_clause_connector='([,;][[:space:]]*|[[:space:]]+(and|but|yet)[[:space:]]+)'
authority_phrase="(${authority_targets}[[:space:]-]+authority|authority[[:space:]]+(for|over|of|within)[[:space:]]+${authority_targets})"
claim_predicate_verbs="(${readiness_claim_verbs}|${authority_verbs}|${claim_identity_verbs}|${authority_provider_verbs})"
coordinated_claim_predicate_verbs="${claim_predicate_verbs}"
missing_value='missing|mismatched|none|null|n/a|tbd|todo|unknown|unavailable|omitted|absent|blank|empty|withheld|placeholder|sample|not[[:space:]_-]*provided|not[[:space:]_-]*set|unsupported|unspecified'
absent_primary_value='no|false|nil'
structured_placeholder_value='missing|none|null|nil|no|false|n/a|tbd|todo|unknown|unavailable|omitted|absent|blank|empty|withheld|placeholder|sample|unsupported|unspecified|not([[:space:]_-]*(provided|set|available|known))?'
supported_export_formats='pdf|csv|json'
required_fields='journey_run_id|repository_revision|report_export_id|export_format|source_record_references|case_section_reference|action_section_reference|reconciliation_section_reference|rc_label_set|redaction_posture|limitation_references'
required_field_table_missing_any_cell_regex="(^|[[:space:]>*-])\|[[:space:]]*\`?(${required_fields})\`?[[:space:]]*\|.*(^|[[:space:]\`|])(${missing_value})([[:space:]_.-]+[^|]*)?(\||$)"
report_export_missing_subfield='((without|no)[[:space:]_-]+(timestamp|operator|export[[:space:]_-]*profile|profile)([[:space:].,;)]|$))'
export_format_missing_subfield='((without|no)[[:space:]_-]+(file[[:space:]_-]*name[[:space:]_-]*pattern|checksum|hash)([[:space:].,;)]|$))'
missing_evidence_subfield_regex="(^|[[:space:]>*-])\`?report_export_id\`?[[:space:]]*[:=][^.[:cntrl:]]*${report_export_missing_subfield}|(^|[[:space:]>*-])\`?export_format\`?[[:space:]]*[:=][^.[:cntrl:]]*${export_format_missing_subfield}"
missing_evidence_subfield_table_regex="(^|[[:space:]>*-])\|[[:space:]]*\`?report_export_id\`?[[:space:]]*\|.*${report_export_missing_subfield}|(^|[[:space:]>*-])\|[[:space:]]*\`?export_format\`?[[:space:]]*\|.*${export_format_missing_subfield}"
workstation_local_path='workstation[-_ ]local[[:space:]_-]+paths?'
workstation_local_unsafe_regex='((stores?|includes?|contains?|embeds?|carr(y|ies)|retains?|preserves?|exposes?)[[:space:]][^.[:cntrl:]]*workstation[-_ ]local[[:space:]_-]+paths?|records?[[:space:]]+(the[[:space:]]+)?workstation[-_ ]local[[:space:]_-]+paths?|workstation[-_ ]local[[:space:]_-]+paths?[^.[:cntrl:]]+(stored|included|embedded|carried|recorded|retained|preserved|exposed))'
workstation_local_safe_active_regex="((cannot|can[[:space:]]+not|does[[:space:]]+not|do[[:space:]]+not|did[[:space:]]+not|will[[:space:]]+not|must[[:space:]]+not|never)[[:space:]]+(store|include|contain|embed|carry|retain|preserve|expose|record)[^,;.[:cntrl:]]*${workstation_local_path})"
workstation_local_safe_passive_regex="(${workstation_local_path}[^,;.[:cntrl:]]*((is|are|was|were)[[:space:]]+)?(not[[:space:]]+(stored|included|contained|embedded|carried|recorded|retained|preserved|exposed)|excluded|redacted|masked|removed|omitted))"

repository_revision_value_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`[:space:],.;)]+|refs/remotes/[^`[:space:],.;)]+|remotes/[^`[:space:],.;)]+|origin/[^`[:space:],.;)]+|[^`[:space:],.;)]*branch)`?([[:space:].,;)]|$)'
repository_revision_assignment_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
repository_revision_mutable_suffix_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][^.[:cntrl:]]*[0-9a-f]{40}[^.[:cntrl:]]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)'
repository_revision_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?([^`|[:space:]]+)`?[[:space:]]*\|'
repository_revision_table_mutable_suffix_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?[^`|]*[0-9a-f]{40}[^`|]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)[^`|]*`?[[:space:]]*\|'
repository_revision_table_branch_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|.*([|[:space:]`(])((main|master|develop|development|trunk|head)([[:space:]_-]+branch)?|refs/heads/[^`|[:space:]]+|refs/remotes/[^`|[:space:]]+|remotes/[^`|[:space:]]+|origin/[^`|[:space:]]+|[[:alnum:]_.-]+[[:space:]_-]+branch)([[:space:]`.,;)|]|$)'
source_record_subordinate_reference='(report[[:space:]_-]*(text|output|metadata|labels?|artifacts?|exports?|files?)|generated[[:space:]_-]*((report[[:space:]_-]*)?(artifacts?|files?))|downloaded[[:space:]_-]*artifacts?|export[[:space:]_-]*(metadata|artifacts?|output)|screenshots?|browser[[:space:]_-]*state|ui[[:space:]_-]*(state|cache))'
source_record_shortcut_regex='(^|[[:space:]>*-])`?source_record_references`?[[:space:]]*[:=][^.[:cntrl:]]*'"${source_record_subordinate_reference}"
source_record_shortcut_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?source_record_references`?[[:space:]]*\|[[:space:]]*`?[^`|]*'"${source_record_subordinate_reference}"'[^`|]*`?[[:space:]]*\|'
source_record_shortcut_table_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?source_record_references`?[[:space:]]*\|.*'"${source_record_subordinate_reference}"
section_authority_terms='((closed|case[[:space:]_-]*closed|case[[:space:]_-]*closure|approval|approved|execution|executed|reconciliation|reconciled|override|truth)[^.;|[:cntrl:]]*(by|via|from|using)[[:space:]_-]+reports?|reports?[[:space:]_-]*(sections?|output)[^.;|[:cntrl:]]*(close|closed|closure|approve|approval|execute|execution|reconcile|reconciliation|override|truth))'
section_authority_regex="(^|[[:space:]>*-])\`?(case_section_reference|action_section_reference|reconciliation_section_reference)\`?[[:space:]]*[:=][^.[:cntrl:]]*${section_authority_terms}"
section_authority_table_regex="(^|[[:space:]>*-])\|[[:space:]]*\`?(case_section_reference|action_section_reference|reconciliation_section_reference)\`?[[:space:]]*\|[[:space:]]*\`?[^\`|]*${section_authority_terms}[^\`|]*\`?[[:space:]]*\|"
section_authority_table_any_cell_regex="(^|[[:space:]>*-])\|[[:space:]]*\`?(case_section_reference|action_section_reference|reconciliation_section_reference)\`?[[:space:]]*\|.*${section_authority_terms}"
label_missing_regex='(^|[[:space:]>*-])`?rc_label_set`?[[:space:]]*[:=][^.[:cntrl:]]*(missing|without|no[[:space:]_-]*labels?|production[[:space:]_-]*truth)'
label_missing_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?rc_label_set`?[[:space:]]*\|[[:space:]]*`?[^`|]*(missing|without|no[[:space:]_-]*labels?|production[[:space:]_-]*truth)[^`|]*`?[[:space:]]*\|'
label_missing_table_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?rc_label_set`?[[:space:]]*\|.*(missing|without|no[[:space:]_-]*labels?|production[[:space:]_-]*truth)'
rc_label_set_assignment_regex='(^|[[:space:]>*-])`?rc_label_set`?[[:space:]]*[:=][^.[:cntrl:]]+'
rc_label_set_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?rc_label_set`?[[:space:]]*\|[[:space:]]*`?([^`|]+)`?[[:space:]]*\|'
workflow_truth_label_regex='(^|[[:space:]`,;|])workflow[[:space:]_-]*truth([[:space:]`,;|.]|$)'
invalid_redaction_posture='(not[[:space:]_-]*needed|none|unredacted|raw[[:space:]_-]*secrets?|secrets?[[:space:]_-]*included|customer[-_ ]private[[:space:]_-]*payloads?|workstation[-_ ]local[[:space:]_-]*paths?[[:space:]_-]*included|pii[[:space:]_-]*(included|not[[:space:]_-]*redacted|unredacted)|((raw[[:space:]_-]+)?(credentials?|tokens?)[[:space:]_-]+(included|unredacted|not[[:space:]_-]*redacted|visible|exposed|present|retained|stored))|((included|unredacted|visible|exposed|retained|stored)[[:space:]_-]+(raw[[:space:]_-]+)?(credentials?|tokens?)))'
redaction_missing_regex='(^|[[:space:]>*-])`?redaction_posture`?[[:space:]]*[:=][^.[:cntrl:]]*'"${invalid_redaction_posture}"
redaction_missing_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?redaction_posture`?[[:space:]]*\|[[:space:]]*`?[^`|]*'"${invalid_redaction_posture}"'[^`|]*`?[[:space:]]*\|'
redaction_missing_table_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?redaction_posture`?[[:space:]]*\|.*'"${invalid_redaction_posture}"
limitation_hidden_regex='(^|[[:space:]>*-])`?limitation_references`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]_-]+in[[:space:]_-]+report[[:space:]_-]+text'
limitation_hidden_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?limitation_references`?[[:space:]]*\|[^|]*hidden[[:space:]_-]+in[[:space:]_-]+report[[:space:]_-]+text[^|]*\|'
limitation_hidden_table_any_cell_regex='(^|[[:space:]>*-])\|[[:space:]]*`?limitation_references`?[[:space:]]*\|.*hidden[[:space:]_-]+in[[:space:]_-]+report[[:space:]_-]+text'
incomplete_export_evidence_regex='export[[:space:]_-]+evidence[^.[:cntrl:]]*(incomplete|partial|missing|unavailable|not[[:space:]_-]+complete)|(incomplete|partial|missing|unavailable|not[[:space:]_-]+complete)[^.[:cntrl:]]*export[[:space:]_-]+evidence'
customer_private_prohibition_regex='((must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include|fail[s]?[[:space:]]+the[[:space:]]+proof)[^.[:cntrl:]]*customer[-_ ]private|customer[-_ ]private[^.[:cntrl:]]*fail[s]?[[:space:]]+the[[:space:]]+proof)'
customer_private_unsafe_regex='(includes|contains|embeds|carries|stores|exposes?)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(examples?|tickets?|alerts?|logs?|chats?|payloads?|exports?)([[:space:].,;)]|[[:space:]]+(are|were|was|is)[[:space:]]+(stored|included|embedded|carried|exposed))|raw[[:space:]]+customer[[:space:]]+data[[:space:]]+(is|are|was|were)[[:space:]]+(stored|included|embedded|carried|exposed)|unredacted[[:space:]]+customer[[:space:]]+(tickets?|alerts?|logs?|chats?|payloads?|exports?|data)([[:space:].,;)]|$)'
safe_customer_private_redaction_regex='customer[-_ ]private[[:space:]]+(data|examples?|tickets?|alerts?|logs?|chats?|payloads?|exports?)[^,;.[:cntrl:]]+(redacted|masked|removed|omitted|not[[:space:]_-]*stored)'
canonical_journey_run_id_row='| `journey_run_id` | the phase 66.1 run identifier that observed the export. | missing or mismatched run identifiers fail the proof. |'
canonical_repository_revision_row='| `repository_revision` | immutable repository revision for the proof packet. | mutable branch names fail the proof. |'
canonical_report_export_id_row='| `report_export_id` | reviewed report export identifier, timestamp, operator, and export profile. | missing export identity or placeholder export ids fail the proof. |'
canonical_export_format_row='| `export_format` | bounded export format, file name pattern, and checksum or hash reference. | unsupported or unspecified export formats fail the proof. |'
canonical_source_record_references_row='| `source_record_references` | direct aegisops references for source alert, case, evidence, approval, action request, execution receipt, and reconciliation records. | report text, screenshots, browser state, or ui cache cannot create source-record truth. |'
canonical_rc_label_set_row='| `rc_label_set` | required labels `rc-evidence`, `phase-66`, `report-export`, and `not-workflow-truth`. | missing rc labels or production-truth labels fail the proof. |'
canonical_redaction_posture_row='| `redaction_posture` | secret, credential, customer-private data, workstation-local path, and pii redaction posture. | raw secrets, customer-private payloads, and workstation-local paths fail the proof. |'
canonical_limitation_references_row='| `limitation_references` | known limitation ids, owner, decision date, and follow-up date when export evidence is incomplete. | missing limitations cannot be hidden in report text. |'
canonical_case_section_reference_row='| `case_section_reference` | reviewed case section containing status, evidence links, owner, and limitation references. | report sections cannot close cases or override case records. |'
canonical_action_section_reference_row='| `action_section_reference` | reviewed action section containing approval, delegated action request, execution receipt, and mismatch posture. | report sections cannot approve, execute, or reconcile actions. |'
canonical_reconciliation_section_reference_row='| `reconciliation_section_reference` | reviewed reconciliation section binding receipt, outcome, mismatch state, follow-up owner, and linked record. | report sections cannot become reconciliation truth. |'
canonical_claim_rejection_line='the proof must reject missing report identity, missing source record references, missing case/action/reconciliation sections, missing rc labels, missing redaction posture, missing limitation references, report-as-truth claims, report-driven case closure, report-driven action execution, report-driven reconciliation, workstation-local paths, production secrets, customer-private data, compliance certification claims, customer portal readiness claims, production sla reporting claims, inferred rc pass, inferred ga pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.'

is_canonical_evidence_row() {
  local line_lower="$1"

  case "${line_lower}" in
    "${canonical_journey_run_id_row}"|"${canonical_repository_revision_row}"|"${canonical_report_export_id_row}"|"${canonical_export_format_row}"|"${canonical_source_record_references_row}"|"${canonical_case_section_reference_row}"|"${canonical_action_section_reference_row}"|"${canonical_reconciliation_section_reference_row}"|"${canonical_rc_label_set_row}"|"${canonical_redaction_posture_row}"|"${canonical_limitation_references_row}")
      return 0
      ;;
  esac
  return 1
}

is_canonical_claim_scan_exemption() {
  local line_lower="$1"

  line_lower="${line_lower#"${line_lower%%[![:space:]]*}"}"
  line_lower="${line_lower%"${line_lower##*[![:space:]]}"}"
  is_canonical_evidence_row "${line_lower}" || [[ "${line_lower}" == "${canonical_claim_rejection_line}" ]]
}

is_safe_customer_private_redaction_line() {
  local line_lower="$1"
  local sanitized_line="${line_lower}"
  local safe_posture_found=0

  while [[ "${sanitized_line}" =~ ${safe_customer_private_redaction_regex} ]]; do
    safe_posture_found=1
    sanitized_line="${sanitized_line/"${BASH_REMATCH[0]}"/safe-customer-private-posture}"
  done
  ((safe_posture_found == 1)) || return 1

  if [[ "${sanitized_line}" =~ ${customer_private_unsafe_regex} ]] ||
    [[ "${sanitized_line}" =~ customer[-_\ ]private[-_\ ]data[[:space:]]*[:=] ]] ||
    [[ "${sanitized_line}" =~ safe-customer-private-posture[^.[:cntrl:]]*(and|but|yet)[[:space:]]+((is|are|was|were)[[:space:]]+)?(stored|included|embedded|carried|recorded|retained|preserved|exposed) ]]; then
    return 1
  fi
  return 0
}

line_has_unsafe_workstation_path() {
  local line_lower="$1"
  local sanitized_line="${line_lower}"

  while [[ "${sanitized_line}" =~ ${workstation_local_safe_active_regex} ]]; do
    sanitized_line="${sanitized_line/"${BASH_REMATCH[0]}"/safe-workstation-path-posture}"
  done
  while [[ "${sanitized_line}" =~ ${workstation_local_safe_passive_regex} ]]; do
    sanitized_line="${sanitized_line/"${BASH_REMATCH[0]}"/safe-workstation-path-posture}"
  done
  [[ "${sanitized_line}" =~ ${workstation_local_unsafe_regex} ]]
}

# Claim policy is grouped by semantic role so each wording form shares one vocabulary.
readiness_forbidden_patterns=(
  "${readiness_claim_subjects}${readiness_claim_bridge}${readiness_claim_verbs}${readiness_claim_bridge}${readiness_claim_outcomes}([[:space:][:punct:]]|$)"
  "${readiness_claim_subjects}${readiness_claim_bridge}${readiness_claim_verbs}[[:space:]]+(the[[:space:]]+)?${readiness_terminal_outcomes}[[:space:]]*([.,;:!?)]|\`|$)"
  "${readiness_claim_outcomes}([[:space:][:punct:]]|$)[^.[:cntrl:]]*${passive_auxiliaries}[[:space:]]+${readiness_passive_claim_verbs}[[:space:]]+${passive_connectors}[[:space:]]+${passive_subject_determiner}${readiness_claim_subjects}([[:space:][:punct:]]|$)"
  "(${readiness_claim_subjects}|aegisops)([^.[:cntrl:]]+)?[[:space:]]+${claim_identity_verbs}[[:space:]]+(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?${readiness_identity_outcomes}([[:space:][:punct:]]|$)"
  "${readiness_claim_subjects}[^.[:cntrl:]]*${positive_clause_connector}${readiness_claim_verbs}${readiness_claim_bridge}${readiness_claim_outcomes}([[:space:][:punct:]]|$)"
  "${readiness_claim_subjects}[^.[:cntrl:]]*${positive_clause_connector}${readiness_claim_verbs}[[:space:]]+(the[[:space:]]+)?${readiness_terminal_outcomes}[[:space:]]*([.,;:!?)]|\`|$)"
)

truth_forbidden_patterns=(
  "${subordinate_subjects}[^.[:cntrl:]]*[[:space:]]+(${claim_identity_verbs}|creates?|created)[[:space:]]+(the[[:space:]]+)?(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?${truth_targets}"
  "${truth_targets}[^.[:cntrl:]]+${passive_auxiliaries}[[:space:]]+(created|established|defined|determined|set|derived)[[:space:]]+${passive_connectors}[[:space:]]+[^.[:cntrl:]]*${subordinate_subjects}"
  "${subordinate_subjects}${readiness_claim_bridge}${readiness_claim_verbs}${readiness_claim_bridge}${truth_targets}"
  "${subordinate_subjects}[^.[:cntrl:]]*[[:space:]]+${claim_identity_verbs}[[:space:]]+(the[[:space:]]+)?(case[[:space:]-]+closure|action[[:space:]-]+execution|action[[:space:]-]+approval|reconciliation)"
)

authority_forbidden_patterns=(
  "${subordinate_subjects}${readiness_claim_bridge}${authority_verbs}[[:space:]]+(the[[:space:]]+)?${authority_objects}([[:space:][:punct:]]|$)"
  "${subordinate_subjects}[^.[:cntrl:]]*${positive_clause_connector}${authority_verbs}[[:space:]]+(the[[:space:]]+)?${authority_objects}([[:space:][:punct:]]|$)"
  "${authority_objects}[^.[:cntrl:]]+${passive_auxiliaries}[[:space:]]+${authority_passive_verbs}[[:space:]]+${passive_connectors}[[:space:]]+[^.[:cntrl:]]*${subordinate_subjects}"
  "${subordinate_subjects}[^.[:cntrl:]]+${authority_provider_verbs}[[:space:]]+(the[[:space:]]+)?${authority_phrase}"
  "${subordinate_subjects}[^.[:cntrl:]]+[[:space:]]+${claim_identity_verbs}[[:space:]]+(the[[:space:]]+)?${authority_phrase}"
  "${subordinate_subjects}[^.[:cntrl:]]+${claim_identity_verbs}[^.[:cntrl:]]+authoritative[[:space:]]+(for|over|as)[^.[:cntrl:]]*${authority_objects}"
)

claim_candidate_regex="(${readiness_claim_outcomes}|${readiness_identity_outcomes}|(^|[[:space:]])${readiness_terminal_outcomes}([[:space:][:punct:]]|$)|${truth_targets}|(^|[[:space:][:punct:]])(${authority_verbs}|${authority_passive_verbs}|${authority_provider_verbs})([[:space:][:punct:]]|$)|authoritative|authority|case[[:space:]-]+closure|action[[:space:]-]+execution|action[[:space:]-]+approval|reconciliation)"

line_has_forbidden_claim() {
  local claim_line="$1"
  local pattern

  forbidden_claim_match=""
  if [[ "${claim_line}" =~ ${readiness_claim_subjects} ]] &&
    [[ "${claim_line}" =~ (${readiness_claim_outcomes}|${readiness_identity_outcomes}|(^|[[:space:]])${readiness_terminal_outcomes}([[:space:][:punct:]]|$)) ]]; then
    for pattern in "${readiness_forbidden_patterns[@]}"; do
      if [[ "${claim_line}" =~ ${pattern} ]]; then
        forbidden_claim_match="${BASH_REMATCH[0]}"
        return 0
      fi
    done
  fi
  if [[ "${claim_line}" =~ ${subordinate_subjects} ]] &&
    [[ "${claim_line}" =~ (truth|case[[:space:]-]+closure|action[[:space:]-]+execution|action[[:space:]-]+approval|reconciliation) ]]; then
    for pattern in "${truth_forbidden_patterns[@]}"; do
      if [[ "${claim_line}" =~ ${pattern} ]]; then
        forbidden_claim_match="${BASH_REMATCH[0]}"
        return 0
      fi
    done
  fi
  if [[ "${claim_line}" =~ ${subordinate_subjects} ]]; then
    for pattern in "${authority_forbidden_patterns[@]}"; do
      if [[ "${claim_line}" =~ ${pattern} ]]; then
        forbidden_claim_match="${BASH_REMATCH[0]}"
        return 0
      fi
    done
  fi
  return 1
}

is_source_record_reference_line() {
  local line_lower="$1"

  [[ "${line_lower}" =~ (^|[[:space:]>*-])\`?source_record_references\`?[[:space:]]*[:=] ]] || [[ "${line_lower}" =~ (^|[[:space:]>*-])\|[[:space:]]*\`?source_record_references\`?[[:space:]]*\| ]]
}

has_complete_source_record_references() {
  local line_lower="$1"

  if tr ',;|' '\n' <<<"${line_lower}" | grep -Eq -- '^[[:space:]]*(`?source_record_references`?[[:space:]]*[:=][[:space:]]*)?(no|without|not[[:space:]_-]+(provided|available|linked|referenced))[[:space:]_-]+(source[[:space:]_-]*alert|case([[:space:]_-]+record)?|evidence([[:space:]_-]+record)?|approval([[:space:]_-]+record)?|action[[:space:]_-]*request([[:space:]_-]+record)?|execution[[:space:]_-]*receipt([[:space:]_-]+record)?|reconciliation([[:space:]_-]+record)?)'; then
    return 1
  fi

  has_reference_identifier "${line_lower}" 'source[[:space:]_-]*alert[[:space:]_-]*record|source[[:space:]_-]*alert|alert[[:space:]_-]*record|alert' &&
    has_reference_identifier "${line_lower}" 'case[[:space:]_-]*record|case' &&
    has_reference_identifier "${line_lower}" 'evidence[[:space:]_-]*record|evidence' &&
    has_reference_identifier "${line_lower}" 'approval[[:space:]_-]*record|approval' &&
    has_reference_identifier "${line_lower}" 'action[[:space:]_-]*request[[:space:]_-]*record|action[[:space:]_-]*request' &&
    has_reference_identifier "${line_lower}" 'execution[[:space:]_-]*receipt[[:space:]_-]*record|execution[[:space:]_-]*receipt' &&
    has_reference_identifier "${line_lower}" 'reconciliation[[:space:]_-]*record|reconciliation'
}

is_named_evidence_field_line() {
  local field_name="$1"
  local line_lower="$2"
  local field_line_regex

  field_line_regex='(^|[[:space:]>*-])`?'"${field_name}"'`?[[:space:]]*[:=]|(^|[[:space:]>*-])\|[[:space:]]*`?'"${field_name}"'`?[[:space:]]*\|'
  [[ "${line_lower}" =~ ${field_line_regex} ]]
}

named_evidence_primary_value() {
  local field_name="$1"
  local line_lower="$2"
  local assignment_regex
  local table_regex

  assignment_regex='(^|[[:space:]>*-])`?'"${field_name}"'`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],;|]+)'
  table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?'"${field_name}"'`?[[:space:]]*\|[[:space:]]*`?([^`|[:space:]]+)'
  if [[ "${line_lower}" =~ ${assignment_regex} ]]; then
    printf '%s\n' "${BASH_REMATCH[2]}"
    return 0
  fi
  if [[ "${line_lower}" =~ ${table_regex} ]]; then
    printf '%s\n' "${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

is_valid_evidence_primary_value() {
  local value="$1"

  [[ "${value}" =~ ^[[:alnum:]][[:alnum:]_.:/-]*$ ]] || return 1
  [[ ! "${value}" =~ ^(${missing_value}|${absent_primary_value})$ ]] || return 1
  case "${value}" in
    alert|case|evidence|approval|action|request|execution|receipt|reconciliation|record|records|reference|references|id|identifier|only|reviewed|known|value|section|status|owner|timestamp|operator|profile|file|format|checksum|hash|bounded)
      return 1
      ;;
  esac
  return 0
}

has_named_evidence_primary_value() {
  local line_lower="$1"
  local field_name="$2"
  local value

  value="$(named_evidence_primary_value "${field_name}" "${line_lower}")" || return 1
  is_valid_evidence_primary_value "${value}"
}

is_valid_iso_date() {
  local value="$1"
  local year
  local month
  local day
  local max_day

  [[ "${value}" =~ ^([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$ ]] || return 1
  year=$((10#${BASH_REMATCH[1]}))
  month=$((10#${BASH_REMATCH[2]}))
  day=$((10#${BASH_REMATCH[3]}))
  ((year > 0)) || return 1

  case "${month}" in
    2)
      max_day=28
      if ((year % 400 == 0 || (year % 4 == 0 && year % 100 != 0))); then
        max_day=29
      fi
      ;;
    4|6|9|11)
      max_day=30
      ;;
    *)
      max_day=31
      ;;
  esac
  ((day <= max_day))
}

is_valid_rfc3339_timestamp() {
  local value="$1"
  local date_value

  [[ "${value}" =~ ^([0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]))t([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$ ]] || return 1
  date_value="${BASH_REMATCH[1]}"
  is_valid_iso_date "${date_value}"
}

is_valid_checksum_reference() {
  local value="$1"
  local checksum_algorithm='(md5|sha-?(1|224|256|384|512)|blake2(b|s)?)'

  if [[ "${value}" =~ ^${checksum_algorithm}: ]]; then
    [[ "${value}" =~ ^${checksum_algorithm}:[0-9a-f]{8,}$ ]]
    return
  fi
  if [[ "${value}" =~ ^[0-9a-f]{8,}$ ]]; then
    return 0
  fi
  [[ "${value}" =~ ^[[:alnum:]][[:alnum:]_.:/-]*[[:alnum:]]$ ]] &&
    [[ "${value}" =~ [0-9] ]] &&
    [[ "${value}" =~ [._:/-] ]]
}

is_valid_non_subordinate_reference() {
  local value="$1"

  [[ ! "${value}" =~ ^(${structured_placeholder_value})([^[:alnum:]].*)?$ ]] &&
    [[ ! "${value}" =~ ${source_record_subordinate_reference} ]]
}

is_valid_structured_subfield_value() {
  local value="$1"
  local validator="${2:-generic}"

  case "${validator}" in
    generic)
      [[ ! "${value}" =~ ^(${structured_placeholder_value})([^[:alnum:]].*)?$ ]]
      ;;
    iso-date)
      is_valid_iso_date "${value}"
      ;;
    mismatch-state)
      [[ "${value}" =~ ^(none|matched|mismatched)$ ]]
      ;;
    checksum-reference)
      is_valid_checksum_reference "${value}"
      ;;
    non-subordinate-reference)
      is_valid_non_subordinate_reference "${value}"
      ;;
    rfc3339-timestamp)
      is_valid_rfc3339_timestamp "${value}"
      ;;
    *)
      return 1
      ;;
  esac
}

structured_subfield_value() {
  local line_lower="$1"
  local label_regex="$2"
  local structured_value_regex
  local value
  local value_index

  structured_value_regex='(^|[[:space:],;|])('"${label_regex}"')[[:space:]]*[:=][[:space:]]*`?([^[:space:]`,;|]+)'
  [[ "${line_lower}" =~ ${structured_value_regex} ]] || return 1
  value_index=$((${#BASH_REMATCH[@]} - 1))
  value="${BASH_REMATCH[${value_index}]}"
  printf '%s\n' "${value}"
}

has_structured_subfield_value() {
  local line_lower="$1"
  local label_regex="$2"
  local validator="${3:-generic}"
  local value

  value="$(structured_subfield_value "${line_lower}" "${label_regex}")" || return 1
  is_valid_structured_subfield_value "${value}" "${validator}"
}

has_required_structured_subfields() {
  local line_lower="$1"
  local subfield_spec
  local label_regex
  local validator
  shift

  for subfield_spec in "$@"; do
    label_regex="${subfield_spec%%::*}"
    validator="generic"
    if [[ "${subfield_spec}" == *"::"* ]]; then
      validator="${subfield_spec#*::}"
    fi
    has_structured_subfield_value "${line_lower}" "${label_regex}" "${validator}" || return 1
  done
}

has_complete_report_export_identity() {
  local line_lower="$1"
  local primary_value

  primary_value="$(named_evidence_primary_value "report_export_id" "${line_lower}")" &&
    is_valid_evidence_primary_value "${primary_value}" &&
    [[ ! "${primary_value}" =~ ^(timestamp|operator|export[[:space:]_-]*profile|profile)([:=_-]|$) ]] &&
    has_required_structured_subfields "${line_lower}" \
      '(export[[:space:]_-]*)?timestamp::rfc3339-timestamp' \
      '(export[[:space:]_-]*)?operator([[:space:]_-]*(id|reference|ref))?' \
      '(export[[:space:]_-]*)?profile([[:space:]_-]*(id|reference|ref))?'
}

is_supported_export_format() {
  local value="$1"

  [[ "${value}" =~ ^(${supported_export_formats})$ ]]
}

is_export_file_name_compatible() {
  local export_format="$1"
  local file_name_pattern="$2"

  case "${export_format}" in
    pdf)
      [[ "${file_name_pattern}" =~ \.pdf$ ]]
      ;;
    csv)
      [[ "${file_name_pattern}" =~ \.csv$ ]]
      ;;
    json)
      [[ "${file_name_pattern}" =~ \.json$ ]]
      ;;
    *)
      return 1
      ;;
  esac
}

has_complete_export_format() {
  local line_lower="$1"
  local file_name_pattern
  local primary_value

  primary_value="$(named_evidence_primary_value "export_format" "${line_lower}")" &&
    is_valid_evidence_primary_value "${primary_value}" &&
    is_supported_export_format "${primary_value}" &&
    [[ ! "${primary_value}" =~ ^(file[[:space:]_-]*name[[:space:]_-]*pattern|filename[[:space:]_-]*pattern|checksum|hash|format|bounded)([:=_-]|$) ]] &&
    file_name_pattern="$(structured_subfield_value "${line_lower}" '(file[[:space:]_-]*name|filename)[[:space:]_-]*pattern')" &&
    is_valid_structured_subfield_value "${file_name_pattern}" &&
    is_export_file_name_compatible "${primary_value}" "${file_name_pattern}" &&
    has_structured_subfield_value "${line_lower}" '(checksum|hash)([[:space:]_-]*(reference|ref))?' 'checksum-reference'
}

has_reference_identifier() {
  local line_lower="$1"
  local label_regex="$2"
  local reference_regex
  local reference_id

  reference_regex='(^|[[:space:],;|`])('"${label_regex}"')[[:space:]_-]+([[:alnum:]][[:alnum:]_.:/-]*)'
  [[ "${line_lower}" =~ ${reference_regex} ]] || return 1
  reference_id="${BASH_REMATCH[3]}"
  is_valid_evidence_primary_value "${reference_id}"
}

has_complete_section_reference() {
  local line_lower="$1"
  local field_name="$2"
  local primary_value
  local -a required_subfields

  primary_value="$(named_evidence_primary_value "${field_name}" "${line_lower}")" || return 1
  is_valid_non_subordinate_reference "${primary_value}" || return 1
  case "${field_name}" in
    case_section_reference)
      required_subfields=(
        'status'
        'evidence[[:space:]_-]*(links?|references?|refs?)'
        'owner([[:space:]_-]*(id|reference|ref))?'
        'limitation([[:space:]_-]*(references?|refs?|ids?))?'
      )
      ;;
    action_section_reference)
      required_subfields=(
        'approval([[:space:]_-]*(record|id|reference|ref))?::non-subordinate-reference'
        'delegated[[:space:]_-]+action[[:space:]_-]*request([[:space:]_-]*(record|id|reference|ref))?::non-subordinate-reference'
        'execution[[:space:]_-]*receipt([[:space:]_-]*(record|id|reference|ref))?::non-subordinate-reference'
        'mismatch[[:space:]_-]*(posture|state)::mismatch-state'
      )
      ;;
    reconciliation_section_reference)
      required_subfields=(
        '(execution[[:space:]_-]*)?receipt([[:space:]_-]*(record|id|reference|ref))?::non-subordinate-reference'
        'outcome::non-subordinate-reference'
        'mismatch[[:space:]_-]*(posture|state)::mismatch-state'
        'follow[[:space:]_-]*up[[:space:]_-]*owner([[:space:]_-]*(id|reference|ref))?'
        'linked[[:space:]_-]*record([[:space:]_-]*(id|reference|ref))?::non-subordinate-reference'
      )
      ;;
    *)
      return 1
      ;;
  esac
  has_required_structured_subfields "${line_lower}" "${required_subfields[@]}"
}

has_safe_redaction_class() {
  local line_lower="$1"
  local class_regex="$2"
  local safe_posture_regex
  local class_posture_regex

  safe_posture_regex='(redacted|masked|removed|omitted|excluded|not[[:space:]_-]*(stored|retained|included|exported|present))'
  class_posture_regex='(^|[[:space:],;|])('"${class_regex}"')([[:space:]_-]+posture)?([[:space:]]*[:=][[:space:]]*|[[:space:]]+)'"${safe_posture_regex}"'([[:space:].,;|]|$)'
  [[ "${line_lower}" =~ ${class_posture_regex} ]]
}

has_complete_redaction_posture() {
  local line_lower="$1"

  has_safe_redaction_class "${line_lower}" 'secrets?' &&
    has_safe_redaction_class "${line_lower}" 'credentials?' &&
    has_safe_redaction_class "${line_lower}" 'customer[-_ ]private([[:space:]_-]+data)?' &&
    has_safe_redaction_class "${line_lower}" 'workstation[-_ ]local[[:space:]_-]+paths?' &&
    has_safe_redaction_class "${line_lower}" 'pii'
}

has_complete_limitation_references() {
  local line_lower="$1"

  has_named_evidence_primary_value "${line_lower}" "limitation_references" || return 1
  if [[ "${line_lower}" =~ ${incomplete_export_evidence_regex} ]]; then
    has_required_structured_subfields "${line_lower}" \
      'owner([[:space:]_-]*(id|reference|ref))?' \
      'decision[[:space:]_-]*date::iso-date' \
      'follow[[:space:]_-]*up[[:space:]_-]*date::iso-date'
    return
  fi
  return 0
}

normalize_negated_claims() {
  local line_lower="$1"
  local normalized_line
  local markdown_asterisk_regex
  local markdown_strikethrough_regex
  local markdown_underscore_regex
  local negation_marker_regex
  local negated_list_claim_regex
  local negated_claim_regex
  local comma_negated_claim_regex
  local or_negated_claim_regex
  local matched_prefix
  local matched_span
  local remaining_line

  normalized_line="${line_lower}"
  markdown_asterisk_regex='\*+([^*]+)\*+'
  markdown_strikethrough_regex='~+([^~]+)~+'
  markdown_underscore_regex='(^|[^[:alnum:]_])_+([^_]+)_+([^[:alnum:]_]|$)'
  while [[ "${normalized_line}" =~ ${markdown_asterisk_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/${BASH_REMATCH[1]}}"
  done
  while [[ "${normalized_line}" =~ ${markdown_strikethrough_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/${BASH_REMATCH[1]}}"
  done
  while [[ "${normalized_line}" =~ ${markdown_underscore_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}}"
  done

  negation_marker_regex='cannot|can[[:space:]]+not|does[[:space:]]+not|do[[:space:]]+not|did[[:space:]]+not|will[[:space:]]+not|must[[:space:]]+not|never'
  if [[ ! "${normalized_line}" =~ ${negation_marker_regex} ]]; then
    normalized_claim_line="${normalized_line}"
    return
  fi

  negated_list_claim_regex="(cannot|can[[:space:]]+not|does[[:space:]]+not|do[[:space:]]+not|did[[:space:]]+not|will[[:space:]]+not|must[[:space:]]+not|never)[[:space:]]+${coordinated_claim_predicate_verbs}"
  negated_claim_regex="(cannot|can[[:space:]]+not|does[[:space:]]+not|do[[:space:]]+not|did[[:space:]]+not|will[[:space:]]+not|must[[:space:]]+not|never)[[:space:]]+${claim_predicate_verbs}"
  while [[ "${normalized_line}" =~ ${negated_list_claim_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/negated-list-claim}"
  done
  while [[ "${normalized_line}" =~ ${negated_claim_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/negated-claim}"
  done

  comma_negated_claim_regex="(negated-list-claim[^.[:cntrl:]]*,[[:space:]]*)${coordinated_claim_predicate_verbs}"
  while [[ "${normalized_line}" =~ ${comma_negated_claim_regex} ]]; do
    matched_span="${BASH_REMATCH[0]}"
    matched_prefix="${BASH_REMATCH[1]}"
    remaining_line="${normalized_line#*"${matched_span}"}"
    if [[ ! "${remaining_line}" =~ ^[^.[:cntrl:]]*([,][[:space:]]*)?(or|nor)[[:space:]]+${coordinated_claim_predicate_verbs} ]]; then
      break
    fi
    normalized_line="${normalized_line/"${matched_span}"/${matched_prefix}negated-list-claim}"
  done

  or_negated_claim_regex="(negated-list-claim[^.[:cntrl:]]*[[:space:]]+(or|nor)[[:space:]]+)${coordinated_claim_predicate_verbs}"
  while [[ "${normalized_line}" =~ ${or_negated_claim_regex} ]]; do
    normalized_line="${normalized_line/"${BASH_REMATCH[0]}"/${BASH_REMATCH[1]}negated-list-claim}"
  done
  normalized_claim_line="${normalized_line}"
}

phase_reference_regex='phase[[:space:]_-]+[0-9]+([.[:space:]_-]+[0-9]+)?'

forbidden_claim_is_scoped() {
  local claim_line="$1"
  local claim_match="$2"
  local scope_regex="$3"
  local claim_prefix
  local phase_reference
  local remaining_prefix
  local scope_active=0

  if [[ "${claim_match}" =~ ${scope_regex} ]]; then
    return 0
  fi

  claim_prefix="${claim_line%%"${claim_match}"*}"
  remaining_prefix="${claim_prefix}"
  while [[ "${remaining_prefix}" =~ ${phase_reference_regex} ]]; do
    phase_reference="${BASH_REMATCH[0]}"
    if [[ "${phase_reference}" =~ ${scope_regex} ]]; then
      scope_active=1
    else
      scope_active=0
    fi
    remaining_prefix="${remaining_prefix#*"${phase_reference}"}"
  done
  ((scope_active == 1))
}

scan_forbidden_claims() {
  local file="$1"
  local description="$2"
  local scope_regex="${3:-}"
  local claim_line_lower
  local line_lower

  while IFS= read -r line_lower; do
    if is_canonical_claim_scan_exemption "${line_lower}"; then
      continue
    fi
    if [[ -n "${scope_regex}" ]] && [[ ! "${line_lower}" =~ phase|phase-66-5-report-export-rc-proof ]]; then
      continue
    fi
    normalize_negated_claims "${line_lower}"
    claim_line_lower="${normalized_claim_line}"
    if [[ -n "${scope_regex}" ]] && [[ ! "${claim_line_lower}" =~ ${scope_regex} ]]; then
      continue
    fi
    if line_has_forbidden_claim "${claim_line_lower}"; then
      if [[ -z "${scope_regex}" ]] || forbidden_claim_is_scoped "${claim_line_lower}" "${forbidden_claim_match}" "${scope_regex}"; then
        echo "Forbidden Phase 66.5 ${description} claim matched" >&2
        exit 1
      fi
    fi
  done < <(lower_visible_text "${file}" | grep -E -- "${claim_candidate_regex}")

  while IFS= read -r line_lower; do
    if is_canonical_claim_scan_exemption "${line_lower}"; then
      continue
    fi
    if [[ -n "${scope_regex}" ]] && [[ ! "${line_lower}" =~ phase|phase-66-5-report-export-rc-proof ]]; then
      continue
    fi
    normalize_negated_claims "${line_lower}"
    claim_line_lower="${normalized_claim_line}"
    if [[ -n "${scope_regex}" ]] && [[ ! "${claim_line_lower}" =~ ${scope_regex} ]]; then
      continue
    fi
    if line_has_forbidden_claim "${claim_line_lower}"; then
      if [[ -z "${scope_regex}" ]] || forbidden_claim_is_scoped "${claim_line_lower}" "${forbidden_claim_match}" "${scope_regex}"; then
        echo "Forbidden Phase 66.5 ${description} claim matched" >&2
        exit 1
      fi
    fi
  done < <(lower_visible_text "${file}" | awk '!/^[[:space:]]*\|/ && NF { paragraph = paragraph " " $0; next } paragraph != "" { print paragraph; paragraph = "" } END { if (paragraph != "") print paragraph }' | grep -E -- "${claim_candidate_regex}")
}

secret_looking_value_regex='authorization[[:space:]]*:[[:space:]]*(bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|basic[[:space:]]+[A-Za-z0-9+/=]{12,})|(bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|basic[[:space:]]+[A-Za-z0-9+/=]{12,})|[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}|(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}'
if perl -pe 's/(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?(redacted|masked|removed|omitted|not[[:space:]_-]*stored)`?([[:space:].,;)]|$)/redacted_credential_posture /ig' "${absolute_doc_path}" | grep -Eiq -- "${secret_looking_value_regex}"; then
  echo "Forbidden Phase 66.5 report export RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- '(includes|contains|embeds|carries|stores|exposes?)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(data|example|ticket|alert|log|chat|payload|export)|raw[[:space:]]+customer[[:space:]]+data[[:space:]]+(is|are|was|were)[[:space:]]+(stored|included|embedded|carried|exposed)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' < <(perl -0ne 'while (/<!--(.*?)-->/gs) { print "$1\n" }' "${absolute_doc_path}" | tr '[:upper:]' '[:lower:]'); then
  echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
  exit 1
fi

while IFS= read -r line_lower; do
  if line_has_unsafe_workstation_path "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: workstation-local path evidence detected" >&2
    exit 1
  fi
done < <(perl -0ne 'while (/<!--(.*?)-->/gs) { print "$1\n" }' "${absolute_doc_path}" | tr '[:upper:]' '[:lower:]')

if grep -Eq -- "(^|[[:space:]>*-])\`?(${required_fields})\`?[[:space:]]*[:=][[:space:]]*\`?(${absent_primary_value})\`?([[:space:]]*[.,;)]|[[:space:]]*$)" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\|[[:space:]]*\`?(${required_fields})\`?[[:space:]]*\|[[:space:]]*\`?(${absent_primary_value})\`?[[:space:]]*\|" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\`?(${required_fields})\`?[[:space:]]*[:=][^.[:cntrl:]]*(^|[[:space:]\`])(${missing_value})([[:space:]_.-]+[^.[:cntrl:]]*)?([[:space:].,;)]|$)" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "${missing_evidence_subfield_regex}|${missing_evidence_subfield_table_regex}" < <(lower_visible_text "${absolute_doc_path}"); then
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

if grep -Eq -- "${limitation_hidden_regex}|${limitation_hidden_table_regex}" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
  exit 1
fi

while IFS= read -r line_lower; do
  if ! is_canonical_evidence_row "${line_lower}" && [[ "${line_lower}" =~ ${required_field_table_missing_any_cell_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
    exit 1
  fi
  if is_canonical_evidence_row "${line_lower}"; then
    continue
  fi
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
  if is_named_evidence_field_line "report_export_id" "${line_lower}" && ! has_complete_report_export_identity "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
    exit 1
  fi
  if is_named_evidence_field_line "export_format" "${line_lower}" && ! has_complete_export_format "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${source_record_shortcut_regex} ]] || [[ "${line_lower}" =~ ${source_record_shortcut_table_regex} ]] || { [[ "${line_lower}" != "${canonical_source_record_references_row}" ]] && [[ "${line_lower}" =~ ${source_record_shortcut_table_any_cell_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid source record reference detected" >&2
    exit 1
  fi
  if is_source_record_reference_line "${line_lower}" && ! has_complete_source_record_references "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: incomplete source record references detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" != "${canonical_limitation_references_row}" ]] && { [[ "${line_lower}" =~ ${limitation_hidden_regex} ]] || [[ "${line_lower}" =~ ${limitation_hidden_table_regex} ]] || [[ "${line_lower}" =~ ${limitation_hidden_table_any_cell_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
    exit 1
  fi
  if is_named_evidence_field_line "limitation_references" "${line_lower}" && ! has_complete_limitation_references "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" != "${canonical_case_section_reference_row}" ]] && [[ "${line_lower}" != "${canonical_action_section_reference_row}" ]] && [[ "${line_lower}" != "${canonical_reconciliation_section_reference_row}" ]] && { [[ "${line_lower}" =~ ${section_authority_regex} ]] || [[ "${line_lower}" =~ ${section_authority_table_regex} ]] || [[ "${line_lower}" =~ ${section_authority_table_any_cell_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: report section authority detected" >&2
    exit 1
  fi
  for section_field in case_section_reference action_section_reference reconciliation_section_reference; do
    if is_named_evidence_field_line "${section_field}" "${line_lower}" && ! has_complete_section_reference "${line_lower}" "${section_field}"; then
      echo "Forbidden Phase 66.5 report export RC proof: missing required evidence value detected" >&2
      exit 1
    fi
  done
  if [[ "${line_lower}" =~ ${label_missing_regex} ]] || [[ "${line_lower}" =~ ${label_missing_table_regex} ]] || { [[ "${line_lower}" != "${canonical_rc_label_set_row}" ]] && [[ "${line_lower}" =~ ${label_missing_table_any_cell_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${rc_label_set_assignment_regex} ]] || [[ "${line_lower}" =~ ${rc_label_set_table_regex} ]]; then
    for required_rc_label in rc-evidence phase-66 report-export not-workflow-truth; do
      required_rc_label_regex="(^|[[:space:]\`,;|])${required_rc_label}([[:space:]\`,;|.]|$)"
      negated_required_rc_label_prefix_regex="(^|[[:space:]\`,;|])(no|not|without|missing|omitted|excluded)[[:space:]_-]+(the[[:space:]_-]+)?${required_rc_label}([[:space:]\`,;|.]|$)"
      negated_required_rc_label_suffix_regex="(^|[[:space:]\`,;|])${required_rc_label}[[:space:]_-]+(is[[:space:]_-]+)?(missing|omitted|excluded|absent)([[:space:]\`,;|.]|$)"
      if [[ ! "${line_lower}" =~ ${required_rc_label_regex} ]] || [[ "${line_lower}" =~ ${negated_required_rc_label_prefix_regex} ]] || [[ "${line_lower}" =~ ${negated_required_rc_label_suffix_regex} ]]; then
        echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
        exit 1
      fi
    done
    label_line_without_required_negative="${line_lower//not-workflow-truth/}"
    if [[ "${label_line_without_required_negative}" =~ ${workflow_truth_label_regex} ]]; then
      echo "Forbidden Phase 66.5 report export RC proof: invalid RC label set detected" >&2
      exit 1
    fi
  fi
  if [[ "${line_lower}" =~ ${redaction_missing_regex} ]] || [[ "${line_lower}" =~ ${redaction_missing_table_regex} ]] || { [[ "${line_lower}" != "${canonical_redaction_posture_row}" ]] && [[ "${line_lower}" =~ ${redaction_missing_table_any_cell_regex} ]]; }; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid redaction posture detected" >&2
    exit 1
  fi
  if is_named_evidence_field_line "redaction_posture" "${line_lower}" && ! has_complete_redaction_posture "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: invalid redaction posture detected" >&2
    exit 1
  fi
  if line_has_unsafe_workstation_path "${line_lower}"; then
    echo "Forbidden Phase 66.5 report export RC proof: workstation-local path evidence detected" >&2
    exit 1
  fi
  if ! is_safe_customer_private_redaction_line "${line_lower}" && [[ "${line_lower}" =~ customer[-_\ ]private[-_\ ]data[[:space:]]*[:=] ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
  if ! is_safe_customer_private_redaction_line "${line_lower}" && [[ "${line_lower}" =~ ${customer_private_unsafe_regex} ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${customer_private_prohibition_regex} ]] && [[ ! "${line_lower}" =~ (includes|contains|embeds|carries|stores|exposes?|are[[:space:]]+stored|is[[:space:]]+stored|were[[:space:]]+stored|was[[:space:]]+stored) ]]; then
    continue
  fi
  if ! is_safe_customer_private_redaction_line "${line_lower}" && [[ "${line_lower}" =~ (includes|contains|embeds|carries|stores|exposes?)[[:space:]]+(customer[-_\ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_\ ]private[[:space:]]+data|raw[[:space:]]+customer[[:space:]]+data[[:space:]]+(is|are|was|were)[[:space:]]+(stored|included|embedded|carried|exposed)|unredacted[[:space:]]+customer[[:space:]]+data ]]; then
    echo "Forbidden Phase 66.5 report export RC proof: customer-private data detected" >&2
    exit 1
  fi
done < <(lower_visible_text "${absolute_doc_path}")

scan_forbidden_claims "${absolute_doc_path}" "report export RC proof"
readme_phase66_5_scope='phase[[:space:]_-]+66(\.|[[:space:]_-]+)5|phase-66-5-report-export-rc-proof'
scan_forbidden_claims "${readme_path}" "README" "${readme_phase66_5_scope}"

if [[ "${PHASE66_5_SKIP_PATH_HYGIENE:-0}" != "1" ]]; then
  path_hygiene_stderr="${tmp_dir}/path-hygiene.err"
  if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
    cat "${path_hygiene_stderr}" >&2
    echo "Forbidden Phase 66.5 report export RC proof absolute path usage detected" >&2
    exit 1
  fi
fi

echo "Phase 66.5 report export RC proof contract and focused negative checks pass."
