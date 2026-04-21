import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import {
  OperatorRoutes,
  createDefaultDependencies,
} from "./OperatorRoutes";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

describe("OperatorRoutes", () => {
  it("redirects unauthenticated users to the reviewed login route", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 401 })),
    });

    render(
      <MemoryRouter initialEntries={["/operator/queue"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Operator Sign-In" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Return path: /operator/queue")).toBeInTheDocument();
  });

  it("routes unsupported backend roles to the forbidden page", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "reviewer@example.com",
          provider: "authentik",
          roles: ["viewer"],
          subject: "user-42",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Access denied" }),
      ).toBeInTheDocument();
    });
  });

  it("fails closed on malformed reviewed session responses", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: "analyst",
          subject: "operator-11",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Session verification failed" }),
      ).toBeInTheDocument();
    });
  });

  it("restores an authorized session into the protected shell", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst"],
          subject: "operator-7",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });
  });
});
