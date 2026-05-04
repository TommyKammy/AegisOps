import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  buildOptionalEvidenceDefinitionsFromPayload,
  buildOptionalExtensionDefinitionsFromPayload,
} from "./optionalExtensionVisibility";
import {
  createAuthorizedFetch,
  createOptionalExtensionPayload,
  createReadinessResponse,
  TestRouteNavigator,
  jsonResponse,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesAuthAndShellTests() {
  describe("auth and shell", () => {
    it("keeps disabled-by-default endpoint and network evidence posture visible", () => {
    const definitions = buildOptionalEvidenceDefinitionsFromPayload(
      createOptionalExtensionPayload(),
    );

    expect(definitions).toEqual([
      expect.objectContaining({
        status: "disabled_by_default",
        title: "Endpoint evidence",
      }),
      expect.objectContaining({
        status: "disabled_by_default",
        title: "Optional network evidence",
      }),
    ]);
    });

    it("fails closed when optional enablement is present without backend availability", () => {
    const definitions = buildOptionalExtensionDefinitionsFromPayload(
      createOptionalExtensionPayload({
        endpoint_evidence: {
          authority_mode: "augmenting_evidence",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "ready",
          reason: "reviewed_endpoint_extension_binding_missing",
        },
      }),
    );

    expect(definitions).toContainEqual(
      expect.objectContaining({
        status: "unavailable",
        title: "Endpoint evidence",
      }),
    );
    });

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
    const fetchFn = createAuthorizedFetch({
      "/diagnostics/readiness": createReadinessResponse({
        ml_shadow: {
          authority_mode: "shadow_only",
          availability: "available",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "degraded",
          reason: "reviewed_ml_shadow_extension_provider_lagging",
        },
        network_evidence: undefined,
      }),
    });
    const dependencies = createDefaultDependencies({
      fetchFn,
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

    expect(
      screen.getByRole("heading", { name: "Optional extension visibility" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Optional-path posture stays subordinate to authoritative workflow pages and reviewed runtime truth.",
      ),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Enabled")).toBeInTheDocument();
    });
    expect(screen.getByText("Disabled By Default")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Reviewed status source: reviewed ml shadow extension provider lagging\./i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Missing optional paths do not imply a control-plane failure when the mainline reviewed workflow remains healthy.",
      ),
    ).toBeInTheDocument();
    expect(fetchFn).toHaveBeenCalledWith(
      "/diagnostics/readiness?order=ASC&page=1&per_page=1&sort=status",
      expect.any(Object),
    );
    });

    it("hides action-review navigation for analyst-only sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
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

    expect(screen.queryByText(/action review/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: "Actions" })).toBeNull();
    expect(screen.queryByRole("menuitem", { name: "Automations" })).toBeNull();
    expect(screen.queryByRole("menuitem", { name: "Admin" })).toBeNull();
    });

    it("fails closed on analyst-only direct access to protected admin routes", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator/admin"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Access denied" }),
      ).toBeInTheDocument();
    });
    });

    it("shows action-review navigation for reviewed approver sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        },
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

    expect(screen.getAllByText(/action review/i).length).toBeGreaterThan(0);
    });

    it("shows action-review navigation for backend canonical platform_admin sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "platform.admin@example.com",
          provider: "authentik",
          roles: ["platform_admin"],
          subject: "operator-44",
        },
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

    expect(screen.getAllByText(/action review/i).length).toBeGreaterThan(0);
    });

    it("uses the configured base path for reviewed operator navigation links and Phase 56.7 workbench aliases", async () => {
    const dependencies = createDefaultDependencies({
      config: {
        basePath: "/reviewed-operator",
      },
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/reviewed-operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    [
      ["Today", "/reviewed-operator/today"],
      ["Queue", "/reviewed-operator/queue"],
      ["Cases", "/reviewed-operator/cases"],
      ["Actions", "/reviewed-operator/actions"],
      ["Sources", "/reviewed-operator/sources"],
      ["Automations", "/reviewed-operator/automations"],
      ["Reports", "/reviewed-operator/reports"],
      ["Health", "/reviewed-operator/health"],
    ].forEach(([label, href]) => {
      expect(screen.getByRole("menuitem", { name: label })).toHaveAttribute(
        "href",
        expect.stringContaining(href),
      );
    });
    expect(screen.queryByRole("menuitem", { name: "Admin" })).toBeNull();
    });

    it("shows Admin navigation only for backend canonical platform_admin sessions", async () => {
    const dependencies = createDefaultDependencies({
      config: {
        basePath: "/reviewed-operator",
      },
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "platform.admin@example.com",
          provider: "authentik",
          roles: ["platform_admin"],
          subject: "operator-44",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/reviewed-operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByRole("menuitem", { name: "Admin" })).toHaveAttribute(
      "href",
      expect.stringContaining("/reviewed-operator/admin"),
    );
    });

    it("renders the user and role admin surface only for platform admins", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "platform.admin@example.com",
          provider: "authentik",
          roles: ["platform_admin"],
          subject: "operator-44",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator/admin"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "User and role administration" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Roles")).toBeInTheDocument();
    expect(
      screen.getByText(
        "User and role changes are reviewed policy/config state only; they cannot rewrite historical workflow truth.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Stale browser role cache is never authority. Backend reread and denial remain decisive.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant/i)).not.toBeInTheDocument();
    });

    it("renders bounded source profile administration for platform admins", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "platform.admin@example.com",
          provider: "authentik",
          roles: ["platform_admin"],
          subject: "operator-44",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator/admin"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Source profile administration" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Wazuh SMB single-node")).toBeInTheDocument();
    expect(screen.getByText("Create: reviewed source profile draft")).toBeInTheDocument();
    expect(screen.getByText("Update: reviewed posture change")).toBeInTheDocument();
    expect(screen.getByText("Disable: source admission blocked")).toBeInTheDocument();
    expect(screen.getByText("Degraded: visible subordinate context")).toBeInTheDocument();
    expect(screen.getByText("Audit trail")).toBeInTheDocument();
    expect(screen.getByText("Future reviewed sources")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Source profile state configures source admission posture only; it cannot become signal, alert, case, evidence, workflow, release, gate, or closeout truth.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Stale source admin UI or browser cache is never authority. Backend record-chain reread remains decisive before source admission or workflow use.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/marketplace/i)).not.toBeInTheDocument();
    });

    it("fails closed when stale platform-admin browser state reaches the admin route", async () => {
    const user = userEvent.setup();
    let sessionRequests = 0;
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input) => {
      const url = String(input);

      if (url.startsWith("/api/operator/session")) {
        sessionRequests += 1;

        return Promise.resolve(
          jsonResponse(
            sessionRequests === 1
              ? {
                  identity: "platform.admin@example.com",
                  provider: "authentik",
                  roles: ["platform_admin"],
                  subject: "operator-44",
                }
              : {
                  identity: "analyst@example.com",
                  provider: "authentik",
                  roles: ["analyst"],
                  subject: "operator-7",
                },
          ),
        );
      }

      if (url.startsWith("/diagnostics/readiness")) {
        return Promise.resolve(jsonResponse(createReadinessResponse()));
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <TestRouteNavigator />
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Go to admin" }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Access denied" }),
      ).toBeInTheDocument();
    });
    expect(sessionRequests).toBeGreaterThanOrEqual(2);
    });

    it("renders an explicit unsupported-route outcome for unknown operator shell paths", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator/not-reviewed-path"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Unsupported operator route" }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Use the queue, authoritative detail links, reviewed diagnostics, or other approved operator entrypoints instead of guessing route shape.",
      ),
    ).toBeInTheDocument();
    });
  });
}
