import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  createOptionalExtensionPayload,
  jsonResponse,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesControlPlaneTests() {
  describe("control-plane status routes", () => {
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
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("Provenance summary")).toBeInTheDocument();
        expect(screen.getByText("Subordinate evidence context")).toBeInTheDocument();
        expect(screen.getAllByText("github_audit").length).toBeGreaterThan(0);
        expect(screen.getByText("recon-123")).toBeInTheDocument();
      });
    });

    it("renders reviewed tracking-ticket posture on case detail without making the ticket authoritative", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-case-detail": {
            case_id: "case-ticket-456",
            case_record: {
              case_id: "case-ticket-456",
              lifecycle_state: "pending_action",
            },
            linked_alert_ids: ["alert-ticket-456"],
            linked_observation_ids: [],
            linked_recommendation_ids: ["recommendation-ticket-456"],
            linked_evidence_ids: ["evidence-ticket-456"],
            linked_reconciliation_ids: ["recon-ticket-456"],
            provenance_summary: {
              authoritative_anchor: {
                record_family: "case",
                record_id: "case-ticket-456",
                source_family: "github_audit",
                provenance_classification: "authoritative",
              },
            },
            linked_alert_records: [],
            linked_evidence_records: [],
            linked_reconciliation_records: [],
            cross_source_timeline: [],
            external_ticket_reference: {
              authority: "non_authoritative",
              status: "present",
              coordination_reference_id: "coord-ref-case-ticket-456",
              coordination_target_type: "zammad",
              coordination_target_id: "ZM-456",
              ticket_reference_url: "https://tickets.example.invalid/tickets/ZM-456",
            },
            current_action_review: {
              action_request_id: "action-request-ticket-456",
              review_state: "approved",
              next_expected_action: "review_created_ticket",
              target_scope: {
                coordination_reference_id: "coord-ref-case-ticket-456",
                coordination_target_type: "zammad",
              },
              coordination_ticket_outcome: {
                authority: "authoritative_aegisops_review",
                status: "created",
                summary:
                  "reviewed create-ticket outcome recorded from authoritative execution and reconciliation",
                action_request_id: "action-request-ticket-456",
                action_execution_id: "action-execution-ticket-456",
                reconciliation_id: "recon-ticket-456",
                coordination_reference_id: "coord-ref-case-ticket-456",
                coordination_target_type: "zammad",
                coordination_target_id: "ZM-456",
                external_receipt_id: "receipt-ticket-456",
                ticket_reference_url: "https://tickets.example.invalid/tickets/ZM-456",
              },
            },
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/cases/case-ticket-456"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByText("Coordination visibility")).toBeInTheDocument();
      expect(screen.getByText("Coordination: created")).toBeInTheDocument();
      expect(screen.getByText("Authority: authoritative_aegisops_review")).toBeInTheDocument();
      expect(screen.getAllByText("coord-ref-case-ticket-456").length).toBeGreaterThan(0);
      expect(screen.getAllByText("zammad").length).toBeGreaterThan(0);
      expect(screen.getAllByText("ZM-456").length).toBeGreaterThan(0);
      expect(screen.getByText("receipt-ticket-456")).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Open downstream coordination reference" })).toHaveAttribute(
        "href",
        "https://tickets.example.invalid/tickets/ZM-456",
      );
      expect(
        screen.getByText(
          "External tickets remain non-authoritative coordination context for this case.",
        ),
      ).toBeInTheDocument();
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
              action_type: "create_tracking_ticket",
              coordination_reference_id: "coord-ref-ui-ticket-001",
              coordination_target_type: "zammad",
              expires_at: "2026-04-23T00:00",
              family: "recommendation",
              record_id: "recommendation-789",
              requester_identity: "analyst@example.com",
              ticket_description: "Open one reviewed ticket for daily operator follow-up.",
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

      render(
        <MemoryRouter initialEntries={["/operator/cases/case-789"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
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
      fireEvent.click(screen.getByRole("option", { name: "create_tracking_ticket" }));
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
        expect(
          screen.getAllByText("action-request-ticket-789").length,
        ).toBeGreaterThan(0);
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
            optional_extensions: createOptionalExtensionPayload(),
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
      expect(
        screen.getByRole("heading", { name: "Optional evidence posture" }),
      ).toBeInTheDocument();
      expect(screen.getByText("Endpoint evidence")).toBeInTheDocument();
      expect(screen.getByText("Optional network evidence")).toBeInTheDocument();
      expect(screen.getAllByText("Disabled By Default")).toHaveLength(2);
      expect(screen.queryByText("ML shadow")).not.toBeInTheDocument();
      expect(fetchFn).toHaveBeenCalledWith(
        "/diagnostics/readiness?order=ASC&page=1&per_page=1&sort=status",
        expect.any(Object),
      );
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
}
