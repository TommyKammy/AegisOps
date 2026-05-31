import ReportProblemOutlinedIcon from "@mui/icons-material/ReportProblemOutlined";
import {
  Alert,
  Chip,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import {
  asString,
  asStringArray,
  AuditedRouteLink,
  EmptyState,
  ErrorState,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  SectionCard,
  formatLabel,
  statusTone,
  useOperatorList,
  useOperatorRecord,
  type UnknownRecord,
} from "./shared";

const LIMITATION_OWNERSHIP_LIST_SORT = {
  field: "limitation_id",
  order: "ASC",
} as const;

function lowerLabel(value: string | null) {
  return formatLabel(value ?? "unknown").toLowerCase();
}

function LimitationOwnershipUnavailable() {
  return (
    <PageFrame
      subtitle="The browser refuses stale, malformed, or authority-promoting limitation projections."
      title="Limitation ownership unavailable"
    >
      <Alert severity="error" variant="outlined">
        The backend limitation ownership projection was stale, malformed, or
        claimed authority the browser cannot hold.
      </Alert>
    </PageFrame>
  );
}

export function LimitationOwnershipPage() {
  const [searchParams] = useSearchParams();
  const requestedLimitationId = searchParams.get("limitation_id")?.trim();

  if (!requestedLimitationId) {
    return <LimitationOwnershipSelectionPage />;
  }

  return <LimitationOwnershipDetailPage limitationId={requestedLimitationId} />;
}

function limitationOwnershipRoute(recordId: string) {
  const params = new URLSearchParams({ limitation_id: recordId });

  return `/operator/limitations?${params.toString()}`;
}

function LimitationOwnershipSelectionTable({ records }: { records: UnknownRecord[] }) {
  if (records.length === 0) {
    return <EmptyState message="No reviewed limitation ownership records are available." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Limitation</TableCell>
          <TableCell>Owner</TableCell>
          <TableCell>Severity</TableCell>
          <TableCell>Review</TableCell>
          <TableCell>Handoff</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {records.map((record) => {
          const limitationId = asString(record.limitation_id) ?? String(record.id);
          const title = asString(record.title) ?? limitationId;

          return (
            <TableRow hover key={limitationId}>
              <TableCell>
                <AuditedRouteLink
                  label="Open reviewed limitation ownership"
                  to={limitationOwnershipRoute(limitationId)}
                >
                  {title}
                </AuditedRouteLink>
              </TableCell>
              <TableCell>{asString(record.owner)}</TableCell>
              <TableCell>{formatLabel(asString(record.severity) ?? "unknown")}</TableCell>
              <TableCell>{formatLabel(asString(record.review_state) ?? "unknown")}</TableCell>
              <TableCell>
                {formatLabel(asString(record.phase66_handoff_posture) ?? "unknown")}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

function LimitationOwnershipSelectionPage() {
  const filter = useMemo(() => ({}), []);
  const results = useOperatorList(
    "limitationOwnership",
    filter,
    LIMITATION_OWNERSHIP_LIST_SORT,
    null,
  );

  if (results.loading && results.data === null) {
    return (
      <PageFrame
        subtitle="Loading backend-reviewed limitation ownership records before detail inspection."
        title="Limitation ownership"
      >
        <LoadingState label="Loading limitation ownership records" />
      </PageFrame>
    );
  }

  return (
    <PageFrame
      subtitle="Choose a reviewed limitation record before loading the backend projection; detail inspection requires an explicit limitation id."
      title="Limitation ownership"
    >
      {results.error && results.data === null ? (
        <ErrorState error={results.error} />
      ) : (
        <Stack spacing={2}>
          <Alert severity="info" variant="outlined">
            Limitation ownership detail remains subordinate backend context and
            requires a concrete reviewed limitation id.
          </Alert>
          <QueryStateNotice
            error={results.error}
            refreshing={results.refreshing}
          />
          <LimitationOwnershipSelectionTable records={results.data ?? []} />
        </Stack>
      )}
    </PageFrame>
  );
}

function LimitationOwnershipDetailPage({ limitationId }: { limitationId: string }) {
  const meta = useMemo(() => ({}), []);
  const { data, error, loading } = useOperatorRecord(
    "limitationOwnership",
    limitationId,
    meta,
  );
  const title = asString(data?.title) ?? "Reviewed limitation";
  const severity = asString(data?.severity);
  const reviewState = asString(data?.review_state);
  const owner = asString(data?.owner);
  const mitigation = asString(data?.mitigation);
  const affectedSurface = asString(data?.affected_surface);
  const acceptedRiskPosture = asString(data?.accepted_risk_posture);
  const handoffPosture = asString(data?.phase66_handoff_posture);
  const dueDate = asString(data?.due_date);
  const reviewCadence = asString(data?.review_cadence);
  const dueDateStatus = asString(data?.review_due_date_status);
  const authorityPosture = asString(data?.authority_posture);
  const evidenceReferences = asStringArray(data?.evidence_references);

  if (loading && !data) {
    return (
      <PageFrame
        subtitle="Loading the backend-reviewed limitation ownership projection."
        title="Limitation ownership"
      >
        <LoadingState label="Loading limitation ownership" />
      </PageFrame>
    );
  }

  if (error || !data) {
    return <LimitationOwnershipUnavailable />;
  }

  return (
    <PageFrame
      subtitle="Reviewed ownership context for known limitations; backend records remain authoritative."
      title="Limitation ownership"
    >
      <Stack spacing={3}>
        <Alert severity="info" variant="outlined">
          This surface cannot satisfy readiness, release, gate, workflow, or
          limitation resolution truth.
        </Alert>
        <SectionCard
          subtitle="Owner, mitigation, evidence, review posture, and handoff posture are rendered from the backend projection."
          title={title}
        >
          <Stack spacing={2}>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {severity ? (
                <Chip
                  color={statusTone(severity)}
                  icon={<ReportProblemOutlinedIcon />}
                  label={formatLabel(severity)}
                  size="small"
                  variant="filled"
                />
              ) : null}
              {reviewState ? (
                <Chip
                  color={statusTone(reviewState)}
                  label={formatLabel(reviewState)}
                  size="small"
                  variant="outlined"
                />
              ) : null}
              {dueDateStatus ? (
                <Chip
                  color={statusTone(dueDateStatus)}
                  label={`Review ${formatLabel(dueDateStatus)}`}
                  size="small"
                  variant="outlined"
                />
              ) : null}
              <Chip
                color="info"
                label="Subordinate limitation context only"
                size="small"
                variant="outlined"
              />
            </Stack>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Stack spacing={1}>
                  <Typography variant="body2">Owner: {owner}</Typography>
                  <Typography color="text.secondary" variant="body2">
                    Affected surface: {lowerLabel(affectedSurface)}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Phase 66 handoff: {lowerLabel(handoffPosture)}
                  </Typography>
                  {reviewState === "accepted_risk" ? (
                    <Typography color="text.secondary" variant="body2">
                      Accepted risk posture:{" "}
                      {formatLabel(acceptedRiskPosture ?? "unknown")}
                    </Typography>
                  ) : null}
                  <Typography color="text.secondary" variant="body2">
                    Due date: {dueDate ?? "Not specified"}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Cadence: {reviewCadence ?? "Not specified"}
                  </Typography>
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Stack spacing={1}>
                  <Typography variant="body2">{mitigation}</Typography>
                  <Typography color="text.secondary" variant="caption">
                    Authority posture: {formatLabel(authorityPosture ?? "unknown")}
                  </Typography>
                </Stack>
              </Grid>
            </Grid>
            <Stack spacing={0.75}>
              <Typography variant="caption">Evidence references</Typography>
              {evidenceReferences.map((reference) => (
                <Typography color="text.secondary" key={reference} variant="body2">
                  {reference}
                </Typography>
              ))}
            </Stack>
          </Stack>
        </SectionCard>
      </Stack>
    </PageFrame>
  );
}
