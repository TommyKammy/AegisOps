import type { GetOneParams, GetOneResult } from "react-admin";
import {
  OperatorDataProviderAuthorizationError,
  OperatorDataProviderContractError,
  UnsupportedOperatorDataProviderOperationError,
} from "./errors";
import { JSON_HEADERS, RESOURCE_BINDINGS } from "./resourceBindings";
import type { OperatorRecord, StandardOperatorResourceName } from "./types";

export function asObject(
  value: unknown,
  message: string,
): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new OperatorDataProviderContractError(message);
  }

  return value as Record<string, unknown>;
}

export function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

export function appendQuery(
  url: URL,
  params: Record<string, string | null | undefined>,
) {
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }
}

export function getRecordField(
  record: Record<string, unknown>,
  fieldPath: string,
): unknown {
  return fieldPath.split(".").reduce<unknown>((value, segment) => {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return undefined;
    }

    return (value as Record<string, unknown>)[segment];
  }, record);
}

export function normalizeRecord(
  resource: string,
  value: unknown,
  idField: string,
): OperatorRecord {
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

export async function fetchJson(
  fetchFn: typeof fetch,
  path: string,
): Promise<unknown> {
  const response = await fetchFn(path, {
    credentials: "include",
    headers: JSON_HEADERS,
  });

  if (response.status === 401 || response.status === 403) {
    throw new OperatorDataProviderAuthorizationError(response.status);
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

export function buildDetailPath(
  resource: StandardOperatorResourceName,
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

export function resolveReconciliationRecord(
  payload: unknown,
  params: GetOneParams,
): GetOneResult {
  const response = asObject(
    payload,
    "Resource reconciliations returned a malformed detail payload.",
  );
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
    data: normalizeRecord("reconciliations", record, "reconciliation_id"),
  };
}
