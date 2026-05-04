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
import {
  RETENTION_NEGATIVE_POSTURES,
  RETENTION_RECORD_FAMILIES,
  RETENTION_STATE_POSTURES,
} from "./adminPostureData";

export function RetentionPolicyAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Retention policy administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Retention policy admin config can define posture and review windows
          only; it cannot delete locked or export-pending records, close active
          workflow records, erase audit truth, or rewrite historical record
          chains.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Stale retention admin cache is never authority. Backend authoritative
          lifecycle state and record-chain reread remain decisive before any
          future purge candidate can be considered.
        </Typography>
      </Stack>

      <Alert severity="warning" variant="outlined">
        Retention administration leaves runtime purge jobs, customer-specific
        retention modeling, broad reporting, and RC/GA readiness outside this
        surface.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Record families
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {RETENTION_RECORD_FAMILIES.map((recordFamily) => (
                    <Stack key={recordFamily.family} spacing={0.5}>
                      <Typography fontWeight={600} variant="body2">
                        {recordFamily.family}
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        {recordFamily.posture}
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
                  Retention states
                </Typography>
                <Divider />
                <Stack spacing={1.25}>
                  {RETENTION_STATE_POSTURES.map((state) => (
                    <Stack key={state.state} spacing={0.75}>
                      <Chip
                        color={
                          state.color as
                            | "default"
                            | "error"
                            | "primary"
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

        <Grid size={{ xs: 12, lg: 3 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Fail-closed checks
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {RETENTION_NEGATIVE_POSTURES.map((posture) => (
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
