#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract"
  "## 1. Gate Names"
  "## 2. Shared Authority Boundary"
  "## 3. Evidence Families"
  "## 4. Pilot Gate"
  "## 5. Beta Gate"
  "## 6. RC Gate"
  "## 7. GA Gate"
  "## 8. Forbidden Claims"
  "## 9. Validation"
  "## 10. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-30"
  "- **Related Issues**: #1041, #1042, #1044"
  "The only approved readiness gate names for the Phase 51 replacement-readiness roadmap are:"
  "| Pilot | Single-customer or tightly controlled design-partner validation of the governed operating experience. | Pre-commercial and pre-GA. |"
  "| Beta | Multi-operator or expanded design-partner validation with repeatable evidence capture and named limitation owners. | Still pre-RC and pre-GA. |"
  "| RC | Replacement candidate readiness for the intended SMB operating scope, pending final GA evidence and launch decisions. | Phase 66 is RC. |"
  "| GA | General availability replacement readiness supported by real-user or design-partner evidence, supportability, and known limitation ownership. | Phase 67 is GA. |"
  "Phase 66 is RC. Phase 67 is GA."
  'Phase 51.7 materialization guard can use the gate names `Pilot`, `Beta`, `RC`, and `GA` from this contract when it validates later roadmap or issue materialization.'
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, and limitation truth."
  "Gate evidence must prove AegisOps records remain authoritative. Wazuh, Shuffle, AI, tickets, evidence systems, dashboards, demo data, browser state, UI cache, downstream receipts, and operator-facing summaries cannot satisfy a gate by acting as workflow truth."
  "Wazuh evidence is accepted only as subordinate detection signal evidence after explicit AegisOps admission and linkage."
  "Shuffle evidence is accepted only as subordinate delegated execution evidence after explicit AegisOps approval, action intent, execution receipt, and reconciliation linkage."
  "AI evidence is accepted only as subordinate advisory trace evidence; AI must not approve actions, execute actions, reconcile execution, close cases, activate detectors, or become source truth."
  'Gate packets must use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, `<support-bundle.md>`, `<upgrade-plan.md>`, and `<design-partner-evidence.md>`.'
  "| Install evidence | Reviewed install or upgrade entry command, selected profile, operator, revision, environment class, and retained output path. | Install success is not accepted unless the resulting AegisOps readiness and record-chain checks bind to the same gate record. |"
  "| Wazuh signal evidence | Wazuh manager, rule or decoder scope, source-family parser coverage, sample signal identifier, AegisOps alert identifier, and admission review result. | Wazuh remains the detection substrate; raw Wazuh alert state does not become AegisOps alert, case, or release truth. |"
  "| Shuffle execution evidence | Workflow identifier, delegated action request, approval record, execution receipt, reconciliation result, mismatch handling, and rollback owner. | Shuffle remains the routine automation substrate; workflow success does not become reconciliation truth without an AegisOps reconciliation record. |"
  "| AI trace evidence | Prompt or tool policy version, advisory output identifier, reviewed recommendation identifier, human decision, and refused autonomous action scope. | AI remains advisory-only and cannot approve, execute, reconcile, close, activate, or define source truth. |"
  "| Report export evidence | Export command, export artifact reference, report schema version, redaction review, and source record identifiers. | Reports are derived surfaces and must cite authoritative AegisOps records instead of becoming independent state. |"
  "| Restore dry-run evidence | Restore point, restore target, clean-state validation, reviewed record-chain replay, failed-path cleanup result, and retained manifest. | Restore acceptance comes from committed AegisOps state and clean-state evidence, not substrate-local backup names or inferred environment naming. |"
  "| Upgrade plan evidence | Version boundary, migration owner, rollback decision point, expected smoke checks, retained upgrade evidence path, and known compatibility risks. | Upgrade success is not accepted until AegisOps readiness, record-chain, and reconciliation checks pass against the target revision. |"
  "| Support bundle evidence | Support bundle command, redaction review, included record identifiers, omitted private data classes, owner, and retention expectation. | Support bundles are evidence packages only and cannot replace authoritative AegisOps gate, case, release, or limitation records. |"
  "| Limitations ownership evidence | Known limitation, affected gate, owner, acceptance or refusal reason, follow-up date, and customer or operator impact. | Limitations remain explicit AegisOps-owned records; unresolved limitations cannot be hidden in tickets, report prose, or roadmap summaries. |"
  "Pilot gate is documented with required evidence."
  "Beta gate is documented with required evidence."
  "RC gate is documented with required evidence."
  "GA gate is documented with required real-user or design-partner evidence."
  'RC replacement readiness means the intended SMB operating scope has complete gate packets for install, Wazuh signal, Shuffle execution, AI trace, report export, restore dry-run, upgrade plan, support bundle, and limitations ownership evidence; all blocking limitations have accepted owners and decision dates; and the replacement boundary from `docs/adr/0011-phase-51-1-replacement-boundary.md` is still preserved.'
  "RC is not GA. RC allows a release-candidate replacement claim only for the explicitly reviewed SMB operating scope and only while the remaining GA evidence is tracked as a named prerequisite."
  "Phase 66 is RC and must not be described as GA."
  "GA replacement readiness requires all RC evidence plus real-user or design-partner evidence that the reviewed operating experience worked across the intended launch scope, including install or upgrade, Wazuh signal admission, Shuffle delegated execution, AI advisory trace review, report export, restore dry-run, upgrade plan rehearsal, support bundle generation, and accepted limitations ownership."
  "Phase 67 is GA and must not be materialized until the GA gate evidence exists."
  "GA must reject broad GA overclaim before real-user or design-partner evidence exists."
  "The gate contract rejects broad GA overclaim before evidence exists."
  "- GA can be claimed without real-user or design-partner evidence."
  "- Wazuh, Shuffle, AI, tickets, evidence systems, dashboards, demo data, browser state, UI cache, downstream receipts, or operator-facing summaries are authoritative for gate acceptance."
  'Run `bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.'
  'Run `bash scripts/test-verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1044 --config <supervisor-config-path>`.'
)

forbidden_lines=(
  "Phase 66 is GA"
  "Phase 66 is GA."
  "RC and GA are interchangeable"
  "RC and GA are interchangeable."
  "AegisOps is already GA."
  "AegisOps is already a self-service commercial replacement."
  "AegisOps is GA because Wazuh emitted alerts."
  "AegisOps is GA because Shuffle ran workflows."
  "AegisOps is GA because AI produced recommendations."
  "AegisOps is GA because tickets were closed."
  "Wazuh is authoritative for gate acceptance."
  "Shuffle is authoritative for gate acceptance."
  "AI is authoritative for gate acceptance."
  "tickets are authoritative for gate acceptance."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 51.3 pilot beta RC GA gate contract: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 51.3 gate contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 51.3 gate contract statement: ${phrase}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index($0, claim) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

for line in "${forbidden_lines[@]}"; do
  if contains_forbidden_outside_forbidden_section "${line}"; then
    echo "Forbidden Phase 51.3 gate contract claim: ${line}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"

if grep -Eq "(${mac_user_home}[^[:space:]]*|${unix_user_home}[^[:space:]]*|${windows_user_profile_backslash}[^[:space:]]*|${windows_user_profile_slash}[^[:space:]]*)" "${doc_path}"; then
  echo "Forbidden Phase 51.3 gate contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 51.3 gate contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/phase-51-3-pilot-beta-rc-ga-gate-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 51.3 pilot beta RC GA gate contract." >&2
  exit 1
fi

echo "Phase 51.3 pilot beta RC GA gate contract is present and preserves gate evidence, RC/GA distinction, and authority boundaries."
