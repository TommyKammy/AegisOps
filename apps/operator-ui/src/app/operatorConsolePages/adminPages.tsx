import {
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

function formatAccess(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
    </Stack>
  );
}
