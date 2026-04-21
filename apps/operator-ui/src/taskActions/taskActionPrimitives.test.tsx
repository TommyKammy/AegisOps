import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AdminContext } from "react-admin";
import {
  createOperatorTaskActionClient,
  OperatorTaskActionError,
} from "./taskActionClient";
import {
  TaskActionClientProvider,
  TaskActionFormCard,
  useTaskActionSubmission,
} from "./taskActionPrimitives";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

function TestTaskActionForm() {
  const submission = useTaskActionSubmission<{ case_id: string }>();

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          refreshTargets: (acknowledgement) => [
            {
              id: acknowledgement.case_id,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordCaseObservation({
              author_identity: "analyst@example.com",
              case_id: "case-123",
              observed_at: "2026-04-22T00:00:00+00:00",
              scope_statement: "Reviewed scoped observation",
              supporting_evidence_ids: ["evidence-123"],
            }) as Promise<{ case_id: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", "analyst@example.com"],
          ["Role", "Analyst"],
        ]}
        binding={[
          ["Record family", "case"],
          ["Record id", "case-123"],
        ]}
        provenance={[
          ["Source", "reviewed case detail"],
          ["Scope", "observation append"],
        ]}
        submission={submission}
        submitLabel="Record observation"
        subtitle="Shared bounded task-action framing keeps actor, binding, and authoritative reread explicit."
        title="Record case observation"
      >
        <div>Observation body</div>
      </TaskActionFormCard>
    </form>
  );
}

describe("taskActionPrimitives", () => {
  it("submits through the bounded task-action client and re-reads authoritative state", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({ case_id: "case-123", observation_id: "observation-123" }),
    );
    const dataProvider = {
      create: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
      getList: vi.fn(),
      getMany: vi.fn(),
      getManyReference: vi.fn(),
      getOne: vi.fn().mockResolvedValue({
        data: {
          case_id: "case-123",
          current_action_review: {
            review_state: "pending",
          },
          id: "case-123",
        },
      }),
      update: vi.fn(),
      updateMany: vi.fn(),
    };
    const user = userEvent.setup();

    render(
      <AdminContext dataProvider={dataProvider}>
        <TaskActionClientProvider
          client={createOperatorTaskActionClient({ fetchFn })}
        >
          <TestTaskActionForm />
        </TaskActionClientProvider>
      </AdminContext>,
    );

    const submitButton = screen.getByRole("button", {
      name: "Record observation",
    });
    expect(submitButton).toBeDisabled();

    await user.click(screen.getByRole("checkbox"));
    expect(submitButton).toBeEnabled();
    await user.click(submitButton);

    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-case-observation",
        expect.objectContaining({
          body: JSON.stringify({
            author_identity: "analyst@example.com",
            case_id: "case-123",
            observed_at: "2026-04-22T00:00:00+00:00",
            scope_statement: "Reviewed scoped observation",
            supporting_evidence_ids: ["evidence-123"],
          }),
          method: "POST",
        }),
      );
    });

    await waitFor(() => {
      expect(dataProvider.getOne).toHaveBeenCalledWith("cases", {
        id: "case-123",
        meta: undefined,
      });
    });

    expect(
      await screen.findByText(
        "Authoritative refresh completed from the reviewed backend record. Refreshed: Case detail.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps uncertainty explicit when the authoritative reread fails after submit", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({ case_id: "case-123", observation_id: "observation-123" }),
    );
    const dataProvider = {
      create: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
      getList: vi.fn(),
      getMany: vi.fn(),
      getManyReference: vi.fn(),
      getOne: vi.fn().mockRejectedValue(new Error("Case reread unavailable.")),
      update: vi.fn(),
      updateMany: vi.fn(),
    };
    const user = userEvent.setup();

    render(
      <AdminContext dataProvider={dataProvider}>
        <TaskActionClientProvider
          client={createOperatorTaskActionClient({ fetchFn })}
        >
          <TestTaskActionForm />
        </TaskActionClientProvider>
      </AdminContext>,
    );

    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Record observation" }));

    expect(
      await screen.findByText(
        /Authoritative re-read did not complete after submit\. Treat the result as unresolved until the reviewed record is refreshed\./i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Case reread unavailable\./i)).toBeInTheDocument();
  });

  it("classifies conflict submit failures without implying success", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          error: "conflict",
          message: "Action is stale against the reviewed backend record.",
        },
        409,
      ),
    );

    await expect(
      createOperatorTaskActionClient({ fetchFn }).recordCaseObservation({
        author_identity: "analyst@example.com",
        case_id: "case-123",
        observed_at: "2026-04-22T00:00:00+00:00",
        scope_statement: "Reviewed scoped observation",
        supporting_evidence_ids: ["evidence-123"],
      }),
    ).rejects.toMatchObject({
      code: "conflict",
      message: "Action is stale against the reviewed backend record.",
      status: 409,
    } satisfies Partial<OperatorTaskActionError>);
  });
});
