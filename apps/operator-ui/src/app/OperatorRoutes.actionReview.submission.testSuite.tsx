import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  jsonResponse,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionReviewSubmissionTests() {
  describe("action review submission routes", () => {
    it("submits a reviewed approval decision and waits for the authoritative reread before rendering the approved lifecycle", async () => {
      const user = userEvent.setup();
      let actionReviewPayload: Record<string, unknown> = {
        action_request_id: "action-request-123",
        read_only: true,
        current_action_review: {
          action_request_id: "action-request-123",
          review_state: "pending",
        },
        action_review: {
          action_request_id: "action-request-123",
          review_state: "pending",
          action_request_state: "pending_approval",
          approval_state: "pending",
          requester_identity: "analyst@example.com",
          recipient_identity: "repo-owner@example.com",
          approver_identities: [],
          decision_rationale: null,
          requested_at: "2026-04-22T00:00:00Z",
          expires_at: "2026-04-23T00:00:00Z",
          next_expected_action: "await_approver_decision",
          timeline: [
            {
              label: "Requested",
              state: "completed",
            },
            {
              label: "Approval decision",
              state: "pending",
            },
          ],
        },
        case_record: {
          case_id: "case-456",
          lifecycle_state: "pending_action",
        },
      };

      const fetchFn = vi
        .fn<typeof fetch>()
        .mockImplementation((input, init) => {
          const url = String(input);

          if (url.startsWith("/api/operator/session")) {
            return Promise.resolve(
              jsonResponse({
                identity: "approver@example.com",
                provider: "authentik",
                roles: ["Approver"],
                subject: "operator-8",
              }),
            );
          }

          if (url.startsWith("/inspect-action-review")) {
            return Promise.resolve(jsonResponse(actionReviewPayload));
          }

          if (url.startsWith("/operator/record-action-approval-decision")) {
            expect(init?.method).toBe("POST");
            expect(init?.body).toBe(
              JSON.stringify({
                action_request_id: "action-request-123",
                approver_identity: "approver@example.com",
                decided_at: "2026-04-22T09:45",
                decision: "grant",
                decision_rationale:
                  "The reviewed owner notification stays within the approved notify boundary.",
              }),
            );
            actionReviewPayload = {
              ...actionReviewPayload,
              current_action_review: {
                action_request_id: "action-request-123",
                review_state: "approved",
              },
              action_review: {
                ...(actionReviewPayload.action_review as Record<
                  string,
                  unknown
                >),
                review_state: "approved",
                action_request_state: "approved",
                approval_decision_id: "approval-decision-123",
                approval_state: "approved",
                approver_identities: ["approver@example.com"],
                decision_rationale:
                  "The reviewed owner notification stays within the approved notify boundary.",
                next_expected_action: "await_execution_receipt",
                timeline: [
                  {
                    label: "Requested",
                    state: "completed",
                  },
                  {
                    label: "Approval decision",
                    state: "approved",
                    details: {
                      decision_rationale:
                        "The reviewed owner notification stays within the approved notify boundary.",
                    },
                  },
                ],
              },
            };
            return Promise.resolve(
              jsonResponse({
                action_request_id: "action-request-123",
                approval_decision_id: "approval-decision-123",
                lifecycle_state: "approved",
              }),
            );
          }

          return Promise.reject(new Error(`Unexpected fetch: ${url}`));
        });
      const dependencies = createDefaultDependencies({ fetchFn });

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
          screen.getByRole("heading", { name: "Record approval decision" }),
        ).toBeInTheDocument();
        expect(screen.getAllByText("pending_approval").length).toBeGreaterThan(
          0,
        );
      });

      const approvalDecisionSection = screen.getByRole("heading", {
        name: "Record approval decision",
      });
      const approvalDecisionCard =
        approvalDecisionSection.closest(".MuiCard-root");
      expect(approvalDecisionCard).not.toBeNull();

      fireEvent.change(
        within(approvalDecisionCard as HTMLElement).getByRole("textbox", {
          name: "Decided at",
        }),
        { target: { value: "2026-04-22T09:45" } },
      );
      fireEvent.change(
        within(approvalDecisionCard as HTMLElement).getByRole("textbox", {
          name: "Decision rationale",
        }),
        {
          target: {
            value:
              "The reviewed owner notification stays within the approved notify boundary.",
          },
        },
      );
      fireEvent.click(
        within(approvalDecisionCard as HTMLElement).getByRole("checkbox"),
      );
      fireEvent.click(
        within(approvalDecisionCard as HTMLElement).getByRole("button", {
          name: "Record approval decision",
        }),
      );

      await waitFor(() => {
        expect(fetchFn).toHaveBeenCalledWith(
          "/operator/record-action-approval-decision",
          expect.objectContaining({
            method: "POST",
          }),
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            "Authoritative refresh completed from the reviewed backend record. Refreshed: Action review detail.",
          ),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getAllByText("await_execution_receipt").length,
        ).toBeGreaterThan(0);
        expect(
          screen.getAllByText("approver@example.com").length,
        ).toBeGreaterThan(0);
        expect(
          screen.getAllByText(
            "The reviewed owner notification stays within the approved notify boundary.",
          ).length,
        ).toBeGreaterThan(0);
      });
    });

    it("keeps approval submission blocked when the backend has not confirmed the current authoritative review", async () => {
      const fetchFn = createAuthorizedFetch(
        {
          "/inspect-action-review": {
            action_request_id: "action-request-123",
            read_only: true,
            current_action_review: {
              review_state: "pending",
            },
            action_review: {
              action_request_id: "action-request-123",
              review_state: "pending",
              action_request_state: "pending_approval",
              approval_state: "pending",
              requester_identity: "analyst@example.com",
              recipient_identity: "repo-owner@example.com",
              approver_identities: [],
              requested_at: "2026-04-22T00:00:00Z",
              expires_at: "2026-04-23T00:00:00Z",
              next_expected_action: "await_approver_decision",
              timeline: [
                {
                  label: "Requested",
                  state: "completed",
                },
                {
                  label: "Approval decision",
                  state: "pending",
                },
              ],
            },
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

      renderOperatorRoute(
        "/operator/action-review/action-request-123",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByText(
            "Approval submission stays blocked because this record is no longer the current authoritative review for the selected scope.",
          ),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("heading", { name: "Record approval decision" }),
      ).not.toBeInTheDocument();
    });
  });
}
