import type { AuthProvider } from "react-admin";
import type { Redirector } from "./navigation";
import type { OperatorUiConfig } from "./config";
import type { SessionStore } from "./session";

export class AuthAccessError extends Error {
  code: "forbidden" | "invalid_session" | "unauthenticated";

  constructor(code: "forbidden" | "invalid_session" | "unauthenticated", message: string) {
    super(message);
    this.code = code;
  }
}

function buildLoginRedirect(loginPath: string, returnTo: string) {
  const url = new URL(loginPath, "http://operator-ui.local");
  url.searchParams.set("returnTo", returnTo);
  return `${url.pathname}${url.search}`;
}

export function createOperatorAuthProvider({
  config,
  sessionStore,
  fetchFn = fetch,
  redirector,
}: {
  config: OperatorUiConfig;
  sessionStore: SessionStore;
  fetchFn?: typeof fetch;
  redirector: Redirector;
}): AuthProvider {
  return {
    async login(params?: { returnTo?: string }) {
      const returnTo = params?.returnTo ?? config.basePath;
      redirector.replace(buildLoginRedirect(config.loginPath, returnTo));
    },

    async logout() {
      try {
        await fetchFn(config.logoutPath, {
          credentials: "include",
          method: "POST",
        });
      } finally {
        sessionStore.clear();
        redirector.replace(`${config.basePath}/login`);
      }
    },

    async checkAuth() {
      await sessionStore.getSession({ force: true });
    },

    async checkError(error: unknown) {
      if (error instanceof AuthAccessError) {
        throw error;
      }

      if (
        typeof error === "object" &&
        error !== null &&
        "status" in error &&
        (error.status === 401 || error.status === 403)
      ) {
        throw new AuthAccessError(
          error.status === 403 ? "forbidden" : "unauthenticated",
          "Backend session boundary rejected the request.",
        );
      }
    },

    async getIdentity() {
      const session = await sessionStore.getSession();

      return {
        fullName: session.identity,
        id: session.subject,
      };
    },

    async getPermissions() {
      const session = await sessionStore.getSession();
      return session.roles;
    },
  };
}
