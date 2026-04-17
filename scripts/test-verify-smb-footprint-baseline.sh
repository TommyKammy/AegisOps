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

## 2. Scope and Decision Rule

Use this baseline to judge whether AegisOps remains operable for the approved small-team deployment target before later work adds substrate, reliability, or ergonomics scope.

A profile is acceptable only if it preserves the positive SMB value proposition and remains realistic for a small business-hours SecOps team to operate.

## 3. Reviewed Deployment Profiles

### 3.1 Lab Profile

The lab profile is the minimum reviewable footprint for first-boot exercises, restore rehearsal, and operator training.

### 3.2 Consultant-Managed Single-Customer Profile

The consultant-managed single-customer profile is the default reviewed deployment shape for a small external operator team managing one customer environment.

### 3.3 Small-Production SMB Operation Profile

The small-production SMB operation profile is the maximum reviewed baseline for Phase 23 roadmap decisions.

## 4. Baseline Expectations by Profile

| Profile | Managed endpoints | vCPU | Memory | Primary storage | Backup and restore expectation | Operator overhead expectation |
| --- | --- | --- | --- | --- | --- | --- |
| Lab | 250 | 8 | 24 GB | 400 GB | PostgreSQL-aware backup plus restore rehearsal | 2 to 4 operator-hours per week |
| Consultant-managed single-customer | 750 | 14 | 48 GB | 1 TB | PostgreSQL-aware backup plus monthly restore rehearsal | 4 to 6 operator-hours per week |
| Small-production SMB operation | 1500 | 20 | 64 GB | 2 TB | PostgreSQL-aware backup plus quarterly restore rehearsal | 6 to 8 operator-hours per week |

CPU and memory expectations must be read as whole-environment planning guidance for the approved control-plane footprint, not as per-container reservations.

Backup expectations must include PostgreSQL-aware backups, configuration backup, and a restore rehearsal expectation rather than relying on hypervisor snapshots alone.

## 5. Operational Burden Baseline

Operator-overhead expectations are part of the footprint baseline because a deployment that fits on paper but requires enterprise-style staffing is out of scope.

The approved small-team operating assumption remains 2 to 6 business-hours SecOps operators with 1 to 3 designated approvers or escalation owners.

## 6. Alignment to Phase 23 Product Thesis

Phase 23 hardening and ergonomics work must stay inside these reviewed profiles unless a later ADR approves a new target footprint.

This baseline supports the product thesis that AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

## 7. Explicitly Out of Scope

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
text = text.replace("## 5. Operational Burden Baseline\n", "", 1)
path.write_text(text)
PY
commit_fixture "${missing_heading_repo}"
assert_fails_with "${missing_heading_repo}" "Missing SMB footprint baseline heading: ## 5. Operational Burden Baseline"

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

echo "SMB footprint baseline verifier tests passed."
