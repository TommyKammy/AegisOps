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
  ACTION_POLICY_AUDIT_TRAIL,
  ACTION_POLICY_POSTURES,
  DISABLED_ACTION_POLICY_POSTURES,
} from "./adminPostureData";

export function ActionPolicyAdministrationPage() {
  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography component="h2" variant="h5">
          Action policy administration
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Action policy admin config is eligible posture only; stale UI or
          cache state cannot approve, execute, reconcile, mutate substrates, or
          rewrite historical receipts.
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Existing approval, execution, and reconciliation authority remains
          backend-owned and reread from the authoritative record chain.
        </Typography>
      </Stack>

      <Alert severity="warning" variant="outlined">
        Controlled and Hard Write default enablement is rejected; those action
        families remain approval-bound and backend-enforced.
      </Alert>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography component="h3" variant="h6">
                  Default low-risk posture
                </Typography>
                <Divider />
                <Stack spacing={1.5}>
                  {ACTION_POLICY_POSTURES.map((policy) => (
                    <Stack key={policy.family} spacing={0.75}>
                      <Stack
                        alignItems="center"
                        direction={{ xs: "column", sm: "row" }}
                        justifyContent="space-between"
                        spacing={1}
                      >
                        <Typography fontWeight={600}>{policy.family}</Typography>
                        <Chip
                          color={
                            policy.posture === "Allowed by default"
                              ? "success"
                              : "warning"
                          }
                          label={policy.posture}
                          size="small"
                        />
                      </Stack>
                      <Typography color="text.secondary" variant="body2">
                        {policy.description}
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
                  Rejected default enablement
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {DISABLED_ACTION_POLICY_POSTURES.map((policy) => (
                    <Stack
                      alignItems="center"
                      direction={{ xs: "column", sm: "row" }}
                      justifyContent="space-between"
                      key={policy.family}
                      spacing={1}
                    >
                      <Typography fontWeight={600} variant="body2">
                        {policy.family}
                      </Typography>
                      <Chip
                        color="error"
                        label={policy.posture}
                        size="small"
                        variant="outlined"
                      />
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
                  Policy audit trail
                </Typography>
                <Divider />
                <Stack spacing={1}>
                  {ACTION_POLICY_AUDIT_TRAIL.map((entry) => (
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
