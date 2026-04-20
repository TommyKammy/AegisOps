import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import type { AuthProvider } from "react-admin";
import {
  AdminContext,
  AppBar,
  Layout,
  Logout,
  Menu,
  TitlePortal,
} from "react-admin";
import { Route, Routes } from "react-router-dom";
import { operatorDataProvider } from "../dataProvider";
import { operatorTheme } from "./theme";

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

function OperatorMenu() {
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
        to="/operator/alerts"
      />
      <Menu.Item
        leftIcon={<InsightsOutlinedIcon />}
        primaryText="Cases"
        to="/operator/cases"
      />
      <Menu.Item
        leftIcon={<CheckCircleOutlineIcon />}
        primaryText="Readiness"
        to="/operator/readiness"
      />
      <Menu.Item
        leftIcon={<GavelOutlinedIcon />}
        primaryText="Action Review"
        to="/operator/action-review"
      />
    </Menu>
  );
}

function OverviewPage() {
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
        {[
          {
            title: "Queue",
            chip: "Next slice",
            description:
              "Queue triage pages will land here once the reviewed data adapter is wired.",
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
            title: "Action review",
            chip: "Guarded",
            description:
              "Action review surfaces remain separate from execution authority and stay read-oriented here.",
          },
        ].map((section) => (
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
}: {
  authProvider: AuthProvider;
}) {
  return (
    <AdminContext
      authProvider={authProvider}
      dataProvider={operatorDataProvider}
      theme={operatorTheme}
    >
      <Layout appBar={OperatorAppBar} menu={OperatorMenu}>
        <Routes>
          <Route element={<OverviewPage />} index />
          <Route
            element={
              <PlaceholderPage
                description="Reviewed queue views will render backend-authoritative queue summaries here."
                title="Queue"
              />
            }
            path="queue"
          />
          <Route
            element={
              <PlaceholderPage
                description="Alert pages remain read-only and anchored to backend-normalized alert records."
                title="Alerts"
              />
            }
            path="alerts"
          />
          <Route
            element={
              <PlaceholderPage
                description="Case pages will preserve authoritative lifecycle state and provenance anchors."
                title="Cases"
              />
            }
            path="cases"
          />
          <Route
            element={
              <PlaceholderPage
                description="Readiness stays derived from authoritative backend state instead of browser-local projections."
                title="Readiness"
              />
            }
            path="readiness"
          />
          <Route
            element={
              <PlaceholderPage
                description="Action review remains inspection-only until a separately reviewed slice introduces action workflows."
                title="Action review"
              />
            }
            path="action-review"
          />
        </Routes>
      </Layout>
    </AdminContext>
  );
}
