import {
  Suspense,
  lazy,
  useEffect,
  useEffectEvent,
  useState,
  type ComponentType,
} from "react";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import BuildCircleOutlinedIcon from "@mui/icons-material/BuildCircleOutlined";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import HealthAndSafetyOutlinedIcon from "@mui/icons-material/HealthAndSafetyOutlined";
import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import HandshakeOutlinedIcon from "@mui/icons-material/HandshakeOutlined";
import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import PlaylistAddCheckOutlinedIcon from "@mui/icons-material/PlaylistAddCheckOutlined";
import RuleFolderOutlinedIcon from "@mui/icons-material/RuleFolderOutlined";
import SensorsOutlinedIcon from "@mui/icons-material/SensorsOutlined";
import TodayOutlinedIcon from "@mui/icons-material/TodayOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import type { AuthProvider, DataProvider } from "react-admin";
import {
  AdminContext,
  AppBar,
  Layout,
  Logout,
  Menu,
  TitlePortal,
  useDataProvider,
} from "react-admin";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { operatorTheme } from "./theme";
import {
  OptionalExtensionVisibilityPanel,
  buildOptionalExtensionDefinitionsFromPayload,
} from "./optionalExtensionVisibility";
import {
  OperatorUiEventLogPanel,
  OperatorUiEventLogProvider,
  type OperatorUiEventLogObserver,
  useOperatorUiEventLog,
} from "./operatorUiEvents";
import { TaskActionClientProvider } from "../taskActions/taskActionPrimitives";
import type { OperatorTaskActionClient } from "../taskActions/taskActionClient";
import { anyRoleHasSurfaceAccess } from "../auth/roleMatrix";
import type { SessionStore } from "../auth/session";

const loadOperatorConsolePages = () => import("./operatorConsolePages");

function lazyOperatorConsolePage<T extends keyof Awaited<ReturnType<typeof loadOperatorConsolePages>>>(
  exportName: T,
) {
  return lazy(async () => {
    const module = await loadOperatorConsolePages();

    return {
      default: module[exportName] as ComponentType<any>,
    };
  });
}

const ActionReviewPage =
  lazyOperatorConsolePage("ActionReviewPage") as unknown as typeof import("./operatorConsolePages").ActionReviewPage;
const AssistantAdvisoryPage =
  lazyOperatorConsolePage("AssistantAdvisoryPage") as unknown as typeof import("./operatorConsolePages").AssistantAdvisoryPage;
const AlertDetailPage =
  lazyOperatorConsolePage("AlertDetailPage") as unknown as typeof import("./operatorConsolePages").AlertDetailPage;
const AlertIndexPage =
  lazyOperatorConsolePage("AlertIndexPage") as unknown as typeof import("./operatorConsolePages").AlertIndexPage;
const CaseDetailPage =
  lazyOperatorConsolePage("CaseDetailPage") as unknown as typeof import("./operatorConsolePages").CaseDetailPage;
const CaseIndexPage =
  lazyOperatorConsolePage("CaseIndexPage") as unknown as typeof import("./operatorConsolePages").CaseIndexPage;
const FirstLoginChecklistPage =
  lazyOperatorConsolePage("FirstLoginChecklistPage") as unknown as typeof import("./operatorConsolePages").FirstLoginChecklistPage;
const ProvenancePage =
  lazyOperatorConsolePage("ProvenancePage") as unknown as typeof import("./operatorConsolePages").ProvenancePage;
const ProvenanceIndexPage =
  lazyOperatorConsolePage("ProvenanceIndexPage") as unknown as typeof import("./operatorConsolePages").ProvenanceIndexPage;
const QueuePage =
  lazyOperatorConsolePage("QueuePage") as unknown as typeof import("./operatorConsolePages").QueuePage;
const ReadinessPage =
  lazyOperatorConsolePage("ReadinessPage") as unknown as typeof import("./operatorConsolePages").ReadinessPage;
const ReconciliationPage =
  lazyOperatorConsolePage("ReconciliationPage") as unknown as typeof import("./operatorConsolePages").ReconciliationPage;
const TodayPage =
  lazyOperatorConsolePage("TodayPage") as unknown as typeof import("./operatorConsolePages").TodayPage;
const BusinessHoursHandoffPage =
  lazyOperatorConsolePage("BusinessHoursHandoffPage") as unknown as typeof import("./operatorConsolePages").BusinessHoursHandoffPage;
const UserRoleAdminPage =
  lazyOperatorConsolePage("UserRoleAdminPage") as unknown as typeof import("./operatorConsolePages").UserRoleAdminPage;

function hasReviewedOperatorRole(
  operatorRoles: readonly string[],
  allowedRoles: readonly string[] = operatorRoles,
) {
  const normalizedAllowedRoles = new Set(
    allowedRoles.map((role) => role.trim().toLowerCase()),
  );

  return operatorRoles.some((role) =>
    normalizedAllowedRoles.has(role.toLowerCase()),
  );
}

function canBrowseActionReview(operatorRoles: readonly string[]) {
  return (
    anyRoleHasSurfaceAccess(
      operatorRoles,
      "actionApprovalDecision",
      "allowed",
    ) ||
    anyRoleHasSurfaceAccess(
      operatorRoles,
      "platformAdministration",
      "admin_only",
    )
  );
}

function canInspectActionReviewDetail(operatorRoles: readonly string[]) {
  return hasReviewedOperatorRole(operatorRoles);
}

function canViewAdmin(operatorRoles: readonly string[]) {
  return anyRoleHasSurfaceAccess(
    operatorRoles,
    "platformAdministration",
    "admin_only",
  );
}

function buildOperatorShellPath(basePath: string, path = "") {
  if (!path) {
    return basePath;
  }

  return `${basePath}/${path}`;
}

function OperatorAppBar() {
  return (
    <AppBar userMenu={false}>
      <TitlePortal />
      <Typography sx={{ flex: 1 }} variant="h6">
        AegisOps Operator Console
      </Typography>
      <Logout />
    </AppBar>
  );
}

function OperatorMenu({
  basePath,
  operatorRoles,
}: {
  basePath: string;
  operatorRoles: readonly string[];
}) {
  const showActionReview = canBrowseActionReview(operatorRoles);
  const showAdmin = canViewAdmin(operatorRoles);

  return (
    <Menu>
      <Menu.DashboardItem primaryText="Overview" />
      <Menu.Item
        leftIcon={<TodayOutlinedIcon />}
        primaryText="Today"
        to={buildOperatorShellPath(basePath, "today")}
      />
      <Menu.Item
        leftIcon={<InboxOutlinedIcon />}
        primaryText="Queue"
        to={buildOperatorShellPath(basePath, "queue")}
      />
      <Menu.Item
        leftIcon={<InsightsOutlinedIcon />}
        primaryText="Cases"
        to={buildOperatorShellPath(basePath, "cases")}
      />
      {showActionReview ? (
        <Menu.Item
          leftIcon={<GavelOutlinedIcon />}
          primaryText="Actions"
          to={buildOperatorShellPath(basePath, "actions")}
        />
      ) : null}
      <Menu.Item
        leftIcon={<SensorsOutlinedIcon />}
        primaryText="Sources"
        to={buildOperatorShellPath(basePath, "sources")}
      />
      {showActionReview ? (
        <Menu.Item
          leftIcon={<BuildCircleOutlinedIcon />}
          primaryText="Automations"
          to={buildOperatorShellPath(basePath, "automations")}
        />
      ) : null}
      <Menu.Item
        leftIcon={<AssessmentOutlinedIcon />}
        primaryText="Reports"
        to={buildOperatorShellPath(basePath, "reports")}
      />
      {showAdmin ? (
        <Menu.Item
          leftIcon={<AdminPanelSettingsOutlinedIcon />}
          primaryText="Admin"
          to={buildOperatorShellPath(basePath, "admin")}
        />
      ) : null}
      <Menu.Item
        leftIcon={<HealthAndSafetyOutlinedIcon />}
        primaryText="Health"
        to={buildOperatorShellPath(basePath, "health")}
      />
      <Menu.Item
        leftIcon={<HandshakeOutlinedIcon />}
        primaryText="Handoff"
        to={buildOperatorShellPath(basePath, "handoff")}
      />
      <Menu.Item
        leftIcon={<WarningAmberOutlinedIcon />}
        primaryText="Alerts"
        to={buildOperatorShellPath(basePath, "alerts")}
      />
      <Menu.Item
        leftIcon={<LinkOutlinedIcon />}
        primaryText="Provenance"
        to={buildOperatorShellPath(basePath, "provenance/alerts")}
      />
      <Menu.Item
        leftIcon={<CheckCircleOutlineIcon />}
        primaryText="Readiness"
        to={buildOperatorShellPath(basePath, "readiness")}
      />
      <Menu.Item
        leftIcon={<PlaylistAddCheckOutlinedIcon />}
        primaryText="First Login"
        to={buildOperatorShellPath(basePath, "first-login-checklist")}
      />
      <Menu.Item
        leftIcon={<RuleFolderOutlinedIcon />}
        primaryText="Reconciliation"
        to={buildOperatorShellPath(basePath, "reconciliation")}
      />
      <Menu.Item
        leftIcon={<AutoAwesomeOutlinedIcon />}
        primaryText="Assistant"
        to={buildOperatorShellPath(basePath, "assistant")}
      />
      {showActionReview ? (
        <Menu.Item
          leftIcon={<GavelOutlinedIcon />}
          primaryText="Action Review"
          to={buildOperatorShellPath(basePath, "action-review")}
        />
      ) : null}
    </Menu>
  );
}

function OverviewPage({
  operatorRoles,
}: {
  operatorRoles: readonly string[];
}) {
  const dataProvider = useDataProvider();
  const [optionalExtensionDefinitions, setOptionalExtensionDefinitions] = useState(() =>
    buildOptionalExtensionDefinitionsFromPayload(null),
  );

  useEffect(() => {
    let active = true;

    void dataProvider
      .getList("runtimeReadiness", {
        filter: {},
        pagination: {
          page: 1,
          perPage: 1,
        },
        sort: {
          field: "status",
          order: "ASC",
        },
      })
      .then((result) => {
        if (!active) {
          return;
        }

        setOptionalExtensionDefinitions(
          buildOptionalExtensionDefinitionsFromPayload(
            result.data[0]?.metrics?.optional_extensions,
          ),
        );
      })
      .catch(() => {
        if (!active) {
          return;
        }

        setOptionalExtensionDefinitions(buildOptionalExtensionDefinitionsFromPayload(null));
      });

    return () => {
      active = false;
    };
  }, [dataProvider]);

  const sections = [
    {
      title: "Queue",
      chip: "Primary surface",
      description:
        "Queue triage stays inside AegisOps as the authoritative review selection surface.",
    },
    {
      title: "Alerts",
      chip: "Read-only",
      description:
        "Alert inspection stays anchored to backend-authoritative alert and provenance records.",
    },
    {
      title: "Cases",
      chip: "Read-only",
      description:
        "Case detail pages will remain task-oriented instead of generic CRUD resources.",
    },
    {
      title: "Assistant",
      chip: "Advisory only",
      description:
        "Assistant advisory stays subordinate to authoritative AegisOps records and remains read-oriented in the reviewed shell.",
    },
    ...(canBrowseActionReview(operatorRoles)
      ? [
          {
            title: "Action review",
            chip: "Guarded",
            description:
              "Action review surfaces remain separate from execution authority and stay read-oriented here.",
          },
        ]
      : []),
  ];

  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h4">
          Protected operator shell
        </Typography>
        <Typography color="text.secondary" variant="body1">
          This React-Admin workspace is the reviewed browser entrypoint for
          later read-only operator pages. Backend session and claim checks stay
          authoritative.
        </Typography>
      </Stack>

      <Grid container spacing={2}>
        {sections.map((section) => (
          <Grid key={section.title} size={{ xs: 12, md: 6 }}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Stack spacing={1.5}>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    spacing={2}
                  >
                    <Typography variant="h6">{section.title}</Typography>
                    <Chip label={section.chip} size="small" />
                  </Stack>
                  <Typography color="text.secondary" variant="body2">
                    {section.description}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <OptionalExtensionVisibilityPanel definitions={optionalExtensionDefinitions} />
    </Stack>
  );
}

function UnsupportedOperatorRoutePage() {
  return (
    <Stack spacing={2} sx={{ p: 3 }}>
      <Typography component="h1" variant="h4">
        Unsupported operator route
      </Typography>
      <Typography color="text.secondary" variant="body1">
        The requested path is not part of the reviewed operator shell.
      </Typography>
      <Typography variant="body2">
        Use the queue, authoritative detail links, reviewed diagnostics, or
        other approved operator entrypoints instead of guessing route shape.
      </Typography>
    </Stack>
  );
}

function DeferredPageFallback() {
  return (
    <Stack
      spacing={2}
      sx={{
        minHeight: 280,
        justifyContent: "center",
        p: 3,
      }}
    >
      <CircularProgress aria-label="Loading reviewed operator surface" />
      <Typography color="text.secondary" variant="body2">
        Loading the reviewed operator surface while the shell preserves the
        backend-authenticated boundary.
      </Typography>
    </Stack>
  );
}

function AdminPolicyRoute({
  basePath,
  sessionStore,
}: {
  basePath: string;
  sessionStore: SessionStore;
}) {
  const [status, setStatus] = useState<"loading" | "authorized" | "forbidden">(
    "loading",
  );

  useEffect(() => {
    let active = true;

    void sessionStore
      .getSession({ force: true })
      .then((session) => {
        if (!active) {
          return;
        }

        setStatus(canViewAdmin(session.roles) ? "authorized" : "forbidden");
      })
      .catch(() => {
        if (active) {
          setStatus("forbidden");
        }
      });

    return () => {
      active = false;
    };
  }, [sessionStore]);

  if (status === "loading") {
    return <DeferredPageFallback />;
  }

  if (status === "forbidden") {
    return <Navigate replace to={buildOperatorShellPath(basePath, "forbidden")} />;
  }

  return <UserRoleAdminPage />;
}

function OperatorShellContent({
  basePath,
  canInspectActionReview,
  canViewAdmin,
  canViewActionReview,
  operatorIdentity,
  operatorRoles,
  sessionStore,
}: {
  basePath: string;
  canInspectActionReview: boolean;
  canViewAdmin: boolean;
  canViewActionReview: boolean;
  operatorIdentity: string;
  operatorRoles: string[];
  sessionStore: SessionStore;
}) {
  const location = useLocation();
  const { recordRouteView } = useOperatorUiEventLog();
  const recordRouteViewEffect = useEffectEvent((route: string) => {
    recordRouteView(route);
  });

  useEffect(() => {
    recordRouteViewEffect(
      `${location.pathname}${location.search}${location.hash}`,
    );
  }, [
    location.hash,
    location.pathname,
    location.search,
    recordRouteViewEffect,
  ]);

  return (
    <Stack spacing={3} sx={{ pb: 3 }}>
      <Suspense fallback={<DeferredPageFallback />}>
        <Routes>
          <Route element={<OverviewPage operatorRoles={operatorRoles} />} index />
          <Route element={<TodayPage />} path="today" />
          <Route element={<BusinessHoursHandoffPage />} path="handoff" />
          <Route element={<QueuePage />} path="queue" />
          <Route element={<AlertIndexPage />} path="alerts" />
          <Route
            element={<AlertDetailPage operatorIdentity={operatorIdentity} />}
            path="alerts/:alertId"
          />
          <Route element={<CaseIndexPage />} path="cases" />
          <Route
            element={<CaseDetailPage operatorIdentity={operatorIdentity} />}
            path="cases/:caseId"
          />
          <Route element={<ProvenanceIndexPage />} path="provenance" />
          <Route element={<ProvenanceIndexPage />} path="provenance/:family" />
          <Route element={<ProvenancePage />} path="provenance/:family/:recordId" />
          <Route element={<ReadinessPage />} path="readiness" />
          <Route element={<ReadinessPage />} path="health" />
          <Route element={<ReadinessPage />} path="sources" />
          <Route
            element={
              canViewActionReview ? (
                <ReadinessPage />
              ) : (
                <Navigate
                  replace
                  to={buildOperatorShellPath(basePath, "forbidden")}
                />
              )
            }
            path="automations"
          />
          <Route
            element={<FirstLoginChecklistPage />}
            path="first-login-checklist"
          />
          <Route element={<ReconciliationPage />} path="reconciliation" />
          <Route element={<ReconciliationPage />} path="reports" />
          <Route
            element={
              canViewAdmin ? (
                <AdminPolicyRoute
                  basePath={basePath}
                  sessionStore={sessionStore}
                />
              ) : (
                <Navigate
                  replace
                  to={buildOperatorShellPath(basePath, "forbidden")}
                />
              )
            }
            path="admin"
          />
          <Route element={<AssistantAdvisoryPage />} path="assistant" />
          <Route
            element={<AssistantAdvisoryPage />}
            path="assistant/:recordFamily/:recordId"
          />
          <Route
            element={
              canViewActionReview ? (
                <ActionReviewPage
                  operatorIdentity={operatorIdentity}
                  operatorRoles={operatorRoles}
                />
              ) : (
                <Navigate
                  replace
                  to={buildOperatorShellPath(basePath, "forbidden")}
                />
              )
            }
            path="action-review"
          />
          <Route
            element={
              canViewActionReview ? (
                <ActionReviewPage
                  operatorIdentity={operatorIdentity}
                  operatorRoles={operatorRoles}
                />
              ) : (
                <Navigate
                  replace
                  to={buildOperatorShellPath(basePath, "forbidden")}
                />
              )
            }
            path="actions"
          />
          <Route
            element={
              canInspectActionReview ? (
                <ActionReviewPage
                  operatorIdentity={operatorIdentity}
                  operatorRoles={operatorRoles}
                />
              ) : (
                <Navigate
                  replace
                  to={buildOperatorShellPath(basePath, "forbidden")}
                />
              )
            }
            path="action-review/:actionRequestId"
          />
          <Route element={<UnsupportedOperatorRoutePage />} path="*" />
        </Routes>
      </Suspense>
      <Stack sx={{ px: { xs: 2, md: 3 } }}>
        <OperatorUiEventLogPanel />
      </Stack>
    </Stack>
  );
}

export function OperatorShell({
  authProvider,
  basePath,
  dataProvider,
  operatorIdentity,
  operatorRoles,
  onEventLogEntriesChange,
  sessionStore,
  taskActionClient,
}: {
  authProvider: AuthProvider;
  basePath: string;
  dataProvider: DataProvider;
  onEventLogEntriesChange?: OperatorUiEventLogObserver;
  operatorIdentity: string;
  operatorRoles: string[];
  sessionStore: SessionStore;
  taskActionClient: OperatorTaskActionClient;
}) {
  const canViewActionReview = canBrowseActionReview(operatorRoles);
  const canInspectActionReview = canInspectActionReviewDetail(operatorRoles);
  const canViewAdminSurface = canViewAdmin(operatorRoles);

  return (
    <AdminContext
      authProvider={authProvider}
      dataProvider={dataProvider}
      theme={operatorTheme}
    >
      <OperatorUiEventLogProvider onEntriesChange={onEventLogEntriesChange}>
        <TaskActionClientProvider client={taskActionClient}>
          <Layout
            appBar={OperatorAppBar}
            menu={() => (
              <OperatorMenu basePath={basePath} operatorRoles={operatorRoles} />
            )}
          >
            <OperatorShellContent
              basePath={basePath}
              canInspectActionReview={canInspectActionReview}
              canViewAdmin={canViewAdminSurface}
              canViewActionReview={canViewActionReview}
              operatorIdentity={operatorIdentity}
              operatorRoles={operatorRoles}
              sessionStore={sessionStore}
            />
          </Layout>
        </TaskActionClientProvider>
      </OperatorUiEventLogProvider>
    </AdminContext>
  );
}
