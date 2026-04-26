import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminContext } from "react-admin";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { createOperatorTaskActionClient } from "./taskActionClient";
import {
  CreateReviewedActionRequestCard,
  PromoteAlertToCaseCard,
  RecordActionApprovalDecisionCard,
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

function setTextboxValue(name: string, value: string) {
  fireEvent.change(screen.getByRole("textbox", { name }), {
    target: { value },
  });
}

function renderCaseworkResetHarness() {
  return renderWithTaskActionProviders(
    <CaseworkCardsHarness
      actionRequestId="action-request-456"
      actionRequestState="pending_approval"
      approvalState="pending"
      caseId="case-456"
      decisionRationale="Pending review"
      expiresAt="2026-05-01T00:00:00Z"
      linkedEvidenceIds={["evidence-123"]}
      linkedLeadIds={["lead-123"]}
      linkedObservationIds={["observation-123"]}
      linkedRecommendationIds={["recommendation-123"]}
    />,
  );
}

function rerenderCaseworkResetHarness(rerender: ReturnType<typeof render>["rerender"]) {
  rerender(
    <AdminContext dataProvider={testDataProvider}>
      <TaskActionClientProvider
        client={createOperatorTaskActionClient({ fetchFn: vi.fn<typeof fetch>() })}
      >
        <CaseworkCardsHarness
          actionRequestId="action-request-789"
          actionRequestState="granted"
          approvalState="approved"
          caseId="case-789"
          decisionRationale="Already granted"
          expiresAt="2026-06-01T00:00:00Z"
          linkedEvidenceIds={["evidence-789"]}
          linkedLeadIds={["lead-789"]}
          linkedObservationIds={["observation-789"]}
          linkedRecommendationIds={["recommendation-789"]}
        />
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
  approvalState,
  caseId,
  decisionRationale,
  expiresAt,
  linkedEvidenceIds,
  linkedLeadIds,
  linkedObservationIds,
  linkedRecommendationIds,
  actionRequestState,
}: {
  actionRequestId: string;
  actionRequestState: string | null;
  approvalState: string | null;
  caseId: string;
  decisionRationale: string | null;
  expiresAt: string | null;
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
      <RecordActionApprovalDecisionCard
        actionRequestId={actionRequestId}
        actionRequestState={actionRequestState}
        approvalState={approvalState}
        approverIdentity="approver@example.com"
        decisionRationale={decisionRationale}
        expiresAt={expiresAt}
        key={`approval-decision-${actionRequestId}`}
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
  it("renders task-oriented metadata for promote, casework, action-request, and fallback flows", () => {
    renderWithTaskActionProviders(
      <>
        <PromoteAlertCardHarness alertId="alert-123" currentCaseId="case-123" />
        <CaseworkCardsHarness
          actionRequestId="action-request-456"
          actionRequestState="pending_approval"
          approvalState="pending"
          decisionRationale="Pending review"
          caseId="case-456"
          expiresAt="2026-05-01T00:00:00Z"
          linkedEvidenceIds={["evidence-123"]}
          linkedLeadIds={["lead-123"]}
          linkedObservationIds={["observation-123"]}
          linkedRecommendationIds={["recommendation-123"]}
        />
      </>,
    );

    for (const title of [
      "Promote alert into case",
      "Record case observation",
      "Record case lead",
      "Record case recommendation",
      "Create reviewed action request",
      "Record approval decision",
      "Record manual fallback",
      "Record escalation note",
    ]) {
      expect(screen.getAllByText(title).length).toBeGreaterThan(0);
    }

    for (const text of [
      "reviewed operator promote endpoint",
      "reviewed operator observation endpoint",
      "reviewed operator lead endpoint",
      "reviewed operator recommendation endpoint",
      "reviewed operator action-request endpoint",
      "reviewed operator approval-decision endpoint",
      "reviewed operator manual-fallback endpoint",
      "reviewed operator escalation-note endpoint",
      "Current review state",
      "Next expected action",
      "Action request id",
      "Recommendation id",
    ]) {
      expect(screen.getAllByText(text).length).toBeGreaterThan(0);
    }
  });

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
    const { rerender } = renderCaseworkResetHarness();

    setTextboxValue("Observed at", "2026");
    setTextboxValue("Scope statement", "scope");
    setTextboxValue("Supporting evidence ids", "stale-evidence");
    setTextboxValue("Observation id", "stale-observation");
    setTextboxValue("Triage rationale", "stale-rationale");
    setTextboxValue("Lead id", "stale-lead");
    setTextboxValue("Intended outcome", "stale-outcome");
    setTextboxValue("Recommendation id", "stale-recommendation");

    rerenderCaseworkResetHarness(rerender);

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
    expect(screen.getByText("Known observation ids: observation-789")).toBeInTheDocument();
    expect(screen.getByText("Known lead ids: lead-789")).toBeInTheDocument();
    expect(screen.getByText("Known recommendation ids: recommendation-789")).toBeInTheDocument();
  }, 15000);

  it("resets action request and approval drafts when the bound case id changes", async () => {
    const { rerender } = renderCaseworkResetHarness();

    setTextboxValue("Recipient identity", "owner-stale@example.com");
    setTextboxValue("Message intent", "stale-intent");
    setTextboxValue("Escalation reason", "stale-escalation");
    setTextboxValue("Expires at", "2026-05");
    setTextboxValue("Action request id override", "stale-request");
    setTextboxValue("Decided at", "2026-04");
    setTextboxValue("Decision rationale", "stale-decision-rationale");

    rerenderCaseworkResetHarness(rerender);

    expect(screen.getByRole("textbox", { name: "Recipient identity" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Message intent" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Escalation reason" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Expires at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Action request id override" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Decided at" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Decision rationale" })).toHaveValue(
      "Already granted",
    );
  }, 15000);

  it("resets manual follow-up drafts when the bound case id changes", async () => {
    const { rerender } = renderCaseworkResetHarness();

    setTextboxValue("Fallback at", "2026-04");
    setTextboxValue("Reason", "stale-reason");
    setTextboxValue("Action taken", "stale-action");
    setTextboxValue("Verification evidence ids", "stale-evidence-list");
    setTextboxValue("Residual uncertainty", "stale-uncertainty");
    setTextboxValue("Escalated at", "2026-04");
    setTextboxValue("Escalated to", "stale-manager");
    setTextboxValue("Note", "stale-note");

    rerenderCaseworkResetHarness(rerender);

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
  }, 15000);
});
