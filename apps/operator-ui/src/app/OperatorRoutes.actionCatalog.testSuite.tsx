import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionCatalogTests() {
  describe("action catalog routes", () => {
    it("renders reviewed action catalog posture from backend action records", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-records": {
              read_only: true,
              records: [
                {
                  action_request_id: "action-request-failed-001",
                  action_type: "enrichment_only_lookup",
                  catalog_action: "enrichment_only_lookup",
                  action_request_state: "approved",
                  approval_state: "policy_not_required",
                  action_execution_state: "failed",
                  reconciliation_state: "missing_reconciliation",
                  fallback_state: "not_recorded",
                  receipt_state: "missing_receipt",
                  requested_at: "2026-05-18T01:03:00Z",
                },
                {
                  action_request_id: "action-request-normal-001",
                  action_type: "operator_notification",
                  catalog_action: "operator_notification",
                  action_request_state: "approved",
                  approval_state: "policy_not_required",
                  action_execution_state: "succeeded",
                  reconciliation_state: "matched",
                  fallback_state: "not_required",
                  receipt_state: "present",
                  simulation_mode: "production",
                  requested_at: "2026-05-18T01:00:00Z",
                },
                {
                  action_request_id: "action-request-fallback-001",
                  action_type: "manual_escalation_request",
                  catalog_action: "manual_escalation_request",
                  action_request_state: "expired",
                  approval_state: "expired",
                  action_execution_state: "pending",
                  reconciliation_state: "stale_receipt",
                  fallback_state: "fallback_required",
                  receipt_state: "stale_receipt",
                  demo_test_label: "demo",
                  requested_at: "2026-05-18T01:02:00Z",
                },
                {
                  action_request_id: "action-request-mismatched-001",
                  action_type: "create_tracking_ticket",
                  catalog_action: "create_tracking_ticket",
                  action_request_state: "rejected",
                  approval_state: "rejected",
                  action_execution_state: "rejected",
                  reconciliation_state: "mismatched",
                  fallback_state: "manual_review",
                  receipt_state: "mismatched_receipt",
                  requested_at: "2026-05-18T01:01:00Z",
                },
              ],
              total_records: 4,
            },
          },
          {
            identity: "approver@example.com",
            provider: "authentik",
            roles: ["Approver"],
            subject: "operator-8",
          },
        ),
      });

      renderOperatorRoute("/operator/actions", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Catalog" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByText("operator_notification")).toBeInTheDocument();
      expect(
        screen.getAllByText("Policy: policy_not_required").length,
      ).toBeGreaterThan(0);
      expect(screen.getAllByText("Request: approved").length).toBeGreaterThan(0);
      expect(screen.getByText("Receipt: present")).toBeInTheDocument();
      expect(screen.getByText("Reconciliation: matched")).toBeInTheDocument();
      expect(screen.getAllByText("Request: rejected").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Approval: rejected").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Request: expired").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Execution: failed").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Fallback: fallback_required").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Receipt: missing_receipt").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Receipt: stale_receipt").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Receipt: mismatched_receipt").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Simulator: demo").length).toBeGreaterThan(0);
      expect(
        screen.getAllByText(/backend AegisOps records remain authoritative/i).length,
      ).toBeGreaterThan(0);
      expect(screen.queryByRole("button", { name: /execute/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /approve/i })).toBeNull();

    });

    it("keeps unavailable automation posture visible when no backend request record exists", async () => {
      const fetchFn = createAuthorizedFetch(
        {
          "/inspect-records": {
            read_only: true,
            records: [],
            total_records: 0,
          },
        },
        {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        },
      );
      const dependencies = createDefaultDependencies({ fetchFn });

      renderOperatorRoute("/operator/automations", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Catalog" }),
        ).toBeInTheDocument();
      });

      expect(screen.getAllByText("Request: unavailable").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Receipt: unavailable").length).toBeGreaterThan(0);
      expect(
        screen.getAllByText(
          "No backend-reviewed action request is currently visible for this catalog entry.",
        ).length,
      ).toBeGreaterThan(0);

      const recordCall = fetchFn.mock.calls.find(([url]) =>
        String(url).startsWith("/inspect-records"),
      );
      expect(recordCall).toBeDefined();
      const parsedUrl = new URL(String(recordCall![0]), "http://operator-ui.local");
      expect(parsedUrl.searchParams.get("family")).toBe("action_request");
    });
  });
}
