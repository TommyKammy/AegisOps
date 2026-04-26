#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-operator-training-handoff-packet.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment" "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/pilot-readiness-checklist.md"
# Single-Customer Pilot Readiness Checklist and Entry Criteria

Operator training and handoff for the pilot must use `docs/deployment/operator-training-handoff-packet.md` and verify it with `scripts/verify-operator-training-handoff-packet.sh` before treating the pilot operator handoff as ready.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

Operator training and handoff for the pilot uses `docs/deployment/operator-training-handoff-packet.md` as the role-readable walkthrough for queue, case, action-review, reviewed-record, non-authority, and evidence handoff practice.
EOF

  cat <<'EOF' > "${target}/docs/control-plane-state-model.md"
# AegisOps Control-Plane State and Reconciliation Model

The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, Reconciliation, and Action Execution.
EOF

  cat <<'EOF' > "${target}/docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md"
# AegisOps Phase 26 First Coordination Substrate and Non-Authoritative Ticket Boundary

The selected coordination substrate is a non-authoritative coordination target.
EOF

  cat <<'EOF' > "${target}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
# AegisOps Phase 15 Identity-Grounded Analyst-Assistant Boundary

The assistant is advisory-only.
EOF
}

write_valid_packet() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/operator-training-handoff-packet.md"
# Operator Training and Handoff Packet

## 1. Purpose and Audience

This packet trains a single-customer pilot operator on the daily AegisOps path from queue review through case handling, action review, evidence handoff, and next-owner handoff.

The packet is role-readable operator guidance, not generic SOC training, a broad SIEM or SOAR course, or assistant prompt engineering training.

Verify the packet with `scripts/verify-operator-training-handoff-packet.sh`.

## 2. Daily Queue, Case, and Action-Review Path

Daily work starts from the AegisOps queue, not from Wazuh, OpenSearch, Zammad, Shuffle, n8n, or assistant output.

The normal operator path is `queue item -> alert or case detail -> evidence review -> casework update -> action-review read -> approval decision -> execution receipt -> reconciliation outcome -> evidence handoff`.

The operator may move from queue to case only through the AegisOps-owned alert, case, evidence, and reconciliation records linked to the queue item.

Action review is the reviewed family that keeps the action request, approval decision, execution receipt, and reconciliation outcome visible without collapsing them into one status badge.

## 3. Reviewed Record Chain

The reviewed record chain is the authoritative sequence of AegisOps-owned records that explains why work entered the queue, what case owns it, what evidence supports it, what action was requested, who approved or rejected it, what execution surface reported, and how reconciliation closed or escalated the outcome.

Operators must follow explicit record identifiers such as `alert_id`, `case_id`, `evidence_id`, `action_request_id`, `approval_decision_id`, `action_execution_id`, and `reconciliation_id` instead of inferring linkage from names, ticket titles, dashboard order, or nearby notes.

## 4. Approval, Execution, and Reconciliation Split

Approval answers whether a specific AegisOps action request is allowed for the reviewed scope.

Execution answers what the approved execution surface actually attempted or refused and which receipt or correlation identifier came back.

Reconciliation answers whether authoritative AegisOps review accepted, rejected, or escalated the observed execution against the approved intent.

Execution success is not reconciliation success, and a ticket closure is neither execution success nor reconciliation success.

## 5. External Ticket Non-Authority

External tickets are coordination references only; they may carry ticket identifiers, URLs, comments, or assignee context, but they do not own AegisOps case, approval, execution, or reconciliation truth.

If an external ticket disagrees with the AegisOps reviewed record chain, operators keep the AegisOps record authoritative and preserve the disagreement for review.

## 6. Assistant Advisory-Only Posture

Assistant output is advisory-only and must remain grounded in reviewed AegisOps records and linked evidence.

The assistant must not approve, execute, reconcile, close a case, widen pilot scope, or replace missing evidence with generated text.

## 7. Evidence Handoff Walkthrough

A handoff starts by naming the reviewed event, operator, release or repository revision when runtime state changed, customer-scoped reference without secrets, and the directly linked AegisOps record identifiers.

The handoff must include the release handoff record, runtime smoke manifest when relevant, detector activation handoff when relevant, external coordination reference when present, assistant limitation statement when assistant output was used, known-limitations review, handoff owner, and next health review or queue owner.

For failed, rejected, forbidden, rollback, restore, or no-go paths, the handoff must preserve the refusal reason and clean-state evidence instead of overwriting the failed attempt with a later success summary.

## 8. Training Checklist

- Can the operator explain the queue item, case detail, action-review detail, approval, execution, reconciliation, and handoff path without using external ticket status as authority?
- Can the operator point to the exact reviewed record identifiers that make up the record chain?
- Can the operator explain why approval, execution, and reconciliation are separate decisions?
- Can the operator state that external tickets and assistant output are non-authoritative?
- Can the operator assemble the evidence handoff with repo-relative commands, placeholders, and no workstation-local absolute paths?

## 9. Out of Scope

Generic SOC curriculum, broad SIEM or SOAR administration, assistant prompt engineering, multi-customer operating model, compliance certification, and ticket-system workflow ownership are out of scope.
EOF
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_shared_docs "${valid_repo}"
write_valid_packet "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_packet_repo="${workdir}/missing-packet"
create_repo "${missing_packet_repo}"
write_shared_docs "${missing_packet_repo}"
commit_fixture "${missing_packet_repo}"
assert_fails_with "${missing_packet_repo}" "Missing operator training and handoff packet:"

missing_record_chain_repo="${workdir}/missing-record-chain"
create_repo "${missing_record_chain_repo}"
write_shared_docs "${missing_record_chain_repo}"
write_valid_packet "${missing_record_chain_repo}"
perl -0pi -e 's/Operators must follow explicit record identifiers such as `alert_id`, `case_id`, `evidence_id`, `action_request_id`, `approval_decision_id`, `action_execution_id`, and `reconciliation_id` instead of inferring linkage from names, ticket titles, dashboard order, or nearby notes\.\n//' "${missing_record_chain_repo}/docs/deployment/operator-training-handoff-packet.md"
commit_fixture "${missing_record_chain_repo}"
assert_fails_with "${missing_record_chain_repo}" "Missing operator training packet statement: Operators must follow explicit record identifiers"

missing_non_authority_repo="${workdir}/missing-non-authority"
create_repo "${missing_non_authority_repo}"
write_shared_docs "${missing_non_authority_repo}"
write_valid_packet "${missing_non_authority_repo}"
perl -0pi -e 's/External tickets are coordination references only; they may carry ticket identifiers, URLs, comments, or assignee context, but they do not own AegisOps case, approval, execution, or reconciliation truth\.\n//' "${missing_non_authority_repo}/docs/deployment/operator-training-handoff-packet.md"
commit_fixture "${missing_non_authority_repo}"
assert_fails_with "${missing_non_authority_repo}" "Missing operator training packet statement: External tickets are coordination references only"

forbidden_authority_repo="${workdir}/forbidden-authority"
create_repo "${forbidden_authority_repo}"
write_shared_docs "${forbidden_authority_repo}"
write_valid_packet "${forbidden_authority_repo}"
printf '\nTicket status is authoritative during handoff.\n' >> "${forbidden_authority_repo}/docs/deployment/operator-training-handoff-packet.md"
commit_fixture "${forbidden_authority_repo}"
assert_fails_with "${forbidden_authority_repo}" "Forbidden operator training handoff statement: ticket status is authoritative"

forbidden_pilot_checklist_repo="${workdir}/forbidden-pilot-checklist"
create_repo "${forbidden_pilot_checklist_repo}"
write_shared_docs "${forbidden_pilot_checklist_repo}"
write_valid_packet "${forbidden_pilot_checklist_repo}"
printf '\nAssistant may approve pilot handoff exceptions.\n' >> "${forbidden_pilot_checklist_repo}/docs/deployment/pilot-readiness-checklist.md"
commit_fixture "${forbidden_pilot_checklist_repo}"
assert_fails_with "${forbidden_pilot_checklist_repo}" "Forbidden operator training handoff statement: assistant may approve"

forbidden_operational_handoff_repo="${workdir}/forbidden-operational-handoff"
create_repo "${forbidden_operational_handoff_repo}"
write_shared_docs "${forbidden_operational_handoff_repo}"
write_valid_packet "${forbidden_operational_handoff_repo}"
printf '\nPrompt engineering training is required before evidence handoff.\n' >> "${forbidden_operational_handoff_repo}/docs/deployment/operational-evidence-handoff-pack.md"
commit_fixture "${forbidden_operational_handoff_repo}"
assert_fails_with "${forbidden_operational_handoff_repo}" "Forbidden operator training handoff statement: prompt engineering training is required"

echo "verify-operator-training-handoff-packet tests passed"
