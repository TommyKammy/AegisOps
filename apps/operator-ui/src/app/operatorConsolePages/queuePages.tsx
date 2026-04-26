import {
  Alert,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import {
  asRecord,
  asRecordArray,
  asString,
  asStringArray,
  formatLabel,
  AuditedRouteLink,
  EmptyState,
  ErrorState,
  formatValue,
  getPath,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  RecordWarnings,
  SectionCard,
  StatusStrip,
  statusTone,
  useOperatorList,
  ValueList,
} from "./shared";

const QUEUE_LANE_LABELS: Record<string, string> = {
  action_required: "Action required",
  reconciliation_mismatch: "Reconciliation mismatch",
  stale_receipt: "Stale receipt",
  optional_extension_degraded: "Optional extension degraded",
  clean: "Clean",
};

function aiTraceReviewStateLabel(state: string) {
  switch (state) {
    case "provider_degraded":
      return "Provider degraded";
    case "citation_failure":
      return "Citation failure";
    case "conflict":
      return "Conflict";
    case "unresolved":
      return "Unresolved";
    default:
      return state
        .replace(/[_-]+/g, " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
  }
}

function QueueAiTraceReviewGroups({ records }: { records: Record<string, unknown>[] }) {
  const groups = records.flatMap((record) =>
    asRecordArray(record.ai_trace_review_groups).map((group) => ({
      alertId: asString(group.alert_id) ?? asString(record.alert_id),
      caseId: asString(group.case_id) ?? asString(record.case_id),
      states: asStringArray(group.states),
      traceCount: typeof group.trace_count === "number" ? group.trace_count : null,
      traceLink: asString(group.trace_link),
      traces: asRecordArray(group.traces),
    })),
  );

  if (groups.length === 0) {
    return null;
  }

  return (
    <SectionCard
      subtitle="Unresolved assistant trace states stay grouped by authoritative alert or case scope for daily review. These links open read-only trace context only."
      title="AI Trace review queue"
    >
      <Stack spacing={2}>
        <Alert severity="warning" variant="outlined">
          AI Trace review is advisory-only; it cannot approve, execute, reconcile, or override reviewed records.
        </Alert>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Scope</TableCell>
              <TableCell>Trace states</TableCell>
              <TableCell>Trace count</TableCell>
              <TableCell>Review link</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((group) => {
              const traceKey =
                group.traceLink ??
                group.traces
                  .map((trace) => asString(trace.ai_trace_id))
                  .find((traceId): traceId is string => traceId !== null) ??
                `${group.alertId ?? "alert"}:${group.caseId ?? "case"}`;
              return (
                <TableRow hover key={traceKey}>
                  <TableCell>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">
                        Alert: {group.alertId ?? "Not available"}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        Case: {group.caseId ?? "No case anchor"}
                      </Typography>
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" flexWrap="wrap" gap={1}>
                      {group.states.map((state) => (
                        <Chip
                          color={statusTone(state)}
                          key={`${traceKey}-${state}`}
                          label={aiTraceReviewStateLabel(state)}
                          size="small"
                          variant={state === "unresolved" ? "outlined" : "filled"}
                        />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>{group.traceCount ?? group.traces.length}</TableCell>
                  <TableCell>
                    {group.traceLink ? (
                      <AuditedRouteLink label="Open AI trace review" to={group.traceLink}>
                        Open AI trace review
                      </AuditedRouteLink>
                    ) : (
                      <Typography color="text.secondary" variant="body2">
                        No trace link
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Stack>
    </SectionCard>
  );
}

function queueLaneLabel(lane: string) {
  return QUEUE_LANE_LABELS[lane] ?? formatLabel(lane);
}

function QueueLaneSummary({ records }: { records: Record<string, unknown>[] }) {
  const counts = Object.keys(QUEUE_LANE_LABELS).map((lane) => {
    const count = records.filter((record) =>
      asStringArray(record.queue_lanes).includes(lane),
    ).length;
    return [lane, count] as const;
  });

  return (
    <SectionCard
      subtitle="These lanes make mismatch and degraded state visible for review without making receipts or optional extensions authoritative."
      title="Queue lanes"
    >
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {counts.map(([lane, count]) => (
          <Chip
            color={statusTone(lane)}
            key={lane}
            label={`${queueLaneLabel(lane)}: ${count}`}
            size="small"
            variant={count > 0 ? "filled" : "outlined"}
          />
        ))}
      </Stack>
    </SectionCard>
  );
}

function QueueLaneDetails({ record }: { record: Record<string, unknown> }) {
  const lanes = asStringArray(record.queue_lanes);
  const details = asRecord(record.queue_lane_details);
  const degradedExtensions = asRecord(details?.optional_extension_degraded);
  const reconciliationMismatch = asRecord(details?.reconciliation_mismatch);
  const staleReceipt = asRecord(details?.stale_receipt);
  const detailLines: string[] = [];

  const mismatchSummary = asString(reconciliationMismatch?.summary);
  if (mismatchSummary) {
    detailLines.push(mismatchSummary);
  }

  const staleSummary = asString(staleReceipt?.summary);
  if (staleSummary && staleSummary !== mismatchSummary) {
    detailLines.push(staleSummary);
  }

  if (degradedExtensions) {
    for (const [extensionName, extensionState] of Object.entries(degradedExtensions)) {
      const extensionRecord = asRecord(extensionState);
      const reason = asString(extensionRecord?.reason);
      if (reason) {
        detailLines.push(
          `${formatLabel(extensionName).toLowerCase()}: ${reason.replace(/_/g, " ")}`,
        );
      }
    }
  }

  if (lanes.length === 0 && detailLines.length === 0) {
    return null;
  }

  return (
    <Stack spacing={0.75}>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {lanes.map((lane) => (
          <Chip
            color={statusTone(lane)}
            key={lane}
            label={queueLaneLabel(lane)}
            size="small"
            variant={lane === "clean" ? "outlined" : "filled"}
          />
        ))}
      </Stack>
      {detailLines.map((line) => (
        <Typography color="text.secondary" key={line} variant="caption">
          {line}
        </Typography>
      ))}
    </Stack>
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
          <Stack spacing={3}>
            <QueueLaneSummary records={data} />
            <QueueAiTraceReviewGroups records={data} />
            <SectionCard
              subtitle="Explicit degraded, pending, and mismatch states remain visible instead of being smoothed away."
              title="Queue records"
            >
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Alert</TableCell>
                    <TableCell>Review state</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Age</TableCell>
                    <TableCell>Case</TableCell>
                    <TableCell>Source family</TableCell>
                    <TableCell>Action review</TableCell>
                    <TableCell>Lanes</TableCell>
                    <TableCell>Next action</TableCell>
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
                    const owner = asString(record.owner);
                    const severity = asString(record.severity);
                    const ageBucket = asString(record.age_bucket);
                    const nextAction = asString(record.next_action);
                    return (
                      <TableRow hover key={String(record.id ?? alertId)}>
                        <TableCell>
                          <Typography component="div">
                            <AuditedRouteLink
                              label="Open alert detail"
                              to={`/operator/alerts/${alertId}`}
                            >
                              {alertId}
                            </AuditedRouteLink>
                          </Typography>
                          <Typography color="text.secondary" variant="caption">
                            {formatValue(record.queue_selection)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <StatusStrip values={[["Review", asString(record.review_state)]]} />
                        </TableCell>
                        <TableCell>{owner ?? "Unassigned"}</TableCell>
                        <TableCell>{severity ?? "Not available"}</TableCell>
                        <TableCell>{ageBucket ?? "Not available"}</TableCell>
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
                        <TableCell>
                          <QueueLaneDetails record={record} />
                        </TableCell>
                        <TableCell>{nextAction ?? "Review queue record"}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </SectionCard>
          </Stack>
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
              ["Owner", asString(record.owner)],
              ["Severity", asString(record.severity)],
              ["Age", asString(record.age_bucket)],
              ["Action review", asString(getPath(record, "current_action_review.review_state"))],
            ]}
          />
          <QueueLaneDetails record={record} />
          <RecordWarnings record={record} />
          <ValueList
            entries={[
              ["Last activity", record.last_activity_at],
              ["Next action", record.next_action],
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
