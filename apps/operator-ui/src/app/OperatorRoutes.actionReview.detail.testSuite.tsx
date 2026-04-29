import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionReviewDetailTests() {
  describe("action review detail routes", () => {
    it("renders the reviewed action-review detail route from backend-authoritative action review data", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-action-review": {
              action_request_id: "action-request-123",
              read_only: true,
              current_action_review: {
                action_request_id: "action-request-123",
                review_state: "approved",
              },
              action_review: {
                action_request_id: "action-request-123",
                review_state: "approved",
                approval_state: "approved",
                requester_identity: "analyst@example.com",
                recipient_identity: "repo-owner@example.com",
                next_expected_action: "await_execution_receipt",
                timeline: [
                  {
                    label: "Requested",
                    state: "completed",
                  },
                  {
                    label: "Approved",
                    state: "active",
                  },
                ],
              },
              case_record: {
                case_id: "case-456",
                lifecycle_state: "open",
              },
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

      renderOperatorRoute(
        "/operator/action-review/action-request-123",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getAllByText("action-request-123").length,
        ).toBeGreaterThan(0);
        expect(
          screen.getAllByText("await_execution_receipt").length,
        ).toBeGreaterThan(0);
        expect(screen.getByText("repo-owner@example.com")).toBeInTheDocument();
        expect(screen.getByText("Requested")).toBeInTheDocument();
        expect(screen.getByText("Approved")).toBeInTheDocument();
      });
      const approvalChip = screen
        .getAllByText("Approval: approved")
        .map((element) => element.closest(".MuiChip-root"))
        .find((element): element is HTMLElement => element !== null);
      expect(approvalChip).toHaveClass("MuiChip-colorSuccess");
      expect(
        screen.queryByText(
          /remains inspection-only until a separately reviewed slice/i,
        ),
      ).not.toBeInTheDocument();
    });

    it("renders recommendation, approval, and reconciliation advisory links from action review detail", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-action-review": {
              action_request_id: "action-request-321",
              read_only: true,
              current_action_review: {
                action_request_id: "action-request-321",
                review_state: "approved",
              },
              action_review: {
                action_request_id: "action-request-321",
                review_state: "approved",
                action_request_state: "approved",
                approval_state: "approved",
                recommendation_id: "recommendation-321",
                approval_decision_id: "approval-321",
                reconciliation_id: "recon-321",
                requester_identity: "analyst@example.com",
                recipient_identity: "repo-owner@example.com",
              },
              case_record: {
                case_id: "case-321",
                lifecycle_state: "open",
              },
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

      renderOperatorRoute(
        "/operator/action-review/action-request-321",
        dependencies,
      );

      expect(
        await screen.findByRole("link", {
          name: "Open recommendation advisory",
        }),
      ).toHaveAttribute(
        "href",
        "/operator/assistant/recommendation/recommendation-321",
      );
      expect(
        screen.getByRole("link", { name: "Open approval advisory" }),
      ).toHaveAttribute(
        "href",
        "/operator/assistant/approval_decision/approval-321",
      );
      expect(
        screen.getByRole("link", { name: "Open reconciliation advisory" }),
      ).toHaveAttribute("href", "/operator/assistant/reconciliation/recon-321");
    });

    it("renders execution receipt, reconciliation mismatch, and coordination visibility on action-review detail", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-action-review": {
              action_request_id: "action-request-789",
              read_only: true,
              current_action_review: {
                action_request_id: "action-request-789",
                review_state: "approved",
              },
              action_review: {
                action_request_id: "action-request-789",
                review_state: "approved",
                action_request_state: "approved",
                approval_state: "approved",
                action_execution_state: "succeeded",
                reconciliation_state: "mismatched",
                requester_identity: "analyst@example.com",
                recipient_identity: "repo-owner@example.com",
                next_expected_action: "review_reconciliation_mismatch",
                execution_surface_type: "automation_substrate",
                execution_surface_id: "shuffle",
                action_execution_id: "action-execution-789",
                delegation_id: "delegation-789",
                execution_run_id: "shuffle-run-789",
                reconciliation_id: "recon-789",
                target_scope: {
                  coordination_reference_id: "coord-ref-requested-789",
                  coordination_target_type: "ticket",
                  coordination_target_id: "ZM-REQ-789",
                },
                mismatch_inspection: {
                  reconciliation_id: "recon-789",
                  lifecycle_state: "mismatched",
                  ingest_disposition: "mismatch",
                  mismatch_summary:
                    "receipt payload disagrees with the reconciled ticket state",
                  execution_run_id: "shuffle-run-789",
                  linked_execution_run_ids: ["shuffle-run-789"],
                },
                reconciliation_detail: {
                  authority: "aegisops_reconciliation_record",
                  expected_aegisops_state: "matched",
                  authoritative_aegisops_state: "mismatched",
                  received_receipt: {
                    ingest_disposition: "mismatch",
                    execution_run_id: "shuffle-run-789",
                    linked_execution_run_ids: ["shuffle-run-789"],
                    correlation_key: "coord-ref-789",
                  },
                  closeout_evidence: {
                    reconciliation_id: "recon-789",
                    compared_at: "2026-04-27T09:00:00Z",
                    mismatch_summary:
                      "receipt payload disagrees with the reconciled ticket state",
                  },
                  action_required: true,
                  next_step: "review_mismatch_before_closeout",
                },
                coordination_ticket_outcome: {
                  authority: "authoritative_aegisops_review",
                  status: "mismatch",
                  summary:
                    "ticket receipt remains mismatched with the reviewed coordination target",
                  action_request_id: "action-request-789",
                  action_execution_id: "action-execution-789",
                  execution_run_id: "shuffle-run-789",
                  reconciliation_id: "recon-789",
                  coordination_reference_id: "coord-ref-789",
                  coordination_target_type: "zammad",
                  coordination_target_id: "ZM-789",
                  external_receipt_id: "receipt-789",
                  ticket_reference_url:
                    "https://tickets.example.invalid/tickets/ZM-789",
                  mismatch: {
                    mismatch_summary:
                      "ticket receipt remains mismatched with the reviewed coordination target",
                  },
                },
                timeline: [
                  {
                    label: "Requested",
                    state: "completed",
                  },
                  {
                    label: "Approved",
                    state: "approved",
                  },
                  {
                    label: "Delegated",
                    state: "delayed",
                  },
                  {
                    label: "Execution",
                    state: "succeeded",
                  },
                  {
                    label: "Reconciliation",
                    state: "mismatched",
                  },
                ],
              },
              case_record: {
                case_id: "case-789",
                lifecycle_state: "open",
              },
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

      renderOperatorRoute(
        "/operator/action-review/action-request-789",
        dependencies,
      );

      await waitFor(() => {
        expect(screen.getByText("Execution receipt")).toBeInTheDocument();
      });

      expect(
        screen.getByRole("heading", { name: "Action Review" }),
      ).toBeInTheDocument();
      expect(screen.getByText("Execution receipt")).toBeInTheDocument();
      expect(screen.getByText("Reconciliation visibility")).toBeInTheDocument();
      expect(screen.getByText("Coordination visibility")).toBeInTheDocument();
      expect(
        screen.getAllByText("action-execution-789").length,
      ).toBeGreaterThan(0);
      expect(screen.getAllByText("shuffle-run-789").length).toBeGreaterThan(0);
      expect(screen.getByText("Expected AegisOps state")).toBeInTheDocument();
      expect(screen.getAllByText("matched").length).toBeGreaterThan(0);
      expect(
        screen.getByText("Authoritative AegisOps state"),
      ).toBeInTheDocument();
      expect(screen.getAllByText("mismatched").length).toBeGreaterThan(0);
      expect(screen.getByText("Received receipt ingest")).toBeInTheDocument();
      expect(
        screen.getByText("review_mismatch_before_closeout"),
      ).toBeInTheDocument();
      expect(screen.getByText("Closeout compared at")).toBeInTheDocument();
      expect(screen.getByText("2026-04-27T09:00:00Z")).toBeInTheDocument();
      expect(
        screen.getAllByText(
          "receipt payload disagrees with the reconciled ticket state",
        ).length,
      ).toBeGreaterThan(0);
      expect(screen.getByText("delayed")).toBeInTheDocument();
      expect(screen.getByText("coord-ref-requested-789")).toBeInTheDocument();
      expect(screen.getByText("coord-ref-789")).toBeInTheDocument();
      expect(screen.getAllByText("receipt-789").length).toBeGreaterThan(0);
      expect(screen.getByText("ZM-REQ-789")).toBeInTheDocument();
      expect(screen.getByText("ZM-789")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Requested and observed coordination references do not match.",
        ),
      ).toBeInTheDocument();
    });

    it("keeps expired approval lifecycle state explicit without implying execution or reconciliation success", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-action-review": {
              action_request_id: "action-request-expired-789",
              read_only: true,
              current_action_review: {
                action_request_id: "action-request-expired-789",
                review_state: "expired",
              },
              action_review: {
                action_request_id: "action-request-expired-789",
                review_state: "expired",
                action_request_state: "expired",
                approval_state: "expired",
                requester_identity: "analyst@example.com",
                recipient_identity: "repo-owner@example.com",
                next_expected_action: "request_new_approval",
                requested_at: "2026-04-21T00:00:00Z",
                expires_at: "2026-04-21T12:00:00Z",
                timeline: [
                  {
                    label: "Requested",
                    state: "completed",
                  },
                  {
                    label: "Approval decision",
                    state: "expired",
                  },
                ],
              },
              case_record: {
                case_id: "case-expired-789",
                lifecycle_state: "open",
              },
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

      renderOperatorRoute(
        "/operator/action-review/action-request-expired-789",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            "Expired means the reviewed approval window no longer authorizes this request. Operators must reread authoritative state rather than infer continued validity.",
          ),
        ).toBeInTheDocument();
      });

      expect(screen.getAllByText("expired").length).toBeGreaterThan(0);
      expect(screen.getByText("Execution receipt")).toBeInTheDocument();
      expect(screen.getByText("Reconciliation visibility")).toBeInTheDocument();
      expect(
        screen.getByText(
          "No authoritative execution receipt is attached to this reviewed request yet.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "No authoritative reconciliation record is visible for this reviewed request yet.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          /Execution receipt visibility is present, but downstream reconciliation is still/i,
        ),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("Coordination visibility"),
      ).not.toBeInTheDocument();
    });
  });
}
