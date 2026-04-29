import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesCaseworkIndexTests() {
  describe("casework index routes", () => {
    it("renders the alert drilldown index instead of the placeholder alert page", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-analyst-queue": {
            queue_name: "analyst_review",
            read_only: true,
            records: [
              {
                alert_id: "alert-index-001",
                review_state: "degraded",
                case_id: "case-index-001",
                case_lifecycle_state: "open",
                reviewed_context: {
                  source: {
                    source_family: "github_audit",
                  },
                },
                external_ticket_reference: {
                  status: "missing_anchor",
                },
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/alerts", dependencies);

      expect(
        await screen.findByRole("heading", { name: "Alerts" }),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          /This route exists so later adapter and page work can land/i,
        ),
      ).not.toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "alert-index-001" }),
      ).toHaveAttribute("href", "/operator/alerts/alert-index-001");
      expect(
        screen.getByRole("link", { name: "case-index-001" }),
      ).toHaveAttribute("href", "/operator/cases/case-index-001");
      expect(screen.getByText("github_audit")).toBeInTheDocument();
      expect(screen.getByText("degraded")).toBeInTheDocument();
      expect(
        screen.getByText("Review state remains degraded."),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Non-authoritative coordination reference is missing_anchor.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /promote/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /record/i }),
      ).not.toBeInTheDocument();
    });

    it("renders an empty read-only case drilldown index instead of the placeholder case page", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-analyst-queue": {
            queue_name: "analyst_review",
            read_only: true,
            records: [
              {
                alert_id: "alert-without-case",
                review_state: "new",
                reviewed_context: {
                  source: {
                    source_family: "wazuh",
                  },
                },
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/cases", dependencies);

      expect(
        await screen.findByRole("heading", { name: "Cases" }),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          /This route exists so later adapter and page work can land/i,
        ),
      ).not.toBeInTheDocument();
      expect(
        screen.getByText(
          "No case anchors are currently visible in the analyst queue.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "Back to queue" }),
      ).toHaveAttribute("href", "/operator/queue");
      expect(
        screen.queryByRole("button", { name: /record observation/i }),
      ).not.toBeInTheDocument();
    });

    it("renders provenance landing as a bounded record-chain index", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-analyst-queue": {
            queue_name: "analyst_review",
            read_only: true,
            records: [
              {
                alert_id: "alert-prov-001",
                review_state: "triaged",
                case_id: "case-prov-001",
                reviewed_context: {
                  source: {
                    source_family: "microsoft_365_audit",
                  },
                },
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/provenance/cases", dependencies);

      expect(
        await screen.findByRole("heading", { name: "Provenance" }),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(
          /This route exists so later adapter and page work can land/i,
        ),
      ).not.toBeInTheDocument();
      expect(
        screen.getByText("Record-chain drilldown index"),
      ).toBeInTheDocument();
      expect(screen.getByText("case-prov-001")).toBeInTheDocument();
      expect(screen.getByText("alert-prov-001")).toBeInTheDocument();
      expect(screen.getByText("microsoft_365_audit")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "Open provenance" }),
      ).toHaveAttribute("href", "/operator/provenance/cases/case-prov-001");
      expect(
        screen.queryByRole("button", { name: /approve/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /execute/i }),
      ).not.toBeInTheDocument();
    });
  });
}
