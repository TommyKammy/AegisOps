#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
packet_path="${repo_root}/docs/deployment/operator-training-handoff-packet.md"
pilot_checklist_path="${repo_root}/docs/deployment/pilot-readiness-checklist.md"
operational_handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
record_chain_path="${repo_root}/docs/control-plane-state-model.md"
coordination_path="${repo_root}/docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md"
assistant_path="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"

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

reject_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
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

require_file "${packet_path}" "operator training and handoff packet"
require_file "${pilot_checklist_path}" "pilot readiness checklist"
require_file "${operational_handoff_path}" "operational evidence handoff pack"
require_file "${record_chain_path}" "control-plane state model"
require_file "${coordination_path}" "external ticket non-authority boundary"
require_file "${assistant_path}" "assistant advisory-only boundary"

required_headings=(
  "# Operator Training and Handoff Packet"
  "## 1. Purpose and Audience"
  "## 2. Daily Queue, Case, and Action-Review Path"
  "## 3. Reviewed Record Chain"
  "## 4. Approval, Execution, and Reconciliation Split"
  "## 5. External Ticket Non-Authority"
  "## 6. Assistant Advisory-Only Posture"
  "## 7. Evidence Handoff Walkthrough"
  "## 8. Training Checklist"
  "## 9. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${packet_path}" "${heading}" "operator training packet heading"
done

required_packet_phrases=(
  "This packet trains a single-customer pilot operator on the daily AegisOps path from queue review through case handling, action review, evidence handoff, and next-owner handoff."
  "The packet is role-readable operator guidance, not generic SOC training, a broad SIEM or SOAR course, or assistant prompt engineering training."
  "Daily work starts from the AegisOps queue, not from Wazuh, OpenSearch, Zammad, Shuffle, n8n, or assistant output."
  'The normal operator path is `queue item -> alert or case detail -> evidence review -> casework update -> action-review read -> approval decision -> execution receipt -> reconciliation outcome -> evidence handoff`.'
  "The operator may move from queue to case only through the AegisOps-owned alert, case, evidence, and reconciliation records linked to the queue item."
  "Action review is the reviewed family that keeps the action request, approval decision, execution receipt, and reconciliation outcome visible without collapsing them into one status badge."
  "The reviewed record chain is the authoritative sequence of AegisOps-owned records that explains why work entered the queue, what case owns it, what evidence supports it, what action was requested, who approved or rejected it, what execution surface reported, and how reconciliation closed or escalated the outcome."
  'Operators must follow explicit record identifiers such as `alert_id`, `case_id`, `evidence_id`, `action_request_id`, `approval_decision_id`, `action_execution_id`, and `reconciliation_id` instead of inferring linkage from names, ticket titles, dashboard order, or nearby notes.'
  'The approval role matrix in `docs/runbook.md` is the reviewed handoff reference for approver, fallback approver, platform admin, operator, and support owner responsibilities.'
  "Approval answers whether a specific AegisOps action request is allowed for the reviewed scope."
  "Execution answers what the approved execution surface actually attempted or refused and which receipt or correlation identifier came back."
  "Reconciliation answers whether authoritative AegisOps review accepted, rejected, or escalated the observed execution against the approved intent."
  "Execution success is not reconciliation success, and a ticket closure is neither execution success nor reconciliation success."
  "Denied approvals, approval timeouts, fallback approver use, and break-glass closeout must be explained from the AegisOps approval record and directly linked evidence before the operator handoff treats the path as blocked, escalated, or returned to normal."
  "External tickets are coordination references only; they may carry ticket identifiers, URLs, comments, or assignee context, but they do not own AegisOps case, approval, execution, or reconciliation truth."
  "If an external ticket disagrees with the AegisOps reviewed record chain, operators keep the AegisOps record authoritative and preserve the disagreement for review."
  "Assistant output is advisory-only and must remain grounded in reviewed AegisOps records and linked evidence."
  "The assistant must not approve, execute, reconcile, close a case, widen pilot scope, or replace missing evidence with generated text."
  "Optional evidence, downstream substrate receipts, browser state, and external tickets are subordinate context only; they may support the handoff but cannot override the reviewed AegisOps record chain."
  "A handoff starts by naming the reviewed event, operator, release or repository revision when runtime state changed, customer-scoped reference without secrets, and the directly linked AegisOps record identifiers."
  "The handoff must include the release handoff record, runtime smoke manifest when relevant, detector activation handoff when relevant, external coordination reference when present, assistant limitation statement when assistant output was used, known-limitations review, handoff owner, and next health review or queue owner."
  "For failed, rejected, forbidden, rollback, restore, or no-go paths, the handoff must preserve the refusal reason and clean-state evidence instead of overwriting the failed attempt with a later success summary."
  "- Can the operator explain the queue item, case detail, action-review detail, approval, execution, reconciliation, and handoff path without using external ticket status as authority?"
  "- Can the operator point to the exact reviewed record identifiers that make up the record chain?"
  "- Can the operator explain why approval, execution, and reconciliation are separate decisions?"
  "- Can the operator point to the runbook approval role matrix and explain denial, timeout, fallback approver, and break-glass closeout evidence without widening authority?"
  "- Can the operator state that external tickets and assistant output are non-authoritative?"
  "- Can the operator assemble the evidence handoff with repo-relative commands, placeholders, and no workstation-local absolute paths?"
  "Generic SOC curriculum, broad SIEM or SOAR administration, assistant prompt engineering, multi-customer operating model, compliance certification, and ticket-system workflow ownership are out of scope."
)

for phrase in "${required_packet_phrases[@]}"; do
  require_phrase "${packet_path}" "${phrase}" "operator training packet statement"
done

require_phrase "${packet_path}" 'Verify the packet with `scripts/verify-operator-training-handoff-packet.sh`.' "operator training packet verifier instruction"
require_phrase "${pilot_checklist_path}" 'Operator training and handoff for the pilot must use `docs/deployment/operator-training-handoff-packet.md` and verify it with `scripts/verify-operator-training-handoff-packet.sh` before treating the pilot operator handoff as ready.' "pilot readiness operator training link"
require_phrase "${operational_handoff_path}" 'Operator training and handoff for the pilot uses `docs/deployment/operator-training-handoff-packet.md` as the role-readable walkthrough for queue, case, action-review, reviewed-record, non-authority, and evidence handoff practice.' "operational handoff operator training link"
require_phrase "${record_chain_path}" "The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, Reconciliation, and Action Execution." "control-plane record-chain baseline"
require_phrase "${coordination_path}" "The selected coordination substrate is a non-authoritative coordination target." "external ticket non-authority baseline"
require_phrase "${assistant_path}" "The assistant is advisory-only." "assistant advisory-only baseline"

handoff_boundary_paths=(
  "${packet_path}"
  "${pilot_checklist_path}"
  "${operational_handoff_path}"
)

for doc_path in "${handoff_boundary_paths[@]}"; do
  for forbidden in \
    "ticket status is authoritative" \
    "ticket closure is authoritative" \
    "assistant may approve" \
    "assistant may execute" \
    "assistant may reconcile" \
    "execution success is reconciliation success" \
    "generic SOC training is required" \
    "prompt engineering training is required"; do
    reject_phrase "${doc_path}" "${forbidden}" "operator training handoff statement"
  done
done

reject_workstation_paths "operator training handoff guidance" \
  "${packet_path}" \
  "${pilot_checklist_path}" \
  "${operational_handoff_path}"

echo "Operator training packet covers queue, case, action review, reviewed record chain, authority split, non-authoritative tickets and assistant output, and evidence handoff."
