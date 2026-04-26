#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/auth-baseline.md"

required_headings=(
  "# AegisOps Authentication, Authorization, and Service Account Ownership Baseline"
  "## 1. Purpose"
  "## 2. Human Identity Baseline"
  "## 3. Authorization and Separation-of-Duties Baseline"
  "## 4. Service Account Ownership Baseline"
  "## 5. Secret Scoping and Credential Lifecycle Baseline"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the baseline authentication, authorization, and service account ownership expectations for future AegisOps implementation work."
  "This document defines policy and ownership expectations only. It does not create live identities, integrate an IdP, mint credentials, or store secret material."
  '| `Analyst` | Investigates alerts, findings, and cases; prepares recommendations and action requests. | Read-oriented investigation access, case updates, and ability to submit approval-bound requests within assigned scope. | Must not approve their own approval-sensitive actions or administer shared platform identity controls. |'
  '| `Approver` | Reviews approval-bound requests and accepts or rejects execution within delegated authority. | Access to approval context, target evidence, and approval decision recording for authorized action classes. | Must remain distinct from the original requester for approval-sensitive actions and must not rely on informal side-channel approval alone. |'
  '| `Platform Administrator` | Operates AegisOps infrastructure, platform configuration, connectivity, and credential plumbing. | Administrative access to platform components, secret delivery paths, service-account provisioning workflows, and recovery procedures. | Must not use `platform_admin` access as a substitute approval path for response actions and must avoid routine use of shared human credentials. |'
  "Approval-sensitive actions must preserve separation between requester, approver, and executor identities even when the same platform component participates in multiple stages."
  "A human user identity must not be repurposed as the standing identity for monitors, workflows, scheduled jobs, webhooks, or integration connectors."
  '| Monitor or detector support | `svc-aegisops-monitor-<scope>` | Platform Administrator | Narrow read or publish permissions required to collect telemetry, emit findings, or call bounded downstream interfaces. |'
  '| Workflow execution | `svc-aegisops-workflow-<scope>` | Platform Administrator | Only the downstream actions, queue subjects, and API scopes required for the approved workflow family. |'
  '| Integration connector | `svc-aegisops-integration-<system>-<scope>` | Platform Administrator | Only the remote-system scopes and local secret access needed for the named integration boundary. |'
  "n8n Community RBAC, if present, must be treated as a convenience layer rather than the sole control boundary for AegisOps authorization."
  "Each secret must have a named owning team, a bounded consumer set, a documented delivery path, and a rotation expectation."
  "Shared credentials without a named owner, machine credentials tied to a human mailbox or personal account, and undocumented long-lived integration tokens are not an approved baseline."
  "Rotation requirements must distinguish between emergency rotation, scheduled rotation, and rotation triggered by ownership or scope change."
  "This baseline makes least-privilege identity ownership explicit before future monitors, workflows, approvals, and integrations are implemented."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing auth baseline document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq "${heading}" "${doc_path}"; then
    echo "Missing auth baseline heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing auth baseline statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Auth baseline document is present and defines personas, service-account ownership, and secret lifecycle expectations."
