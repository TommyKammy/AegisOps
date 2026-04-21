import type {
  DataProvider,
  GetListParams,
  GetListResult,
  GetOneParams,
  GetOneResult,
  RaRecord,
} from "react-admin";

type OperatorResourceName =
  | "queue"
  | "alerts"
  | "cases"
  | "runtimeReadiness"
  | "reconciliations"
  | "advisoryOutput"
  | "actionReview";

interface OperatorDataProviderConfig {
  fetchFn?: typeof fetch;
}

interface OperatorRecordFamilyListResponse {
  records: unknown;
  total_records?: unknown;
}

interface OperatorResourceBinding {
  detailPath?: string;
  detailQueryKey?: string;
  idField: string;
  listPath?: string;
  recordFamily?: string;
}

const JSON_HEADERS = {
  Accept: "application/json",
};

const RESOURCE_BINDINGS: Record<Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">, OperatorResourceBinding> =
  {
    queue: {
      idField: "alert_id",
      listPath: "/inspect-analyst-queue",
    },
    alerts: {
      detailPath: "/inspect-alert-detail",
      detailQueryKey: "alert_id",
      idField: "alert_id",
      listPath: "/inspect-records",
      recordFamily: "alert",
    },
    cases: {
      detailPath: "/inspect-case-detail",
      detailQueryKey: "case_id",
      idField: "case_id",
      listPath: "/inspect-records",
      recordFamily: "case",
    },
    runtimeReadiness: {
      detailPath: "/inspect-readiness-diagnostics",
      idField: "status",
      listPath: "/inspect-readiness-diagnostics",
    },
    reconciliations: {
      detailPath: "/inspect-reconciliation-status",
      idField: "reconciliation_id",
      listPath: "/inspect-reconciliation-status",
    },
  };

export class UnsupportedOperatorDataProviderOperationError extends Error {}

class OperatorDataProviderContractError extends Error {}

function rejectUnsupported(method: string, resource: string): Promise<never> {
  return Promise.reject(
    new UnsupportedOperatorDataProviderOperationError(
      `The reviewed operator shell does not support ${method} for resource ${resource}.`,
    ),
  );
}

function asObject(value: unknown, message: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new OperatorDataProviderContractError(message);
  }

  return value as Record<string, unknown>;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function appendQuery(url: URL, params: Record<string, string | null | undefined>) {
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }
}

function normalizeRecord(
  resource: string,
  value: unknown,
  idField: string,
): RaRecord {
  const record = asObject(
    value,
    `Resource ${resource} returned a non-object record.`,
  );
  const identifier = asString(record[idField]);

  if (identifier === null) {
    throw new OperatorDataProviderContractError(
      `Resource ${resource} record is missing authoritative identifier field ${idField}.`,
    );
  }

  return {
    ...record,
    id: identifier,
  };
}

function buildListUrl(
  resource: Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
  params: GetListParams,
): string {
  const binding = RESOURCE_BINDINGS[resource];
  if (!binding.listPath) {
    throw new UnsupportedOperatorDataProviderOperationError(
      `The reviewed operator shell does not support getList for resource ${resource}.`,
    );
  }

  const page = params.pagination?.page ?? 1;
  const perPage = params.pagination?.perPage ?? 25;
  const sortField = params.sort?.field ?? RESOURCE_BINDINGS[resource].idField;
  const sortOrder = params.sort?.order ?? "ASC";

  const url = new URL(binding.listPath, "http://operator-ui.local");
  appendQuery(url, {
    family: binding.recordFamily,
    order: sortOrder,
    page: String(page),
    per_page: String(perPage),
    sort: sortField,
  });

  for (const [key, value] of Object.entries(params.filter)) {
    if (typeof value === "string" && value.trim()) {
      url.searchParams.set(key, value.trim());
    }
  }

  return `${url.pathname}${url.search}`;
}

async function fetchJson(fetchFn: typeof fetch, path: string): Promise<unknown> {
  const response = await fetchFn(path, {
    credentials: "include",
    headers: JSON_HEADERS,
  });

  if (response.status === 401 || response.status === 403) {
    const error = new Error("Backend operator boundary rejected the request.");
    Object.assign(error, { status: response.status });
    throw error;
  }

  if (!response.ok) {
    throw new OperatorDataProviderContractError(
      `Unexpected operator boundary response status ${response.status} for ${path}.`,
    );
  }

  try {
    return await response.json();
  } catch {
    throw new OperatorDataProviderContractError(
      `Operator boundary response for ${path} is not valid JSON.`,
    );
  }
}

async function getListForStandardResource(
  fetchFn: typeof fetch,
  resource: Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
  params: GetListParams,
): Promise<GetListResult> {
  const binding = RESOURCE_BINDINGS[resource];
  const payload = await fetchJson(fetchFn, buildListUrl(resource, params));

  if (resource === "runtimeReadiness") {
    const record = normalizeRecord(resource, payload, binding.idField);
    return {
      data: [record],
      total: 1,
    };
  }

  const response = asObject(
    payload,
    `Resource ${resource} returned a malformed list payload.`,
  ) as unknown as OperatorRecordFamilyListResponse;
  const rawRecords = Array.isArray(response.records) ? response.records : null;

  if (rawRecords === null) {
    throw new OperatorDataProviderContractError(
      `Resource ${resource} list payload is missing records.`,
    );
  }

  const data = rawRecords.map((record) =>
    normalizeRecord(resource, record, binding.idField),
  );
  const total =
    typeof response.total_records === "number"
      ? response.total_records
      : data.length;

  return {
    data,
    total,
  };
}

function buildDetailPath(
  resource: Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
  params: GetOneParams,
): string {
  const binding = RESOURCE_BINDINGS[resource];

  if (!binding.detailPath) {
    throw new UnsupportedOperatorDataProviderOperationError(
      `The reviewed operator shell does not support getOne for resource ${resource}.`,
    );
  }

  if (!binding.detailQueryKey) {
    return binding.detailPath;
  }

  const identifier =
    typeof params.id === "string" || typeof params.id === "number"
      ? String(params.id).trim()
      : "";
  if (!identifier) {
    throw new OperatorDataProviderContractError(
      `Resource ${resource} getOne requires a non-empty identifier.`,
    );
  }

  const url = new URL(binding.detailPath, "http://operator-ui.local");
  url.searchParams.set(binding.detailQueryKey, identifier);
  return `${url.pathname}${url.search}`;
}

async function getOneForStandardResource(
  fetchFn: typeof fetch,
  resource: Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
  params: GetOneParams,
): Promise<GetOneResult> {
  const binding = RESOURCE_BINDINGS[resource];
  const payload = await fetchJson(fetchFn, buildDetailPath(resource, params));

  if (resource === "reconciliations") {
    const response = asObject(
      payload,
      "Resource reconciliations returned a malformed detail payload.",
    ) as unknown as OperatorRecordFamilyListResponse;
    const rawRecords = Array.isArray(response.records) ? response.records : null;
    if (rawRecords === null) {
      throw new OperatorDataProviderContractError(
        "Resource reconciliations detail payload is missing records.",
      );
    }

    const targetId = String(params.id).trim();
    const record = rawRecords.find((candidate) => {
      const value = asObject(
        candidate,
        "Resource reconciliations returned a non-object record.",
      );
      return asString(value.reconciliation_id) === targetId;
    });

    if (record === undefined) {
      throw new OperatorDataProviderContractError(
        `Resource reconciliations is missing authoritative record ${targetId}.`,
      );
    }

    return {
      data: normalizeRecord(resource, record, binding.idField),
    };
  }

  return {
    data: normalizeRecord(resource, payload, binding.idField),
  };
}

async function getOneForAdvisoryOutput(
  fetchFn: typeof fetch,
  params: GetOneParams,
): Promise<GetOneResult> {
  const meta =
    params.meta && typeof params.meta === "object"
      ? (params.meta as Record<string, unknown>)
      : null;
  const recordFamily = asString(meta?.recordFamily);
  const recordId = asString(meta?.recordId);

  if (!recordFamily || !recordId) {
    throw new UnsupportedOperatorDataProviderOperationError(
      "The reviewed operator shell requires authoritative recordFamily and recordId metadata for resource advisoryOutput.",
    );
  }

  const url = new URL("/inspect-advisory-output", "http://operator-ui.local");
  url.searchParams.set("family", recordFamily);
  url.searchParams.set("record_id", recordId);

  const payload = asObject(
    await fetchJson(fetchFn, `${url.pathname}${url.search}`),
    "Resource advisoryOutput returned a malformed detail payload.",
  );

  return {
    data: {
      ...payload,
      id: `${recordFamily}:${recordId}`,
      record_family: recordFamily,
      record_id: recordId,
    },
  };
}

export function createOperatorDataProvider({
  fetchFn = fetch,
}: OperatorDataProviderConfig = {}): DataProvider {
  return {
    create: (_resource) => rejectUnsupported("create", _resource),
    delete: (_resource) => rejectUnsupported("delete", _resource),
    deleteMany: (_resource) => rejectUnsupported("deleteMany", _resource),
    getList(resource, params) {
      if (resource === "advisoryOutput" || resource === "actionReview") {
        return rejectUnsupported("getList", resource);
      }

      return getListForStandardResource(
        fetchFn,
        resource as Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
        params,
      );
    },
    getMany: (_resource) => rejectUnsupported("getMany", _resource),
    getManyReference: (_resource) =>
      rejectUnsupported("getManyReference", _resource),
    getOne(resource, params) {
      if (resource === "advisoryOutput") {
        return getOneForAdvisoryOutput(fetchFn, params);
      }

      if (resource === "actionReview") {
        return rejectUnsupported("getOne", resource);
      }

      return getOneForStandardResource(
        fetchFn,
        resource as Exclude<OperatorResourceName, "advisoryOutput" | "actionReview">,
        params,
      );
    },
    update: (_resource) => rejectUnsupported("update", _resource),
    updateMany: (_resource) => rejectUnsupported("updateMany", _resource),
  };
}

export const operatorDataProvider = createOperatorDataProvider();
