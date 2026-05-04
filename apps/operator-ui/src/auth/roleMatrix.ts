export const RBAC_ROLE_IDS = [
  "platform_admin",
  "analyst",
  "approver",
  "read_only_auditor",
  "support_operator",
  "external_collaborator",
] as const;

export type RbacRoleId = (typeof RBAC_ROLE_IDS)[number];

export type RbacSurfaceAccess =
  | "allowed"
  | "denied"
  | "read_only"
  | "admin_only"
  | "support_only"
  | "no_authority";

export interface RbacRoleContract {
  description: string;
  surfaces: {
    actionApprovalDecision: RbacSurfaceAccess;
    actionRequestSubmission: RbacSurfaceAccess;
    auditExport: RbacSurfaceAccess;
    externalCollaboration: RbacSurfaceAccess;
    historicalTruthRewrite: RbacSurfaceAccess;
    investigationNotes: RbacSurfaceAccess;
    platformAdministration: RbacSurfaceAccess;
    supportDiagnostics: RbacSurfaceAccess;
    workbenchInspection: RbacSurfaceAccess;
    workflowAuthorityOverride: RbacSurfaceAccess;
  };
  workflowAuthority: false;
}

export const RBAC_ROLE_MATRIX: Record<RbacRoleId, RbacRoleContract> = {
  platform_admin: {
    description:
      "Operates platform configuration and identity wiring without becoming workflow truth.",
    surfaces: {
      actionApprovalDecision: "denied",
      actionRequestSubmission: "denied",
      auditExport: "admin_only",
      externalCollaboration: "denied",
      historicalTruthRewrite: "denied",
      investigationNotes: "read_only",
      platformAdministration: "admin_only",
      supportDiagnostics: "denied",
      workbenchInspection: "read_only",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
  analyst: {
    description:
      "Reviews assigned workflow records and submits approval-bound action requests.",
    surfaces: {
      actionApprovalDecision: "denied",
      actionRequestSubmission: "allowed",
      auditExport: "denied",
      externalCollaboration: "denied",
      historicalTruthRewrite: "denied",
      investigationNotes: "allowed",
      platformAdministration: "denied",
      supportDiagnostics: "denied",
      workbenchInspection: "allowed",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
  approver: {
    description:
      "Records reviewed approval decisions on approval-bound requests in assigned scope.",
    surfaces: {
      actionApprovalDecision: "allowed",
      actionRequestSubmission: "denied",
      auditExport: "denied",
      externalCollaboration: "denied",
      historicalTruthRewrite: "denied",
      investigationNotes: "read_only",
      platformAdministration: "denied",
      supportDiagnostics: "denied",
      workbenchInspection: "read_only",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
  read_only_auditor: {
    description:
      "Inspects reviewed workflow and audit surfaces without write authority.",
    surfaces: {
      actionApprovalDecision: "denied",
      actionRequestSubmission: "denied",
      auditExport: "read_only",
      externalCollaboration: "denied",
      historicalTruthRewrite: "denied",
      investigationNotes: "read_only",
      platformAdministration: "denied",
      supportDiagnostics: "denied",
      workbenchInspection: "read_only",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
  support_operator: {
    description:
      "Runs customer-safe diagnostics and support workflows without approval or closeout authority.",
    surfaces: {
      actionApprovalDecision: "denied",
      actionRequestSubmission: "denied",
      auditExport: "denied",
      externalCollaboration: "denied",
      historicalTruthRewrite: "denied",
      investigationNotes: "read_only",
      platformAdministration: "denied",
      supportDiagnostics: "support_only",
      workbenchInspection: "read_only",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
  external_collaborator: {
    description:
      "Supplies bounded collaboration context without AegisOps workflow authority.",
    surfaces: {
      actionApprovalDecision: "denied",
      actionRequestSubmission: "denied",
      auditExport: "denied",
      externalCollaboration: "no_authority",
      historicalTruthRewrite: "denied",
      investigationNotes: "read_only",
      platformAdministration: "denied",
      supportDiagnostics: "denied",
      workbenchInspection: "read_only",
      workflowAuthorityOverride: "denied",
    },
    workflowAuthority: false,
  },
};

export function normalizeRbacRole(role: string): string {
  return role.trim().toLowerCase();
}

export function isCommercialRbacRole(role: string): role is RbacRoleId {
  return Object.prototype.hasOwnProperty.call(
    RBAC_ROLE_MATRIX,
    normalizeRbacRole(role),
  );
}

export function getRbacRoleContract(role: string): RbacRoleContract | null {
  const normalizedRole = normalizeRbacRole(role);
  return isCommercialRbacRole(normalizedRole)
    ? RBAC_ROLE_MATRIX[normalizedRole]
    : null;
}

export function roleHasSurfaceAccess(
  role: string,
  surface: keyof RbacRoleContract["surfaces"],
  access: RbacSurfaceAccess,
): boolean {
  return getRbacRoleContract(role)?.surfaces[surface] === access;
}

export function anyRoleHasSurfaceAccess(
  roles: readonly string[],
  surface: keyof RbacRoleContract["surfaces"],
  access: RbacSurfaceAccess,
): boolean {
  return roles.some((role) => roleHasSurfaceAccess(role, surface, access));
}
