#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-58-5-upgrade-rollback-plan-contract.md"

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 58.5 upgrade rollback plan contract: ${doc_path}" >&2
  exit 1
fi

doc_text="$(<"${doc_path}")"

required_phrases=(
  "# Phase 58.5 Upgrade And Rollback Plan Contract"
  "Phase 58.5 defines the reviewed upgrade plan and rollback plan evidence"
  "Upgrade and rollback plans are reviewed planning evidence only."
  "upgrades, run rollbacks, mutate substrate state, approve release readiness,"
  "No live upgrade command, rollback command, scheduler, queue worker, substrate"
  "- Contract verifier: \`bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh\`."
  "- Focused verifier regression: \`bash scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh\`."
  "- Path hygiene: \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "- Issue lint: \`node <codex-supervisor-root>/dist/index.js issue-lint 1240 --config <supervisor-config-path>\`."
  "| \`version_before\` | Reviewed current AegisOps, profile, substrate, or package version before the proposed change. | Missing, floating, \`latest\`, beta, RC, TODO, or inferred versions fail. |"
  "| \`version_after\` | Reviewed target AegisOps, profile, substrate, or package version after the proposed change. | Missing, floating, \`latest\`, beta, RC, TODO, or unreviewed target versions fail. |"
  "| \`target_profile\` | Explicit reviewed deployment profile, product profile, substrate profile, or package profile affected by the plan. | Missing, guessed, path-derived, issue-title-derived, or operator-comment-derived profile binding fails. |"
  "| \`preflight_result\` | Reviewed preflight evidence reference proving the current state is eligible for planning review. | Missing, failed, stale, placeholder, sample, or Wazuh-only preflight evidence fails. |"
  "| \`backup_reference\` | Reviewed Phase 58.3 backup manifest or restore rehearsal reference used before the plan is considered reviewable. | Missing, placeholder, Wazuh-only, ticket-only, or inferred backup evidence fails. |"
  "| \`rollback_owner\` | Named accountable owner or owner group for rollback decisions. | Missing, placeholder, sample, broad operator discretion, or inferred owner fails. |"
  "| \`rollback_trigger\` | Reviewed condition that requires rollback review or rejects continued upgrade progress. | Missing, placeholder, broad operator discretion, TODO, or post-facto trigger definition fails. |"
  "| \`rollback_target\` | Reviewed restore point, configuration revision, package revision, or profile revision to return to if rollback is triggered. | Missing, guessed, ticket-only, dashboard-only, or memory-derived rollback targets fail. |"
  "| \`known_limitations\` | Reviewed limitations, non-goals, unsafe states, and retained manual steps for the proposed change. | Missing limitations or commercial-readiness, RC, GA, or replacement overclaims fail. |"
  "| \`evidence_links\` | Links to AegisOps-owned release, restore, backup, source-health, smoke, or validation evidence records. | Missing links, Wazuh-only links, Shuffle-only links, ticket-only links, or operator-facing status text alone fails. |"
  "| \`authority_boundary\` | Explicit statement that plans are subordinate planning evidence and cannot mutate substrate state or replace AegisOps truth. | Missing boundary or plan-as-authority claims fail. |"
  "| \`incompatible_version\` | \`version_before\` or \`version_after\` is unsupported, floating, unreviewed, beta, RC, \`latest\`, or inconsistent with the target profile. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |"
  "| \`missing_backup_evidence\` | \`backup_reference\` is absent, placeholder-only, ticket-only, Wazuh-only, stale, or not tied to reviewed custody evidence. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |"
  "| \`missing_rollback_owner\` | Rollback owner is absent, TODO-only, sample-only, inferred from a team name, or broad operator discretion. | Reject the plan before any maintenance window is accepted. |"
  "| \`missing_rollback_trigger\` | Rollback trigger is absent, placeholder-only, after-the-fact, or leaves rollback to vague operator judgment. | Reject the plan before any maintenance window is accepted. |"
  "| \`unsafe_plan_state\` | Plan claims silent upgrade, automatic rollback, substrate mutation, release truth, gate truth, restore truth, workflow truth, or closeout truth. | Keep the guard in place and require a reviewed follow-up contract. |"
  "| \`placeholder_evidence\` | Evidence links, owners, triggers, versions, preflight results, or rollback targets use TODO, sample, example, fake, guessed, or unsigned values. | Reject the plan until a trusted evidence source is supplied. |"
  "| \`plan_as_release_truth\` | Plan evidence is used to approve release readiness, close a gate, close a workflow, prove restore success, or replace Phase 51 gate records. | Reject the plan and preserve authoritative AegisOps record-chain truth. |"
  "| \`substrate_mutation\` | Plan review attempts to mutate Wazuh, Shuffle, PostgreSQL, OpenSearch, proxy, runtime config, schema, or package state. | Reject the operation; Phase 58.5 is planning evidence only. |"
  "Upgrade plans and rollback plans are subordinate planning evidence."
  "control-plane records remain authoritative for alert, case, evidence, approval,"
  "Plan validation cannot approve release readiness, satisfy Pilot, Beta, RC, or GA"
  "When provenance, target profile, preflight, backup, rollback owner, rollback"
  "- silent upgrade claims;"
  "- unsafe rollback claims;"
  "- missing owner evidence;"
  "- missing trigger evidence;"
  "- placeholder evidence;"
  "- plan-as-release-truth claims;"
  "- substrate mutation claims;"
  "- incompatible version claims;"
  "- missing backup evidence;"
  "- workstation-local absolute path guidance."
  "Phase 58.5 does not implement live upgrade execution, live rollback execution,"
  "silent upgrade, automatic rollback, Wazuh broad upgrader behavior, Shuffle broad"
  "- \`bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh\`"
  "- \`bash scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh\`"
  "- \`bash scripts/verify-publishable-path-hygiene.sh\`"
  "- \`node <codex-supervisor-root>/dist/index.js issue-lint 1240 --config <supervisor-config-path>\`"
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_text}"; then
    echo "Missing Phase 58.5 upgrade rollback plan contract statement: ${phrase}" >&2
    exit 1
  fi
done

for forbidden in \
  "silent upgrade is allowed" \
  "silent upgrade can proceed" \
  "upgrade plan is release truth" \
  "rollback plan is release truth" \
  "upgrade plan is gate truth" \
  "rollback plan is workflow truth" \
  "plan validation approves release readiness" \
  "plan validation mutates substrate state" \
  "live upgrade execution is implemented" \
  "live rollback execution is implemented" \
  "automatic rollback is implemented" \
  "substrate mutation is implemented"; do
  if grep -Fqi -- "${forbidden}" <<<"${doc_text}"; then
    echo "Forbidden Phase 58.5 upgrade rollback plan contract claim: ${forbidden}" >&2
    exit 1
  fi
done

local_path_prefix="(^|[[:space:]\`\"'(<])"
unix_home_pattern="${local_path_prefix}/(Users|home)/"
windows_home_pattern="${local_path_prefix}[A-Za-z]:\\\\Users\\\\"

if grep -Eq "${unix_home_pattern}|${windows_home_pattern}" <<<"${doc_text}"; then
  echo "Forbidden Phase 58.5 upgrade rollback plan contract claim: workstation-local path" >&2
  exit 1
fi

echo "Phase 58.5 upgrade rollback plan contract defines plan fields, failure states, and subordinate authority boundaries."
