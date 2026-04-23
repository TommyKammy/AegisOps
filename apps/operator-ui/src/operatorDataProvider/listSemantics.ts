import type { GetListParams, GetListResult } from "react-admin";
import { OperatorDataProviderContractError, UnsupportedOperatorDataProviderOperationError } from "./errors";
import { RESOURCE_BINDINGS } from "./resourceBindings";
import { appendQuery, asObject, asString, fetchJson, getRecordField, normalizeRecord } from "./shared";
import type { OperatorRecordFamilyListResponse, StandardListReaderOptions, StandardOperatorResourceName } from "./types";

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

function matchesListFilters(
  record: Record<string, unknown>,
  filter: Record<string, unknown>,
): boolean {
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
  records: Record<string, unknown>[],
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

function buildListUrl(
  resource: StandardOperatorResourceName,
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

export async function getListForStandardResource({
  binding,
  fetchFn,
  params,
  resource,
}: StandardListReaderOptions): Promise<GetListResult> {
  const payload = await fetchJson(fetchFn, buildListUrl(resource, params));
  let records: Record<string, unknown>[];
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
