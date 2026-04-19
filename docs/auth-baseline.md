# AegisOps Authentication, Authorization, and Service Account Ownership Baseline

## 1. Purpose

This document defines the baseline authentication, authorization, and service account ownership expectations for future AegisOps implementation work.

It supplements `docs/requirements-baseline.md`, `docs/architecture.md`, `docs/secops-domain-model.md`, `docs/response-action-safety-model.md`, and `docs/control-plane-state-model.md` by making identity boundaries explicit before live identity providers, workflow credentials, or approval implementations exist.

This document defines policy and ownership expectations only. It does not create live identities, integrate an IdP, mint credentials, or store secret material.

## 2. Human Identity Baseline

Future AegisOps implementation must distinguish human operator personas from machine identities and must assign authority according to least privilege rather than tool convenience.

The baseline personas for approval-sensitive and platform-sensitive work are:

| Persona | Primary responsibility | Minimum allowed authority | Prohibited baseline shortcut |
| ---- | ---- | ---- | ---- |
| `Analyst` | Investigates alerts, findings, and cases; prepares recommendations and action requests. | Read-oriented investigation access, case updates, and ability to submit approval-bound requests within assigned scope. | Must not approve their own approval-sensitive actions or administer shared platform identity controls. |
| `Approver` | Reviews approval-bound requests and accepts or rejects execution within delegated authority. | Access to approval context, target evidence, and approval decision recording for authorized action classes. | Must remain distinct from the original requester for approval-sensitive actions and must not rely on informal side-channel approval alone. |
| `Platform Administrator` | Operates AegisOps infrastructure, platform configuration, connectivity, and credential plumbing. | Administrative access to platform components, secret delivery paths, service-account provisioning workflows, and recovery procedures. | Must not use platform-administrator access as a substitute approval path for response actions and must avoid routine use of shared human credentials. |

Additional future personas may be defined later, but they must inherit from this least-privilege model rather than weakening it.

Human access must be attributable to an individual operator identity with an auditable role assignment, approved administrative path, and documented ownership in the future identity source of truth.

Shared interactive administrator logins, anonymous operator accounts, and mailbox-backed human access are not an approved baseline.

The reviewed runtime boundary for human access must bind operator and approver sessions to one reviewed identity-provider path rather than trusting free-form client identity headers.

For the current SMB operating model, Authentik is the preferred reviewed human IdP boundary when a concrete provider choice is required, provided it remains behind the approved reverse proxy and does not widen AegisOps into broad IAM-program ownership.

At minimum, the reviewed reverse-proxy boundary must inject and protect all of the following before approval-sensitive runtime access is admitted:

- the reviewed identity-provider identifier;
- an attributable provider subject for the authenticated human session;
- the reviewed human identity string used inside the control plane; and
- the reviewed role assertion used for analyst, approver, or platform-administrator separation.

If any of those claims are missing, malformed, or do not match the reviewed provider boundary, the runtime must fail closed rather than inferring identity from partial headers or local naming conventions.

## 3. Authorization and Separation-of-Duties Baseline

Authorization must align to the platform boundary being crossed, not merely to which UI or workflow engine happens to expose the action.

Approval-sensitive actions must preserve separation between requester, approver, and executor identities even when the same platform component participates in multiple stages.

At minimum, the baseline requires:

- the requester identity that proposed the action to remain attributable;
- the approver identity that authorized or rejected the action to remain distinct for approval-sensitive actions;
- the executor identity to be a bounded machine or service identity rather than an untracked human session where automation is involved; and
- platform-administration authority to remain separate from approval authority unless a separately reviewed exception explicitly narrows the overlap.

A human user identity must not be repurposed as the standing identity for monitors, workflows, scheduled jobs, webhooks, or integration connectors.

Human approval alone is not sufficient if execution later occurs under a broad shared credential that cannot prove which workflow, monitor, or integration acted.

n8n Community RBAC, if present, must be treated as a convenience layer rather than the sole control boundary for AegisOps authorization.

OpenSearch roles, workflow-level permissions, reverse-proxy access controls, secret-delivery boundaries, downstream API scopes, and future AegisOps control-plane policy must compose into the authorization model instead of being collapsed into one coarse role assignment.

## 4. Service Account Ownership Baseline

Every future automation surface must run under an explicit machine identity with a named owner, bounded purpose, and limited scope.

The default ownership baseline is:

| Automation surface | Service-account pattern | Owning role | Minimum authority expectation |
| ---- | ---- | ---- | ---- |
| Monitor or detector support | `svc-aegisops-monitor-<scope>` | Platform Administrator | Narrow read or publish permissions required to collect telemetry, emit findings, or call bounded downstream interfaces. |
| Workflow execution | `svc-aegisops-workflow-<scope>` | Platform Administrator | Only the downstream actions, queue subjects, and API scopes required for the approved workflow family. |
| Integration connector | `svc-aegisops-integration-<system>-<scope>` | Platform Administrator | Only the remote-system scopes and local secret access needed for the named integration boundary. |
| Administrative automation | `svc-aegisops-admin-<scope>` | Platform Administrator | Only the maintenance or recovery permissions explicitly required for the named platform procedure, with stronger review than normal workflow identities. |

Every service account must have:

- a named owning team or role responsible for provisioning, review, and retirement;
- a documented automation surface and purpose statement;
- an explicit list of allowed systems, scopes, or API operations;
- a credential delivery path that does not expose the secret through Git or ad hoc personal storage; and
- a retirement expectation when the workflow, monitor, or integration is removed or materially redesigned.

Service accounts must be segmented by function and trust boundary. One credential should not silently span monitoring, approval, workflow execution, and platform administration when those responsibilities can be separated.

Credentials used by monitors or integrations must remain machine-owned even if a human initially provisions the remote side.

Personal accounts, shared chat identities, and human mailbox-backed tokens are not acceptable substitutes for service accounts.

## 5. Secret Scoping and Credential Lifecycle Baseline

Each secret must have a named owning team, a bounded consumer set, a documented delivery path, and a rotation expectation.

Secret scope must match the minimum authority of the identity that uses it. Credentials that cover multiple unrelated systems, excessive API scopes, or multiple approval boundaries must be split unless a reviewed exception documents why separation is not feasible.

Secrets for workflow execution, monitors, and integrations must be scoped so compromise of one automation surface does not automatically grant broad platform administration or unrelated downstream access.

Shared credentials without a named owner, machine credentials tied to a human mailbox or personal account, and undocumented long-lived integration tokens are not an approved baseline.

Rotation requirements must distinguish between emergency rotation, scheduled rotation, and rotation triggered by ownership or scope change.

At minimum, the future operating model must define:

- emergency rotation when compromise, suspected leakage, or unauthorized use is detected;
- scheduled rotation for long-lived secrets according to the secret class and system constraints;
- ownership-change rotation when the owning team, administrator set, or managed integration responsibility changes materially; and
- scope-change rotation when privilege is widened, narrowed, or rebound to a different automation surface.

Secret metadata may be documented in approved parameter or runbook artifacts, but live secret values, private keys, and production tokens must remain outside Git.

When a concrete managed secret backend is needed for the reviewed SMB operating model, OpenBao is the preferred reviewed boundary so long as it stays subordinate to the AegisOps authority model and does not widen the platform into a general-purpose vault program.

The reviewed credential-delivery pattern is:

- direct environment values only for narrowly controlled local review or bootstrap paths;
- mounted secret files for reviewed container startup and first-boot flows; and
- explicit OpenBao references for managed service-account and provider credentials when a shared secret-delivery boundary is required.

Any managed-secret integration must fail closed when the backend is unavailable, the referenced secret is unreadable, or the resolved value is empty or stale.

The initial reviewed credential families for this delivery model are the PostgreSQL DSN, Wazuh ingest secrets, reverse-proxy boundary secret, admin bootstrap and break-glass tokens, and the future reviewed machine credentials for Shuffle delegation, assistant-provider access, and reviewed ticketing integrations.

## 6. Baseline Alignment Notes

This baseline makes least-privilege identity ownership explicit before future monitors, workflows, approvals, and integrations are implemented.

It reinforces the requirements baseline rule that secrets stay out of Git, the architecture rule that detection and execution remain separate, the response-action safety rule that approval does not collapse into execution, and the control-plane rule that approval and action records must remain attributable across system boundaries.

It also prevents future implementation from assuming that n8n Community RBAC alone, undocumented shared credentials, or human-owned monitor access is sufficient for AegisOps authorization.
