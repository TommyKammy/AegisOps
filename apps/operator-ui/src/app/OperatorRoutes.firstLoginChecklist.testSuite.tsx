import { screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesFirstLoginChecklistTests() {
  describe("first-login checklist route", () => {
    it("renders the Phase 55 checklist sequence from backend-owned records", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "runtime_readiness",
                authority_record_id: "ready",
              },
              {
                step_key: "seeded_queue",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "queue",
                authority_record_id: "demo-queue-1",
              },
              {
                step_key: "sample_wazuh_alert",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "alert",
                authority_record_id: "alert-wazuh-1",
              },
              {
                step_key: "promote_to_case",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "case",
                authority_record_id: "case-1",
              },
              {
                step_key: "evidence",
                state: "degraded",
                authority_source: "backend_authoritative_record",
                authority_record_family: "evidence",
                authority_record_id: "evidence-1",
              },
              {
                step_key: "ai_summary",
                state: "skipped",
                authority_source: "backend_authoritative_record",
                authority_record_family: "assistant_advisory",
                authority_record_id: "advisory-1",
              },
              {
                step_key: "action_request",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "action_request",
                authority_record_id: "action-request-1",
              },
              {
                step_key: "approval_decision",
                state: "blocked",
                authority_source: "backend_authoritative_record",
                authority_record_family: "action_review",
                authority_record_id: "review-1",
              },
              {
                step_key: "shuffle_receipt",
                state: "unavailable",
                authority_source: "backend_authoritative_record",
                authority_record_family: "execution_receipt",
                authority_record_id: "receipt-1",
              },
              {
                step_key: "reconciliation",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "reconciliation",
                authority_record_id: "recon-1",
              },
              {
                step_key: "report_export",
                state: "skipped",
                authority_source: "backend_authoritative_record",
                authority_record_family: "report_export",
                authority_record_id: "report-1",
              },
            ],
            total_records: 11,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "First-Login Checklist" }),
        ).toBeInTheDocument();
      });

      const checklist = screen.getByRole("list", {
        name: "Phase 55 first-login checklist",
      });
      const rows = within(checklist).getAllByRole("listitem");
      expect(rows).toHaveLength(11);
      expect(rows.map((row) => within(row).getByTestId("step-title").textContent)).toEqual([
        "Stack health",
        "Seeded queue",
        "Sample Wazuh-origin alert",
        "Promote to case",
        "Evidence",
        "AI summary",
        "Action request",
        "Approval or rejection",
        "Shuffle execution receipt",
        "Reconciliation",
        "Report export",
      ]);
      expect(
        within(rows[4]).getByText("State: degraded"),
      ).toBeInTheDocument();
      expect(within(rows[5]).getByText("State: skipped")).toBeInTheDocument();
      expect(within(rows[7]).getByText("State: blocked")).toBeInTheDocument();
      expect(
        within(rows[8]).getByText("State: unavailable"),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Checklist progress is derived from backend records only; browser state, UI cache, Wazuh state, Shuffle state, AI output, tickets, verifier output, and issue-lint output remain subordinate context.",
        ),
      ).toBeInTheDocument();
    });

    it("fails closed when checklist completion comes from browser cache", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "browser_cache",
                authority_record_family: "runtime_readiness",
                authority_record_id: "ready",
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Checklist state from browser_cache is not trusted workflow truth.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("State: completed")).not.toBeInTheDocument();
    });

    it("fails closed when a checklist step is bound to the wrong backend record family", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "case",
                authority_record_id: "case-1",
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Checklist step stack_health is bound to case, expected runtime_readiness.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("State: completed")).not.toBeInTheDocument();
    });
  });
}
