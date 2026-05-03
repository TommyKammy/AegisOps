import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

const normalBusinessHoursHandoff = {
  authority_boundary:
    "Business-hours handoff display is coordination guidance only; AegisOps records remain authoritative for lifecycle, approval, execution, reconciliation, evidence, audit, and closeout truth.",
  business_hours_handoff_contract_version: "phase-56-6",
  handoff_id: "handoff-2026-05-04",
  handoff_state: "blocked",
  items: [
    {
      ai_summary_handling: {
        advisory_only: true,
        posture: "accepted_for_reference",
        summary_id: "ai-trace-accepted-101",
      },
      backend_record_binding: {
        direct_binding_required: true,
        record_family: "case",
        record_id: "case-101",
      },
      blocked_owner: "analyst-001",
      changed_work: "Case promoted and evidence review started.",
      evidence_gaps: ["Missing endpoint custody record."],
      follow_up: "Collect endpoint custody evidence before approval review.",
      item_id: "handoff-item-101",
      state: "unresolved",
      title: "Continue investigation for case-101",
    },
    {
      ai_summary_handling: {
        advisory_only: true,
        posture: "rejected_for_reference",
        summary_id: "ai-trace-rejected-202",
      },
      backend_record_binding: {
        direct_binding_required: true,
        record_family: "action_request",
        record_id: "action-request-202",
      },
      blocked_owner: "approver-002",
      changed_work: "Containment request failed after approved execution path.",
      evidence_gaps: ["Missing failed execution receipt."],
      follow_up: "Re-review scope before retry or manual fallback.",
      item_id: "handoff-item-202",
      state: "failed",
      title: "Failed containment needs owner follow-up",
    },
  ],
  projection_authority_allowed: false,
  read_only: true,
  stale_cache: false,
};

export function registerOperatorRoutesBusinessHoursHandoffTests() {
  describe("business-hours handoff route", () => {
    it("renders unresolved and failed handoff items with explicit owners, evidence gaps, and advisory AI handling", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-business-hours-handoff": normalBusinessHoursHandoff,
        }),
      });

      renderOperatorRoute("/operator/handoff", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Business-hours handoff" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByText("Continue investigation for case-101")).toBeInTheDocument();
      expect(
        screen.getByText("Failed containment needs owner follow-up"),
      ).toBeInTheDocument();
      expect(screen.getByText("Owner: analyst-001")).toBeInTheDocument();
      expect(screen.getByText("Owner: approver-002")).toBeInTheDocument();
      expect(screen.getByText("Missing endpoint custody record.")).toBeInTheDocument();
      expect(screen.getByText("Missing failed execution receipt.")).toBeInTheDocument();
      expect(screen.getByText("AI accepted for reference")).toBeInTheDocument();
      expect(screen.getByText("AI rejected for reference")).toBeInTheDocument();
      expect(screen.getAllByText("Advisory only").length).toBeGreaterThan(0);
      expect(screen.getAllByText("State remains open").length).toBeGreaterThan(0);
      expect(
        screen.getByText(
          "Handoff copy cannot close cases, approve actions, execute work, reconcile outcomes, satisfy audit evidence, or override backend records.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /close case/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /approve/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /execute/i })).toBeNull();
    });

    it("fails closed on stale cache-only handoff state", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-business-hours-handoff": {
            ...normalBusinessHoursHandoff,
            stale_cache: true,
          },
        }),
      });

      renderOperatorRoute("/operator/handoff", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", {
            name: "Business-hours handoff unavailable",
          }),
        ).toBeInTheDocument();
      });

      expect(screen.queryByText("Continue investigation for case-101")).toBeNull();
      expect(
        screen.getByText(
          "The backend handoff projection was stale or malformed, so the browser refused to present it as current handoff guidance.",
        ),
      ).toBeInTheDocument();
    });
  });
}
