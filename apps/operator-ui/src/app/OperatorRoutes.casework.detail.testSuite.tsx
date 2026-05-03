import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  createDeferredResponse,
  renderOperatorRoute,
  createReadinessResponse,
  jsonResponse,
  TestRouteNavigator,
} from "./OperatorRoutes.testSupport";

function createCaseTimelineProjection(overrides: Record<string, unknown> = {}) {
  const segments = [
    ["wazuh_signal", "subordinate_context", "normal", "reconciliation", "recon-123"],
    ["aegisops_alert", "authoritative_aegisops_record", "normal", "alert", "alert-123"],
    ["evidence", "authoritative_aegisops_record", "degraded", "evidence", "evidence-123"],
    ["ai_summary", "subordinate_context", "missing", "ai_trace", null],
    ["recommendation", "subordinate_context", "normal", "recommendation", "rec-123"],
    ["action_request", "authoritative_aegisops_record", "normal", "action_request", "ar-123"],
    ["approval", "authoritative_aegisops_record", "normal", "approval_decision", "approval-123"],
    ["shuffle_receipt", "subordinate_context", "stale", "action_execution", "exec-123"],
    ["reconciliation", "authoritative_aegisops_record", "mismatch", "reconciliation", "recon-123"],
  ].map(([segment, authority_posture, state, record_family, record_id]) => ({
    authority_posture,
    backend_record_binding: {
      direct_binding_required: true,
      record_family,
      record_id,
    },
    incomplete_reason: state === "normal" ? null : `phase564_${state}`,
    operator_visible: true,
    projection_can_complete_segment: false,
    segment,
    state,
    truth_source: `aegisops_${record_family}_record`,
  }));

  return {
    authority_boundary:
      "Case timeline projection is derived display context only; AegisOps records remain authoritative.",
    case_id: "case-456",
    contract_version: "phase-56-3",
    inferred_linkage_allowed: false,
    projection_authority_allowed: false,
    segments,
    ...overrides,
  };
}

function createCaseDetailPayload(overrides: Record<string, unknown> = {}) {
  return {
    case_id: "case-456",
    case_record: {
      case_id: "case-456",
      lifecycle_state: "pending_action",
    },
    case_timeline_projection: createCaseTimelineProjection(),
    cross_source_timeline: [],
    linked_alert_ids: ["alert-123"],
    linked_alert_records: [],
    linked_evidence_ids: ["evidence-123"],
    linked_evidence_records: [],
    linked_lead_ids: [],
    linked_observation_ids: [],
    linked_recommendation_ids: [],
    linked_reconciliation_ids: ["recon-123"],
    linked_reconciliation_records: [],
    provenance_summary: {
      authoritative_anchor: {
        provenance_classification: "authoritative",
        record_family: "case",
        record_id: "case-456",
        source_family: "aegisops",
      },
    },
    ...overrides,
  };
}

export function registerOperatorRoutesCaseworkDetailTests() {
  describe("casework detail routes", () => {
    it("renders the reviewed case timeline chain in backend order with authority labels", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-case-detail": createCaseDetailPayload(),
        }),
      });

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      const timeline = screen.getByRole("table", {
        name: "Reviewed case timeline",
      });
      const rows = within(timeline).getAllByRole("row").slice(1);

      expect(rows.map((row) => within(row).getAllByRole("cell")[0]?.textContent)).toEqual([
        "Wazuh Signal",
        "Aegisops Alert",
        "Evidence",
        "Ai Summary",
        "Recommendation",
        "Action Request",
        "Approval",
        "Shuffle Receipt",
        "Reconciliation",
      ]);
      expect(within(rows[0] as HTMLElement).getByText("Subordinate Context")).toBeInTheDocument();
      expect(
        within(rows[1] as HTMLElement).getByText("Authoritative Aegisops Record"),
      ).toBeInTheDocument();
      expect(
        within(rows[7] as HTMLElement).getByText("Display cannot complete workflow truth"),
      ).toBeInTheDocument();
    });

    it("keeps missing, degraded, stale, mismatch, and unsupported timeline segments visible", async () => {
      const projection = createCaseTimelineProjection({
        segments: createCaseTimelineProjection().segments.map((segment: unknown, index) => {
          const record = segment as Record<string, unknown>;
          const states = ["missing", "degraded", "stale", "mismatch", "unsupported"];
          return {
            ...record,
            incomplete_reason: `phase564_${states[index % states.length]}`,
            state: states[index % states.length],
          };
        }),
      });
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-case-detail": createCaseDetailPayload({
            case_timeline_projection: projection,
          }),
        }),
      });

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      const timeline = await screen.findByRole("table", {
        name: "Reviewed case timeline",
      });

      for (const state of ["missing", "degraded", "stale", "mismatch", "unsupported"]) {
        expect(within(timeline).getAllByText(state).length).toBeGreaterThan(0);
        expect(within(timeline).getAllByText(`phase564_${state}`).length).toBeGreaterThan(0);
      }
      for (const staleState of within(timeline).getAllByText("stale")) {
        expect(staleState.closest(".MuiChip-root")).toHaveClass("MuiChip-colorWarning");
      }
      for (const unsupportedState of within(timeline).getAllByText("unsupported")) {
        expect(unsupportedState.closest(".MuiChip-root")).toHaveClass("MuiChip-colorError");
      }
      expect(screen.queryByText("Completed by timeline display")).not.toBeInTheDocument();
    });

    it.each([
      [
        "unsupported timeline contract version",
        createCaseTimelineProjection({ contract_version: "phase-56-4" }),
      ],
      [
        "cache-sourced timeline truth",
        createCaseTimelineProjection({ cache_sourced: true }),
      ],
      [
        "unsupported segment type",
        createCaseTimelineProjection({
          segments: createCaseTimelineProjection().segments.map(
            (segment: unknown, index) =>
              index === 0
                ? {
                    ...(segment as Record<string, unknown>),
                    segment: "browser_approval",
                  }
                : segment,
          ),
        }),
      ],
      [
        "wrong authority label",
        createCaseTimelineProjection({
          segments: createCaseTimelineProjection().segments.map(
            (segment: unknown, index) =>
              index === 0
                ? {
                    ...(segment as Record<string, unknown>),
                    authority_posture: "browser_truth",
                  }
                : segment,
          ),
        }),
      ],
      [
        "display state as completion truth",
        createCaseTimelineProjection({
          segments: createCaseTimelineProjection().segments.map(
            (segment: unknown, index) =>
              index === 0
                ? {
                    ...(segment as Record<string, unknown>),
                    projection_can_complete_segment: true,
                  }
                : segment,
          ),
        }),
      ],
    ])("fails closed on %s", async (_label, caseTimelineProjection) => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-case-detail": createCaseDetailPayload({
            case_timeline_projection: caseTimelineProjection,
          }),
        }),
      });

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      expect(
        await screen.findByText(
          "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("table", { name: "Reviewed case timeline" }),
      ).not.toBeInTheDocument();
    });

    it("renders alert detail with authoritative and subordinate sections separated", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-alert-detail": {
            alert_id: "alert-123",
            alert: {
              alert_id: "alert-123",
              lifecycle_state: "triaged",
            },
            case_record: {
              case_id: "case-456",
            },
            review_state: "triaged",
            escalation_boundary: "case_optional",
            provenance: {
              admission_kind: "live",
              admission_channel: "live_wazuh_webhook",
            },
            lineage: {
              finding_id: "finding-123",
              analytic_signal_id: "signal-123",
              source_systems: ["wazuh"],
              substrate_detection_record_ids: ["wazuh:1731595300.1234567"],
              accountable_source_identities: ["manager:wazuh-manager-github-1"],
              evidence_ids: ["evidence-123"],
              reconciliation_id: "recon-123",
            },
            latest_reconciliation: {
              reconciliation_id: "recon-123",
            },
            linked_evidence_records: [
              {
                evidence_id: "evidence-123",
                source_system: "wazuh",
                derivation_relationship: "native_detection_record",
              },
            ],
          },
        }),
      });

      renderOperatorRoute("/operator/alerts/alert-123", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Alert Detail" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getAllByText("Authoritative anchor").length,
        ).toBeGreaterThan(0);
        expect(
          screen.getAllByText("Subordinate evidence context").length,
        ).toBeGreaterThan(0);
        expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
        expect(screen.getByText("recon-123")).toBeInTheDocument();
      });
    });

    it("reuses last verified alert detail during refetch and keeps transient refresh failures explicit", async () => {
      const user = userEvent.setup();
      const deferredAlertRefresh = createDeferredResponse();
      let alertDetailRequests = 0;
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

        if (url.startsWith("/inspect-alert-detail")) {
          alertDetailRequests += 1;

          if (alertDetailRequests === 1) {
            return Promise.resolve(
              jsonResponse({
                alert_id: "alert-123",
                alert: {
                  alert_id: "alert-123",
                  lifecycle_state: "triaged",
                },
                review_state: "triaged",
                provenance: {
                  admission_channel: "live_wazuh_webhook",
                },
                linked_evidence_records: [],
              }),
            );
          }

          return deferredAlertRefresh.promise;
        }

        if (url.startsWith("/diagnostics/readiness")) {
          return Promise.resolve(jsonResponse(createReadinessResponse()));
        }

        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      render(
        <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
          <TestRouteNavigator />
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Alert Detail" }),
        ).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Readiness" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", { name: "Go to alert detail" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Alert Detail" }),
        ).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
      expect(
        screen.queryByLabelText("Loading alert detail"),
      ).not.toBeInTheDocument();

      deferredAlertRefresh.reject(
        new Error("Alert detail refresh unavailable."),
      );

      expect(
        await screen.findByText((content) =>
          content.includes(
            "Showing the last verified operator data while refresh is unavailable.",
          ),
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText((content) =>
          content.includes("Alert detail refresh unavailable."),
        ),
      ).toBeInTheDocument();
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
    });

    it("fails closed on malformed alert-detail refetch instead of rendering cached data as current", async () => {
      const user = userEvent.setup();
      let alertDetailRequests = 0;
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

        if (url.startsWith("/inspect-alert-detail")) {
          alertDetailRequests += 1;

          if (alertDetailRequests === 1) {
            return Promise.resolve(
              jsonResponse({
                alert_id: "alert-123",
                alert: {
                  alert_id: "alert-123",
                  lifecycle_state: "triaged",
                },
                review_state: "triaged",
                provenance: {
                  admission_channel: "live_wazuh_webhook",
                },
                linked_evidence_records: [],
              }),
            );
          }

          return Promise.resolve(
            new Response("{", {
              headers: {
                "Content-Type": "application/json",
              },
              status: 200,
            }),
          );
        }

        if (url.startsWith("/diagnostics/readiness")) {
          return Promise.resolve(jsonResponse(createReadinessResponse()));
        }

        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      render(
        <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
          <TestRouteNavigator />
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Alert Detail" }),
        ).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Readiness" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", { name: "Go to alert detail" }),
      );

      expect(
        await screen.findByText(
          "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByText("live_wazuh_webhook")).not.toBeInTheDocument();
    });
  });
}
