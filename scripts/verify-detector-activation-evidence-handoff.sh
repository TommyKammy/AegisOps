#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
manifest_doc="${repo_root}/docs/detector-activation-evidence-handoff.md"
exemplar_doc="${repo_root}/docs/deployment/detector-activation-evidence.single-customer-pilot.example.md"
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

reject_placeholders() {
  local path="$1"
  local description="$2"

  if grep -Eiq 'TODO|sample secret|fake secret|placeholder credential|change-me|replace-with|guess(ed)? scope|unsigned token|<replace-[^>]+>|secret=[^[:space:]]+|token=[^[:space:]]+|password=[^[:space:]]+' "${path}"; then
    echo "Placeholder or untrusted ${description} value detected: ${path}" >&2
    exit 1
  fi
}

reject_workstation_paths() {
  local description="$1"
  shift

  local macos_home_pattern linux_home_pattern windows_home_pattern workstation_local_path_pattern
  macos_home_pattern='/'"Users"'/[^[:space:])>]+'
  linux_home_pattern='/'"home"'/[^[:space:])>]+'
  windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

require_file "${manifest_doc}" "detector activation evidence handoff manifest"
require_file "${exemplar_doc}" "filled redacted detector activation evidence exemplar"
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
  'The filled redacted single-customer exemplar in `docs/deployment/detector-activation-evidence.single-customer-pilot.example.md` shows how one GitHub audit detector activation handoff connects Wazuh substrate evidence to AegisOps analytic signal admission without making Wazuh rule state workflow truth.'
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

required_exemplar_text=(
  "# Detector Activation Evidence Handoff - Filled Redacted Single-Customer Pilot Example"
  "Release identifier: aegisops-single-customer-pilot-2026-04-27-c4527e5"
  "Candidate rule identifier: github-audit-privilege-change"
  "Source-family package: GitHub audit via reviewed Wazuh-backed intake boundary"
  "Lifecycle state: staging-review-accepted"
  "Reviewer: pilot-detector-reviewer-redacted"
  "Rule intent: Detect reviewed GitHub organization and repository administrator membership changes that require AegisOps analytic signal admission review before pilot detector scope is accepted."
  "Source scope: GitHub audit organization and repository administration events from the reviewed Wazuh-backed intake fixture set for the single-customer pilot; tenant, repository, organization, actor, and team linkage must not be inferred from names alone."
  "Activation owner: pilot-detector-owner-redacted"
  "Disable owner: pilot-disable-owner-redacted"
  "Rollback owner: pilot-rollback-owner-redacted"
  "Activation window: 2026-04-27T09:00:00+09:00 to 2026-05-04T17:00:00+09:00"
  "Reviewer sign-off: pilot-detector-reviewer-redacted accepted the staging fixture, parser, provenance, expected-volume, false-positive, disable, rollback, and AegisOps record-linkage evidence on 2026-04-27."
  "Repository revision: c4527e5"
  "Expected alert volume: 0-3 alerts per business day during the first pilot week"
  "Expected benign cases: Reviewed repository administration, approved maintainer changes, access review cleanup, automation identity maintenance, scheduled change windows, onboarding, and offboarding activity."
  "False-positive review: Routine repository administration, access review cleanup, automation identity behavior, and scheduled maintenance were reviewed as expected benign cases"
  "Next-review date: 2026-05-04"
  "Fixture evidence: control-plane/tests/fixtures/wazuh/github-audit-alert.json"
  'Parser evidence: decoder.name `github_audit`, rule.id `github-audit-privilege-change`, and source-family parser coverage verified by the GitHub audit detector activation candidate tests'
  "Source field coverage: Reviewed GitHub audit actor, organization, repository, action, membership target, source timestamp, Wazuh manager, decoder, rule, and provenance fields from the exact fixture set."
  "Timestamp quality: Fixture-backed source timestamp and Wazuh ingestion timestamp are present, parseable, and not used to infer activation success without AegisOps record linkage."
  "Provenance evidence: Wazuh manager, decoder, rule, source-family parser coverage, and AegisOps release-gate evidence record are explicitly named before the candidate is admitted."
  "Exact fixture set: control-plane/tests/fixtures/wazuh/github-audit-alert.json at repository revision c4527e5"
  'Validation command result: PASS for `bash scripts/verify-github-audit-detector-activation-candidate.sh`'
  'Wazuh substrate evidence: Wazuh manager `wazuh-manager-github-1`, decoder `github_audit`, rule `github-audit-privilege-change`, and fixture-backed GitHub audit fields are evidence for admission review only'
  'AegisOps analytic signal admission: AegisOps alert `alert-redacted-github-admin-0001`, case `case-redacted-github-admin-0001`, evidence `evidence-redacted-github-admin-0001`, and release-gate record `release-gate-redacted-2026-04-27` are the control-plane records used for handoff review'
  "Admission result: accepted-for-pilot-entry-review"
  'Reviewed linkage: release-gate record `release-gate-redacted-2026-04-27` binds the candidate rule, fixture evidence, parser evidence, reviewer sign-off, activation window, and AegisOps alert, case, and evidence identifiers for this release only.'
  "Authority boundary: Wazuh rule state, raw Wazuh alerts, GitHub audit fields, OpenSearch state, Zammad tickets, and downstream detector receipts remain subordinate evidence; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain workflow truth."
  'Disable path: Move the candidate back to `candidate`, remove it from the reviewed pilot detector scope, and preserve the refused or disabled outcome in the release-gate evidence record before the next health review.'
  "Disable reason: missing parser evidence, missing provenance, unaccepted false-positive rate, missing owner, or missing AegisOps record linkage blocks or disables the reviewed pilot detector scope."
  'Rollback path: Restore the last reviewed fixture set and candidate revision, rerun `bash scripts/verify-github-audit-detector-activation-candidate.sh`, and keep pilot entry blocked if parser evidence, Wazuh provenance, or AegisOps record linkage is missing.'
  "Rollback reason: parser drift, Wazuh provenance drift, candidate revision drift, unsupported source fields, or failed admission sanity requires restoring the reviewed fixture set and candidate revision before pilot entry can continue."
  "Restored rule revision: c4527e5"
  "Restored fixture set: control-plane/tests/fixtures/wazuh/github-audit-alert.json at repository revision c4527e5"
  'Validation rerun result: PASS for `bash scripts/verify-github-audit-detector-activation-candidate.sh` after rollback fixture restoration.'
  "Operator notification path: pilot handoff owner records the disabled or rolled-back detector scope in the release-gate evidence record and the next business health review."
  "Follow-up owner: pilot-detector-owner-redacted"
  "Known limitations: The exemplar covers only the GitHub audit repository administrator membership-change candidate for one pilot release. It does not activate Entra ID, Microsoft 365 audit, endpoint, network, broad detector catalog, automatic detector deployment, direct GitHub API actioning, or live source-side mutation."
  "Clean-state outcome: Rejected activation attempts must leave no orphan alert, partial case, partial durable write, or misleading handoff evidence."
)

for phrase in "${required_exemplar_text[@]}"; do
  require_phrase "${exemplar_doc}" "${phrase}" "filled redacted detector activation evidence exemplar entry"
done

reject_placeholders "${exemplar_doc}" "filled redacted detector activation evidence exemplar"

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

reject_workstation_paths "detector activation evidence handoff guidance" \
  "${manifest_doc}" \
  "${exemplar_doc}" \
  "${wazuh_runbook}" \
  "${github_runbook}" \
  "${entra_runbook}" \
  "${github_candidate}" \
  "${entra_candidate}"

echo "Detector activation evidence handoff manifest and source-family runbook alignment are present and bounded."
