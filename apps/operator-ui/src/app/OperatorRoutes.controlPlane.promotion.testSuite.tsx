import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  jsonResponse,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesControlPlanePromotionTests() {
  describe("control-plane alert promotion routes", () => {
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

      renderOperatorRoute("/operator/alerts/alert-123", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Alert Detail" }),
        ).toBeInTheDocument();
      });

      const promoteSection = await screen.findByRole("heading", {
        name: "Promote alert into case",
      });
      const promoteCard = promoteSection.closest(".MuiCard-root");
      expect(promoteCard).not.toBeNull();

      await user.click(
        within(promoteCard as HTMLElement).getByRole("checkbox"),
      );
      await user.click(
        within(promoteCard as HTMLElement).getByRole("button", {
          name: "Promote alert",
        }),
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
  });
}
