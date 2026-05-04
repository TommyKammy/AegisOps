import {
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { RBAC_ROLE_MATRIX, type RbacRoleId } from "../../auth/roleMatrix";

const ADMIN_ROLE_IDS: RbacRoleId[] = [
  "platform_admin",
  "analyst",
  "approver",
  "read_only_auditor",
  "support_operator",
  "external_collaborator",
];

const ADMIN_USERS = [
  {
    email: "platform.admin@example.com",
    role: "platform_admin",
    status: "Reviewed admin policy",
  },
  {
    email: "analyst@example.com",
    role: "analyst",
    status: "Reviewed operator policy",
  },
  {
    email: "approver@example.com",
    role: "approver",
    status: "Reviewed approval policy",
  },
] as const;

const SOURCE_PROFILE_STATES = [
  {
    label: "Create: reviewed source profile draft",
    posture:
      "New profile requests stay blocked until source family, custody, parser, provenance, and admission boundaries are reviewed.",
  },
  {
    label: "Update: reviewed posture change",
    posture:
      "Version, intake, credential, and source-health posture changes require explicit reviewed evidence and audit linkage.",
  },
  {
    label: "Disable: source admission blocked",
    posture:
      "Disabled profiles block future source admission without rewriting historical alerts, cases, evidence, or reconciliation records.",
  },
  {
    label: "Degraded: visible subordinate context",
    posture:
      "Degraded posture stays visible to operators as source-health context only and cannot advance workflow state.",
  },
] as const;

const SOURCE_PROFILE_AUDIT_TRAIL = [
  "Created by reviewed platform_admin session",
  "Changed fields and reason captured",
  "Disable or degraded transition records source admission impact",
  "Backend record-chain reread required before workflow use",
] as const;

const FUTURE_SOURCE_POSTURE = [
  "Explicit reviewed source-family identifier",
  "Parser and provenance evidence present",
  "Credential custody reference reviewed",
  "No source profile state promoted to record-chain truth",
] as const;

function formatAccess(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function SourceProfileAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Source profile administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Source profile state configures source admission posture only; it
          cannot become signal, alert, case, evidence, workflow, release, gate,
          or closeout truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale source admin UI or browser cache is never authority. Backend
          record-chain reread remains decisive before source admission or
          workflow use.
        </Typography>
      </Stack>

      <Alert severity="info" variant="outlined">
        Wazuh profile administration remains bounded to reviewed source profile
        expectations; unsupported source onboarding and broad source catalog
        claims stay out of this surface.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack
                  alignItems="center"
                  direction={{ xs: "column", sm: "row" }}
                  justifyContent="space-between"
                  spacing={1}
                >
                  <Stack spacing={0.5}>
                    <Typography fontWeight={700}>Wazuh SMB single-node</Typography>
                    <Typography color="text.secondary" variant="body2">
                      Reviewed source profile for the Phase 53 Wazuh substrate
                      contract and source-health posture.
                    </Typography>
                  </Stack>
                  <Chip color="success" label="Reviewed" size="small" />
                </Stack>
                <Divider />
                <Stack spacing={1}>
                  {SOURCE_PROFILE_STATES.map((state) => (
                    <Stack key={state.label} spacing={0.5}>
                      <Typography fontWeight={600} variant="body2">
                        {state.label}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        {state.posture}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Audit trail
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {SOURCE_PROFILE_AUDIT_TRAIL.map((entry) => (
                    <Typography key={entry} variant="body2">
                      {entry}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3.5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Future reviewed sources
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {FUTURE_SOURCE_POSTURE.map((entry) => (
                    <Typography key={entry} variant="body2">
                      {entry}
                    </Typography>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

export function UserRoleAdminPage() {
  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h4">
          User and role administration
        </Typography>
        <Typography color="text.secondary" variant="body1">
          User and role changes are reviewed policy/config state only; they
          cannot rewrite historical workflow truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale browser role cache is never authority. Backend reread and denial
          remain decisive.
        </Typography>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack spacing={0.5}>
                  <Typography component="h2" variant="h5">
                    Users
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Minimum reviewed account bindings for the operator console.
                    The backend remains the source of effective access.
                  </Typography>
                </Stack>
                <Divider />
                {ADMIN_USERS.map((user) => (
                  <Stack key={user.email} spacing={0.75}>
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      spacing={1}
                    >
                      <Typography fontWeight={600}>{user.email}</Typography>
                      <Chip label={user.status} size="small" />
                    </Stack>
                    <Typography color="text.secondary" variant="body2">
                      Assigned role: {user.role}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack spacing={0.5}>
                  <Typography component="h2" variant="h5">
                    Roles
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    Phase 57.1 role matrix values are rendered as policy posture,
                    not workflow authority or approval truth.
                  </Typography>
                </Stack>
                <Divider />
                {ADMIN_ROLE_IDS.map((roleId) => {
                  const contract = RBAC_ROLE_MATRIX[roleId];

                  return (
                    <Stack key={roleId} spacing={1}>
                      <Stack
                        alignItems="center"
                        direction={{ xs: "column", sm: "row" }}
                        justifyContent="space-between"
                        spacing={1}
                      >
                        <Typography fontWeight={600}>{roleId}</Typography>
                        <Chip
                          color={
                            roleId === "platform_admin" ? "primary" : "default"
                          }
                          label={formatAccess(contract.surfaces.platformAdministration)}
                          size="small"
                        />
                      </Stack>
                      <Typography color="text.secondary" variant="body2">
                        {contract.description}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        Historical truth rewrite:{" "}
                        {formatAccess(contract.surfaces.historicalTruthRewrite)}
                      </Typography>
                    </Stack>
                  );
                })}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <SourceProfileAdministrationPage />
    </Stack>
  );
}
