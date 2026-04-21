import { MenuItem, Stack, TextField } from "@mui/material";
import { useState } from "react";
import {
  TaskActionFormCard,
  useTaskActionSubmission,
} from "./taskActionPrimitives";

function normalizeOptionalString(value: string) {
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : undefined;
}

function splitIdentifierList(value: string) {
  return value
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

export function PromoteAlertToCaseCard({
  alertId,
  currentCaseId,
  onSubmitted,
  operatorIdentity,
}: {
  alertId: string;
  currentCaseId: string | null;
  onSubmitted?: () => void;
  operatorIdentity: string;
}) {
  const submission = useTaskActionSubmission<{ case_id?: string }>();
  const [caseIdOverride, setCaseIdOverride] = useState("");
  const [caseLifecycleState, setCaseLifecycleState] = useState("open");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: (acknowledgement) => [
            {
              id: alertId,
              label: "Alert detail",
              resource: "alerts",
            },
            ...(typeof acknowledgement.case_id === "string" && acknowledgement.case_id.trim()
              ? [
                  {
                    id: acknowledgement.case_id,
                    label: "Case detail",
                    resource: "cases" as const,
                  },
                ]
              : []),
          ],
          run: (client) =>
            client.promoteAlertToCase({
              alert_id: alertId,
              case_id: normalizeOptionalString(caseIdOverride),
              case_lifecycle_state: caseLifecycleState,
            }) as Promise<{ case_id?: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Alert promotion"],
        ]}
        binding={[
          ["Record family", "alert"],
          ["Alert id", alertId],
          ["Current case", currentCaseId ?? "No authoritative case anchor"],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator promote endpoint"],
          ["Refresh target", "alert detail and promoted case detail"],
        ]}
        submission={submission}
        submitLabel="Promote alert"
        subtitle="This bounded action promotes the reviewed alert into a case and re-reads backend-owned alert and case detail after submit."
        title="Promote alert into case"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Case id override"
            onChange={(event) => {
              setCaseIdOverride(event.target.value);
            }}
            value={caseIdOverride}
          />
          <TextField
            fullWidth
            label="Lifecycle state"
            onChange={(event) => {
              setCaseLifecycleState(event.target.value);
            }}
            select
            value={caseLifecycleState}
          >
            <MenuItem value="open">open</MenuItem>
            <MenuItem value="pending_action">pending_action</MenuItem>
          </TextField>
        </Stack>
      </TaskActionFormCard>
    </form>
  );
}

export function RecordCaseObservationCard({
  caseId,
  linkedEvidenceIds,
  onSubmitted,
  operatorIdentity,
}: {
  caseId: string;
  linkedEvidenceIds: string[];
  onSubmitted?: () => void;
  operatorIdentity: string;
}) {
  const submission = useTaskActionSubmission<{ case_id: string }>();
  const [observedAt, setObservedAt] = useState("");
  const [scopeStatement, setScopeStatement] = useState("");
  const [supportingEvidenceIds, setSupportingEvidenceIds] = useState(
    linkedEvidenceIds.join(", "),
  );

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordCaseObservation({
              author_identity: operatorIdentity,
              case_id: caseId,
              observed_at: observedAt.trim(),
              scope_statement: scopeStatement.trim(),
              supporting_evidence_ids: splitIdentifierList(supportingEvidenceIds),
            }) as Promise<{ case_id: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Case observation"],
        ]}
        binding={[
          ["Record family", "case"],
          ["Case id", caseId],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator observation endpoint"],
          ["Refresh target", "case detail"],
        ]}
        submission={submission}
        submitLabel="Record observation"
        subtitle="Record a reviewed case observation without dropping into a generic editor or bypassing backend-owned case state."
        title="Record case observation"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Observed at"
            onChange={(event) => {
              setObservedAt(event.target.value);
            }}
            required
            value={observedAt}
          />
          <TextField
            fullWidth
            label="Scope statement"
            minRows={3}
            multiline
            onChange={(event) => {
              setScopeStatement(event.target.value);
            }}
            required
            value={scopeStatement}
          />
          <TextField
            fullWidth
            label="Supporting evidence ids"
            onChange={(event) => {
              setSupportingEvidenceIds(event.target.value);
            }}
            value={supportingEvidenceIds}
          />
        </Stack>
      </TaskActionFormCard>
    </form>
  );
}

export function RecordCaseLeadCard({
  caseId,
  linkedObservationIds,
  onSubmitted,
  operatorIdentity,
}: {
  caseId: string;
  linkedObservationIds: string[];
  onSubmitted?: () => void;
  operatorIdentity: string;
}) {
  const submission = useTaskActionSubmission<{ case_id: string }>();
  const [observationId, setObservationId] = useState("");
  const [triageRationale, setTriageRationale] = useState("");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordCaseLead({
              case_id: caseId,
              observation_id: normalizeOptionalString(observationId),
              triage_owner: operatorIdentity,
              triage_rationale: triageRationale.trim(),
            }) as Promise<{ case_id: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Case lead"],
        ]}
        binding={[
          ["Record family", "case"],
          ["Case id", caseId],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator lead endpoint"],
          ["Refresh target", "case detail"],
        ]}
        submission={submission}
        submitLabel="Record lead"
        subtitle="Record the next reviewed lead for this case while keeping the authoritative case linkage and actor identity backend-owned."
        title="Record case lead"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            helperText={
              linkedObservationIds.length > 0
                ? `Known observation ids: ${linkedObservationIds.join(", ")}`
                : "No authoritative observation ids are currently linked."
            }
            label="Observation id"
            onChange={(event) => {
              setObservationId(event.target.value);
            }}
            value={observationId}
          />
          <TextField
            fullWidth
            label="Triage rationale"
            minRows={3}
            multiline
            onChange={(event) => {
              setTriageRationale(event.target.value);
            }}
            required
            value={triageRationale}
          />
        </Stack>
      </TaskActionFormCard>
    </form>
  );
}

export function RecordCaseRecommendationCard({
  caseId,
  linkedLeadIds,
  onSubmitted,
  operatorIdentity,
}: {
  caseId: string;
  linkedLeadIds: string[];
  onSubmitted?: () => void;
  operatorIdentity: string;
}) {
  const submission = useTaskActionSubmission<{ case_id: string }>();
  const [leadId, setLeadId] = useState("");
  const [intendedOutcome, setIntendedOutcome] = useState("");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordCaseRecommendation({
              case_id: caseId,
              intended_outcome: intendedOutcome.trim(),
              lead_id: normalizeOptionalString(leadId),
              review_owner: operatorIdentity,
            }) as Promise<{ case_id: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Case recommendation"],
        ]}
        binding={[
          ["Record family", "case"],
          ["Case id", caseId],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator recommendation endpoint"],
          ["Refresh target", "case detail"],
        ]}
        submission={submission}
        submitLabel="Record recommendation"
        subtitle="Record the reviewed recommendation outcome without widening the workflow into approvals, execution control, or reconciliation mutation."
        title="Record case recommendation"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            helperText={
              linkedLeadIds.length > 0
                ? `Known lead ids: ${linkedLeadIds.join(", ")}`
                : "No authoritative lead ids are currently linked."
            }
            label="Lead id"
            onChange={(event) => {
              setLeadId(event.target.value);
            }}
            value={leadId}
          />
          <TextField
            fullWidth
            label="Intended outcome"
            minRows={3}
            multiline
            onChange={(event) => {
              setIntendedOutcome(event.target.value);
            }}
            required
            value={intendedOutcome}
          />
        </Stack>
      </TaskActionFormCard>
    </form>
  );
}

export function CreateReviewedActionRequestCard({
  caseId,
  linkedRecommendationIds,
  onSubmitted,
  operatorIdentity,
}: {
  caseId: string;
  linkedRecommendationIds: string[];
  onSubmitted?: () => void;
  operatorIdentity: string;
}) {
  const submission = useTaskActionSubmission<{ action_request_id?: string; case_id?: string }>();
  const [recommendationId, setRecommendationId] = useState(
    linkedRecommendationIds.length === 1 ? linkedRecommendationIds[0] ?? "" : "",
  );
  const [recipientIdentity, setRecipientIdentity] = useState("");
  const [messageIntent, setMessageIntent] = useState("");
  const [escalationReason, setEscalationReason] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [actionRequestIdOverride, setActionRequestIdOverride] = useState("");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.createReviewedActionRequest({
              action_request_id: normalizeOptionalString(actionRequestIdOverride),
              escalation_reason: escalationReason.trim(),
              expires_at: expiresAt.trim(),
              family: "recommendation",
              message_intent: messageIntent.trim(),
              recipient_identity: recipientIdentity.trim(),
              record_id: recommendationId.trim(),
              requester_identity: operatorIdentity,
            }) as Promise<{ action_request_id?: string; case_id?: string }>,
        });
      }}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Reviewed action request"],
        ]}
        binding={[
          ["Record family", "recommendation"],
          ["Case id", caseId],
          ["Recommendation id", recommendationId.trim() || "Select authoritative recommendation id"],
        ]}
        provenance={[
          ["Backend boundary", "reviewed operator action-request endpoint"],
          ["Refresh target", "case detail"],
        ]}
        submission={submission}
        submitLabel="Create action request"
        subtitle="Create a reviewed action request from an authoritative recommendation anchor without exposing approval or execution controls."
        title="Create reviewed action request"
      >
        <Stack spacing={2}>
          <TextField
            fullWidth
            helperText={
              linkedRecommendationIds.length > 0
                ? `Known recommendation ids: ${linkedRecommendationIds.join(", ")}`
                : "No authoritative recommendation ids are currently linked."
            }
            label="Recommendation id"
            onChange={(event) => {
              setRecommendationId(event.target.value);
            }}
            required
            value={recommendationId}
          />
          <TextField
            fullWidth
            label="Recipient identity"
            onChange={(event) => {
              setRecipientIdentity(event.target.value);
            }}
            required
            value={recipientIdentity}
          />
          <TextField
            fullWidth
            label="Message intent"
            minRows={3}
            multiline
            onChange={(event) => {
              setMessageIntent(event.target.value);
            }}
            required
            value={messageIntent}
          />
          <TextField
            fullWidth
            label="Escalation reason"
            minRows={3}
            multiline
            onChange={(event) => {
              setEscalationReason(event.target.value);
            }}
            required
            value={escalationReason}
          />
          <TextField
            fullWidth
            label="Expires at"
            onChange={(event) => {
              setExpiresAt(event.target.value);
            }}
            required
            value={expiresAt}
          />
          <TextField
            fullWidth
            label="Action request id override"
            onChange={(event) => {
              setActionRequestIdOverride(event.target.value);
            }}
            value={actionRequestIdOverride}
          />
        </Stack>
      </TaskActionFormCard>
    </form>
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
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordActionReviewManualFallback({
              action_request_id: actionRequestId,
              action_taken: actionTaken.trim(),
              authority_boundary: authorityBoundary,
              fallback_actor_identity: operatorIdentity,
              fallback_at: fallbackAt.trim(),
              reason: reason.trim(),
              residual_uncertainty: normalizeOptionalString(residualUncertainty),
              verification_evidence_ids: splitIdentifierList(verificationEvidenceIds),
            }) as Promise<{ action_request_id: string }>,
        });
      }}
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
    </form>
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
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted: () => onSubmitted?.(),
          refreshTargets: [
            {
              id: caseId,
              label: "Case detail",
              resource: "cases",
            },
          ],
          run: (client) =>
            client.recordActionReviewEscalationNote({
              action_request_id: actionRequestId,
              escalated_at: escalatedAt.trim(),
              escalated_by_identity: operatorIdentity,
              escalated_to: escalatedTo.trim(),
              note: note.trim(),
            }) as Promise<{ action_request_id: string }>,
        });
      }}
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
    </form>
  );
}
