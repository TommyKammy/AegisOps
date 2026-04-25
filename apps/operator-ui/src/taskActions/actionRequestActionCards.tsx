import { MenuItem, Stack, TextField } from "@mui/material";
import { useState } from "react";
import {
  TaskActionFormCard,
  TaskActionSubmissionForm,
  useTaskActionSubmission,
} from "./taskActionPrimitives";

import { normalizeOptionalString } from "./taskActionCardUtils";

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
  const [actionType, setActionType] = useState("notify_identity_owner");
  const [recipientIdentity, setRecipientIdentity] = useState("");
  const [messageIntent, setMessageIntent] = useState("");
  const [escalationReason, setEscalationReason] = useState("");
  const [coordinationReferenceId, setCoordinationReferenceId] = useState("");
  const [coordinationTargetType, setCoordinationTargetType] = useState("zammad");
  const [ticketTitle, setTicketTitle] = useState("");
  const [ticketDescription, setTicketDescription] = useState("");
  const [ticketSeverity, setTicketSeverity] = useState("medium");
  const [expiresAt, setExpiresAt] = useState("");
  const [actionRequestIdOverride, setActionRequestIdOverride] = useState("");

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
        client.createReviewedActionRequest(
          actionType === "create_tracking_ticket"
            ? {
                action_request_id: normalizeOptionalString(actionRequestIdOverride),
                action_type: "create_tracking_ticket",
                coordination_reference_id: coordinationReferenceId.trim(),
                coordination_target_type: coordinationTargetType.trim(),
                expires_at: expiresAt.trim(),
                family: "recommendation",
                record_id: recommendationId.trim(),
                requester_identity: operatorIdentity,
                ticket_description: ticketDescription.trim(),
                ticket_severity: ticketSeverity.trim(),
                ticket_title: ticketTitle.trim(),
              }
            : {
                action_request_id: normalizeOptionalString(actionRequestIdOverride),
                escalation_reason: escalationReason.trim(),
                expires_at: expiresAt.trim(),
                family: "recommendation",
                message_intent: messageIntent.trim(),
                recipient_identity: recipientIdentity.trim(),
                record_id: recommendationId.trim(),
                requester_identity: operatorIdentity,
              },
        ) as Promise<{ action_request_id?: string; case_id?: string }>
      }
      submission={submission}
    >
      <TaskActionFormCard
        actor={[
          ["Identity", operatorIdentity],
          ["Action", "Reviewed action request"],
        ]}
        binding={[
          ["Record family", "recommendation"],
          ["Case id", caseId],
          [
            "Recommendation id",
            recommendationId.trim() || "Select authoritative recommendation id",
          ],
          ["Action type", actionType],
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
            label="Action type"
            onChange={(event) => {
              setActionType(event.target.value);
            }}
            select
            value={actionType}
          >
            <MenuItem value="notify_identity_owner">notify_identity_owner</MenuItem>
            <MenuItem value="create_tracking_ticket">create_tracking_ticket</MenuItem>
          </TextField>
          {actionType === "create_tracking_ticket" ? (
            <>
              <TextField
                fullWidth
                label="Coordination reference id"
                onChange={(event) => {
                  setCoordinationReferenceId(event.target.value);
                }}
                required
                value={coordinationReferenceId}
              />
              <TextField
                fullWidth
                label="Coordination target type"
                onChange={(event) => {
                  setCoordinationTargetType(event.target.value);
                }}
                select
                value={coordinationTargetType}
              >
                <MenuItem value="zammad">zammad</MenuItem>
                <MenuItem value="glpi">glpi</MenuItem>
              </TextField>
              <TextField
                fullWidth
                label="Ticket title"
                onChange={(event) => {
                  setTicketTitle(event.target.value);
                }}
                required
                value={ticketTitle}
              />
              <TextField
                fullWidth
                label="Ticket description"
                minRows={3}
                multiline
                onChange={(event) => {
                  setTicketDescription(event.target.value);
                }}
                required
                value={ticketDescription}
              />
              <TextField
                fullWidth
                label="Ticket severity"
                onChange={(event) => {
                  setTicketSeverity(event.target.value);
                }}
                select
                value={ticketSeverity}
              >
                <MenuItem value="low">low</MenuItem>
                <MenuItem value="medium">medium</MenuItem>
              </TextField>
            </>
          ) : (
            <>
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
            </>
          )}
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
    </TaskActionSubmissionForm>
  );
}
