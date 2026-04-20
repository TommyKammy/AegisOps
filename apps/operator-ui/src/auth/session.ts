import { AuthAccessError } from "./authProvider";
import type { OperatorUiConfig } from "./config";

export interface OperatorSession {
  identity: string;
  provider: string;
  roles: string[];
  subject: string;
}

export interface SessionStore {
  clear: () => void;
  getSession: (options?: { force?: boolean }) => Promise<OperatorSession>;
}

function normalizeRoles(roles: unknown): string[] {
  if (!Array.isArray(roles)) {
    throw new AuthAccessError(
      "invalid_session",
      "Operator session is missing the reviewed role claims.",
    );
  }

  return roles
    .filter((role): role is string => typeof role === "string")
    .map((role) => role.trim().toLowerCase())
    .filter(Boolean);
}

function validateSession(
  value: unknown,
  config: OperatorUiConfig,
): OperatorSession {
  if (typeof value !== "object" || value === null) {
    throw new AuthAccessError(
      "invalid_session",
      "Operator session payload is not an object.",
    );
  }

  const provider =
    "provider" in value && typeof value.provider === "string"
      ? value.provider.trim()
      : "";
  const subject =
    "subject" in value && typeof value.subject === "string"
      ? value.subject.trim()
      : "";
  const identity =
    "identity" in value && typeof value.identity === "string"
      ? value.identity.trim()
      : "";
  const roles = normalizeRoles("roles" in value ? value.roles : undefined);

  if (!provider || !subject || !identity) {
    throw new AuthAccessError(
      "invalid_session",
      "Operator session is missing reviewed provider, subject, or identity claims.",
    );
  }

  if (!roles.some((role) => config.allowedRoles.includes(role))) {
    throw new AuthAccessError(
      "forbidden",
      "The authenticated session does not include a reviewed operator role.",
    );
  }

  return {
    identity,
    provider,
    roles,
    subject,
  };
}

export function createSessionStore({
  config,
  fetchFn = fetch,
}: {
  config: OperatorUiConfig;
  fetchFn?: typeof fetch;
}): SessionStore {
  let cachedSession: OperatorSession | null = null;

  return {
    clear() {
      cachedSession = null;
    },

    async getSession(options?: { force?: boolean }) {
      if (cachedSession && !options?.force) {
        return cachedSession;
      }

      const response = await fetchFn(config.sessionPath, {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (response.status === 401) {
        throw new AuthAccessError(
          "unauthenticated",
          "Operator session is not authenticated.",
        );
      }

      if (response.status === 403) {
        throw new AuthAccessError(
          "forbidden",
          "Operator session is authenticated but not authorized.",
        );
      }

      if (!response.ok) {
        throw new AuthAccessError(
          "invalid_session",
          `Unexpected operator session status ${response.status}.`,
        );
      }

      cachedSession = validateSession(await response.json(), config);
      return cachedSession;
    },
  };
}
