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
  FUTURE_SOURCE_POSTURE,
  SOURCE_PROFILE_AUDIT_TRAIL,
  SOURCE_PROFILE_STATES,
} from "./adminPostureData";

export function SourceProfileAdministrationPage() {
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
