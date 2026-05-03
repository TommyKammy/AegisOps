import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import PauseCircleOutlineIcon from "@mui/icons-material/PauseCircleOutline";
import ReportProblemOutlinedIcon from "@mui/icons-material/ReportProblemOutlined";
import { Alert, Chip, Stack, Typography } from "@mui/material";
import { useMemo } from "react";
import { OperatorDataProviderContractError } from "../../dataProvider";
import {
  asString,
  formatLabel,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  SectionCard,
  useOperatorList,
  type UnknownRecord,
} from "./shared";

type ChecklistState =
  | "completed"
  | "skipped"
  | "degraded"
  | "blocked"
  | "unavailable";

interface ChecklistStepContract {
  key: string;
  title: string;
  backendAnchor: string;
  expectedRecordFamily: string;
}

interface ChecklistStepView extends ChecklistStepContract {
  authorityRecordFamily: string;
  authorityRecordId: string;
  state: ChecklistState;
}

const TRUSTED_AUTHORITY_SOURCE = "backend_authoritative_record";

const CHECKLIST_STEPS: ChecklistStepContract[] = [
  {
    key: "stack_health",
    title: "Stack health",
    backendAnchor: "Reviewed diagnostics/readiness record",
    expectedRecordFamily: "runtime_readiness",
  },
  {
    key: "seeded_queue",
    title: "Seeded queue",
    backendAnchor: "Demo-only queue record admitted by AegisOps",
    expectedRecordFamily: "queue",
  },
  {
    key: "sample_wazuh_alert",
    title: "Sample Wazuh-origin alert",
    backendAnchor: "AegisOps alert record with Wazuh provenance",
    expectedRecordFamily: "alert",
  },
  {
    key: "promote_to_case",
    title: "Promote to case",
    backendAnchor: "AegisOps case lifecycle record",
    expectedRecordFamily: "case",
  },
  {
    key: "evidence",
    title: "Evidence",
    backendAnchor: "Case-bound evidence record",
    expectedRecordFamily: "evidence",
  },
  {
    key: "ai_summary",
    title: "AI summary",
    backendAnchor: "Assistant advisory output anchored to the workflow record",
    expectedRecordFamily: "assistant_advisory",
  },
  {
    key: "action_request",
    title: "Action request",
    backendAnchor: "Reviewed action request record",
    expectedRecordFamily: "action_request",
  },
  {
    key: "approval_decision",
    title: "Approval or rejection",
    backendAnchor: "Action review decision record",
    expectedRecordFamily: "action_review",
  },
  {
    key: "shuffle_receipt",
    title: "Shuffle execution receipt",
    backendAnchor: "Execution receipt linked to the approved request",
    expectedRecordFamily: "execution_receipt",
  },
  {
    key: "reconciliation",
    title: "Reconciliation",
    backendAnchor: "AegisOps reconciliation record",
    expectedRecordFamily: "reconciliation",
  },
  {
    key: "report_export",
    title: "Report export",
    backendAnchor: "Report export artifact derived from authoritative records",
    expectedRecordFamily: "report_export",
  },
];

const ALLOWED_STATES = new Set<ChecklistState>([
  "completed",
  "skipped",
  "degraded",
  "blocked",
  "unavailable",
]);

function checklistStateIcon(state: ChecklistState) {
  switch (state) {
    case "completed":
      return <CheckCircleOutlineIcon fontSize="small" />;
    case "skipped":
      return <PauseCircleOutlineIcon fontSize="small" />;
    case "degraded":
      return <ReportProblemOutlinedIcon fontSize="small" />;
    case "blocked":
      return <ErrorOutlineIcon fontSize="small" />;
    case "unavailable":
      return <InfoOutlinedIcon fontSize="small" />;
  }
}

function checklistStateColor(
  state: ChecklistState,
): "default" | "error" | "info" | "success" | "warning" {
  switch (state) {
    case "completed":
      return "success";
    case "skipped":
    case "unavailable":
      return "default";
    case "degraded":
      return "warning";
    case "blocked":
      return "error";
  }
}

function readChecklistState(record: UnknownRecord): ChecklistState {
  const state = asString(record.state);
  if (!ALLOWED_STATES.has(state as ChecklistState)) {
    throw new OperatorDataProviderContractError(
      `Checklist state ${state ?? "missing"} is not part of the reviewed contract.`,
    );
  }

  return state as ChecklistState;
}

function buildChecklistRows(records: UnknownRecord[]): ChecklistStepView[] {
  const contractByKey = new Map(CHECKLIST_STEPS.map((step) => [step.key, step]));
  const recordsByKey = new Map<string, UnknownRecord>();

  for (const record of records) {
    const stepKey = asString(record.step_key);
    if (stepKey === null || !contractByKey.has(stepKey)) {
      throw new OperatorDataProviderContractError(
        "First-login checklist payload includes an unsupported step.",
      );
    }

    if (recordsByKey.has(stepKey)) {
      throw new OperatorDataProviderContractError(
        `First-login checklist payload includes duplicate step ${stepKey}.`,
      );
    }

    recordsByKey.set(stepKey, record);
  }

  return CHECKLIST_STEPS.map((step) => {
    const record = recordsByKey.get(step.key);
    if (!record) {
      return {
        ...step,
        authorityRecordFamily: step.expectedRecordFamily,
        authorityRecordId: "Not available",
        state: "unavailable",
      };
    }

    const authoritySource = asString(record.authority_source);
    if (authoritySource !== TRUSTED_AUTHORITY_SOURCE) {
      throw new OperatorDataProviderContractError(
        `Checklist state from ${authoritySource ?? "missing_authority_source"} is not trusted workflow truth.`,
      );
    }

    const authorityRecordFamily = asString(record.authority_record_family);
    const authorityRecordId = asString(record.authority_record_id);
    if (authorityRecordFamily === null || authorityRecordId === null) {
      throw new OperatorDataProviderContractError(
        `Checklist step ${step.key} is missing its backend authority record binding.`,
      );
    }
    if (authorityRecordFamily !== step.expectedRecordFamily) {
      throw new OperatorDataProviderContractError(
        `Checklist step ${step.key} is bound to ${authorityRecordFamily}, expected ${step.expectedRecordFamily}.`,
      );
    }

    return {
      ...step,
      authorityRecordFamily,
      authorityRecordId,
      state: readChecklistState(record),
    };
  });
}

export function FirstLoginChecklistPage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "step_key",
      order: "ASC" as const,
    }),
    [],
  );
  const { data, error, loading, refreshing } = useOperatorList(
    "firstLoginChecklist",
    filter,
    sort,
    CHECKLIST_STEPS.length,
  );

  let checklistRows: ChecklistStepView[] | null = null;
  let contractError: Error | null = null;
  if (data) {
    try {
      checklistRows = buildChecklistRows(data as UnknownRecord[]);
    } catch (error) {
      contractError = error instanceof Error ? error : new Error(String(error));
    }
  }

  return (
    <PageFrame
      subtitle="This first-login checklist guides the Phase 55 first-user path while keeping browser progress subordinate to backend-owned workflow records."
      title="First-Login Checklist"
    >
      {loading && !data ? (
        <LoadingState label="Loading first-login checklist" />
      ) : null}
      {error && !data ? (
        <Alert severity="error" variant="outlined">
          {error.message}
        </Alert>
      ) : null}
      {contractError ? (
        <Alert severity="error" variant="outlined">
          {contractError.message}
        </Alert>
      ) : null}
      {checklistRows ? (
        <Stack spacing={3}>
          <QueryStateNotice error={error} refreshing={refreshing} />
          <Alert severity="info" variant="outlined">
            Checklist progress is derived from backend records only; browser
            state, UI cache, Wazuh state, Shuffle state, AI output, tickets,
            verifier output, and issue-lint output remain subordinate context.
          </Alert>
          <SectionCard
            subtitle="Skipped, degraded, blocked, and unavailable states remain distinct and never count as successful completion."
            title="Guided workflow contract"
          >
            <Stack
              aria-label="Phase 55 first-login checklist"
              component="ol"
              spacing={2}
              sx={{ m: 0, pl: 0 }}
            >
              {checklistRows.map((step, index) => (
                <Stack
                  component="li"
                  key={step.key}
                  spacing={1}
                  sx={{
                    borderBottom:
                      index === checklistRows.length - 1
                        ? "none"
                        : "1px solid",
                    borderColor: "divider",
                    display: "block",
                    listStyle: "none",
                    pb: index === checklistRows.length - 1 ? 0 : 2,
                  }}
                >
                  <Stack
                    alignItems={{ xs: "flex-start", sm: "center" }}
                    direction={{ xs: "column", sm: "row" }}
                    justifyContent="space-between"
                    spacing={1}
                  >
                    <Typography data-testid="step-title" variant="subtitle1">
                      {step.title}
                    </Typography>
                    <Chip
                      color={checklistStateColor(step.state)}
                      icon={checklistStateIcon(step.state)}
                      label={`State: ${step.state}`}
                      size="small"
                      variant={
                        checklistStateColor(step.state) === "default"
                          ? "outlined"
                          : "filled"
                      }
                    />
                  </Stack>
                  <Typography color="text.secondary" variant="body2">
                    Backend anchor: {step.backendAnchor}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Authority record: {formatLabel(step.authorityRecordFamily)}{" "}
                    {step.authorityRecordId}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </SectionCard>
        </Stack>
      ) : null}
    </PageFrame>
  );
}
