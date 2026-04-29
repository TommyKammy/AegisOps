import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesActionReviewAccessTests() {
  describe("action review access routes", () => {
    it("shows an explicit forbidden outcome for analyst-only action-review landing routes", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({}),
      });

      renderOperatorRoute("/operator/action-review", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Access denied" }),
        ).toBeInTheDocument();
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

      renderOperatorRoute(
        "/operator/action-review/action-request-123",
        dependencies,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
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
          initialEntries={[
            "/reviewed-operator/action-review/action-request-123",
          ]}
        >
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Action Review" }),
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByRole("heading", { name: "Access denied" }),
      ).not.toBeInTheDocument();
      expect(
        screen.getByText(
          "The current reviewed session can inspect this record but cannot submit approval decisions without approver role authority.",
        ),
      ).toBeInTheDocument();
    });
  });
}
