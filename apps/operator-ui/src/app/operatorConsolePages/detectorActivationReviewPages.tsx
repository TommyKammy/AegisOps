import {
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
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

const DETECTOR_ACTIVATION_REVIEW_FILTER = {};
const DETECTOR_ACTIVATION_REVIEW_SORT = {
  field: "detector_identifier",
  order: "ASC",
} as const;

function reasonForLifecycle(record: UnknownRecord) {
  const lifecycleState = asString(record.lifecycle_state);
  if (lifecycleState === "disabled") {
    return asString(record.disabled_reason);
  }
  if (lifecycleState === "rollback") {
    return asString(record.rollback_reason);
  }
  if (lifecycleState === "review-overdue") {
    return asString(record.review_overdue_reason);
  }

  return null;
}

function DetectorLifecycleCard({ record }: { record: UnknownRecord }) {
  const lifecycleState = asString(record.lifecycle_state);
  const sourceNativeState = asString(record.source_native_lifecycle_state);
  const reason = reasonForLifecycle(record);
  const auditReferences = asStringArray(record.lifecycle_audit_references);

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
                {asString(record.detector_identifier)}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {asString(record.detector_lifecycle_id)}
              </Typography>
            </Stack>
            <Chip
              color={statusTone(lifecycleState)}
              label={lifecycleState}
              size="small"
              variant={statusTone(lifecycleState) === "default" ? "outlined" : "filled"}
            />
          </Stack>

          <StatusStrip
            values={[
              ["Source", asString(record.source_family)],
              ["Cadence", asString(record.review_cadence)],
              ["Next review", asString(record.next_review_at)],
            ]}
          />

          <ValueList
            entries={[
              ["Activation owner", asString(record.owner)],
              ["Expected volume", asString(record.expected_volume)],
              ["Expected signal posture", asString(record.expected_signal_posture)],
              ["False-positive review", asString(record.false_positive_review)],
              ["Disable owner", asString(record.disable_owner)],
              ["Rollback owner", asString(record.rollback_owner)],
              ["Next review", asString(record.next_review_at)],
              ["Catalog entry", asString(record.source_catalog_entry)],
              ["Reviewed audit references", auditReferences],
            ]}
          />

          {reason ? (
            <>
              <Divider />
              <Typography color="text.secondary" variant="body2">
                {reason}
              </Typography>
            </>
          ) : null}

          {sourceNativeState ? (
            <Alert severity="info" variant="outlined">
              {`Source-native ${sourceNativeState} status is subordinate display context only.`}
            </Alert>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function DetectorActivationReviewPage() {
  const detectorRecords = useOperatorList(
    "detectorActivationReview",
    DETECTOR_ACTIVATION_REVIEW_FILTER,
    DETECTOR_ACTIVATION_REVIEW_SORT,
    null,
  );

  if (detectorRecords.loading && detectorRecords.data === null) {
    return <LoadingState label="Loading detector activation review" />;
  }

  return (
    <PageFrame
      subtitle="Detector activation posture is rendered only from reviewed AegisOps detector lifecycle records. Browser state, UI cache, source-native detector status, and Wazuh state cannot approve activation, disablement, rollback, or reconciliation."
      title="Detector Activation Review"
    >
      {detectorRecords.error && detectorRecords.data === null ? (
        <ErrorState error={detectorRecords.error} />
      ) : (
        <Stack spacing={2}>
          <QueryStateNotice
            error={detectorRecords.error}
            refreshing={detectorRecords.refreshing}
          />
          <Alert severity="info" variant="outlined">
            Reviewed owners, expected volume, false-positive review, disable
            owner, rollback owner, next review, and overdue posture remain
            read-only operator visibility until the backend authoritative record
            chain is reread.
          </Alert>
          {detectorRecords.data && detectorRecords.data.length > 0 ? (
            <Grid container spacing={2}>
              {detectorRecords.data.map((record) => (
                <Grid key={asString(record.detector_lifecycle_id)} size={{ xs: 12, lg: 6 }}>
                  <DetectorLifecycleCard record={record} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <EmptyState message="No reviewed detector lifecycle records are available for activation review." />
          )}
        </Stack>
      )}
    </PageFrame>
  );
}
