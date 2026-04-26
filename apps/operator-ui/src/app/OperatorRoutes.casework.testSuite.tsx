import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  createDeferredResponse,
  createReadinessResponse,
  jsonResponse,
  TestRouteNavigator,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesCaseworkTests() {
  describe("casework routes", () => {
    it("records reviewed route views in the bounded UI event log", async () => {
      const user = userEvent.setup();
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-alert-detail": {
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
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
          <TestRouteNavigator />
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
      });

      expect(
        screen.getByRole("heading", { name: "Reviewed UI event log" }),
      ).toBeInTheDocument();
      expect(screen.getByText("Route: /operator/alerts/alert-123")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Readiness" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("Route: /operator/readiness")).toBeInTheDocument();
      });
    });

    it("renders the reviewed queue route from backend-authoritative queue records", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-analyst-queue": {
          queue_name: "analyst_review",
          read_only: true,
          records: [
            {
              alert_id: "alert-123",
              review_state: "degraded",
              case_id: "case-456",
              case_lifecycle_state: "open",
              owner: "analyst-review-001",
              age_seconds: 3600,
              age_bucket: "fresh",
              severity: "high",
              last_activity_at: "2026-04-26T22:16:17Z",
              next_action: "Review the queue projection before any approval-bound response.",
              accountable_source_identities: [
                "manager:wazuh-manager-github-1",
              ],
              reviewed_context: {
                source: {
                  source_family: "github_audit",
                },
              },
              current_action_review: {
                review_state: "pending",
                next_expected_action: "await_approver_decision",
              },
            },
          ],
          total_records: 1,
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/queue"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Analyst Queue" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("alert-123")).toBeInTheDocument();
        expect(screen.getAllByText(/Review: degraded/i).length).toBeGreaterThan(0);
        expect(screen.getByText("analyst-review-001")).toBeInTheDocument();
        expect(screen.getByText("fresh")).toBeInTheDocument();
        expect(screen.getByText("high")).toBeInTheDocument();
        expect(screen.getByText("2026-04-26T22:16:17Z")).toBeInTheDocument();
        expect(
          screen.getAllByText("Review the queue projection before any approval-bound response.")
            .length,
        ).toBeGreaterThan(0);
        expect(
          screen.getByText(/Primary review surface/i),
        ).toBeInTheDocument();
        expect(screen.getByText("github_audit")).toBeInTheDocument();
      });
    });

    it("keeps degraded and missing-anchor queue warnings explicit", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-analyst-queue": {
          queue_name: "analyst_review",
          read_only: true,
          records: [
            {
              alert_id: "alert-789",
              review_state: "degraded",
              case_lifecycle_state: "open",
              external_ticket_reference: {
                status: "missing_anchor",
              },
              reviewed_context: {
                source: {
                  source_family: "microsoft_365_audit",
                },
              },
            },
          ],
          total_records: 1,
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/queue"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Analyst Queue" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("alert-789")).toBeInTheDocument();
        expect(screen.getByText("No case anchor")).toBeInTheDocument();
        expect(
          screen.getByText("Review state remains degraded."),
        ).toBeInTheDocument();
        expect(
          screen.getByText(
            "Non-authoritative coordination reference is missing_anchor.",
          ),
        ).toBeInTheDocument();
        expect(
          screen.getByText(
            "Case lifecycle state is present without an authoritative case identifier.",
          ),
        ).toBeInTheDocument();
      });
    });

    it("renders mismatch, stale receipt, degraded extension, action-required, and clean queue lanes", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-analyst-queue": {
          queue_name: "analyst_review",
          read_only: true,
          lane_counts: {
            action_required: 1,
            reconciliation_mismatch: 1,
            stale_receipt: 1,
            optional_extension_degraded: 1,
            clean: 1,
          },
          records: [
            {
              alert_id: "alert-lanes-mismatch",
              review_state: "new",
              queue_lanes: [
                "action_required",
                "reconciliation_mismatch",
                "stale_receipt",
                "optional_extension_degraded",
              ],
              queue_lane_details: {
                reconciliation_mismatch: {
                  state: "mismatched",
                  summary: "stale downstream execution observation requires refresh",
                },
                stale_receipt: {
                  state: "stale",
                  summary: "stale downstream execution observation requires refresh",
                },
                optional_extension_degraded: {
                  endpoint_evidence: {
                    readiness: "degraded",
                    reason: "receipt_lag_requires_review",
                  },
                },
              },
            },
            {
              alert_id: "alert-lanes-clean",
              review_state: "triaged",
              queue_lanes: ["clean"],
            },
          ],
          total_records: 2,
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/queue"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Queue lanes" })).toBeInTheDocument();
      });

      expect(screen.getByText("Action required: 1")).toBeInTheDocument();
      expect(screen.getByText("Reconciliation mismatch: 1")).toBeInTheDocument();
      expect(screen.getByText("Stale receipt: 1")).toBeInTheDocument();
      expect(screen.getByText("Optional extension degraded: 1")).toBeInTheDocument();
      expect(screen.getByText("Clean: 1")).toBeInTheDocument();
      expect(screen.getByText("alert-lanes-mismatch")).toBeInTheDocument();
      expect(screen.getAllByText("Reconciliation mismatch").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Stale receipt").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Optional extension degraded").length).toBeGreaterThan(0);
      expect(
        screen.getAllByText("stale downstream execution observation requires refresh").length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText("endpoint evidence: receipt lag requires review").length,
      ).toBeGreaterThan(0);
      expect(screen.getByText("alert-lanes-clean")).toBeInTheDocument();
      expect(screen.getAllByText("Clean").length).toBeGreaterThan(0);
    });

    it("renders grouped AI trace review states in the analyst queue", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-analyst-queue": {
          queue_name: "analyst_review",
          read_only: true,
          records: [
            {
              alert_id: "alert-123",
              review_state: "degraded",
              case_id: "case-456",
              case_lifecycle_state: "open",
              ai_trace_review_groups: [
                {
                  alert_id: "alert-123",
                  case_id: "case-456",
                  trace_count: 1,
                  states: [
                    "conflict",
                    "citation_failure",
                    "provider_degraded",
                    "unresolved",
                  ],
                  trace_link: "/operator/assistant/ai_trace/ai-trace-queue-unresolved-001",
                  traces: [
                    {
                      ai_trace_id: "ai-trace-queue-unresolved-001",
                      lifecycle_state: "under_review",
                      draft_status: "unresolved",
                      provider_status: "failed",
                      provider_operational_quality: "degraded",
                      unresolved_reasons: [
                        "provider_generation_failed",
                        "missing_supporting_citations",
                        "conflicting_reviewed_context",
                      ],
                    },
                  ],
                },
              ],
              reviewed_context: {
                source: {
                  source_family: "github_audit",
                },
              },
            },
          ],
          total_records: 1,
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/queue"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(
        await screen.findByRole("heading", { name: "AI Trace review queue" }),
      ).toBeInTheDocument();
      expect(screen.getByText("Provider degraded")).toBeInTheDocument();
      expect(screen.getByText("Citation failure")).toBeInTheDocument();
      expect(screen.getByText("Conflict")).toBeInTheDocument();
      expect(screen.getByText("Unresolved")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "Open AI trace review" }),
      ).toHaveAttribute(
        "href",
        "/operator/assistant/ai_trace/ai-trace-queue-unresolved-001",
      );
      expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
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

      render(
        <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getAllByText("Authoritative anchor").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Subordinate evidence context").length).toBeGreaterThan(0);
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
        expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));
      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Readiness" })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Go to alert detail" }));

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
      expect(screen.queryByLabelText("Loading alert detail")).not.toBeInTheDocument();

      deferredAlertRefresh.reject(new Error("Alert detail refresh unavailable."));

      expect(
        await screen.findByText((content) =>
          content.includes("Showing the last verified operator data while refresh is unavailable."),
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText((content) => content.includes("Alert detail refresh unavailable.")),
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
        expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
      });
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Go to readiness" }));
      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Readiness" })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Go to alert detail" }));

      expect(
        await screen.findByText(
          "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByText("live_wazuh_webhook")).not.toBeInTheDocument();
    });
  });
}
