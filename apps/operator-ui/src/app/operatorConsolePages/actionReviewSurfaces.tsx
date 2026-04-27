import { Alert, Link, Stack, Typography } from "@mui/material";
import { useOperatorUiEventLog } from "../operatorUiEvents";
import {
  asRecord,
  asRecordArray,
  asString,
  isAllowedExternalHref,
  statusTone,
  type UnknownRecord,
} from "./recordUtils";
import { SectionCard, StatusStrip, ValueList } from "./pageChrome";

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
  const reconciliationDetail = asRecord(actionReview?.reconciliation_detail);
  const receivedReceipt = asRecord(reconciliationDetail?.received_receipt);
  const closeoutEvidence = asRecord(reconciliationDetail?.closeout_evidence);
  const mismatchInspection = asRecord(actionReview?.mismatch_inspection);
  const reconciliationState = asString(actionReview?.reconciliation_state);
  const mismatchSummary = asString(mismatchInspection?.mismatch_summary);
  const closeoutSummary = asString(closeoutEvidence?.mismatch_summary);
  const actionRequired =
    reconciliationDetail?.action_required === true
      ? "yes"
      : reconciliationDetail?.action_required === false
        ? "no"
        : null;

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
            ["Action required", actionRequired],
            ["Next step", asString(reconciliationDetail?.next_step)],
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
            {closeoutSummary ??
              "No authoritative reconciliation record is visible for this reviewed request yet."}
          </Alert>
        ) : null}
        <ValueList
          entries={[
            ["Reconciliation id", asString(actionReview?.reconciliation_id)],
            [
              "Expected AegisOps state",
              asString(reconciliationDetail?.expected_aegisops_state),
            ],
            [
              "Authoritative AegisOps state",
              asString(reconciliationDetail?.authoritative_aegisops_state),
            ],
            ["Received receipt ingest", asString(receivedReceipt?.ingest_disposition)],
            ["Received receipt run", asString(receivedReceipt?.execution_run_id)],
            ["Closeout action required", actionRequired],
            ["Closeout next step", asString(reconciliationDetail?.next_step)],
            ["Closeout compared at", asString(closeoutEvidence?.compared_at)],
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
        <Alert severity="info" variant="outlined">
          External tickets remain non-authoritative coordination context for this case.
        </Alert>
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
