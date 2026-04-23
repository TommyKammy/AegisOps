import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import ReportProblemOutlinedIcon from "@mui/icons-material/ReportProblemOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Link,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { type ReactNode, useMemo, useState } from "react";
import { Link as ReactRouterLink, useParams } from "react-router-dom";
import { useDataProvider } from "react-admin";
import {
  CreateReviewedActionRequestCard,
  PromoteAlertToCaseCard,
  RecordActionApprovalDecisionCard,
  RecordActionReviewEscalationNoteCard,
  RecordActionReviewManualFallbackCard,
  RecordCaseLeadCard,
  RecordCaseObservationCard,
  RecordCaseRecommendationCard,
} from "../taskActions/caseworkActionCards";
import {
  OptionalExtensionVisibilityPanel,
  buildOptionalEvidenceDefinitionsFromPayload,
} from "./optionalExtensionVisibility";
import { useOperatorUiEventLog } from "./operatorUiEvents";
import {
  buildOperatorQueryKey,
  useOperatorQueryLoader,
  useOperatorQueryState,
} from "./operatorQueryCache";

type UnknownRecord = Record<string, unknown>;

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refreshing: boolean;
}

function asRecord(value: unknown): UnknownRecord | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as UnknownRecord;
}

function asRecordArray(value: unknown): UnknownRecord[] {
  return Array.isArray(value)
    ? value.map((entry) => asRecord(entry)).filter((entry): entry is UnknownRecord => entry !== null)
    : [];
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function isAllowedExternalHref(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value
        .map((entry) => asString(entry))
        .filter((entry): entry is string => entry !== null)
    : [];
}

function getPath(record: UnknownRecord | null, path: string): unknown {
  if (record === null) {
    return undefined;
  }

  return path.split(".").reduce<unknown>((value, segment) => {
    const next = asRecord(value);
    return next?.[segment];
  }, record);
}

function formatLabel(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

const ADVISORY_SUMMARY_FIELDS = ["summary", "message", "output_text", "advisory_text"] as const;
const ADVISORY_DETAIL_EXCLUDED_FIELDS = [
  "id",
  "record_family",
  "record_id",
  "output_kind",
  "status",
  "read_only",
  "cited_summary",
  "candidate_recommendations",
  "uncertainty_flags",
  "citations",
  ...ADVISORY_SUMMARY_FIELDS,
] as const;

const SUPPORTED_ADVISORY_RECORD_FAMILIES = new Set([
  "alert",
  "case",
  "recommendation",
  "approval_decision",
  "reconciliation",
]);

function formatValue(value: unknown): string {
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

function advisorySummary(record: UnknownRecord) {
  const citedSummary = asRecord(record.cited_summary);
  const citedText = asString(citedSummary?.text);
  const citedCitations = asStringArray(citedSummary?.citations);
  const fallbackText =
    ADVISORY_SUMMARY_FIELDS.map((key) => asString(record[key])).find(
      (value): value is string => value !== null,
    ) ?? null;

  return {
    citations: citedText ? citedCitations : [],
    text: citedText ?? fallbackText,
  };
}

function advisoryRecommendations(record: UnknownRecord) {
  return asRecordArray(record.candidate_recommendations).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

function advisoryContextEntries(record: UnknownRecord, field: "key_observations" | "unresolved_questions") {
  return asRecordArray(record[field]).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

function advisoryUncertaintyMessage(flag: string): string {
  switch (flag) {
    case "missing_supporting_citations":
      return "Required reviewed citations are missing, so this advisory output remains fail-closed.";
    case "missing_evidence_citation":
      return "Linked evidence citations required for this advisory output are missing.";
    case "conflicting_reviewed_context":
      return "Reviewed context conflicts remain unresolved and must stay visible before any operator action.";
    case "ambiguous_identity_alias_only":
      return "Alias-style identity context is still unresolved; stable reviewed identifiers are still required.";
    case "reviewed_casework_identity_ambiguity":
      return "Reviewed casework identity ambiguity remains open across linked records and evidence.";
    case "scope_authority_pressure":
      return "Assistant output tried to imply scope or authority beyond the reviewed record boundary.";
    case "approval_authority_pressure":
      return "Assistant output must not imply approval authority.";
    case "execution_authority_pressure":
      return "Assistant output must not imply execution authority.";
    case "reconciliation_authority_pressure":
      return "Assistant output must not imply reconciliation authority.";
    case "advisory_only":
      return "Assistant output remains advisory-only and subordinate to the authoritative record.";
    default:
      return `${formatLabel(flag)} remains visible on this advisory output.`;
  }
}

function advisoryUncertaintyLabel(flag: string): string {
  switch (flag) {
    case "missing_supporting_citations":
      return "Missing citation support";
    case "missing_evidence_citation":
      return "Missing evidence citation";
    case "conflicting_reviewed_context":
      return "Conflicting reviewed context";
    case "ambiguous_identity_alias_only":
      return "Alias-only identity ambiguity";
    case "reviewed_casework_identity_ambiguity":
      return "Reviewed casework identity ambiguity";
    case "scope_authority_pressure":
      return "Scope authority pressure";
    case "approval_authority_pressure":
      return "Approval authority pressure";
    case "execution_authority_pressure":
      return "Execution authority pressure";
    case "reconciliation_authority_pressure":
      return "Reconciliation authority pressure";
    case "advisory_only":
      return "Advisory only";
    default:
      return formatLabel(flag);
  }
}

function statusTone(
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

function canRecordActionApprovalDecision(operatorRoles: readonly string[]) {
  return operatorRoles.some((role) => role.toLowerCase() === "approver");
}

function approvalLifecycleExplanation(approvalState: string | null) {
  switch ((approvalState ?? "").toLowerCase()) {
    case "approved":
      return "Approved remains a lifecycle-bearing reviewed decision. Execution may still be pending, blocked, or later found mismatched by reconciliation.";
    case "rejected":
      return "Rejected keeps the reviewed request blocked. The operator console must not imply execution authority returned through a local retry or toggle.";
    case "expired":
      return "Expired means the reviewed approval window no longer authorizes this request. Operators must reread authoritative state rather than infer continued validity.";
    case "superseded":
      return "Superseded means a newer authoritative request or decision replaced this record. This page stays anchored to the selected record without redefining it as current truth.";
    case "unresolved":
      return "Unresolved means authoritative completion is still missing or inconclusive. The UI must keep the decision path explicit instead of implying durable success.";
    case "pending":
      return "Pending means approval is still waiting on a reviewed decision or prerequisite. Approval remains a decision surface, not a reversible setting.";
    default:
      return "Approval lifecycle stays explicit here so operators can distinguish pending, approved, rejected, expired, superseded, and unresolved states without collapsing them into generic status text.";
  }
}

function approvalLifecycleSeverity(
  approvalState: string | null,
): "error" | "info" | "success" | "warning" {
  const tone = statusTone(approvalState);
  return tone === "default" ? "info" : tone;
}

function findTimelineStage(
  actionReview: UnknownRecord | null,
  stage: string,
): UnknownRecord | null {
  const normalizedStage = stage.toLowerCase();
  return (
    asRecordArray(actionReview?.timeline).find((entry) => {
      const candidate = (asString(entry.stage) ?? asString(entry.label))?.toLowerCase();
      return candidate === normalizedStage;
    }) ?? null
  );
}

function dispatchLifecycleState(actionReview: UnknownRecord | null): string | null {
  const timelineStageState =
    asString(findTimelineStage(actionReview, "delegation")?.state) ??
    asString(findTimelineStage(actionReview, "delegated")?.state);
  if (timelineStageState !== null) {
    return timelineStageState;
  }
  if (asString(actionReview?.delegation_id) !== null) {
    return "delegated";
  }
  if (asString(actionReview?.approval_state) === "approved") {
    return "pending_delegation";
  }
  return null;
}

function ExecutionReceiptSection({ actionReview }: { actionReview: UnknownRecord | null }) {
  const coordinationOutcome = asRecord(actionReview?.coordination_ticket_outcome);
  const executionState = asString(actionReview?.action_execution_state);
  const reconciliationState = asString(actionReview?.reconciliation_state);
  const dispatchState = dispatchLifecycleState(actionReview);
  const actionExecutionId = asString(actionReview?.action_execution_id);

  return (
    <SectionCard
      subtitle="Dispatch, execution receipt, and reconciliation are rendered as separate lifecycle surfaces so downstream completion is not overstated."
      title="Execution receipt"
    >
      <Stack spacing={2}>
        <StatusStrip
          values={[
            ["Dispatch", dispatchState],
            ["Execution", executionState],
            ["Reconciliation", reconciliationState],
            ["Coordination", asString(coordinationOutcome?.status)],
          ]}
        />
        {!actionExecutionId ? (
          <Alert severity="warning" variant="outlined">
            No authoritative execution receipt is attached to this reviewed request yet.
          </Alert>
        ) : null}
        {actionExecutionId && reconciliationState !== "matched" ? (
          <Alert severity="warning" variant="outlined">
            Execution receipt visibility is present, but downstream reconciliation is still
            {reconciliationState ? ` ${reconciliationState}` : " unresolved"}.
          </Alert>
        ) : null}
        <ValueList
          entries={[
            ["Action execution id", actionExecutionId],
            ["Delegation id", asString(actionReview?.delegation_id)],
            ["Execution run id", asString(actionReview?.execution_run_id)],
            ["Execution surface type", asString(actionReview?.execution_surface_type)],
            ["Execution surface id", asString(actionReview?.execution_surface_id)],
            ["External receipt id", asString(coordinationOutcome?.external_receipt_id)],
            ["Next expected action", asString(actionReview?.next_expected_action)],
          ]}
        />
      </Stack>
    </SectionCard>
  );
}

function ReconciliationVisibilitySection({
  actionReview,
}: {
  actionReview: UnknownRecord | null;
}) {
  const mismatchInspection = asRecord(actionReview?.mismatch_inspection);
  const reconciliationState = asString(actionReview?.reconciliation_state);
  const mismatchSummary = asString(mismatchInspection?.mismatch_summary);

  return (
    <SectionCard
      subtitle="Mismatch, missing receipt, and unresolved downstream outcomes stay explicit instead of being normalized into generic success."
      title="Reconciliation visibility"
    >
      <Stack spacing={2}>
        <StatusStrip
          values={[
            ["Reconciliation", reconciliationState],
            ["Ingest", asString(mismatchInspection?.ingest_disposition)],
          ]}
        />
        {mismatchInspection ? (
          <Alert severity="warning" variant="outlined">
            {mismatchSummary ??
              "Authoritative reconciliation still reports a mismatch or unresolved downstream state."}
          </Alert>
        ) : null}
        {!mismatchInspection && !asString(actionReview?.reconciliation_id) ? (
          <Alert severity="warning" variant="outlined">
            No authoritative reconciliation record is visible for this reviewed request yet.
          </Alert>
        ) : null}
        <ValueList
          entries={[
            ["Reconciliation id", asString(actionReview?.reconciliation_id)],
            ["Mismatch summary", mismatchSummary],
            ["Correlation key", asString(mismatchInspection?.correlation_key)],
            ["Observed execution run", asString(mismatchInspection?.execution_run_id)],
            ["Linked execution runs", mismatchInspection?.linked_execution_run_ids],
            ["Compared at", asString(mismatchInspection?.compared_at)],
            ["Last seen at", asString(mismatchInspection?.last_seen_at)],
          ]}
        />
      </Stack>
    </SectionCard>
  );
}

function CoordinationVisibilitySection({
  actionReview,
}: {
  actionReview: UnknownRecord | null;
}) {
  const { recordBoundedExternalOpen } = useOperatorUiEventLog();
  const coordinationOutcome = asRecord(actionReview?.coordination_ticket_outcome);
  const targetScope = asRecord(actionReview?.target_scope);
  const ticketReferenceUrl = asString(coordinationOutcome?.ticket_reference_url);
  const requestedCoordinationReferenceId = asString(targetScope?.coordination_reference_id);
  const observedCoordinationReferenceId = asString(coordinationOutcome?.coordination_reference_id);
  const requestedCoordinationTargetType = asString(targetScope?.coordination_target_type);
  const observedCoordinationTargetType = asString(coordinationOutcome?.coordination_target_type);
  const requestedCoordinationTargetId = asString(targetScope?.coordination_target_id);
  const observedCoordinationTargetId = asString(coordinationOutcome?.coordination_target_id);
  const coordinationReferenceMismatch =
    requestedCoordinationReferenceId !== null &&
    observedCoordinationReferenceId !== null &&
    requestedCoordinationReferenceId !== observedCoordinationReferenceId;
  const coordinationTargetTypeMismatch =
    requestedCoordinationTargetType !== null &&
    observedCoordinationTargetType !== null &&
    requestedCoordinationTargetType !== observedCoordinationTargetType;
  const coordinationTargetIdMismatch =
    requestedCoordinationTargetId !== null &&
    observedCoordinationTargetId !== null &&
    requestedCoordinationTargetId !== observedCoordinationTargetId;

  if (coordinationOutcome === null && targetScope === null) {
    return null;
  }

  return (
    <SectionCard
      subtitle="Downstream coordination references stay visible as subordinate context without replacing AegisOps-owned request, approval, execution, or reconciliation truth."
      title="Coordination visibility"
    >
      <Stack spacing={2}>
        <StatusStrip
          values={[
            ["Coordination", asString(coordinationOutcome?.status)],
            ["Authority", asString(coordinationOutcome?.authority)],
          ]}
        />
        {asString(coordinationOutcome?.summary) ? (
          <Alert severity="info" variant="outlined">
            {asString(coordinationOutcome?.summary)}
          </Alert>
        ) : null}
        {coordinationReferenceMismatch ||
        coordinationTargetTypeMismatch ||
        coordinationTargetIdMismatch ? (
          <Alert severity="warning" variant="outlined">
            Requested and observed coordination references do not match.
          </Alert>
        ) : null}
        <ValueList
          entries={[
            [
              "Requested coordination reference id",
              requestedCoordinationReferenceId,
            ],
            [
              "Observed coordination reference id",
              observedCoordinationReferenceId,
            ],
            [
              "Requested coordination target type",
              requestedCoordinationTargetType,
            ],
            [
              "Observed coordination target type",
              observedCoordinationTargetType,
            ],
            [
              "Requested coordination target id",
              requestedCoordinationTargetId,
            ],
            [
              "Observed coordination target id",
              observedCoordinationTargetId,
            ],
            ["External receipt id", asString(coordinationOutcome?.external_receipt_id)],
            ["Linked action execution", asString(coordinationOutcome?.action_execution_id)],
            ["Linked reconciliation", asString(coordinationOutcome?.reconciliation_id)],
          ]}
        />
        {ticketReferenceUrl && isAllowedExternalHref(ticketReferenceUrl) ? (
          <Link
            href={ticketReferenceUrl}
            onClick={() => {
              recordBoundedExternalOpen(
                "Open downstream coordination reference",
                ticketReferenceUrl,
              );
            }}
            rel="noreferrer"
            target="_blank"
            underline="hover"
          >
            Open downstream coordination reference
          </Link>
        ) : ticketReferenceUrl ? (
          <Typography color="text.secondary" variant="body2">
            Downstream coordination reference: {ticketReferenceUrl}
          </Typography>
        ) : null}
      </Stack>
    </SectionCard>
  );
}

function useOperatorList(
  resource: string,
  filter: Record<string, unknown>,
  sort: { field: string; order: "ASC" | "DESC" },
  perPage = 25,
): QueryState<UnknownRecord[]> {
  const dataProvider = useDataProvider();
  const key = useMemo(
    () => buildOperatorQueryKey(["list", resource, filter, perPage, sort]),
    [filter, perPage, resource, sort],
  );
  const queryFn = useMemo(
    () => async () => {
      const result = await dataProvider.getList(resource, {
        filter,
        pagination: {
          page: 1,
          perPage,
        },
        sort,
      });

      return result.data.map((record) => record as UnknownRecord);
    },
    [dataProvider, filter, perPage, resource, sort],
  );
  const state = useOperatorQueryState<UnknownRecord[]>(key);

  useOperatorQueryLoader({
    key,
    policy: {
      refetchOnMount: true,
      retainStaleOnError: true,
    },
    queryFn,
  });

  return state;
}

function useOperatorRecord(
  resource: string,
  id: string,
  meta?: Record<string, unknown>,
): QueryState<UnknownRecord> {
  const dataProvider = useDataProvider();
  const metaRecord =
    meta && typeof meta === "object" ? meta : {};
  const { reloadToken, ...cacheableMeta } = metaRecord;
  const refreshToken =
    typeof reloadToken === "number" && reloadToken > 0 ? reloadToken : undefined;
  const requestMetaKey = useMemo(
    () => buildOperatorQueryKey(["request-meta", metaRecord]),
    [metaRecord],
  );
  const requestMeta = useMemo(
    () => (Object.keys(metaRecord).length > 0 ? metaRecord : undefined),
    [requestMetaKey],
  );
  const key = useMemo(
    () => buildOperatorQueryKey(["record", resource, id, cacheableMeta]),
    [cacheableMeta, id, resource],
  );
  const queryFn = useMemo(
    () => async () => {
      const result = await dataProvider.getOne(resource, {
        id,
        meta: requestMeta,
      });

      return result.data as UnknownRecord;
    },
    [dataProvider, id, requestMeta, requestMetaKey, resource],
  );
  const state = useOperatorQueryState<UnknownRecord>(key);

  useOperatorQueryLoader({
    force: refreshToken !== undefined,
    key,
    policy: {
      refetchOnMount: true,
      retainStaleOnError: true,
    },
    queryFn,
    refreshToken,
  });

  return state;
}

function PageFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <Stack spacing={3} sx={{ p: { xs: 2, md: 3 } }}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h4">
          {title}
        </Typography>
        <Typography color="text.secondary" maxWidth={860} variant="body1">
          {subtitle}
        </Typography>
      </Stack>
      {children}
    </Stack>
  );
}

function LoadingState({ label }: { label: string }) {
  return (
    <Box sx={{ display: "grid", minHeight: 280, placeItems: "center" }}>
      <Stack alignItems="center" spacing={2}>
        <CircularProgress aria-label={label} />
        <Typography color="text.secondary" variant="body2">
          Loading reviewed operator data.
        </Typography>
      </Stack>
    </Box>
  );
}

function ErrorState({ error }: { error: Error }) {
  if (error.name === "OperatorDataProviderAuthorizationError") {
    return (
      <Alert severity="warning" variant="outlined">
        Reviewed backend authorization is required before this operator surface can render.
      </Alert>
    );
  }

  if (error.name === "OperatorDataProviderContractError") {
    return (
      <Alert severity="error" variant="outlined">
        Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.
      </Alert>
    );
  }

  return (
    <Alert severity="error" variant="outlined">
      {error.message}
    </Alert>
  );
}

function QueryStateNotice({
  error,
  refreshing,
}: {
  error: Error | null;
  refreshing: boolean;
}) {
  if (error) {
    return (
      <Alert severity="warning" variant="outlined">
        Showing the last verified operator data while refresh is unavailable.
        <br />
        {error.message}
      </Alert>
    );
  }

  if (refreshing) {
    return (
      <Alert severity="info" variant="outlined">
        Refreshing reviewed operator data while the last verified state remains visible.
      </Alert>
    );
  }

  return null;
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography variant="h6">{title}</Typography>
            {subtitle ? (
              <Typography color="text.secondary" variant="body2">
                {subtitle}
              </Typography>
            ) : null}
          </Stack>
          <Divider />
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function ValueList({
  entries,
}: {
  entries: Array<[string, unknown]>;
}) {
  return (
    <Stack divider={<Divider flexItem />} spacing={0}>
      {entries.map(([label, value]) => (
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          key={label}
          spacing={1}
          sx={{ py: 1 }}
        >
          <Typography color="text.secondary" variant="body2">
            {label}
          </Typography>
          <Typography sx={{ textAlign: { sm: "right" } }} variant="body2">
            {formatValue(value)}
          </Typography>
        </Stack>
      ))}
    </Stack>
  );
}

function StatusStrip({
  values,
}: {
  values: Array<[string, string | null]>;
}) {
  return (
    <Stack direction="row" flexWrap="wrap" gap={1}>
      {values
        .filter(([, value]) => value !== null)
        .map(([label, value]) => (
          <Chip
            color={statusTone(value)}
            key={`${label}-${value}`}
            label={`${label}: ${value}`}
            size="small"
            variant={statusTone(value) === "default" ? "outlined" : "filled"}
          />
        ))}
    </Stack>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <Alert severity="info" variant="outlined">
      {message}
    </Alert>
  );
}

function AdvisoryContextList({
  entries,
  emptyMessage,
}: {
  entries: Array<{ citations: string[]; text: string | null }>;
  emptyMessage: string;
}) {
  const populatedEntries = entries.filter(
    (entry): entry is { citations: string[]; text: string } => entry.text !== null,
  );

  if (populatedEntries.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <Stack spacing={2}>
      {populatedEntries.map((entry, index) => (
        <Card elevation={0} key={`${entry.text}-${index}`} sx={{ border: "1px solid", borderColor: "divider" }}>
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="body1">{entry.text}</Typography>
              {entry.citations.length > 0 ? (
                <Stack direction="row" flexWrap="wrap" gap={1}>
                  {entry.citations.map((citation) => (
                    <Chip key={`${entry.text}-${citation}`} label={citation} size="small" variant="outlined" />
                  ))}
                </Stack>
              ) : (
                <EmptyState message="No reviewed citations were attached to this context entry." />
              )}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

function supportedAnchorRoute(
  recordFamily: string | null,
  recordId: string | null,
): { label: string; to: string } | null {
  if (recordFamily === null || recordId === null) {
    return null;
  }

  if (recordFamily === "alert") {
    return {
      label: "Open alert detail",
      to: `/operator/alerts/${recordId}`,
    };
  }

  if (recordFamily === "case") {
    return {
      label: "Open case detail",
      to: `/operator/cases/${recordId}`,
    };
  }

  return null;
}

function RecordWarnings({ record }: { record: UnknownRecord }) {
  const warnings: string[] = [];
  const reviewState = asString(record.review_state);
  const externalTicketStatus = asString(getPath(record, "external_ticket_reference.status"));

  if (reviewState !== null && ["degraded", "rejected", "missing_anchor", "mismatch"].includes(reviewState)) {
    warnings.push(`Review state remains ${reviewState}.`);
  }
  if (externalTicketStatus !== null && externalTicketStatus !== "present") {
    warnings.push(`Non-authoritative coordination reference is ${externalTicketStatus}.`);
  }
  if (asString(record.case_id) === null && asString(record.case_lifecycle_state) !== null) {
    warnings.push("Case lifecycle state is present without an authoritative case identifier.");
  }

  if (warnings.length === 0) {
    return null;
  }

  return (
    <Stack spacing={1}>
      {warnings.map((warning) => (
        <Alert icon={<ReportProblemOutlinedIcon fontSize="inherit" />} key={warning} severity="warning" variant="outlined">
          {warning}
        </Alert>
      ))}
    </Stack>
  );
}

function extractSubordinateLinks(record: UnknownRecord): Array<{ href: string; label: string }> {
  const entries: Array<{ href: string; label: string }> = [];

  for (const [key, value] of Object.entries(record)) {
    const href = asString(value);
    if (href && isAllowedExternalHref(href)) {
      entries.push({
        href,
        label: formatLabel(key),
      });
    }
  }

  return entries;
}

function SubordinateLinks({ records }: { records: UnknownRecord[] }) {
  const links = records.flatMap((record) => extractSubordinateLinks(record));
  const { recordBoundedExternalOpen } = useOperatorUiEventLog();

  if (links.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2">
        No substrate deep link was exposed by the reviewed backend payload.
      </Typography>
    );
  }

  return (
    <Stack direction="row" flexWrap="wrap" gap={1}>
      {links.map((link) => (
        <Button
          component={Link}
          endIcon={<OpenInNewOutlinedIcon />}
          href={link.href}
          key={`${link.label}-${link.href}`}
          onClick={() => {
            recordBoundedExternalOpen(link.label, link.href);
          }}
          rel="noreferrer"
          size="small"
          target="_blank"
          variant="outlined"
        >
          {link.label}
        </Button>
      ))}
    </Stack>
  );
}

function AuditedRouteLink({
  children,
  label,
  to,
}: {
  children: ReactNode;
  label: string;
  to: string;
}) {
  const { recordNavigation } = useOperatorUiEventLog();

  return (
    <Link
      component={ReactRouterLink}
      onClick={() => {
        recordNavigation(label, to);
      }}
      to={to}
      underline="hover"
    >
      {children}
    </Link>
  );
}

function AuditedRouteButton({
  children,
  label,
  to,
}: {
  children: ReactNode;
  label: string;
  to: string;
}) {
  const { recordNavigation } = useOperatorUiEventLog();

  return (
    <Button
      component={ReactRouterLink}
      endIcon={<LaunchOutlinedIcon />}
      onClick={() => {
        recordNavigation(label, to);
      }}
      to={to}
      variant="outlined"
    >
      {children}
    </Button>
  );
}

export function QueuePage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "last_seen_at",
      order: "DESC" as const,
    }),
    [],
  );
  const { data, error, loading, refreshing } = useOperatorList("queue", filter, sort);

  return (
    <PageFrame
      subtitle="Primary review surface; substrate links stay secondary. AegisOps queue records remain the authoritative selection surface for operator review."
      title="Analyst Queue"
    >
      {loading && !data ? <LoadingState label="Loading analyst queue" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data ? <QueryStateNotice error={error} refreshing={refreshing} /> : null}
      {data ? (
        data.length > 0 ? (
          <SectionCard
            subtitle="Explicit degraded, pending, and mismatch states remain visible instead of being smoothed away."
            title="Queue records"
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Alert</TableCell>
                  <TableCell>Review state</TableCell>
                  <TableCell>Case</TableCell>
                  <TableCell>Source family</TableCell>
                  <TableCell>Action review</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((record) => {
                  const alertId = asString(record.alert_id) ?? "Unknown alert";
                  const caseId = asString(record.case_id);
                  const sourceFamily = asString(
                    getPath(record, "reviewed_context.source.source_family"),
                  );
                  const actionReviewState = asString(
                    getPath(record, "current_action_review.review_state"),
                  );
                  return (
                    <TableRow hover key={String(record.id ?? alertId)}>
                      <TableCell>
                        <Stack spacing={0.75}>
                          <AuditedRouteLink
                            label="Open alert detail"
                            to={`/operator/alerts/${alertId}`}
                          >
                            {alertId}
                          </AuditedRouteLink>
                          <Typography color="text.secondary" variant="caption">
                            {formatValue(record.queue_selection)}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <StatusStrip values={[["Review", asString(record.review_state)]]} />
                      </TableCell>
                      <TableCell>
                        {caseId ? (
                          <AuditedRouteLink
                            label="Open case detail"
                            to={`/operator/cases/${caseId}`}
                          >
                            {caseId}
                          </AuditedRouteLink>
                        ) : (
                          <Typography color="text.secondary" variant="body2">
                            No case anchor
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{sourceFamily ?? "Not available"}</TableCell>
                      <TableCell>{actionReviewState ?? "No active review"}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </SectionCard>
        ) : (
          <EmptyState message="The reviewed analyst queue is empty." />
        )
      ) : null}

      {data?.map((record) => (
        <SectionCard
          key={`queue-summary-${String(record.id ?? record.alert_id)}`}
          subtitle="AegisOps-owned queue state stays primary. Subordinate source hints remain secondary below it."
          title={`Queue summary: ${formatValue(record.alert_id)}`}
        >
          <StatusStrip
            values={[
              ["Review", asString(record.review_state)],
              ["Case", asString(record.case_lifecycle_state)],
              ["Escalation", asString(record.escalation_boundary)],
              [
                "Action review",
                asString(getPath(record, "current_action_review.review_state")),
              ],
            ]}
          />
          <RecordWarnings record={record} />
          <ValueList
            entries={[
              ["Accountable identities", asStringArray(record.accountable_source_identities)],
              ["Subordinate detection ids", asStringArray(record.substrate_detection_record_ids)],
              ["Correlation key", record.correlation_key],
            ]}
          />
        </SectionCard>
      ))}
    </PageFrame>
  );
}

function AlertDetailPageBody({
  alertId,
  operatorIdentity,
}: {
  alertId: string;
  operatorIdentity: string;
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord("alerts", alertId, recordMeta);

  if (loading && !data) {
    return <LoadingState label="Loading alert detail" />;
  }

  if (error && !data) {
    return <ErrorState error={error} />;
  }

  if (!data) {
    return <EmptyState message="Alert detail is unavailable." />;
  }

  const alertRecord = asRecord(data.alert);
  const caseRecord = asRecord(data.case_record);
  const lineage = asRecord(data.lineage);
  const evidenceRecords = asRecordArray(data.linked_evidence_records);
  const reconciliationRecord = asRecord(data.latest_reconciliation);

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="Authoritative anchor records stay primary even when subordinate substrate context disagrees or is missing."
        title="Authoritative anchor"
      >
        <StatusStrip
          values={[
            ["Lifecycle", asString(alertRecord?.lifecycle_state)],
            ["Review", asString(data.review_state)],
            ["Escalation", asString(data.escalation_boundary)],
          ]}
        />
        <RecordWarnings record={data} />
        <ValueList
          entries={[
            ["Alert id", alertRecord?.alert_id ?? data.alert_id],
            ["Case id", caseRecord?.case_id],
            ["Finding id", lineage?.finding_id],
            ["Analytic signal", lineage?.analytic_signal_id],
          ]}
        />
        <Stack direction="row" gap={1}>
          {caseRecord?.case_id ? (
            <AuditedRouteButton
              label="Open case detail"
              to={`/operator/cases/${String(caseRecord.case_id)}`}
            >
              Open case detail
            </AuditedRouteButton>
          ) : null}
          <AuditedRouteButton
            label="Open assistant advisory"
            to={`/operator/assistant/alert/${alertId}`}
          >
            Open assistant advisory
          </AuditedRouteButton>
          <AuditedRouteButton
            label="Open provenance"
            to={`/operator/provenance/alerts/${alertId}`}
          >
            Open provenance
          </AuditedRouteButton>
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Admission path and authoritative lineage stay explicit. Missing or partial linkage is not hidden."
        title="Provenance"
      >
        <ValueList
          entries={[
            ["Admission kind", getPath(data, "provenance.admission_kind")],
            ["Admission channel", getPath(data, "provenance.admission_channel")],
            ["Source system", data.source_system],
            ["Source families", lineage?.source_systems],
            ["Accountable identities", lineage?.accountable_source_identities],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="These surfaces stay secondary to the authoritative alert record and preserve mismatches instead of smoothing them away."
        title="Subordinate evidence context"
      >
        <ValueList
          entries={[
            ["Latest reconciliation", reconciliationRecord?.reconciliation_id],
            ["Detection ids", lineage?.substrate_detection_record_ids],
            ["Evidence ids", lineage?.evidence_ids],
            [
              "Current action review",
              getPath(data, "current_action_review.review_state"),
            ],
          ]}
        />
        {evidenceRecords.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Evidence</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Relationship</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {evidenceRecords.map((record) => (
                <TableRow key={String(record.evidence_id)}>
                  <TableCell>{formatValue(record.evidence_id)}</TableCell>
                  <TableCell>{formatValue(record.source_system)}</TableCell>
                  <TableCell>{formatValue(record.derivation_relationship)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No subordinate evidence records were linked." />
        )}
        <SubordinateLinks records={[...evidenceRecords, reconciliationRecord].filter((record): record is UnknownRecord => record !== null)} />
      </SectionCard>

      <PromoteAlertToCaseCard
        alertId={alertId}
        key={alertId}
        currentCaseId={asString(caseRecord?.case_id)}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />
    </Stack>
  );
}

export function AlertDetailPage({
  operatorIdentity,
}: {
  operatorIdentity: string;
}) {
  const params = useParams();
  const alertId = asString(params.alertId);

  return (
    <PageFrame
      subtitle="Read-only alert inspection keeps authoritative anchors, provenance, and subordinate evidence context explicitly separated."
      title="Alert Detail"
    >
      {alertId ? (
        <AlertDetailPageBody alertId={alertId} operatorIdentity={operatorIdentity} />
      ) : (
        <ErrorState error={new Error("Missing alert identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}

function CaseDetailPageBody({
  caseId,
  operatorIdentity,
}: {
  caseId: string;
  operatorIdentity: string;
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord("cases", caseId, recordMeta);

  if (loading && !data) {
    return <LoadingState label="Loading case detail" />;
  }

  if (error && !data) {
    return <ErrorState error={error} />;
  }

  if (!data) {
    return <EmptyState message="Case detail is unavailable." />;
  }

  const caseRecord = asRecord(data.case_record);
  const provenanceSummary = asRecord(data.provenance_summary);
  const authoritativeAnchor = asRecord(getPath(provenanceSummary, "authoritative_anchor"));
  const reconciliationRecords = asRecordArray(data.linked_reconciliation_records);
  const alertRecords = asRecordArray(data.linked_alert_records);
  const evidenceRecords = asRecordArray(data.linked_evidence_records);
  const timelineEntries = asRecordArray(data.cross_source_timeline);
  const currentActionReview = asRecord(data.current_action_review);
  const linkedEvidenceIds = asStringArray(data.linked_evidence_ids);
  const linkedObservationIds = asStringArray(data.linked_observation_ids);
  const linkedLeadIds = asStringArray(data.linked_lead_ids);
  const linkedRecommendationIds = asStringArray(data.linked_recommendation_ids);
  const currentActionRequestId = asString(currentActionReview?.action_request_id);
  const currentReviewState = asString(currentActionReview?.review_state);
  const nextExpectedAction = asString(currentActionReview?.next_expected_action);

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="Case lifecycle state and linked identifiers come from the authoritative AegisOps case record, not from summaries or substrate convenience surfaces."
        title="Authoritative anchor"
      >
        <StatusStrip
          values={[
            ["Lifecycle", asString(caseRecord?.lifecycle_state)],
            ["Current action review", asString(getPath(data, "current_action_review.review_state"))],
            ["Coordination reference", asString(getPath(data, "external_ticket_reference.status"))],
          ]}
        />
        <RecordWarnings record={data} />
        <ValueList
          entries={[
            ["Case id", caseRecord?.case_id ?? data.case_id],
            ["Current action request", currentActionRequestId],
            ["Alert ids", data.linked_alert_ids],
            ["Observation ids", data.linked_observation_ids],
            ["Lead ids", data.linked_lead_ids],
            ["Recommendation ids", data.linked_recommendation_ids],
          ]}
        />
        <Stack direction="row" gap={1}>
          {currentActionRequestId ? (
            <AuditedRouteButton
              label="Open action review"
              to={`/operator/action-review/${currentActionRequestId}`}
            >
              Open action review
            </AuditedRouteButton>
          ) : null}
          <AuditedRouteButton
            label="Open assistant advisory"
            to={`/operator/assistant/case/${caseId}`}
          >
            Open assistant advisory
          </AuditedRouteButton>
          <AuditedRouteButton
            label="Open provenance"
            to={`/operator/provenance/cases/${caseId}`}
          >
            Open provenance
          </AuditedRouteButton>
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Cross-source lineage stays anchored to the reviewed case record. Only directly linked context is pulled into this surface."
        title="Provenance summary"
      >
        <ValueList
          entries={[
            ["Anchor record family", authoritativeAnchor?.record_family],
            ["Anchor record id", authoritativeAnchor?.record_id],
            ["Anchor source family", authoritativeAnchor?.source_family],
            ["Provenance classification", authoritativeAnchor?.provenance_classification],
            ["Linked evidence ids", data.linked_evidence_ids],
            ["Linked reconciliation ids", data.linked_reconciliation_ids],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="Subordinate alert, evidence, and reconciliation context stays visible but secondary to the authoritative case state."
        title="Subordinate evidence context"
      >
        <ValueList
          entries={[
            ["Alert records", alertRecords.length],
            ["Evidence records", evidenceRecords.length],
            ["Reconciliation records", reconciliationRecords.length],
          ]}
        />
        {timelineEntries.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Record family</TableCell>
                <TableCell>Record id</TableCell>
                <TableCell>Source family</TableCell>
                <TableCell>Classification</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timelineEntries.map((entry, index) => (
                <TableRow key={`${String(entry.record_id ?? index)}-${index}`}>
                  <TableCell>{formatValue(entry.record_family)}</TableCell>
                  <TableCell>{formatValue(entry.record_id)}</TableCell>
                  <TableCell>{formatValue(entry.source_family)}</TableCell>
                  <TableCell>{formatValue(entry.provenance_classification)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No subordinate cross-source timeline entries were returned." />
        )}
        <SubordinateLinks
          records={[
            ...alertRecords,
            ...evidenceRecords,
            ...reconciliationRecords,
          ]}
        />
      </SectionCard>

      <RecordCaseObservationCard
        caseId={caseId}
        key={`observation-${caseId}`}
        linkedEvidenceIds={linkedEvidenceIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      <RecordCaseLeadCard
        caseId={caseId}
        key={`lead-${caseId}`}
        linkedObservationIds={linkedObservationIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      <RecordCaseRecommendationCard
        caseId={caseId}
        key={`recommendation-${caseId}`}
        linkedLeadIds={linkedLeadIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      {linkedRecommendationIds.length > 0 ? (
        <CreateReviewedActionRequestCard
          caseId={caseId}
          key={`action-request-${caseId}`}
          linkedRecommendationIds={linkedRecommendationIds}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
        />
      ) : null}

      {currentActionRequestId ? (
        <RecordActionReviewManualFallbackCard
          actionRequestId={currentActionRequestId}
          caseId={caseId}
          key={`manual-fallback-${caseId}-${currentActionRequestId}`}
          linkedEvidenceIds={linkedEvidenceIds}
          nextExpectedAction={nextExpectedAction}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
          reviewState={currentReviewState}
        />
      ) : null}

      {currentActionRequestId ? (
        <RecordActionReviewEscalationNoteCard
          actionRequestId={currentActionRequestId}
          caseId={caseId}
          key={`escalation-note-${caseId}-${currentActionRequestId}`}
          nextExpectedAction={nextExpectedAction}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
          reviewState={currentReviewState}
        />
      ) : null}
    </Stack>
  );
}

export function CaseDetailPage({
  operatorIdentity,
}: {
  operatorIdentity: string;
}) {
  const params = useParams();
  const caseId = asString(params.caseId);

  return (
    <PageFrame
      subtitle="Read-only case inspection keeps authoritative lifecycle state primary and preserves subordinate evidence lineage as secondary context."
      title="Case Detail"
    >
      {caseId ? (
        <CaseDetailPageBody caseId={caseId} operatorIdentity={operatorIdentity} />
      ) : (
        <ErrorState error={new Error("Missing case identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}

function ActionReviewPageBody({
  actionRequestId,
  operatorIdentity,
  operatorRoles,
}: {
  actionRequestId: string;
  operatorIdentity: string;
  operatorRoles: readonly string[];
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord("actionReview", actionRequestId, recordMeta);

  if (loading && !data) {
    return <LoadingState label="Loading action review detail" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Action review detail is unavailable." />;
  }

  const actionReview = asRecord(data.action_review);
  const currentActionReview = asRecord(data.current_action_review);
  const caseRecord = asRecord(data.case_record);
  const alertRecord = asRecord(data.alert_record);
  const timelineEntries = asRecordArray(actionReview?.timeline);
  const selectedActionRequestId = asString(actionReview?.action_request_id);
  const currentActionRequestId = asString(currentActionReview?.action_request_id);
  const actionRequestState = asString(actionReview?.action_request_state);
  const approvalState = asString(actionReview?.approval_state);
  const approvalDecisionId = asString(actionReview?.approval_decision_id);
  const reconciliationId = asString(actionReview?.reconciliation_id);
  const decisionRationale = asString(actionReview?.decision_rationale);
  const approverIdentities = asStringArray(actionReview?.approver_identities);
  const recommendationId = asString(actionReview?.recommendation_id);
  const isCurrentAuthoritativeReview =
    selectedActionRequestId !== null &&
    currentActionRequestId !== null &&
    currentActionRequestId === selectedActionRequestId;
  const canRecordApproval =
    canRecordActionApprovalDecision(operatorRoles) &&
    isCurrentAuthoritativeReview &&
    actionRequestState === "pending_approval" &&
    approvalState === "pending";

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="This page stays anchored to one authoritative action-review record. Browser-local routing does not redefine the active review."
        title="Action request detail"
      >
        <StatusStrip
          values={[
            ["Review", asString(actionReview?.review_state)],
            ["Approval", asString(actionReview?.approval_state)],
            ["Execution", asString(actionReview?.action_execution_state)],
            ["Reconciliation", asString(actionReview?.reconciliation_state)],
          ]}
        />
        {currentActionRequestId && currentActionRequestId !== selectedActionRequestId ? (
          <Alert severity="warning" variant="outlined">
            The requested record is no longer the current authoritative review for this scope.
            Current review: {currentActionRequestId}.
          </Alert>
        ) : null}
        <ValueList
          entries={[
            ["Action request id", selectedActionRequestId ?? actionRequestId],
            ["Current authoritative review", currentActionRequestId],
            ["Action request lifecycle", actionRequestState],
            ["Approval decision id", asString(actionReview?.approval_decision_id)],
            ["Requester", asString(actionReview?.requester_identity)],
            ["Recipient", asString(actionReview?.recipient_identity)],
            ["Recommendation id", asString(actionReview?.recommendation_id)],
            ["Requested at", asString(actionReview?.requested_at)],
            ["Expires at", asString(actionReview?.expires_at)],
            ["Next expected action", asString(actionReview?.next_expected_action)],
            ["Execution surface", asString(actionReview?.execution_surface_id)],
            ["Execution surface type", asString(actionReview?.execution_surface_type)],
            ["Message intent", asString(actionReview?.message_intent)],
            ["Escalation reason", asString(actionReview?.escalation_reason)],
          ]}
        />
        <Stack direction="row" gap={1}>
          {caseRecord?.case_id ? (
            <AuditedRouteButton
              label="Open case detail"
              to={`/operator/cases/${String(caseRecord.case_id)}`}
            >
              Open case detail
            </AuditedRouteButton>
          ) : null}
          {recommendationId ? (
            <AuditedRouteButton
              label="Open recommendation advisory"
              to={`/operator/assistant/recommendation/${recommendationId}`}
            >
              Open recommendation advisory
            </AuditedRouteButton>
          ) : null}
          {approvalDecisionId ? (
            <AuditedRouteButton
              label="Open approval advisory"
              to={`/operator/assistant/approval_decision/${approvalDecisionId}`}
            >
              Open approval advisory
            </AuditedRouteButton>
          ) : null}
          {reconciliationId ? (
            <AuditedRouteButton
              label="Open reconciliation advisory"
              to={`/operator/assistant/reconciliation/${reconciliationId}`}
            >
              Open reconciliation advisory
            </AuditedRouteButton>
          ) : null}
          {alertRecord?.alert_id ? (
            <AuditedRouteButton
              label="Open alert detail"
              to={`/operator/alerts/${String(alertRecord.alert_id)}`}
            >
              Open alert detail
            </AuditedRouteButton>
          ) : null}
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Approval is rendered as authoritative lifecycle state with explicit actor, rationale, and expiry instead of as a generic mutable field."
        title="Approval lifecycle"
      >
        <Stack spacing={2}>
          <Alert severity={approvalLifecycleSeverity(approvalState)} variant="outlined">
            {approvalLifecycleExplanation(approvalState)}
          </Alert>
          <ValueList
            entries={[
              ["Approval lifecycle", approvalState],
              ["Approver identities", approverIdentities],
              ["Decision rationale", decisionRationale],
              ["Approval binding expires at", asString(actionReview?.expires_at)],
              ["Next expected action", asString(actionReview?.next_expected_action)],
            ]}
          />
          {!canRecordActionApprovalDecision(operatorRoles) ? (
            <Alert severity="info" variant="outlined">
              The current reviewed session can inspect this record but cannot submit approval decisions without approver role authority.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) && !isCurrentAuthoritativeReview ? (
            <Alert severity="warning" variant="outlined">
              Approval submission stays blocked because this record is no longer the current authoritative review for the selected scope.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) &&
          isCurrentAuthoritativeReview &&
          actionRequestState !== "pending_approval" ? (
            <Alert severity="info" variant="outlined">
              Approval submission is only available while the authoritative action-request lifecycle is <strong>pending_approval</strong>.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) &&
          isCurrentAuthoritativeReview &&
          actionRequestState === "pending_approval" &&
          approvalState !== "pending" ? (
            <Alert severity="info" variant="outlined">
              Approval submission is only available while the authoritative approval lifecycle is <strong>pending</strong>.
            </Alert>
          ) : null}
        </Stack>
      </SectionCard>

      <ExecutionReceiptSection actionReview={actionReview} />

      <ReconciliationVisibilitySection actionReview={actionReview} />

      <CoordinationVisibilitySection actionReview={actionReview} />

      <SectionCard
        subtitle="Authoritative linkage stays explicit so later approval, execution, and reconciliation panels can extend this view without inferring broader workflow truth."
        title="Authoritative linkage"
      >
        <ValueList
          entries={[
            ["Case id", caseRecord?.case_id],
            ["Case lifecycle", caseRecord?.lifecycle_state],
            ["Alert id", alertRecord?.alert_id],
            ["Alert lifecycle", alertRecord?.lifecycle_state],
            ["Target scope", actionReview?.target_scope],
            ["Requested payload", actionReview?.requested_payload],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="Lifecycle-bearing review history remains visible without collapsing request, approval, execution, and reconciliation into one convenience badge."
        title="Review timeline"
      >
        {timelineEntries.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Stage</TableCell>
                <TableCell>State</TableCell>
                <TableCell>At</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timelineEntries.map((entry, index) => (
                <TableRow key={`${String(entry.label ?? entry.state ?? index)}-${index}`}>
                  <TableCell>{formatValue(entry.label)}</TableCell>
                  <TableCell>{formatValue(entry.state)}</TableCell>
                  <TableCell>{formatValue(entry.at)}</TableCell>
                  <TableCell>{formatValue(entry.details)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No action review timeline entries were returned." />
        )}
      </SectionCard>

      {canRecordApproval && selectedActionRequestId ? (
        <RecordActionApprovalDecisionCard
          actionRequestId={selectedActionRequestId}
          actionRequestState={actionRequestState}
          approvalState={approvalState}
          approverIdentity={operatorIdentity}
          decisionRationale={decisionRationale}
          expiresAt={asString(actionReview?.expires_at)}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
        />
      ) : null}
    </Stack>
  );
}

export function ActionReviewPage({
  operatorIdentity,
  operatorRoles,
}: {
  operatorIdentity: string;
  operatorRoles: readonly string[];
}) {
  const params = useParams();
  const actionRequestId = asString(params.actionRequestId);

  return (
    <PageFrame
      subtitle="Read-only action-review inspection keeps authoritative request detail, active-review selection, and lifecycle history visible without widening the browser into workflow authority."
      title="Action Review"
    >
      {actionRequestId ? (
        <ActionReviewPageBody
          actionRequestId={actionRequestId}
          operatorIdentity={operatorIdentity}
          operatorRoles={operatorRoles}
        />
      ) : (
        <SectionCard
          subtitle="Open action review from a case or alert detail page so the shell stays anchored to one authoritative action-request record."
          title="Select an action review"
        >
          <EmptyState message="No action request is selected yet." />
        </SectionCard>
      )}
    </PageFrame>
  );
}

function AdvisoryDetailTable({ record }: { record: UnknownRecord }) {
  const rows = Object.entries(record).filter(([key]) => {
    return !ADVISORY_DETAIL_EXCLUDED_FIELDS.includes(
      key as (typeof ADVISORY_DETAIL_EXCLUDED_FIELDS)[number],
    );
  });

  if (rows.length === 0) {
    return <EmptyState message="No additional advisory fields were returned for this record." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Field</TableCell>
          <TableCell>Value</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map(([key, value]) => (
          <TableRow key={key}>
            <TableCell>{formatLabel(key)}</TableCell>
            <TableCell>{formatValue(value)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function AssistantAdvisoryPageBody({
  recordFamily,
  recordId,
}: {
  recordFamily: string;
  recordId: string;
}) {
  const advisoryId = `${recordFamily}:${recordId}`;
  const meta = useMemo(
    () => ({
      recordFamily,
      recordId,
    }),
    [recordFamily, recordId],
  );
  const { data, error, loading, refreshing } = useOperatorRecord("advisoryOutput", advisoryId, meta);
  const anchorLink = supportedAnchorRoute(recordFamily, recordId);

  if (loading && !data) {
    return <LoadingState label="Loading assistant advisory" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Assistant advisory is unavailable." />;
  }

  const summary = advisorySummary(data);
  const recommendationDrafts = advisoryRecommendations(data).filter(
    (entry): entry is { citations: string[]; text: string } => entry.text !== null,
  );
  const keyObservations = advisoryContextEntries(data, "key_observations");
  const unresolvedQuestions = advisoryContextEntries(data, "unresolved_questions");
  const citations = asStringArray(data.citations);
  const uncertaintyFlags = asStringArray(data.uncertainty_flags);
  const showsRecommendationDraft =
    asString(data.output_kind) === "recommendation_draft" || recommendationDrafts.length > 0;
  const hasCitationFailure =
    uncertaintyFlags.includes("missing_supporting_citations") ||
    uncertaintyFlags.includes("missing_evidence_citation");
  const hasUnresolvedState = asString(data.status) === "unresolved";
  const hasReviewedContextConflict = uncertaintyFlags.includes("conflicting_reviewed_context");
  const hasFailureVisibility =
    hasCitationFailure || hasUnresolvedState || hasReviewedContextConflict;

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="Assistant output stays subordinate to the selected authoritative record and remains read-only inside the reviewed shell."
        title="Authoritative advisory anchor"
      >
        <StatusStrip
          values={[
            ["Status", asString(data.status)],
            ["Output", asString(data.output_kind)],
          ]}
        />
        <ValueList
          entries={[
            ["Record family", asString(data.record_family) ?? recordFamily],
            ["Record id", asString(data.record_id) ?? recordId],
            ["Read only", formatValue(data.read_only)],
          ]}
        />
        {anchorLink ? (
          <AuditedRouteButton label={anchorLink.label} to={anchorLink.to}>
            {anchorLink.label}
          </AuditedRouteButton>
        ) : null}
        <Alert severity="warning" variant="outlined">
          Assistant output does not approve, execute, or reconcile workflow state.
        </Alert>
      </SectionCard>

      {hasFailureVisibility ? (
        <SectionCard
          subtitle="Citation failures, unresolved grounding, and reviewed-context conflicts stay explicit instead of being normalized into a cleaner assistant summary."
          title="Advisory failure visibility"
        >
          <Stack spacing={2}>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {uncertaintyFlags.map((flag) => (
                <Chip
                  color={flag === "advisory_only" ? "warning" : "error"}
                  key={flag}
                  label={advisoryUncertaintyLabel(flag)}
                  size="small"
                  variant={flag === "advisory_only" ? "outlined" : "filled"}
                />
              ))}
            </Stack>
            {hasUnresolvedState ? (
              <Alert severity="error" variant="outlined">
                Assistant advisory remains unresolved because required citation or reviewed-context checks failed.
              </Alert>
            ) : null}
            {hasCitationFailure ? (
              <Alert severity="error" variant="outlined">
                Missing citation support is visible here so uncited assistant prose does not resemble reviewed workflow truth.
              </Alert>
            ) : null}
            {hasReviewedContextConflict ? (
              <Alert severity="warning" variant="outlined">
                Conflicting reviewed context remains visible here; the browser does not silently pick one record as authoritative support for assistant output.
              </Alert>
            ) : null}
            <Stack spacing={1}>
              {uncertaintyFlags.map((flag) => (
                <Alert
                  key={`uncertainty-${flag}`}
                  severity={flag === "advisory_only" ? "info" : flag === "conflicting_reviewed_context" ? "warning" : "error"}
                  variant="outlined"
                >
                  {advisoryUncertaintyMessage(flag)}
                </Alert>
              ))}
            </Stack>
          </Stack>
        </SectionCard>
      ) : null}

      <SectionCard
        subtitle="Citation-led assistant output stays visibly subordinate to the authoritative anchor and remains advisory only."
        title="Cited advisory output"
      >
        {summary.text ? (
          <Stack spacing={2}>
            <Alert severity={hasCitationFailure || hasUnresolvedState ? "warning" : "info"} variant="outlined">
              {summary.text}
            </Alert>
            {summary.citations.length > 0 ? (
              <Stack direction="row" flexWrap="wrap" gap={1}>
                {summary.citations.map((citation) => (
                  <Chip key={citation} label={citation} size="small" variant="outlined" />
                ))}
              </Stack>
            ) : (
              <EmptyState message="No cited summary anchors were returned for this advisory output." />
            )}
          </Stack>
        ) : (
          <EmptyState message="No assistant summary text was returned for this record." />
        )}
      </SectionCard>

      <SectionCard
        subtitle="Reviewed context, linked evidence, and unresolved grounding questions stay inspectable here instead of collapsing into a cleaner assistant answer."
        title="Assistant context explorer"
      >
        <Stack spacing={3}>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Reviewed context</Typography>
            <AdvisoryContextList
              emptyMessage="No reviewed context observations were returned for this advisory output."
              entries={keyObservations}
            />
          </Stack>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Unresolved grounding</Typography>
            <AdvisoryContextList
              emptyMessage="No unresolved grounding questions were returned for this advisory output."
              entries={unresolvedQuestions}
            />
          </Stack>
        </Stack>
      </SectionCard>

      {showsRecommendationDraft ? (
        <SectionCard
          subtitle="Recommendation proposals remain explicit assistant drafts and do not replace reviewed workflow state."
          title="Recommendation draft"
        >
          <Stack spacing={2}>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              <Chip color="warning" label="Draft only" size="small" />
              {uncertaintyFlags.map((flag) => (
                <Chip key={flag} label={formatLabel(flag)} size="small" variant="outlined" />
              ))}
            </Stack>
            <Alert severity="warning" variant="outlined">
              Assistant output does not approve, execute, or reconcile workflow state.
            </Alert>
            {recommendationDrafts.length > 0 ? (
              <Stack spacing={2}>
                {recommendationDrafts.map((draft, index) => (
                  <Card elevation={0} key={`${draft.text}-${index}`} sx={{ border: "1px solid", borderColor: "divider" }}>
                    <CardContent>
                      <Stack spacing={2}>
                        <Typography variant="body1">{draft.text}</Typography>
                        {draft.citations.length > 0 ? (
                          <Stack direction="row" flexWrap="wrap" gap={1}>
                            {draft.citations.map((citation) => (
                              <Chip key={`${draft.text}-${citation}`} label={citation} size="small" variant="outlined" />
                            ))}
                          </Stack>
                        ) : (
                          <EmptyState message="This recommendation draft did not include supporting citations." />
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            ) : (
              <EmptyState message="No recommendation draft proposals were returned for this advisory output." />
            )}
          </Stack>
        </SectionCard>
      ) : null}

      <SectionCard
        subtitle="Evidence citations stay visible as directly linked support for this advisory output."
        title="Evidence anchors"
      >
        {citations.length > 0 ? (
          <Stack direction="row" flexWrap="wrap" gap={1}>
            {citations.map((citation) => (
              <Chip key={citation} label={citation} size="small" variant="outlined" />
            ))}
          </Stack>
        ) : (
          <EmptyState message="No advisory citations were returned for this record." />
        )}
      </SectionCard>

      <SectionCard
        subtitle="Additional reviewed advisory fields remain readable here until richer advisory-specific rendering lands."
        title="Advisory detail"
      >
        <AdvisoryDetailTable record={data} />
      </SectionCard>
    </Stack>
  );
}

export function AssistantAdvisoryPage() {
  const params = useParams();
  const recordFamily = asString(params.recordFamily);
  const recordId = asString(params.recordId);
  const hasSupportedAdvisoryBinding =
    recordFamily !== null && SUPPORTED_ADVISORY_RECORD_FAMILIES.has(recordFamily);

  return (
    <PageFrame
      subtitle="Assistant advisory stays a dedicated read surface anchored to one authoritative record. It does not become a generic assistant chat or mutable workflow console."
      title="Assistant Advisory"
    >
      {hasSupportedAdvisoryBinding && recordId ? (
        <AssistantAdvisoryPageBody
          recordFamily={recordFamily}
          recordId={recordId}
        />
      ) : (
        <>
          {recordFamily === null || recordId === null ? (
            <SectionCard
              subtitle="Open assistant advisory from alert, case, or action-review detail so the route stays grounded in one authoritative record."
              title="Select advisory context"
            >
              <EmptyState message="No authoritative record is selected for assistant advisory yet." />
            </SectionCard>
          ) : (
            <ErrorState
              error={
                new Error(
                  "Unsupported assistant advisory route. Use alert, case, recommendation, approval decision, or reconciliation with an authoritative identifier.",
                )
              }
            />
          )}
        </>
      )}
    </PageFrame>
  );
}

function ProvenanceAlertBody({ alertId }: { alertId: string }) {
  const { data, error, loading, refreshing } = useOperatorRecord("alerts", alertId);

  if (loading && !data) {
    return <LoadingState label="Loading alert provenance" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Alert provenance is unavailable." />;
  }

  const lineage = asRecord(data.lineage);

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="This page is provenance-focused but still anchored to the reviewed alert record rather than to substrate-native summaries."
        title="Alert provenance"
      >
        <ValueList
          entries={[
            ["Alert id", data.alert_id],
            ["Reconciliation id", lineage?.reconciliation_id],
            ["Detection ids", lineage?.substrate_detection_record_ids],
            ["Accountable identities", lineage?.accountable_source_identities],
            ["First seen", lineage?.first_seen_at],
            ["Last seen", lineage?.last_seen_at],
          ]}
        />
      </SectionCard>
    </Stack>
  );
}

function ProvenanceCaseBody({ caseId }: { caseId: string }) {
  const { data, error, loading, refreshing } = useOperatorRecord("cases", caseId);

  if (loading && !data) {
    return <LoadingState label="Loading case provenance" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Case provenance is unavailable." />;
  }

  const provenanceSummary = asRecord(data.provenance_summary);
  const authoritativeAnchor = asRecord(getPath(provenanceSummary, "authoritative_anchor"));

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="Only directly linked case lineage is shown here. Neighbor or sibling lineage is not widened by inference."
        title="Case provenance"
      >
        <ValueList
          entries={[
            ["Case id", data.case_id],
            ["Anchor family", authoritativeAnchor?.record_family],
            ["Anchor id", authoritativeAnchor?.record_id],
            ["Anchor source family", authoritativeAnchor?.source_family],
            ["Linked reconciliation ids", data.linked_reconciliation_ids],
            ["Linked evidence ids", data.linked_evidence_ids],
          ]}
        />
      </SectionCard>
    </Stack>
  );
}

export function ProvenancePage() {
  const params = useParams();
  const family = asString(params.family);
  const recordId = asString(params.recordId);

  return (
    <PageFrame
      subtitle="Provenance stays a dedicated inspection surface so anchor linkage, lineage, and subordinate context can be reviewed without collapsing them together."
      title="Provenance"
    >
      {family === "alerts" && recordId ? <ProvenanceAlertBody alertId={recordId} /> : null}
      {family === "cases" && recordId ? <ProvenanceCaseBody caseId={recordId} /> : null}
      {(family !== "alerts" && family !== "cases") || recordId === null ? (
        <ErrorState error={new Error("Unsupported provenance route. Use alerts or cases with an authoritative identifier.")} />
      ) : null}
    </PageFrame>
  );
}

export function ReadinessPage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "status",
      order: "ASC" as const,
    }),
    [],
  );
  const { data, error, loading, refreshing } = useOperatorList("runtimeReadiness", filter, sort, 1);

  const record = data?.[0] ?? null;
  const reviewPathHealth = asRecord(getPath(record, "metrics.review_path_health"));
  const sourceHealth = asRecord(getPath(record, "metrics.source_health"));
  const automationHealth = asRecord(getPath(record, "metrics.automation_substrate_health"));
  const optionalEvidenceDefinitions = buildOptionalEvidenceDefinitionsFromPayload(
    getPath(record, "metrics.optional_extensions"),
  );

  return (
    <PageFrame
      subtitle="Readiness remains a reviewed status surface. It does not become a hidden write console or override authoritative backend state."
      title="Readiness"
    >
      {loading && !record ? <LoadingState label="Loading readiness diagnostics" /> : null}
      {error && !record ? <ErrorState error={error} /> : null}
      {record ? <QueryStateNotice error={error} refreshing={refreshing} /> : null}
      {record ? (
        <Stack spacing={3}>
          <SectionCard
            subtitle="Degraded or missing prerequisite signals remain explicit here."
            title="Readiness status"
          >
            <StatusStrip
              values={[
                ["Status", asString(record.status)],
                ["Booted", String(formatValue(record.booted))],
                ["Startup", String(formatValue(getPath(record, "startup.startup_ready")))],
                ["Shutdown", String(formatValue(getPath(record, "shutdown.shutdown_ready")))],
              ]}
            />
            <ValueList
              entries={[
                ["Persistence mode", record.persistence_mode],
                ["Latest reconciliation", getPath(record, "latest_reconciliation.reconciliation_id")],
                ["Action requests approved", getPath(record, "metrics.action_requests.approved")],
                ["Terminal executions", getPath(record, "metrics.action_executions.terminal")],
              ]}
            />
          </SectionCard>
          <SectionCard
            subtitle="Operator-facing health summaries are derived surfaces and stay subordinate to the authoritative diagnostic payload."
            title="Diagnostic breakdown"
          >
            <ValueList
              entries={[
                ["Review path overall state", reviewPathHealth?.overall_state],
                ["Review count", reviewPathHealth?.review_count],
                ["Tracked sources", sourceHealth?.tracked_sources],
                ["Tracked automation surfaces", automationHealth?.tracked_surfaces],
              ]}
            />
          </SectionCard>
          <SectionCard
            subtitle="Optional endpoint and network evidence paths stay visibly subordinate to authoritative alerts, cases, evidence anchors, and workflow records."
            title="Optional evidence posture"
          >
            <OptionalExtensionVisibilityPanel definitions={optionalEvidenceDefinitions} />
          </SectionCard>
        </Stack>
      ) : null}
    </PageFrame>
  );
}

export function ReconciliationPage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "latest_compared_at",
      order: "DESC" as const,
    }),
    [],
  );
  const { data, error, loading, refreshing } = useOperatorList("reconciliations", filter, sort);

  return (
    <PageFrame
      subtitle="Reconciliation surfaces keep mismatch and linkage problems visible instead of collapsing them into generic success dashboards."
      title="Reconciliation"
    >
      {loading && !data ? <LoadingState label="Loading reconciliation status" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data ? <QueryStateNotice error={error} refreshing={refreshing} /> : null}
      {data ? (
        data.length > 0 ? (
          <Stack spacing={3}>
            <SectionCard
              subtitle="Records are sorted from the latest comparison so unresolved mismatches stay visible first."
              title="Reconciliation records"
            >
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Reconciliation</TableCell>
                    <TableCell>Lifecycle</TableCell>
                    <TableCell>Ingest disposition</TableCell>
                    <TableCell>Mismatch summary</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.map((record) => (
                    <TableRow key={String(record.id ?? record.reconciliation_id)}>
                      <TableCell>{formatValue(record.reconciliation_id)}</TableCell>
                      <TableCell>{formatValue(record.lifecycle_state)}</TableCell>
                      <TableCell>{formatValue(record.ingest_disposition)}</TableCell>
                      <TableCell>{formatValue(record.mismatch_summary)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </SectionCard>
            {data.map((record) => (
              <SectionCard
                key={`reconciliation-${String(record.id ?? record.reconciliation_id)}`}
                subtitle="Authoritative reconciliation state stays primary. Subject linkage remains subordinate context and is shown without payload expansion."
                title={`Reconciliation detail: ${formatValue(record.reconciliation_id)}`}
              >
                <StatusStrip
                  values={[
                    ["Lifecycle", asString(record.lifecycle_state)],
                    ["Disposition", asString(record.ingest_disposition)],
                  ]}
                />
                <ValueList
                  entries={[
                    ["Compared at", record.compared_at],
                    ["Latest compared at", record.latest_compared_at],
                    ["Mismatch summary", record.mismatch_summary],
                    ["Subject linkage", record.subject_linkage],
                  ]}
                />
              </SectionCard>
            ))}
          </Stack>
        ) : (
          <EmptyState message="No reconciliation records are currently available." />
        )
      ) : null}
    </PageFrame>
  );
}
