import { describe, expect, it } from "vitest";
import entrySource from "../adminPages.tsx?raw";
import postureDataSource from "./adminPostureData.ts?raw";

describe("admin page module structure", () => {
  it("keeps the admin entry file as a compatibility export", () => {
    expect(entrySource.trim()).toBe(
      'export { UserRoleAdminPage } from "./adminPages/UserRoleAdminPage";',
    );
    expect(entrySource).not.toContain("SOURCE_PROFILE_STATES");
    expect(entrySource).not.toContain("function SourceProfileAdministrationPage");
    expect(postureDataSource).toContain("export const SOURCE_PROFILE_STATES");
    expect(postureDataSource).toContain("export const AUDIT_EXPORT_STATES");
  });
});
