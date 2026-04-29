import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  jsonResponse,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesControlPlaneTicketRequestTests() {
  describe("control-plane tracking-ticket request routes", () => {
    it("creates reviewed tracking-ticket action requests from case detail", async () => {
      let caseDetailPayload: Record<string, unknown> = {
        case_id: "case-789",
        case_record: {
          case_id: "case-789",
          lifecycle_state: "pending_action",
        },
        linked_alert_ids: ["alert-789"],
        linked_observation_ids: [],
        linked_lead_ids: [],
        linked_recommendation_ids: ["recommendation-789"],
        linked_evidence_ids: ["evidence-789"],
        linked_reconciliation_ids: ["recon-789"],
        provenance_summary: {
          authoritative_anchor: {
            record_family: "case",
            record_id: "case-789",
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
      const fetchFn = vi
        .fn<typeof fetch>()
        .mockImplementation((input, init) => {
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
                action_type: "create_tracking_ticket",
                coordination_reference_id: "coord-ref-ui-ticket-001",
                coordination_target_type: "zammad",
                expires_at: "2026-04-23T00:00",
                family: "recommendation",
                record_id: "recommendation-789",
                requester_identity: "analyst@example.com",
                ticket_description:
                  "Open one reviewed ticket for daily operator follow-up.",
                ticket_severity: "medium",
                ticket_title: "Review repository owner change",
              }),
            );
            caseDetailPayload = {
              ...caseDetailPayload,
              current_action_review: {
                action_request_id: "action-request-ticket-789",
                review_state: "unresolved",
                next_expected_action: "await_approval_decision",
              },
            };
            return Promise.resolve(
              jsonResponse({
                action_request_id: "action-request-ticket-789",
                case_id: "case-789",
              }),
            );
          }

          return Promise.reject(new Error(`Unexpected fetch: ${url}`));
        });
      const dependencies = createDefaultDependencies({ fetchFn });

      renderOperatorRoute("/operator/cases/case-789", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      const actionRequestSection = screen.getByRole("heading", {
        name: "Create reviewed action request",
      });
      const actionRequestCard = actionRequestSection.closest(".MuiCard-root");
      expect(actionRequestCard).not.toBeNull();
      fireEvent.mouseDown(
        within(actionRequestCard as HTMLElement).getByRole("combobox", {
          name: "Action type",
        }),
      );
      fireEvent.click(
        screen.getByRole("option", { name: "create_tracking_ticket" }),
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Recommendation id",
        }),
        { target: { value: "recommendation-789" } },
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Coordination reference id",
        }),
        { target: { value: "coord-ref-ui-ticket-001" } },
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Ticket title",
        }),
        { target: { value: "Review repository owner change" } },
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Ticket description",
        }),
        {
          target: {
            value: "Open one reviewed ticket for daily operator follow-up.",
          },
        },
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Expires at",
        }),
        { target: { value: "2026-04-23T00:00" } },
      );
      fireEvent.click(
        within(actionRequestCard as HTMLElement).getByRole("checkbox"),
      );
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
        expect(
          screen.getAllByText("action-request-ticket-789").length,
        ).toBeGreaterThan(0);
      });
    }, 10000);
  });
}
