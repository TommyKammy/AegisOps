import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { createDefaultDependencies, OperatorRoutes } from "./OperatorRoutes";
import { resetOperatorQueryCacheForTests } from "./operatorQueryCache";
import {
  createAuthorizedFetch,
  jsonResponse,
} from "./OperatorRoutes.testSupport";
import { EvidencePackReviewSection } from "./operatorConsolePages/caseDetailEvidencePackSection";

const freshCollectionTimestamp = new Date().toISOString();
const staleCollectionTimestamp = new Date(
  Date.now() - 7 * 60 * 60 * 1000,
).toISOString();

function createEvidencePack(overrides: Record<string, unknown> = {}) {
  const caseId = typeof overrides.case_id === "string" ? overrides.case_id : "case-456";
  const evidenceRequestId =
    typeof overrides.evidence_request_id === "string"
      ? overrides.evidence_request_id
      : "evidence-request-001";
  const sourceId =
    typeof overrides.source_id === "string"
      ? overrides.source_id
      : "malwarebazaar_hash_reputation";
  const collectionTimestamp =
    overrides.freshness_state === "fresh"
      ? freshCollectionTimestamp
      : staleCollectionTimestamp;

  return {
    authoritative_workflow_truth: false,
    case_id: caseId,
    confidence: {
      ambiguity_badge: "unresolved",
      freshness: "stale",
      posture: "external_hash_reputation_subordinate_context",
      source_native_score_authority: "none",
    },
    confidence_state: "present",
    conflict_state: "conflicting",
    consumer: "case_workbench",
    custody: {
      aegisops_evidence_record_id: "evidence-enrichment-001",
      collection_timestamp: collectionTimestamp,
      enrichment_request_id: "enrichment-request-001",
      response_digest: "sha256:" + "a".repeat(64),
      reviewed_file_hash: "b".repeat(64),
    },
    custody_state: "complete",
    degraded_reasons: ["stale_reputation", "conflicting_enrichment"],
    evidence_request_id: evidenceRequestId,
    freshness_state: "stale",
    provenance: {
      authority_posture: "subordinate_evidence_context_only",
      case_binding: caseId,
      collection_timestamp: collectionTimestamp,
      custody_reference: "custody-ref-enrichment-001",
      enrichment_request_id: "enrichment-request-001",
      request_binding: evidenceRequestId,
      response_digest: "sha256:" + "a".repeat(64),
      source_id: sourceId,
      target_binding: "b".repeat(64),
    },
    provenance_state: "bound",
    source_id: sourceId,
    source_state: "available",
    status: "degraded",
    uncertainty_label: "unresolved_conflict",
    unavailable_reasons: [],
    authority_posture: "subordinate_evidence_context_only",
    workflow_authority: "none",
    ...overrides,
  };
}

function createEvidencePackWithSource(sourceId: string) {
  const pack = createEvidencePack({ source_id: sourceId });
  return {
    ...pack,
    provenance: {
      ...pack.provenance,
      source_id: sourceId,
    },
  };
}

function createUnavailableEvidencePack() {
  return createEvidencePack({
    confidence: {
      ...createEvidencePack().confidence,
      ambiguity_badge: "related-entity",
      freshness: "fresh",
    },
    conflict_state: "none",
    degraded_reasons: [],
    freshness_state: "fresh",
    source_state: "unavailable",
    status: "unavailable",
    uncertainty_label: "source_unavailable",
    unavailable_reasons: ["source_unavailable"],
  });
}

function createCaseDetailPayload(overrides: Record<string, unknown> = {}) {
  return {
    case_id: "case-456",
    case_record: {
      case_id: "case-456",
      lifecycle_state: "pending_action",
    },
    cross_source_timeline: [],
    linked_alert_ids: ["alert-123"],
    linked_alert_records: [],
    linked_evidence_ids: ["evidence-123"],
    linked_evidence_packs: [createEvidencePack()],
    linked_evidence_records: [
      {
        evidence_id: "evidence-enrichment-001",
        provenance: {
          custody_reference: "custody-ref-enrichment-001",
        },
      },
    ],
    linked_lead_ids: [],
    linked_observation_ids: [],
    linked_recommendation_ids: [],
    linked_reconciliation_ids: [],
    linked_reconciliation_records: [],
    provenance_summary: {
      authoritative_anchor: {
        provenance_classification: "authoritative",
        record_family: "case",
        record_id: "case-456",
        source_family: "aegisops",
      },
    },
    ...overrides,
  };
}

const fullRouteWait = { timeout: 10_000 };
const fullRouteTestTimeout = 15_000;

describe("case detail evidence pack UI", () => {
  beforeEach(() => {
    resetOperatorQueryCacheForTests();
  });

  it("keeps evidence-pack rendering isolated behind the case-detail evidence-pack section", () => {
    render(<EvidencePackReviewSection evidencePacks={[createEvidencePack()]} />);

    const evidencePackTable = screen.getByRole("table", {
      name: "Linked evidence packs",
    });
    const rows = within(evidencePackTable).getAllByRole("row").slice(1);

    expect(rows).toHaveLength(1);
    expect(
      within(rows[0] as HTMLElement).getByText("evidence-request-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("Subordinate evidence context only"),
    ).toBeInTheDocument();
  });

  it("renders linked evidence pack custody, provenance, stale/conflict, freshness, confidence, uncertainty, and source state as subordinate context", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": createCaseDetailPayload(),
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    const evidencePackTable = await screen.findByRole("table", {
      name: "Linked evidence packs",
    }, fullRouteWait);
    const rows = within(evidencePackTable).getAllByRole("row").slice(1);

    expect(rows).toHaveLength(1);
    expect(
      within(rows[0] as HTMLElement).getByText("evidence-request-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("malwarebazaar_hash_reputation"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("stale"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("conflicting"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement)
        .getByText("conflicting")
        .closest(".MuiChip-root"),
    ).toHaveClass("MuiChip-colorWarning");
    expect(
      within(rows[0] as HTMLElement).getByText("present"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("unresolved_conflict"),
    ).toBeInTheDocument();
    expect(within(rows[0] as HTMLElement).getByText("available")).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("evidence-enrichment-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("custody-ref-enrichment-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("Subordinate evidence context only"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Evidence pack can close case")).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence pack proves RC readiness")).not.toBeInTheDocument();
  }, fullRouteTestTimeout);

  it("flags unavailable evidence sources as an error state", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": createCaseDetailPayload({
          linked_evidence_packs: [createUnavailableEvidencePack()],
        }),
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    const evidencePackTable = await screen.findByRole("table", {
      name: "Linked evidence packs",
    }, fullRouteWait);
    const row = within(evidencePackTable).getAllByRole("row")[1] as HTMLElement;

    expect(within(row).getByText("unavailable").closest(".MuiChip-root")).toHaveClass(
      "MuiChip-colorError",
    );
  }, fullRouteTestTimeout);

  it("renders supported non-SHA256 reviewed hash bindings", async () => {
    const md5Hash = "c".repeat(32);
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": createCaseDetailPayload({
          linked_evidence_packs: [
            createEvidencePack({
              custody: {
                ...createEvidencePack().custody,
                reviewed_file_hash: md5Hash,
              },
              provenance: {
                ...createEvidencePack().provenance,
                target_binding: md5Hash,
              },
            }),
          ],
        }),
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("table", { name: "Linked evidence packs" }, fullRouteWait),
    ).toBeInTheDocument();
    expect(screen.queryByText("Reviewed operator data could not be verified.")).not.toBeInTheDocument();
  }, fullRouteTestTimeout);

  it("keeps empty and degraded evidence-pack states explicit", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": createCaseDetailPayload({
          linked_evidence_packs: [],
        }),
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText(
        "No linked evidence packs were returned for this case.",
        undefined,
        fullRouteWait,
      ),
    ).toBeInTheDocument();
  }, fullRouteTestTimeout);

  it.each([
    ["UI-cache source", createEvidencePack({ cache_sourced: true })],
    ["browser-state source", createEvidencePack({ projection_source: "browser_state" })],
    ["hidden stale label", createEvidencePack({ freshness_state: "" })],
    ["unsupported stale label", createEvidencePack({ freshness_state: "rc_ready" })],
    ["hidden conflict label", createEvidencePack({ conflict_state: "" })],
    ["unsupported conflict label", createEvidencePack({ conflict_state: "ready_to_close" })],
    ["unsupported consumer", createEvidencePack({ consumer: "workflow_gate" })],
    ["AI grounding consumer", createEvidencePack({ consumer: "ai_grounding" })],
    ["unsupported source", createEvidencePackWithSource("workflow_gate")],
    [
      "unsupported degraded reason",
      createEvidencePack({ degraded_reasons: ["case_truth"] }),
    ],
    [
      "unsupported unavailable reason",
      createEvidencePack({ unavailable_reasons: ["approval_truth"] }),
    ],
    [
      "missing degraded reason array",
      createEvidencePack({ degraded_reasons: undefined }),
    ],
    [
      "null unavailable reason array",
      createEvidencePack({ unavailable_reasons: null }),
    ],
    [
      "stale pack inside source freshness window",
      createEvidencePack({
        custody: {
          ...createEvidencePack().custody,
          collection_timestamp: freshCollectionTimestamp,
        },
        provenance: {
          ...createEvidencePack().provenance,
          collection_timestamp: freshCollectionTimestamp,
        },
      }),
    ],
    [
      "available status with degraded reason",
      createEvidencePack({ status: "available" }),
    ],
    [
      "degraded status without degraded reason",
      createEvidencePack({
        degraded_reasons: [],
        conflict_state: "none",
        freshness_state: "fresh",
        uncertainty_label: "related_entity_not_authoritative",
        confidence: {
          ...createEvidencePack().confidence,
          ambiguity_badge: "related-entity",
          freshness: "fresh",
        },
      }),
    ],
    [
      "stale state without stale reason",
      createEvidencePack({
        degraded_reasons: ["conflicting_enrichment"],
      }),
    ],
    [
      "provenance target mismatch",
      createEvidencePack({
        provenance: {
          ...createEvidencePack().provenance,
          target_binding: "c".repeat(64),
        },
      }),
    ],
    [
      "provenance custody reference mismatch",
      createEvidencePack({
        provenance: {
          ...createEvidencePack().provenance,
          custody_reference: "custody-ref-tampered",
        },
      }),
    ],
    [
      "invalid reviewed file hash",
      createEvidencePack({
        custody: {
          ...createEvidencePack().custody,
          reviewed_file_hash: "not-a-hash",
        },
        provenance: {
          ...createEvidencePack().provenance,
          target_binding: "not-a-hash",
        },
      }),
    ],
    [
      "invalid response digest",
      createEvidencePack({
        custody: {
          ...createEvidencePack().custody,
          response_digest: "not-a-digest",
        },
        provenance: {
          ...createEvidencePack().provenance,
          response_digest: "not-a-digest",
        },
      }),
    ],
    [
      "non-aware collection timestamp",
      createEvidencePack({
        custody: {
          ...createEvidencePack().custody,
          collection_timestamp: "2026-05-30T00:00:00",
        },
        provenance: {
          ...createEvidencePack().provenance,
          collection_timestamp: "2026-05-30T00:00:00",
        },
      }),
    ],
    [
      "invalid calendar collection timestamp",
      createEvidencePack({
        custody: {
          ...createEvidencePack().custody,
          collection_timestamp: "2026-02-30T00:00:00Z",
        },
        provenance: {
          ...createEvidencePack().provenance,
          collection_timestamp: "2026-02-30T00:00:00Z",
        },
      }),
    ],
    [
      "enabled source stale reason",
      createEvidencePack({
        confidence: {
          ...createEvidencePack().confidence,
          ambiguity_badge: "related-entity",
          freshness: "fresh",
        },
        conflict_state: "none",
        degraded_reasons: ["source_stale"],
        freshness_state: "fresh",
        source_state: "degraded",
        uncertainty_label: "stale_review_required",
      }),
    ],
    [
      "enabled source denied reason",
      createEvidencePack({
        confidence: {
          ...createEvidencePack().confidence,
          ambiguity_badge: "related-entity",
          freshness: "fresh",
        },
        conflict_state: "none",
        degraded_reasons: [],
        freshness_state: "fresh",
        source_state: "unavailable",
        status: "unavailable",
        uncertainty_label: "source_unavailable",
        unavailable_reasons: ["source_denied"],
      }),
    ],
    ["missing custody display", createEvidencePack({ custody: null })],
    [
      "incomplete custody display",
      createEvidencePack({
        custody: {
          aegisops_evidence_record_id: "evidence-enrichment-001",
        },
      }),
    ],
    ["missing provenance display", createEvidencePack({ provenance: null })],
    [
      "incomplete provenance display",
      createEvidencePack({
        provenance: {
          request_binding: "evidence-request-001",
          case_binding: "case-456",
          source_id: "malwarebazaar_hash_reputation",
        },
      }),
    ],
    [
      "incomplete confidence display",
      createEvidencePack({
        confidence: {
          source_native_score_authority: "none",
        },
      }),
    ],
    [
      "nested provenance authority",
      createEvidencePack({
        provenance: {
          ...createEvidencePack().provenance,
          authority_posture: "authoritative_aegisops_record",
        },
      }),
    ],
    [
      "nested confidence authority",
      createEvidencePack({
        confidence: {
          ...createEvidencePack().confidence,
          source_native_score_authority: "workflow_truth",
        },
      }),
    ],
    [
      "unexpected confidence posture",
      createEvidencePack({
        confidence: {
          ...createEvidencePack().confidence,
          posture: "authoritative_aegisops_record",
        },
      }),
    ],
    ["evidence truth", createEvidencePack({ authoritative_workflow_truth: true })],
    [
      "authoritative posture",
      createEvidencePack({ authority_posture: "authoritative_aegisops_record" }),
    ],
    ["workflow authority", createEvidencePack({ workflow_authority: "close_case" })],
    ["RC readiness claim", createEvidencePack({ release_readiness_claim: "rc_ready" })],
    ["unexpected evidence-pack field", createEvidencePack({ workflow_truth: true })],
    ["role bypass", createEvidencePack({ operator_visible: false })],
  ])("fails closed on %s", async (_label, evidencePack) => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch({
        "/inspect-case-detail": createCaseDetailPayload({
          linked_evidence_packs: [evidencePack],
        }),
      }),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(
          screen.getByText(
            "Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.",
          ),
        ).toBeInTheDocument();
      },
      fullRouteWait,
    );
    expect(
      screen.queryByRole("table", { name: "Linked evidence packs" }),
    ).not.toBeInTheDocument();
  });

  it("requires an approved operator session before evidence packs are visible", async () => {
    const dependencies = createDefaultDependencies({
      fetchFn: createAuthorizedFetch(
        {
          "/inspect-case-detail": createCaseDetailPayload(),
        },
        {
          identity: "contractor@example.com",
          provider: "authentik",
          roles: ["unreviewed_contractor"],
          subject: "operator-9",
        },
      ),
    });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Access denied" }, fullRouteWait),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("table", { name: "Linked evidence packs" }),
    ).not.toBeInTheDocument();
  }, fullRouteTestTimeout);

  it("rereads backend case detail after case writes instead of treating edited evidence ids as evidence-pack truth", async () => {
    let caseDetailRequests = 0;
    const fetchFn = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.startsWith("/api/operator/session")) {
        return jsonResponse({
          identity: "analyst@example.com",
          provider: "authentik",
          roles: ["Analyst"],
          subject: "operator-7",
        });
      }

      if (url.startsWith("/inspect-case-detail")) {
        caseDetailRequests += 1;
        return jsonResponse(
          createCaseDetailPayload({
            linked_evidence_packs:
              caseDetailRequests === 1
                ? [createEvidencePack()]
                : [
                    createEvidencePack({
                      evidence_request_id: "evidence-request-reread",
                      status: "available",
                      degraded_reasons: [],
                      freshness_state: "fresh",
                      conflict_state: "none",
                      uncertainty_label: "related_entity_not_authoritative",
                      confidence: {
                        ...createEvidencePack().confidence,
                        ambiguity_badge: "related-entity",
                        freshness: "fresh",
                      },
                    }),
                  ],
          }),
        );
      }

      if (
        url.startsWith("/operator/record-case-observation") &&
        init?.method === "POST"
      ) {
        return jsonResponse({ observation_id: "observation-1" }, 201);
      }

      if (url.startsWith("/diagnostics/readiness")) {
        return jsonResponse({ metrics: {}, status: "ready" });
      }

      throw new Error(`Unexpected fetch: ${url}`);
    };
    const dependencies = createDefaultDependencies({ fetchFn });

    render(
      <MemoryRouter initialEntries={["/operator/cases/case-456"]}>
        <OperatorRoutes dependencies={dependencies} />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("evidence-request-001", undefined, fullRouteWait),
    ).toBeInTheDocument();
    const user = userEvent.setup();
    await user.type(
      await screen.findByRole("textbox", { name: "Observed at" }, fullRouteWait),
      "2026-05-30T12:00:00Z",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Scope statement" }),
      "Follow up stale evidence.",
    );
    await user.clear(
      screen.getByRole("textbox", { name: "Supporting evidence ids" }),
    );
    await user.type(
      screen.getByRole("textbox", { name: "Supporting evidence ids" }),
      "stale-evidence",
    );
    await user.click(
      screen.getAllByRole("checkbox", {
        name: "I confirm this reviewed task action should be submitted.",
      })[0] as HTMLElement,
    );
    await user.click(screen.getByRole("button", { name: "Record observation" }));

    expect(
      await screen.findByText("evidence-request-reread", undefined, fullRouteWait),
    ).toBeInTheDocument();
    expect(screen.queryByText("stale-evidence")).not.toBeInTheDocument();
  }, fullRouteTestTimeout);
});
