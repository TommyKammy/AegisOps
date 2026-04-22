import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import {
  OperatorRoutes,
  createDefaultDependencies,
} from "./OperatorRoutes";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

function createAuthorizedFetch(
  handlers: Record<string, unknown>,
  sessionOverride?: {
    identity: string;
    provider: string;
    roles: string[];
    subject: string;
  },
) {
  return vi.fn<typeof fetch>().mockImplementation((input) => {
    const url = String(input);

    if (url.startsWith("/api/operator/session")) {
      return Promise.resolve(
        jsonResponse(
          sessionOverride ?? {
            identity: "analyst@example.com",
            provider: "authentik",
            roles: ["Analyst"],
            subject: "operator-7",
          },
        ),
      );
    }

    const match = Object.entries(handlers).find(([prefix]) => url.startsWith(prefix));
    if (match) {
      return Promise.resolve(jsonResponse(match[1]));
    }

    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });
}

describe("OperatorRoutes", () => {
  it("redirects unauthenticated users to the reviewed login route", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 401 })),
    });

    render(
      <MemoryRouter initialEntries={["/operator/queue"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Operator Sign-In" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Return path: /operator/queue")).toBeInTheDocument();
  });

  it("routes unsupported backend roles to the forbidden page", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "reviewer@example.com",
          provider: "authentik",
          roles: ["viewer"],
          subject: "user-42",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Access denied" }),
      ).toBeInTheDocument();
    });
  });

  it("fails closed on malformed reviewed session responses", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: "analyst",
          subject: "operator-11",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Session verification failed" }),
      ).toBeInTheDocument();
    });
  });

  it("restores an authorized session into the protected shell", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst"],
          subject: "operator-7",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });
  });

  it("hides action-review navigation for analyst-only sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/action review/i)).not.toBeInTheDocument();
  });

  it("shows action-review navigation for reviewed approver sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    expect(screen.getAllByText(/action review/i).length).toBeGreaterThan(0);
  });

  it("redirects analyst-only deep links away from the action-review route", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator/action-review"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/action review/i)).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Queue triage stays inside AegisOps as the authoritative review selection surface.",
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

    expect(screen.getAllByText("Approval lifecycle").length).toBeGreaterThan(0);
    expect(screen.getAllByText("expired").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Expired means the reviewed approval window no longer authorizes this request. Operators must reread authoritative state rather than infer continued validity.",
      ),
    ).toBeInTheDocument();
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

  it("renders case detail with provenance summary and subordinate context", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": {
          case_id: "case-456",
          case_record: {
            case_id: "case-456",
            lifecycle_state: "pending_action",
          },
          linked_alert_ids: ["alert-123"],
          linked_observation_ids: ["observation-123"],
          linked_recommendation_ids: ["recommendation-123"],
          linked_evidence_ids: ["evidence-123"],
          linked_reconciliation_ids: ["recon-123"],
          provenance_summary: {
            authoritative_anchor: {
              record_family: "case",
              record_id: "case-456",
              source_family: "github_audit",
              provenance_classification: "authoritative",
            },
          },
          linked_alert_records: [
            {
              alert_id: "alert-123",
            },
          ],
          linked_evidence_records: [
            {
              evidence_id: "evidence-123",
            },
          ],
          linked_reconciliation_records: [
            {
              reconciliation_id: "recon-123",
            },
          ],
          cross_source_timeline: [
            {
              record_family: "case",
              record_id: "case-456",
              source_family: "github_audit",
              provenance_classification: "authoritative",
            },
          ],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Provenance summary")).toBeInTheDocument();
      expect(screen.getByText("Subordinate evidence context")).toBeInTheDocument();
      expect(screen.getAllByText("github_audit").length).toBeGreaterThan(0);
      expect(screen.getByText("recon-123")).toBeInTheDocument();
    });
  });

  it("promotes an alert into a case from alert detail and re-renders authoritative state", async () => {
    const user = userEvent.setup();
    let alertDetailPayload: Record<string, unknown> = {
      alert_id: "alert-123",
      alert: {
        alert_id: "alert-123",
        lifecycle_state: "triaged",
      },
      review_state: "triaged",
      escalation_boundary: "case_optional",
      provenance: {
        admission_kind: "live",
        admission_channel: "live_wazuh_webhook",
      },
      lineage: {
        source_systems: ["wazuh"],
      },
      linked_evidence_records: [],
    };
    let caseDetailPayload: Record<string, unknown> = {
      case_id: "case-456",
      case_record: {
        case_id: "case-456",
        lifecycle_state: "open",
      },
      linked_alert_ids: ["alert-123"],
      linked_observation_ids: [],
      linked_lead_ids: [],
      linked_recommendation_ids: [],
      linked_evidence_ids: [],
      linked_reconciliation_ids: [],
      provenance_summary: {
        authoritative_anchor: {
          record_family: "case",
          record_id: "case-456",
          source_family: "github_audit",
          provenance_classification: "authoritative",
        },
      },
      linked_alert_records: [],
      linked_evidence_records: [],
      linked_reconciliation_records: [],
      cross_source_timeline: [],
    };
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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
        return Promise.resolve(jsonResponse(alertDetailPayload));
      }

      if (url.startsWith("/inspect-case-detail")) {
        return Promise.resolve(jsonResponse(caseDetailPayload));
      }

      if (url.startsWith("/operator/promote-alert-to-case")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            alert_id: "alert-123",
            case_lifecycle_state: "open",
          }),
        );
        alertDetailPayload = {
          ...alertDetailPayload,
          case_record: {
            case_id: "case-456",
          },
        };
        return Promise.resolve(
          jsonResponse({
            alert_id: "alert-123",
            case_id: "case-456",
            lifecycle_state: "open",
          }),
        );
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
    });

    const promoteSection = await screen.findByRole("heading", {
      name: "Promote alert into case",
    });
    const promoteCard = promoteSection.closest(".MuiCard-root");
    expect(promoteCard).not.toBeNull();

    await user.click(within(promoteCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(promoteCard as HTMLElement).getByRole("button", { name: "Promote alert" }),
    );

    await waitFor(() => {
      expect(screen.getAllByText("case-456").length).toBeGreaterThan(0);
    });

    expect(fetchFn).toHaveBeenCalledWith(
      "/operator/promote-alert-to-case",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });


  it("records bounded case observations, leads, and recommendations from case detail", async () => {
    const user = userEvent.setup();
    let caseDetailPayload: Record<string, unknown> = {
      case_id: "case-456",
      case_record: {
        case_id: "case-456",
        lifecycle_state: "pending_action",
      },
      linked_alert_ids: ["alert-123"],
      linked_observation_ids: [],
      linked_lead_ids: [],
      linked_recommendation_ids: [],
      linked_evidence_ids: ["evidence-123"],
      linked_reconciliation_ids: ["recon-123"],
      provenance_summary: {
        authoritative_anchor: {
          record_family: "case",
          record_id: "case-456",
          source_family: "github_audit",
          provenance_classification: "authoritative",
        },
      },
      linked_alert_records: [],
      linked_evidence_records: [],
      linked_reconciliation_records: [],
      cross_source_timeline: [],
    };
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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

      if (url.startsWith("/inspect-case-detail")) {
        return Promise.resolve(jsonResponse(caseDetailPayload));
      }

      if (url.startsWith("/operator/record-case-observation")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            author_identity: "analyst@example.com",
            case_id: "case-456",
            observed_at: "2026-04-22T00:00",
            scope_statement: "Observed repository permission change requires tracked review.",
            supporting_evidence_ids: ["evidence-123", "evidence-456"],
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_observation_ids: ["observation-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            observation_id: "observation-123",
          }),
        );
      }

      if (url.startsWith("/operator/record-case-lead")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            case_id: "case-456",
            observation_id: "observation-123",
            triage_owner: "analyst@example.com",
            triage_rationale: "Privilege-impacting change needs durable follow-up.",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_lead_ids: ["lead-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            lead_id: "lead-123",
            observation_id: "observation-123",
          }),
        );
      }

      if (url.startsWith("/operator/record-case-recommendation")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            case_id: "case-456",
            intended_outcome: "Review repository owner change evidence before approval.",
            lead_id: "lead-123",
            review_owner: "analyst@example.com",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_recommendation_ids: ["recommendation-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            lead_id: "lead-123",
            recommendation_id: "recommendation-123",
          }),
        );
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
    });

    const observationSection = await screen.findByRole("heading", {
      name: "Record case observation",
    });
    const observationCard = observationSection.closest(".MuiCard-root");
    expect(observationCard).not.toBeNull();
    await user.type(
      within(observationCard as HTMLElement).getByRole("textbox", {
        name: "Observed at",
      }),
      "2026-04-22T00:00",
    );
    await user.type(
      within(observationCard as HTMLElement).getByRole("textbox", {
        name: "Scope statement",
      }),
      "Observed repository permission change requires tracked review.",
    );
    const supportingEvidenceField = within(observationCard as HTMLElement).getByRole(
      "textbox",
      {
        name: "Supporting evidence ids",
      },
    );
    await user.clear(supportingEvidenceField);
    await user.type(supportingEvidenceField, "evidence-123, evidence-456");
    await user.click(within(observationCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(observationCard as HTMLElement).getByRole("button", { name: "Record observation" }),
    );
    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-case-observation",
        expect.objectContaining({
          method: "POST",
        }),
      );
      expect(screen.getByText("Known observation ids: observation-123")).toBeInTheDocument();
    });

    const leadSection = screen.getByRole("heading", { name: "Record case lead" });
    const leadCard = leadSection.closest(".MuiCard-root");
    expect(leadCard).not.toBeNull();
    await user.type(
      within(leadCard as HTMLElement).getByRole("textbox", {
        name: "Observation id",
      }),
      "observation-123",
    );
    await user.type(
      within(leadCard as HTMLElement).getByRole("textbox", {
        name: "Triage rationale",
      }),
      "Privilege-impacting change needs durable follow-up.",
    );
    await user.click(within(leadCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(leadCard as HTMLElement).getByRole("button", { name: "Record lead" }),
    );
    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-case-lead",
        expect.objectContaining({
          method: "POST",
        }),
      );
      expect(screen.getByText("Known lead ids: lead-123")).toBeInTheDocument();
    });

    const recommendationSection = screen.getByRole("heading", {
      name: "Record case recommendation",
    });
    const recommendationCard = recommendationSection.closest(".MuiCard-root");
    expect(recommendationCard).not.toBeNull();
    await user.type(
      within(recommendationCard as HTMLElement).getByRole("textbox", {
        name: "Lead id",
      }),
      "lead-123",
    );
    await user.type(
      within(recommendationCard as HTMLElement).getByRole("textbox", {
        name: "Intended outcome",
      }),
      "Review repository owner change evidence before approval.",
    );
    await user.click(within(recommendationCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(recommendationCard as HTMLElement).getByRole("button", {
        name: "Record recommendation",
      }),
    );
    await waitFor(() => {
      expect(screen.getAllByText("recommendation-123").length).toBeGreaterThan(0);
    });
  }, 20000);

  it("creates reviewed action requests and records manual follow-up notes from case detail", async () => {
    const user = userEvent.setup();
    let caseDetailPayload: Record<string, unknown> = {
      case_id: "case-456",
      case_record: {
        case_id: "case-456",
        lifecycle_state: "pending_action",
      },
      linked_alert_ids: ["alert-123"],
      linked_observation_ids: ["observation-123"],
      linked_lead_ids: ["lead-123"],
      linked_recommendation_ids: ["recommendation-123"],
      linked_evidence_ids: ["evidence-123"],
      linked_reconciliation_ids: ["recon-123"],
      provenance_summary: {
        authoritative_anchor: {
          record_family: "case",
          record_id: "case-456",
          source_family: "github_audit",
          provenance_classification: "authoritative",
        },
      },
      linked_alert_records: [],
      linked_evidence_records: [],
      linked_reconciliation_records: [],
      cross_source_timeline: [],
      current_action_review: null,
    };
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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

      if (url.startsWith("/inspect-case-detail")) {
        return Promise.resolve(jsonResponse(caseDetailPayload));
      }

      if (url.startsWith("/operator/create-reviewed-action-request")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            escalation_reason:
              "Repository owner notification must stay tracked inside the reviewed request path.",
            expires_at: "2026-04-23T00:00",
            family: "recommendation",
            message_intent:
              "Notify the accountable repository owner about the reviewed repository change.",
            recipient_identity: "repo-owner@example.com",
            record_id: "recommendation-123",
            requester_identity: "analyst@example.com",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          current_action_review: {
            action_request_id: "action-request-123",
            review_state: "unresolved",
            next_expected_action: "await_manual_follow_up",
          },
        };
        return Promise.resolve(
          jsonResponse({
            action_request_id: "action-request-123",
            case_id: "case-456",
          }),
        );
      }

      if (url.startsWith("/operator/record-action-review-manual-fallback")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            action_request_id: "action-request-123",
            action_taken:
              "Completed the approved owner notification manually using the reviewed fallback path.",
            authority_boundary: "approved_human_fallback",
            fallback_actor_identity: "analyst@example.com",
            fallback_at: "2026-04-22T09:15",
            reason: "The automation path was unavailable after reviewed approval.",
            residual_uncertainty: "Awaiting recipient acknowledgement.",
            verification_evidence_ids: ["evidence-123", "evidence-456"],
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          current_action_review: {
            ...(caseDetailPayload.current_action_review as Record<string, unknown>),
            runtime_visibility: {
              manual_fallback: {
                fallback_actor_identity: "analyst@example.com",
              },
            },
          },
        };
        return Promise.resolve(
          jsonResponse({
            action_request_id: "action-request-123",
          }),
        );
      }

      if (url.startsWith("/operator/record-action-review-escalation-note")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            action_request_id: "action-request-123",
            escalated_at: "2026-04-22T09:30",
            escalated_by_identity: "analyst@example.com",
            escalated_to: "on-call-manager-001",
            note: "Escalated because the unresolved reviewed request could not wait for the next shift.",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          current_action_review: {
            ...(caseDetailPayload.current_action_review as Record<string, unknown>),
            runtime_visibility: {
              ...((
                (caseDetailPayload.current_action_review as Record<string, unknown>)
                  .runtime_visibility as Record<string, unknown> | undefined
              ) ?? {}),
              escalation_notes: {
                escalated_by_identity: "analyst@example.com",
              },
            },
          },
        };
        return Promise.resolve(
          jsonResponse({
            action_request_id: "action-request-123",
          }),
        );
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Create reviewed action request" })).toBeInTheDocument();
    });

    const actionRequestSection = screen.getByRole("heading", {
      name: "Create reviewed action request",
    });
    const actionRequestCard = actionRequestSection.closest(".MuiCard-root");
    expect(actionRequestCard).not.toBeNull();
    fireEvent.change(
      within(actionRequestCard as HTMLElement).getByRole("textbox", {
        name: "Recommendation id",
      }),
      { target: { value: "recommendation-123" } },
    );
    fireEvent.change(
      within(actionRequestCard as HTMLElement).getByRole("textbox", {
        name: "Recipient identity",
      }),
      { target: { value: "repo-owner@example.com" } },
    );
    fireEvent.change(
      within(actionRequestCard as HTMLElement).getByRole("textbox", {
        name: "Message intent",
      }),
      {
        target: {
          value: "Notify the accountable repository owner about the reviewed repository change.",
        },
      },
    );
    fireEvent.change(
      within(actionRequestCard as HTMLElement).getByRole("textbox", {
        name: "Escalation reason",
      }),
      {
        target: {
          value: "Repository owner notification must stay tracked inside the reviewed request path.",
        },
      },
    );
    fireEvent.change(
      within(actionRequestCard as HTMLElement).getByRole("textbox", {
        name: "Expires at",
      }),
      { target: { value: "2026-04-23T00:00" } },
    );
    fireEvent.click(within(actionRequestCard as HTMLElement).getByRole("checkbox"));
    fireEvent.click(
      within(actionRequestCard as HTMLElement).getByRole("button", {
        name: "Create action request",
      }),
    );

    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/create-reviewed-action-request",
        expect.objectContaining({
          method: "POST",
        }),
      );
      expect(screen.getAllByText("action-request-123").length).toBeGreaterThan(0);
    });

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Record manual fallback" }),
      ).toBeInTheDocument();
    });
    const manualFallbackSection = screen.getByRole("heading", {
      name: "Record manual fallback",
    });
    const manualFallbackCard = manualFallbackSection.closest(".MuiCard-root");
    expect(manualFallbackCard).not.toBeNull();
    fireEvent.change(
      within(manualFallbackCard as HTMLElement).getByRole("textbox", {
        name: "Fallback at",
      }),
      { target: { value: "2026-04-22T09:15" } },
    );
    fireEvent.change(
      within(manualFallbackCard as HTMLElement).getByRole("textbox", {
        name: "Reason",
      }),
      {
        target: {
          value: "The automation path was unavailable after reviewed approval.",
        },
      },
    );
    fireEvent.change(
      within(manualFallbackCard as HTMLElement).getByRole("textbox", {
        name: "Action taken",
      }),
      {
        target: {
          value:
            "Completed the approved owner notification manually using the reviewed fallback path.",
        },
      },
    );
    const verificationEvidenceField = within(manualFallbackCard as HTMLElement).getByRole(
      "textbox",
      {
        name: "Verification evidence ids",
      },
    );
    fireEvent.change(verificationEvidenceField, {
      target: { value: "evidence-123, evidence-456" },
    });
    fireEvent.change(
      within(manualFallbackCard as HTMLElement).getByRole("textbox", {
        name: "Residual uncertainty",
      }),
      { target: { value: "Awaiting recipient acknowledgement." } },
    );
    fireEvent.click(within(manualFallbackCard as HTMLElement).getByRole("checkbox"));
    fireEvent.click(
      within(manualFallbackCard as HTMLElement).getByRole("button", {
        name: "Record manual fallback",
      }),
    );

    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-action-review-manual-fallback",
        expect.objectContaining({
          method: "POST",
        }),
      );
    });

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Record escalation note" }),
      ).toBeInTheDocument();
    });
    const escalationNoteSection = screen.getByRole("heading", {
      name: "Record escalation note",
    });
    const escalationNoteCard = escalationNoteSection.closest(".MuiCard-root");
    expect(escalationNoteCard).not.toBeNull();
    fireEvent.change(
      within(escalationNoteCard as HTMLElement).getByRole("textbox", {
        name: "Escalated at",
      }),
      { target: { value: "2026-04-22T09:30" } },
    );
    fireEvent.change(
      within(escalationNoteCard as HTMLElement).getByRole("textbox", {
        name: "Escalated to",
      }),
      { target: { value: "on-call-manager-001" } },
    );
    fireEvent.change(
      within(escalationNoteCard as HTMLElement).getByRole("textbox", {
        name: "Note",
      }),
      {
        target: {
          value:
            "Escalated because the unresolved reviewed request could not wait for the next shift.",
        },
      },
    );
    fireEvent.click(within(escalationNoteCard as HTMLElement).getByRole("checkbox"));
    fireEvent.click(
      within(escalationNoteCard as HTMLElement).getByRole("button", {
        name: "Record escalation note",
      }),
    );

    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-action-review-escalation-note",
        expect.objectContaining({
          method: "POST",
        }),
      );
    });
  }, 10000);

  it("renders readiness from the reviewed diagnostics surface", async () => {
    const fetchFn = createAuthorizedFetch({
      "/diagnostics/readiness": {
        status: "ready",
        booted: true,
        startup: {
          startup_ready: true,
        },
        shutdown: {
          shutdown_ready: false,
        },
        persistence_mode: "postgresql",
        latest_reconciliation: {
          reconciliation_id: "recon-123",
        },
        metrics: {
          action_requests: {
            approved: 1,
          },
          action_executions: {
            terminal: 1,
          },
          review_path_health: {
            overall_state: "healthy",
            review_count: 1,
          },
          source_health: {
            tracked_sources: 1,
          },
          automation_substrate_health: {
            tracked_surfaces: 1,
          },
        },
      },
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/readiness"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Readiness" })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("postgresql")).toBeInTheDocument();
    });
    expect(fetchFn).toHaveBeenCalledWith(
      "/diagnostics/readiness?order=ASC&page=1&per_page=1&sort=status",
      expect.any(Object),
    );
  });

  it("renders a case-anchored assistant advisory route from reviewed advisory output", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-advisory-output": {
          read_only: true,
          record_family: "case",
          record_id: "case-456",
          output_kind: "case_summary",
          status: "ready",
          summary:
            "Repository owner membership drift remains bounded to the reviewed case scope.",
          citations: ["case-456", "alert-123", "evidence-123"],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/assistant/case/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
    });

    expect(screen.getAllByText("case").length).toBeGreaterThan(0);
    expect(screen.getAllByText("case-456").length).toBeGreaterThan(0);
    expect(screen.getByText(/Output: case_summary/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: ready/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        "Repository owner membership drift remains bounded to the reviewed case scope.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("evidence-123")).toBeInTheDocument();
  });

  it("renders cited recommendation draft output with explicit assistant-only framing", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-advisory-output": {
          read_only: true,
          record_family: "recommendation",
          record_id: "recommendation-123",
          output_kind: "recommendation_draft",
          status: "ready",
          cited_summary: {
            text: "The assistant draft stays anchored to the cited evidence before any reviewed action.",
            citations: ["recommendation-123", "evidence-123", "case-456"],
          },
          candidate_recommendations: [
            {
              text: "Proposal only: confirm the repository ownership change before raising an action request.",
              citations: ["evidence-123", "case-456"],
            },
          ],
          uncertainty_flags: ["advisory_only"],
          citations: ["recommendation-123", "evidence-123", "case-456"],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/assistant/recommendation/recommendation-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    const citedOutputSection = await screen.findByRole("heading", { name: "Cited advisory output" });
    const citedOutputCard = citedOutputSection.closest(".MuiCard-root");
    expect(citedOutputCard).not.toBeNull();
    expect(
      within(citedOutputCard as HTMLElement).getByText(
        "The assistant draft stays anchored to the cited evidence before any reviewed action.",
      ),
    ).toBeInTheDocument();
    expect(within(citedOutputCard as HTMLElement).getByText("recommendation-123")).toBeInTheDocument();
    expect(within(citedOutputCard as HTMLElement).getByText("evidence-123")).toBeInTheDocument();
    expect(within(citedOutputCard as HTMLElement).getByText("case-456")).toBeInTheDocument();

    const draftSection = screen.getByRole("heading", { name: "Recommendation draft" });
    const draftCard = draftSection.closest(".MuiCard-root");
    expect(draftCard).not.toBeNull();
    expect(within(draftCard as HTMLElement).getByText("Draft only")).toBeInTheDocument();
    expect(
      within(draftCard as HTMLElement).getByText(
        "Proposal only: confirm the repository ownership change before raising an action request.",
      ),
    ).toBeInTheDocument();
    expect(
      within(draftCard as HTMLElement).getByText(
        "Assistant output does not approve, execute, or reconcile workflow state.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Advisory failure visibility" }),
    ).not.toBeInTheDocument();
  });

  it("keeps fallback advisory summary fields out of the detail table", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-advisory-output": {
          read_only: true,
          record_family: "recommendation",
          record_id: "recommendation-123",
          output_kind: "recommendation_summary",
          status: "ready",
          cited_summary: {
            citations: ["recommendation-123", "evidence-123"],
          },
          message: "Use the reviewed recommendation as bounded advisory context.",
          advisory_text: "This fallback field should not be repeated in detail rows.",
          supporting_note: "Analyst follow-up remains separate from advisory prose.",
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/assistant/recommendation/recommendation-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("Use the reviewed recommendation as bounded advisory context."),
    ).toBeInTheDocument();

    const citedOutputSection = await screen.findByRole("heading", { name: "Cited advisory output" });
    const citedOutputCard = citedOutputSection.closest(".MuiCard-root");
    expect(citedOutputCard).not.toBeNull();
    expect(
      within(citedOutputCard as HTMLElement).getByText(
        "No cited summary anchors were returned for this advisory output.",
      ),
    ).toBeInTheDocument();
    expect(within(citedOutputCard as HTMLElement).queryByText("recommendation-123")).not.toBeInTheDocument();
    expect(within(citedOutputCard as HTMLElement).queryByText("evidence-123")).not.toBeInTheDocument();

    const detailTable = screen.getByRole("table");
    expect(within(detailTable).queryByText("Message")).not.toBeInTheDocument();
    expect(within(detailTable).queryByText("Output Text")).not.toBeInTheDocument();
    expect(within(detailTable).queryByText("Advisory Text")).not.toBeInTheDocument();
    expect(within(detailTable).getByText("Supporting Note")).toBeInTheDocument();
    expect(
      within(detailTable).getByText(
        "Analyst follow-up remains separate from advisory prose.",
      ),
    ).toBeInTheDocument();
  });

  it("renders explicit citation-failure and reviewed-context visibility for unresolved advisory output", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-advisory-output": {
          read_only: true,
          record_family: "case",
          record_id: "case-456",
          output_kind: "case_summary",
          status: "unresolved",
          cited_summary: {
            text: "Case summary case-456 remains unresolved because citation completeness or reviewed-context consistency is incomplete.",
            citations: ["case-456"],
          },
          key_observations: [
            {
              text: "Reviewed context exposes stable identifiers for the cited advisory output.",
              citations: [
                "reviewed_context.asset.asset_id=asset-123",
                "reviewed_context.identity.user_id=user-456",
              ],
            },
          ],
          unresolved_questions: [
            {
              text: "Which reviewed records, linked evidence, or stable reviewed-context identifiers support this advisory output?",
              citations: ["case-456"],
            },
            {
              text: "Which reviewed-context values are authoritative for: identity.user_id?",
              citations: ["case-456", "alert-123"],
            },
          ],
          uncertainty_flags: [
            "advisory_only",
            "missing_supporting_citations",
            "conflicting_reviewed_context",
          ],
          citations: ["case-456", "alert-123"],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/assistant/case/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Advisory failure visibility" })).toBeInTheDocument();
    expect(
      screen.getByText(/Missing citation support is visible here/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Conflicting reviewed context remains visible here/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Assistant advisory remains unresolved because required citation or reviewed-context checks failed.",
      ),
    ).toBeInTheDocument();

    const contextSection = screen.getByRole("heading", { name: "Assistant context explorer" });
    const contextCard = contextSection.closest(".MuiCard-root");
    expect(contextCard).not.toBeNull();
    expect(
      within(contextCard as HTMLElement).getByText(
        "Reviewed context exposes stable identifiers for the cited advisory output.",
      ),
    ).toBeInTheDocument();
    expect(
      within(contextCard as HTMLElement).getByText(
        "Which reviewed records, linked evidence, or stable reviewed-context identifiers support this advisory output?",
      ),
    ).toBeInTheDocument();
    expect(
      within(contextCard as HTMLElement).getByText(
        "reviewed_context.asset.asset_id=asset-123",
      ),
    ).toBeInTheDocument();
  });

  it("renders reconciliation mismatch visibility from reviewed records", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-reconciliation-status": {
          read_only: true,
          total_records: 1,
          records: [
            {
              reconciliation_id: "recon-123",
              lifecycle_state: "mismatch",
              ingest_disposition: "updated",
              mismatch_summary: "case linkage mismatch remains unresolved",
              compared_at: "2026-04-21T00:00:00+00:00",
              subject_linkage: {
                case_ids: ["case-456"],
              },
            },
          ],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/reconciliation"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Reconciliation" })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(
        screen.getAllByText("case linkage mismatch remains unresolved").length,
      ).toBeGreaterThan(0);
    });
    expect(screen.getAllByText(/mismatch/i).length).toBeGreaterThan(0);
  });
});
