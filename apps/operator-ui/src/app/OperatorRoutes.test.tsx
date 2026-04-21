import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import {
  OperatorRoutes,
  createDefaultDependencies,
} from "./OperatorRoutes";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

function createAuthorizedFetch(
  handlers: Record<string, unknown>,
) {
  return vi.fn<typeof fetch>().mockImplementation((input) => {
    const url = String(input);

    if (url.startsWith("/api/operator/session")) {
      return Promise.resolve(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst"],
          subject: "operator-7",
        }),
      );
    }

    const match = Object.entries(handlers).find(([prefix]) => url.startsWith(prefix));
    if (match) {
      return Promise.resolve(jsonResponse(match[1]));
    }

    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });
}

describe("OperatorRoutes", () => {
  it("redirects unauthenticated users to the reviewed login route", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 401 })),
    });

    render(
      <MemoryRouter initialEntries={["/operator/queue"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Operator Sign-In" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Return path: /operator/queue")).toBeInTheDocument();
  });

  it("routes unsupported backend roles to the forbidden page", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "reviewer@example.com",
          provider: "authentik",
          roles: ["viewer"],
          subject: "user-42",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Access denied" }),
      ).toBeInTheDocument();
    });
  });

  it("fails closed on malformed reviewed session responses", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: "analyst",
          subject: "operator-11",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Session verification failed" }),
      ).toBeInTheDocument();
    });
  });

  it("restores an authorized session into the protected shell", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst"],
          subject: "operator-7",
        }),
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });
  });

  it("renders the reviewed queue route from backend-authoritative queue records", async () => {
    const fetchFn = createAuthorizedFetch({
      "/inspect-analyst-queue": {
        queue_name: "analyst_review",
        read_only: true,
        records: [
          {
            alert_id: "alert-123",
            review_state: "degraded",
            case_id: "case-456",
            case_lifecycle_state: "open",
            accountable_source_identities: [
              "manager:wazuh-manager-github-1",
            ],
            reviewed_context: {
              source: {
                source_family: "github_audit",
              },
            },
            current_action_review: {
              review_state: "pending",
              next_expected_action: "await_approver_decision",
            },
          },
        ],
        total_records: 1,
      },
    });
    const dependencies = createDefaultDependencies({
      fetchFn,
    });

    render(
      <MemoryRouter initialEntries={["/operator/queue"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Analyst Queue" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("alert-123")).toBeInTheDocument();
    expect(screen.getAllByText(/Review: degraded/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Primary review surface/i),
    ).toBeInTheDocument();
    expect(screen.getByText("github_audit")).toBeInTheDocument();
  });

  it("renders alert detail with authoritative and subordinate sections separated", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-alert-detail": {
          alert_id: "alert-123",
          alert: {
            alert_id: "alert-123",
            lifecycle_state: "triaged",
          },
          case_record: {
            case_id: "case-456",
          },
          review_state: "triaged",
          escalation_boundary: "case_optional",
          provenance: {
            admission_kind: "live",
            admission_channel: "live_wazuh_webhook",
          },
          lineage: {
            finding_id: "finding-123",
            analytic_signal_id: "signal-123",
            source_systems: ["wazuh"],
            substrate_detection_record_ids: ["wazuh:1731595300.1234567"],
            accountable_source_identities: ["manager:wazuh-manager-github-1"],
            evidence_ids: ["evidence-123"],
            reconciliation_id: "recon-123",
          },
          latest_reconciliation: {
            reconciliation_id: "recon-123",
          },
          linked_evidence_records: [
            {
              evidence_id: "evidence-123",
              source_system: "wazuh",
              derivation_relationship: "native_detection_record",
            },
          ],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
    });

    expect(screen.getAllByText("Authoritative anchor").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Subordinate evidence context").length).toBeGreaterThan(0);
    expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
    expect(screen.getByText("recon-123")).toBeInTheDocument();
  });

  it("renders case detail with provenance summary and subordinate context", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": {
          case_id: "case-456",
          case_record: {
            case_id: "case-456",
            lifecycle_state: "pending_action",
          },
          linked_alert_ids: ["alert-123"],
          linked_observation_ids: ["observation-123"],
          linked_recommendation_ids: ["recommendation-123"],
          linked_evidence_ids: ["evidence-123"],
          linked_reconciliation_ids: ["recon-123"],
          provenance_summary: {
            authoritative_anchor: {
              record_family: "case",
              record_id: "case-456",
              source_family: "github_audit",
              provenance_classification: "authoritative",
            },
          },
          linked_alert_records: [
            {
              alert_id: "alert-123",
            },
          ],
          linked_evidence_records: [
            {
              evidence_id: "evidence-123",
            },
          ],
          linked_reconciliation_records: [
            {
              reconciliation_id: "recon-123",
            },
          ],
          cross_source_timeline: [
            {
              record_family: "case",
              record_id: "case-456",
              source_family: "github_audit",
              provenance_classification: "authoritative",
            },
          ],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
    });

    expect(screen.getByText("Provenance summary")).toBeInTheDocument();
    expect(screen.getByText("Subordinate evidence context")).toBeInTheDocument();
    expect(screen.getAllByText("github_audit").length).toBeGreaterThan(0);
    expect(screen.getByText("recon-123")).toBeInTheDocument();
  });

  it("renders readiness from the reviewed diagnostics surface", async () => {
    const fetchFn = createAuthorizedFetch({
      "/diagnostics/readiness": {
        status: "ready",
        booted: true,
        startup: {
          startup_ready: true,
        },
        shutdown: {
          shutdown_ready: false,
        },
        persistence_mode: "postgresql",
        latest_reconciliation: {
          reconciliation_id: "recon-123",
        },
        metrics: {
          action_requests: {
            approved: 1,
          },
          action_executions: {
            terminal: 1,
          },
          review_path_health: {
            overall_state: "healthy",
            review_count: 1,
          },
          source_health: {
            tracked_sources: 1,
          },
          automation_substrate_health: {
            tracked_surfaces: 1,
          },
        },
      },
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/readiness"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Readiness" })).toBeInTheDocument();
    });

    expect(screen.getByText("postgresql")).toBeInTheDocument();
    expect(fetchFn).toHaveBeenCalledWith(
      "/diagnostics/readiness?order=ASC&page=1&per_page=1&sort=status",
      expect.any(Object),
    );
  });

  it("renders reconciliation mismatch visibility from reviewed records", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-reconciliation-status": {
          read_only: true,
          total_records: 1,
          records: [
            {
              reconciliation_id: "recon-123",
              lifecycle_state: "mismatch",
              ingest_disposition: "updated",
              mismatch_summary: "case linkage mismatch remains unresolved",
              compared_at: "2026-04-21T00:00:00+00:00",
              subject_linkage: {
                case_ids: ["case-456"],
              },
            },
          ],
        },
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/reconciliation"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Reconciliation" })).toBeInTheDocument();
    });

    expect(
      screen.getAllByText("case linkage mismatch remains unresolved").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/mismatch/i).length).toBeGreaterThan(0);
  });
});
