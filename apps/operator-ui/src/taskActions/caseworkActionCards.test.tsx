import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminContext } from "react-admin";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { createOperatorTaskActionClient } from "./taskActionClient";
import {
  CreateReviewedActionRequestCard,
  PromoteAlertToCaseCard,
  RecordActionReviewEscalationNoteCard,
  RecordActionReviewManualFallbackCard,
  RecordCaseLeadCard,
  RecordCaseObservationCard,
  RecordCaseRecommendationCard,
} from "./caseworkActionCards";
import { TaskActionClientProvider } from "./taskActionPrimitives";

const testDataProvider = {
  create: vi.fn(),
  delete: vi.fn(),
  deleteMany: vi.fn(),
  getList: vi.fn(),
  getMany: vi.fn(),
  getManyReference: vi.fn(),
  getOne: vi.fn(),
  update: vi.fn(),
  updateMany: vi.fn(),
};

function renderWithTaskActionProviders(ui: ReactNode) {
  return render(
    <AdminContext dataProvider={testDataProvider}>
      <TaskActionClientProvider
        client={createOperatorTaskActionClient({ fetchFn: vi.fn<typeof fetch>() })}
      >
        {ui}
      </TaskActionClientProvider>
    </AdminContext>,
  );
}

function PromoteAlertCardHarness({
  alertId,
  currentCaseId,
}: {
  alertId: string;
  currentCaseId: string | null;
}) {
  return (
    <PromoteAlertToCaseCard
      alertId={alertId}
      currentCaseId={currentCaseId}
      key={alertId}
      operatorIdentity="analyst@example.com"
    />
  );
}

function CaseworkCardsHarness({
  actionRequestId,
  caseId,
  linkedEvidenceIds,
  linkedLeadIds,
  linkedObservationIds,
  linkedRecommendationIds,
}: {
  actionRequestId: string;
  caseId: string;
  linkedEvidenceIds: string[];
  linkedLeadIds: string[];
  linkedObservationIds: string[];
  linkedRecommendationIds: string[];
}) {
  return (
    <>
      <RecordCaseObservationCard
        caseId={caseId}
        key={`observation-${caseId}`}
        linkedEvidenceIds={linkedEvidenceIds}
        operatorIdentity="analyst@example.com"
      />
      <RecordCaseLeadCard
        caseId={caseId}
        key={`lead-${caseId}`}
        linkedObservationIds={linkedObservationIds}
        operatorIdentity="analyst@example.com"
      />
      <RecordCaseRecommendationCard
        caseId={caseId}
        key={`recommendation-${caseId}`}
        linkedLeadIds={linkedLeadIds}
        operatorIdentity="analyst@example.com"
      />
      <CreateReviewedActionRequestCard
        caseId={caseId}
        key={`action-request-${caseId}`}
        linkedRecommendationIds={linkedRecommendationIds}
        operatorIdentity="analyst@example.com"
      />
      <RecordActionReviewManualFallbackCard
        actionRequestId={actionRequestId}
        caseId={caseId}
        key={`manual-fallback-${caseId}-${actionRequestId}`}
        linkedEvidenceIds={linkedEvidenceIds}
        nextExpectedAction="await_manual_follow_up"
        operatorIdentity="analyst@example.com"
        reviewState="unresolved"
      />
      <RecordActionReviewEscalationNoteCard
        actionRequestId={actionRequestId}
        caseId={caseId}
        key={`escalation-note-${caseId}-${actionRequestId}`}
        nextExpectedAction="await_manual_follow_up"
        operatorIdentity="analyst@example.com"
        reviewState="unresolved"
      />
    </>
  );
}

describe("caseworkActionCards", () => {
  it("resets promote draft state when the bound alert id changes", async () => {
    const user = userEvent.setup();
    const { rerender } = renderWithTaskActionProviders(
      <PromoteAlertCardHarness alertId="alert-123" currentCaseId={null} />,
    );

    await user.type(
      screen.getByRole("textbox", { name: "Case id override" }),
      "case-stale",
    );
    expect(screen.getByRole("textbox", { name: "Case id override" })).toHaveValue(
      "case-stale",
    );

    rerender(
      <AdminContext dataProvider={testDataProvider}>
        <TaskActionClientProvider
          client={createOperatorTaskActionClient({ fetchFn: vi.fn<typeof fetch>() })}
        >
          <PromoteAlertCardHarness alertId="alert-456" currentCaseId="case-456" />
        </TaskActionClientProvider>
      </AdminContext>,
    );

    expect(screen.getByRole("textbox", { name: "Case id override" })).toHaveValue("");
    expect(screen.getByText("alert-456")).toBeInTheDocument();
  });

  it("resets observation, lead, and recommendation drafts when the bound case id changes", async () => {
    const user = userEvent.setup();
    const { rerender } = renderWithTaskActionProviders(
      <CaseworkCardsHarness
        actionRequestId="action-request-456"
        caseId="case-456"
        linkedEvidenceIds={["evidence-123"]}
        linkedLeadIds={["lead-123"]}
        linkedObservationIds={["observation-123"]}
        linkedRecommendationIds={["recommendation-123"]}
      />,
    );

    await user.type(screen.getByRole("textbox", { name: "Observed at" }), "2026");
    await user.type(screen.getByRole("textbox", { name: "Scope statement" }), "scope");
    await user.clear(screen.getByRole("textbox", { name: "Supporting evidence ids" }));
    await user.type(
      screen.getByRole("textbox", { name: "Supporting evidence ids" }),
      "stale-evidence",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Observation id" }),
      "stale-observation",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Triage rationale" }),
      "stale-rationale",
    );
    await user.type(screen.getByRole("textbox", { name: "Lead id" }), "stale-lead");
    await user.type(
      screen.getByRole("textbox", { name: "Intended outcome" }),
      "stale-outcome",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Recommendation id" }),
      "stale-recommendation",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Recipient identity" }),
      "owner-stale@example.com",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Message intent" }),
      "stale-intent",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Escalation reason" }),
      "stale-escalation",
    );
    await user.type(screen.getByRole("textbox", { name: "Expires at" }), "2026-05");
    await user.type(
      screen.getByRole("textbox", { name: "Action request id override" }),
      "stale-request",
    );
    await user.type(screen.getByRole("textbox", { name: "Fallback at" }), "2026-04");
    await user.type(screen.getByRole("textbox", { name: "Reason" }), "stale-reason");
    await user.type(
      screen.getByRole("textbox", { name: "Action taken" }),
      "stale-action",
    );
    await user.clear(
      screen.getByRole("textbox", { name: "Verification evidence ids" }),
    );
    await user.type(
      screen.getByRole("textbox", { name: "Verification evidence ids" }),
      "stale-evidence-list",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Residual uncertainty" }),
      "stale-uncertainty",
    );
    await user.type(screen.getByRole("textbox", { name: "Escalated at" }), "2026-04");
    await user.type(screen.getByRole("textbox", { name: "Escalated to" }), "stale-manager");
    await user.type(screen.getByRole("textbox", { name: "Note" }), "stale-note");

    rerender(
      <AdminContext dataProvider={testDataProvider}>
        <TaskActionClientProvider
          client={createOperatorTaskActionClient({ fetchFn: vi.fn<typeof fetch>() })}
        >
          <CaseworkCardsHarness
            actionRequestId="action-request-789"
            caseId="case-789"
            linkedEvidenceIds={["evidence-789"]}
            linkedLeadIds={["lead-789"]}
            linkedObservationIds={["observation-789"]}
            linkedRecommendationIds={["recommendation-789"]}
          />
        </TaskActionClientProvider>
      </AdminContext>,
    );

    expect(screen.getByRole("textbox", { name: "Observed at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Scope statement" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Supporting evidence ids" })).toHaveValue(
      "evidence-789",
    );
    expect(screen.getByRole("textbox", { name: "Observation id" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Triage rationale" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Lead id" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Intended outcome" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Recommendation id" })).toHaveValue(
      "recommendation-789",
    );
    expect(screen.getByRole("textbox", { name: "Recipient identity" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Message intent" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Escalation reason" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Expires at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Action request id override" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Fallback at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Reason" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Action taken" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Verification evidence ids" })).toHaveValue(
      "evidence-789",
    );
    expect(screen.getByRole("textbox", { name: "Residual uncertainty" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Escalated at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Escalated to" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Note" })).toHaveValue("");
    expect(screen.getByText("Known observation ids: observation-789")).toBeInTheDocument();
    expect(screen.getByText("Known lead ids: lead-789")).toBeInTheDocument();
    expect(screen.getByText("Known recommendation ids: recommendation-789")).toBeInTheDocument();
  }, 10000);
});
