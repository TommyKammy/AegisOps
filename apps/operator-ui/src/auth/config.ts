import { RBAC_ROLE_IDS } from "./roleMatrix";

export interface OperatorUiConfig {
  allowedRoles: string[];
  basePath: string;
  loginPath: string;
  logoutPath: string;
  sessionPath: string;
}

const DEFAULT_ALLOWED_ROLES = [...RBAC_ROLE_IDS];

export function createOperatorUiConfig(
  overrides: Partial<OperatorUiConfig> = {},
): OperatorUiConfig {
  return {
    allowedRoles: overrides.allowedRoles ?? DEFAULT_ALLOWED_ROLES,
    basePath: overrides.basePath ?? "/operator",
    loginPath: overrides.loginPath ?? "/auth/oidc/login",
    logoutPath: overrides.logoutPath ?? "/api/operator/logout",
    sessionPath: overrides.sessionPath ?? "/api/operator/session",
  };
}
