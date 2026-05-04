import type { RbacRoleId } from "../../../auth/roleMatrix";

export const ADMIN_ROLE_IDS: RbacRoleId[] = [
  "platform_admin",
  "analyst",
  "approver",
  "read_only_auditor",
  "support_operator",
  "external_collaborator",
];

export const ADMIN_USERS = [
  {
    email: "platform.admin@example.com",
    role: "platform_admin",
    status: "Reviewed admin policy",
  },
  {
    email: "analyst@example.com",
    role: "analyst",
    status: "Reviewed operator policy",
  },
  {
    email: "approver@example.com",
    role: "approver",
    status: "Reviewed approval policy",
  },
] as const;

export const SOURCE_PROFILE_STATES = [
  {
    label: "Create: reviewed source profile draft",
    posture:
      "New profile requests stay blocked until source family, custody, parser, provenance, and admission boundaries are reviewed.",
  },
  {
    label: "Update: reviewed posture change",
    posture:
      "Version, intake, credential, and source-health posture changes require explicit reviewed evidence and audit linkage.",
  },
  {
    label: "Disable: source admission blocked",
    posture:
      "Disabled profiles block future source admission without rewriting historical alerts, cases, evidence, or reconciliation records.",
  },
  {
    label: "Degraded: visible subordinate context",
    posture:
      "Degraded posture stays visible to operators as source-health context only and cannot advance workflow state.",
  },
] as const;

export const SOURCE_PROFILE_AUDIT_TRAIL = [
  "Created by reviewed platform_admin session",
  "Changed fields and reason captured",
  "Disable or degraded transition records source admission impact",
  "Backend record-chain reread required before workflow use",
] as const;

export const FUTURE_SOURCE_POSTURE = [
  "Explicit reviewed source-family identifier",
  "Parser and provenance evidence present",
  "Credential custody reference reviewed",
  "No source profile state promoted to record-chain truth",
] as const;

export const ACTION_POLICY_POSTURES = [
  {
    family: "Read",
    posture: "Allowed by default",
    description:
      "Eligible for policy-authorized enrichment only when request context and execution logging stay complete.",
  },
  {
    family: "Notify",
    posture: "Allowed by default",
    description:
      "Eligible for reviewed notification posture when recipient, message intent, and escalation path are explicit.",
  },
  {
    family: "Soft Write",
    posture: "Degraded until reviewed",
    description:
      "Coordination writes stay disabled or degraded until the exact reversible action pattern and evidence path are reviewed.",
  },
] as const;

export const DISABLED_ACTION_POLICY_POSTURES = [
  {
    family: "Controlled",
    posture: "Disabled by default",
  },
  {
    family: "Hard Write",
    posture: "Disabled by default",
  },
] as const;

export const ACTION_POLICY_AUDIT_TRAIL = [
  "Policy posture change reason captured",
  "Changed by reviewed platform_admin session",
  "Default enablement decision and effective state recorded",
  "Backend authorization reread required before action use",
] as const;

export const RETENTION_RECORD_FAMILIES = [
  {
    family: "Alerts",
    posture: "Preserve authoritative detection linkage",
  },
  {
    family: "Cases",
    posture: "Preserve workflow lifecycle and closeout truth",
  },
  {
    family: "Evidence",
    posture: "Preserve custody, provenance, and subordinate context",
  },
  {
    family: "AI traces",
    posture: "Preserve advisory-only trace boundaries",
  },
  {
    family: "Audit exports",
    posture: "Preserve export custody and audit reconstruction",
  },
  {
    family: "Execution receipts",
    posture: "Preserve execution outcome and receipt lineage",
  },
  {
    family: "Reconciliations",
    posture: "Preserve mismatch and terminal reconciliation truth",
  },
] as const;

export const RETENTION_STATE_POSTURES = [
  {
    state: "Locked",
    posture: "Deletion rejected while the authoritative record is locked.",
    color: "error",
  },
  {
    state: "Export pending",
    posture: "Deletion rejected until export custody is resolved.",
    color: "error",
  },
  {
    state: "Expired",
    posture: "Eligible for future review only after authoritative reread.",
    color: "warning",
  },
  {
    state: "Active",
    posture: "Policy cannot close or advance active workflow records.",
    color: "primary",
  },
  {
    state: "Denied",
    posture: "Denied disposition remains preserved audit truth.",
    color: "default",
  },
] as const;

export const RETENTION_NEGATIVE_POSTURES = [
  "Unsafe deletion rejected",
  "Historical rewrite rejected",
  "Policy-as-closeout rejected",
  "Stale retention cache rejected",
] as const;

export const AUDIT_EXPORT_STATES = [
  {
    state: "Normal",
    posture:
      "Reviewed export window is ready to derive evidence from authoritative records.",
    color: "success",
  },
  {
    state: "Empty",
    posture:
      "No eligible authoritative records are present; empty export remains explicit.",
    color: "default",
  },
  {
    state: "Degraded",
    posture:
      "Export remains blocked or marked degraded when snapshot or custody signals are incomplete.",
    color: "warning",
  },
  {
    state: "Denied",
    posture:
      "Denied role access cannot request export configuration or view protected output.",
    color: "error",
  },
  {
    state: "Export pending",
    posture:
      "Pending generated output cannot be treated as audit, workflow, release, gate, or closeout truth.",
    color: "error",
  },
] as const;

export const AUDIT_EXPORT_ACCESS_ROLES: RbacRoleId[] = [
  "platform_admin",
  "read_only_auditor",
  "analyst",
  "approver",
  "support_operator",
  "external_collaborator",
];

export const AUDIT_EXPORT_NEGATIVE_POSTURES = [
  "Export config as audit truth rejected",
  "Export output as workflow truth rejected",
  "Denied role access rejected",
  "Stale export cache as authority rejected",
] as const;
