import {
  Alert,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  StatusStrip,
  ValueList,
  asString,
  asStringArray,
  statusTone,
  useOperatorList,
  type UnknownRecord,
} from "./shared";

const SOURCE_HEALTH_FILTER = {};
const SOURCE_HEALTH_SORT = {
  field: "source_family",
  order: "ASC",
} as const;

function SourceHealthCard({ record }: { record: UnknownRecord }) {
  const healthState = asString(record.health_state);
  const evidenceReferences = asStringArray(record.evidence_references);

  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack
            alignItems={{ xs: "flex-start", sm: "center" }}
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            spacing={1}
          >
            <Stack spacing={0.5}>
              <Typography fontWeight={700}>
                {asString(record.source_family)}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {asString(record.source_health_id)}
              </Typography>
            </Stack>
            <Chip
              color={statusTone(healthState)}
              label={healthState}
              size="small"
              variant={statusTone(healthState) === "default" ? "outlined" : "filled"}
            />
          </Stack>

          <StatusStrip
            values={[
              ["Reviewed", asString(record.reviewed_state)],
              ["Detector drift", asString(record.detector_drift)],
              ["Credential", asString(record.credential_posture)],
            ]}
          />

          <ValueList
            entries={[
              ["Catalog entry", asString(record.source_catalog_entry)],
              ["Observed at", asString(record.observed_at)],
              ["Reviewed at", asString(record.reviewed_at)],
              ["Reviewed evidence", evidenceReferences],
            ]}
          />

          <Alert severity="warning" variant="outlined">
            {asString(record.operator_visible_reason)}
          </Alert>
        </Stack>
      </CardContent>
    </Card>
  );
}

export function SourceHealthDashboardPage() {
  const sourceHealthRecords = useOperatorList(
    "sourceHealthDashboard",
    SOURCE_HEALTH_FILTER,
    SOURCE_HEALTH_SORT,
    null,
  );

  if (sourceHealthRecords.loading && sourceHealthRecords.data === null) {
    return <LoadingState label="Loading source-health dashboard" />;
  }

  return (
    <PageFrame
      subtitle="Source-health posture is reviewed operational context only. Source-native health, browser state, UI cache, detector display state, and dashboard state cannot close cases, approve action, reconcile outcomes, or suppress signals."
      title="Source Health Dashboard"
    >
      {sourceHealthRecords.error && sourceHealthRecords.data === null ? (
        <ErrorState error={sourceHealthRecords.error} />
      ) : (
        <Stack spacing={2}>
          <QueryStateNotice
            error={sourceHealthRecords.error}
            refreshing={sourceHealthRecords.refreshing}
          />
          <Alert severity="info" variant="outlined">
            Rows are bound to reviewed source catalog entries and remain
            read-only until the backend authoritative record chain is reread.
          </Alert>
          {sourceHealthRecords.data && sourceHealthRecords.data.length > 0 ? (
            <Grid container spacing={2}>
              {sourceHealthRecords.data.map((record) => (
                <Grid key={asString(record.source_health_id)} size={{ xs: 12, lg: 6 }}>
                  <SourceHealthCard record={record} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <EmptyState message="No reviewed source-health records are available for dashboard visibility." />
          )}
        </Stack>
      )}
    </PageFrame>
  );
}
