import { expect, type Page, type Route, test } from "@playwright/test";

const defaultSession = {
  identity: "analyst@example.com",
  provider: "authentik",
  roles: ["Analyst"],
  subject: "operator-7",
};

const defaultReadiness = {
  metrics: {
    optional_extensions: {
      overall_state: "ready",
      tracked_extensions: 4,
      extensions: {
        assistant: {
          authority_mode: "advisory_only",
          availability: "available",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "ready",
          reason: "bounded_reviewed_summary_provider_available",
        },
        endpoint_evidence: {
          authority_mode: "augmenting_evidence",
          availability: "unavailable",
          enablement: "disabled_by_default",
          mainline_dependency: "non_blocking",
          readiness: "not_applicable",
          reason: "isolated_executor_runtime_not_configured",
        },
        network_evidence: {
          authority_mode: "augmenting_evidence",
          availability: "unavailable",
          enablement: "disabled_by_default",
          mainline_dependency: "non_blocking",
          readiness: "not_applicable",
          reason: "reviewed_network_evidence_extension_not_activated",
        },
        ml_shadow: {
          authority_mode: "shadow_only",
          availability: "available",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "degraded",
          reason: "reviewed_ml_shadow_extension_provider_lagging",
        },
      },
    },
  },
  status: "ready",
};

const queuePayload = {
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
      current_action_review: {
        review_state: "pending",
      },
    },
  ],
  total_records: 1,
};

const actionReviewPayload = {
  action_request_id: "action-request-123",
  read_only: true,
  action_review: {
    action_request_id: "action-request-123",
    action_request_state: "pending_approval",
    approval_state: "pending",
    review_state: "pending",
    action_execution_state: "not_started",
    reconciliation_state: "not_started",
    requester_identity: "analyst@example.com",
    recipient_identity: "security-team@example.com",
    message_intent: "notify",
    next_expected_action: "await_approver_decision",
    timeline: [
      {
        label: "Action request",
        state: "pending_approval",
      },
    ],
  },
  current_action_review: {
    action_request_id: "action-request-123",
    review_state: "pending",
  },
  case_record: {
    case_id: "case-456",
    lifecycle_state: "open",
  },
  alert_record: {
    alert_id: "alert-789",
    lifecycle_state: "open",
  },
};

function fulfillJson(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    body: JSON.stringify(body),
    contentType: "application/json",
    status,
  });
}

async function stubOperatorBackend(
  page: Page,
  options: {
    session?: unknown;
    sessionStatus?: number;
  } = {},
) {
  await page.route("**/api/operator/session", (route) =>
    fulfillJson(
      route,
      options.session ?? defaultSession,
      options.sessionStatus ?? 200,
    ),
  );
  await page.route("**/diagnostics/readiness?**", (route) =>
    fulfillJson(route, defaultReadiness),
  );
  await page.route("**/inspect-analyst-queue?**", (route) =>
    fulfillJson(route, queuePayload),
  );
  await page.route("**/inspect-action-review?**", (route) =>
    fulfillJson(route, actionReviewPayload),
  );
}

test("unauthenticated protected deep links preserve a bounded return path without rendering shell data", async ({
  page,
}) => {
  await stubOperatorBackend(page, { sessionStatus: 401 });

  await page.goto("/operator/queue?focus=degraded#summary");

  await expect(
    page.getByRole("heading", { name: "Operator Sign-In" }),
  ).toBeVisible();
  await expect(
    page.getByText("Return path: /operator/queue?focus=degraded#summary"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Analyst Queue" }),
  ).toHaveCount(0);
});

test("role gating blocks analyst browser navigation to action review collection routes", async ({
  page,
}) => {
  await stubOperatorBackend(page);

  await page.goto("/operator/action-review");

  await expect(page.getByRole("heading", { name: "Access denied" })).toBeVisible();
  await expect(page).toHaveURL(/\/operator\/forbidden$/);
  await expect(page.getByRole("heading", { name: "Action Review" })).toHaveCount(0);
});

test("operator workflows render degraded queue state and approver action-review detail from backend records", async ({
  page,
}) => {
  await stubOperatorBackend(page, {
    session: {
      identity: "approver@example.com",
      provider: "authentik",
      roles: ["Approver"],
      subject: "operator-8",
    },
  });

  await page.goto("/operator/queue");

  await expect(page.getByRole("heading", { name: "Analyst Queue" })).toBeVisible();
  await expect(page.getByRole("link", { name: "alert-789" })).toBeVisible();
  await expect(page.getByText("Review: degraded").first()).toBeVisible();
  await expect(page.getByText("No case anchor")).toBeVisible();
  await expect(
    page.getByText("Review state remains degraded."),
  ).toBeVisible();
  await expect(
    page.getByText("Non-authoritative coordination reference is missing_anchor."),
  ).toBeVisible();

  await page.goto("/operator/action-review/action-request-123");

  await expect(page.getByRole("heading", { name: "Action Review" })).toBeVisible();
  await expect(page.getByText("Action request id").first()).toBeVisible();
  await expect(page.getByText("action-request-123").first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Record approval decision" }),
  ).toBeVisible();
});
