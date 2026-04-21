import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminContext } from "react-admin";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { createOperatorTaskActionClient } from "./taskActionClient";
import {
  PromoteAlertToCaseCard,
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
  caseId,
  linkedEvidenceIds,
  linkedLeadIds,
  linkedObservationIds,
}: {
  caseId: string;
  linkedEvidenceIds: string[];
  linkedLeadIds: string[];
  linkedObservationIds: string[];
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
        caseId="case-456"
        linkedEvidenceIds={["evidence-123"]}
        linkedLeadIds={["lead-123"]}
        linkedObservationIds={["observation-123"]}
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

    rerender(
      <AdminContext dataProvider={testDataProvider}>
        <TaskActionClientProvider
          client={createOperatorTaskActionClient({ fetchFn: vi.fn<typeof fetch>() })}
        >
          <CaseworkCardsHarness
            caseId="case-789"
            linkedEvidenceIds={["evidence-789"]}
            linkedLeadIds={["lead-789"]}
            linkedObservationIds={["observation-789"]}
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
    expect(screen.getByText("Known observation ids: observation-789")).toBeInTheDocument();
    expect(screen.getByText("Known lead ids: lead-789")).toBeInTheDocument();
  });
});
