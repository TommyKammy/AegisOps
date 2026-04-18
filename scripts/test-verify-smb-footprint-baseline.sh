#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-smb-footprint-baseline.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/README.md"
# AegisOps

See `docs/smb-footprint-and-deployment-profile-baseline.md` for the reviewed SMB footprint baseline that anchors roadmap and runbook decisions.
EOF

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook Skeleton

Startup, restore, and operator burden assumptions must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.
EOF

  cat <<'EOF' > "${target}/docs/Revised Phase23-20 Epic Roadmap.md"
# Revised Phase 23-20 Epic Roadmap

Phase 23 planning remains anchored to `docs/smb-footprint-and-deployment-profile-baseline.md`.
EOF
}

write_valid_baseline_doc() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/smb-footprint-and-deployment-profile-baseline.md"
# SMB Footprint and Deployment-Profile Baseline

## 1. Purpose

This baseline publishes the reviewed SMB deployment profiles that future footprint, reliability, and operator-experience work must target.

Use this baseline to replace intuition-only sizing discussions with a concrete, reviewable deployment floor and ceiling for the approved Phase 27 operating model.

## 2. Scope and Decision Rule

Use this baseline to judge whether AegisOps remains operable for the approved small-team deployment target before later work adds substrate, reliability, or ergonomics scope.

A profile is acceptable only if it preserves the positive SMB value proposition and remains realistic for a small business-hours SecOps team to operate.

## 3. Reviewed Deployment Profiles

### 3.1 Lab Profile

The lab profile is the minimum reviewable footprint for first-boot exercises, restore rehearsal, and operator training.

### 3.2 Single-Customer Profile

The single-customer profile is the default reviewed deployment shape for one customer environment with explicit operator ownership and no implied multi-tenant fleet posture.

### 3.3 Small-Production SMB Operation Profile

The small-production SMB operation profile is the maximum reviewed baseline for Phase 27 roadmap decisions.

## 4. Baseline Expectations by Profile

| Profile | Managed endpoints | vCPU | Memory | Primary storage | Backup expectation | Restore expectation | Upgrade and rollback expectation | Health and operator cadence | Identity and secret-management expectation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lab | 250 to 500 | 8 to 10 | 24 to 32 GB | 400 to 600 GB usable persistent storage | Daily PostgreSQL-aware backup, configuration backup after reviewed changes, and a named operator responsible for verifying the backup job outcome | At least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery | Reviewed upgrades fit one business-hours maintenance window and rollback returns to the prior known-good backup without extra platform staff or high-availability failover machinery | Startup, queue, backup, and reverse-proxy health reviewed at least three times per week during business hours, with one operator capturing the readiness result | One named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list are sufficient for the lab path |
| Single-customer | 500 to 1,000 | 12 to 16 | 40 to 56 GB | 0.8 to 1.5 TB usable persistent storage | Daily PostgreSQL-aware backup, weekly backup review, and reviewed configuration backup before platform changes that affect customer operations | Monthly restore rehearsal against a reviewed single-customer recovery target, including validation that customer-scoped workflow truth and linked evidence return cleanly | Reviewed upgrades fit one planned maintenance window per month and rollback remains operator-led without cluster failover tooling or multi-customer coordination assumptions | Daily queue and health review on business days plus weekly platform hygiene review for certificates, storage growth, and backup drift | Named customer-scoped approver ownership, a reviewed secret rotation checklist, and explicit break-glass custody for customer credentials are required |
| Small-production SMB operation | 1,000 to 1,500 | 16 to 24 | 56 to 96 GB | 1.5 to 3 TB usable persistent storage | Daily PostgreSQL-aware backup, weekly backup review, and pre-change configuration backup with documented custody | Monthly restore rehearsal with documented recovery timing, clean-state validation, and reconciliation checks before normal operations resume | Reviewed upgrades require a documented change plan, same-day rollback readiness, and no dependence on enterprise-only deployment tooling, dedicated database teams, or multi-region failover | Daily queue and platform health review on business days plus weekly drift, storage-growth, and capacity review by the named operator team | Two-person ownership coverage for approver and secret custody, scheduled rotation checkpoints, and documented break-glass audit follow-up are required |

CPU and memory expectations must be read as whole-environment planning guidance for the approved control-plane footprint, not as per-container reservations.

Backup expectations must include PostgreSQL-aware backups, configuration backup, and a restore rehearsal expectation rather than relying on hypervisor snapshots alone.

## 5. Capacity Budget Guardrails

Each reviewed profile must publish explicit budget assumptions for backup, restore, upgrade, rollback, health review, identity administration, and secret management rather than leaving Phase 27 day-2 hardening work to infer them later.

Upgrade and rollback expectations must stay narrow enough that one small business-hours operator team can complete a reviewed platform change and, if needed, return to the prior known-good state without enterprise-only tooling.

Health expectations must state the minimum operator review cadence that later readiness, drift, and alert-handling work can assume.

Identity and secret-management expectations must keep named approver ownership, secret rotation touch points, and break-glass handling inside the reviewed SMB operating posture.

## 6. Operational Burden Baseline

Operator-overhead expectations are part of the footprint baseline because a deployment that fits on paper but requires enterprise-style staffing is out of scope.

The approved small-team operating assumption remains 2 to 6 business-hours SecOps operators with 1 to 3 designated approvers or escalation owners.

## 7. Alignment to Phase 27 Day-2 Hardening

Phase 27 day-2 hardening work must stay inside these reviewed profiles unless a later ADR approves a new target footprint.

Later upgrade, rollback, health, identity, and secret-management work must target one of these reviewed profiles rather than inventing a broader operating posture by implication.

This baseline supports the product thesis that AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

## 8. Explicitly Out of Scope

High-availability overbuild, large-cluster sizing, and generic enterprise capacity planning are explicitly out of scope for this baseline.
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
write_valid_baseline_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
write_shared_docs "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing SMB footprint baseline document:"

missing_heading_repo="${workdir}/missing-heading"
create_repo "${missing_heading_repo}"
write_shared_docs "${missing_heading_repo}"
write_valid_baseline_doc "${missing_heading_repo}"
python3 - <<'PY' "${missing_heading_repo}/docs/smb-footprint-and-deployment-profile-baseline.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace("## 5. Capacity Budget Guardrails\n", "", 1)
path.write_text(text)
PY
commit_fixture "${missing_heading_repo}"
assert_fails_with "${missing_heading_repo}" "Missing SMB footprint baseline heading: ## 5. Capacity Budget Guardrails"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_repo "${missing_readme_link_repo}"
write_shared_docs "${missing_readme_link_repo}"
write_valid_baseline_doc "${missing_readme_link_repo}"
python3 - <<'PY' "${missing_readme_link_repo}/README.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace("docs/smb-footprint-and-deployment-profile-baseline.md", "docs/other-doc.md", 1)
path.write_text(text)
PY
commit_fixture "${missing_readme_link_repo}"
assert_fails_with "${missing_readme_link_repo}" "Missing README SMB footprint baseline reference: docs/smb-footprint-and-deployment-profile-baseline.md"

missing_scope_repo="${workdir}/missing-scope"
create_repo "${missing_scope_repo}"
write_shared_docs "${missing_scope_repo}"
write_valid_baseline_doc "${missing_scope_repo}"
python3 - <<'PY' "${missing_scope_repo}/docs/smb-footprint-and-deployment-profile-baseline.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "High-availability overbuild, large-cluster sizing, and generic enterprise capacity planning are explicitly out of scope for this baseline.\n",
    "",
    1,
)
path.write_text(text)
PY
commit_fixture "${missing_scope_repo}"
assert_fails_with "${missing_scope_repo}" "Missing SMB footprint baseline statement: High-availability overbuild, large-cluster sizing, and generic enterprise capacity planning are explicitly out of scope for this baseline."

old_profile_name_repo="${workdir}/old-profile-name"
create_repo "${old_profile_name_repo}"
write_shared_docs "${old_profile_name_repo}"
write_valid_baseline_doc "${old_profile_name_repo}"
python3 - <<'PY' "${old_profile_name_repo}/docs/smb-footprint-and-deployment-profile-baseline.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace("### 3.2 Single-Customer Profile", "### 3.2 Consultant-Managed Single-Customer Profile", 1)
text = text.replace(
    "The single-customer profile is the default reviewed deployment shape for one customer environment with explicit operator ownership and no implied multi-tenant fleet posture.",
    "The consultant-managed single-customer profile is the default reviewed deployment shape for a small external operator team managing one customer environment.",
    1,
)
text = text.replace("| Single-customer |", "| Consultant-managed single-customer |", 1)
path.write_text(text)
PY
commit_fixture "${old_profile_name_repo}"
assert_fails_with "${old_profile_name_repo}" "Missing SMB footprint baseline heading: ### 3.2 Single-Customer Profile"

weak_profile_budget_repo="${workdir}/weak-profile-budget"
create_repo "${weak_profile_budget_repo}"
write_shared_docs "${weak_profile_budget_repo}"
write_valid_baseline_doc "${weak_profile_budget_repo}"
python3 - <<'PY' "${weak_profile_budget_repo}/docs/smb-footprint-and-deployment-profile-baseline.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "| Lab | 250 to 500 | 8 to 10 | 24 to 32 GB | 400 to 600 GB usable persistent storage | Daily PostgreSQL-aware backup, configuration backup after reviewed changes, and a named operator responsible for verifying the backup job outcome | At least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery | Reviewed upgrades fit one business-hours maintenance window and rollback returns to the prior known-good backup without extra platform staff or high-availability failover machinery | Startup, queue, backup, and reverse-proxy health reviewed at least three times per week during business hours, with one operator capturing the readiness result | One named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list are sufficient for the lab path |",
    "| Lab | 250 to 500 | 8 to 10 | 24 to 32 GB | 400 to 600 GB usable persistent storage | | | | | |",
    1,
)
path.write_text(text)
PY
commit_fixture "${weak_profile_budget_repo}"
assert_fails_with "${weak_profile_budget_repo}" "Missing SMB footprint baseline statement: | Lab | 250 to 500 | 8 to 10 | 24 to 32 GB | 400 to 600 GB usable persistent storage | Daily PostgreSQL-aware backup, configuration backup after reviewed changes, and a named operator responsible for verifying the backup job outcome | At least one restore rehearsal per quarter against the reviewed lab path, including confirmation that approval, evidence, action-execution, and reconciliation records remain intact after recovery | Reviewed upgrades fit one business-hours maintenance window and rollback returns to the prior known-good backup without extra platform staff or high-availability failover machinery | Startup, queue, backup, and reverse-proxy health reviewed at least three times per week during business hours, with one operator capturing the readiness result | One named approver owner, one reviewed secret rotation touch point, and a documented break-glass contact list are sufficient for the lab path |"

missing_budget_guardrail_repo="${workdir}/missing-budget-guardrail"
create_repo "${missing_budget_guardrail_repo}"
write_shared_docs "${missing_budget_guardrail_repo}"
write_valid_baseline_doc "${missing_budget_guardrail_repo}"
python3 - <<'PY' "${missing_budget_guardrail_repo}/docs/smb-footprint-and-deployment-profile-baseline.md"
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "Each reviewed profile must publish explicit budget assumptions for backup, restore, upgrade, rollback, health review, identity administration, and secret management rather than leaving Phase 27 day-2 hardening work to infer them later.\n\n",
    "",
    1,
)
path.write_text(text)
PY
commit_fixture "${missing_budget_guardrail_repo}"
assert_fails_with "${missing_budget_guardrail_repo}" "Missing SMB footprint baseline statement: Each reviewed profile must publish explicit budget assumptions for backup, restore, upgrade, rollback, health review, identity administration, and secret management rather than leaving Phase 27 day-2 hardening work to infer them later."

echo "SMB footprint baseline verifier tests passed."
