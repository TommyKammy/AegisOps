import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
  sessionOverride?: {
    identity: string;
    provider: string;
    roles: string[];
    subject: string;
  },
) {
  return vi.fn<typeof fetch>().mockImplementation((input) => {
    const url = String(input);

    if (url.startsWith("/api/operator/session")) {
      return Promise.resolve(
        jsonResponse(
          sessionOverride ?? {
            identity: "analyst@example.com",
            provider: "authentik",
            roles: ["Analyst"],
            subject: "operator-7",
          },
        ),
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

  it("hides action-review navigation for analyst-only sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
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

    expect(screen.queryByText(/action review/i)).not.toBeInTheDocument();
  });

  it("shows action-review navigation for reviewed approver sessions", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {},
        {
          identity: "approver@example.com",
          provider: "authentik",
          roles: ["Approver"],
          subject: "operator-8",
        },
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

    expect(screen.getAllByText(/action review/i).length).toBeGreaterThan(0);
  });

  it("redirects analyst-only deep links away from the action-review route", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({}),
    });

    render(
      <MemoryRouter initialEntries={["/operator/action-review"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Protected operator shell" }),
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/action review/i)).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Queue triage stays inside AegisOps as the authoritative review selection surface.",
      ),
    ).toBeInTheDocument();
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

    await waitFor(() => {
      expect(screen.getByText("alert-123")).toBeInTheDocument();
      expect(screen.getAllByText(/Review: degraded/i).length).toBeGreaterThan(0);
      expect(
        screen.getByText(/Primary review surface/i),
      ).toBeInTheDocument();
      expect(screen.getByText("github_audit")).toBeInTheDocument();
    });
  });

  it("keeps degraded and missing-anchor queue warnings explicit", async () => {
    const fetchFn = createAuthorizedFetch({
      "/inspect-analyst-queue": {
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

    await waitFor(() => {
      expect(screen.getByText("alert-789")).toBeInTheDocument();
      expect(screen.getByText("No case anchor")).toBeInTheDocument();
      expect(
        screen.getByText("Review state remains degraded."),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Non-authoritative coordination reference is missing_anchor.",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Case lifecycle state is present without an authoritative case identifier.",
        ),
      ).toBeInTheDocument();
    });
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

    await waitFor(() => {
      expect(screen.getAllByText("Authoritative anchor").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Subordinate evidence context").length).toBeGreaterThan(0);
      expect(screen.getByText("live_wazuh_webhook")).toBeInTheDocument();
      expect(screen.getByText("recon-123")).toBeInTheDocument();
    });
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

    await waitFor(() => {
      expect(screen.getByText("Provenance summary")).toBeInTheDocument();
      expect(screen.getByText("Subordinate evidence context")).toBeInTheDocument();
      expect(screen.getAllByText("github_audit").length).toBeGreaterThan(0);
      expect(screen.getByText("recon-123")).toBeInTheDocument();
    });
  });

  it("promotes an alert into a case from alert detail and re-renders authoritative state", async () => {
    const user = userEvent.setup();
    let alertDetailPayload: Record<string, unknown> = {
      alert_id: "alert-123",
      alert: {
        alert_id: "alert-123",
        lifecycle_state: "triaged",
      },
      review_state: "triaged",
      escalation_boundary: "case_optional",
      provenance: {
        admission_kind: "live",
        admission_channel: "live_wazuh_webhook",
      },
      lineage: {
        source_systems: ["wazuh"],
      },
      linked_evidence_records: [],
    };
    let caseDetailPayload: Record<string, unknown> = {
      case_id: "case-456",
      case_record: {
        case_id: "case-456",
        lifecycle_state: "open",
      },
      linked_alert_ids: ["alert-123"],
      linked_observation_ids: [],
      linked_lead_ids: [],
      linked_recommendation_ids: [],
      linked_evidence_ids: [],
      linked_reconciliation_ids: [],
      provenance_summary: {
        authoritative_anchor: {
          record_family: "case",
          record_id: "case-456",
          source_family: "github_audit",
          provenance_classification: "authoritative",
        },
      },
      linked_alert_records: [],
      linked_evidence_records: [],
      linked_reconciliation_records: [],
      cross_source_timeline: [],
    };
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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

      if (url.startsWith("/inspect-alert-detail")) {
        return Promise.resolve(jsonResponse(alertDetailPayload));
      }

      if (url.startsWith("/inspect-case-detail")) {
        return Promise.resolve(jsonResponse(caseDetailPayload));
      }

      if (url.startsWith("/operator/promote-alert-to-case")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            alert_id: "alert-123",
            case_lifecycle_state: "open",
          }),
        );
        alertDetailPayload = {
          ...alertDetailPayload,
          case_record: {
            case_id: "case-456",
          },
        };
        return Promise.resolve(
          jsonResponse({
            alert_id: "alert-123",
            case_id: "case-456",
            lifecycle_state: "open",
          }),
        );
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/alerts/alert-123"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Alert Detail" })).toBeInTheDocument();
    });

    const promoteSection = await screen.findByRole("heading", {
      name: "Promote alert into case",
    });
    const promoteCard = promoteSection.closest(".MuiCard-root");
    expect(promoteCard).not.toBeNull();

    await user.click(within(promoteCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(promoteCard as HTMLElement).getByRole("button", { name: "Promote alert" }),
    );

    await waitFor(() => {
      expect(screen.getAllByText("case-456").length).toBeGreaterThan(0);
    });

    expect(fetchFn).toHaveBeenCalledWith(
      "/operator/promote-alert-to-case",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });


  it("records bounded case observations, leads, and recommendations from case detail", async () => {
    const user = userEvent.setup();
    let caseDetailPayload: Record<string, unknown> = {
      case_id: "case-456",
      case_record: {
        case_id: "case-456",
        lifecycle_state: "pending_action",
      },
      linked_alert_ids: ["alert-123"],
      linked_observation_ids: [],
      linked_lead_ids: [],
      linked_recommendation_ids: [],
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
      linked_alert_records: [],
      linked_evidence_records: [],
      linked_reconciliation_records: [],
      cross_source_timeline: [],
    };
    const fetchFn = vi.fn<typeof fetch>().mockImplementation((input, init) => {
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

      if (url.startsWith("/inspect-case-detail")) {
        return Promise.resolve(jsonResponse(caseDetailPayload));
      }

      if (url.startsWith("/operator/record-case-observation")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            author_identity: "analyst@example.com",
            case_id: "case-456",
            observed_at: "2026-04-22T00:00",
            scope_statement: "Observed repository permission change requires tracked review.",
            supporting_evidence_ids: ["evidence-123", "evidence-456"],
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_observation_ids: ["observation-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            observation_id: "observation-123",
          }),
        );
      }

      if (url.startsWith("/operator/record-case-lead")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            case_id: "case-456",
            observation_id: "observation-123",
            triage_owner: "analyst@example.com",
            triage_rationale: "Privilege-impacting change needs durable follow-up.",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_lead_ids: ["lead-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            lead_id: "lead-123",
            observation_id: "observation-123",
          }),
        );
      }

      if (url.startsWith("/operator/record-case-recommendation")) {
        expect(init?.method).toBe("POST");
        expect(init?.body).toBe(
          JSON.stringify({
            case_id: "case-456",
            intended_outcome: "Review repository owner change evidence before approval.",
            lead_id: "lead-123",
            review_owner: "analyst@example.com",
          }),
        );
        caseDetailPayload = {
          ...caseDetailPayload,
          linked_recommendation_ids: ["recommendation-123"],
        };
        return Promise.resolve(
          jsonResponse({
            case_id: "case-456",
            lead_id: "lead-123",
            recommendation_id: "recommendation-123",
          }),
        );
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Case Detail" })).toBeInTheDocument();
    });

    const observationSection = await screen.findByRole("heading", {
      name: "Record case observation",
    });
    const observationCard = observationSection.closest(".MuiCard-root");
    expect(observationCard).not.toBeNull();
    await user.type(
      within(observationCard as HTMLElement).getByRole("textbox", {
        name: "Observed at",
      }),
      "2026-04-22T00:00",
    );
    await user.type(
      within(observationCard as HTMLElement).getByRole("textbox", {
        name: "Scope statement",
      }),
      "Observed repository permission change requires tracked review.",
    );
    const supportingEvidenceField = within(observationCard as HTMLElement).getByRole(
      "textbox",
      {
        name: "Supporting evidence ids",
      },
    );
    await user.clear(supportingEvidenceField);
    await user.type(supportingEvidenceField, "evidence-123, evidence-456");
    await user.click(within(observationCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(observationCard as HTMLElement).getByRole("button", { name: "Record observation" }),
    );
    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-case-observation",
        expect.objectContaining({
          method: "POST",
        }),
      );
      expect(screen.getByText("Known observation ids: observation-123")).toBeInTheDocument();
    });

    const leadSection = screen.getByRole("heading", { name: "Record case lead" });
    const leadCard = leadSection.closest(".MuiCard-root");
    expect(leadCard).not.toBeNull();
    await user.type(
      within(leadCard as HTMLElement).getByRole("textbox", {
        name: "Observation id",
      }),
      "observation-123",
    );
    await user.type(
      within(leadCard as HTMLElement).getByRole("textbox", {
        name: "Triage rationale",
      }),
      "Privilege-impacting change needs durable follow-up.",
    );
    await user.click(within(leadCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(leadCard as HTMLElement).getByRole("button", { name: "Record lead" }),
    );
    await waitFor(() => {
      expect(fetchFn).toHaveBeenCalledWith(
        "/operator/record-case-lead",
        expect.objectContaining({
          method: "POST",
        }),
      );
      expect(screen.getByText("Known lead ids: lead-123")).toBeInTheDocument();
    });

    const recommendationSection = screen.getByRole("heading", {
      name: "Record case recommendation",
    });
    const recommendationCard = recommendationSection.closest(".MuiCard-root");
    expect(recommendationCard).not.toBeNull();
    await user.type(
      within(recommendationCard as HTMLElement).getByRole("textbox", {
        name: "Lead id",
      }),
      "lead-123",
    );
    await user.type(
      within(recommendationCard as HTMLElement).getByRole("textbox", {
        name: "Intended outcome",
      }),
      "Review repository owner change evidence before approval.",
    );
    await user.click(within(recommendationCard as HTMLElement).getByRole("checkbox"));
    await user.click(
      within(recommendationCard as HTMLElement).getByRole("button", {
        name: "Record recommendation",
      }),
    );
    await waitFor(() => {
      expect(screen.getAllByText("recommendation-123").length).toBeGreaterThan(0);
    });
  }, 10000);

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

    await waitFor(() => {
      expect(screen.getByText("postgresql")).toBeInTheDocument();
    });
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
