import { useEffect, useState } from "react";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import RuleFolderOutlinedIcon from "@mui/icons-material/RuleFolderOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Card,
  CardContent,
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
import { Navigate, Route, Routes } from "react-router-dom";
import { operatorTheme } from "./theme";
import {
  ActionReviewPage,
  AssistantAdvisoryPage,
  AlertDetailPage,
  CaseDetailPage,
  ProvenancePage,
  QueuePage,
  ReadinessPage,
  ReconciliationPage,
} from "./operatorConsolePages";
import {
  OptionalExtensionVisibilityPanel,
  buildOptionalExtensionDefinitionsFromPayload,
} from "./optionalExtensionVisibility";
import { TaskActionClientProvider } from "../taskActions/taskActionPrimitives";
import type { OperatorTaskActionClient } from "../taskActions/taskActionClient";

function hasReviewedOperatorRole(
  operatorRoles: readonly string[],
  allowedRoles: readonly string[],
) {
  return operatorRoles.some((role) =>
    allowedRoles.includes(role.toLowerCase()),
  );
}

function canBrowseActionReview(operatorRoles: readonly string[]) {
  return operatorRoles.some((role) =>
    ["approver", "platform-administrator"].includes(role),
  );
}

function canInspectActionReviewDetail(operatorRoles: readonly string[]) {
  return hasReviewedOperatorRole(operatorRoles, [
    "analyst",
    "approver",
    "platform-administrator",
  ]);
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
  operatorRoles,
}: {
  operatorRoles: readonly string[];
}) {
  const showActionReview = canBrowseActionReview(operatorRoles);

  return (
    <Menu>
      <Menu.DashboardItem primaryText="Overview" />
      <Menu.Item
        leftIcon={<InboxOutlinedIcon />}
        primaryText="Queue"
        to="/operator/queue"
      />
      <Menu.Item
        leftIcon={<WarningAmberOutlinedIcon />}
        primaryText="Alerts"
        to="/operator/queue"
      />
      <Menu.Item
        leftIcon={<InsightsOutlinedIcon />}
        primaryText="Cases"
        to="/operator/queue"
      />
      <Menu.Item
        leftIcon={<LinkOutlinedIcon />}
        primaryText="Provenance"
        to="/operator/provenance/alerts"
      />
      <Menu.Item
        leftIcon={<CheckCircleOutlineIcon />}
        primaryText="Readiness"
        to="/operator/readiness"
      />
      <Menu.Item
        leftIcon={<RuleFolderOutlinedIcon />}
        primaryText="Reconciliation"
        to="/operator/reconciliation"
      />
      <Menu.Item
        leftIcon={<AutoAwesomeOutlinedIcon />}
        primaryText="Assistant"
        to="/operator/assistant"
      />
      {showActionReview ? (
        <Menu.Item
          leftIcon={<GavelOutlinedIcon />}
          primaryText="Action Review"
          to="/operator/action-review"
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

function PlaceholderPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Stack spacing={2} sx={{ p: 3 }}>
      <Typography component="h1" variant="h4">
        {title}
      </Typography>
      <Typography color="text.secondary" variant="body1">
        {description}
      </Typography>
      <Typography variant="body2">
        This route exists so later adapter and page work can land without
        replacing the approved auth boundary.
      </Typography>
    </Stack>
  );
}

export function OperatorShell({
  authProvider,
  dataProvider,
  operatorIdentity,
  operatorRoles,
  taskActionClient,
}: {
  authProvider: AuthProvider;
  dataProvider: DataProvider;
  operatorIdentity: string;
  operatorRoles: string[];
  taskActionClient: OperatorTaskActionClient;
}) {
  const canViewActionReview = canBrowseActionReview(operatorRoles);
  const canInspectActionReview = canInspectActionReviewDetail(operatorRoles);

  return (
    <AdminContext
      authProvider={authProvider}
      dataProvider={dataProvider}
      theme={operatorTheme}
    >
      <TaskActionClientProvider client={taskActionClient}>
        <Layout
          appBar={OperatorAppBar}
          menu={() => <OperatorMenu operatorRoles={operatorRoles} />}
        >
          <Routes>
            <Route element={<OverviewPage operatorRoles={operatorRoles} />} index />
            <Route element={<QueuePage />} path="queue" />
            <Route
              element={<AlertDetailPage operatorIdentity={operatorIdentity} />}
              path="alerts/:alertId"
            />
            <Route
              element={<CaseDetailPage operatorIdentity={operatorIdentity} />}
              path="cases/:caseId"
            />
            <Route element={<ProvenancePage />} path="provenance/:family/:recordId" />
            <Route element={<ReadinessPage />} path="readiness" />
            <Route element={<ReconciliationPage />} path="reconciliation" />
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
                  <Navigate replace to="/operator/forbidden" />
                )
              }
              path="action-review"
            />
            <Route
              element={
                canInspectActionReview ? (
                  <ActionReviewPage
                    operatorIdentity={operatorIdentity}
                    operatorRoles={operatorRoles}
                  />
                ) : (
                  <Navigate replace to="/operator/forbidden" />
                )
              }
              path="action-review/:actionRequestId"
            />
            <Route
              element={
                <PlaceholderPage
                  description="Use the queue as the primary route into alert detail."
                  title="Alerts"
                />
              }
              path="alerts"
            />
            <Route
              element={
                <PlaceholderPage
                  description="Use the queue or linked alert detail to open a specific case."
                  title="Cases"
                />
              }
              path="cases"
            />
            <Route
              element={
                <PlaceholderPage
                  description="Open provenance from alert or case detail so the page stays anchored to an authoritative record."
                  title="Provenance"
                />
              }
              path="provenance/*"
            />
            <Route element={<UnsupportedOperatorRoutePage />} path="*" />
          </Routes>
        </Layout>
      </TaskActionClientProvider>
    </AdminContext>
  );
}
