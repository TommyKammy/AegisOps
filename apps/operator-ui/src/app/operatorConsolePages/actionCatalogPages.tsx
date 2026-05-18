import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { Link as ReactRouterLink } from "react-router-dom";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  StatusStrip,
  ValueList,
  asRecord,
  asString,
  formatValue,
  getPath,
  statusTone,
  useOperatorList,
  type UnknownRecord,
} from "./shared";

const ACTION_CATALOG_FILTER = {};
const ACTION_CATALOG_SORT = {
  field: "requested_at",
  order: "DESC",
} as const;

const REVIEWED_ACTION_CATALOG = [
  {
    catalogAction: "enrichment_only_lookup",
    family: "Read",
    policy: "policy_not_required",
    receipt: "AegisOps execution receipt with lookup evidence reference",
    reconciliation: "Subordinate lookup context only",
  },
  {
    catalogAction: "operator_notification",
    family: "Notify",
    policy: "policy_not_required",
    receipt: "AegisOps execution receipt with normalized delivery reference",
    reconciliation: "Notification attempted, delivered, failed, or fallback-needed",
  },
  {
    catalogAction: "manual_escalation_request",
    family: "Notify",
    policy: "human_required_for_protected_follow_up",
    receipt: "AegisOps execution receipt with escalation owner and fallback flag",
    reconciliation: "Manual escalation requested; no automatic approval or closure",
  },
  {
    catalogAction: "create_tracking_ticket",
    family: "Soft Write",
    policy: "human_required",
    receipt: "AegisOps execution receipt with non-authoritative ticket pointer",
    reconciliation: "Ticket coordination context cannot become workflow truth",
  },
] as const;

const ACTION_TYPE_ALIASES: Record<string, string> = {
  notify_identity_owner: "operator_notification",
};

function recordCatalogAction(record: UnknownRecord): string | null {
  const direct =
    asString(record.catalog_action) ??
    asString(getPath(record, "policy_basis.catalog_action")) ??
    asString(getPath(record, "policy_evaluation.catalog_action")) ??
    asString(getPath(record, "requested_payload.catalog_action")) ??
    asString(record.action_type) ??
    asString(getPath(record, "requested_payload.action_type"));

  return direct ? (ACTION_TYPE_ALIASES[direct] ?? direct) : null;
}

function latestRecordByCatalogAction(records: UnknownRecord[] | null) {
  const latest = new Map<string, UnknownRecord>();
  for (const record of records ?? []) {
    const catalogAction = recordCatalogAction(record);
    if (catalogAction !== null && !latest.has(catalogAction)) {
      latest.set(catalogAction, record);
    }
  }
  return latest;
}

function policyPosture(record: UnknownRecord | null, fallback: string) {
  return (
    asString(record?.approval_requirement) ??
    asString(getPath(record, "policy_evaluation.approval_requirement")) ??
    asString(getPath(record, "policy_evaluation.approval_requirement_override")) ??
    asString(getPath(record, "policy_basis.approval_requirement")) ??
    fallback
  );
}

function requestState(record: UnknownRecord | null) {
  return (
    asString(record?.action_request_state) ??
    asString(record?.lifecycle_state) ??
    "unavailable"
  );
}

function approvalState(record: UnknownRecord | null) {
  return (
    asString(record?.approval_state) ??
    asString(getPath(record, "approval.lifecycle_state")) ??
    asString(record?.approval_decision_state) ??
    (record ? "not_attached" : "unavailable")
  );
}

function receiptState(record: UnknownRecord | null) {
  if (record === null) {
    return "unavailable";
  }
  return (
    asString(record.receipt_state) ??
    asString(record.action_execution_state) ??
    asString(getPath(record, "shuffle_receipt.status")) ??
    (asString(record.action_execution_id) ? "present" : "missing_receipt")
  );
}

function reconciliationState(record: UnknownRecord | null) {
  if (record === null) {
    return "unavailable";
  }
  return (
    asString(record.reconciliation_state) ??
    asString(getPath(record, "reconciliation.lifecycle_state")) ??
    (asString(record.reconciliation_id) ? "present" : "missing_reconciliation")
  );
}

function fallbackState(record: UnknownRecord | null) {
  if (record === null) {
    return "unavailable";
  }
  return (
    asString(record.fallback_state) ??
    asString(record.manual_fallback_state) ??
    asString(getPath(record, "fallback.fallback_state")) ??
    "not_recorded"
  );
}

function mismatchPosture(record: UnknownRecord | null) {
  if (record === null) {
    return "automation_unavailable";
  }

  const candidates = [
    asString(record.mismatch_state),
    asString(record.mismatch_posture),
    asString(getPath(record, "mismatch_inspection.lifecycle_state")),
    receiptState(record),
    reconciliationState(record),
    fallbackState(record),
  ].filter((value): value is string => value !== null);
  const degraded = candidates.find((value) =>
    /(failed|failure|fallback|missing|mismatch|rejected|stale|unavailable)/i.test(value),
  );

  return degraded ?? "none";
}

function simulatorPosture(record: UnknownRecord | null) {
  const simulator = asRecord(record?.simulator_output);
  return (
    asString(record?.demo_test_label) ??
    asString(record?.simulation_mode) ??
    asString(simulator?.demo_test_label) ??
    asString(simulator?.production_exclusion) ??
    "production_record_only"
  );
}

function ActionCatalogEntryCard({
  definition,
  record,
}: {
  definition: (typeof REVIEWED_ACTION_CATALOG)[number];
  record: UnknownRecord | null;
}) {
  const request = requestState(record);
  const approval = approvalState(record);
  const receipt = receiptState(record);
  const reconciliation = reconciliationState(record);
  const fallback = fallbackState(record);
  const mismatch = mismatchPosture(record);
  const simulator = simulatorPosture(record);
  const actionRequestId = asString(record?.action_request_id);

  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider", height: "100%" }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack
            alignItems={{ xs: "flex-start", sm: "center" }}
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            spacing={1}
          >
            <Stack spacing={0.5}>
              <Typography fontWeight={700}>{definition.catalogAction}</Typography>
              <Typography color="text.secondary" variant="body2">
                {definition.family}
              </Typography>
            </Stack>
            <Chip
              color={statusTone(request)}
              label={request}
              size="small"
              variant={statusTone(request) === "default" ? "outlined" : "filled"}
            />
          </Stack>

          <StatusStrip
            values={[
              ["Policy", policyPosture(record, definition.policy)],
              ["Request", request],
              ["Approval", approval],
              ["Execution", asString(record?.action_execution_state)],
              ["Receipt", receipt],
              ["Reconciliation", reconciliation],
              ["Fallback", fallback],
              ["Mismatch", mismatch],
              ["Simulator", simulator],
            ]}
          />

          {record === null ? (
            <Alert severity="warning" variant="outlined">
              No backend-reviewed action request is currently visible for this catalog entry.
            </Alert>
          ) : null}
          {mismatch !== "none" ? (
            <Alert severity="warning" variant="outlined">
              Failure, fallback, missing receipt, stale receipt, mismatched receipt, or unavailable automation posture remains review-visible and cannot be normalized into success by the UI.
            </Alert>
          ) : null}
          {simulator !== "production_record_only" && simulator !== "production" ? (
            <Alert severity="info" variant="outlined">
              Simulator/demo output is subordinate context only; backend AegisOps records remain authoritative.
            </Alert>
          ) : null}

          <ValueList
            entries={[
              ["Action request id", actionRequestId],
              ["Reviewed receipt expectation", definition.receipt],
              ["Reconciliation expectation", definition.reconciliation],
              ["Requested at", asString(record?.requested_at)],
              ["Expires at", asString(record?.expires_at)],
              ["Execution surface", asString(record?.execution_surface_id)],
              ["Action execution id", asString(record?.action_execution_id)],
              ["Reconciliation id", asString(record?.reconciliation_id)],
            ]}
          />

          {actionRequestId ? (
            <Button
              component={ReactRouterLink}
              size="small"
              to={`/operator/action-review/${actionRequestId}`}
              variant="outlined"
            >
              Open action review
            </Button>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function ActionCatalogPage() {
  const actionRecords = useOperatorList(
    "actionCatalog",
    ACTION_CATALOG_FILTER,
    ACTION_CATALOG_SORT,
    null,
  );
  const latest = latestRecordByCatalogAction(actionRecords.data);

  if (actionRecords.loading && actionRecords.data === null) {
    return <LoadingState label="Loading action catalog" />;
  }

  return (
    <PageFrame
      subtitle="Reviewed Read, Notify, and Soft Write actions are visible here as a thin browser surface over AegisOps-owned request, approval, receipt, fallback, and reconciliation records."
      title="Action Catalog"
    >
      {actionRecords.error && actionRecords.data === null ? (
        <ErrorState error={actionRecords.error} />
      ) : (
        <Stack spacing={2}>
          <QueryStateNotice
            error={actionRecords.error}
            refreshing={actionRecords.refreshing}
          />
          <Alert severity="info" variant="outlined">
            UI cache, browser state, simulator output, downstream ticket state, and automation substrate status are subordinate context only; backend AegisOps records remain authoritative.
          </Alert>
          {actionRecords.data && actionRecords.data.length === 0 ? (
            <EmptyState message="No action requests are currently visible; the reviewed catalog remains bounded to default Phase 62 actions." />
          ) : null}
          <Grid container spacing={2}>
            {REVIEWED_ACTION_CATALOG.map((definition) => (
              <Grid key={definition.catalogAction} size={{ xs: 12, lg: 6 }}>
                <ActionCatalogEntryCard
                  definition={definition}
                  record={latest.get(definition.catalogAction) ?? null}
                />
              </Grid>
            ))}
          </Grid>
          <Typography color="text.secondary" variant="body2">
            Controlled Write and Hard Write actions are not default requestable controls in this reviewed catalog.
            Current visible records: {formatValue(actionRecords.data?.length ?? 0)}.
          </Typography>
        </Stack>
      )}
    </PageFrame>
  );
}
