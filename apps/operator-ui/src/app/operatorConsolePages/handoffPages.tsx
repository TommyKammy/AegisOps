import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useMemo } from "react";
import {
  asRecord,
  asRecordArray,
  asString,
  EmptyState,
  LoadingState,
  PageFrame,
  SectionCard,
  formatLabel,
  statusTone,
  useOperatorRecord,
} from "./shared";

function BusinessHoursHandoffUnavailable() {
  return (
    <PageFrame
      subtitle="The browser refuses stale or malformed handoff projections."
      title="Business-hours handoff unavailable"
    >
      <Alert severity="error" variant="outlined">
        The backend handoff projection was stale or malformed, so the browser
        refused to present it as current handoff guidance.
      </Alert>
    </PageFrame>
  );
}

function aiSummaryLabel(posture: string | null) {
  if (posture === "accepted_for_reference") {
    return "AI accepted for reference";
  }
  if (posture === "rejected_for_reference") {
    return "AI rejected for reference";
  }
  return "AI summary missing";
}

function HandoffItem({ item }: { item: Record<string, unknown> }) {
  const title = asString(item.title) ?? "Untitled handoff item";
  const state = asString(item.state);
  const changedWork = asString(item.changed_work);
  const blockedOwner = asString(item.blocked_owner);
  const followUp = asString(item.follow_up);
  const binding = asRecord(item.backend_record_binding);
  const recordFamily = asString(binding?.record_family);
  const recordId = asString(binding?.record_id);
  const aiSummaryHandling = asRecord(item.ai_summary_handling);
  const aiPosture = asString(aiSummaryHandling?.posture);
  const evidenceGaps = Array.isArray(item.evidence_gaps)
    ? item.evidence_gaps.filter((gap) => asString(gap) !== null)
    : [];

  return (
    <Stack
      spacing={1.25}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        height: "100%",
        p: 1.5,
      }}
    >
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {state ? (
          <Chip
            color={statusTone(state)}
            label={formatLabel(state)}
            size="small"
            variant="filled"
          />
        ) : null}
        <Chip
          color="warning"
          label="State remains open"
          size="small"
          variant="outlined"
        />
        <Chip
          color="info"
          icon={<AutoAwesomeOutlinedIcon />}
          label="Advisory only"
          size="small"
          variant="outlined"
        />
      </Stack>
      <Typography variant="subtitle2">{title}</Typography>
      <Typography color="text.secondary" variant="body2">
        {changedWork}
      </Typography>
      <Typography variant="body2">Owner: {blockedOwner}</Typography>
      <Typography color="text.secondary" variant="body2">
        Follow-up: {followUp}
      </Typography>
      <Stack spacing={0.5}>
        <Typography variant="caption">Evidence gaps</Typography>
        {evidenceGaps.length > 0 ? (
          evidenceGaps.map((gap) => (
            <Typography color="text.secondary" key={String(gap)} variant="body2">
              {String(gap)}
            </Typography>
          ))
        ) : (
          <Typography color="text.secondary" variant="body2">
            No explicit evidence gaps in this handoff item.
          </Typography>
        )}
      </Stack>
      <Typography color="text.secondary" variant="caption">
        Backend anchor: {recordFamily ?? "record"}:{recordId ?? "missing"}
      </Typography>
      <Typography color="text.secondary" variant="caption">
        {aiSummaryLabel(aiPosture)}
      </Typography>
    </Stack>
  );
}

export function BusinessHoursHandoffPage() {
  const meta = useMemo(() => ({}), []);
  const { data, error, loading } = useOperatorRecord(
    "businessHoursHandoff",
    "current",
    meta,
  );
  const items = asRecordArray(data?.items);

  if (loading && !data) {
    return (
      <PageFrame
        subtitle="Loading the current backend-bound handoff projection."
        title="Business-hours handoff"
      >
        <LoadingState label="Loading business-hours handoff" />
      </PageFrame>
    );
  }

  if (error) {
    return <BusinessHoursHandoffUnavailable />;
  }

  return (
    <PageFrame
      subtitle="Part-time operator handoff guidance for changed work, blocked owners, follow-up, evidence gaps, and advisory AI summary handling."
      title="Business-hours handoff"
    >
      <Stack spacing={3}>
        <Alert severity="info" variant="outlined">
          Handoff copy cannot close cases, approve actions, execute work,
          reconcile outcomes, satisfy audit evidence, or override backend
          records.
        </Alert>
        <SectionCard
          subtitle="Unresolved and failed paths remain open until the backend record chain changes."
          title="Handoff items"
        >
          {items.length > 0 ? (
            <Grid container spacing={2}>
              {items.map((item) => (
                <Grid key={asString(item.item_id) ?? JSON.stringify(item)} size={{ xs: 12, md: 6 }}>
                  <HandoffItem item={item} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <EmptyState message="No backend-bound handoff items are in the current projection." />
          )}
        </SectionCard>
      </Stack>
    </PageFrame>
  );
}
