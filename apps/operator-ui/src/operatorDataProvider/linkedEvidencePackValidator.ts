import { OperatorDataProviderContractError } from "./errors";
import { asObject, asString } from "./shared";

const EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES = new Set([
  "browser_state",
  "browser_cache",
  "ui_cache",
  "cache",
]);
const EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE =
  "subordinate_evidence_context_only";
const EVIDENCE_PACK_SUPPORTED_SOURCE_ID = "malwarebazaar_hash_reputation";
const EVIDENCE_PACK_CONFIDENCE_POSTURE =
  "external_hash_reputation_subordinate_context";
const EVIDENCE_PACK_FRESHNESS_WINDOW_MS = 6 * 60 * 60 * 1000;
const EVIDENCE_PACK_ALLOWED_LABELS = {
  consumer: new Set(["case_workbench"]),
  status: new Set(["available", "degraded", "unavailable"]),
  freshness_state: new Set(["fresh", "stale"]),
  custody_state: new Set(["complete"]),
  confidence_state: new Set(["present"]),
  provenance_state: new Set(["bound"]),
  conflict_state: new Set(["conflicting", "none"]),
  source_state: new Set(["available", "degraded", "unavailable"]),
  uncertainty_label: new Set([
    "related_entity_not_authoritative",
    "stale_review_required",
    "unresolved_conflict",
    "source_unavailable",
  ]),
};
const EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS = new Set([
  "stale_reputation",
  "conflicting_enrichment",
  "source_stale",
]);
const EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS = new Set([
  "source_denied",
  "source_unavailable",
]);
const EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS = new Set([
  "reviewed_file_hash",
  "enrichment_request_id",
  "collection_timestamp",
  "response_digest",
  "aegisops_evidence_record_id",
]);
const EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS = new Set([
  "request_binding",
  "case_binding",
  "target_binding",
  "source_id",
  "enrichment_request_id",
  "collection_timestamp",
  "response_digest",
  "custody_reference",
  "authority_posture",
]);
const EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS = new Set([
  "posture",
  "freshness",
  "ambiguity_badge",
  "source_native_score_authority",
]);
const EVIDENCE_PACK_CONTRACT_FIELDS = new Set([
  "evidence_request_id",
  "case_id",
  "source_id",
  "consumer",
  "status",
  "freshness_state",
  "custody_state",
  "confidence_state",
  "provenance_state",
  "conflict_state",
  "source_state",
  "uncertainty_label",
  "authority_posture",
  "workflow_authority",
  "degraded_reasons",
  "unavailable_reasons",
  "authoritative_workflow_truth",
  "custody",
  "provenance",
  "confidence",
]);
const EVIDENCE_PACK_RECOGNIZED_FIELDS = new Set([
  ...EVIDENCE_PACK_CONTRACT_FIELDS,
  "cache_sourced",
  "stale_cache",
  "projection_source",
  "operator_visible",
  "release_readiness_claim",
  "rc_readiness_claim",
  "gate_readiness_claim",
]);
function validateEvidencePackLabel(
  fieldName: keyof typeof EVIDENCE_PACK_ALLOWED_LABELS,
  value: string,
  evidenceRequestId: string,
) {
  if (!EVIDENCE_PACK_ALLOWED_LABELS[fieldName].has(value)) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} has an unsupported evidence-pack label.`,
    );
  }
}

function validateEvidencePackReasons(
  value: unknown,
  allowedReasons: Set<string>,
) {
  if (value === undefined || value === null) {
    throw new OperatorDataProviderContractError(
      "Resource cases linked_evidence_packs item has unsupported evidence-pack reasons.",
    );
  }
  if (!Array.isArray(value)) {
    throw new OperatorDataProviderContractError(
      "Resource cases linked_evidence_packs item has unsupported evidence-pack reasons.",
    );
  }
  value.forEach((reason) => {
    if (!asString(reason) || !allowedReasons.has(asString(reason) ?? "")) {
      throw new OperatorDataProviderContractError(
        "Resource cases linked_evidence_packs item has unsupported evidence-pack reasons.",
      );
    }
  });
}

function validateEvidencePackMetadataMap(
  value: Record<string, unknown>,
  requiredFields: Set<string>,
  evidenceRequestId: string,
) {
  const fieldNames = Object.keys(value);
  if (
    fieldNames.length !== requiredFields.size ||
    fieldNames.some((fieldName) => !requiredFields.has(fieldName)) ||
    Array.from(requiredFields).some((fieldName) => asString(value[fieldName]) === null)
  ) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} is missing required evidence-pack metadata.`,
    );
  }
}

function isSupportedReviewedHash(value: string | null) {
  return (
    value !== null &&
    /^(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$/.test(value)
  );
}

function isSha256Digest(value: string | null) {
  return value !== null && /^sha256:[0-9a-fA-F]{64}$/.test(value);
}

function isAwareTimestamp(value: string | null) {
  if (value === null) {
    return false;
  }
  const match = value?.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/,
  );
  if (!match || Number.isNaN(Date.parse(value))) {
    return false;
  }

  const [, yearText, monthText, dayText, hourText, minuteText, secondText, zoneText] =
    match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const offsetHour =
    zoneText === "Z" ? 0 : Number(zoneText.slice(1, 3));
  const offsetMinute =
    zoneText === "Z" ? 0 : Number(zoneText.slice(4, 6));
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();

  return (
    month >= 1 &&
    month <= 12 &&
    day >= 1 &&
    day <= daysInMonth &&
    hour >= 0 &&
    hour <= 23 &&
    minute >= 0 &&
    minute <= 59 &&
    second >= 0 &&
    second <= 59 &&
    offsetHour >= 0 &&
    offsetHour <= 23 &&
    offsetMinute >= 0 &&
    offsetMinute <= 59
  );
}

function validateEvidencePackMetadataFormats(
  custody: Record<string, unknown>,
  provenance: Record<string, unknown>,
  evidenceRequestId: string,
) {
  if (
    !isSupportedReviewedHash(asString(custody.reviewed_file_hash)) ||
    !isSha256Digest(asString(custody.response_digest)) ||
    !isAwareTimestamp(asString(custody.collection_timestamp)) ||
    !isAwareTimestamp(asString(provenance.collection_timestamp))
  ) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} has invalid evidence-pack metadata.`,
    );
  }
}

function validateEvidencePackFreshnessWindow(
  custody: Record<string, unknown>,
  freshnessState: string,
  evidenceRequestId: string,
) {
  const collectionTimestamp = asString(custody.collection_timestamp);
  if (collectionTimestamp === null || !isAwareTimestamp(collectionTimestamp)) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} has invalid evidence-pack metadata.`,
    );
  }

  const ageMs = Date.now() - Date.parse(collectionTimestamp);
  if (
    ageMs < 0 ||
    (freshnessState === "fresh" && ageMs > EVIDENCE_PACK_FRESHNESS_WINDOW_MS) ||
    (freshnessState === "stale" && ageMs <= EVIDENCE_PACK_FRESHNESS_WINDOW_MS)
  ) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} has an invalid evidence-pack freshness window.`,
    );
  }
}

function expectedEvidencePackUncertaintyLabel(
  status: string,
  freshnessState: string,
  degradedReasons: string[],
  unavailableReasons: string[],
) {
  if (status === "unavailable" || unavailableReasons.length > 0) {
    return "source_unavailable";
  }
  if (degradedReasons.includes("conflicting_enrichment")) {
    return "unresolved_conflict";
  }
  if (
    freshnessState === "stale" ||
    degradedReasons.includes("stale_reputation") ||
    degradedReasons.includes("source_stale")
  ) {
    return "stale_review_required";
  }
  return "related_entity_not_authoritative";
}

function evidencePackReasonList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((reason) => asString(reason)).filter((reason): reason is string => reason !== null)
    : [];
}

function linkedEvidenceRecordCustodyReference(
  response: Record<string, unknown>,
  evidenceRecordId: string,
  evidenceRequestId: string,
) {
  if (!Array.isArray(response.linked_evidence_records)) {
    throw new OperatorDataProviderContractError(
      `Resource cases linked_evidence_packs item ${evidenceRequestId} must be backed by linked evidence records.`,
    );
  }

  for (const recordValue of response.linked_evidence_records) {
    const record = asObject(
      recordValue,
      "Resource cases linked_evidence_records item must be an object.",
    );
    if (asString(record.evidence_id) !== evidenceRecordId) {
      continue;
    }
    const provenance = asObject(
      record.provenance,
      `Resource cases linked_evidence_packs item ${evidenceRequestId} must be backed by linked evidence provenance.`,
    );
    const custodyReference = asString(provenance.custody_reference);
    if (custodyReference === null) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} must keep custody reference bound to the linked evidence record.`,
      );
    }
    return custodyReference;
  }

  throw new OperatorDataProviderContractError(
    `Resource cases linked_evidence_packs item ${evidenceRequestId} must be backed by linked evidence records.`,
  );
}

function validateEvidencePackReasonConsistency(
  pack: Record<string, unknown>,
  confidence: Record<string, unknown>,
  labels: {
    status: string;
    freshnessState: string;
    conflictState: string;
    sourceState: string;
    uncertaintyLabel: string;
  },
) {
  const degradedReasons = evidencePackReasonList(pack.degraded_reasons);
  const unavailableReasons = evidencePackReasonList(pack.unavailable_reasons);
  const inconsistentMessage =
    "Resource cases linked_evidence_packs item has inconsistent evidence-pack reasons.";

  if (
    degradedReasons.includes("source_stale") ||
    unavailableReasons.includes("source_denied")
  ) {
    throw new OperatorDataProviderContractError(inconsistentMessage);
  }

  if (
    (labels.status === "available" &&
      (degradedReasons.length > 0 || unavailableReasons.length > 0)) ||
    (labels.status === "degraded" &&
      (degradedReasons.length === 0 || unavailableReasons.length > 0)) ||
    (labels.status === "unavailable" && unavailableReasons.length === 0)
  ) {
    throw new OperatorDataProviderContractError(inconsistentMessage);
  }
  if (
    degradedReasons.includes("stale_reputation") !==
    (labels.freshnessState === "stale")
  ) {
    throw new OperatorDataProviderContractError(inconsistentMessage);
  }
  const expectedConflictState = degradedReasons.includes("conflicting_enrichment")
    ? "conflicting"
    : "none";
  const expectedSourceState =
    labels.status === "unavailable" || unavailableReasons.length > 0
      ? "unavailable"
      : degradedReasons.includes("source_stale")
        ? "degraded"
        : "available";

  if (
    labels.conflictState !== expectedConflictState ||
    labels.sourceState !== expectedSourceState ||
    labels.uncertaintyLabel !==
      expectedEvidencePackUncertaintyLabel(
        labels.status,
        labels.freshnessState,
        degradedReasons,
        unavailableReasons,
      ) ||
    asString(confidence.freshness) !== labels.freshnessState ||
    asString(confidence.ambiguity_badge) !==
      (degradedReasons.includes("conflicting_enrichment")
        ? "unresolved"
        : "related-entity")
  ) {
    throw new OperatorDataProviderContractError(inconsistentMessage);
  }
}

export function validateLinkedEvidencePacks(payload: unknown, requestedCaseId: string) {
  const response = asObject(
    payload,
    "Resource cases returned a malformed detail payload.",
  );
  const evidencePacks = response.linked_evidence_packs;

  if (evidencePacks === undefined || evidencePacks === null) {
    return;
  }
  if (!Array.isArray(evidencePacks)) {
    throw new OperatorDataProviderContractError(
      "Resource cases linked_evidence_packs must be an array.",
    );
  }

  evidencePacks.forEach((packValue) => {
    const pack = asObject(
      packValue,
      "Resource cases linked_evidence_packs item must be an object.",
    );
    const evidenceRequestId = asString(pack.evidence_request_id);
    const caseId = asString(pack.case_id);
    const sourceId = asString(pack.source_id);
    const consumer = asString(pack.consumer);
    const status = asString(pack.status);
    const freshnessState = asString(pack.freshness_state);
    const custodyState = asString(pack.custody_state);
    const confidenceState = asString(pack.confidence_state);
    const provenanceState = asString(pack.provenance_state);
    const conflictState = asString(pack.conflict_state);
    const sourceState = asString(pack.source_state);
    const uncertaintyLabel = asString(pack.uncertainty_label);
    const authorityPosture = asString(pack.authority_posture);
    const workflowAuthority = asString(pack.workflow_authority);
    const projectionSource = asString(pack.projection_source);
    const custody = asObject(
      pack.custody,
      "Resource cases linked_evidence_packs item custody must be an object.",
    );
    const provenance = asObject(
      pack.provenance,
      "Resource cases linked_evidence_packs item provenance must be an object.",
    );
    const confidence = asObject(
      pack.confidence,
      "Resource cases linked_evidence_packs item confidence must be an object.",
    );

    if (
      evidenceRequestId === null ||
      caseId === null ||
      sourceId === null ||
      consumer === null ||
      status === null ||
      freshnessState === null ||
      custodyState === null ||
      confidenceState === null ||
      provenanceState === null ||
      conflictState === null ||
      sourceState === null ||
      uncertaintyLabel === null ||
      authorityPosture === null
    ) {
      throw new OperatorDataProviderContractError(
        "Resource cases linked_evidence_packs item is missing required evidence-pack labels.",
      );
    }
    if (caseId !== requestedCaseId) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} must stay bound to case ${requestedCaseId}.`,
      );
    }
    if (sourceId !== EVIDENCE_PACK_SUPPORTED_SOURCE_ID) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} has an unsupported evidence-pack source.`,
      );
    }
    validateEvidencePackLabel("consumer", consumer, evidenceRequestId);
    validateEvidencePackLabel("status", status, evidenceRequestId);
    validateEvidencePackLabel(
      "freshness_state",
      freshnessState,
      evidenceRequestId,
    );
    validateEvidencePackLabel("custody_state", custodyState, evidenceRequestId);
    validateEvidencePackLabel(
      "confidence_state",
      confidenceState,
      evidenceRequestId,
    );
    validateEvidencePackLabel(
      "provenance_state",
      provenanceState,
      evidenceRequestId,
    );
    validateEvidencePackLabel("conflict_state", conflictState, evidenceRequestId);
    validateEvidencePackLabel("source_state", sourceState, evidenceRequestId);
    validateEvidencePackLabel(
      "uncertainty_label",
      uncertaintyLabel,
      evidenceRequestId,
    );
    validateEvidencePackReasons(
      pack.degraded_reasons,
      EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS,
    );
    validateEvidencePackReasons(
      pack.unavailable_reasons,
      EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS,
    );
    validateEvidencePackMetadataMap(
      custody,
      EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS,
      evidenceRequestId,
    );
    validateEvidencePackMetadataMap(
      provenance,
      EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS,
      evidenceRequestId,
    );
    validateEvidencePackMetadataMap(
      confidence,
      EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS,
      evidenceRequestId,
    );
    validateEvidencePackMetadataFormats(custody, provenance, evidenceRequestId);
    validateEvidencePackFreshnessWindow(
      custody,
      freshnessState,
      evidenceRequestId,
    );
    const evidenceRecordId = asString(custody.aegisops_evidence_record_id);
    if (
      evidenceRecordId === null ||
      asString(provenance.request_binding) !== evidenceRequestId ||
      asString(provenance.case_binding) !== requestedCaseId ||
      asString(provenance.source_id) !== sourceId ||
      asString(provenance.target_binding) !== asString(custody.reviewed_file_hash) ||
      asString(provenance.enrichment_request_id) !==
        asString(custody.enrichment_request_id) ||
      asString(provenance.collection_timestamp) !==
        asString(custody.collection_timestamp) ||
      asString(provenance.response_digest) !== asString(custody.response_digest) ||
      asString(provenance.custody_reference) !==
        linkedEvidenceRecordCustodyReference(
          response,
          evidenceRecordId,
          evidenceRequestId,
        )
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} must keep provenance bound to the evidence request and case.`,
      );
    }
    if (
      asString(provenance.authority_posture) !==
      EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} must keep provenance subordinate.`,
      );
    }
    if (asString(confidence.source_native_score_authority) !== "none") {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} cannot carry workflow authority.`,
      );
    }
    if (asString(confidence.posture) !== EVIDENCE_PACK_CONFIDENCE_POSTURE) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} has an unsupported confidence posture.`,
      );
    }
    validateEvidencePackReasonConsistency(pack, confidence, {
      status,
      freshnessState,
      conflictState,
      sourceState,
      uncertaintyLabel,
    });
    if (
      pack.authoritative_workflow_truth !== false ||
      authorityPosture !== EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE ||
      workflowAuthority !== "none"
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} cannot carry workflow authority.`,
      );
    }
    if (pack.operator_visible !== undefined && pack.operator_visible !== true) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} must stay operator visible.`,
      );
    }
    if (
      (pack.cache_sourced !== undefined && pack.cache_sourced !== false) ||
      (pack.stale_cache !== undefined && pack.stale_cache !== false) ||
      EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES.has(projectionSource ?? "")
    ) {
      throw new OperatorDataProviderContractError(
        "Resource cases rejects cache or browser sourced evidence-pack truth.",
      );
    }
    if (
      pack.release_readiness_claim !== undefined ||
      pack.rc_readiness_claim !== undefined ||
      pack.gate_readiness_claim !== undefined
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} cannot claim release readiness.`,
      );
    }
    if (
      Object.keys(pack).some(
        (fieldName) => !EVIDENCE_PACK_RECOGNIZED_FIELDS.has(fieldName),
      )
    ) {
      throw new OperatorDataProviderContractError(
        `Resource cases linked_evidence_packs item ${evidenceRequestId} has unexpected evidence-pack fields.`,
      );
    }
  });
}

