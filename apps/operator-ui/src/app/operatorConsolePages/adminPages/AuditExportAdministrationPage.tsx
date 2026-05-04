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
import { RBAC_ROLE_MATRIX } from "../../../auth/roleMatrix";
import { formatAccess } from "./adminDisplay";
import {
  AUDIT_EXPORT_ACCESS_ROLES,
  AUDIT_EXPORT_NEGATIVE_POSTURES,
  AUDIT_EXPORT_STATES,
} from "./adminPostureData";

export function AuditExportAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Audit export administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Audit export admin config can request export windows and custody
          posture only; it cannot rewrite historical audit records, workflow
          records, release gates, or closeout truth.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Generated exports remain derived evidence from authoritative AegisOps
          records and must be reread from one committed backend snapshot.
        </Typography>
      </Stack>

      <Alert severity="info" variant="outlined">
        This surface does not add commercial reporting breadth, compliance
        templates, support bundles, production report custody, or RC/GA
        readiness claims.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Export states
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {AUDIT_EXPORT_STATES.map((state) => (
                    <Stack key={state.state} spacing={0.75}>
                      <Chip
                        color={
                          state.color as
                            | "default"
                            | "error"
                            | "success"
                            | "warning"
                        }
                        label={state.state}
                        size="small"
                        sx={{ alignSelf: "flex-start" }}
                        variant={state.color === "default" ? "outlined" : "filled"}
                      />
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

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  RBAC export access
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {AUDIT_EXPORT_ACCESS_ROLES.map((roleId) => (
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      key={roleId}
                      spacing={1}
                    >
                      <Typography fontWeight={600} variant="body2">
                        {roleId}:{" "}
                        {formatAccess(RBAC_ROLE_MATRIX[roleId].surfaces.auditExport)}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 3 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Fail-closed checks
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {AUDIT_EXPORT_NEGATIVE_POSTURES.map((posture) => (
                    <Typography key={posture} variant="body2">
                      {posture}
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
