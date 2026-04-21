import { describe, expect, it, vi } from "vitest";
import {
  createOperatorDataProvider,
  UnsupportedOperatorDataProviderOperationError,
} from "./dataProvider";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

describe("createOperatorDataProvider", () => {
  it("applies reviewed queue list filters, sorting, and pagination client-side", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        queue_name: "analyst_review",
        read_only: true,
        records: [
          {
            alert_id: "alert-003",
            review_state: "investigating",
          },
          {
            alert_id: "alert-001",
            review_state: "new",
          },
          {
            alert_id: "alert-002",
            review_state: "new",
          },
        ],
        total_records: 3,
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getList("queue", {
        filter: {
          review_state: " new ",
        },
        pagination: { page: 2, perPage: 1 },
        sort: { field: "alert_id", order: "DESC" },
      }),
    ).resolves.toEqual({
      data: [
        {
          alert_id: "alert-001",
          id: "alert-001",
          review_state: "new",
        },
      ],
      total: 2,
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect(fetchFn.mock.calls[0]?.[0]).toBe(
      "/inspect-analyst-queue?order=DESC&page=2&per_page=1&sort=alert_id&review_state=new",
    );
    expect(fetchFn.mock.calls[0]?.[1]).toEqual({
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    });
  });

  it("maps reviewed alert detail reads into react-admin record semantics", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        alert: {
          alert_id: "alert-007",
          lifecycle_state: "triaged",
        },
        alert_id: "alert-007",
        current_action_review: null,
        latest_reconciliation: {
          reconciliation_id: "recon-007",
        },
        read_only: true,
        review_state: "triaged",
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getOne("alerts", {
        id: "alert-007",
      }),
    ).resolves.toEqual({
      data: {
        alert: {
          alert_id: "alert-007",
          lifecycle_state: "triaged",
        },
        alert_id: "alert-007",
        current_action_review: null,
        id: "alert-007",
        latest_reconciliation: {
          reconciliation_id: "recon-007",
        },
        read_only: true,
        review_state: "triaged",
      },
    });

    expect(fetchFn).toHaveBeenCalledWith(
      "/inspect-alert-detail?alert_id=alert-007",
      {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      },
    );
  });

  it("uses the reviewed readiness diagnostics route for runtime readiness reads", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        status: "ready",
        read_only: true,
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getList("runtimeReadiness", {
        filter: {},
        pagination: { page: 1, perPage: 1 },
        sort: { field: "status", order: "ASC" },
      }),
    ).resolves.toEqual({
      data: [
        {
          id: "ready",
          read_only: true,
          status: "ready",
        },
      ],
      total: 1,
    });

    expect(fetchFn).toHaveBeenCalledWith("/diagnostics/readiness?order=ASC&page=1&per_page=1&sort=status", {
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    });
  });

  it("fails closed when a reviewed queue record is missing its authoritative anchor", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        queue_name: "analyst_review",
        read_only: true,
        records: [
          {
            review_state: "new",
          },
        ],
        total_records: 1,
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getList("queue", {
        filter: {},
        pagination: { page: 1, perPage: 25 },
        sort: { field: "alert_id", order: "ASC" },
      }),
    ).rejects.toThrow(
      "Resource queue record is missing authoritative identifier field alert_id.",
    );
  });

  it("requires authoritative scope metadata before advisory output reads", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        advisory_output: {
          output_kind: "recommendation",
          status: "ready",
        },
        read_only: true,
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getOne("advisoryOutput", {
        id: "advisory-001",
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );

    await expect(
      dataProvider.getOne("advisoryOutput", {
        id: "advisory-001",
        meta: {
          recordFamily: "case",
          recordId: "case-001",
        },
      }),
    ).rejects.toThrow(
      "Resource advisoryOutput requires params.id to match case:case-001.",
    );

    await expect(
      dataProvider.getOne("advisoryOutput", {
        id: "case:case-001",
        meta: {
          recordFamily: "case",
          recordId: "case-001",
        },
      }),
    ).resolves.toEqual({
      data: expect.objectContaining({
        id: "case:case-001",
        record_family: "case",
        record_id: "case-001",
      }),
    });
  });

  it("reads one action review by authoritative action_request_id without enabling list semantics", async () => {
    const fetchFn = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        action_request_id: "action-request-001",
        review_state: "approved",
        current_action_review: {
          action_request_id: "action-request-001",
          review_state: "approved",
        },
        action_review: {
          action_request_id: "action-request-001",
          review_state: "approved",
          requester_identity: "analyst-001",
        },
        case_record: {
          case_id: "case-001",
          lifecycle_state: "open",
        },
        read_only: true,
      }),
    );
    const dataProvider = createOperatorDataProvider({ fetchFn });

    await expect(
      dataProvider.getOne("actionReview", {
        id: "action-request-001",
      }),
    ).resolves.toEqual({
      data: expect.objectContaining({
        id: "action-request-001",
        action_request_id: "action-request-001",
        read_only: true,
      }),
    });

    expect(fetchFn).toHaveBeenCalledWith(
      "/inspect-action-review?action_request_id=action-request-001",
      {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      },
    );

    await expect(
      dataProvider.getList("actionReview", {
        filter: {},
        pagination: { page: 1, perPage: 25 },
        sort: { field: "id", order: "ASC" },
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
  });

  it("rejects unsupported standard-resource typos explicitly", async () => {
    const dataProvider = createOperatorDataProvider({
      fetchFn: vi.fn<typeof fetch>(),
    });

    await expect(
      dataProvider.getList("unknown-resource" as never, {
        filter: {},
        pagination: { page: 1, perPage: 25 },
        sort: { field: "id", order: "ASC" },
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );

    await expect(
      dataProvider.getOne("unknown-resource" as never, {
        id: "record-001",
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
  });

  it("rejects all mutation verbs so the adapter remains read-only", async () => {
    const dataProvider = createOperatorDataProvider({
      fetchFn: vi.fn<typeof fetch>(),
    });

    await expect(
      dataProvider.create("alerts", { data: { alert_id: "alert-001" } }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
    await expect(
      dataProvider.update("alerts", {
        data: { review_state: "triaged" },
        id: "alert-001",
        previousData: { id: "alert-001" },
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
    await expect(
      dataProvider.updateMany("alerts", {
        data: { review_state: "triaged" },
        ids: ["alert-001"],
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
    await expect(
      dataProvider.delete("alerts", {
        id: "alert-001",
        previousData: { id: "alert-001" },
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
    await expect(
      dataProvider.deleteMany("alerts", {
        ids: ["alert-001"],
      }),
    ).rejects.toThrow(
      UnsupportedOperatorDataProviderOperationError,
    );
  });
});
