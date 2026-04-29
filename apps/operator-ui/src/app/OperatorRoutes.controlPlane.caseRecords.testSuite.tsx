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

export function registerOperatorRoutesControlPlaneCaseRecordTests() {
  describe("control-plane case record routes", () => {
    it("records bounded case observations, leads, and recommendations from case detail", async () => {
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

          if (url.startsWith("/operator/record-case-observation")) {
            expect(init?.method).toBe("POST");
            expect(init?.body).toBe(
              JSON.stringify({
                author_identity: "analyst@example.com",
                case_id: "case-456",
                observed_at: "2026-04-22T00:00",
                scope_statement:
                  "Observed repository permission change requires tracked review.",
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
                triage_rationale:
                  "Privilege-impacting change needs durable follow-up.",
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
                intended_outcome:
                  "Review repository owner change evidence before approval.",
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

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      const observationSection = await screen.findByRole("heading", {
        name: "Record case observation",
      });
      const observationCard = observationSection.closest(".MuiCard-root");
      expect(observationCard).not.toBeNull();
      fireEvent.change(
        within(observationCard as HTMLElement).getByRole("textbox", {
          name: "Observed at",
        }),
        { target: { value: "2026-04-22T00:00" } },
      );
      fireEvent.change(
        within(observationCard as HTMLElement).getByRole("textbox", {
          name: "Scope statement",
        }),
        {
          target: {
            value:
              "Observed repository permission change requires tracked review.",
          },
        },
      );
      const supportingEvidenceField = within(
        observationCard as HTMLElement,
      ).getByRole("textbox", {
        name: "Supporting evidence ids",
      });
      fireEvent.change(supportingEvidenceField, {
        target: { value: "evidence-123, evidence-456" },
      });
      fireEvent.click(
        within(observationCard as HTMLElement).getByRole("checkbox"),
      );
      fireEvent.click(
        within(observationCard as HTMLElement).getByRole("button", {
          name: "Record observation",
        }),
      );
      await waitFor(() => {
        expect(fetchFn).toHaveBeenCalledWith(
          "/operator/record-case-observation",
          expect.objectContaining({
            method: "POST",
          }),
        );
        expect(
          screen.getByText("Known observation ids: observation-123"),
        ).toBeInTheDocument();
      });

      const leadSection = screen.getByRole("heading", {
        name: "Record case lead",
      });
      const leadCard = leadSection.closest(".MuiCard-root");
      expect(leadCard).not.toBeNull();
      fireEvent.change(
        within(leadCard as HTMLElement).getByRole("textbox", {
          name: "Observation id",
        }),
        { target: { value: "observation-123" } },
      );
      fireEvent.change(
        within(leadCard as HTMLElement).getByRole("textbox", {
          name: "Triage rationale",
        }),
        {
          target: {
            value: "Privilege-impacting change needs durable follow-up.",
          },
        },
      );
      fireEvent.click(within(leadCard as HTMLElement).getByRole("checkbox"));
      fireEvent.click(
        within(leadCard as HTMLElement).getByRole("button", {
          name: "Record lead",
        }),
      );
      await waitFor(() => {
        expect(fetchFn).toHaveBeenCalledWith(
          "/operator/record-case-lead",
          expect.objectContaining({
            method: "POST",
          }),
        );
        expect(
          screen.getByText("Known lead ids: lead-123"),
        ).toBeInTheDocument();
      });

      const recommendationSection = screen.getByRole("heading", {
        name: "Record case recommendation",
      });
      const recommendationCard = recommendationSection.closest(".MuiCard-root");
      expect(recommendationCard).not.toBeNull();
      fireEvent.change(
        within(recommendationCard as HTMLElement).getByRole("textbox", {
          name: "Lead id",
        }),
        { target: { value: "lead-123" } },
      );
      fireEvent.change(
        within(recommendationCard as HTMLElement).getByRole("textbox", {
          name: "Intended outcome",
        }),
        {
          target: {
            value: "Review repository owner change evidence before approval.",
          },
        },
      );
      fireEvent.click(
        within(recommendationCard as HTMLElement).getByRole("checkbox"),
      );
      fireEvent.click(
        within(recommendationCard as HTMLElement).getByRole("button", {
          name: "Record recommendation",
        }),
      );
      await waitFor(() => {
        expect(
          screen.getAllByText("recommendation-123").length,
        ).toBeGreaterThan(0);
      });
    }, 20000);
  });
}
