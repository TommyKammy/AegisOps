#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-auth-baseline-doc.sh"

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

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/auth-baseline.md"
  git -C "${target}" add docs/auth-baseline.md
}

commit_fixture() {
  local target="$1"

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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# AegisOps Authentication, Authorization, and Service Account Ownership Baseline

## 1. Purpose

This document defines the baseline authentication, authorization, and service account ownership expectations for future AegisOps implementation work.

This document defines policy and ownership expectations only. It does not create live identities, integrate an IdP, mint credentials, or store secret material.

## 2. Human Identity Baseline

| Persona | Primary responsibility | Minimum allowed authority | Prohibited baseline shortcut |
| ---- | ---- | ---- | ---- |
| `Analyst` | Investigates alerts, findings, and cases; prepares recommendations and action requests. | Read-oriented investigation access, case updates, and ability to submit approval-bound requests within assigned scope. | Must not approve their own approval-sensitive actions or administer shared platform identity controls. |
| `Approver` | Reviews approval-bound requests and accepts or rejects execution within delegated authority. | Access to approval context, target evidence, and approval decision recording for authorized action classes. | Must remain distinct from the original requester for approval-sensitive actions and must not rely on informal side-channel approval alone. |
| `Platform Administrator` | Operates AegisOps infrastructure, platform configuration, connectivity, and credential plumbing. | Administrative access to platform components, secret delivery paths, service-account provisioning workflows, and recovery procedures. | Must not use `platform_admin` access as a substitute approval path for response actions and must avoid routine use of shared human credentials. |

## 3. Authorization and Separation-of-Duties Baseline

Approval-sensitive actions must preserve separation between requester, approver, and executor identities even when the same platform component participates in multiple stages.

A human user identity must not be repurposed as the standing identity for monitors, workflows, scheduled jobs, webhooks, or integration connectors.

n8n Community RBAC, if present, must be treated as a convenience layer rather than the sole control boundary for AegisOps authorization.

## 4. Service Account Ownership Baseline

| Automation surface | Service-account pattern | Owning role | Minimum authority expectation |
| ---- | ---- | ---- | ---- |
| Monitor or detector support | `svc-aegisops-monitor-<scope>` | Platform Administrator | Narrow read or publish permissions required to collect telemetry, emit findings, or call bounded downstream interfaces. |
| Workflow execution | `svc-aegisops-workflow-<scope>` | Platform Administrator | Only the downstream actions, queue subjects, and API scopes required for the approved workflow family. |
| Integration connector | `svc-aegisops-integration-<system>-<scope>` | Platform Administrator | Only the remote-system scopes and local secret access needed for the named integration boundary. |

## 5. Secret Scoping and Credential Lifecycle Baseline

Each secret must have a named owning team, a bounded consumer set, a documented delivery path, and a rotation expectation.

Shared credentials without a named owner, machine credentials tied to a human mailbox or personal account, and undocumented long-lived integration tokens are not an approved baseline.

Rotation requirements must distinguish between emergency rotation, scheduled rotation, and rotation triggered by ownership or scope change.

## 6. Baseline Alignment Notes

This baseline makes least-privilege identity ownership explicit before future monitors, workflows, approvals, and integrations are implemented.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing auth baseline document:"

missing_persona_repo="${workdir}/missing-persona"
create_repo "${missing_persona_repo}"
write_doc "${missing_persona_repo}" '# AegisOps Authentication, Authorization, and Service Account Ownership Baseline

## 1. Purpose

This document defines the baseline authentication, authorization, and service account ownership expectations for future AegisOps implementation work.

This document defines policy and ownership expectations only. It does not create live identities, integrate an IdP, mint credentials, or store secret material.

## 2. Human Identity Baseline

| Persona | Primary responsibility | Minimum allowed authority | Prohibited baseline shortcut |
| ---- | ---- | ---- | ---- |
| `Analyst` | Investigates alerts, findings, and cases; prepares recommendations and action requests. | Read-oriented investigation access, case updates, and ability to submit approval-bound requests within assigned scope. | Must not approve their own approval-sensitive actions or administer shared platform identity controls. |

## 3. Authorization and Separation-of-Duties Baseline

Approval-sensitive actions must preserve separation between requester, approver, and executor identities even when the same platform component participates in multiple stages.

A human user identity must not be repurposed as the standing identity for monitors, workflows, scheduled jobs, webhooks, or integration connectors.

n8n Community RBAC, if present, must be treated as a convenience layer rather than the sole control boundary for AegisOps authorization.

## 4. Service Account Ownership Baseline

| Automation surface | Service-account pattern | Owning role | Minimum authority expectation |
| ---- | ---- | ---- | ---- |
| Monitor or detector support | `svc-aegisops-monitor-<scope>` | Platform Administrator | Narrow read or publish permissions required to collect telemetry, emit findings, or call bounded downstream interfaces. |
| Workflow execution | `svc-aegisops-workflow-<scope>` | Platform Administrator | Only the downstream actions, queue subjects, and API scopes required for the approved workflow family. |
| Integration connector | `svc-aegisops-integration-<system>-<scope>` | Platform Administrator | Only the remote-system scopes and local secret access needed for the named integration boundary. |

## 5. Secret Scoping and Credential Lifecycle Baseline

Each secret must have a named owning team, a bounded consumer set, a documented delivery path, and a rotation expectation.

Shared credentials without a named owner, machine credentials tied to a human mailbox or personal account, and undocumented long-lived integration tokens are not an approved baseline.

Rotation requirements must distinguish between emergency rotation, scheduled rotation, and rotation triggered by ownership or scope change.

## 6. Baseline Alignment Notes

This baseline makes least-privilege identity ownership explicit before future monitors, workflows, approvals, and integrations are implemented.'
commit_fixture "${missing_persona_repo}"
assert_fails_with "${missing_persona_repo}" '| `Approver` | Reviews approval-bound requests and accepts or rejects execution within delegated authority. | Access to approval context, target evidence, and approval decision recording for authorized action classes. | Must remain distinct from the original requester for approval-sensitive actions and must not rely on informal side-channel approval alone. |'

missing_secret_repo="${workdir}/missing-secret"
create_repo "${missing_secret_repo}"
write_doc "${missing_secret_repo}" '# AegisOps Authentication, Authorization, and Service Account Ownership Baseline

## 1. Purpose

This document defines the baseline authentication, authorization, and service account ownership expectations for future AegisOps implementation work.

This document defines policy and ownership expectations only. It does not create live identities, integrate an IdP, mint credentials, or store secret material.

## 2. Human Identity Baseline

| Persona | Primary responsibility | Minimum allowed authority | Prohibited baseline shortcut |
| ---- | ---- | ---- | ---- |
| `Analyst` | Investigates alerts, findings, and cases; prepares recommendations and action requests. | Read-oriented investigation access, case updates, and ability to submit approval-bound requests within assigned scope. | Must not approve their own approval-sensitive actions or administer shared platform identity controls. |
| `Approver` | Reviews approval-bound requests and accepts or rejects execution within delegated authority. | Access to approval context, target evidence, and approval decision recording for authorized action classes. | Must remain distinct from the original requester for approval-sensitive actions and must not rely on informal side-channel approval alone. |
| `Platform Administrator` | Operates AegisOps infrastructure, platform configuration, connectivity, and credential plumbing. | Administrative access to platform components, secret delivery paths, service-account provisioning workflows, and recovery procedures. | Must not use `platform_admin` access as a substitute approval path for response actions and must avoid routine use of shared human credentials. |

## 3. Authorization and Separation-of-Duties Baseline

Approval-sensitive actions must preserve separation between requester, approver, and executor identities even when the same platform component participates in multiple stages.

A human user identity must not be repurposed as the standing identity for monitors, workflows, scheduled jobs, webhooks, or integration connectors.

n8n Community RBAC, if present, must be treated as a convenience layer rather than the sole control boundary for AegisOps authorization.

## 4. Service Account Ownership Baseline

| Automation surface | Service-account pattern | Owning role | Minimum authority expectation |
| ---- | ---- | ---- | ---- |
| Monitor or detector support | `svc-aegisops-monitor-<scope>` | Platform Administrator | Narrow read or publish permissions required to collect telemetry, emit findings, or call bounded downstream interfaces. |
| Workflow execution | `svc-aegisops-workflow-<scope>` | Platform Administrator | Only the downstream actions, queue subjects, and API scopes required for the approved workflow family. |
| Integration connector | `svc-aegisops-integration-<system>-<scope>` | Platform Administrator | Only the remote-system scopes and local secret access needed for the named integration boundary. |

## 5. Secret Scoping and Credential Lifecycle Baseline

Each secret must have a named owning team, a bounded consumer set, a documented delivery path, and a rotation expectation.

Shared credentials without a named owner, machine credentials tied to a human mailbox or personal account, and undocumented long-lived integration tokens are not an approved baseline.

## 6. Baseline Alignment Notes

This baseline makes least-privilege identity ownership explicit before future monitors, workflows, approvals, and integrations are implemented.'
commit_fixture "${missing_secret_repo}"
assert_fails_with "${missing_secret_repo}" "Rotation requirements must distinguish between emergency rotation, scheduled rotation, and rotation triggered by ownership or scope change."
