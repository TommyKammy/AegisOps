import { OperatorDataProviderContractError } from "./errors";
import { asString } from "./shared";

const DETECTOR_LIFECYCLE_STATES = new Set([
  "candidate",
  "staging",
  "active",
  "disabled",
  "rollback",
  "review-overdue",
]);

const DETECTOR_ACTIVATION_REVIEW_REQUIRED_FIELDS = [
  "detector_lifecycle_id",
  "owner",
  "source_family",
  "source_catalog_entry",
  "detector_identifier",
  "expected_signal_posture",
  "review_cadence",
  "rollback_owner",
  "disable_owner",
] as const;

const SOURCE_HEALTH_STATES = new Set([
  "available",
  "degraded",
  "unavailable",
  "stale_source",
  "missing_agent",
  "parser_failure",
  "volume_anomaly",
  "credential_degraded",
  "detector_drift",
  "mismatched",
]);

const SOURCE_HEALTH_REQUIRED_FIELDS = [
  "source_health_id",
  "source_family",
  "source_catalog_entry",
  "health_state",
  "reviewed_state",
  "lifecycle_state",
  "reviewed_at",
  "observed_at",
  "detector_drift",
  "credential_posture",
  "operator_visible_reason",
] as const;

const SOURCE_HEALTH_REVIEWED_STATES = new Set([
  "reviewed",
  "superseded",
  "withdrawn",
]);

const RECORD_SEARCH_FAMILIES = new Set([
  "alert",
  "case",
  "evidence",
  "detector_lifecycle",
  "false_positive_review",
  "suppression_proposal",
  "source_health",
]);

const RECORD_SEARCH_REVIEWED_ROUTE_PATTERNS_BY_FAMILY = new Map<string, RegExp[]>([
  ["alert", [/^\/operator\/alerts\/[^/?#]+$/]],
  ["case", [/^\/operator\/cases\/[^/?#]+$/]],
  ["evidence", [/^\/operator\/alerts\/[^/?#]+$/, /^\/operator\/cases\/[^/?#]+$/]],
  ["detector_lifecycle", [/^\/operator\/detectors$/]],
  [
    "false_positive_review",
    [
      /^\/operator\/alerts\/[^/?#]+$/,
      /^\/operator\/cases\/[^/?#]+$/,
      /^\/operator\/detectors$/,
    ],
  ],
  [
    "suppression_proposal",
    [
      /^\/operator\/alerts\/[^/?#]+$/,
      /^\/operator\/cases\/[^/?#]+$/,
      /^\/operator\/detectors$/,
    ],
  ],
  ["source_health", [/^\/operator\/source-health$/]],
]);

const REVIEWED_SOURCE_CATALOG_ENTRIES_BY_FAMILY = new Map<string, Set<string>>([
  [
    "wazuh_detection",
    new Set(["docs/phase-61-minimum-source-catalog-contract.md"]),
  ],
  [
    "github_audit",
    new Set([
      "docs/source-families/github-audit/onboarding-package.md",
      "docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md",
    ]),
  ],
  [
    "microsoft_365_audit",
    new Set(["docs/source-families/microsoft-365-audit/onboarding-package.md"]),
  ],
  [
    "entra_id",
    new Set([
      "docs/source-families/entra-id/onboarding-package.md",
      "docs/source-families/entra-id/detector-activation-candidates/privileged-role-assignment.md",
    ]),
  ],
  [
    "windows_security_endpoint",
    new Set([
      "docs/source-families/windows-security-and-endpoint/onboarding-package.md",
    ]),
  ],
]);

export function validateDetectorActivationReviewRecord(
  record: Record<string, unknown>,
) {
  for (const field of DETECTOR_ACTIVATION_REVIEW_REQUIRED_FIELDS) {
    if (asString(record[field]) === null) {
      throw new OperatorDataProviderContractError(
        `Resource detectorActivationReview record is missing reviewed field ${field}.`,
      );
    }
  }

  const lifecycleState = asString(record.lifecycle_state);
  if (lifecycleState === null || !DETECTOR_LIFECYCLE_STATES.has(lifecycleState)) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview record has unsupported lifecycle_state.",
    );
  }

  if ("stale_display_state" in record && record.stale_display_state !== false) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview rejects stale display state.",
    );
  }

  if (!Array.isArray(record.lifecycle_audit_references)) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview requires lifecycle_audit_references.",
    );
  }
  if (
    record.lifecycle_audit_references.length === 0 ||
    record.lifecycle_audit_references.some((reference) => asString(reference) === null)
  ) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview requires non-empty reviewed audit references.",
    );
  }

  if (lifecycleState === "disabled" && asString(record.disabled_reason) === null) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview disabled records require disabled_reason.",
    );
  }
  if (lifecycleState === "rollback" && asString(record.rollback_reason) === null) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview rollback records require rollback_reason.",
    );
  }
  if (
    lifecycleState === "review-overdue" &&
    asString(record.review_overdue_reason) === null
  ) {
    throw new OperatorDataProviderContractError(
      "Resource detectorActivationReview review-overdue records require review_overdue_reason.",
    );
  }
}

export function validateSourceHealthDashboardRecord(record: Record<string, unknown>) {
  for (const field of SOURCE_HEALTH_REQUIRED_FIELDS) {
    if (asString(record[field]) === null) {
      throw new OperatorDataProviderContractError(
        `Resource sourceHealthDashboard record is missing reviewed field ${field}.`,
      );
    }
  }

  const healthState = asString(record.health_state);
  if (healthState === null || !SOURCE_HEALTH_STATES.has(healthState)) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard record has unsupported health_state.",
    );
  }

  const reviewedState = asString(record.reviewed_state);
  if (
    reviewedState === null ||
    !SOURCE_HEALTH_REVIEWED_STATES.has(reviewedState)
  ) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard record has unsupported reviewed_state.",
    );
  }
  if (asString(record.lifecycle_state) !== reviewedState) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard requires lifecycle_state to match reviewed_state.",
    );
  }

  const sourceFamily = asString(record.source_family);
  const sourceCatalogEntry = asString(record.source_catalog_entry);
  const reviewedCatalogEntries =
    sourceFamily === null
      ? undefined
      : REVIEWED_SOURCE_CATALOG_ENTRIES_BY_FAMILY.get(sourceFamily);
  if (
    sourceFamily === null ||
    sourceCatalogEntry === null ||
    reviewedCatalogEntries === undefined ||
    !reviewedCatalogEntries.has(sourceCatalogEntry)
  ) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard requires a reviewed source catalog entry.",
    );
  }

  if (record.cache_sourced !== false) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard rejects cache-sourced source health.",
    );
  }
  if (
    record.source_native_authority !== false ||
    record.display_state_authority !== false
  ) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard rejects source-health display state as workflow truth.",
    );
  }
  if (!Array.isArray(record.evidence_references)) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard requires evidence_references.",
    );
  }
  if (
    record.evidence_references.length === 0 ||
    record.evidence_references.some((reference) => asString(reference) === null)
  ) {
    throw new OperatorDataProviderContractError(
      "Resource sourceHealthDashboard requires non-empty reviewed evidence references.",
    );
  }
}

export function validateRecordSearchResult(record: Record<string, unknown>) {
  const recordFamily = asString(record.record_family);
  if (recordFamily === null || !RECORD_SEARCH_FAMILIES.has(recordFamily)) {
    throw new OperatorDataProviderContractError(
      "Resource recordSearch result has unsupported record_family.",
    );
  }
  if (asString(record.record_id) === null) {
    throw new OperatorDataProviderContractError(
      "Resource recordSearch result is missing reviewed record_id.",
    );
  }
  const route = asString(record.route);
  if (
    route === null ||
    asString(record.route_kind) !== "reviewed_surface" ||
    !isReviewedRecordSearchRoute(recordFamily, route)
  ) {
    throw new OperatorDataProviderContractError(
      "Resource recordSearch result must route to a reviewed surface.",
    );
  }
  if (record.authority !== "navigation_only" || record.raw_source_authority !== false) {
    throw new OperatorDataProviderContractError(
      "Resource recordSearch rejects search results as workflow truth.",
    );
  }
  if (record.stale_cache === true || record.cache_sourced === true) {
    throw new OperatorDataProviderContractError(
      "Resource recordSearch rejects stale-cache results.",
    );
  }
}

function isReviewedRecordSearchRoute(recordFamily: string, route: string): boolean {
  const allowedPatterns =
    RECORD_SEARCH_REVIEWED_ROUTE_PATTERNS_BY_FAMILY.get(recordFamily);
  return allowedPatterns?.some((pattern) => pattern.test(route)) ?? false;
}
