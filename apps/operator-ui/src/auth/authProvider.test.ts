import { describe, expect, it, vi } from "vitest";
import { createOperatorAuthProvider } from "./authProvider";
import { createOperatorUiConfig } from "./config";
import { createSessionStore } from "./session";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

describe("createOperatorAuthProvider", () => {
  it("redirects login through the reviewed OIDC entrypoint", async () => {
    const redirector = {
      replace: vi.fn(),
    };
    const config = createOperatorUiConfig();
    const sessionStore = createSessionStore({
      config,
      fetchFn: vi.fn(),
    });

    const authProvider = createOperatorAuthProvider({
      config,
      sessionStore,
      fetchFn: vi.fn(),
      redirector,
    });

    await authProvider.login({
      returnTo: "/operator/queue?status=open",
    });

    expect(redirector.replace).toHaveBeenCalledWith(
      "/auth/oidc/login?returnTo=%2Foperator%2Fqueue%3Fstatus%3Dopen",
    );
  });

  it("posts logout to the backend session boundary and clears the shell", async () => {
    const fetchFn = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          identity: "alice@example.com",
          provider: "authentik",
          roles: ["analyst"],
          subject: "operator-123",
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    const redirector = {
      replace: vi.fn(),
    };
    const config = createOperatorUiConfig();
    const sessionStore = createSessionStore({
      config,
      fetchFn,
    });

    const authProvider = createOperatorAuthProvider({
      config,
      sessionStore,
      fetchFn,
      redirector,
    });

    await authProvider.checkAuth({});
    await authProvider.logout({});

    expect(fetchFn).toHaveBeenNthCalledWith(
      2,
      "/api/operator/logout",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
      }),
    );
    expect(redirector.replace).toHaveBeenCalledWith("/operator/login");
  });
});
