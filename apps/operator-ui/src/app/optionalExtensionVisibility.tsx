import { Alert, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";

export type OptionalExtensionStatus =
  | "enabled"
  | "disabled_by_default"
  | "unavailable"
  | "degraded";

interface OptionalExtensionDefinition {
  description: string;
  status: OptionalExtensionStatus;
  title: string;
}

const OPTIONAL_EXTENSION_DEFINITIONS: OptionalExtensionDefinition[] = [
  {
    title: "Assistant",
    status: "enabled",
    description:
      "Enabled and ready means the bounded reviewed summary provider is available. Secondary enrichment remains non-blocking and never outranks authoritative workflow truth.",
  },
  {
    title: "Endpoint evidence",
    status: "disabled_by_default",
    description:
      "Disabled by default means no reviewed endpoint-evidence request is active. The operator shell keeps that posture visible without implying a control-plane gap.",
  },
  {
    title: "Optional network evidence",
    status: "unavailable",
    description:
      "Unavailable means the optional path is not activated on this reviewed runtime and does not block boot, queue review, approval, execution, or reconciliation truth.",
  },
  {
    title: "ML shadow",
    status: "degraded",
    description:
      "Degraded remains shadow-only and non-authoritative. Operators must repair or disable the optional path instead of widening authority or inferring healthy state from silence.",
  },
];

function optionalExtensionStatusMetadata(status: OptionalExtensionStatus): {
  color: "default" | "error" | "info" | "success" | "warning";
  label: string;
} {
  switch (status) {
    case "enabled":
      return {
        color: "success",
        label: "Enabled",
      };
    case "disabled_by_default":
      return {
        color: "default",
        label: "Disabled By Default",
      };
    case "unavailable":
      return {
        color: "info",
        label: "Unavailable",
      };
    case "degraded":
      return {
        color: "warning",
        label: "Degraded",
      };
  }
}

export function OptionalExtensionStatusChip({
  status,
}: {
  status: OptionalExtensionStatus;
}) {
  const metadata = optionalExtensionStatusMetadata(status);

  return <Chip color={metadata.color} label={metadata.label} size="small" />;
}

export function OptionalExtensionVisibilityPanel() {
  return (
    <Stack spacing={2.5}>
      <Stack spacing={1}>
        <Typography component="h2" variant="h5">
          Optional extension visibility
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Optional-path posture stays subordinate to authoritative workflow pages and reviewed
          runtime truth.
        </Typography>
      </Stack>

      <Alert severity="info" variant="outlined">
        Missing optional paths do not imply a control-plane failure when the mainline reviewed
        workflow remains healthy.
      </Alert>

      <Grid container spacing={2}>
        {OPTIONAL_EXTENSION_DEFINITIONS.map((definition) => (
          <Grid key={definition.title} size={{ xs: 12, md: 6 }}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Stack spacing={1.5}>
                  <Stack direction="row" justifyContent="space-between" spacing={2}>
                    <Typography variant="h6">{definition.title}</Typography>
                    <OptionalExtensionStatusChip status={definition.status} />
                  </Stack>
                  <Typography color="text.secondary" variant="body2">
                    {definition.description}
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
