import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import { createAuthorizedFetch } from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesAssistantTests() {
  describe("assistant routes", () => {
    it("renders a case-anchored assistant advisory route from reviewed advisory output", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "case",
            record_id: "case-456",
            output_kind: "case_summary",
            status: "ready",
            summary:
              "Repository owner membership drift remains bounded to the reviewed case scope.",
            citations: ["case-456", "alert-123", "evidence-123"],
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/case/case-456"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            "Repository owner membership drift remains bounded to the reviewed case scope.",
          ),
        ).toBeInTheDocument();
      });

      expect(screen.getAllByText("case-456").length).toBeGreaterThan(0);
      expect(screen.getByRole("link", { name: "Open case detail" })).toBeInTheDocument();
      expect(screen.getByText(/Output: case_summary/i)).toBeInTheDocument();
      expect(screen.getByText(/Status: ready/i)).toBeInTheDocument();
      expect(screen.getByText("evidence-123")).toBeInTheDocument();
    });

    it("keeps no-authority semantics explicit for cited advisory output without a recommendation draft", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "case",
            record_id: "case-456",
            output_kind: "case_summary",
            status: "ready",
            cited_summary: {
              text: "The reviewed case remains open while the assistant summary stays advisory-only.",
              citations: ["case-456", "alert-123"],
            },
            uncertainty_flags: ["advisory_only"],
            citations: ["case-456", "alert-123"],
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/case/case-456"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(await screen.findByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: "Recommendation draft" })).not.toBeInTheDocument();

      const anchorSection = screen.getByRole("heading", { name: "Authoritative advisory anchor" });
      const anchorCard = anchorSection.closest(".MuiCard-root");
      expect(anchorCard).not.toBeNull();
      expect(within(anchorCard as HTMLElement).getByText("Read only")).toBeInTheDocument();
      expect(within(anchorCard as HTMLElement).getByText("true")).toBeInTheDocument();
      expect(
        within(anchorCard as HTMLElement).getByText(
          /Assistant output does not approve, execute, or reconcile workflow state\./i,
        ),
      ).toBeInTheDocument();
    });

    it("renders cited recommendation draft output with explicit assistant-only framing", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "recommendation",
            record_id: "recommendation-123",
            output_kind: "recommendation_draft",
            status: "ready",
            cited_summary: {
              text: "The assistant draft stays anchored to the cited evidence before any reviewed action.",
              citations: ["recommendation-123", "evidence-123", "case-456"],
            },
            candidate_recommendations: [
              {
                text: "Proposal only: confirm the repository ownership change before raising an action request.",
                citations: ["evidence-123", "case-456"],
              },
            ],
            uncertainty_flags: ["advisory_only"],
            citations: ["recommendation-123", "evidence-123", "case-456"],
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/recommendation/recommendation-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      const citedOutputSection = await screen.findByRole("heading", { name: "Cited advisory output" });
      const citedOutputCard = citedOutputSection.closest(".MuiCard-root");
      expect(citedOutputCard).not.toBeNull();
      expect(
        within(citedOutputCard as HTMLElement).getByText(
          "The assistant draft stays anchored to the cited evidence before any reviewed action.",
        ),
      ).toBeInTheDocument();
      expect(within(citedOutputCard as HTMLElement).getByText("recommendation-123")).toBeInTheDocument();
      expect(within(citedOutputCard as HTMLElement).getByText("evidence-123")).toBeInTheDocument();
      expect(within(citedOutputCard as HTMLElement).getByText("case-456")).toBeInTheDocument();

      const draftSection = screen.getByRole("heading", { name: "Recommendation draft" });
      const draftCard = draftSection.closest(".MuiCard-root");
      expect(draftCard).not.toBeNull();
      expect(within(draftCard as HTMLElement).getByText("Draft only")).toBeInTheDocument();
      expect(
        within(draftCard as HTMLElement).getByText(
          "Proposal only: confirm the repository ownership change before raising an action request.",
        ),
      ).toBeInTheDocument();
      expect(
        within(draftCard as HTMLElement).getByText(
          "Assistant output does not approve, execute, or reconcile workflow state.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", { name: "Advisory failure visibility" }),
      ).not.toBeInTheDocument();
    });

    it("keeps fallback advisory summary fields out of the detail table", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "recommendation",
            record_id: "recommendation-123",
            output_kind: "recommendation_summary",
            status: "ready",
            cited_summary: {
              citations: ["recommendation-123", "evidence-123"],
            },
            message: "Use the reviewed recommendation as bounded advisory context.",
            advisory_text: "This fallback field should not be repeated in detail rows.",
            supporting_note: "Analyst follow-up remains separate from advisory prose.",
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/recommendation/recommendation-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(
        await screen.findByText("Use the reviewed recommendation as bounded advisory context."),
      ).toBeInTheDocument();

      const citedOutputSection = await screen.findByRole("heading", { name: "Cited advisory output" });
      const citedOutputCard = citedOutputSection.closest(".MuiCard-root");
      expect(citedOutputCard).not.toBeNull();
      expect(
        within(citedOutputCard as HTMLElement).getByText(
          "No cited summary anchors were returned for this advisory output.",
        ),
      ).toBeInTheDocument();
      expect(within(citedOutputCard as HTMLElement).queryByText("recommendation-123")).not.toBeInTheDocument();
      expect(within(citedOutputCard as HTMLElement).queryByText("evidence-123")).not.toBeInTheDocument();

      const detailTable = screen.getByRole("table");
      expect(within(detailTable).queryByText("Message")).not.toBeInTheDocument();
      expect(within(detailTable).queryByText("Output Text")).not.toBeInTheDocument();
      expect(within(detailTable).queryByText("Advisory Text")).not.toBeInTheDocument();
      expect(within(detailTable).getByText("Supporting Note")).toBeInTheDocument();
      expect(
        within(detailTable).getByText(
          "Analyst follow-up remains separate from advisory prose.",
        ),
      ).toBeInTheDocument();
    });

    it("renders explicit citation-failure and reviewed-context visibility for unresolved advisory output", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "case",
            record_id: "case-456",
            output_kind: "case_summary",
            status: "unresolved",
            cited_summary: {
              text: "Case summary case-456 remains unresolved because citation completeness or reviewed-context consistency is incomplete.",
              citations: ["case-456"],
            },
            key_observations: [
              {
                text: "Reviewed context exposes stable identifiers for the cited advisory output.",
                citations: [
                  "reviewed_context.asset.asset_id=asset-123",
                  "reviewed_context.identity.user_id=user-456",
                ],
              },
            ],
            unresolved_questions: [
              {
                text: "Which reviewed records, linked evidence, or stable reviewed-context identifiers support this advisory output?",
                citations: ["case-456"],
              },
              {
                text: "Which reviewed-context values are authoritative for: identity.user_id?",
                citations: ["case-456", "alert-123"],
              },
            ],
            uncertainty_flags: [
              "advisory_only",
              "missing_supporting_citations",
              "conflicting_reviewed_context",
            ],
            citations: ["case-456", "alert-123"],
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/case/case-456"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(await screen.findByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
      expect(await screen.findByRole("heading", { name: "Advisory failure visibility" })).toBeInTheDocument();
      expect(
        screen.getByText(/Missing citation support is visible here/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Conflicting reviewed context remains visible here/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Assistant advisory remains unresolved because required citation or reviewed-context checks failed.",
        ),
      ).toBeInTheDocument();

      const contextSection = screen.getByRole("heading", { name: "Assistant context explorer" });
      const contextCard = contextSection.closest(".MuiCard-root");
      expect(contextCard).not.toBeNull();
      expect(
        within(contextCard as HTMLElement).getByText(
          "Reviewed context exposes stable identifiers for the cited advisory output.",
        ),
      ).toBeInTheDocument();
      expect(
        within(contextCard as HTMLElement).getByText(
          "Which reviewed records, linked evidence, or stable reviewed-context identifiers support this advisory output?",
        ),
      ).toBeInTheDocument();
      expect(
        within(contextCard as HTMLElement).getByText(
          "reviewed_context.asset.asset_id=asset-123",
        ),
      ).toBeInTheDocument();
    });

    it("renders provider-degraded advisory visibility for unresolved assistant output", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-advisory-output": {
            read_only: true,
            record_family: "recommendation",
            record_id: "recommendation-789",
            output_kind: "recommendation_draft",
            status: "unresolved",
            cited_summary: {
              text: "Reviewed recommendation recommendation-789 remains bounded to the last trusted summary.",
              citations: ["recommendation-789", "case-456"],
            },
            unresolved_questions: [
              {
                text: "Which reviewed provider result, retry evidence, or citation repair resolves this advisory failure?",
                citations: ["recommendation-789", "ai-trace-789"],
              },
            ],
            uncertainty_flags: ["advisory_only", "provider_generation_failed"],
            citations: ["recommendation-789", "case-456", "ai-trace-789"],
          },
        }),
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/recommendation/recommendation-789"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(await screen.findByRole("heading", { name: "Advisory failure visibility" })).toBeInTheDocument();
      expect(screen.getByText("Provider degraded")).toBeInTheDocument();
      expect(
        screen.getByText(/Provider degraded state is visible here/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "The bounded assistant provider did not return a trusted summary, so the reviewed advisory remains unresolved.",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
    });

    it("renders the AI trace review queue skeleton with accepted rejected and corrected states", async () => {
      const fetchFn = createAuthorizedFetch({
        "/inspect-ai-trace-review-queue": {
          read_only: true,
          queue_name: "ai_trace_review",
          total_records: 3,
          state_counts: {
            accepted: 1,
            corrected: 1,
            rejected: 1,
          },
          records: [
            {
              ai_trace_id: "ai-trace-review-accepted-001",
              review_state: "accepted",
              registered_agent_id: "agent-governed-summary-001",
              registered_tool_id: "tool-case-summary-001",
              reviewed_record_family: "case",
              reviewed_record_id: "case-trace-review-001",
              citations: ["case-trace-review-001", "evidence-trace-review-001"],
              reviewer_note: "Accepted as cited context only; case truth stays authoritative.",
              expiration_posture: "expires_with_reviewed_case",
              authority_mode: "advisory_only",
              authoritative_workflow_truth: false,
              trace_link: "/operator/assistant/ai_trace/ai-trace-review-accepted-001",
            },
            {
              ai_trace_id: "ai-trace-review-rejected-001",
              review_state: "rejected",
              registered_agent_id: "agent-governed-summary-001",
              registered_tool_id: "tool-case-summary-001",
              reviewed_record_family: "case",
              reviewed_record_id: "case-trace-review-001",
              citations: ["case-trace-review-001"],
              reviewer_note: "Rejected because supporting citations were incomplete.",
              expiration_posture: "expires_with_reviewed_case",
              authority_mode: "advisory_only",
              authoritative_workflow_truth: false,
            },
            {
              ai_trace_id: "ai-trace-review-corrected-001",
              review_state: "corrected",
              registered_agent_id: "agent-governed-summary-001",
              registered_tool_id: "tool-case-summary-001",
              reviewed_record_family: "case",
              reviewed_record_id: "case-trace-review-001",
              citations: ["case-trace-review-001", "evidence-trace-review-001"],
              reviewer_note: "Corrected by reviewer note before any downstream use.",
              expiration_posture: "expires_with_reviewed_case",
              authority_mode: "advisory_only",
              authoritative_workflow_truth: false,
            },
          ],
        },
      });
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/trace-review"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      expect(await screen.findByRole("heading", { name: "AI Trace Review Queue" })).toBeInTheDocument();
      expect(screen.getByText("Accepted")).toBeInTheDocument();
      expect(screen.getByText("Rejected")).toBeInTheDocument();
      expect(screen.getByText("Corrected")).toBeInTheDocument();
      expect(screen.getAllByText("agent-governed-summary-001").length).toBeGreaterThan(0);
      expect(screen.getAllByText("tool-case-summary-001").length).toBeGreaterThan(0);
      expect(screen.getAllByText("case-trace-review-001").length).toBeGreaterThan(0);
      expect(
        screen.getAllByRole("link", { name: "case-trace-review-001" })[0],
      ).toHaveAttribute("href", "/operator/cases/case-trace-review-001");
      expect(screen.getAllByText("evidence-trace-review-001").length).toBeGreaterThan(0);
      expect(
        screen.getByText("Corrected by reviewer note before any downstream use."),
      ).toBeInTheDocument();
      expect(screen.getAllByText("expires_with_reviewed_case").length).toBeGreaterThan(0);
      expect(
        screen.getByText(/Trace review state cannot approve actions/i),
      ).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
      expect(fetchFn).toHaveBeenCalledWith(
        "/inspect-ai-trace-review-queue?order=ASC&page=1&per_page=500&sort=review_state",
        {
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        },
      );
    });

    it("fails closed on unsupported assistant advisory route families", async () => {
      const fetchFn = createAuthorizedFetch({});
      const dependencies = createDefaultDependencies({
        fetchFn,
      });

      render(
        <MemoryRouter initialEntries={["/operator/assistant/not-reviewed/record-123"]}>
          <OperatorRoutes dependencies={dependencies} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Assistant Advisory" })).toBeInTheDocument();
      });

      expect(
        screen.getByText(
          "Unsupported assistant advisory route. Use alert, case, recommendation, approval decision, or reconciliation with an authoritative identifier.",
        ),
      ).toBeInTheDocument();
      expect(
        fetchFn.mock.calls.some(([url]) =>
          String(url).includes("/inspect-advisory-output"),
        ),
      ).toBe(false);
    });
  });
}
