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
  listSemantics?: "client";
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
      listSemantics: "client",
    },
    alerts: {
      detailPath: "/inspect-alert-detail",
      detailQueryKey: "alert_id",
      idField: "alert_id",
      listPath: "/inspect-records",
      listSemantics: "client",
      recordFamily: "alert",
    },
    cases: {
      detailPath: "/inspect-case-detail",
      detailQueryKey: "case_id",
      idField: "case_id",
      listPath: "/inspect-records",
      listSemantics: "client",
      recordFamily: "case",
    },
    runtimeReadiness: {
      detailPath: "/diagnostics/readiness",
      idField: "status",
      listPath: "/diagnostics/readiness",
      listSemantics: "client",
    },
    reconciliations: {
      detailPath: "/inspect-reconciliation-status",
      idField: "reconciliation_id",
      listPath: "/inspect-reconciliation-status",
      listSemantics: "client",
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

function isStandardResource(
  resource: string,
): resource is Exclude<OperatorResourceName, "advisoryOutput" | "actionReview"> {
  return Object.prototype.hasOwnProperty.call(RESOURCE_BINDINGS, resource);
}

function getRecordField(record: Record<string, unknown>, fieldPath: string): unknown {
  return fieldPath.split(".").reduce<unknown>((value, segment) => {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return undefined;
    }

    return (value as Record<string, unknown>)[segment];
  }, record);
}

function comparePrimitiveValues(left: unknown, right: unknown): number {
  if (left === right) {
    return 0;
  }

  if (left === null || left === undefined) {
    return 1;
  }

  if (right === null || right === undefined) {
    return -1;
  }

  if (typeof left === "number" && typeof right === "number") {
    return left - right;
  }

  if (typeof left === "boolean" && typeof right === "boolean") {
    return Number(left) - Number(right);
  }

  return String(left).localeCompare(String(right), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function matchesPrimitiveFilter(candidate: unknown, filterValue: unknown): boolean {
  if (Array.isArray(candidate)) {
    return candidate.some((item) => matchesPrimitiveFilter(item, filterValue));
  }

  if (typeof filterValue === "string") {
    const operand = filterValue.trim().toLowerCase();
    if (!operand) {
      return true;
    }

    if (candidate === null || candidate === undefined) {
      return false;
    }

    return String(candidate).toLowerCase().includes(operand);
  }

  if (
    typeof filterValue === "number" ||
    typeof filterValue === "boolean" ||
    typeof filterValue === "bigint"
  ) {
    return (
      candidate === filterValue ||
      (candidate !== null &&
        candidate !== undefined &&
        String(candidate).trim() === String(filterValue))
    );
  }

  return candidate === filterValue;
}

function matchesFilterValue(candidate: unknown, filterValue: unknown): boolean {
  if (filterValue === null || filterValue === undefined) {
    return true;
  }

  if (Array.isArray(filterValue)) {
    if (filterValue.length === 0) {
      return true;
    }

    return filterValue.some((item) => matchesPrimitiveFilter(candidate, item));
  }

  if (typeof filterValue === "object") {
    const filterObject = filterValue as Record<string, unknown>;
    const filterEntries = Object.entries(filterObject).filter(([, value]) => {
      if (value === null || value === undefined) {
        return false;
      }

      if (typeof value === "string") {
        return value.trim().length > 0;
      }

      if (Array.isArray(value)) {
        return value.length > 0;
      }

      return true;
    });

    if (filterEntries.length === 0) {
      return true;
    }

    const knownOperatorKeys = new Set([
      "contains",
      "endsWith",
      "eq",
      "equals",
      "in",
      "is",
      "ne",
      "neq",
      "not",
      "startsWith",
    ]);
    const usesKnownOperators = filterEntries.some(([key]) =>
      knownOperatorKeys.has(key),
    );

    if (usesKnownOperators) {
      return filterEntries.every(([key, value]) => {
        switch (key) {
          case "contains":
            return matchesPrimitiveFilter(candidate, value);
          case "endsWith": {
            const operand = asString(value);
            return operand !== null && candidate !== null && candidate !== undefined
              ? String(candidate).toLowerCase().endsWith(operand.toLowerCase())
              : false;
          }
          case "eq":
          case "equals":
          case "is":
            return matchesPrimitiveFilter(candidate, value);
          case "in":
            return Array.isArray(value)
              ? value.some((entry) => matchesPrimitiveFilter(candidate, entry))
              : matchesPrimitiveFilter(candidate, value);
          case "ne":
          case "neq":
          case "not":
            return !matchesPrimitiveFilter(candidate, value);
          case "startsWith": {
            const operand = asString(value);
            return operand !== null && candidate !== null && candidate !== undefined
              ? String(candidate).toLowerCase().startsWith(operand.toLowerCase())
              : false;
          }
          default:
            return true;
        }
      });
    }

    if (typeof candidate !== "object" || candidate === null || Array.isArray(candidate)) {
      return false;
    }

    return filterEntries.every(([key, value]) =>
      matchesFilterValue(
        (candidate as Record<string, unknown>)[key],
        value,
      ),
    );
  }

  return matchesPrimitiveFilter(candidate, filterValue);
}

function matchesListFilters(record: RaRecord, filter: Record<string, unknown>): boolean {
  return Object.entries(filter).every(([field, value]) => {
    if (value === null || value === undefined) {
      return true;
    }

    if (typeof value === "string" && value.trim().length === 0) {
      return true;
    }

    if (Array.isArray(value) && value.length === 0) {
      return true;
    }

    return matchesFilterValue(getRecordField(record, field), value);
  });
}

function applyClientSideListSemantics(
  records: RaRecord[],
  params: GetListParams,
): GetListResult {
  const filteredRecords = records.filter((record) =>
    matchesListFilters(record, params.filter ?? {}),
  );
  const sortField = params.sort?.field;
  const sortOrder = params.sort?.order ?? "ASC";
  const sortedRecords = sortField
    ? [...filteredRecords].sort((left, right) => {
        const comparison = comparePrimitiveValues(
          getRecordField(left, sortField),
          getRecordField(right, sortField),
        );
        return sortOrder === "DESC" ? comparison * -1 : comparison;
      })
    : filteredRecords;
  const total = sortedRecords.length;
  const page = Math.max(1, params.pagination?.page ?? 1);
  const perPage = Math.max(1, params.pagination?.perPage ?? 25);
  const start = (page - 1) * perPage;

  return {
    data: sortedRecords.slice(start, start + perPage),
    total,
  };
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
  let records: RaRecord[];
  let totalRecords: number | null = null;

  if (resource === "runtimeReadiness") {
    records = [normalizeRecord(resource, payload, binding.idField)];
  } else {
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

    records = rawRecords.map((record) =>
      normalizeRecord(resource, record, binding.idField),
    );
    totalRecords =
      typeof response.total_records === "number"
        ? response.total_records
        : records.length;
  }

  if (binding.listSemantics === "client") {
    return applyClientSideListSemantics(records, params);
  }

  return {
    data: records,
    total: totalRecords ?? records.length,
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

  const requestedId =
    typeof params.id === "string" || typeof params.id === "number"
      ? String(params.id).trim()
      : "";
  const authoritativeId = `${recordFamily}:${recordId}`;

  if (!requestedId) {
    throw new OperatorDataProviderContractError(
      "Resource advisoryOutput getOne requires a non-empty identifier.",
    );
  }

  if (requestedId !== authoritativeId) {
    throw new OperatorDataProviderContractError(
      `Resource advisoryOutput requires params.id to match ${authoritativeId}.`,
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
      id: requestedId,
      record_family: recordFamily,
      record_id: recordId,
    },
  };
}

async function getOneForActionReview(
  fetchFn: typeof fetch,
  params: GetOneParams,
): Promise<GetOneResult> {
  const requestedId =
    typeof params.id === "string" || typeof params.id === "number"
      ? String(params.id).trim()
      : "";

  if (!requestedId) {
    throw new OperatorDataProviderContractError(
      "Resource actionReview getOne requires a non-empty identifier.",
    );
  }

  const url = new URL("/inspect-action-review", "http://operator-ui.local");
  url.searchParams.set("action_request_id", requestedId);

  const payload = asObject(
    await fetchJson(fetchFn, `${url.pathname}${url.search}`),
    "Resource actionReview returned a malformed detail payload.",
  );
  const authoritativeId = asString(payload.action_request_id);
  const selectedReview = asObject(
    payload.action_review,
    "Resource actionReview detail payload is missing action_review.",
  );
  const selectedReviewId = asString(selectedReview.action_request_id);

  if (authoritativeId === null) {
    throw new OperatorDataProviderContractError(
      "Resource actionReview detail payload is missing action_request_id.",
    );
  }

  if (authoritativeId !== requestedId) {
    throw new OperatorDataProviderContractError(
      `Resource actionReview requires response action_request_id to match ${requestedId}.`,
    );
  }
  if (selectedReviewId === null) {
    throw new OperatorDataProviderContractError(
      "Resource actionReview detail payload is missing action_review.action_request_id.",
    );
  }
  if (selectedReviewId !== requestedId) {
    throw new OperatorDataProviderContractError(
      `Resource actionReview requires action_review.action_request_id to match ${requestedId}.`,
    );
  }

  return {
    data: {
      ...payload,
      id: authoritativeId,
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

      if (!isStandardResource(resource)) {
        return rejectUnsupported("getList", resource);
      }

      return getListForStandardResource(fetchFn, resource, params);
    },
    getMany: (_resource) => rejectUnsupported("getMany", _resource),
    getManyReference: (_resource) =>
      rejectUnsupported("getManyReference", _resource),
    getOne(resource, params) {
      if (resource === "advisoryOutput") {
        return getOneForAdvisoryOutput(fetchFn, params);
      }

      if (resource === "actionReview") {
        return getOneForActionReview(fetchFn, params);
      }

      if (!isStandardResource(resource)) {
        return rejectUnsupported("getOne", resource);
      }

      return getOneForStandardResource(fetchFn, resource, params);
    },
    update: (_resource) => rejectUnsupported("update", _resource),
    updateMany: (_resource) => rejectUnsupported("updateMany", _resource),
  };
}

export const operatorDataProvider = createOperatorDataProvider();
