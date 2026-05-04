#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-57-1-rbac-role-matrix-contract.md"
matrix_path="${repo_root}/apps/operator-ui/src/auth/roleMatrix.ts"
matrix_test_path="${repo_root}/apps/operator-ui/src/auth/roleMatrix.test.ts"
session_test_path="${repo_root}/apps/operator-ui/src/auth/session.test.ts"

required_headings=(
  "# Phase 57.1 RBAC Role Matrix Contract"
  "## 1. Purpose"
  "## 2. Role Matrix"
  "## 3. Required Behavior"
  "## 4. Authority Boundary"
  "## 5. Negative Tests"
  "## 6. Scope Boundaries"
  "## 7. Verification Commands"
)

required_doc_phrases=(
  "This contract defines the minimum commercial RBAC role matrix before user, role, source, action policy, retention, audit export, and AI enablement administration expands."
  "The RBAC matrix defines access and policy posture only. It cannot rewrite historical workflow truth or make support or external users authoritative for approval, execution, reconciliation, audit, release, gate, or closeout truth."
  '| `platform_admin` | read-only | read-only | denied | denied | admin-only | denied | admin-only | denied | denied | denied |'
  '| `analyst` | allowed | allowed | allowed | denied | denied | denied | denied | denied | denied | denied |'
  '| `approver` | read-only | read-only | denied | allowed | denied | denied | denied | denied | denied | denied |'
  '| `read_only_auditor` | read-only | read-only | denied | denied | denied | denied | read-only | denied | denied | denied |'
  '| `support_operator` | read-only | read-only | denied | denied | denied | support-only | denied | denied | denied | denied |'
  '| `external_collaborator` | read-only | read-only | denied | denied | denied | denied | denied | no-authority | denied | denied |'
  "The matrix covers allowed, denied, read-only, admin-only, support-only, and no-authority behavior."
  "Support operator access is support-only for customer-safe diagnostics and cannot receive workflow authority for approval, execution, reconciliation, audit, release, gate, or closeout truth."
  "External collaborator access is no-authority collaboration context and cannot receive workflow authority for approval, execution, reconciliation, audit, release, gate, or closeout truth."
  "Backend authorization remains the enforcement boundary for protected reads, write-capable operator actions, approval decisions, action execution delegation, reconciliation closeout, audit export, support diagnostics, and administration."
  "If browser role cache and backend authorization disagree, the backend denial wins and the browser must preserve the denial explicitly instead of rendering guessed or cached protected content."
  "Admin configuration cannot rewrite historical workflow truth, lifecycle state, approval state, action execution state, reconciliation state, audit-export truth, release truth, gate truth, or closeout truth."
  "Negative tests must reject support operator workflow authority, external collaborator workflow authority, UI role cache as authority, self-approval through role confusion, and admin configuration rewriting historical truth."
  "Existing backend authority and reread-after-write posture remain unchanged."
  'Run `npm test --workspace apps/operator-ui -- --run src/auth/roleMatrix.test.ts src/auth/session.test.ts`.'
  'Run `bash scripts/verify-phase-57-1-rbac-role-matrix-contract.sh`.'
  'Run `bash scripts/test-verify-phase-57-1-rbac-role-matrix-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1207 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1208 --config <supervisor-config-path>`.'
)

required_roles=(
  "platform_admin"
  "analyst"
  "approver"
  "read_only_auditor"
  "support_operator"
  "external_collaborator"
)

required_access_values=(
  "allowed"
  "denied"
  "read_only"
  "admin_only"
  "support_only"
  "no_authority"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 57.1 RBAC role matrix contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${matrix_path}" ]]; then
  echo "Missing Phase 57.1 executable role matrix: ${matrix_path}" >&2
  exit 1
fi

if [[ ! -f "${matrix_test_path}" ]]; then
  echo "Missing Phase 57.1 role matrix tests: ${matrix_test_path}" >&2
  exit 1
fi

if [[ ! -f "${session_test_path}" ]]; then
  echo "Missing reviewed session role coverage tests: ${session_test_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 57.1 RBAC role matrix contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 57.1 RBAC role matrix contract statement: ${phrase}" >&2
    exit 1
  fi
done

for role in "${required_roles[@]}"; do
  if ! grep -Fq -- "\"${role}\"" "${matrix_path}"; then
    echo "Missing Phase 57.1 RBAC role in executable matrix: ${role}" >&2
    exit 1
  fi
  if ! grep -Fq -- "\`${role}\`" "${doc_path}"; then
    echo "Missing Phase 57.1 RBAC role in contract table: ${role}" >&2
    exit 1
  fi
  if ! grep -Fq -- "\"${role}\"" "${matrix_test_path}" "${session_test_path}"; then
    echo "Missing Phase 57.1 RBAC role in focused tests: ${role}" >&2
    exit 1
  fi
done

for access in "${required_access_values[@]}"; do
  if ! grep -Fq -- "\"${access}\"" "${matrix_path}" "${matrix_test_path}"; then
    echo "Missing Phase 57.1 RBAC access behavior in executable matrix/tests: ${access}" >&2
    exit 1
  fi
done

if ! grep -Fq -- "workflowAuthority: false" "${matrix_path}"; then
  echo "Missing fail-closed workflowAuthority=false posture in executable role matrix" >&2
  exit 1
fi

if grep -R -nE '/Users/[^[:space:]]+|/home/[^[:space:]]+|C:\\\\Users\\\\' \
  "${doc_path}" "${matrix_path}" "${matrix_test_path}" "${session_test_path}" >&2; then
  echo "Phase 57.1 RBAC artifacts contain workstation-local absolute paths" >&2
  exit 1
fi

echo "Phase 57.1 RBAC role matrix contract is present with executable role coverage and authority-boundary negative posture."
