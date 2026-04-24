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

type TaskActionResource =
  | "actionReview"
  | "advisoryOutput"
  | "alerts"
  | "cases"
  | "reconciliations";

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
  onSubmitted?(acknowledgement: TAcknowledgement): void;
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

interface TaskActionSubmissionFormProps<TAcknowledgement>
  extends TaskActionSubmissionRequest<TAcknowledgement> {
  children: ReactNode;
  submission: TaskActionSubmissionController<TAcknowledgement>;
}

const TaskActionClientContext = createContext<TaskActionContextValue | null>(null);

export function taskActionStatusMessage(error: Error | null) {
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
          request.onSubmitted?.(acknowledgement);
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
          request.onSubmitted?.(acknowledgement);
          setState({
            acknowledgement,
            error: null,
            phase: "success",
            refreshRecords,
          });
        } catch (error: unknown) {
          request.onSubmitted?.(acknowledgement);
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

export function TaskActionSubmissionForm<TAcknowledgement>({
  children,
  onSubmitted,
  refreshTargets,
  run,
  submission,
}: TaskActionSubmissionFormProps<TAcknowledgement>) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submission.submit({
          onSubmitted,
          refreshTargets,
          run,
        });
      }}
    >
      {children}
    </form>
  );
}

export type {
  TaskActionRefreshRecord,
  TaskActionRefreshTarget,
  TaskActionSubmissionController,
  TaskActionSubmissionRequest,
  TaskActionSubmissionState,
};
