import type { GetOneParams, GetOneResult } from "react-admin";
import { OperatorDataProviderContractError, UnsupportedOperatorDataProviderOperationError } from "./errors";
import { RESOURCE_BINDINGS } from "./resourceBindings";
import { asObject, asString, buildDetailPath, fetchJson, normalizeRecord, resolveReconciliationRecord } from "./shared";
import type { StandardOperatorResourceName } from "./types";

const TODAY_VIEW_LANES = [
  "priority",
  "stale_work",
  "pending_approvals",
  "degraded_sources",
  "reconciliation_mismatches",
  "evidence_gaps",
  "ai_suggested_focus",
] as const;

const CASE_TIMELINE_SEGMENTS = [
  "wazuh_signal",
  "aegisops_alert",
  "evidence",
  "ai_summary",
  "recommendation",
  "action_request",
  "approval",
  "shuffle_receipt",
  "reconciliation",
] as const;

const CASE_TIMELINE_STATES = new Set([
  "normal",
  "missing",
  "degraded",
  "stale",
  "mismatch",
  "unsupported",
]);

const CASE_TIMELINE_AUTHORITY_POSTURES = new Set([
  "authoritative_aegisops_record",
  "subordinate_context",
]);

const CASE_TIMELINE_CONTRACT_VERSION = "phase-56-3";

export async function getOneForStandardResource(
  fetchFn: typeof fetch,
  resource: StandardOperatorResourceName,
  params: GetOneParams,
): Promise<GetOneResult> {
  const binding = RESOURCE_BINDINGS[resource];
  const payload = await fetchJson(fetchFn, buildDetailPath(resource, params));

  if (resource === "reconciliations") {
    return resolveReconciliationRecord(payload, params);
  }

  if (resource === "cases") {
    validateCaseTimelineProjection(payload, String(params.id).trim());
  }

  return {
    data: normalizeRecord(resource, payload, binding.idField),
  };
}

function validateCaseTimelineProjection(payload: unknown, requestedCaseId: string) {
  const response = asObject(
    payload,
    "Resource cases returned a malformed detail payload.",
  );
  const projectionValue = response.case_timeline_projection;

  if (projectionValue === undefined || projectionValue === null) {
    return;
  }

  const projection = asObject(
    projectionValue,
    "Resource cases case_timeline_projection must be an object.",
  );
  const caseId = asString(projection.case_id);
  const contractVersion = asString(projection.contract_version);
  const segments = Array.isArray(projection.segments)
    ? projection.segments
    : null;
  const projectionSource = asString(projection.projection_source);

  if (caseId === null || contractVersion === null || segments === null) {
    throw new OperatorDataProviderContractError(
      "Resource cases case_timeline_projection is missing case_id, contract_version, or segments.",
    );
  }
  if (contractVersion !== CASE_TIMELINE_CONTRACT_VERSION) {
    throw new OperatorDataProviderContractError(
      `Resource cases case_timeline_projection requires contract_version ${CASE_TIMELINE_CONTRACT_VERSION}; received ${contractVersion}.`,
    );
  }
  if (caseId !== requestedCaseId) {
    throw new OperatorDataProviderContractError(
      `Resource cases case_timeline_projection requires case_id to match ${requestedCaseId}.`,
    );
  }
  if (
    (projection.cache_sourced !== undefined && projection.cache_sourced !== false) ||
    (projection.stale_cache !== undefined && projection.stale_cache !== false) ||
    ["browser_cache", "ui_cache", "cache"].includes(projectionSource ?? "")
  ) {
    throw new OperatorDataProviderContractError(
      "Resource cases rejects cache-sourced case timeline truth.",
    );
  }
  if (
    projection.projection_authority_allowed !== false ||
    projection.inferred_linkage_allowed !== false
  ) {
    throw new OperatorDataProviderContractError(
      "Resource cases case_timeline_projection must reject projection authority and inferred linkage.",
    );
  }
  if (segments.length !== CASE_TIMELINE_SEGMENTS.length) {
    throw new OperatorDataProviderContractError(
      "Resource cases case_timeline_projection must include every reviewed segment.",
    );
  }

  segments.forEach((segmentValue, index) => {
    const segment = asObject(
      segmentValue,
      "Resource cases case_timeline_projection segment must be an object.",
    );
    const segmentName = asString(segment.segment);
    const state = asString(segment.state);
    const authorityPosture = asString(segment.authority_posture);
    const binding = asObject(
      segment.backend_record_binding,
      "Resource cases case_timeline_projection segment is missing backend_record_binding.",
    );
    const recordFamily = asString(binding.record_family);
    const recordId = asString(binding.record_id);
    const incompleteReason = asString(segment.incomplete_reason);

    if (segmentName !== CASE_TIMELINE_SEGMENTS[index]) {
      throw new OperatorDataProviderContractError(
        "Resource cases case_timeline_projection segment order or type is unsupported.",
      );
    }
    if (state === null || !CASE_TIMELINE_STATES.has(state)) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} has unsupported state.`,
      );
    }
    if (
      authorityPosture === null ||
      !CASE_TIMELINE_AUTHORITY_POSTURES.has(authorityPosture)
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} has unsupported authority posture.`,
      );
    }
    if (recordFamily === null) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} is missing record_family.`,
      );
    }
    if (binding.direct_binding_required !== true) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} must require direct binding.`,
      );
    }
    if (segment.operator_visible !== true) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} must stay operator visible.`,
      );
    }
    if (segment.projection_can_complete_segment !== false) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} cannot complete workflow truth from display state.`,
      );
    }
    if (recordId === null && incompleteReason === null) {
      throw new OperatorDataProviderContractError(
        `Resource cases case_timeline_projection segment ${segmentName} without record_id requires incomplete_reason.`,
      );
    }
  });
}

export async function getOneForAdvisoryOutput(
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

function validateTodayLaneItem(
  lane: string,
  item: unknown,
): Record<string, unknown> {
  const record = asObject(
    item,
    `Resource todayView lane ${lane} returned a non-object item.`,
  );
  const id = asString(record.id);
  const title = asString(record.title);
  const state = asString(record.state);
  const anchor = asObject(
    record.authoritative_record,
    `Resource todayView lane ${lane} item is missing authoritative_record.`,
  );

  if (id === null || title === null || state === null) {
    throw new OperatorDataProviderContractError(
      `Resource todayView lane ${lane} item is missing id, title, or state.`,
    );
  }

  if (asString(anchor.family) === null || asString(anchor.id) === null) {
    throw new OperatorDataProviderContractError(
      `Resource todayView lane ${lane} item authoritative_record is missing family or id.`,
    );
  }

  if (lane === "ai_suggested_focus" && record.advisory_only !== true) {
    throw new OperatorDataProviderContractError(
      "Resource todayView ai_suggested_focus items must be advisory_only.",
    );
  }

  return record;
}

export async function getOneForTodayView(
  fetchFn: typeof fetch,
): Promise<GetOneResult> {
  const payload = asObject(
    await fetchJson(fetchFn, "/inspect-today-view"),
    "Resource todayView returned a malformed detail payload.",
  );
  const projectionId = asString(payload.projection_id);
  const contractVersion = asString(
    payload.today_view_projection_contract_version,
  );
  const lanes = asObject(
    payload.lanes,
    "Resource todayView detail payload is missing lanes.",
  );

  if (projectionId === null || contractVersion === null) {
    throw new OperatorDataProviderContractError(
      "Resource todayView detail payload is missing projection_id or contract version.",
    );
  }

  if (payload.stale_cache !== false) {
    throw new OperatorDataProviderContractError(
      "Resource todayView requires stale_cache=false and rejects stale or malformed projection cache guidance.",
    );
  }

  if (payload.read_only !== true) {
    throw new OperatorDataProviderContractError(
      "Resource todayView detail payload must be read_only.",
    );
  }

  const normalizedLanes = TODAY_VIEW_LANES.reduce<Record<string, unknown[]>>(
    (result, lane) => {
      const rawLane = lanes[lane];
      if (!Array.isArray(rawLane)) {
        throw new OperatorDataProviderContractError(
          `Resource todayView detail payload is missing lane ${lane}.`,
        );
      }

      result[lane] = rawLane.map((item) => validateTodayLaneItem(lane, item));
      return result;
    },
    {},
  );

  return {
    data: {
      ...payload,
      id: "current",
      lanes: normalizedLanes,
    },
  };
}

export async function getOneForActionReview(
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
