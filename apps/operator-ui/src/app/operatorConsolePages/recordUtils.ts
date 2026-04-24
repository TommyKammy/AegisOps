export type UnknownRecord = Record<string, unknown>;

export function asRecord(value: unknown): UnknownRecord | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as UnknownRecord;
}

export function asRecordArray(value: unknown): UnknownRecord[] {
  return Array.isArray(value)
    ? value.map((entry) => asRecord(entry)).filter((entry): entry is UnknownRecord => entry !== null)
    : [];
}

export function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export function isAllowedExternalHref(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value
        .map((entry) => asString(entry))
        .filter((entry): entry is string => entry !== null)
    : [];
}

export function getPath(record: UnknownRecord | null, path: string): unknown {
  if (record === null) {
    return undefined;
  }

  return path.split(".").reduce<unknown>((value, segment) => {
    const next = asRecord(value);
    return next?.[segment];
  }, record);
}

export function formatLabel(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not available";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const flattened = value
      .map((entry) => formatValue(entry))
      .filter((entry) => entry !== "Not available");
    return flattened.length > 0 ? flattened.join(", ") : "Not available";
  }

  return JSON.stringify(value);
}

export function statusTone(
  status: string | null,
): "default" | "error" | "info" | "success" | "warning" {
  if (status === null) {
    return "default";
  }

  const normalized = status.toLowerCase();
  if (
    normalized.includes("failed") ||
    normalized.includes("forbidden") ||
    normalized.includes("mismatch") ||
    normalized.includes("missing") ||
    normalized.includes("rejected")
  ) {
    return "error";
  }
  if (
    normalized.includes("degraded") ||
    normalized.includes("pending") ||
    normalized.includes("delayed") ||
    normalized.includes("expired")
  ) {
    return "warning";
  }
  if (
    normalized.includes("approved") ||
    normalized.includes("completed") ||
    normalized.includes("executed") ||
    normalized.includes("reconciled") ||
    normalized.includes("matched") ||
    normalized.includes("healthy") ||
    normalized.includes("ready") ||
    normalized.includes("open")
  ) {
    return "success";
  }
  if (normalized.includes("review") || normalized.includes("triage")) {
    return "info";
  }

  return "default";
}
