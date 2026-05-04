import { describe, expect, it } from "vitest";
import {
  RBAC_ROLE_IDS,
  RBAC_ROLE_MATRIX,
  anyRoleHasSurfaceAccess,
  getRbacRoleContract,
} from "./roleMatrix";

describe("Phase 57.1 RBAC role matrix", () => {
  it("names every required commercial RBAC role", () => {
    expect(RBAC_ROLE_IDS).toEqual([
      "platform_admin",
      "analyst",
      "approver",
      "read_only_auditor",
      "support_operator",
      "external_collaborator",
    ]);
  });

  it("covers allowed, denied, read-only, admin-only, support-only, and no-authority behavior", () => {
    const observedAccess = new Set(
      Object.values(RBAC_ROLE_MATRIX).flatMap((contract) =>
        Object.values(contract.surfaces),
      ),
    );

    expect(observedAccess).toEqual(
      new Set([
        "allowed",
        "denied",
        "read_only",
        "admin_only",
        "support_only",
        "no_authority",
      ]),
    );
  });

  it("keeps support and external roles out of workflow authority", () => {
    for (const role of ["support_operator", "external_collaborator"]) {
      const contract = getRbacRoleContract(role);

      expect(contract?.workflowAuthority).toBe(false);
      expect(contract?.surfaces.actionApprovalDecision).toBe("denied");
      expect(contract?.surfaces.actionRequestSubmission).toBe("denied");
      expect(contract?.surfaces.workflowAuthorityOverride).toBe("denied");
      expect(contract?.surfaces.historicalTruthRewrite).toBe("denied");
    }
  });

  it("does not treat platform administration as approval authority", () => {
    expect(
      anyRoleHasSurfaceAccess(
        ["platform_admin"],
        "platformAdministration",
        "admin_only",
      ),
    ).toBe(true);
    expect(
      anyRoleHasSurfaceAccess(
        ["platform_admin"],
        "actionApprovalDecision",
        "allowed",
      ),
    ).toBe(false);
  });

  it("separates analyst request authority from approver decision authority", () => {
    expect(
      anyRoleHasSurfaceAccess(
        ["analyst"],
        "actionRequestSubmission",
        "allowed",
      ),
    ).toBe(true);
    expect(
      anyRoleHasSurfaceAccess(
        ["analyst"],
        "actionApprovalDecision",
        "allowed",
      ),
    ).toBe(false);
    expect(
      anyRoleHasSurfaceAccess(
        ["approver"],
        "actionApprovalDecision",
        "allowed",
      ),
    ).toBe(true);
    expect(
      anyRoleHasSurfaceAccess(
        ["approver"],
        "actionRequestSubmission",
        "allowed",
      ),
    ).toBe(false);
  });

  it("keeps read-only auditor and external collaborator write-forbidden", () => {
    for (const role of ["read_only_auditor", "external_collaborator"]) {
      const contract = getRbacRoleContract(role);

      expect(contract?.surfaces.workbenchInspection).toBe("read_only");
      expect(contract?.surfaces.investigationNotes).toBe("read_only");
      expect(contract?.surfaces.actionRequestSubmission).toBe("denied");
      expect(contract?.surfaces.actionApprovalDecision).toBe("denied");
    }
  });
});
