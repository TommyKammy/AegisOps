import { MenuItem, Stack, TextField } from "@mui/material";
import { useState } from "react";
import {
  TaskActionFormCard,
  TaskActionSubmissionForm,
  useTaskActionSubmission,
} from "./taskActionPrimitives";

import { normalizeOptionalString, splitIdentifierList } from "./taskActionCardUtils";

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
    <TaskActionSubmissionForm
      onSubmitted={onSubmitted}
      refreshTargets={(acknowledgement) => [
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
      ]}
      run={(client) =>
        client.promoteAlertToCase({
          alert_id: alertId,
          case_id: normalizeOptionalString(caseIdOverride),
          case_lifecycle_state: caseLifecycleState,
        }) as Promise<{ case_id?: string }>
      }
      submission={submission}
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
    </TaskActionSubmissionForm>
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
        client.recordCaseObservation({
          author_identity: operatorIdentity,
          case_id: caseId,
          observed_at: observedAt.trim(),
          scope_statement: scopeStatement.trim(),
          supporting_evidence_ids: splitIdentifierList(supportingEvidenceIds),
        }) as Promise<{ case_id: string }>
      }
      submission={submission}
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
    </TaskActionSubmissionForm>
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
        client.recordCaseLead({
          case_id: caseId,
          observation_id: normalizeOptionalString(observationId),
          triage_owner: operatorIdentity,
          triage_rationale: triageRationale.trim(),
        }) as Promise<{ case_id: string }>
      }
      submission={submission}
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
    </TaskActionSubmissionForm>
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
        client.recordCaseRecommendation({
          case_id: caseId,
          intended_outcome: intendedOutcome.trim(),
          lead_id: normalizeOptionalString(leadId),
          review_owner: operatorIdentity,
        }) as Promise<{ case_id: string }>
      }
      submission={submission}
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
    </TaskActionSubmissionForm>
  );
}

export { CreateReviewedActionRequestCard } from "./actionRequestActionCards";
export {
  RecordActionApprovalDecisionCard,
  RecordActionReviewEscalationNoteCard,
  RecordActionReviewManualFallbackCard,
} from "./actionReviewActionCards";
