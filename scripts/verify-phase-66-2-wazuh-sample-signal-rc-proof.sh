#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/deployment/wazuh-manager-intake-binding-contract.md"
  "docs/deployment/wazuh-source-health-projection-contract.md"
  "docs/deployment/wazuh-authority-boundary-negative-tests.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
  "scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
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

require_file "${absolute_doc_path}" "Phase 66.2 Wazuh sample signal RC proof"
require_file "${readme_path}" "README for Phase 66.2 link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.2 reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.2 verifier script ${verifier_script}"
done

require_phrase "${readme_path}" "- [Phase 66.2 Wazuh sample signal RC proof](docs/phase-66-2-wazuh-sample-signal-rc-proof.md) defines the reviewed Wazuh-origin sample signal proof surface for RC evidence while preserving Wazuh as subordinate analytic-signal context and excluding broad SIEM parity, production telemetry import, source-native truth, GA, and commercial replacement claims." "README canonical Phase 66.2 boundary bullet"
require_phrase "${readme_path}" "The Phase 66.2 Wazuh sample signal RC proof is defined by the [Phase 66.2 Wazuh sample signal RC proof](docs/phase-66-2-wazuh-sample-signal-rc-proof.md)." "README Product positioning Phase 66.2 reference"

required_phrases=(
  "# Phase 66.2 Wazuh Sample Signal RC Proof"
  "**Status**: Accepted as the Phase 66.2 Wazuh sample signal RC proof contract for release-candidate evidence planning only."
  "**Related Baseline**: \`docs/phase-66-1-clean-host-rc-e2e-harness.md\`, \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`, \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, \`docs/deployment/wazuh-manager-intake-binding-contract.md\`, \`docs/deployment/wazuh-source-health-projection-contract.md\`, \`docs/deployment/wazuh-authority-boundary-negative-tests.md\`, \`docs/phase-65-closeout-evaluation.md\`"
  "**Related Issues**: #1397, #1399"
  "This contract defines the Phase 66.2 Wazuh sample signal RC proof surface."
  "The proof depends on the Phase 66.1 clean-host RC E2E harness."
  "The Wazuh sample signal proof demonstrates that a sample Wazuh-origin signal can be observed, health-checked, admitted, and linked by AegisOps without turning Wazuh into alert truth, case truth, source truth, release truth, gate truth, or workflow authority."
  "This proof is RC evidence only."
  "Admission succeeds only after AegisOps creates or links an admission record and alert record."
  "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth."
  "Wazuh remains a subordinate analytic-signal source."
  "The proof must reject missing sample signal identity, missing source-health reference, missing intake binding reference, missing admission record, missing provenance, missing limitation references, source-native truth, broad SIEM parity, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth."
  "Phase 66.2 proves one reviewed Wazuh sample signal path for RC evidence."
  "Later Phase 66 issues must still prove Shuffle sample execution, AI-assisted triage, report export, supportability, RC authority-boundary proof pack, and closeout evidence independently."
  'Run `bash scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`.'
  'Run `bash scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1399 --config <supervisor-config-path>`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 66.2 Wazuh sample signal proof term in ${doc_path}"
done

evidence_section="$(section_text "${absolute_doc_path}" "## 2. Sample Signal Evidence" "## 3. Source Health And Admission")"
evidence_rows=(
  "| \`journey_run_id\` | The Phase 66.1 run identifier that observed the sample signal. | Missing or mismatched run identifiers fail the proof. |"
  "| \`repository_revision\` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |"
  "| \`wazuh_profile\` | \`smb-single-node\` Wazuh product profile reference. | Any other profile is out of scope. |"
  "| \`sample_signal_id\` | Stable sample signal identifier. | Dashboard text or filenames cannot create signal identity. |"
  "| \`source_family\` | Wazuh source family and parser family. | Source family cannot be inferred from nearby prose. |"
  "| \`source_health_reference\` | Reviewed source-health projection record or artifact reference. | Wazuh health is subordinate context only. |"
  "| \`intake_binding_reference\` | Reviewed \`/intake/wazuh\` binding and proxy route reference. | Direct or ad hoc intake paths fail the proof. |"
  "| \`admission_record_id\` | AegisOps admission record for the sample signal. | Wazuh alerts remain candidate signals until admission. |"
  "| \`aegisops_alert_id\` | AegisOps alert identifier created or linked after admission. | Wazuh alert ids are not AegisOps alert truth. |"
  "| \`provenance_reference\` | Explicit Wazuh manager, rule, event, timestamp, proxy, and custody provenance. | Raw forwarded headers or inferred linkage fail the proof. |"
  "| \`case_linking_posture\` | \`not_linked\`, \`linked_by_aegisops_case_workflow\`, or \`explicitly_deferred\`. | Wazuh cannot promote, close, or mutate cases. |"
  "| \`limitation_references\` | Known limitation ids, owner, decision date, and follow-up date when evidence is incomplete. | Missing limitations cannot be hidden in source-health text. |"
)

for row in "${evidence_rows[@]}"; do
  require_section_phrase "${evidence_section}" "${row}" "Phase 66.2 sample signal evidence field"
done

source_health_section="$(section_text "${absolute_doc_path}" "## 3. Source Health And Admission" "## 4. Authority Boundary")"
source_health_terms=(
  "The proof must cite \`docs/deployment/wazuh-source-health-projection-contract.md\`"
  "The proof must cite \`docs/deployment/wazuh-manager-intake-binding-contract.md\`"
  "manager, dashboard, indexer, intake, signal freshness, parser, volume, and credential posture"
  "source family, source system, source component, source id, event id, event timestamp, Wazuh manager id, Wazuh rule id, Wazuh rule level, ingest channel, admission channel, secret custody reference, proxy route, and reviewer"
  "Wazuh manager state, Wazuh dashboard state, Wazuh alert status, Wazuh rule state, webhook acknowledgement, source-health projection, verifier output, and issue-lint output remain subordinate evidence."
)

for term in "${source_health_terms[@]}"; do
  require_section_phrase "${source_health_section}" "${term}" "Phase 66.2 source-health or admission term"
done

limitations_section="$(section_text "${absolute_doc_path}" "## 5. Accepted Limitations" "## 6. Verification")"
require_section_phrase "${limitations_section}" "It does not prove broad Wazuh detector parity, production customer telemetry import, production monitoring coverage, real design-partner success, source-native truth, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness." "Phase 66.2 accepted limitations boundary"

subordinate_authority_subjects='(wazuh[[:space:]]+alerts?|wazuh[[:space:]]+manager[[:space:]]+state|wazuh[[:space:]]+dashboard[[:space:]]+state|wazuh[[:space:]]+alert[[:space:]]+status|wazuh[[:space:]]+indexer[[:space:]]+contents|wazuh[[:space:]]+source[[:space:]]+health|wazuh[[:space:]]+rule[[:space:]]+state|wazuh[[:space:]]+timestamps?|webhook[[:space:]-]+acknowledgements?|source[- ]health[[:space:]]+projection|generated[[:space:]-]+config(uration)?|tickets?|ai[[:space:]]+output|browser[[:space:]]+state|ui[[:space:]]+cache|verifier[[:space:]]+output|issue-lint[[:space:]]+output|downstream[[:space:]]+receipts?)'
authority_verbs='(approve[s]?|execute[s]?|reconcile[s]?|close[s]?|release[s]?|gate[s]?|mutate[s]?|promote[s]?)'
authority_objects='(aegisops[[:space:]]+records?|case|alert|record|workflow|release|gate|evidence|approval|action[[:space:]-]+requests?|execution[[:space:]-]+receipts?|reconciliation|audit|limitation|source[[:space:]-]+admission|closeout)'

repository_revision_value_regex='(^|[[:space:]>*-])`?repository_revision`?[[:space:]]*[:=][[:space:]]*`?(main|master|develop|development|trunk|head|refs/heads/[^`[:space:],.;)]+|refs/remotes/[^`[:space:],.;)]+|remotes/[^`[:space:],.;)]+|origin/[^`[:space:],.;)]+|[^`[:space:],.;)]*branch)`?([[:space:].,;)]|$)'
wazuh_profile_value_regex='(^|[[:space:]>*-])`?wazuh_profile`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'
source_family_shortcut_regex='(^|[[:space:]>*-])`?source_family`?[[:space:]]*[:=][^.[:cntrl:]]*(inferred([[:space:]-]+from)?[[:space:]-]+nearby[[:space:]-]+prose|inferred|nearby[[:space:]-]+prose)'
case_linking_value_regex='(^|[[:space:]>*-])`?case_linking_posture`?[[:space:]]*[:=][[:space:]]*`?([^`[:space:],.;)]+)'

forbidden_patterns=(
  'phase[[:space:]]+66\.2[[:space:]]+(proves|satisfies|passes|accepts|grants)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|broad[[:space:]]+wazuh|broad[[:space:]]+siem|production[[:space:]]+(customer[[:space:]]+)?telemetry|production[[:space:]]+monitoring|commercial[[:space:]]+replacement|source[- ]native|real[[:space:]]+design[- ]partner|phase[[:space:]]+66[[:space:]]+closeout)'
  'phase[[:space:]]+66\.2[[:space:]]+confirms[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|broad[[:space:]]+(wazuh|siem)[^.[:cntrl:]]+(parity|coverage|readiness)|production[[:space:]]+(customer[[:space:]]+)?telemetry[[:space:]]+(import|coverage|readiness)|production[[:space:]]+monitoring[[:space:]]+(coverage|readiness)|commercial[[:space:]]+replacement[[:space:]]+readiness|source[- ]native[[:space:]]+truth|real[[:space:]]+design[- ]partner[[:space:]]+success|phase[[:space:]]+66[[:space:]]+closeout)'
  'phase[[:space:]]+66\.2[[:space:]]+(satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc([[:space:][:punct:]]|$)|release[- ]candidate)'
  'phase[[:space:]]+66\.2[[:space:]]+proves[^.[:cntrl:]]*(rc[- ]?(gate|readiness|pass)|release[- ]candidate[- ]?(gate|readiness|pass))'
  '(phase[[:space:]]+66\.2|this[[:space:]]+proof|proof|aegisops)[[:space:]]+(is|becomes|serves[[:space:]]+as)[[:space:]]+(now[[:space:]]+|already[[:space:]]+|effectively[[:space:]]+)?ready[[:space:]]+for[[:space:]]+(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate)'
  '(this[[:space:]]+)?proof[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms|achieves)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|rc([[:space:][:punct:]]|$)|release[- ]candidate|readiness|broad[[:space:]]+wazuh|broad[[:space:]]+siem|production[[:space:]]+(customer[[:space:]]+)?telemetry|production[[:space:]]+monitoring|source[- ]native|commercial[[:space:]]+replacement)'
  'source[- ]native[[:space:]]+truth[[:space:]]+(is|becomes|serves[[:space:]]+as|accepted|approved|allowed)'
  'broad[[:space:]]+(wazuh|siem)[^.[:cntrl:]]+parity[[:space:]]+(is|becomes|serves[[:space:]]+as|accepted|approved|allowed|achieved|satisfied)'
  'wazuh[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(alert|case|evidence|source([[:space:]-]+admission)?|workflow|release|gate|readiness|closeout)[[:space:]]+truth'
  'wazuh[[:space:]]+(alerts|signals|events|samples)[[:space:]]+(are|become|becomes|serve[[:space:]]+as)[^.[:cntrl:]]*(alert|case|evidence|source([[:space:]-]+admission)?|workflow|release|gate|readiness|closeout)[[:space:]]+truth'
  'wazuh[[:space:]]+alert[[:space:]-]+ids?[[:space:]]+(are|become|becomes|serve[[:space:]]+as)[[:space:]]+(aegisops[[:space:]]+)?alert[[:space:]]+truth'
  'wazuh[- ]origin[[:space:]]+input[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(alert|case|evidence|source([[:space:]-]+admission)?|workflow|release|gate|readiness|closeout)[[:space:]]+truth'
  "${subordinate_authority_subjects}[[:space:]]+(is|are|become|becomes|serve[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(alert|case|evidence|source([[:space:]-]+admission)?|workflow|release|gate|readiness|closeout)[[:space:]]+truth"
  "wazuh[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "wazuh[[:space:]]+(manager|dashboard|indexer|alert|rule|timestamp|webhook)[^.[:cntrl:]]+state[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "(generated[[:space:]-]+config|generated[[:space:]-]+configuration)[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "(ai[[:space:]]+output|browser[[:space:]]+state|ui[[:space:]]+cache|ticket|tickets|downstream[[:space:]]+receipts?)[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  "${subordinate_authority_subjects}[[:space:]]+${authority_verbs}[^.[:cntrl:]]*${authority_objects}"
  '(dashboard[[:space:]]+text|file[[:space:]]+names|filenames)[[:space:]]+(create[s]?|generate[s]?|establish(es)?|prove[s]?|suppl(y|ies))[^.[:cntrl:]]*signal[[:space:]-]+identit'
  '(raw[[:space:]]+forwarded[[:space:]]+headers?|inferred[[:space:]]+linkage)[[:space:]]+(prove[s]?|create[s]?|establish(es)?|suppl(y|ies)|satisf(y|ies))[^.[:cntrl:]]*provenance'
  '(direct|ad[[:space:]-]+hoc)[[:space:]]+intake[[:space:]]+paths?[[:space:]]+(prove[s]?|create[s]?|establish(es)?|suppl(y|ies)|satisf(y|ies))[^.[:cntrl:]]*intake[[:space:]-]+binding'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(ga([[:space:][:punct:]]|$)|general[- ]availability|commercial[[:space:]]+replacement|broad[[:space:]]+siem)'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate|workflow|source)[[:space:]]+truth'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(readiness|release|gate|workflow|source|rc([[:space:][:punct:]]|$)|ga([[:space:][:punct:]]|$))'
)

forbidden_regex="$(IFS='|'; printf '%s' "${forbidden_patterns[*]}")"

scan_forbidden_claims() {
  local file="$1"
  local description="$2"

  if grep -Eiq -- "${forbidden_regex}" < <(visible_text "${file}"); then
    echo "Forbidden Phase 66.2 ${description} claim matched" >&2
    exit 1
  fi
}

scan_forbidden_claims "${absolute_doc_path}" "Wazuh sample signal RC proof"
scan_forbidden_claims "${readme_path}" "README"

if grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|(password|passwd|secret([_ -]?key)?|private[_ -]?key|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- '(^|[[:space:]>*-])`?(journey_run_id|repository_revision|sample_signal_id|source_health_reference|intake_binding_reference|admission_record_id|aegisops_alert_id|provenance_reference|limitation_references)`?[[:space:]]*[:=][[:space:]]*`?(missing|none|null|n/a|tbd|todo|unknown|not[[:space:]_-]*provided|not[[:space:]_-]*set)`?([[:space:].,;)]|$)' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: missing required evidence value detected" >&2
  exit 1
fi

if grep -Eiq -- '(^|[[:space:]>*-])`?limitation_references`?[[:space:]]*[:=][^.[:cntrl:]]*hidden[[:space:]-]+in[[:space:]-]+source[- ]health[[:space:]-]+text' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: hidden limitation references detected" >&2
  exit 1
fi

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" =~ ${repository_revision_value_regex} ]]; then
    echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: mutable repository revision detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${wazuh_profile_value_regex} ]] && [[ "${BASH_REMATCH[2]}" != "smb-single-node" ]]; then
    echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: invalid Wazuh profile detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${source_family_shortcut_regex} ]]; then
    echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: inferred source-family value detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ ${case_linking_value_regex} ]]; then
    case "${BASH_REMATCH[2]}" in
      not_linked|linked_by_aegisops_case_workflow|explicitly_deferred)
        ;;
      *)
        echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: invalid case-linking posture detected" >&2
        exit 1
        ;;
    esac
  fi
  if grep -Eiq -- 'customer[-_ ]private[[:space:]]+data[[:space:]]*[:=]' <<<"${line}"; then
    echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ (must[[:space:]]+reject|rejects|rejected|forbidden|not[[:space:]]+include|must[[:space:]]+not[[:space:]]+include) ]]; then
    continue
  fi
  if grep -Eiq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(data|example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line}"; then
    echo "Forbidden Phase 66.2 Wazuh sample signal RC proof: customer-private data detected" >&2
    exit 1
  fi
done < <(visible_text "${absolute_doc_path}")

path_hygiene_stderr="${repo_root}/.tmp-phase66-2-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 66.2 Wazuh sample signal RC proof absolute path usage detected" >&2
  exit 1
fi

echo "Phase 66.2 Wazuh sample signal RC proof contract and focused negative checks pass."
