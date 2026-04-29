import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  createOptionalExtensionPayload,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesControlPlaneReadOnlyTests() {
  describe("control-plane read-only status routes", () => {
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

      renderOperatorRoute("/operator/cases/case-456", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("Provenance summary")).toBeInTheDocument();
        expect(
          screen.getByText("Subordinate evidence context"),
        ).toBeInTheDocument();
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
              ticket_reference_url:
                "https://tickets.example.invalid/tickets/ZM-456",
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
                ticket_reference_url:
                  "https://tickets.example.invalid/tickets/ZM-456",
              },
            },
          },
        }),
      });

      renderOperatorRoute("/operator/cases/case-ticket-456", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Case Detail" }),
        ).toBeInTheDocument();
      });

      expect(screen.getByText("Coordination visibility")).toBeInTheDocument();
      expect(screen.getByText("Coordination: created")).toBeInTheDocument();
      expect(
        screen.getByText("Authority: authoritative_aegisops_review"),
      ).toBeInTheDocument();
      expect(
        screen.getAllByText("coord-ref-case-ticket-456").length,
      ).toBeGreaterThan(0);
      expect(screen.getAllByText("zammad").length).toBeGreaterThan(0);
      expect(screen.getAllByText("ZM-456").length).toBeGreaterThan(0);
      expect(screen.getByText("receipt-ticket-456")).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Open downstream coordination reference",
        }),
      ).toHaveAttribute(
        "href",
        "https://tickets.example.invalid/tickets/ZM-456",
      );
      expect(
        screen.getByText(
          "External tickets remain non-authoritative coordination context for this case.",
        ),
      ).toBeInTheDocument();
    });

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

      renderOperatorRoute("/operator/readiness", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Readiness" }),
        ).toBeInTheDocument();
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
      const readinessCall = fetchFn.mock.calls.find(([url]) =>
        String(url).startsWith("/diagnostics/readiness"),
      );
      expect(readinessCall).toBeDefined();
      const [readinessUrl, readinessOptions] = readinessCall!;
      const parsedReadinessUrl = new URL(
        String(readinessUrl),
        "http://operator-ui.local",
      );
      expect(parsedReadinessUrl.pathname).toBe("/diagnostics/readiness");
      expect(parsedReadinessUrl.searchParams.get("order")).toBe("ASC");
      expect(parsedReadinessUrl.searchParams.get("page")).toBe("1");
      expect(parsedReadinessUrl.searchParams.get("per_page")).toBe("1");
      expect(parsedReadinessUrl.searchParams.get("sort")).toBe("status");
      expect(readinessOptions).toEqual(expect.any(Object));
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

      renderOperatorRoute("/operator/reconciliation", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Reconciliation" }),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getAllByText("case linkage mismatch remains unresolved")
            .length,
        ).toBeGreaterThan(0);
      });
      expect(screen.getAllByText(/mismatch/i).length).toBeGreaterThan(0);
    });
  });
}
