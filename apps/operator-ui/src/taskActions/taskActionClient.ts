interface OperatorTaskActionClientConfig {
  fetchFn?: typeof fetch;
}

interface PromoteAlertToCasePayload {
  alert_id: string;
  case_id?: string;
  case_lifecycle_state?: string;
}

interface RecordCaseObservationPayload {
  case_id: string;
  author_identity: string;
  observed_at: string;
  scope_statement: string;
  supporting_evidence_ids: string[];
}

interface RecordCaseLeadPayload {
  case_id: string;
  triage_owner: string;
  triage_rationale: string;
  observation_id?: string;
}

interface RecordCaseRecommendationPayload {
  case_id: string;
  review_owner: string;
  intended_outcome: string;
  lead_id?: string;
}

interface CreateReviewedActionRequestPayload {
  action_type?: string;
  family: string;
  record_id: string;
  requester_identity: string;
  recipient_identity?: string;
  message_intent?: string;
  escalation_reason?: string;
  coordination_reference_id?: string;
  coordination_target_type?: string;
  ticket_title?: string;
  ticket_description?: string;
  ticket_severity?: string;
  expires_at: string;
  action_request_id?: string;
}

interface RecordActionApprovalDecisionPayload {
  action_request_id: string;
  approval_decision_id?: string;
  approver_identity: string;
  decided_at: string;
  decision: string;
  decision_rationale: string;
}

interface RecordActionReviewManualFallbackPayload {
  action_request_id: string;
  fallback_at: string;
  fallback_actor_identity: string;
  authority_boundary: string;
  reason: string;
  action_taken: string;
  verification_evidence_ids: string[];
  residual_uncertainty?: string;
}

interface RecordActionReviewEscalationNotePayload {
  action_request_id: string;
  escalated_at: string;
  escalated_by_identity: string;
  escalated_to: string;
  note: string;
}

interface OperatorTaskActionClient {
  createReviewedActionRequest(
    payload: CreateReviewedActionRequestPayload,
  ): Promise<unknown>;
  promoteAlertToCase(payload: PromoteAlertToCasePayload): Promise<unknown>;
  recordActionApprovalDecision(
    payload: RecordActionApprovalDecisionPayload,
  ): Promise<unknown>;
  recordActionReviewEscalationNote(
    payload: RecordActionReviewEscalationNotePayload,
  ): Promise<unknown>;
  recordActionReviewManualFallback(
    payload: RecordActionReviewManualFallbackPayload,
  ): Promise<unknown>;
  recordCaseLead(payload: RecordCaseLeadPayload): Promise<unknown>;
  recordCaseObservation(
    payload: RecordCaseObservationPayload,
  ): Promise<unknown>;
  recordCaseRecommendation(
    payload: RecordCaseRecommendationPayload,
  ): Promise<unknown>;
}

const JSON_HEADERS = {
  Accept: "application/json",
  "Content-Type": "application/json",
};

export class OperatorTaskActionError extends Error {
  code: string | null;
  details: unknown;
  status: number;

  constructor(message: string, options: { code?: string | null; details?: unknown; status: number }) {
    super(message);
    this.code = options.code ?? null;
    this.details = options.details;
    this.name = "OperatorTaskActionError";
    this.status = options.status;
  }
}

function asObject(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
}

function getErrorMessage(status: number, body: unknown, path: string) {
  const payload = asObject(body);
  const message = payload && typeof payload.message === "string" && payload.message.trim()
    ? payload.message.trim()
    : `Reviewed task action request failed with status ${status} for ${path}.`;
  return message;
}

async function parseJson(response: Response, path: string): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new OperatorTaskActionError(
      `Reviewed task action response for ${path} is not valid JSON.`,
      { status: response.status },
    );
  }
}

async function submitJson(
  fetchFn: typeof fetch,
  path: string,
  payload: unknown,
): Promise<unknown> {
  const response = await fetchFn(path, {
    body: JSON.stringify(payload),
    credentials: "include",
    headers: JSON_HEADERS,
    method: "POST",
  });
  const body = await parseJson(response, path);

  if (!response.ok) {
    const errorPayload = asObject(body);
    throw new OperatorTaskActionError(getErrorMessage(response.status, body, path), {
      code:
        errorPayload && typeof errorPayload.error === "string"
          ? errorPayload.error
          : null,
      details: body,
      status: response.status,
    });
  }

  return body;
}

export function createOperatorTaskActionClient({
  fetchFn = fetch,
}: OperatorTaskActionClientConfig = {}): OperatorTaskActionClient {
  return {
    createReviewedActionRequest(payload) {
      return submitJson(fetchFn, "/operator/create-reviewed-action-request", payload);
    },
    promoteAlertToCase(payload) {
      return submitJson(fetchFn, "/operator/promote-alert-to-case", payload);
    },
    recordActionApprovalDecision(payload) {
      return submitJson(fetchFn, "/operator/record-action-approval-decision", payload);
    },
    recordActionReviewEscalationNote(payload) {
      return submitJson(fetchFn, "/operator/record-action-review-escalation-note", payload);
    },
    recordActionReviewManualFallback(payload) {
      return submitJson(fetchFn, "/operator/record-action-review-manual-fallback", payload);
    },
    recordCaseLead(payload) {
      return submitJson(fetchFn, "/operator/record-case-lead", payload);
    },
    recordCaseObservation(payload) {
      return submitJson(fetchFn, "/operator/record-case-observation", payload);
    },
    recordCaseRecommendation(payload) {
      return submitJson(fetchFn, "/operator/record-case-recommendation", payload);
    },
  };
}

export type {
  CreateReviewedActionRequestPayload,
  OperatorTaskActionClient,
  PromoteAlertToCasePayload,
  RecordActionApprovalDecisionPayload,
  RecordActionReviewEscalationNotePayload,
  RecordActionReviewManualFallbackPayload,
  RecordCaseLeadPayload,
  RecordCaseObservationPayload,
  RecordCaseRecommendationPayload,
};
