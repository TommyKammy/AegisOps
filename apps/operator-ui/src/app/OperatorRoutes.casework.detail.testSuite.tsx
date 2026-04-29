import { render, screen, waitFor } from "@testing-library/react";
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

export function registerOperatorRoutesCaseworkDetailTests() {
  describe("casework detail routes", () => {
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
