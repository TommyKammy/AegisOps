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
  jsonResponse,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesControlPlaneActionRequestTests() {
  describe("control-plane action request routes", () => {
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

          if (
            url.startsWith("/operator/record-action-review-manual-fallback")
          ) {
            expect(init?.method).toBe("POST");
            expect(init?.body).toBe(
              JSON.stringify({
                action_request_id: "action-request-123",
                action_taken:
                  "Completed the approved owner notification manually using the reviewed fallback path.",
                authority_boundary: "approved_human_fallback",
                fallback_actor_identity: "analyst@example.com",
                fallback_at: "2026-04-22T09:15",
                reason:
                  "The automation path was unavailable after reviewed approval.",
                residual_uncertainty: "Awaiting recipient acknowledgement.",
                verification_evidence_ids: ["evidence-123", "evidence-456"],
              }),
            );
            caseDetailPayload = {
              ...caseDetailPayload,
              current_action_review: {
                ...(caseDetailPayload.current_action_review as Record<
                  string,
                  unknown
                >),
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

          if (
            url.startsWith("/operator/record-action-review-escalation-note")
          ) {
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
                ...(caseDetailPayload.current_action_review as Record<
                  string,
                  unknown
                >),
                runtime_visibility: {
                  ...(((
                    caseDetailPayload.current_action_review as Record<
                      string,
                      unknown
                    >
                  ).runtime_visibility as
                    | Record<string, unknown>
                    | undefined) ?? {}),
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

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByRole("heading", {
            name: "Create reviewed action request",
          }),
        ).toBeInTheDocument();
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
            value:
              "Notify the accountable repository owner about the reviewed repository change.",
          },
        },
      );
      fireEvent.change(
        within(actionRequestCard as HTMLElement).getByRole("textbox", {
          name: "Escalation reason",
        }),
        {
          target: {
            value:
              "Repository owner notification must stay tracked inside the reviewed request path.",
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
          screen.getAllByText("action-request-123").length,
        ).toBeGreaterThan(0);
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
            value:
              "The automation path was unavailable after reviewed approval.",
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
      const verificationEvidenceField = within(
        manualFallbackCard as HTMLElement,
      ).getByRole("textbox", {
        name: "Verification evidence ids",
      });
      fireEvent.change(verificationEvidenceField, {
        target: { value: "evidence-123, evidence-456" },
      });
      fireEvent.change(
        within(manualFallbackCard as HTMLElement).getByRole("textbox", {
          name: "Residual uncertainty",
        }),
        { target: { value: "Awaiting recipient acknowledgement." } },
      );
      fireEvent.click(
        within(manualFallbackCard as HTMLElement).getByRole("checkbox"),
      );
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
      fireEvent.click(
        within(escalationNoteCard as HTMLElement).getByRole("checkbox"),
      );
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
    }, 20000);
  });
}
