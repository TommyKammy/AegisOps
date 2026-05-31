#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-64-5-phase66-limitation-handoff.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
phase64_contract_path="${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
phase64_records_path="${repo_root}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
phase63_closeout_path="${repo_root}/docs/phase-63-closeout-evaluation.md"
gate_contract_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${file}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 64.5 Phase 66 limitation handoff evidence"
require_file "${readme_path}" "README for Phase 64.5 handoff link check"
require_file "${phase64_contract_path}" "Phase 64.1 known limitation ownership contract"
require_file "${phase64_records_path}" "Phase 64.1 reviewed limitation ownership records"
require_file "${phase63_closeout_path}" "Phase 63 closeout evaluation"
require_file "${gate_contract_path}" "Phase 51.3 gate contract"

require_phrase "${readme_path}" "- [Phase 64.5 Phase 66 limitation handoff](docs/phase-64-5-phase66-limitation-handoff.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 64.5 Phase 66 limitation handoff is defined by the [Phase 64.5 Phase 66 limitation handoff](docs/phase-64-5-phase66-limitation-handoff.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 64.5 Phase 66 Limitation Handoff Evidence
**Status**: Accepted as Phase 66 limitation handoff planning evidence only.
**Related Issues**: #1365, #1367, #1368, #1369, #1370
Phase 64.5 records how Phase 66 may consume reviewed Phase 64 limitation ownership records as subordinate RC proof input without satisfying RC gates by itself.
Phase 66 limitation handoff evidence is planning and review evidence only. It cannot satisfy RC gates, release gates, readiness truth, case truth, approval truth, execution truth, reconciliation truth, closeout truth, gate truth, or limitation truth by itself.
AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.
The handoff references reviewed Phase 64 known limitation ownership records in `docs/phase-64-1-reviewed-limitation-ownership-records.md` as subordinate evidence only.
Every Phase 66 limitation handoff entry requires limitation id, owner, mitigation status, evidence references, open blockers, accepted risks, next review date, and RC-gate consumption notes.
Missing limitation owner, missing mitigation, missing evidence references, missing open blocker list, missing next review date, inferred RC pass, gate truth shortcut, release truth shortcut, verifier-as-readiness-truth, issue-lint-as-readiness-truth, Beta readiness claim, RC readiness claim, GA readiness claim, or commercial readiness claim must fail.
The Phase 66 limitation handoff cannot mark any Pilot, Beta, RC, GA, release, readiness, case, approval, execution, reconciliation, closeout, gate, or limitation truth accepted.
`bash scripts/verify-phase-64-1-known-limitation-ownership-record-contract.sh`
`bash scripts/verify-phase-64-5-phase66-limitation-handoff.sh`
`bash scripts/test-verify-phase-64-5-phase66-limitation-handoff.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`node <codex-supervisor-root>/dist/index.js issue-lint 1370 --config <supervisor-config-path>`
Issue-lint output is planning and metadata evidence only. It does not become readiness truth, release truth, gate truth, limitation truth, closeout truth, or RC proof.
Verifier output is validation evidence only. It does not become readiness truth, release truth, gate truth, limitation truth, closeout truth, or RC proof.
Remaining Phase 66 proof obligations: independent RC gate packet, support bundle evidence, restore evidence, upgrade and rollback evidence, first-user RC behavior, daily-operator RC behavior, supportability evidence, security review, packaging evidence, issue-lint evidence, verifier evidence, and explicit gate acceptance outside this handoff.
No product behavior, source breadth, SOAR breadth, SIEM breadth, evidence collection, AI behavior, operator UI behavior, runtime workflow, release gate execution, RC proof, GA proof, limitation resolution workflow, or production rollout readiness claim is implemented here.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 64.5 handoff term in ${doc_path}"
done

required_record_phrases=()
while IFS= read -r phrase; do
  required_record_phrases+=("${phrase}")
done <<'EOF_RECORD_PHRASE'
# Phase 64.1 Reviewed Limitation Ownership Records
These records instantiate the Phase 64.1 `known_limitation_ownership` contract as reviewed evidence inputs only.
They do not resolve limitations, satisfy RC gates, prove release readiness, approve GA readiness, replace support evidence, create release truth, create gate truth, or create readiness truth.
Phase 66 may consume these records only as subordinate limitation ownership evidence while proving RC gates independently.
| `limitation-phase64-support-bundle-001` | Support bundle evidence remains separately tracked. | material | supportability_evidence | supportability-owner | Track the support bundle slice before Phase 66 RC proof. | `docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition` | accepted_risk | weekly | none | bounded_pre_rc_limitation | handoff_required | reviewed_evidence_input_only |
| `limitation-phase64-rc-gate-consumption-001` | RC gate packet still needs independent proof. | material | release_gate_evidence | release-gate-owner | Keep limitation ownership as subordinate RC packet planning evidence only. | `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`; `docs/phase-64-1-known-limitation-ownership-record-contract.md` | mitigation_planned | weekly | none | gate_consumption_risk_requires_independent_proof | handoff_required | reviewed_evidence_input_only |
### limitation-phase64-support-bundle-001
### limitation-phase64-rc-gate-consumption-001
No product behavior, source behavior, workflow behavior, RC proof, GA proof, release gate execution, or production rollout readiness claim is implemented here.
EOF_RECORD_PHRASE

for phrase in "${required_record_phrases[@]}"; do
  require_phrase "${phase64_records_path}" "${phrase}" "required Phase 64.1 reviewed limitation record term"
done

trim_cell() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

reject_blank_or_placeholder() {
  local value="$1"
  local description="$2"
  local limitation_id="$3"
  local normalized
  local placeholder_key

  value="$(trim_cell "${value}")"
  normalized="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')"
  placeholder_key="$(printf '%s' "${normalized}" | sed -E 's/^`+//; s/`+$//; s/^[[:space:][:punct:]]+//; s/[[:space:][:punct:]]+$//; s/[[:space:][:punct:]]+//g')"

  if [[ -z "${value}" || -z "${placeholder_key}" || "${placeholder_key}" =~ ^(none|na|tbd|todo|placeholder)$ ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: missing ${description}" >&2
    exit 1
  fi
}

normalize_comparison_text() {
  local value="$1"

  printf '%s' "${value}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[-_]+/ /g; s/[[:space:]]+/ /g; s/^ //; s/ $//'
}

require_normalized_contains() {
  local value="$1"
  local expected="$2"
  local description="$3"
  local limitation_id="$4"
  local value_posture
  local normalized_value
  local normalized_expected

  value_posture="${value%%;*}"
  normalized_value="$(normalize_comparison_text "${value_posture}")"
  normalized_expected="$(normalize_comparison_text "${expected}")"

  if [[ -z "${normalized_expected}" || "${normalized_value}" != "${normalized_expected}" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: ${description} does not match reviewed Phase 64 record" >&2
    exit 1
  fi
}

require_backticked_reference() {
  local references="$1"
  local expected="$2"
  local description="$3"
  local limitation_id="$4"
  local reference

  while IFS= read -r reference; do
    reference="${reference#\`}"
    reference="${reference%\`}"

    if [[ "${reference}" == "${expected}" ]]; then
      return 0
    fi
  done < <(grep -oE '`[^`]+`' <<<"${references}" || true)

  echo "Invalid Phase 64.5 handoff row for ${limitation_id}: missing ${description}" >&2
  exit 1
}

reject_no_open_blocker_assertion() {
  local value="$1"
  local limitation_id="$2"
  local normalized

  normalized="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^[:alnum:]]+/ /g; s/[[:space:]]+/ /g; s/^ //; s/ $//')"

  if [[ "${normalized}" =~ (^|[[:space:]])no[[:space:]]+open[[:space:]]+blockers?([[:space:]]+remain)?($|[[:space:]]) || \
        "${normalized}" =~ (^|[[:space:]])no[[:space:]]+remaining[[:space:]]+blockers?($|[[:space:]]) || \
        "${normalized}" =~ (^|[[:space:]])all[[:space:]]+blockers?[[:space:]]+(resolved|closed|cleared)($|[[:space:]]) ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: open blockers must list remaining blockers" >&2
    exit 1
  fi
}

require_real_iso_date() {
  local value="$1"
  local description="$2"
  local limitation_id="$3"
  local year
  local month
  local day
  local year_number
  local month_number
  local day_number
  local max_day

  if [[ ! "${value}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: ${description} must use YYYY-MM-DD" >&2
    exit 1
  fi

  year="${value:0:4}"
  month="${value:5:2}"
  day="${value:8:2}"
  year_number=$((10#${year}))
  month_number=$((10#${month}))
  day_number=$((10#${day}))

  if (( month_number < 1 || month_number > 12 )); then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: ${description} must use a real YYYY-MM-DD calendar date" >&2
    exit 1
  fi

  case "${month_number}" in
    1|3|5|7|8|10|12) max_day=31 ;;
    4|6|9|11) max_day=30 ;;
    2)
      if (( (year_number % 400 == 0) || (year_number % 4 == 0 && year_number % 100 != 0) )); then
        max_day=29
      else
        max_day=28
      fi
      ;;
  esac

  if (( day_number < 1 || day_number > max_day )); then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: ${description} must use a real YYYY-MM-DD calendar date" >&2
    exit 1
  fi
}

handoff_document_date="$(sed -nE 's/^- \*\*Date\*\*: ([0-9]{4}-[0-9]{2}-[0-9]{2})$/\1/p' "${absolute_doc_path}" | head -n 1)"
if [[ -z "${handoff_document_date}" ]]; then
  echo "Missing Phase 64.5 handoff document date" >&2
  exit 1
fi

require_real_iso_date "${handoff_document_date}" "handoff document date" "document"

handoff_ids=""

validate_handoff_row() {
  local row="$1"
  local pipe_count
  local empty_prefix
  local limitation_id_cell
  local owner
  local mitigation_status
  local evidence_references
  local open_blockers
  local accepted_risks
  local next_review_date
  local rc_gate_notes
  local empty_suffix
  local limitation_id
  local reviewed_record_reference
  local reviewed_record_matches
  local reviewed_record_count
  local reviewed_record_row
  local record_limitation_id_cell
  local record_title
  local record_severity
  local record_affected_surface
  local record_owner
  local record_mitigation
  local record_evidence_references
  local record_review_state
  local record_review_cadence
  local record_due_date
  local record_accepted_risk_posture
  local record_handoff_posture
  local record_authority_boundary
  local record_evidence_reference
  local record_evidence_reference_target

  if [[ ! "${row}" =~ ^\|.*\|[[:space:]]*$ ]]; then
    echo "Invalid Phase 64.5 handoff table row: ${row}" >&2
    exit 1
  fi

  pipe_count="$(grep -o '|' <<<"${row}" | wc -l | tr -d '[:space:]')"
  if [[ "${pipe_count}" != "9" ]]; then
    echo "Invalid Phase 64.5 handoff table row: expected 8 columns: ${row}" >&2
    exit 1
  fi

  IFS='|' read -r empty_prefix limitation_id_cell owner mitigation_status evidence_references open_blockers accepted_risks next_review_date rc_gate_notes empty_suffix <<<"${row}"

  limitation_id_cell="$(trim_cell "${limitation_id_cell}")"
  if [[ ! "${limitation_id_cell}" =~ ^\`limitation-phase64-[a-z0-9-]+-[0-9]{3}\`$ ]]; then
    echo "Invalid Phase 64.5 handoff row limitation id: ${limitation_id_cell}" >&2
    exit 1
  fi

  limitation_id="${limitation_id_cell#\`}"
  limitation_id="${limitation_id%\`}"

  reject_blank_or_placeholder "${owner}" "owner" "${limitation_id}"
  reject_blank_or_placeholder "${mitigation_status}" "mitigation status" "${limitation_id}"
  reject_blank_or_placeholder "${evidence_references}" "evidence references" "${limitation_id}"
  reject_blank_or_placeholder "${open_blockers}" "open blockers" "${limitation_id}"
  reject_blank_or_placeholder "${accepted_risks}" "accepted risks" "${limitation_id}"
  reject_blank_or_placeholder "${next_review_date}" "next review date" "${limitation_id}"
  reject_blank_or_placeholder "${rc_gate_notes}" "RC-gate consumption notes" "${limitation_id}"
  reject_no_open_blocker_assertion "${open_blockers}" "${limitation_id}"

  next_review_date="$(trim_cell "${next_review_date}")"
  require_real_iso_date "${next_review_date}" "next review date" "${limitation_id}"

  if [[ "${next_review_date}" < "${handoff_document_date}" || "${next_review_date}" == "${handoff_document_date}" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: next review date must be after the handoff document date" >&2
    exit 1
  fi

  if [[ -n "${handoff_ids}" ]] && grep -Fxq -- "${limitation_id}" <<<"${handoff_ids}"; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: duplicate Phase 64.5 handoff rows" >&2
    exit 1
  fi

  reviewed_record_reference="docs/phase-64-1-reviewed-limitation-ownership-records.md#${limitation_id}"
  require_backticked_reference "${evidence_references}" "${reviewed_record_reference}" "reviewed Phase 64 limitation record reference" "${limitation_id}"

  reviewed_record_matches="$(grep -F -- "| \`${limitation_id}\` |" "${phase64_records_path}" || true)"
  if [[ -z "${reviewed_record_matches}" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: reviewed Phase 64 limitation record is absent" >&2
    exit 1
  fi

  reviewed_record_count="$(printf '%s\n' "${reviewed_record_matches}" | wc -l | tr -d '[:space:]')"
  if [[ "${reviewed_record_count}" != "1" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: duplicate reviewed Phase 64 limitation records" >&2
    exit 1
  fi

  reviewed_record_row="${reviewed_record_matches}"

  IFS='|' read -r empty_prefix record_limitation_id_cell record_title record_severity record_affected_surface record_owner record_mitigation record_evidence_references record_review_state record_review_cadence record_due_date record_accepted_risk_posture record_handoff_posture record_authority_boundary empty_suffix <<<"${reviewed_record_row}"

  record_owner="$(trim_cell "${record_owner}")"
  record_evidence_references="$(trim_cell "${record_evidence_references}")"
  record_review_state="$(trim_cell "${record_review_state}")"
  record_accepted_risk_posture="$(trim_cell "${record_accepted_risk_posture}")"
  record_handoff_posture="$(trim_cell "${record_handoff_posture}")"

  if [[ "$(trim_cell "${owner}")" != "${record_owner}" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: owner does not match reviewed Phase 64 record" >&2
    exit 1
  fi

  if [[ "${record_handoff_posture}" != "handoff_required" ]]; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: reviewed Phase 64 record is not marked for handoff" >&2
    exit 1
  fi

  while IFS= read -r record_evidence_reference; do
    record_evidence_reference_target="${record_evidence_reference#\`}"
    record_evidence_reference_target="${record_evidence_reference_target%\`}"

    if [[ -z "${record_evidence_reference}" ]]; then
      continue
    fi

    require_backticked_reference "${evidence_references}" "${record_evidence_reference_target}" "reviewed Phase 64 evidence reference ${record_evidence_reference}" "${limitation_id}"
  done < <(grep -oE '`[^`]+`' <<<"${record_evidence_references}" || true)

  require_normalized_contains "${mitigation_status}" "${record_review_state}" "mitigation status" "${limitation_id}"
  require_normalized_contains "${accepted_risks}" "${record_accepted_risk_posture}" "accepted risks" "${limitation_id}"

  if ! grep -Eiq '(subordinate|no rc gate|does not satisfy|independent)' <<<"${rc_gate_notes}"; then
    echo "Invalid Phase 64.5 handoff row for ${limitation_id}: RC-gate consumption notes must preserve subordinate handoff boundary" >&2
    exit 1
  fi

  handoff_ids="${handoff_ids}${limitation_id}"$'\n'
}

handoff_row_count=0
in_handoff_entries=0
in_handoff_table=0
while IFS= read -r row; do
  trimmed_row="$(trim_cell "${row}")"

  if [[ "${trimmed_row}" == "## Handoff Entries" ]]; then
    in_handoff_entries=1
    continue
  fi

  if (( in_handoff_entries == 0 )); then
    continue
  fi

  if [[ "${trimmed_row}" =~ ^##[[:space:]] ]]; then
    break
  fi

  if [[ -z "${trimmed_row}" ]]; then
    if (( in_handoff_table == 1 )); then
      break
    fi
    continue
  fi

  if [[ "${trimmed_row}" == "| Limitation id | Owner | Mitigation status | Evidence references | Open blockers | Accepted risks | Next review date | RC-gate consumption notes |" ]]; then
    in_handoff_table=1
    continue
  fi

  if (( in_handoff_table == 1 )); then
    if [[ "${trimmed_row}" == "| --- | --- | --- | --- | --- | --- | --- | --- |" ]]; then
      continue
    fi

    if [[ ! "${trimmed_row}" =~ ^\| ]]; then
      echo "Invalid Phase 64.5 handoff table row: ${row}" >&2
      exit 1
    fi

    validate_handoff_row "${trimmed_row}"
    handoff_row_count=$((handoff_row_count + 1))
  fi
done < "${absolute_doc_path}"

if (( handoff_row_count == 0 )); then
  echo "Missing Phase 64.5 handoff table rows" >&2
  exit 1
fi

while IFS= read -r row; do
  trimmed_row="$(trim_cell "${row}")"

  if [[ ! "${trimmed_row}" =~ ^\|[[:space:]]+\`limitation-phase64-[a-z0-9-]+-[0-9]{3}\`[[:space:]]+\| ]]; then
    continue
  fi

  if [[ ! "${trimmed_row}" == *"| handoff_required |"* ]]; then
    continue
  fi

  IFS='|' read -r empty_prefix limitation_id_cell _ <<<"${trimmed_row}"
  limitation_id_cell="$(trim_cell "${limitation_id_cell}")"
  limitation_id="${limitation_id_cell#\`}"
  limitation_id="${limitation_id%\`}"

  if ! grep -Fxq -- "${limitation_id}" <<<"${handoff_ids}"; then
    echo "Missing Phase 64.5 handoff row for reviewed Phase 64 limitation: ${limitation_id}" >&2
    exit 1
  fi
done < "${phase64_records_path}"

path_hygiene_text() {
  local file="$1"

  tr '[:upper:]' '[:lower:]' < "${file}" | \
    sed 's#\\/#/#g' | \
    perl -pe 'for my $decode_round (1, 2, 3, 4, 5) { s/%([0-9a-f]{2})/chr(hex($1))/eg; }'
}

absolute_path_boundary='(^|[[:space:](){}<>;,!?`"'\''"])'
generic_absolute_path_boundary='(^|[[:space:](){}<;,!?`"'\''=])'
slash="/"
users_segment="users"
home_segment="home"
root_segment="root"
volumes_segment="volumes"
var_segment="var"
private_segment="private"
etc_segment="etc"
tmp_segment="tmp"
opt_segment="opt"
mnt_segment="mnt"
local_root_name_pattern="(users|home|root|volumes|var|private|etc|tmp|opt|mnt)"
local_root_tail_pattern="(/[^[:space:]]*|[[:space:](){}<>;,!?=.]|$)"
local_path_pattern="(${slash}${users_segment}${slash}|${slash}${home_segment}${slash}|${slash}${root_segment}${slash}|${slash}${volumes_segment}${slash}|${slash}${var_segment}${slash}folders${slash}|${slash}${private_segment}${slash}${var_segment}${slash}folders${slash}|${slash}${etc_segment}${slash}|${slash}${tmp_segment}${slash}|${slash}${private_segment}${slash}${tmp_segment}${slash}|${slash}${opt_segment}${slash}|${slash}${mnt_segment}${slash}[a-z]${slash}|[a-z]:\\\\+${users_segment}\\\\+|[a-z]:${slash}${users_segment}${slash})"
local_path_with_tail="${local_path_pattern}[^[:space:]]*"
absolute_path_pattern="(${absolute_path_boundary}${local_path_with_tail}|file:(//localhost)?/*${local_path_with_tail})"
generic_unix_local_absolute_path_pattern="${generic_absolute_path_boundary}/${local_root_name_pattern}${local_root_tail_pattern}"
generic_windows_absolute_path_pattern='(^|[[:space:](){}<>;,!`"'\''?&])([a-z]:\\+[^[:space:]]*|[a-z]:/[^[:space:]]*)'

if path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   path_hygiene_text "${phase64_records_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${generic_unix_local_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${generic_unix_local_absolute_path_pattern}" || \
   path_hygiene_text "${phase64_records_path}" | grep -Eq -- "${generic_unix_local_absolute_path_pattern}" || \
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${generic_windows_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${generic_windows_absolute_path_pattern}" || \
   path_hygiene_text "${phase64_records_path}" | grep -Eq -- "${generic_windows_absolute_path_pattern}"; then
  echo "Forbidden Phase 64.5 handoff: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="No product behavior, source breadth, SOAR breadth, SIEM breadth, evidence collection, AI behavior, operator UI behavior, runtime workflow, release gate execution, RC proof, GA proof, limitation resolution workflow, or production rollout readiness claim is implemented here."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"
required_rejection_line="Missing limitation owner, missing mitigation, missing evidence references, missing open blocker list, missing next review date, inferred RC pass, gate truth shortcut, release truth shortcut, verifier-as-readiness-truth, issue-lint-as-readiness-truth, Beta readiness claim, RC readiness claim, GA readiness claim, or commercial readiness claim must fail."
required_rejection_line_lower="$(printf '%s' "${required_rejection_line}" | tr '[:upper:]' '[:lower:]')"
forbidden_claim_pattern='(aegisops is beta ready|aegisops is rc ready|aegisops is ga ready|aegisops is release ready|aegisops is production ready|phase 66 rc proof is complete|phase 66 proves rc readiness|phase 64\.5 proves rc readiness|phase 64\.5 satisfies rc gates|phase 64\.5 satisfies release gates|handoff infers rc pass|inferred rc pass|rc readiness is complete|beta readiness is complete|ga readiness is complete|commercial readiness is complete|production rollout readiness is complete|handoff evidence is gate truth|handoff evidence is release truth|handoff evidence is readiness truth|verifier output is readiness truth|verifier as readiness truth|issue lint output is readiness truth|issue lint as readiness truth|release truth shortcut|gate truth shortcut|rc gate is accepted by this handoff|release gate is accepted by this handoff|gate is accepted by this handoff)'
forbidden_compact_claim_pattern='(aegisopsisbetaready|aegisopsisrcready|aegisopsisgaready|aegisopsisreleaseready|aegisopsisproductionready|phase66rcproofiscomplete|phase66provesrcreadiness|phase645provesrcreadiness|phase645satisfiesrcgates|phase645satisfiesreleasegates|handoffinfersrcpass|inferredrcpass|rcreadinessiscomplete|betareadinessiscomplete|gareadinessiscomplete|commercialreadinessiscomplete|productionrolloutreadinessiscomplete|handoffevidenceisgatetruth|handoffevidenceisreleasetruth|handoffevidenceisreadinesstruth|verifieroutputisreadinesstruth|verifierasreadinesstruth|issuelintoutputisreadinesstruth|issuelintasreadinesstruth|releasetruthshortcut|gatetruthshortcut|rcgateisacceptedbythishandoff|releasegateisacceptedbythishandoff|gateisacceptedbythishandoff)'

scan_forbidden_claims() {
  local file="$1"
  local file_label="$2"
  local offender
  local perl_status

  set +e
  offender="$(ALLOWED_NON_CLAIM_LINE="${allowed_non_claim_line_lower}" \
    REQUIRED_REJECTION_LINE="${required_rejection_line_lower}" \
    FORBIDDEN_CLAIM_PATTERN="${forbidden_claim_pattern}" \
    FORBIDDEN_COMPACT_CLAIM_PATTERN="${forbidden_compact_claim_pattern}" \
    perl -ne '
      chomp(my $line = $_);
      my $line_lower = lc $line;
      next if $line_lower eq $ENV{"ALLOWED_NON_CLAIM_LINE"} || $line_lower eq $ENV{"REQUIRED_REJECTION_LINE"};

      my $normalized_line = $line_lower;
      $normalized_line =~ s/[-_]+/ /g;
      $normalized_line =~ s/[[:space:]]+/ /g;

      my $compact_line = $line_lower;
      $compact_line =~ s/[^[:alnum:]]//g;

      if ($normalized_line =~ /$ENV{"FORBIDDEN_CLAIM_PATTERN"}/ || $compact_line =~ /$ENV{"FORBIDDEN_COMPACT_CLAIM_PATTERN"}/) {
        print $line;
        exit 2;
      }
    ' "${file}")"
  perl_status=$?
  set -e

  if [[ "${perl_status}" == "2" ]]; then
    echo "Forbidden Phase 64.5 handoff claim in ${file_label}: ${offender}" >&2
    exit 1
  fi

  if [[ "${perl_status}" != "0" ]]; then
    echo "Failed to scan Phase 64.5 handoff claims in ${file_label}" >&2
    exit 1
  fi
}

scan_forbidden_claims "${absolute_doc_path}" "${doc_path}"
scan_forbidden_claims "${readme_path}" "README.md"
scan_forbidden_claims "${phase64_records_path}" "docs/phase-64-1-reviewed-limitation-ownership-records.md"

echo "Phase 64.5 Phase 66 limitation handoff evidence verifier passes."
