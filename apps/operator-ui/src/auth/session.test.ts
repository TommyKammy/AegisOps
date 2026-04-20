import { describe, expect, it, vi } from "vitest";
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
});
