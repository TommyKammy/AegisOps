import { Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { useMemo } from "react";
import {
  asString,
  asStringArray,
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
  useOperatorList,
  ValueList,
} from "./shared";

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
              ["Action review", asString(getPath(record, "current_action_review.review_state"))],
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
