import { MenuItem, Stack, TextField } from "@mui/material";
import { useState } from "react";
import {
  TaskActionFormCard,
  TaskActionSubmissionForm,
  useTaskActionSubmission,
} from "./taskActionPrimitives";

import { normalizeOptionalString, splitIdentifierList } from "./taskActionCardUtils";

export function RecordActionApprovalDecisionCard({
  actionRequestId,
  actionRequestState,
  approvalState,
  approverIdentity,
  decisionRationale,
  expiresAt,
  onSubmitted,
}: {
  actionRequestId: string;
  actionRequestState: string | null;
  approvalState: string | null;
  approverIdentity: string;
  decisionRationale: string | null;
  expiresAt: string | null;
  onSubmitted?: () => void;
}) {
  const submission = useTaskActionSubmission<{ action_request_id: string }>();
  const [decidedAt, setDecidedAt] = useState("");
  const [decision, setDecision] = useState("grant");
  const [approvalDecisionIdOverride, setApprovalDecisionIdOverride] = useState("");
  const [nextDecisionRationale, setNextDecisionRationale] = useState(
    decisionRationale ?? "",
  );

  return (
    <TaskActionSubmissionForm
      onSubmitted={onSubmitted}
      refreshTargets={[
        {
          id: actionRequestId,
          label: "Action review detail",
          resource: "actionReview",
        },
      ]}
      run={(client) =>
        client.recordActionApprovalDecision({
          action_request_id: actionRequestId,
          approval_decision_id: normalizeOptionalString(approvalDecisionIdOverride),
          approver_identity: approverIdentity,
          decided_at: decidedAt.trim(),
          decision,
          decision_rationale: nextDecisionRationale.trim(),
        }) as Promise<{ action_request_id: string }>
      }
      submission={submission}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", approverIdentity],
          ["Action", "Approval decision"],
        ]}
        binding={[
          ["Record family", "action_request"],
          ["Action request id", actionRequestId],
          ["Lifecycle", actionRequestState ?? "Not available"],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator approval-decision endpoint"],
          ["Current approval state", approvalState ?? "Not available"],
          ["Approval window", expiresAt ?? "Not available"],
        ]}
        submission={submission}
        submitLabel="Record approval decision"
        subtitle="Record one reviewed approval decision against the authoritative action request. This surface stays decision-oriented and requires an authoritative reread before the lifecycle is treated as durable."
        title="Record approval decision"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Decided at"
            onChange={(event) => {
              setDecidedAt(event.target.value);
            }}
            required
            value={decidedAt}
          />
          <TextField
            fullWidth
            label="Decision"
            onChange={(event) => {
              setDecision(event.target.value);
            }}
            select
            value={decision}
          >
            <MenuItem value="grant">grant</MenuItem>
            <MenuItem value="reject">reject</MenuItem>
          </TextField>
          <TextField
            fullWidth
            label="Decision rationale"
            minRows={3}
            multiline
            onChange={(event) => {
              setNextDecisionRationale(event.target.value);
            }}
            required
            value={nextDecisionRationale}
          />
          <TextField
            fullWidth
            label="Approval decision id override"
            onChange={(event) => {
              setApprovalDecisionIdOverride(event.target.value);
            }}
            value={approvalDecisionIdOverride}
          />
        </Stack>
      </TaskActionFormCard>
    </TaskActionSubmissionForm>
  );
}

export function RecordActionReviewManualFallbackCard({
  actionRequestId,
  caseId,
  linkedEvidenceIds,
  nextExpectedAction,
  onSubmitted,
  operatorIdentity,
  reviewState,
}: {
  actionRequestId: string;
  caseId: string;
  linkedEvidenceIds: string[];
  nextExpectedAction: string | null;
  onSubmitted?: () => void;
  operatorIdentity: string;
  reviewState: string | null;
}) {
  const submission = useTaskActionSubmission<{ action_request_id: string }>();
  const [fallbackAt, setFallbackAt] = useState("");
  const [authorityBoundary, setAuthorityBoundary] = useState("approved_human_fallback");
  const [reason, setReason] = useState("");
  const [actionTaken, setActionTaken] = useState("");
  const [verificationEvidenceIds, setVerificationEvidenceIds] = useState(
    linkedEvidenceIds.join(", "),
  );
  const [residualUncertainty, setResidualUncertainty] = useState("");

  return (
    <TaskActionSubmissionForm
      onSubmitted={onSubmitted}
      refreshTargets={[
        {
          id: caseId,
          label: "Case detail",
          resource: "cases",
        },
      ]}
      run={(client) =>
        client.recordActionReviewManualFallback({
          action_request_id: actionRequestId,
          action_taken: actionTaken.trim(),
          authority_boundary: authorityBoundary,
          fallback_actor_identity: operatorIdentity,
          fallback_at: fallbackAt.trim(),
          reason: reason.trim(),
          residual_uncertainty: normalizeOptionalString(residualUncertainty),
          verification_evidence_ids: splitIdentifierList(verificationEvidenceIds),
        }) as Promise<{ action_request_id: string }>
      }
      submission={submission}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Manual fallback note"],
        ]}
        binding={[
          ["Record family", "action_request"],
          ["Case id", caseId],
          ["Action request id", actionRequestId],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator manual-fallback endpoint"],
          ["Current review state", reviewState ?? "Not available"],
          ["Next expected action", nextExpectedAction ?? "Not available"],
        ]}
        submission={submission}
        submitLabel="Record manual fallback"
        subtitle="Record a reviewed manual fallback against the authoritative action request without widening the UI into execution ownership or generic coordination editing."
        title="Record manual fallback"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Fallback at"
            onChange={(event) => {
              setFallbackAt(event.target.value);
            }}
            required
            value={fallbackAt}
          />
          <TextField
            fullWidth
            label="Authority boundary"
            onChange={(event) => {
              setAuthorityBoundary(event.target.value);
            }}
            select
            value={authorityBoundary}
          >
            <MenuItem value="approved_human_fallback">approved_human_fallback</MenuItem>
          </TextField>
          <TextField
            fullWidth
            label="Reason"
            minRows={3}
            multiline
            onChange={(event) => {
              setReason(event.target.value);
            }}
            required
            value={reason}
          />
          <TextField
            fullWidth
            label="Action taken"
            minRows={3}
            multiline
            onChange={(event) => {
              setActionTaken(event.target.value);
            }}
            required
            value={actionTaken}
          />
          <TextField
            fullWidth
            helperText={
              linkedEvidenceIds.length > 0
                ? `Known evidence ids: ${linkedEvidenceIds.join(", ")}`
                : "No authoritative evidence ids are currently linked."
            }
            label="Verification evidence ids"
            onChange={(event) => {
              setVerificationEvidenceIds(event.target.value);
            }}
            value={verificationEvidenceIds}
          />
          <TextField
            fullWidth
            label="Residual uncertainty"
            minRows={2}
            multiline
            onChange={(event) => {
              setResidualUncertainty(event.target.value);
            }}
            value={residualUncertainty}
          />
        </Stack>
      </TaskActionFormCard>
    </TaskActionSubmissionForm>
  );
}

export function RecordActionReviewEscalationNoteCard({
  actionRequestId,
  caseId,
  nextExpectedAction,
  onSubmitted,
  operatorIdentity,
  reviewState,
}: {
  actionRequestId: string;
  caseId: string;
  nextExpectedAction: string | null;
  onSubmitted?: () => void;
  operatorIdentity: string;
  reviewState: string | null;
}) {
  const submission = useTaskActionSubmission<{ action_request_id: string }>();
  const [escalatedAt, setEscalatedAt] = useState("");
  const [escalatedTo, setEscalatedTo] = useState("");
  const [note, setNote] = useState("");

  return (
    <TaskActionSubmissionForm
      onSubmitted={onSubmitted}
      refreshTargets={[
        {
          id: caseId,
          label: "Case detail",
          resource: "cases",
        },
      ]}
      run={(client) =>
        client.recordActionReviewEscalationNote({
          action_request_id: actionRequestId,
          escalated_at: escalatedAt.trim(),
          escalated_by_identity: operatorIdentity,
          escalated_to: escalatedTo.trim(),
          note: note.trim(),
        }) as Promise<{ action_request_id: string }>
      }
      submission={submission}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Escalation note"],
        ]}
        binding={[
          ["Record family", "action_request"],
          ["Case id", caseId],
          ["Action request id", actionRequestId],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator escalation-note endpoint"],
          ["Current review state", reviewState ?? "Not available"],
          ["Next expected action", nextExpectedAction ?? "Not available"],
        ]}
        submission={submission}
        submitLabel="Record escalation note"
        subtitle="Record a reviewed escalation note on the authoritative action request while keeping approval decisions and execution controls outside this slice."
        title="Record escalation note"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Escalated at"
            onChange={(event) => {
              setEscalatedAt(event.target.value);
            }}
            required
            value={escalatedAt}
          />
          <TextField
            fullWidth
            label="Escalated to"
            onChange={(event) => {
              setEscalatedTo(event.target.value);
            }}
            required
            value={escalatedTo}
          />
          <TextField
            fullWidth
            label="Note"
            minRows={3}
            multiline
            onChange={(event) => {
              setNote(event.target.value);
            }}
            required
            value={note}
          />
        </Stack>
      </TaskActionFormCard>
    </TaskActionSubmissionForm>
  );
}
