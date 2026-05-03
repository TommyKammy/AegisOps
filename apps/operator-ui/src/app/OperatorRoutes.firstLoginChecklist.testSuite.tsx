import { screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createDefaultDependencies } from "./OperatorRoutes";
import {
  createAuthorizedFetch,
  renderOperatorRoute,
} from "./OperatorRoutes.testSupport";

export function registerOperatorRoutesFirstLoginChecklistTests() {
  describe("first-login checklist route", () => {
    it("renders the Phase 55 checklist sequence from backend-owned records", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "runtime_readiness",
                authority_record_id: "ready",
              },
              {
                step_key: "seeded_queue",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "queue",
                authority_record_id: "demo-queue-1",
              },
              {
                step_key: "sample_wazuh_alert",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "alert",
                authority_record_id: "alert-wazuh-1",
              },
              {
                step_key: "promote_to_case",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "case",
                authority_record_id: "case-1",
              },
              {
                step_key: "evidence",
                state: "degraded",
                authority_source: "backend_authoritative_record",
                authority_record_family: "evidence",
                authority_record_id: "evidence-1",
              },
              {
                step_key: "ai_summary",
                state: "skipped",
                authority_source: "backend_authoritative_record",
                authority_record_family: "assistant_advisory",
                authority_record_id: "advisory-1",
              },
              {
                step_key: "action_request",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "action_request",
                authority_record_id: "action-request-1",
              },
              {
                step_key: "approval_decision",
                state: "blocked",
                authority_source: "backend_authoritative_record",
                authority_record_family: "action_review",
                authority_record_id: "review-1",
              },
              {
                step_key: "shuffle_receipt",
                state: "unavailable",
                authority_source: "backend_authoritative_record",
                authority_record_family: "execution_receipt",
                authority_record_id: "receipt-1",
              },
              {
                step_key: "reconciliation",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "reconciliation",
                authority_record_id: "recon-1",
              },
              {
                step_key: "report_export",
                state: "skipped",
                authority_source: "backend_authoritative_record",
                authority_record_family: "report_export",
                authority_record_id: "report-1",
              },
            ],
            total_records: 11,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "First-Login Checklist" }),
        ).toBeInTheDocument();
      });

      const checklist = screen.getByRole("list", {
        name: "Phase 55 first-login checklist",
      });
      const rows = within(checklist).getAllByRole("listitem");
      expect(rows).toHaveLength(11);
      expect(rows.map((row) => within(row).getByTestId("step-title").textContent)).toEqual([
        "Stack health",
        "Seeded queue",
        "Sample Wazuh-origin alert",
        "Promote to case",
        "Evidence",
        "AI summary",
        "Action request",
        "Approval or rejection",
        "Shuffle execution receipt",
        "Reconciliation",
        "Report export",
      ]);
      expect(
        within(rows[4]).getByText("State: degraded"),
      ).toBeInTheDocument();
      expect(within(rows[5]).getByText("State: skipped")).toBeInTheDocument();
      expect(within(rows[7]).getByText("State: blocked")).toBeInTheDocument();
      expect(
        within(rows[8]).getByText("State: unavailable"),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Checklist progress is derived from backend records only; browser state, UI cache, Wazuh state, Shuffle state, AI output, tickets, verifier output, and issue-lint output remain subordinate context.",
        ),
      ).toBeInTheDocument();
    });

    it("fails closed when checklist completion comes from browser cache", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "browser_cache",
                authority_record_family: "runtime_readiness",
                authority_record_id: "ready",
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Checklist state from browser_cache is not trusted workflow truth.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("State: completed")).not.toBeInTheDocument();
    });

    it("fails closed when a checklist step is bound to the wrong backend record family", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "completed",
                authority_source: "backend_authoritative_record",
                authority_record_family: "case",
                authority_record_id: "case-1",
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Checklist step stack_health is bound to case, expected runtime_readiness.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("State: completed")).not.toBeInTheDocument();
    });

    it("renders bounded empty-state and failure-state copy without promoting UI state to workflow truth", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "stack_health",
                state: "blocked",
                failure_state_key: "port_conflict",
                authority_source: "backend_authoritative_record",
                authority_record_family: "runtime_readiness",
                authority_record_id: "ready-blocked",
              },
              {
                step_key: "seeded_queue",
                state: "unavailable",
                failure_state_key: "missing_seed_data",
                authority_source: "backend_authoritative_record",
                authority_record_family: "queue",
                authority_record_id: "queue-empty",
              },
              {
                step_key: "sample_wazuh_alert",
                state: "blocked",
                failure_state_key: "missing_wazuh",
                authority_source: "backend_authoritative_record",
                authority_record_family: "alert",
                authority_record_id: "alert-missing-wazuh",
              },
              {
                step_key: "promote_to_case",
                state: "blocked",
                failure_state_key: "missing_idp",
                authority_source: "backend_authoritative_record",
                authority_record_family: "case",
                authority_record_id: "case-idp-blocked",
              },
              {
                step_key: "evidence",
                state: "blocked",
                failure_state_key: "missing_secrets",
                authority_source: "backend_authoritative_record",
                authority_record_family: "evidence",
                authority_record_id: "evidence-secret-blocked",
              },
              {
                step_key: "approval_decision",
                state: "blocked",
                failure_state_key: "protected_surface_denial",
                authority_source: "backend_authoritative_record",
                authority_record_family: "action_review",
                authority_record_id: "review-denied",
              },
              {
                step_key: "shuffle_receipt",
                state: "blocked",
                failure_state_key: "missing_shuffle",
                authority_source: "backend_authoritative_record",
                authority_record_family: "execution_receipt",
                authority_record_id: "receipt-missing-shuffle",
              },
            ],
            total_records: 7,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      const expectedCopies = [
        "A required port is already in use. Free the conflicting service or select a reviewed profile override, then rerun startup checks.",
        "Demo seed data is empty. Run the reviewed demo seed path and refresh only after AegisOps records are admitted.",
        "Wazuh signal intake is unavailable. Confirm the reviewed Wazuh profile and intake binding, then rerun the readiness check.",
        "Identity provider configuration is missing. Configure the reviewed IdP issuer, client, and redirect binding before enabling protected workflows.",
        "Required secret references are missing. Mount the reviewed secret files or OpenBao bindings and restart the affected service; placeholder values stay blocked.",
        "Protected surface access was denied. Sign in with an authorized operator role or ask an administrator to review RBAC; denial remains correct until backend auth changes.",
        "Shuffle delegated execution is unavailable. Confirm the reviewed Shuffle profile and template import contract, then retry after backend records report readiness.",
      ];

      for (const copy of expectedCopies) {
        await waitFor(() => {
          expect(screen.getByText(copy)).toBeInTheDocument();
        });
      }

      expect(
        screen.getAllByText(
          "This copy is operator guidance only and cannot approve, repair, reconcile, close, release, gate, or mutate authoritative AegisOps records.",
        ),
      ).toHaveLength(expectedCopies.length);

      const pageText = document.body.textContent ?? "";
      expect(pageText).not.toMatch(/automatic repair/i);
      expect(pageText).not.toMatch(/UI copy is workflow truth/i);
      expect(pageText).not.toMatch(/Phase 58 supportability is complete/i);
    });

    it("fails closed when missing Wazuh is presented as successful completion", async () => {
      const dependencies = createDefaultDependencies({
        fetchFn: createAuthorizedFetch({
          "/inspect-first-login-checklist": {
            records: [
              {
                step_key: "sample_wazuh_alert",
                state: "completed",
                failure_state_key: "missing_wazuh",
                authority_source: "backend_authoritative_record",
                authority_record_family: "alert",
                authority_record_id: "alert-missing-wazuh",
              },
            ],
            total_records: 1,
          },
        }),
      });

      renderOperatorRoute("/operator/first-login-checklist", dependencies);

      await waitFor(() => {
        expect(
          screen.getByText(
            "Checklist step sample_wazuh_alert cannot present failure state missing_wazuh as successful completion.",
          ),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText("State: completed")).not.toBeInTheDocument();
    });
  });
}
