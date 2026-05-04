import { describe, expect, it, vi } from "vitest";
import { AuthAccessError } from "./authProvider";
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

describe("createSessionStore", () => {
  it("returns only reviewed operator roles from the validated session", async () => {
    const config = createOperatorUiConfig({
      allowedRoles: ["analyst", "approver"],
    });
    const sessionStore = createSessionStore({
      config,
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst", "viewer", "approver"],
          subject: "operator-9",
        }),
      ),
    });

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      roles: ["analyst", "approver"],
    });
  });

  it("accepts the backend canonical platform_admin role by default", async () => {
    const config = createOperatorUiConfig();
    const sessionStore = createSessionStore({
      config,
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "platform.admin@example.com",
          provider: "authentik",
          roles: ["platform_admin"],
          subject: "operator-44",
        }),
      ),
    });

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      roles: ["platform_admin"],
    });
  });

  it("accepts every Phase 57.1 commercial RBAC matrix role by default", async () => {
    const config = createOperatorUiConfig();
    const sessionStore = createSessionStore({
      config,
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "auditor@example.com",
          provider: "authentik",
          roles: [
            "platform_admin",
            "analyst",
            "approver",
            "read_only_auditor",
            "support_operator",
            "external_collaborator",
          ],
          subject: "operator-57-1",
        }),
      ),
    });

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      roles: [
        "platform_admin",
        "analyst",
        "approver",
        "read_only_auditor",
        "support_operator",
        "external_collaborator",
      ],
    });
  });

  it("clears a cached session when a forced refresh returns unauthenticated", async () => {
    const config = createOperatorUiConfig({
      allowedRoles: ["analyst"],
    });
    const fetchFn = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          identity: "stale@example.com",
          provider: "authentik",
          roles: ["analyst"],
          subject: "operator-9",
        }),
      )
      .mockResolvedValueOnce(
        new Response(null, {
          status: 401,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          identity: "fresh@example.com",
          provider: "authentik",
          roles: ["analyst"],
          subject: "operator-10",
        }),
      );
    const sessionStore = createSessionStore({
      config,
      fetchFn,
    });

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      identity: "stale@example.com",
    });

    await expect(sessionStore.getSession({ force: true })).rejects.toMatchObject({
      code: "unauthenticated",
    } satisfies Partial<AuthAccessError>);

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      identity: "fresh@example.com",
    });
    expect(fetchFn).toHaveBeenCalledTimes(3);
  });

  it("clears a cached session when a forced refresh returns invalid JSON", async () => {
    const config = createOperatorUiConfig({
      allowedRoles: ["analyst"],
    });
    const fetchFn = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          identity: "stale@example.com",
          provider: "authentik",
          roles: ["analyst"],
          subject: "operator-9",
        }),
      )
      .mockResolvedValueOnce(
        new Response("not-json", {
          headers: {
            "Content-Type": "application/json",
          },
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          identity: "fresh@example.com",
          provider: "authentik",
          roles: ["analyst"],
          subject: "operator-10",
        }),
      );
    const sessionStore = createSessionStore({
      config,
      fetchFn,
    });

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      identity: "stale@example.com",
    });

    await expect(sessionStore.getSession({ force: true })).rejects.toMatchObject({
      code: "invalid_session",
    } satisfies Partial<AuthAccessError>);

    await expect(sessionStore.getSession()).resolves.toMatchObject({
      identity: "fresh@example.com",
    });
    expect(fetchFn).toHaveBeenCalledTimes(3);
  });
});
