import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import { createAuthorizedFetch, jsonResponse } from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionReviewTests() {
  describe("action review routes", () => {
    it("shows an explicit forbidden outcome for analyst-only action-review landing routes", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator/action-review"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Access denied" })).toBeInTheDocument();
    });
    });

    it("allows analyst deep links into reviewed action-review detail as read-only inspection", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-action-review": {
          action_request_id: "action-request-123",
          read_only: true,
          current_action_review: {
            action_request_id: "action-request-123",
            review_state: "pending",
          },
          action_review: {
            action_request_id: "action-request-123",
            review_state: "pending",
            approval_state: "pending",
            requester_identity: "analyst@example.com",
            recipient_identity: "repo-owner@example.com",
            next_expected_action: "await_approver_decision",
          },
          case_record: {
            case_id: "case-456",
            lifecycle_state: "pending_action",
          },
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/action-review/action-request-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "The current reviewed session can inspect this record but cannot submit approval decisions without approver role authority.",
      ),
    ).toBeInTheDocument();
    });

    it("honors allowed-role extensions for reviewed action-review detail routes", async () => {
      const dependencies = createDefaultDependencies({
        config: {
          allowedRoles: [
            "analyst",
            "approver",
            "platform_admin",
            "security-auditor",
          ],
          basePath: "/reviewed-operator",
        },
        fetchFn: createAuthorizedFetch(
          {
            "/inspect-action-review": {
              action_request_id: "action-request-123",
              read_only: true,
              current_action_review: {
                action_request_id: "action-request-123",
                review_state: "pending",
              },
              action_review: {
                action_request_id: "action-request-123",
                review_state: "pending",
                approval_state: "pending",
                requester_identity: "analyst@example.com",
                recipient_identity: "repo-owner@example.com",
                next_expected_action: "await_approver_decision",
              },
              case_record: {
                case_id: "case-456",
                lifecycle_state: "pending_action",
              },
            },
          },
          {
            identity: "security.auditor@example.com",
            provider: "authentik",
            roles: ["Security-Auditor"],
            subject: "operator-42",
          },
        ),
      });

      render(
        <MemoryRouter
          initialEntries={["/reviewed-operator/action-review/action-request-123"]}
        >
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      });

      expect(screen.queryByRole("heading", { name: "Access denied" })).not.toBeInTheDocument();
      expect(
        screen.getByText(
          "The current reviewed session can inspect this record but cannot submit approval decisions without approver role authority.",
        ),
      ).toBeInTheDocument();
    });

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

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getAllByText("action-request-123").length).toBeGreaterThan(0);
        expect(screen.getAllByText("await_execution_receipt").length).toBeGreaterThan(0);
        expect(screen.getByText("repo-owner@example.com")).toBeInTheDocument();
        expect(screen.getByText("Requested")).toBeInTheDocument();
        expect(screen.getByText("Approved")).toBeInTheDocument();
      });
      const approvalChip = screen
        .getAllByText("Approval: approved")
        .map((element) => element.closest(".MuiChip-root"))
        .find((element): element is HTMLElement => element !== null);
      expect(approvalChip).toHaveClass("MuiChip-colorSuccess");
      expect(screen.queryByText(/remains inspection-only until a separately reviewed slice/i)).not.toBeInTheDocument();
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

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-321"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(
        await screen.findByRole("link", { name: "Open recommendation advisory" }),
      ).toHaveAttribute("href", "/operator/assistant/recommendation/recommendation-321");
      expect(
        screen.getByRole("link", { name: "Open approval advisory" }),
      ).toHaveAttribute("href", "/operator/assistant/approval_decision/approval-321");
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
                  mismatch_summary: "receipt payload disagrees with the reconciled ticket state",
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
                  summary: "ticket receipt remains mismatched with the reviewed coordination target",
                  action_request_id: "action-request-789",
                  action_execution_id: "action-execution-789",
                  execution_run_id: "shuffle-run-789",
                  reconciliation_id: "recon-789",
                  coordination_reference_id: "coord-ref-789",
                  coordination_target_type: "zammad",
                  coordination_target_id: "ZM-789",
                  external_receipt_id: "receipt-789",
                  ticket_reference_url: "https://tickets.example.invalid/tickets/ZM-789",
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

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-789"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByText("Execution receipt")).toBeInTheDocument();
      });

      expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      expect(screen.getByText("Execution receipt")).toBeInTheDocument();
      expect(screen.getByText("Reconciliation visibility")).toBeInTheDocument();
      expect(screen.getByText("Coordination visibility")).toBeInTheDocument();
      expect(screen.getAllByText("action-execution-789").length).toBeGreaterThan(0);
      expect(screen.getAllByText("shuffle-run-789").length).toBeGreaterThan(0);
      expect(screen.getByText("Expected AegisOps state")).toBeInTheDocument();
      expect(screen.getAllByText("matched").length).toBeGreaterThan(0);
      expect(screen.getByText("Authoritative AegisOps state")).toBeInTheDocument();
      expect(screen.getAllByText("mismatched").length).toBeGreaterThan(0);
      expect(screen.getByText("Received receipt ingest")).toBeInTheDocument();
      expect(screen.getByText("review_mismatch_before_closeout")).toBeInTheDocument();
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
        screen.getByText("Requested and observed coordination references do not match."),
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

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-expired-789"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
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
        screen.getByText("No authoritative execution receipt is attached to this reviewed request yet."),
      ).toBeInTheDocument();
      expect(
        screen.getByText("No authoritative reconciliation record is visible for this reviewed request yet."),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(/Execution receipt visibility is present, but downstream reconciliation is still/i),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("Coordination visibility")).not.toBeInTheDocument();
    });

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

      const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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
              ...(actionReviewPayload.action_review as Record<string, unknown>),
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

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Record approval decision" }),
        ).toBeInTheDocument();
        expect(screen.getAllByText("pending_approval").length).toBeGreaterThan(0);
      });

      const approvalDecisionSection = screen.getByRole("heading", {
        name: "Record approval decision",
      });
      const approvalDecisionCard = approvalDecisionSection.closest(".MuiCard-root");
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
      fireEvent.click(within(approvalDecisionCard as HTMLElement).getByRole("checkbox"));
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
        expect(screen.getAllByText("await_execution_receipt").length).toBeGreaterThan(0);
        expect(screen.getAllByText("approver@example.com").length).toBeGreaterThan(0);
        expect(
          screen.getAllByText(
            "The reviewed owner notification stays within the approved notify boundary.",
          ).length,
        ).toBeGreaterThan(0);
      });
    });

    it("keeps approval submission blocked when the backend has not confirmed the current authoritative review", async () => {
      const fetchFn = createAuthorizedFetch({
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
      }, {
        identity: "approver@example.com",
        provider: "authentik",
        roles: ["Approver"],
        subject: "operator-8",
      });
      const dependencies = createDefaultDependencies({ fetchFn });

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
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

    it("sanitizes bounded external-link logging so secret-like URL suffixes stay out of the UI event log", async () => {
      const user = userEvent.setup();
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-action-review": {
            action_request_id: "action-request-246",
            read_only: true,
            current_action_review: {
              action_request_id: "action-request-246",
              review_state: "approved",
            },
            action_review: {
              action_request_id: "action-request-246",
              review_state: "approved",
              approval_state: "approved",
              requester_identity: "analyst@example.com",
              recipient_identity: "repo-owner@example.com",
              coordination_ticket_outcome: {
                authority: "authoritative_aegisops_review",
                status: "present",
                ticket_reference_url:
                  "https://tickets.example.invalid/incidents/246/signed/super-secret-token?token=query-secret",
              },
            },
          },
        }, {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-246"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("link", {
          name: "Open downstream coordination reference",
        }),
      );

      expect(screen.getByText("Target: https://tickets.example.invalid/incidents/246/<redacted-path-suffix>")).toBeInTheDocument();
      expect(screen.queryByText(/query-secret|super-secret-token/)).not.toBeInTheDocument();
    });

    it("keeps unsafe coordination reference schemes non-clickable", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-action-review": {
            action_request_id: "action-request-unsafe-link",
            read_only: true,
            current_action_review: {
              action_request_id: "action-request-unsafe-link",
              review_state: "approved",
            },
            action_review: {
              action_request_id: "action-request-unsafe-link",
              review_state: "approved",
              approval_state: "approved",
              requester_identity: "analyst@example.com",
              recipient_identity: "repo-owner@example.com",
              coordination_ticket_outcome: {
                authority: "authoritative_aegisops_review",
                status: "present",
                ticket_reference_url: "javascript:alert('ticket')",
              },
            },
          },
        }, {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/action-review/action-request-unsafe-link"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Action Review" })).toBeInTheDocument();
      });

      expect(screen.queryByRole("link", {
        name: "Open downstream coordination reference",
      })).not.toBeInTheDocument();
      expect(screen.getByText("Downstream coordination reference: javascript:alert('ticket')")).toBeInTheDocument();
      expect(screen.queryByText("External open")).not.toBeInTheDocument();
    });
  });
}
