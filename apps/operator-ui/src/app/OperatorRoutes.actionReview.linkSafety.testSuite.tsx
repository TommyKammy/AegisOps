import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionReviewLinkSafetyTests() {
  describe("action review link safety routes", () => {
    it("sanitizes bounded external-link logging so secret-like URL suffixes stay out of the UI event log", async () => {
      const user = userEvent.setup();
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
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
          },
          {
            identity: "approver@example.com",
            provider: "authentik",
            roles: ["Approver"],
            subject: "operator-8",
          },
        ),
      });

      renderOperatorRoute(
        "/operator/action-review/action-request-246",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("link", {
          name: "Open downstream coordination reference",
        }),
      );

      expect(
        screen.queryByText(/query-secret|super-secret-token/),
      ).not.toBeInTheDocument();

      const eventLogHeading = screen.getByRole("heading", {
        name: "Reviewed UI event log",
      });
      const eventLogCard = eventLogHeading.closest(".MuiCard-root");
      expect(eventLogCard).not.toBeNull();
      const eventLog = within(eventLogCard as HTMLElement);
      expect(eventLog.getByText("External open")).toBeInTheDocument();
      expect(
        eventLog.getByText("Open downstream coordination reference"),
      ).toBeInTheDocument();
      expect(
        eventLog.getByText(
          "Target: https://tickets.example.invalid/incidents/246/<redacted-path-suffix>",
        ),
      ).toBeInTheDocument();
      expect(
        eventLogCard,
      ).not.toHaveTextContent(/query-secret|super-secret-token/);
    });

    it("keeps unsafe coordination reference schemes non-clickable", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch(
          {
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
          },
          {
            identity: "approver@example.com",
            provider: "authentik",
            roles: ["Approver"],
            subject: "operator-8",
          },
        ),
      });

      renderOperatorRoute(
        "/operator/action-review/action-request-unsafe-link",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("link", {
          name: "Open downstream coordination reference",
        }),
      ).not.toBeInTheDocument();
      expect(
        screen.getByText(
          "Downstream coordination reference: javascript:alert('ticket')",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByText("External open")).not.toBeInTheDocument();
    });
  });
}
