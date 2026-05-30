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

function createEvidencePack(overrides: Record<string, unknown> = {}) {
  return {
    authoritative_workflow_truth: false,
    case_id: "case-456",
    confidence_state: "related_entity_not_authoritative",
    conflict_state: "unresolved_conflict",
    custody_reference: "custody://case-456/evidence-pack-001",
    custody_state: "complete",
    evidence_pack_id: "evidence-pack-001",
    freshness_state: "stale_review_required",
    operator_visible: true,
    provenance_reference: "provenance://case-456/enrichment-001",
    provenance_state: "bound",
    source_id: "malwarebazaar_hash_reputation",
    source_state: "degraded",
    uncertainty_label: "review_required",
    workflow_authority: "none",
    ...overrides,
  };
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
    linked_evidence_records: [],
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
      within(rows[0] as HTMLElement).getByText("evidence-pack-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("malwarebazaar_hash_reputation"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("stale_review_required"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("unresolved_conflict"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("related_entity_not_authoritative"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("review_required"),
    ).toBeInTheDocument();
    expect(within(rows[0] as HTMLElement).getByText("degraded")).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("custody://case-456/evidence-pack-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("provenance://case-456/enrichment-001"),
    ).toBeInTheDocument();
    expect(
      within(rows[0] as HTMLElement).getByText("Subordinate evidence context only"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Evidence pack can close case")).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence pack proves RC readiness")).not.toBeInTheDocument();
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
    ["hidden conflict label", createEvidencePack({ conflict_state: "" })],
    ["missing custody display", createEvidencePack({ custody_reference: null })],
    ["missing provenance display", createEvidencePack({ provenance_reference: null })],
    ["evidence truth", createEvidencePack({ authoritative_workflow_truth: true })],
    ["workflow authority", createEvidencePack({ workflow_authority: "close_case" })],
    ["RC readiness claim", createEvidencePack({ release_readiness_claim: "rc_ready" })],
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
                      evidence_pack_id: "evidence-pack-reread",
                      freshness_state: "fresh",
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
      await screen.findByText("evidence-pack-001", undefined, fullRouteWait),
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
      await screen.findByText("evidence-pack-reread", undefined, fullRouteWait),
    ).toBeInTheDocument();
    expect(screen.queryByText("stale-evidence")).not.toBeInTheDocument();
  }, fullRouteTestTimeout);
});
