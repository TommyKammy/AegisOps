import {
  Alert,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  asString,
  asStringArray,
  AuditedRouteButton,
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
  type UnknownRecord,
  useOperatorList,
} from "./shared";

const QUEUE_SORT = {
  field: "last_seen_at",
  order: "DESC" as const,
};

function sourceFamily(record: UnknownRecord) {
  return asString(getPath(record, "reviewed_context.source.source_family"));
}

function caseLifecycle(record: UnknownRecord) {
  return asString(record.case_lifecycle_state) ?? asString(getPath(record, "case_record.lifecycle_state"));
}

function ReviewedQueueLink() {
  return (
    <AuditedRouteButton label="Back to queue" to="/operator/queue">
      Back to queue
    </AuditedRouteButton>
  );
}

function AlertIndexTable({ records }: { records: UnknownRecord[] }) {
  if (records.length === 0) {
    return <EmptyState message="No alert records are currently visible in the analyst queue." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Alert</TableCell>
          <TableCell>Review</TableCell>
          <TableCell>Case anchor</TableCell>
          <TableCell>Source family</TableCell>
          <TableCell>Provenance</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {records.map((record) => {
          const alertId = asString(record.alert_id);
          const caseId = asString(record.case_id);

          return (
            <TableRow key={alertId ?? String(record.id)} hover>
              <TableCell>
                {alertId ? (
                  <AuditedRouteLink label="Open alert detail" to={`/operator/alerts/${alertId}`}>
                    {alertId}
                  </AuditedRouteLink>
                ) : (
                  formatValue(alertId)
                )}
              </TableCell>
              <TableCell>{formatValue(record.review_state)}</TableCell>
              <TableCell>
                {caseId ? (
                  <AuditedRouteLink label="Open case detail" to={`/operator/cases/${caseId}`}>
                    {caseId}
                  </AuditedRouteLink>
                ) : (
                  "No case anchor"
                )}
              </TableCell>
              <TableCell>{formatValue(sourceFamily(record))}</TableCell>
              <TableCell>
                {alertId ? (
                  <AuditedRouteLink
                    label="Open alert provenance"
                    to={`/operator/provenance/alerts/${alertId}`}
                  >
                    Open provenance
                  </AuditedRouteLink>
                ) : (
                  "Unavailable"
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function AlertIndexPage() {
  const filter = useMemo(() => ({}), []);
  const { data, error, loading, refreshing } = useOperatorList(
    "queue",
    filter,
    QUEUE_SORT,
  );

  return (
    <PageFrame
      subtitle="Read-only alert drilldown starts from backend-authoritative queue records and keeps cases, provenance, and subordinate context as linked inspection surfaces."
      title="Alerts"
    >
      {loading && !data ? <LoadingState label="Loading alert drilldown index" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data ? (
        <Stack spacing={3}>
          <QueryStateNotice error={error} refreshing={refreshing} />
          <SectionCard
            subtitle="The queue record is the bounded selection surface. Open a detail page to inspect the full authoritative alert record chain."
            title="Alert drilldown index"
          >
            <Stack spacing={2}>
              <Alert severity="info" variant="outlined">
                This page is read-only and cannot promote, approve, execute, reconcile, or edit downstream tickets.
              </Alert>
              <AlertIndexTable records={data} />
            </Stack>
          </SectionCard>
          {data.map((record) => (
            <RecordWarnings key={`warning-${String(record.id)}`} record={record} />
          ))}
          <ReviewedQueueLink />
        </Stack>
      ) : null}
    </PageFrame>
  );
}

function uniqueCaseRecords(records: UnknownRecord[]) {
  const cases = new Map<string, UnknownRecord>();

  for (const record of records) {
    const caseId = asString(record.case_id);
    if (!caseId || cases.has(caseId)) {
      continue;
    }

    cases.set(caseId, record);
  }

  return Array.from(cases.values());
}

function CaseIndexTable({ records }: { records: UnknownRecord[] }) {
  const cases = uniqueCaseRecords(records);

  if (cases.length === 0) {
    return <EmptyState message="No case anchors are currently visible in the analyst queue." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Case</TableCell>
          <TableCell>Lifecycle</TableCell>
          <TableCell>Linked alert</TableCell>
          <TableCell>Source family</TableCell>
          <TableCell>Provenance</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {cases.map((record) => {
          const caseId = asString(record.case_id);
          const alertId = asString(record.alert_id);

          return (
            <TableRow key={caseId ?? String(record.id)} hover>
              <TableCell>
                {caseId ? (
                  <AuditedRouteLink label="Open case detail" to={`/operator/cases/${caseId}`}>
                    {caseId}
                  </AuditedRouteLink>
                ) : (
                  formatValue(caseId)
                )}
              </TableCell>
              <TableCell>{formatValue(caseLifecycle(record))}</TableCell>
              <TableCell>
                {alertId ? (
                  <AuditedRouteLink label="Open alert detail" to={`/operator/alerts/${alertId}`}>
                    {alertId}
                  </AuditedRouteLink>
                ) : (
                  "Unavailable"
                )}
              </TableCell>
              <TableCell>{formatValue(sourceFamily(record))}</TableCell>
              <TableCell>
                {caseId ? (
                  <AuditedRouteLink
                    label="Open case provenance"
                    to={`/operator/provenance/cases/${caseId}`}
                  >
                    Open provenance
                  </AuditedRouteLink>
                ) : (
                  "Unavailable"
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function CaseIndexPage() {
  const filter = useMemo(() => ({}), []);
  const { data, error, loading, refreshing } = useOperatorList(
    "queue",
    filter,
    QUEUE_SORT,
  );

  return (
    <PageFrame
      subtitle="Read-only case drilldown starts from case anchors already present in the authoritative analyst queue projection."
      title="Cases"
    >
      {loading && !data ? <LoadingState label="Loading case drilldown index" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data ? (
        <Stack spacing={3}>
          <QueryStateNotice error={error} refreshing={refreshing} />
          <SectionCard
            subtitle="Cases listed here are selected only from explicit queue case anchors; sibling or naming-derived cases are not inferred."
            title="Case drilldown index"
          >
            <Stack spacing={2}>
              <Alert severity="info" variant="outlined">
                This page is read-only and cannot record observations, leads, recommendations, approvals, executions, or ticket edits.
              </Alert>
              <CaseIndexTable records={data} />
            </Stack>
          </SectionCard>
          <ReviewedQueueLink />
        </Stack>
      ) : null}
    </PageFrame>
  );
}

function ProvenanceIndexTable({
  family,
  records,
}: {
  family: "alerts" | "cases";
  records: UnknownRecord[];
}) {
  const visibleRecords =
    family === "cases" ? uniqueCaseRecords(records) : records;

  if (visibleRecords.length === 0) {
    return (
      <EmptyState
        message={`No ${family === "cases" ? "case anchors" : "alert records"} are currently visible for provenance drilldown.`}
      />
    );
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Authoritative record</TableCell>
          <TableCell>Linked context</TableCell>
          <TableCell>Source family</TableCell>
          <TableCell>Provenance drilldown</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {visibleRecords.map((record) => {
          const alertId = asString(record.alert_id);
          const caseId = asString(record.case_id);
          const recordId = family === "cases" ? caseId : alertId;
          const linkedContext =
            family === "cases" ? alertId : caseId ?? asStringArray(record.linked_case_ids).join(", ");

          return (
            <TableRow key={`${family}-${recordId ?? String(record.id)}`} hover>
              <TableCell>{formatValue(recordId)}</TableCell>
              <TableCell>{formatValue(linkedContext)}</TableCell>
              <TableCell>{formatValue(sourceFamily(record))}</TableCell>
              <TableCell>
                {recordId ? (
                  <AuditedRouteLink
                    label="Open provenance detail"
                    to={`/operator/provenance/${family}/${recordId}`}
                  >
                    Open provenance
                  </AuditedRouteLink>
                ) : (
                  "Unavailable"
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function ProvenanceIndexPage() {
  const params = useParams();
  const family = asString(params.family);
  const selectedFamily = family === "cases" ? "cases" : "alerts";
  const filter = useMemo(() => ({}), []);
  const { data, error, loading, refreshing } = useOperatorList(
    "queue",
    filter,
    QUEUE_SORT,
  );

  return (
    <PageFrame
      subtitle="Read-only provenance drilldown starts from explicitly linked queue records and opens bounded record-chain pages for alert or case anchors."
      title="Provenance"
    >
      {family !== null && family !== "alerts" && family !== "cases" ? (
        <ErrorState
          error={
            new Error(
              "Unsupported provenance route. Use alerts or cases with an authoritative identifier.",
            )
          }
        />
      ) : null}
      {loading && !data ? <LoadingState label="Loading provenance drilldown index" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data && (family === null || family === "alerts" || family === "cases") ? (
        <Stack spacing={3}>
          <QueryStateNotice error={error} refreshing={refreshing} />
          <SectionCard
            subtitle="Choose an explicit alert or case anchor before inspecting provenance. The page does not infer lineage from names, neighbors, or sibling records."
            title="Record-chain drilldown index"
          >
            <Stack spacing={2}>
              <StatusStrip
                values={[
                  ["Family", selectedFamily],
                  ["Read mode", "read-only"],
                ]}
              />
              <Stack direction="row" gap={1}>
                <AuditedRouteButton label="Show alert provenance" to="/operator/provenance/alerts">
                  Alert provenance
                </AuditedRouteButton>
                <AuditedRouteButton label="Show case provenance" to="/operator/provenance/cases">
                  Case provenance
                </AuditedRouteButton>
              </Stack>
              <Typography color="text.secondary" variant="body2">
                Missing optional evidence remains unavailable rather than being promoted into authoritative record truth.
              </Typography>
              <ProvenanceIndexTable family={selectedFamily} records={data} />
            </Stack>
          </SectionCard>
          <ReviewedQueueLink />
        </Stack>
      ) : null}
    </PageFrame>
  );
}
