import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  createReadinessResponse,
  jsonResponse,
  renderOperatorRoute,
  TestRouteNavigator,
} from "./OperatorRoutes.testSupport";

const normalTodayProjection = {
  authority_boundary:
    "Today view projection is subordinate backend summary context only.",
  generated_at: "2026-05-04T08:00:00Z",
  lanes: {
    ai_suggested_focus: [
      {
        advisory_only: true,
        authoritative_record: {
          family: "case",
          id: "case-101",
        },
        id: "focus-1",
        reason: "Directly linked stale case and evidence gap need review.",
        state: "normal",
        title: "Review case-101 before lunch handoff",
      },
    ],
    degraded_sources: [
      {
        authoritative_record: {
          family: "source",
          id: "source-wazuh-1",
        },
        id: "degraded-1",
        reason: "Wazuh source health is lagging but remains subordinate.",
        source_family: "wazuh",
        state: "degraded",
        title: "Wazuh manager freshness degraded",
      },
    ],
    evidence_gaps: [
      {
        authoritative_record: {
          family: "case",
          id: "case-101",
        },
        id: "evidence-1",
        reason: "Required custody record is missing.",
        state: "evidence_gap",
        title: "Evidence custody gap on case-101",
      },
    ],
    pending_approvals: [
      {
        authoritative_record: {
          family: "action_review",
          id: "review-101",
        },
        id: "approval-1",
        reason: "Approver decision is required before execution.",
        state: "normal",
        title: "Approve containment request review-101",
      },
    ],
    priority: [
      {
        authoritative_record: {
          family: "case",
          id: "case-101",
        },
        id: "priority-1",
        priority_rank: 1,
        reason: "High severity case has pending approval and evidence gap.",
        state: "normal",
        title: "Review case-101",
      },
    ],
    reconciliation_mismatches: [
      {
        authoritative_record: {
          family: "reconciliation",
          id: "recon-101",
        },
        id: "mismatch-1",
        reason: "Receipt and reconciliation state disagree.",
        state: "mismatch",
        title: "Reconciliation mismatch recon-101",
      },
    ],
    stale_work: [
      {
        authoritative_record: {
          family: "alert",
          id: "alert-101",
        },
        id: "stale-1",
        reason: "No authoritative lifecycle update in four hours.",
        state: "stale",
        title: "Stale alert alert-101",
      },
    ],
  },
  projection_id: "today-2026-05-04",
  projection_state: "normal",
  read_only: true,
  stale_cache: false,
  today_view_projection_contract_version: "2026-05-04",
};

export function registerOperatorRoutesTodayTests() {
  describe("today workbench route", () => {
    it("discovers the Today workbench through reviewed operator navigation", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-today-view": normalTodayProjection,
        }),
      });

      renderOperatorRoute("/operator/today", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Today" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByRole("menuitem", { name: "Today" })).toHaveAttribute(
        "href",
        expect.stringContaining("/operator/today"),
      );
      expect(screen.getByText("Daily SOC Workbench")).toBeInTheDocument();
    });

    it("renders normal work focus, stale and degraded badges, gaps, mismatches, approvals, and advisory AI focus", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/diagnostics/readiness": createReadinessResponse({
            assistant: {
              authority_mode: "advisory_only",
              availability: "available",
              enablement: "enabled",
              mainline_dependency: "non_blocking",
              readiness: "degraded",
              reason: "reviewed_assistant_provider_lagging",
            },
          }),
          "/inspect-today-view": normalTodayProjection,
        }),
      });

      renderOperatorRoute("/operator/today", dependencies);

      await waitFor(() => {
        expect(screen.getByText("Review case-101")).toBeInTheDocument();
      });

      expect(screen.getByText("Stale alert alert-101")).toBeInTheDocument();
      expect(
        screen.getByText("Wazuh manager freshness degraded"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Approve containment request review-101"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Reconciliation mismatch recon-101"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Evidence custody gap on case-101"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Review case-101 before lunch handoff"),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Workbench health summary" }),
      ).toBeInTheDocument();
      expect(screen.getByText("Status: ready")).toBeInTheDocument();
      expect(screen.getByText("Assistant readiness: degraded")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Health summary is backend-bound operator context only; it cannot satisfy release, readiness, audit, approval, execution, reconciliation, or closeout gates.",
        ),
      ).toBeInTheDocument();
      expect(screen.getAllByText("Stale").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Degraded").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Advisory only").length).toBeGreaterThan(0);
      expect(screen.queryByRole("button", { name: /approve/i })).toBeNull();
      expect(
        screen.queryByRole("button", { name: /close today work/i }),
      ).toBeNull();
      expect(screen.queryByRole("button", { name: /execute/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /reconcile/i })).toBeNull();
    });

    it("renders bounded operator task cards that route to existing reviewed surfaces only", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-today-view": normalTodayProjection,
        }),
      });

      renderOperatorRoute("/operator/today", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Operator task cards" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByRole("link", { name: "Review stale work" }),
      ).toHaveAttribute("href", "/operator/alerts/alert-101");
      expect(
        screen.getByRole("link", { name: "Inspect pending approvals" }),
      ).toHaveAttribute("href", "/operator/action-review/review-101");
      expect(
        screen.getByRole("link", { name: "Resolve evidence gaps" }),
      ).toHaveAttribute("href", "/operator/cases/case-101");
      expect(
        screen.getByRole("link", { name: "Check degraded sources" }),
      ).toHaveAttribute("href", "/operator/readiness");
      expect(
        screen.getByRole("link", { name: "Inspect mismatches" }),
      ).toHaveAttribute("href", "/operator/reconciliation");
      expect(
        screen.getByRole("link", { name: "Prepare handoff" }),
      ).toHaveAttribute("href", "/operator/handoff");

      expect(screen.getAllByText("State remains unresolved").length).toBeGreaterThan(0);
      expect(
        screen.getByText(
          "Task cards launch reviewed routes or bounded write surfaces; they cannot approve, execute, reconcile, close, or treat UI state as task completion truth.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /mark resolved/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /complete task/i })).toBeNull();
    });

    it("renders an explicit empty state without implying workflow completion", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-today-view": {
            ...normalTodayProjection,
            lanes: {
              ai_suggested_focus: [],
              degraded_sources: [],
              evidence_gaps: [],
              pending_approvals: [],
              priority: [],
              reconciliation_mismatches: [],
              stale_work: [],
            },
            projection_id: "today-empty",
            projection_state: "empty",
          },
        }),
      });

      renderOperatorRoute("/operator/today", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Today" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByText("No eligible AegisOps work is in the Today projection."),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Empty Today output is not production readiness, approval, execution, reconciliation, or closeout truth.",
        ),
      ).toBeInTheDocument();
    });

    it("rejects stale cache or malformed backend data instead of presenting it as current authority", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-today-view": {
            ...normalTodayProjection,
            stale_cache: true,
          },
        }),
      });

      renderOperatorRoute("/operator/today", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Today projection unavailable" }),
        ).toBeInTheDocument();
      });

      expect(screen.queryByText("Review case-101")).toBeNull();
      expect(
        screen.getByText(
          "The backend projection was stale or malformed, so the browser refused to present it as current workflow guidance.",
        ),
      ).toBeInTheDocument();
    });

    it.each([
      [
        "missing",
        () => {
          const payload: Record<string, unknown> = {
            ...normalTodayProjection,
          };
          delete payload.stale_cache;
          return payload;
        },
      ],
      [
        "non-boolean",
        () => ({
          ...normalTodayProjection,
          stale_cache: "false",
        }),
      ],
    ])(
      "rejects %s stale_cache contract values instead of presenting them as current authority",
      async (_caseName, buildProjection) => {
        const dependencies = createDefaultDependencies({
          fetchFn: createAuthorizedFetch({
            "/inspect-today-view": buildProjection(),
          }),
        });

        renderOperatorRoute("/operator/today", dependencies);

        await waitFor(() => {
          expect(
            screen.getByRole("heading", {
              name: "Today projection unavailable",
            }),
          ).toBeInTheDocument();
        });

        expect(screen.queryByText("Review case-101")).toBeNull();
        expect(
          screen.getByText(
            "The backend projection was stale or malformed, so the browser refused to present it as current workflow guidance.",
          ),
        ).toBeInTheDocument();
      },
    );

    it("fails closed when a Today projection reread errors after cached data exists", async () => {
      const user = userEvent.setup();
      let todayRequests = 0;
      const fetchFn = vi.fn<typeof fetch>().mockImplementation((input) => {
        const url = String(input);

        if (url.startsWith("/api/operator/session")) {
          return Promise.resolve(
            jsonResponse({
              identity: "analyst@example.com",
              provider: "authentik",
              roles: ["Analyst"],
              subject: "operator-7",
            }),
          );
        }

        if (url.startsWith("/inspect-today-view")) {
          todayRequests += 1;

          if (todayRequests === 1) {
            return Promise.resolve(jsonResponse(normalTodayProjection));
          }

          return Promise.reject(
            new Error("Today projection refresh unavailable."),
          );
        }

        if (url.startsWith("/diagnostics/readiness")) {
          return Promise.resolve(jsonResponse(createReadinessResponse()));
        }

        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      render(
        <MemoryRouter initialEntries={["/operator/today"]}>
          <TestRouteNavigator />
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Today" }),
        ).toBeInTheDocument();
      });
      expect(screen.getByText("Review case-101")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Readiness" }),
        ).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Go to Today" }));

      expect(
        await screen.findByRole("heading", {
          name: "Today projection unavailable",
        }),
      ).toBeInTheDocument();
      expect(screen.queryByText("Review case-101")).not.toBeInTheDocument();
    });
  });
}
