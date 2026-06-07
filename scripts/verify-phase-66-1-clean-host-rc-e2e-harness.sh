#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-1-clean-host-rc-e2e-harness.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-65-closeout-evaluation.md"
  "docs/getting-started/first-user-journey.md"
  "docs/getting-started/first-user-demo-report-export.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"
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

require_file "${absolute_doc_path}" "Phase 66.1 clean-host RC E2E harness"
require_file "${readme_path}" "README for Phase 66.1 link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.1 reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.1 verifier script ${verifier_script}"
done

require_phrase "${readme_path}" "- [Phase 66.1 clean-host RC E2E harness](docs/phase-66-1-clean-host-rc-e2e-harness.md) defines the clean-host release-candidate journey contract from setup through report export while preserving Phase 65 as input evidence only and excluding GA, production rollout, self-service commercial, and broad SIEM/SOAR parity claims." "README canonical Phase 66.1 boundary bullet"
require_phrase "${readme_path}" "The Phase 66.1 clean-host RC E2E harness is defined by the [Phase 66.1 clean-host RC E2E harness](docs/phase-66-1-clean-host-rc-e2e-harness.md)." "README Product positioning Phase 66.1 reference"

required_phrases=(
  "# Phase 66.1 Clean-Host RC E2E Harness"
  "**Status**: Accepted as the Phase 66.1 clean-host RC E2E harness contract for release-candidate proof planning only."
  "**Related Issues**: #1397, #1398"
  "This contract defines the Phase 66.1 clean-host RC E2E harness shape for the first release-candidate replacement-readiness journey."
  "Phase 65 packaging evidence is input only."
  'The harness proves that a documented clean-host profile can collect one bounded RC journey packet for `init -> up -> doctor -> seed-demo -> UI workflow -> report export`.'
  "The harness is proof evidence only."
  "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  "Wazuh, Shuffle, AI, reports, UI state, browser state, verifier output, issue-lint output, release artifacts, demo data, tickets, evidence systems, dashboards, support bundles, and downstream receipts remain subordinate context."
  "The harness must reject missing journey steps, missing evidence fields, missing authority boundaries, missing limitations, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, self-service commercial readiness claims, production rollout readiness claims, broad SIEM/SOAR parity claims, verifier-as-readiness-truth, and issue-lint-as-readiness-truth."
  "Phase 66.1 proves the harness shape and evidence contract for one bounded clean-host RC E2E path."
  "Later Phase 66 issues must still prove Wazuh sample signal, Shuffle sample execution, AI-assisted triage, report export, supportability, authority-boundary negative tests, and closeout evidence independently."
  'Run `bash scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh`.'
  'Run `bash scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh`.'
  'Run `bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1398 --config <supervisor-config-path>`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 66.1 harness term in ${doc_path}"
done

profile_section="$(section_text "${absolute_doc_path}" "## 2. Clean-Host Profile" "## 3. Required Journey Steps")"
profile_fields=(
  "| \`journey_run_id\` | Stable identifier for the reviewed RC E2E run. | Missing or reused run identifiers fail the harness. |"
  "| \`repository_revision\` | Immutable repository revision for the harness run. | Mutable branch names fail the harness. |"
  "| \`profile\` | \`smb-single-node\`. | Any other profile must be handled by a later contract. |"
  "| \`environment_class\` | \`clean-host-rc-e2e\`. | Unlabeled local developer state fails the harness. |"
  "| \`runtime_env_reference\` | Repo-relative placeholder such as \`<runtime-env-file>\`. | Workstation-local paths and raw secret material fail the harness. |"
  "| \`operator_role\` | Human operator or maintainer role that performed the run. | Browser state or UI cache cannot stand in for operator identity. |"
  "| \`evidence_dir\` | Repo-relative placeholder such as \`<evidence-dir>\`. | Untracked local paths cannot become proof evidence. |"
  "| \`phase65_input_references\` | Phase 65 closeout and packaging artifacts consumed as subordinate input. | Phase 65 closure cannot satisfy RC E2E by inference. |"
)

for row in "${profile_fields[@]}"; do
  require_section_phrase "${profile_section}" "${row}" "Phase 66.1 clean-host profile field"
done

journey_section="$(section_text "${absolute_doc_path}" "## 3. Required Journey Steps" "## 4. Evidence Packet Fields")"
journey_steps=(
  '`aegisops init --profile smb-single-node`'
  '`aegisops up --with-wazuh --with-shuffle`'
  '`aegisops doctor`'
  '`aegisops seed-demo`'
  "Login"
  "Health review"
  "Queue item"
  "Wazuh-origin signal inspection"
  "Case promotion"
  "Evidence review"
  "AI trace review"
  "Action request"
  "Approval"
  "Shuffle delegation receipt"
  "Reconciliation"
  "Report export"
  "Next-step guidance"
)

for step in "${journey_steps[@]}"; do
  require_section_phrase "${journey_section}" "${step}" "Phase 66.1 required journey step"
done

evidence_section="$(section_text "${absolute_doc_path}" "## 4. Evidence Packet Fields" "## 5. Authority Boundary")"
evidence_fields=(
  "\`journey_run_id\`, \`repository_revision\`, \`profile\`, \`environment_class\`, \`runtime_env_reference\`, \`operator_role\`, \`evidence_dir\`."
  "\`wazuh_signal_id\`, \`source_health_reference\`, \`aegisops_alert_id\`, \`admission_review_id\`, \`provenance_reference\`."
  "\`shuffle_workflow_id\`, \`action_request_id\`, \`approval_decision_id\`, \`execution_receipt_id\`, \`reconciliation_id\`."
  "\`ai_trace_id\`, \`citation_set\`, \`reviewed_recommendation_id\`, \`human_decision\`, \`autonomous_action_refusal\`."
  "\`export_command\`, \`export_artifact_reference\`, \`report_schema_version\`, \`redaction_review_id\`, \`source_record_ids\`."
  "\`doctor_result_id\`, \`support_bundle_posture\`, \`backup_restore_posture\`, \`upgrade_plan_reference\`, \`known_limitation_ids\`."
  "\`limitation_id\`, \`owner\`, \`accepted_or_refused_reason\`, \`decision_date\`, \`follow_up_date\`."
)

for field_group in "${evidence_fields[@]}"; do
  require_section_phrase "${evidence_section}" "${field_group}" "Phase 66.1 evidence packet field group"
done

limitations_section="$(section_text "${absolute_doc_path}" "## 6. Accepted Limitations" "## 7. Verification")"
require_section_phrase "${limitations_section}" "It does not collect real design-partner evidence, prove real design-partner success, complete support-bundle review, complete restore dry-run proof, complete upgrade rehearsal proof, approve production rollout, approve self-service commercial readiness, or satisfy Phase 67 GA readiness." "Phase 66.1 accepted limitations boundary"

forbidden_patterns=(
  'phase[[:space:]]+66\.1[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(ga|general[- ]availability)'
  'phase[[:space:]]+66\.1[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(production[[:space:]]+rollout|self[- ]service[[:space:]]+commercial|broad[[:space:]]+siem|broad[[:space:]]+soar|real[[:space:]]+design[- ]partner)'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(ga|general[- ]availability|production[[:space:]]+rollout|self[- ]service[[:space:]]+commercial|broad[[:space:]]+siem|broad[[:space:]]+soar)'
  '(wazuh|shuffle|ai|report|ui|browser|verifier|issue-lint)[[:space:]]+(output[[:space:]]+)?(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(workflow|gate|release|readiness|reconciliation|approval)[[:space:]]+truth'
  'ai[[:space:]]+(approves|executes|reconciles|closes|activates)[^.[:cntrl:]]*(action|case|detector|record)'
)

while IFS= read -r line || [[ -n "${line}" ]]; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" =~ (does[[:space:]]+not|cannot|must[[:space:]]+reject|reject|out[[:space:]]+of[[:space:]]+scope|no[[:space:]]+) ]]; then
    continue
  fi
  for pattern in "${forbidden_patterns[@]}"; do
    if grep -Eiq -- "${pattern}" <<<"${line}"; then
      echo "Forbidden Phase 66.1 clean-host RC E2E harness claim matched: ${pattern}" >&2
      exit 1
    fi
  done
done < <(visible_text "${absolute_doc_path}")

if grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|(password|passwd|secret|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 66.1 clean-host RC E2E harness: production secret-looking value detected" >&2
  exit 1
fi

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" =~ (reject|without|must[[:space:]]+reject|does[[:space:]]+not|cannot|no[[:space:]]+) ]]; then
    continue
  fi
  if grep -Eiq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line}"; then
    echo "Forbidden Phase 66.1 clean-host RC E2E harness: customer-private data detected" >&2
    exit 1
  fi
done < <(visible_text "${absolute_doc_path}")

path_hygiene_stderr="${repo_root}/.tmp-phase66-1-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 66.1 clean-host RC E2E harness absolute path usage detected" >&2
  exit 1
fi

echo "Phase 66.1 clean-host RC E2E harness contract and focused negative checks pass."
