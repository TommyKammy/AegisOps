import { Alert, Stack, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { RecordActionApprovalDecisionCard } from "../../taskActions/caseworkActionCards";
import {
  approvalLifecycleExplanation,
  approvalLifecycleSeverity,
  asRecord,
  asRecordArray,
  asString,
  asStringArray,
  AuditedRouteButton,
  canRecordActionApprovalDecision,
  CoordinationVisibilitySection,
  EmptyState,
  ErrorState,
  ExecutionReceiptSection,
  formatValue,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  ReconciliationVisibilitySection,
  SectionCard,
  StatusStrip,
  useOperatorRecord,
  ValueList,
} from "./shared";

function ActionReviewPageBody({
  actionRequestId,
  operatorIdentity,
  operatorRoles,
}: {
  actionRequestId: string;
  operatorIdentity: string;
  operatorRoles: readonly string[];
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord(
    "actionReview",
    actionRequestId,
    recordMeta,
  );

  if (loading && !data) {
    return <LoadingState label="Loading action review detail" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Action review detail is unavailable." />;
  }

  const actionReview = asRecord(data.action_review);
  const currentActionReview = asRecord(data.current_action_review);
  const caseRecord = asRecord(data.case_record);
  const alertRecord = asRecord(data.alert_record);
  const timelineEntries = asRecordArray(actionReview?.timeline);
  const selectedActionRequestId = asString(actionReview?.action_request_id);
  const currentActionRequestId = asString(currentActionReview?.action_request_id);
  const actionRequestState = asString(actionReview?.action_request_state);
  const approvalState = asString(actionReview?.approval_state);
  const approvalDecisionId = asString(actionReview?.approval_decision_id);
  const reconciliationId = asString(actionReview?.reconciliation_id);
  const decisionRationale = asString(actionReview?.decision_rationale);
  const approverIdentities = asStringArray(actionReview?.approver_identities);
  const recommendationId = asString(actionReview?.recommendation_id);
  const isCurrentAuthoritativeReview =
    selectedActionRequestId !== null &&
    currentActionRequestId !== null &&
    currentActionRequestId === selectedActionRequestId;
  const canRecordApproval =
    canRecordActionApprovalDecision(operatorRoles) &&
    isCurrentAuthoritativeReview &&
    actionRequestState === "pending_approval" &&
    approvalState === "pending";

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="This page stays anchored to one authoritative action-review record. Browser-local routing does not redefine the active review."
        title="Action request detail"
      >
        <StatusStrip
          values={[
            ["Review", asString(actionReview?.review_state)],
            ["Approval", asString(actionReview?.approval_state)],
            ["Execution", asString(actionReview?.action_execution_state)],
            ["Reconciliation", asString(actionReview?.reconciliation_state)],
          ]}
        />
        {currentActionRequestId && currentActionRequestId !== selectedActionRequestId ? (
          <Alert severity="warning" variant="outlined">
            The requested record is no longer the current authoritative review for this scope.
            Current review: {currentActionRequestId}.
          </Alert>
        ) : null}
        <ValueList
          entries={[
            ["Action request id", selectedActionRequestId ?? actionRequestId],
            ["Current authoritative review", currentActionRequestId],
            ["Action request lifecycle", actionRequestState],
            ["Approval decision id", asString(actionReview?.approval_decision_id)],
            ["Requester", asString(actionReview?.requester_identity)],
            ["Recipient", asString(actionReview?.recipient_identity)],
            ["Recommendation id", asString(actionReview?.recommendation_id)],
            ["Requested at", asString(actionReview?.requested_at)],
            ["Expires at", asString(actionReview?.expires_at)],
            ["Next expected action", asString(actionReview?.next_expected_action)],
            ["Execution surface", asString(actionReview?.execution_surface_id)],
            ["Execution surface type", asString(actionReview?.execution_surface_type)],
            ["Message intent", asString(actionReview?.message_intent)],
            ["Escalation reason", asString(actionReview?.escalation_reason)],
          ]}
        />
        <Stack direction="row" gap={1}>
          {caseRecord?.case_id ? (
            <AuditedRouteButton
              label="Open case detail"
              to={`/operator/cases/${String(caseRecord.case_id)}`}
            >
              Open case detail
            </AuditedRouteButton>
          ) : null}
          {recommendationId ? (
            <AuditedRouteButton
              label="Open recommendation advisory"
              to={`/operator/assistant/recommendation/${recommendationId}`}
            >
              Open recommendation advisory
            </AuditedRouteButton>
          ) : null}
          {approvalDecisionId ? (
            <AuditedRouteButton
              label="Open approval advisory"
              to={`/operator/assistant/approval_decision/${approvalDecisionId}`}
            >
              Open approval advisory
            </AuditedRouteButton>
          ) : null}
          {reconciliationId ? (
            <AuditedRouteButton
              label="Open reconciliation advisory"
              to={`/operator/assistant/reconciliation/${reconciliationId}`}
            >
              Open reconciliation advisory
            </AuditedRouteButton>
          ) : null}
          {alertRecord?.alert_id ? (
            <AuditedRouteButton
              label="Open alert detail"
              to={`/operator/alerts/${String(alertRecord.alert_id)}`}
            >
              Open alert detail
            </AuditedRouteButton>
          ) : null}
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Approval is rendered as authoritative lifecycle state with explicit actor, rationale, and expiry instead of as a generic mutable field."
        title="Approval lifecycle"
      >
        <Stack spacing={2}>
          <Alert severity={approvalLifecycleSeverity(approvalState)} variant="outlined">
            {approvalLifecycleExplanation(approvalState)}
          </Alert>
          <ValueList
            entries={[
              ["Approval lifecycle", approvalState],
              ["Approver identities", approverIdentities],
              ["Decision rationale", decisionRationale],
              ["Approval binding expires at", asString(actionReview?.expires_at)],
              ["Next expected action", asString(actionReview?.next_expected_action)],
            ]}
          />
          {!canRecordActionApprovalDecision(operatorRoles) ? (
            <Alert severity="info" variant="outlined">
              The current reviewed session can inspect this record but cannot submit approval decisions without approver role authority.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) && !isCurrentAuthoritativeReview ? (
            <Alert severity="warning" variant="outlined">
              Approval submission stays blocked because this record is no longer the current authoritative review for the selected scope.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) &&
          isCurrentAuthoritativeReview &&
          actionRequestState !== "pending_approval" ? (
            <Alert severity="info" variant="outlined">
              Approval submission is only available while the authoritative action-request lifecycle is <strong>pending_approval</strong>.
            </Alert>
          ) : null}
          {canRecordActionApprovalDecision(operatorRoles) &&
          isCurrentAuthoritativeReview &&
          actionRequestState === "pending_approval" &&
          approvalState !== "pending" ? (
            <Alert severity="info" variant="outlined">
              Approval submission is only available while the authoritative approval lifecycle is <strong>pending</strong>.
            </Alert>
          ) : null}
        </Stack>
      </SectionCard>

      <ExecutionReceiptSection actionReview={actionReview} />
      <ReconciliationVisibilitySection actionReview={actionReview} />
      <CoordinationVisibilitySection actionReview={actionReview} />

      <SectionCard
        subtitle="Authoritative linkage stays explicit so later approval, execution, and reconciliation panels can extend this view without inferring broader workflow truth."
        title="Authoritative linkage"
      >
        <ValueList
          entries={[
            ["Case id", caseRecord?.case_id],
            ["Case lifecycle", caseRecord?.lifecycle_state],
            ["Alert id", alertRecord?.alert_id],
            ["Alert lifecycle", alertRecord?.lifecycle_state],
            ["Target scope", actionReview?.target_scope],
            ["Requested payload", actionReview?.requested_payload],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="Lifecycle-bearing review history remains visible without collapsing request, approval, execution, and reconciliation into one convenience badge."
        title="Review timeline"
      >
        {timelineEntries.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Stage</TableCell>
                <TableCell>State</TableCell>
                <TableCell>At</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timelineEntries.map((entry, index) => (
                <TableRow key={`${String(entry.label ?? entry.state ?? index)}-${index}`}>
                  <TableCell>{formatValue(entry.label)}</TableCell>
                  <TableCell>{formatValue(entry.state)}</TableCell>
                  <TableCell>{formatValue(entry.at)}</TableCell>
                  <TableCell>{formatValue(entry.details)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No action review timeline entries were returned." />
        )}
      </SectionCard>

      {canRecordApproval && selectedActionRequestId ? (
        <RecordActionApprovalDecisionCard
          actionRequestId={selectedActionRequestId}
          actionRequestState={actionRequestState}
          approvalState={approvalState}
          approverIdentity={operatorIdentity}
          decisionRationale={decisionRationale}
          expiresAt={asString(actionReview?.expires_at)}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
        />
      ) : null}
    </Stack>
  );
}

export function ActionReviewPage({
  operatorIdentity,
  operatorRoles,
}: {
  operatorIdentity: string;
  operatorRoles: readonly string[];
}) {
  const params = useParams();
  const actionRequestId = asString(params.actionRequestId);

  return (
    <PageFrame
      subtitle="Read-only action-review inspection keeps authoritative request detail, active-review selection, and lifecycle history visible without widening the browser into workflow authority."
      title="Action Review"
    >
      {actionRequestId ? (
        <ActionReviewPageBody
          actionRequestId={actionRequestId}
          operatorIdentity={operatorIdentity}
          operatorRoles={operatorRoles}
        />
      ) : (
        <SectionCard
          subtitle="Open action review from a case or alert detail page so the shell stays anchored to one authoritative action-request record."
          title="Select an action review"
        >
          <EmptyState message="No action request is selected yet." />
        </SectionCard>
      )}
    </PageFrame>
  );
}
