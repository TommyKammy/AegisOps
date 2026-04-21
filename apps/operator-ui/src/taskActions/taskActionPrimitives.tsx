import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import {
  createContext,
  type ReactNode,
  useContext,
  useMemo,
  useState,
} from "react";
import type { DataProvider, GetOneParams, GetOneResult } from "react-admin";
import { useDataProvider } from "react-admin";
import {
  type OperatorTaskActionClient,
  OperatorTaskActionError,
} from "./taskActionClient";

type TaskActionResource = "advisoryOutput" | "alerts" | "cases" | "reconciliations";

interface TaskActionClientProviderProps {
  children: ReactNode;
  client: OperatorTaskActionClient;
}

interface TaskActionContextValue {
  client: OperatorTaskActionClient;
}

interface TaskActionRefreshTarget {
  id: GetOneParams["id"];
  label: string;
  meta?: GetOneParams["meta"];
  resource: TaskActionResource;
}

interface TaskActionRefreshRecord {
  data: GetOneResult["data"];
  label: string;
  resource: TaskActionResource;
}

interface TaskActionSubmissionRequest<TAcknowledgement> {
  refreshTargets?:
    | TaskActionRefreshTarget[]
    | ((acknowledgement: TAcknowledgement) => TaskActionRefreshTarget[]);
  run(client: OperatorTaskActionClient): Promise<TAcknowledgement>;
}

interface TaskActionSubmissionState<TAcknowledgement> {
  acknowledgement: TAcknowledgement | null;
  error: Error | null;
  phase: "degraded" | "failed" | "idle" | "refreshing" | "submitting" | "success";
  refreshRecords: TaskActionRefreshRecord[];
}

interface TaskActionSubmissionController<TAcknowledgement> {
  reset(): void;
  state: TaskActionSubmissionState<TAcknowledgement>;
  submit(request: TaskActionSubmissionRequest<TAcknowledgement>): Promise<void>;
}

const TaskActionClientContext = createContext<TaskActionContextValue | null>(null);

function taskActionStatusMessage(error: Error | null) {
  if (error instanceof OperatorTaskActionError) {
    if (error.status === 401 || error.status === 403) {
      return "Reviewed backend authorization denied the task action.";
    }
    if (error.status === 409) {
      return "The reviewed backend rejected a stale or conflicting task action.";
    }
  }

  return error?.message ?? "The reviewed task action failed.";
}

async function rereadAuthoritativeTargets(
  dataProvider: DataProvider,
  refreshTargets: TaskActionRefreshTarget[],
): Promise<TaskActionRefreshRecord[]> {
  const results = await Promise.all(
    refreshTargets.map(async (target) => {
      const reread = await dataProvider.getOne(target.resource, {
        id: target.id,
        meta: target.meta,
      });
      return {
        data: reread.data,
        label: target.label,
        resource: target.resource,
      };
    }),
  );

  return results;
}

export function TaskActionClientProvider({
  children,
  client,
}: TaskActionClientProviderProps) {
  const value = useMemo(() => ({ client }), [client]);
  return (
    <TaskActionClientContext.Provider value={value}>
      {children}
    </TaskActionClientContext.Provider>
  );
}

export function useOperatorTaskActionClient() {
  const context = useContext(TaskActionClientContext);
  if (context === null) {
    throw new Error("Operator task-action client context is unavailable.");
  }

  return context.client;
}

export function useTaskActionSubmission<TAcknowledgement>(): TaskActionSubmissionController<TAcknowledgement> {
  const client = useOperatorTaskActionClient();
  const dataProvider = useDataProvider();
  const [state, setState] = useState<TaskActionSubmissionState<TAcknowledgement>>({
    acknowledgement: null,
    error: null,
    phase: "idle",
    refreshRecords: [],
  });

  return {
    reset() {
      setState({
        acknowledgement: null,
        error: null,
        phase: "idle",
        refreshRecords: [],
      });
    },
    state,
    async submit(request) {
      setState({
        acknowledgement: null,
        error: null,
        phase: "submitting",
        refreshRecords: [],
      });

      try {
        const acknowledgement = await request.run(client);
        const refreshTargets =
          typeof request.refreshTargets === "function"
            ? request.refreshTargets(acknowledgement)
            : (request.refreshTargets ?? []);

        if (refreshTargets.length === 0) {
          setState({
            acknowledgement,
            error: null,
            phase: "success",
            refreshRecords: [],
          });
          return;
        }

        setState({
          acknowledgement,
          error: null,
          phase: "refreshing",
          refreshRecords: [],
        });

        try {
          const refreshRecords = await rereadAuthoritativeTargets(
            dataProvider,
            refreshTargets,
          );
          setState({
            acknowledgement,
            error: null,
            phase: "success",
            refreshRecords,
          });
        } catch (error: unknown) {
          setState({
            acknowledgement,
            error:
              error instanceof Error
                ? error
                : new Error("Authoritative reread failed after task submit."),
            phase: "degraded",
            refreshRecords: [],
          });
        }
      } catch (error: unknown) {
        setState({
          acknowledgement: null,
          error:
            error instanceof Error
              ? error
              : new Error("Unknown task-action submit failure."),
          phase: "failed",
          refreshRecords: [],
        });
      }
    },
  };
}

function TaskActionStatusBanner<TAcknowledgement>({
  submission,
}: {
  submission: TaskActionSubmissionController<TAcknowledgement>;
}) {
  const { error, phase, refreshRecords } = submission.state;

  if (phase === "idle") {
    return null;
  }

  if (phase === "submitting" || phase === "refreshing") {
    return (
      <Alert
        icon={<CircularProgress aria-label="Submitting reviewed task action" size={18} />}
        severity="info"
        variant="outlined"
      >
        {phase === "submitting"
          ? "Submitting the reviewed task action."
          : "Re-reading authoritative backend state after submit."}
      </Alert>
    );
  }

  if (phase === "success") {
    return (
      <Alert severity="success" variant="outlined">
        Authoritative refresh completed from the reviewed backend record.
        {refreshRecords.length > 0 ? ` Refreshed: ${refreshRecords.map((record) => record.label).join(", ")}.` : ""}
      </Alert>
    );
  }

  if (phase === "degraded") {
    return (
      <Alert
        icon={<WarningAmberOutlinedIcon fontSize="inherit" />}
        severity="warning"
        variant="outlined"
      >
        Authoritative re-read did not complete after submit. Treat the result as unresolved until the reviewed record is refreshed. {taskActionStatusMessage(error)}
      </Alert>
    );
  }

  return (
    <Alert severity="error" variant="outlined">
      {taskActionStatusMessage(error)}
    </Alert>
  );
}

function MetadataList({
  entries,
  title,
}: {
  entries: Array<[string, string]>;
  title: string;
}) {
  return (
    <Stack spacing={1}>
      <Typography variant="subtitle2">{title}</Typography>
      <Stack divider={<Divider flexItem />} spacing={0}>
        {entries.map(([label, value]) => (
          <Stack
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            key={`${title}-${label}`}
            spacing={1}
            sx={{ py: 0.75 }}
          >
            <Typography color="text.secondary" variant="body2">
              {label}
            </Typography>
            <Typography sx={{ textAlign: { sm: "right" } }} variant="body2">
              {value}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}

export function TaskActionFormCard<TAcknowledgement>({
  actor,
  binding,
  children,
  confirmLabel = "I confirm this reviewed task action should be submitted.",
  provenance,
  submission,
  submitLabel,
  subtitle,
  title,
}: {
  actor: Array<[string, string]>;
  binding: Array<[string, string]>;
  children: ReactNode;
  confirmLabel?: string;
  provenance: Array<[string, string]>;
  submission: TaskActionSubmissionController<TAcknowledgement>;
  submitLabel: string;
  subtitle: string;
  title: string;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const busy =
    submission.state.phase === "submitting" ||
    submission.state.phase === "refreshing";

  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={3}>
          <Stack spacing={1}>
            <Typography variant="h6">{title}</Typography>
            <Typography color="text.secondary" variant="body2">
              {subtitle}
            </Typography>
          </Stack>

          <Divider />

          <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
            <Box flex={1}>
              <MetadataList entries={actor} title="Actor context" />
            </Box>
            <Box flex={1}>
              <MetadataList entries={binding} title="Authoritative binding" />
            </Box>
            <Box flex={1}>
              <MetadataList entries={provenance} title="Provenance context" />
            </Box>
          </Stack>

          <Divider />

          {children}

          <TaskActionStatusBanner submission={submission} />

          <Stack
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            spacing={2}
          >
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmed}
                  onChange={(event) => {
                    setConfirmed(event.target.checked);
                  }}
                />
              }
              label={confirmLabel}
            />
            <Button disabled={!confirmed || busy} type="submit" variant="contained">
              {busy ? "Working..." : submitLabel}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

export type {
  TaskActionRefreshRecord,
  TaskActionRefreshTarget,
  TaskActionSubmissionController,
  TaskActionSubmissionRequest,
  TaskActionSubmissionState,
};
