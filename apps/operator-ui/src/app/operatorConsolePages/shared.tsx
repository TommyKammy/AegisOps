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
  Typography,
} from "@mui/material";
import { type ReactNode, useMemo } from "react";
import { Link as ReactRouterLink } from "react-router-dom";
import { useDataProvider } from "react-admin";
import { useOperatorUiEventLog } from "../operatorUiEvents";
import {
  buildOperatorQueryKey,
  useOperatorQueryLoader,
  useOperatorQueryState,
} from "../operatorQueryCache";

export type UnknownRecord = Record<string, unknown>;

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refreshing: boolean;
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

export const SUPPORTED_ADVISORY_RECORD_FAMILIES = new Set([
  "alert",
  "case",
  "recommendation",
  "approval_decision",
  "reconciliation",
]);

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

export function advisorySummary(record: UnknownRecord) {
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

export function advisoryRecommendations(record: UnknownRecord) {
  return asRecordArray(record.candidate_recommendations).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

export function advisoryContextEntries(
  record: UnknownRecord,
  field: "key_observations" | "unresolved_questions",
) {
  return asRecordArray(record[field]).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

export function advisoryUncertaintyMessage(flag: string): string {
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

export function advisoryUncertaintyLabel(flag: string): string {
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

export function advisoryDetailRows(record: UnknownRecord) {
  return Object.entries(record).filter(([key]) => {
    return !ADVISORY_DETAIL_EXCLUDED_FIELDS.includes(
      key as (typeof ADVISORY_DETAIL_EXCLUDED_FIELDS)[number],
    );
  });
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

export function canRecordActionApprovalDecision(operatorRoles: readonly string[]) {
  return operatorRoles.some((role) => role.toLowerCase() === "approver");
}

export function approvalLifecycleExplanation(approvalState: string | null) {
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

export function approvalLifecycleSeverity(
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

export function ExecutionReceiptSection({
  actionReview,
}: {
  actionReview: UnknownRecord | null;
}) {
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

export function ReconciliationVisibilitySection({
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

export function CoordinationVisibilitySection({
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
            ["Requested coordination reference id", requestedCoordinationReferenceId],
            ["Observed coordination reference id", observedCoordinationReferenceId],
            ["Requested coordination target type", requestedCoordinationTargetType],
            ["Observed coordination target type", observedCoordinationTargetType],
            ["Requested coordination target id", requestedCoordinationTargetId],
            ["Observed coordination target id", observedCoordinationTargetId],
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

export function useOperatorList(
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

export function useOperatorRecord(
  resource: string,
  id: string,
  meta?: Record<string, unknown>,
): QueryState<UnknownRecord> {
  const dataProvider = useDataProvider();
  const metaRecord = meta && typeof meta === "object" ? meta : {};
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

export function PageFrame({
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

export function LoadingState({ label }: { label: string }) {
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

export function ErrorState({ error }: { error: Error }) {
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

export function QueryStateNotice({
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

export function SectionCard({
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

export function ValueList({
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

export function StatusStrip({
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

export function EmptyState({ message }: { message: string }) {
  return (
    <Alert severity="info" variant="outlined">
      {message}
    </Alert>
  );
}

export function AdvisoryContextList({
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
        <Card
          elevation={0}
          key={`${entry.text}-${index}`}
          sx={{ border: "1px solid", borderColor: "divider" }}
        >
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="body1">{entry.text}</Typography>
              {entry.citations.length > 0 ? (
                <Stack direction="row" flexWrap="wrap" gap={1}>
                  {entry.citations.map((citation) => (
                    <Chip
                      key={`${entry.text}-${citation}`}
                      label={citation}
                      size="small"
                      variant="outlined"
                    />
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

export function supportedAnchorRoute(
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

export function RecordWarnings({ record }: { record: UnknownRecord }) {
  const warnings: string[] = [];
  const reviewState = asString(record.review_state);
  const externalTicketStatus = asString(getPath(record, "external_ticket_reference.status"));

  if (
    reviewState !== null &&
    ["degraded", "rejected", "missing_anchor", "mismatch"].includes(reviewState)
  ) {
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
        <Alert
          icon={<ReportProblemOutlinedIcon fontSize="inherit" />}
          key={warning}
          severity="warning"
          variant="outlined"
        >
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

export function SubordinateLinks({ records }: { records: UnknownRecord[] }) {
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

export function AuditedRouteLink({
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

export function AuditedRouteButton({
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
