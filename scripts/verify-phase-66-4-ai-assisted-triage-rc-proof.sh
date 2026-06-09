#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-4-ai-assisted-triage-rc-proof.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
tmp_dir="$(mktemp -d)"
doc_visible_path="${tmp_dir}/phase-66-4-doc.visible.md"
readme_visible_path="${tmp_dir}/README.visible.md"
doc_visible_lower_path="${tmp_dir}/phase-66-4-doc.visible.lower.md"
readme_visible_lower_path="${tmp_dir}/README.visible.lower.md"
trap 'rm -rf "${tmp_dir}"' EXIT

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-59-3-ai-trace-lifecycle-contract.md"
  "docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
  "docs/phase-60-3-case-timeline-summary-agent.md"
  "docs/phase-60-6-cited-recommendation-draft-agent.md"
  "docs/phase-63-7-ai-grounding-adapter.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
  "scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
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
  if [[ "$#" -eq 1 && "$1" == "${readme_path}" && -s "${readme_visible_lower_path}" ]]; then
    cat "${readme_visible_lower_path}"
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

require_section_phrase() {
  local section="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(perl -0pe 's/<!--.*?-->//gs' <<<"${section}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 66.4 AI-assisted triage RC proof"
require_file "${readme_path}" "README for Phase 66.4 link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.4 reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.4 verifier script ${verifier_script}"
done

perl -0pe 's/<!--.*?-->//gs' "${absolute_doc_path}" >"${doc_visible_path}"
perl -0pe 's/<!--.*?-->//gs' "${readme_path}" >"${readme_visible_path}"
tr '[:upper:]' '[:lower:]' <"${doc_visible_path}" >"${doc_visible_lower_path}"
tr '[:upper:]' '[:lower:]' <"${readme_visible_path}" >"${readme_visible_lower_path}"

require_phrase "${readme_path}" "- [Phase 66.4 AI-assisted triage RC proof](docs/phase-66-4-ai-assisted-triage-rc-proof.md) defines the reviewed AI-assisted triage proof surface for RC evidence while preserving AI output as cited, reviewable, advisory evidence and excluding AI approval, AI execution, AI reconciliation, case-closure authority, GA, and commercial replacement claims." "README canonical Phase 66.4 boundary bullet"
require_phrase "${readme_path}" "The Phase 66.4 AI-assisted triage RC proof is defined by the [Phase 66.4 AI-assisted triage RC proof](docs/phase-66-4-ai-assisted-triage-rc-proof.md)." "README Product positioning Phase 66.4 reference"

required_phrases=(
  "# Phase 66.4 AI-Assisted Triage RC Proof"
  "**Status**: Accepted as the Phase 66.4 AI-assisted triage RC proof contract for release-candidate evidence planning only."
  "**Related Baseline**: \`docs/phase-66-1-clean-host-rc-e2e-harness.md\`, \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`, \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, \`docs/phase-59-3-ai-trace-lifecycle-contract.md\`, \`docs/phase-59-4-ai-disabled-degraded-mode-contract.md\`, \`docs/phase-60-3-case-timeline-summary-agent.md\`, \`docs/phase-60-6-cited-recommendation-draft-agent.md\`, \`docs/phase-63-7-ai-grounding-adapter.md\`, \`docs/phase-65-closeout-evaluation.md\`"
  "**Related Issues**: #1397, #1401"
  "This contract defines the Phase 66.4 AI-assisted triage RC proof surface."
  "The proof depends on the Phase 66.1 clean-host RC E2E harness."
  "The AI-assisted triage proof demonstrates that cited assistant output can help an operator review an alert, summarize evidence, mark uncertainty, draft a recommendation, and record accepted, rejected, or unresolved review posture while AegisOps records remain the authoritative system for alert, case, evidence, approval, action, reconciliation, release, gate, and closeout truth."
  "This proof is RC evidence only."
  "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth."
  "AI output remains advisory and tool-governed."
  "The proof must reject missing citations, missing review states, missing degraded or disabled posture, missing limitation references, AI approval, AI execution, AI reconciliation, AI case closure, AI-as-truth claims, prompt-injection shortcuts, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, issue-lint-as-readiness-truth, and AI-as-readiness-truth."
  "Phase 66.4 records one reviewed AI-assisted triage path for RC evidence."
  "Later Phase 66 issues must still prove report export, supportability, RC authority-boundary proof pack, and closeout evidence independently."
  'Run `bash scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh`.'
  'Run `bash scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1401 --config <supervisor-config-path>`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 66.4 AI-assisted triage proof term in ${doc_path}"
done

evidence_section="$(section_text "${absolute_doc_path}" "## 2. AI-Assisted Triage Evidence" "## 3. Cited Summary And Reviewability")"
evidence_rows=(
  "| \`journey_run_id\` | The Phase 66.1 run identifier that observed the AI-assisted triage path. | Missing or mismatched run identifiers fail the proof. |"
  "| \`repository_revision\` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |"
  "| \`ai_trace_id\` | Reviewed AI trace lifecycle record for the cited assistant interaction. | Prompt text, model output, or UI text alone cannot create trace truth. |"
  "| \`source_evidence_references\` | Reviewed AegisOps evidence ids, alert ids, case ids, and source references used by the assistant. | Missing citations fail the proof. |"
  "| \`cited_summary_id\` | Cited triage summary linked to exact evidence references and reviewer. | Uncited summaries, invented citations, or hidden source text fail the proof. |"
  "| \`uncertainty_flags\` | Explicit uncertainty, ambiguity, stale-evidence, and low-confidence flags when present. | Uncertainty cannot be hidden in assistant prose. |"
  "| \`recommendation_draft_id\` | Draft recommendation with cited rationale, scope, reviewer, and review state. | Recommendation text cannot approve, execute, reconcile, or close records. |"
  "| \`operator_review_state\` | \`accepted\`, \`rejected\`, or \`unresolved\` with reviewer, timestamp, rationale, and follow-up owner. | Missing review state or AI self-approval fails the proof. |"
  "| \`degraded_disabled_posture\` | AI disabled, degraded, stale, unavailable, or rejected-output posture and manual fallback path. | AI output cannot be required for RC journey continuation. |"
  "| \`prompt_injection_review_id\` | Reviewed prompt-injection, instruction-conflict, and unsafe-tool-use assessment. | Prompt-injection compliance or instruction following cannot override AegisOps policy. |"
  "| \`limitation_references\` | Known limitation ids, owner, decision date, and follow-up date when evidence is incomplete. | Missing limitations cannot be hidden in assistant output. |"
)

for row in "${evidence_rows[@]}"; do
  require_section_phrase "${evidence_section}" "${row}" "Phase 66.4 AI-assisted triage evidence field"
done

reviewability_section="$(section_text "${absolute_doc_path}" "## 3. Cited Summary And Reviewability" "## 4. Authority Boundary")"
reviewability_terms=(
  "The proof must cite \`docs/phase-59-3-ai-trace-lifecycle-contract.md\`"
  "The proof must cite \`docs/phase-60-3-case-timeline-summary-agent.md\`"
  "The proof must cite \`docs/phase-60-6-cited-recommendation-draft-agent.md\`"
  "The proof must cite \`docs/phase-59-4-ai-disabled-degraded-mode-contract.md\`"
  "The proof must cite \`docs/phase-63-7-ai-grounding-adapter.md\`"
  "trace id, model family, prompt template, tool context, source evidence references, output hash, reviewer, retention posture, and redaction posture"
  "summary id, alert id, case id, evidence ids, source timestamps, confidence flags, stale-evidence flags, ambiguity flags, reviewer, and review outcome"
  "draft id, cited rationale, rejected alternatives, unresolved questions, follow-up owner, accepted state, rejected state, and unresolved state"
  "AI unavailable, AI disabled, stale source evidence, model failure, unsafe output, rejected output, and manual review continuation"
  "Model output, prompt text, browser state, UI cache, verifier output, issue-lint output, source tool output, and optional evidence remain subordinate evidence."
)

for term in "${reviewability_terms[@]}"; do
  require_section_phrase "${reviewability_section}" "${term}" "Phase 66.4 cited summary or reviewability term"
done

limitations_section="$(section_text "${absolute_doc_path}" "## 5. Accepted Limitations" "## 6. Verification")"
require_section_phrase "${limitations_section}" "It does not prove autonomous remediation, AI approval, AI execution, AI reconciliation, AI case closure, detector activation, source-native truth, release truth, gate truth, broad AI SOC replacement, real design-partner success, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness." "Phase 66.4 accepted limitations boundary"

subordinate_authority_subjects='(ai([[:space:]]+(outputs?|summary|summaries|recommendations?|trace|trace[[:space:]-]+state|assistant|model|draft|confidence|uncertainty|review|grounding|citation|tool|prompt|prompt[[:space:]-]+injection|generated[[:space:]-]+text))?|assistant[[:space:]]+(outputs?|summaries|recommendations?)|model[[:space:]]+(outputs?|recommendations?)|prompt[[:space:]]+text|prompt[[:space:]-]+injection[[:space:]]+(results?|compliance|outputs?)|grounding[[:space:]]+outputs?|tool[[:space:]]+outputs?|source[[:space:]]+snippets?|citations?|confidence[[:space:]]+scores?|uncertainty[[:space:]]+flags?|browser[[:space:]]+state|ui[[:space:]]+cache|verifier[[:space:]]+outputs?|issue-lint[[:space:]]+outputs?|optional[[:space:]]+evidence)'
authority_verbs='(approve[s]?|execute[s]?|reconcile[s]?|close[s]?|release[s]?|gate[s]?|mutate[s]?|promote[s]?)'
authority_modals='(can|may|must|should|will|would|could)'
passive_authority_verbs='(approved|executed|reconciled|closed|released|gated|mutated|promoted)'
authority_objects='(aegisops[[:space:]]+records?|case|cases|alert|record|workflow|release|gate|evidence|approval|actions?|remediation[[:space:]-]+actions?|action[[:space:]-]+requests?|execution[[:space:]-]+receipts?|reconciliation|audit|limitation|source[[:space:]-]+admission|closeout)'

repository_revision_value_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`[:space:],.;)]+|refs/remotes/[^`[:space:],.;)]+|remotes/[^`[:space:],.;)]+|origin/[^`[:space:],.;)]+|[^`[:space:],.;)]*branch)`?([[:space:].,;)]|$)'
repository_revision_assignment_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
repository_revision_mutable_suffix_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][^.[:cntrl:]]*[0-9a-f]{40}[^.[:cntrl:]]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)'
repository_revision_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?([^`|[:space:]]+)`?[[:space:]]*\|'
repository_revision_table_mutable_suffix_regex='(^|[[:space:]>*-])\|[[:space:]]*`?repository_revision`?[[:space:]]*\|[[:space:]]*`?[^`|]*[0-9a-f]{40}[^`|]*(main|master|develop|development|trunk|head|refs/heads/|refs/remotes/|remotes/|origin/|branch)[^`|]*`?[[:space:]]*\|'
missing_value='missing|mismatched|none|null|n/a|tbd|todo|unknown|omitted|absent|blank|empty|withheld|not[[:space:]_-]*provided|not[[:space:]_-]*set'
required_fields='journey_run_id|repository_revision|ai_trace_id|source_evidence_references|cited_summary_id|uncertainty_flags|recommendation_draft_id|operator_review_state|degraded_disabled_posture|prompt_injection_review_id|limitation_references'
review_state_value_regex='(^|[[:space:]>*-])`?operator_review_state`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
review_state_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?operator_review_state`?[[:space:]]*\|[[:space:]]*`?([^`|[:space:]]+)`?[[:space:]]*\|'
review_state_authority_suffix_regex='(^|[[:space:]>*-])`?operator_review_state`?[[:space:]]*[:=][^.[:cntrl:]]*(accepted|rejected|unresolved)[^.[:cntrl:]]*(by[[:space:]_-]+ai|ai[[:space:]_-]*approved|ai[[:space:]_-]*self|self[[:space:]_-]*approved)'
review_state_table_authority_suffix_regex='(^|[[:space:]>*-])\|[[:space:]]*`?operator_review_state`?[[:space:]]*\|[[:space:]]*`?[^`|]*(accepted|rejected|unresolved)[^`|]*(by[[:space:]_-]+ai|ai[[:space:]_-]*approved|ai[[:space:]_-]*self|self[[:space:]_-]*approved)[^`|]*`?[[:space:]]*\|'
ai_trace_shortcut_regex='(^|[[:space:]>*-])`?ai_trace_id`?[[:space:]]*[:=][^.[:cntrl:]]*(prompt[[:space:]_-]*text|model[[:space:]_-]*output|ui[[:space:]_-]*text)'
ai_trace_shortcut_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?ai_trace_id`?[[:space:]]*\|[[:space:]]*`?[^`|]*(prompt[[:space:]_-]*text|model[[:space:]_-]*output|ui[[:space:]_-]*text)[^`|]*`?[[:space:]]*\|'
citation_shortcut_fields='source_evidence_references|cited_summary_id|recommendation_draft_id'
citation_shortcut_regex='(^|[[:space:]>*-])`?('"${citation_shortcut_fields}"')`?[[:space:]]*[:=][^.[:cntrl:]]*(uncited|no[[:space:]_-]*citations?|invented|hidden[[:space:]_-]*source|assistant[[:space:]_-]*prose|model[[:space:]_-]*output)'
citation_shortcut_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?('"${citation_shortcut_fields}"')`?[[:space:]]*\|[[:space:]]*`?[^`|]*(uncited|no[[:space:]_-]*citations?|invented|hidden[[:space:]_-]*source|assistant[[:space:]_-]*prose|model[[:space:]_-]*output)[^`|]*`?[[:space:]]*\|'
uncertainty_hidden_regex='(^|[[:space:]>*-])`?uncertainty_flags`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]_-]+in[[:space:]_-]+assistant[[:space:]_-]+prose'
uncertainty_hidden_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?uncertainty_flags`?[[:space:]]*\|[[:space:]]*`?[^`|]*hidden[[:space:]_-]+in[[:space:]_-]+assistant[[:space:]_-]+prose[^`|]*`?[[:space:]]*\|'
recommendation_authority_regex='(^|[[:space:]>*-])`?recommendation_draft_id`?[[:space:]]*[:=][^.[:cntrl:]]*(approved|executed|reconciled|closed|case[[:space:]_-]*closed|auto[[:space:]_-]*approved)'
recommendation_authority_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?recommendation_draft_id`?[[:space:]]*\|[[:space:]]*`?[^`|]*(approved|executed|reconciled|closed|case[[:space:]_-]*closed|auto[[:space:]_-]*approved)[^`|]*`?[[:space:]]*\|'
degraded_missing_regex='(^|[[:space:]>*-])`?degraded_disabled_posture`?[[:space:]]*[:=][^.[:cntrl:]]*(not[[:space:]_-]*needed|required[[:space:]_-]*for[[:space:]_-]*rc|always[[:space:]_-]*available)'
degraded_missing_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?degraded_disabled_posture`?[[:space:]]*\|[[:space:]]*`?[^`|]*(not[[:space:]_-]*needed|required[[:space:]_-]*for[[:space:]_-]*rc|always[[:space:]_-]*available)[^`|]*`?[[:space:]]*\|'
prompt_injection_shortcut_regex='(^|[[:space:]>*-])`?prompt_injection_review_id`?[[:space:]]*[:=][^.[:cntrl:]]*(comply|complied|follow[[:space:]_-]*instructions|instruction[[:space:]_-]*following|override[[:space:]_-]*policy|ignore[[:space:]_-]*policy|developer[[:space:]_-]*override)'
prompt_injection_shortcut_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?prompt_injection_review_id`?[[:space:]]*\|[[:space:]]*`?[^`|]*(comply|complied|follow[[:space:]_-]*instructions|instruction[[:space:]_-]*following|override[[:space:]_-]*policy|ignore[[:space:]_-]*policy|developer[[:space:]_-]*override)[^`|]*`?[[:space:]]*\|'
limitation_hidden_regex='(^|[[:space:]>*-])`?limitation_references`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]_-]+in[[:space:]_-]+assistant[[:space:]_-]+output'
limitation_hidden_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?limitation_references`?[[:space:]]*\|[[:space:]]*`?[^`|]*hidden[[:space:]_-]+in[[:space:]_-]+assistant[[:space:]_-]+output[^`|]*`?[[:space:]]*\|'
customer_private_table_regex='(^|[[:space:]>*-])\|[[:space:]]*`?(customer[-_ ]private[-_ ]data|raw[[:space:]_-]*customer[[:space:]_-]*data|unredacted[[:space:]_-]*customer)`?[[:space:]]*\|[[:space:]]*`?[^`|[:space:]][^`|]*`?[[:space:]]*\|'
customer_private_prohibition_regex='(must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include)[^.[:cntrl:]]*customer[-_ ]private'

forbidden_patterns=(
  'phase[[:space:]]+66\.4[[:space:]]+(proves|satisfies|passes|accepts|grants|achieves|enables|validates|demonstrates|confirms)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|rc[[:space:]-]+gate|rc[[:space:]-]+readiness|rc[[:space:]-]+pass|broad[[:space:]]+ai|ai[[:space:]]+soc[[:space:]]+replacement|autonomous[[:space:]]+remediation|ai[[:space:]]+(approval|execution|reconciliation|case[[:space:]-]+closure)|detector[[:space:]]+activation|release[[:space:]]+truth|gate[[:space:]]+truth|readiness[[:space:]]+truth|commercial[[:space:]]+replacement|real[[:space:]]+design[- ]partner|phase[[:space:]]+66[[:space:]]+closeout)'
  'phase[[:space:]]+66\.4[[:space:]]+(satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc([[:space:][:punct:]]|$)|release[- ]candidate)'
  '(phase[[:space:]]+66\.4|this[[:space:]]+proof|proof|aegisops)[[:space:]]+(is|becomes|serves[[:space:]]+as)[[:space:]]+(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?(ready[[:space:]]+for[[:space:]]+(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate|commercial[[:space:]]+replacement)|(ga|rc|release[- ]candidate|commercial[[:space:]]+replacement)[[:space:]-]+ready)'
  '(this[[:space:]]+)?proof[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms|achieves|demonstrates)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate|readiness|broad[[:space:]]+ai|ai[[:space:]]+soc|commercial[[:space:]]+replacement)'
  'ai[[:space:]]+(output|summary|recommendation|trace|assistant|model)[^.[:cntrl:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(approval|execution|reconciliation|case|workflow|release|gate|evidence|audit|limitation|readiness|closeout)[[:space:]]+(source[[:space:]]+of[[:space:]]+)?truth'
  "${subordinate_authority_subjects}[^.[:cntrl:]]+[[:space:]]+(is|are|becomes?|serves[[:space:]]+as)[^.[:cntrl:]]*source[[:space:]]+of[[:space:]]+truth[[:space:]]+(for|over|as)[^.[:cntrl:]]*(approval|approvals?|execution|case[[:space:]-]+closure|reconciliation|actions?|aegisops)"
  "${subordinate_authority_subjects}([[:space:]]+${authority_modals})?[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "${authority_objects}[^.[:cntrl:]]+[[:space:]](is|are|was|were|be|been|being)[[:space:]]+${passive_authority_verbs}[[:space:]]+by[[:space:]]+${subordinate_authority_subjects}"
  "${subordinate_authority_subjects}[^.[:cntrl:]]+[[:space:]]+(has|have|holds?|carries|grants?)[[:space:]]+[^.[:cntrl:]]*((approval|approvals?|execution|case[[:space:]-]+closure|reconciliation|actions?|aegisops)[^.[:cntrl:]]+authority|authority[^.[:cntrl:]]*(approval|approvals?|execution|case[[:space:]-]+closure|reconciliation|actions?|aegisops))"
  "${subordinate_authority_subjects}[^.[:cntrl:]]+[[:space:]]+(is|are|becomes?)[[:space:]]+authoritative[[:space:]]+(for|over|as)[^.[:cntrl:]]*(approval|approvals?|execution|case[[:space:]-]+closure|reconciliation|actions?|aegisops)"
  '(ai|assistant|model)[^.[:cntrl:]]+(auto[[:space:]-]+approve|auto[[:space:]-]+execute|auto[[:space:]-]+reconcile|auto[[:space:]-]+close|autonomously[[:space:]]+(approve|execute|reconcile|close))'
  'prompt[[:space:]-]+injection[^.[:cntrl:]]+(overrides|bypasses|supersedes|replaces)[^.[:cntrl:]]*(policy|approval|review|aegisops)'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate|workflow|source)[[:space:]]+truth'
  '(verifier([[:space:]]+outputs?)?|issue-lint([[:space:]]+outputs?)?|ai[[:space:]]+outputs?|ai[[:space:]]+summary|ai[[:space:]]+recommendations?)[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(readiness|release|gate|workflow|source|rc([[:space:][:punct:]]|$)|ga([[:space:][:punct:]]|$))'
)

is_safe_forbidden_claim_line() {
  local line_lower="$1"
  local safe_forbidden_claim_line_regex='^[[:space:]>*-]*(phase[[:space:]]+66\.4|this[[:space:]]+proof|proof|aegisops)[^.[:cntrl:]]+(confirms|records|states)[^.[:cntrl:]]+(does[[:space:]]+not[[:space:]]+prove|do[[:space:]]+not[[:space:]]+prove|remains?[[:space:]]+out[[:space:]]+of[[:space:]]+scope|cannot[[:space:]])[^.[:cntrl:]]*[.]?[[:space:]]*$'
  local same_line_authority_suffix_regex='(^|[[:space:]])(but|and)[[:space:]]+'
  if [[ "${line_lower}" =~ ${same_line_authority_suffix_regex} ]] || [[ "${line_lower}" =~ \; ]]; then
    return 1
  fi
  if [[ "${line_lower}" =~ ${safe_forbidden_claim_line_regex} ]]; then
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
    if [[ "${scope}" == "phase66_4_readme" ]] && [[ ! "${line_lower}" =~ (phase[[:space:]]+66\.4|ai-assisted[[:space:]]+triage|rc[[:space:]]+proof) ]]; then
      continue
    fi
    if is_safe_forbidden_claim_line "${line_lower}"; then
      continue
    fi
    for forbidden_pattern in "${forbidden_patterns[@]}"; do
      if [[ "${line_lower}" =~ ${forbidden_pattern} ]]; then
        echo "Forbidden Phase 66.4 ${description} claim matched" >&2
        exit 1
      fi
    done
  done < <(lower_visible_text "${file}")

  if [[ "${scope}" == "all" ]]; then
    line_lower="$(lower_visible_text "${file}" | awk 'NF { printf "%s ", $0 } !NF { printf "\n" }')"
    for forbidden_pattern in "${forbidden_patterns[@]}"; do
      if [[ "${line_lower}" =~ ${forbidden_pattern} ]]; then
        echo "Forbidden Phase 66.4 ${description} claim matched" >&2
        exit 1
      fi
    done
  fi
}

if grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*(bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|basic[[:space:]]+[A-Za-z0-9+/=]{12,})|(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}' "${absolute_doc_path}"; then
  echo "Forbidden Phase 66.4 AI-assisted triage RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- '(^|[[:space:]>*-])\|[[:space:]]*`?(password|passwd|secret([_ -]?(key|access[_ -]?key))?|private[_ -]?key|token|api[_ -]?key|aws[_ -]?secret[_ -]?access[_ -]?key)`?[[:space:]]*\|[[:space:]]*`?[^[:space:]`|<>]+`?[[:space:]]*\|' "${absolute_doc_path}"; then
  echo "Forbidden Phase 66.4 AI-assisted triage RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\`?(${required_fields})\`?[[:space:]]*[:=][[:space:]]*\`?(${missing_value})([[:space:]_.-]+[^.[:cntrl:]]*)?([[:space:].,;)]|$)" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.4 AI-assisted triage RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eq -- "(^|[[:space:]>*-])\|[[:space:]]*\`?(${required_fields})\`?[[:space:]]*\|[[:space:]]*\`?(${missing_value})([[:space:]_.-]+[^|]*)?\|" < <(lower_visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.4 AI-assisted triage RC proof: missing required evidence value detected" >&2
  exit 1
fi

while IFS= read -r line_lower; do
  if [[ "${line_lower}" =~ ${repository_revision_value_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_mutable_suffix_regex} ]] || [[ "${line_lower}" =~ ${repository_revision_table_mutable_suffix_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_assignment_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: non-immutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${repository_revision_table_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: non-immutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${review_state_value_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^(accepted|rejected|unresolved)$ ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid operator review state detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${review_state_authority_suffix_regex} ]] || [[ "${line_lower}" =~ ${review_state_table_authority_suffix_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid operator review state detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${review_state_table_regex} ]] && [[ ! "${BASH_REMATCH[2]}" =~ ^(accepted|rejected|unresolved)$ ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid operator review state detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${ai_trace_shortcut_regex} ]] || [[ "${line_lower}" =~ ${ai_trace_shortcut_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid AI trace detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${citation_shortcut_regex} ]] || [[ "${line_lower}" =~ ${citation_shortcut_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid citation evidence detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${uncertainty_hidden_regex} ]] || [[ "${line_lower}" =~ ${uncertainty_hidden_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: hidden uncertainty detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${recommendation_authority_regex} ]] || [[ "${line_lower}" =~ ${recommendation_authority_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: recommendation authority shortcut detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${degraded_missing_regex} ]] || [[ "${line_lower}" =~ ${degraded_missing_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: invalid degraded or disabled posture detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${prompt_injection_shortcut_regex} ]] || [[ "${line_lower}" =~ ${prompt_injection_shortcut_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: prompt-injection shortcut detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${limitation_hidden_regex} ]] || [[ "${line_lower}" =~ ${limitation_hidden_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: hidden limitation references detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${customer_private_table_regex} ]]; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: customer-private data detected" >&2
    exit 1
  fi
  if grep -Eq -- 'customer[-_ ]private[-_ ]data[[:space:]]*[:=]' <<<"${line_lower}"; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${customer_private_prohibition_regex} ]] && ! grep -Eiq -- '(^|[[:space:];,])(but|and)?[[:space:]]*(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)' <<<"${line_lower}"; then
    continue
  fi
  if grep -Eq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(data|example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line_lower}"; then
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof: customer-private data detected" >&2
    exit 1
  fi
done < <(lower_visible_text "${absolute_doc_path}")

scan_forbidden_claims "${absolute_doc_path}" "AI-assisted triage RC proof"
scan_forbidden_claims "${readme_path}" "README" "phase66_4_readme"

if [[ "${PHASE66_4_SKIP_PATH_HYGIENE:-0}" != "1" ]]; then
  path_hygiene_stderr="${tmp_dir}/path-hygiene.err"
  if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
    cat "${path_hygiene_stderr}" >&2
    echo "Forbidden Phase 66.4 AI-assisted triage RC proof absolute path usage detected" >&2
    exit 1
  fi
fi

echo "Phase 66.4 AI-assisted triage RC proof contract and focused negative checks pass."
