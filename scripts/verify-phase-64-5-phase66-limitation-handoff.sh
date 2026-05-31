#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-64-5-phase66-limitation-handoff.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
phase64_contract_path="${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
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
The handoff references Phase 64 known limitation ownership records as subordinate evidence only.
Every Phase 66 limitation handoff entry requires limitation id, owner, mitigation status, evidence references, open blockers, accepted risks, next review date, and RC-gate consumption notes.
Missing limitation owner, missing mitigation, missing evidence references, missing open blocker list, missing next review date, inferred RC pass, gate truth shortcut, release truth shortcut, verifier-as-readiness-truth, issue-lint-as-readiness-truth, Beta readiness claim, RC readiness claim, GA readiness claim, or commercial readiness claim must fail.
The Phase 66 limitation handoff cannot mark any Pilot, Beta, RC, GA, release, readiness, case, approval, execution, reconciliation, closeout, gate, or limitation truth accepted.
| `limitation-phase64-support-bundle-001` | supportability-owner | accepted risk; support bundle evidence remains separately tracked | `docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition`; `docs/phase-64-1-known-limitation-ownership-record-contract.md` | Phase 51.3 support bundle command, redaction review, included record identifiers, omitted private data classes, owner, retention expectation, and verifier evidence remain required before RC proof can treat support evidence as satisfied. | bounded pre-RC limitation accepted only as reviewed ownership evidence | 2026-06-15 | Phase 66 may cite this as subordinate limitation ownership evidence only; it does not satisfy support bundle evidence, RC readiness, release truth, or gate truth. |
| `limitation-phase64-rc-gate-consumption-001` | release-gate-owner | mitigation planned; RC packet assembly still needs independent gate proof | `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`; `docs/phase-64-1-known-limitation-ownership-record-contract.md` | RC gate packet must still prove install, Wazuh signal, Shuffle execution, AI trace, report export, restore dry-run, upgrade plan, support bundle, and limitations ownership evidence against the approved RC gate. | gate consumption risk accepted only when limitation ownership stays subordinate | 2026-06-15 | Phase 66 may use the owner, mitigation, risk, and review-date fields to plan RC proof; no RC gate is accepted by this handoff. |
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
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${generic_unix_local_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${generic_unix_local_absolute_path_pattern}" || \
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${generic_windows_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${generic_windows_absolute_path_pattern}"; then
  echo "Forbidden Phase 64.5 handoff: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="No product behavior, source breadth, SOAR breadth, SIEM breadth, evidence collection, AI behavior, operator UI behavior, runtime workflow, release gate execution, RC proof, GA proof, limitation resolution workflow, or production rollout readiness claim is implemented here."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"
required_rejection_line="Missing limitation owner, missing mitigation, missing evidence references, missing open blocker list, missing next review date, inferred RC pass, gate truth shortcut, release truth shortcut, verifier-as-readiness-truth, issue-lint-as-readiness-truth, Beta readiness claim, RC readiness claim, GA readiness claim, or commercial readiness claim must fail."
required_rejection_line_lower="$(printf '%s' "${required_rejection_line}" | tr '[:upper:]' '[:lower:]')"

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${line_lower}" == "${allowed_non_claim_line_lower}" || "${line_lower}" == "${required_rejection_line_lower}" ]]; then
    continue
  fi

  if grep -Eiq '(aegisops is beta ready|aegisops is rc ready|aegisops is ga ready|phase 66 rc proof is complete|phase 66 proves rc readiness|phase 64\.5 proves rc readiness|phase 64\.5 satisfies rc gates|phase 64\.5 satisfies release gates|handoff evidence is gate truth|handoff evidence is release truth|handoff evidence is readiness truth|verifier output is readiness truth|issue-lint output is readiness truth|release truth shortcut|gate truth shortcut|commercial readiness is complete|production rollout readiness is complete)' <<<"${line_lower}"; then
    echo "Forbidden Phase 64.5 handoff claim: ${line}" >&2
    exit 1
  fi
done < "${absolute_doc_path}"

echo "Phase 64.5 Phase 66 limitation handoff evidence verifier passes."
