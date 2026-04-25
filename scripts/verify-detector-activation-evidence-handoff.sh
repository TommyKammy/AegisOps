#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
manifest_doc="${repo_root}/docs/detector-activation-evidence-handoff.md"
wazuh_runbook="${repo_root}/docs/wazuh-rule-lifecycle-runbook.md"
github_runbook="${repo_root}/docs/source-families/github-audit/analyst-triage-runbook.md"
entra_runbook="${repo_root}/docs/source-families/entra-id/analyst-triage-runbook.md"
github_candidate="${repo_root}/docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md"
entra_candidate="${repo_root}/docs/source-families/entra-id/detector-activation-candidates/privileged-role-assignment.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_absent_case_insensitive() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${manifest_doc}" "detector activation evidence handoff manifest"
require_file "${wazuh_runbook}" "Wazuh rule lifecycle runbook"
require_file "${github_runbook}" "GitHub audit analyst triage runbook"
require_file "${entra_runbook}" "Entra ID analyst triage runbook"
require_file "${github_candidate}" "GitHub audit detector activation candidate"
require_file "${entra_candidate}" "Entra ID detector activation candidate"

required_manifest_text=(
  "# Detector Activation Evidence Handoff Manifest"
  "The detector activation evidence handoff is a compact review package for Phase 40 detector activation, disable, and rollback decisions."
  "The manifest is evidence custody only; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain authoritative."
  "It must not become a compliance archive platform, unlimited detector history system, external ticket authority, or optional-extension prerequisite."
  "## 2. Manifest Fields"
  "| Field | Required evidence | Authority boundary |"
  "| Rule review evidence | Candidate rule identifier, lifecycle state, source-family package, reviewer, rule intent, source scope, expected alert volume, expected benign cases, false-positive review, next-review date, and activation owner. | Rule review evidence gates activation but does not make the detector source authoritative for case or workflow truth. |"
  "| Fixture and parser evidence | Reviewed fixture paths, parser or decoder identity, validation command result, source field coverage, timestamp quality, provenance evidence, and the exact fixture set used for review. | Fixture evidence proves the admitted alert shape only; parser drift or fixture drift blocks activation until refreshed review is recorded. |"
  "| Activation evidence | Activation window, reviewer sign-off, activation owner, disable owner, rollback owner, release-gate evidence record, repository revision, and the AegisOps alert, case, evidence, or reconciliation identifiers that received detector evidence. | Activation is accepted only through AegisOps-owned records and release-gate evidence, not through Wazuh, OpenSearch, GitHub, Entra ID, or ticket status alone. |"
  "| Rollback and disable evidence | Disable reason, rollback reason, restored rule revision, restored fixture set, validation rerun result, operator notification path, follow-up owner, and release-gate evidence record. | Rollback is a non-destructive content, rule-set, fixture, and validation reset path; it does not authorize direct source-side mutation or undocumented hotfixes. |"
  "| Alert or case admission sanity | AegisOps alert, case, evidence, or reconciliation identifiers, admission result, reviewed linkage to the source-family record, and clean-state outcome for failed or rejected paths. | Case admission remains control-plane-owned and must fail closed when provenance, scope, linkage, or snapshot consistency is missing. |"
  "| Known limitations | Deferred detector behavior, unsupported source fields, parser gaps, expected false-positive limits, retention limit, optional-extension non-requirements, and follow-up owner. | Limitations preserve review context without creating an unlimited history system or expanding detector authority. |"
  "## 3. Required Review Questions"
  "- Does the handoff name the exact candidate rule, source-family package, fixture set, validation command result, reviewer, activation owner, disable owner, rollback owner, and next-review date?"
  "- Does the handoff cite AegisOps-owned alert, case, evidence, reconciliation, or release-gate records for activation and rollback evidence?"
  "- Did alert or case admission preserve explicit reviewed linkage, fail closed on missing provenance or scope, and leave no orphan record, partial durable write, or half-admitted case after rejected paths?"
  "## 4. Source-Family Alignment"
  "GitHub audit and Entra ID runbooks must point detector activation review to this manifest before a candidate moves beyond staging review."
  "## 5. Validation"
  'Run `scripts/verify-detector-activation-evidence-handoff.sh` after changing this manifest, the GitHub audit runbook, the Entra ID runbook, or detector activation candidate evidence.'
  "## 6. Out of Scope"
  "Unlimited detector history retention, compliance archive platform design, external ticket authority, direct GitHub API actioning, direct Entra ID actioning, optional-extension startup gates, and source-owned workflow truth are out of scope."
)

for phrase in "${required_manifest_text[@]}"; do
  require_phrase "${manifest_doc}" "${phrase}" "detector activation evidence handoff manifest statement"
done

required_alignment_text=(
  'Detector activation evidence handoff must use `docs/detector-activation-evidence-handoff.md` as the manifest for rule review evidence, fixture and parser evidence, activation evidence, rollback evidence, alert or case admission sanity, and known limitations.'
  "The handoff must cite AegisOps-owned alert, case, evidence, reconciliation, or release-gate records; source-family output, Wazuh status, OpenSearch status, GitHub status, Entra ID status, and external ticket fields are evidence only."
  "Missing provenance, missing parser evidence, missing reviewer ownership, inferred scope linkage, placeholder credentials, or mixed-snapshot admission evidence blocks activation handoff until the prerequisite is supplied."
)

for phrase in "${required_alignment_text[@]}"; do
  require_phrase "${github_runbook}" "${phrase}" "GitHub audit detector handoff alignment"
  require_phrase "${entra_runbook}" "${phrase}" "Entra ID detector handoff alignment"
done

require_phrase "${wazuh_runbook}" '`docs/detector-activation-evidence-handoff.md` is the reviewed detector activation evidence handoff manifest for Phase 40 activation, disable, rollback, alert or case admission sanity, and known limitations.' "Wazuh runbook detector handoff manifest link"
require_phrase "${github_candidate}" 'Activation handoff must follow `docs/detector-activation-evidence-handoff.md` before this candidate moves beyond staging review.' "GitHub candidate detector handoff link"
require_phrase "${entra_candidate}" 'Activation handoff must follow `docs/detector-activation-evidence-handoff.md` before this candidate moves beyond staging review.' "Entra ID candidate detector handoff link"

for path in "${manifest_doc}" "${github_runbook}" "${entra_runbook}" "${github_candidate}" "${entra_candidate}"; do
  require_absent_case_insensitive "${path}" "requires unlimited retention" "detector handoff boundary statement"
  require_absent_case_insensitive "${path}" "optional extension prerequisite" "detector handoff prerequisite statement"
  require_absent_case_insensitive "${path}" "direct GitHub API actioning is approved" "GitHub authority statement"
  require_absent_case_insensitive "${path}" "direct Entra ID actioning is approved" "Entra ID authority statement"
done

echo "Detector activation evidence handoff manifest and source-family runbook alignment are present and bounded."
