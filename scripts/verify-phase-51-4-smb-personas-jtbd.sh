#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 51.4 SMB Personas and Jobs-to-Be-Done Matrix"
  "## 1. Purpose"
  "## 2. Shared Operating Assumptions"
  "## 3. Personas and Jobs-to-Be-Done Matrix"
  "### 3.1 Internal IT Manager"
  "### 3.2 Part-Time Security Operator"
  "### 3.3 Approver / Escalation Owner"
  "### 3.4 Platform Admin"
  "### 3.5 Bounded External Support Collaborator"
  "## 4. Later Roadmap Usage"
  "## 5. Authority Boundary"
  "## 6. Validation"
  "## 7. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Related Issues**: #1041, #1042, #1045"
  "This document defines product-planning personas and jobs-to-be-done for the post-Phase50 SMB replacement roadmap."
  "This document changes documentation and verification only. It does not implement RBAC, UI, support, AI, admin, Wazuh, Shuffle, ticketing, or evidence-system behavior."
  "The default staffing model is business-hours security work with explicit after-hours escalation, not a 24x7 staffed SOC."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, and limitation truth."
  "External support collaborators, AI, Wazuh, Shuffle, tickets, evidence systems, dashboards, report exports, and operator-facing summaries remain subordinate context."
  "| Internal IT Manager | Keep daily security work understandable while also owning normal IT operations. | Review prioritized alerts, confirm business impact, decide which issues need operator follow-up, coordinate with approvers, and keep leadership aware of limitations. | Fear that AegisOps becomes another broad SIEM/SOAR program, requires 24x7 staffing, hides risky automation behind AI, or leaves unclear ownership after a failed action. | Needs concise business-hours queue summaries, clear evidence links, explicit escalation owner handoff, and release-gate or limitation summaries that can be shared internally. | May request investigation, update non-approval case context, and coordinate follow-up within assigned scope. Must not approve their own approval-sensitive requests, use IT ownership as platform-admin authority, or treat Wazuh, Shuffle, AI, tickets, or support advice as authoritative AegisOps truth. | Phase 52 setup and guided onboarding, Phase 55 daily operator queue, Phase 62 report export, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |"
  "| Part-Time Security Operator | Triage real signals efficiently without becoming a full-time SOC analyst. | Review admitted Wazuh signals, group related evidence, create or update AegisOps cases, draft action requests, check delegated Shuffle receipts, and prepare handoff notes before returning to other work. | Fear missing critical context, being blamed for automation they did not approve, losing the thread across shifts, or having AI produce confident but unaudited guidance. | Needs saved investigation state, next-step prompts, evidence anchors, explicit approval status, failed-delegation cleanup notes, and handoff text that a later operator can resume. | May investigate, annotate, and request approval-bound actions within assigned scope. Must not self-approve sensitive actions, execute destructive actions outside reviewed delegation, close cases from AI advice alone, or promote raw Wazuh or Shuffle state into AegisOps reconciliation truth. | Phase 54 Wazuh signal intake, Phase 55 daily queue, Phase 57 AI advisory trace, Phase 59 Shuffle delegated execution, Phase 61 restore dry-run evidence. |"
  "| Approver / Escalation Owner | Make accountable decisions on actions that need human authority or after-hours escalation. | Review requester identity, evidence, risk, blast radius, proposed action, rollback owner, and timing; approve or reject within delegated authority; decide when after-hours escalation is justified. | Fear rubber-stamp approvals, unclear separation from the requester, missing rollback context, or hidden support or AI pressure to approve an unsafe action. | Needs immutable approval context, requester separation, explicit action intent, rollback and mismatch handling notes, and after-hours escalation reason captured in the AegisOps record. | May approve or reject approval-bound requests within delegated scope and own escalation decisions. Must remain distinct from the requester where required, must not rely on side-channel approvals alone, and must not let support, AI, tickets, Wazuh, or Shuffle approve actions by proxy. | Phase 56 approval ergonomics, Phase 59 delegated execution, Phase 60 reconciliation, Phase 64 limitation ownership, Phase 66 RC evidence packet. |"
  "| Platform Admin | Keep AegisOps deployable, recoverable, connected, and auditable for the SMB footprint. | Configure reviewed runtime settings, maintain identity and secret boundaries, run install or upgrade preflights, collect support bundles, rehearse restore and rollback, and repair platform connectivity without changing case truth. | Fear brittle installs, hidden credential drift, backup or restore gaps, unclear ownership of service accounts, or being asked to bypass approvals during an incident. | Needs deterministic preflight output, repo-relative runbooks, secret-custody checks, backup and restore manifests, support-bundle redaction guidance, and clear separation from approver authority. | May administer platform components, service-account plumbing, recovery procedures, and approved configuration paths. Must not use platform-admin access as a substitute approval path, mutate authoritative case or reconciliation outcomes outside reviewed controls, or grant external support direct backend or substrate authority. | Phase 52 setup, Phase 53 install profile, Phase 58 admin and secret custody, Phase 61 restore dry-run, Phase 63 support bundle, Phase 65 upgrade plan. |"
  "| Bounded External Support Collaborator | Help diagnose platform or product issues without becoming an operator, approver, administrator, or source of truth. | Review redacted support bundles, ask clarifying questions, suggest documented remediation steps, and identify product defects or known limitations for the customer-owned team to accept or reject. | Fear receiving private production data, being expected to provide 24x7 coverage, being blamed for customer decisions, or accidentally becoming an authority path through informal advice. | Needs redacted bundles, explicit customer owner, limitation owner, reproduction steps, environment class, retained evidence references, and a written boundary for what support may not do. | May provide advisory diagnosis from redacted evidence and documented product knowledge only. Must not access customer-private production systems directly, approve actions, execute actions, mutate AegisOps records, operate Wazuh or Shuffle, close cases, or make AI, tickets, or support notes authoritative. | Phase 63 support bundle, Phase 64 known limitations ownership, Phase 66 RC supportability evidence, Phase 67 GA support-readiness evidence. |"
  "| Persona | Primary later phases | Usage |"
  "| Internal IT Manager | Phase 52, Phase 55, Phase 62, Phase 66, Phase 67 | Shapes setup language, daily summaries, leadership-ready reports, RC evidence, and GA launch evidence around narrow SMB ownership. |"
  "| Part-Time Security Operator | Phase 54, Phase 55, Phase 57, Phase 59, Phase 61 | Shapes signal triage, queue ergonomics, advisory AI traces, delegated execution review, and restore-readiness handoffs. |"
  "| Approver / Escalation Owner | Phase 56, Phase 59, Phase 60, Phase 64, Phase 66 | Shapes approval context, separation-of-duties proof, reconciliation ownership, limitations decisions, and RC gate packets. |"
  "| Platform Admin | Phase 52, Phase 53, Phase 58, Phase 61, Phase 63, Phase 65 | Shapes install, configuration, secret custody, restore rehearsal, support-bundle, and upgrade-plan requirements. |"
  "| Bounded External Support Collaborator | Phase 63, Phase 64, Phase 66, Phase 67 | Shapes redacted support-bundle evidence, limitation ownership, supportability proof, and GA support-readiness boundaries. |"
  "These personas do not grant external support, AI, Wazuh, Shuffle, tickets, evidence systems, dashboards, reports, or operator-facing summaries authority over AegisOps records."
  'Run `bash scripts/verify-phase-51-4-smb-personas-jtbd.sh`.'
  'Run `bash scripts/test-verify-phase-51-4-smb-personas-jtbd.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1045 --config <supervisor-config-path>`.'
)

forbidden_lines=(
  "AegisOps assumes a 24x7 staffed SOC by default."
  "24x7 staffed SOC is the default operating model."
  "External support may approve AegisOps actions."
  "External support may execute AegisOps actions."
  "External support may mutate AegisOps records."
  "External support is authoritative for AegisOps records."
  "AI may approve AegisOps actions."
  "AI may execute AegisOps actions."
  "AI is authoritative for AegisOps records."
  "Wazuh is authoritative for AegisOps records."
  "Shuffle is authoritative for AegisOps records."
  "tickets are authoritative for AegisOps records."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 51.4 SMB personas and jobs-to-be-done document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 51.4 personas heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 51.4 personas statement: ${phrase}" >&2
    exit 1
  fi
done

if ! grep -Eq '^- \*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "${doc_path}"; then
  echo "Missing or invalid Phase 51.4 personas date line (- **Date**: YYYY-MM-DD)." >&2
  exit 1
fi

for line in "${forbidden_lines[@]}"; do
  if grep -Fq -- "${line}" "${doc_path}"; then
    echo "Forbidden Phase 51.4 personas authority or staffing claim: ${line}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"

if grep -Eq "(${mac_user_home}[^[:space:]]*|${unix_user_home}[^[:space:]]*|${windows_user_profile_backslash}[^[:space:]]*|${windows_user_profile_slash}[^[:space:]]*)" "${doc_path}"; then
  echo "Forbidden Phase 51.4 personas document: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 51.4 personas link check: ${readme_path}" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/phase-51-4-smb-personas-jobs-to-be-done\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 51.4 SMB personas and jobs-to-be-done document." >&2
  exit 1
fi

echo "Phase 51.4 SMB personas and jobs-to-be-done matrix is present and preserves SMB staffing and authority boundaries."
