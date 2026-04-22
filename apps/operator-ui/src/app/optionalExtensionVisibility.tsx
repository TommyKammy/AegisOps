import { Alert, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";

export type OptionalExtensionStatus =
  | "enabled"
  | "disabled_by_default"
  | "unavailable"
  | "degraded";

export interface OptionalExtensionDefinition {
  description: string;
  status: OptionalExtensionStatus;
  title: string;
}

interface OptionalExtensionSignal {
  availability?: unknown;
  enablement?: unknown;
  reason?: unknown;
  readiness?: unknown;
}

const OPTIONAL_EXTENSION_FAMILY_METADATA = [
  {
    baseDescription:
      "Assistant posture remains advisory-only and never outranks authoritative workflow truth.",
    key: "assistant",
    title: "Assistant",
  },
  {
    baseDescription:
      "Endpoint evidence stays subordinate to an already reviewed case and approved bounded request.",
    key: "endpoint_evidence",
    title: "Endpoint evidence",
  },
  {
    baseDescription:
      "Optional network evidence remains subordinate to reviewed control-plane truth and non-blocking for the mainline runtime.",
    key: "network_evidence",
    title: "Optional network evidence",
  },
  {
    baseDescription:
      "ML shadow remains shadow-only, audit-focused, and outside approval, execution, and reconciliation authority.",
    key: "ml_shadow",
    title: "ML shadow",
  },
] as const;

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function humanizeReason(reason: string | null): string | null {
  if (reason === null) {
    return null;
  }

  return reason.replaceAll("_", " ");
}

function deriveOptionalExtensionStatus(extension: OptionalExtensionSignal | null): OptionalExtensionStatus {
  const enablement = asString(extension?.enablement);
  const availability = asString(extension?.availability);
  const readiness = asString(extension?.readiness);

  if (readiness === "degraded" || readiness === "delayed") {
    return "degraded";
  }

  if (enablement === "disabled_by_default") {
    return "disabled_by_default";
  }

  if (enablement === "enabled") {
    return availability === "available" ? "enabled" : "unavailable";
  }

  if (availability === "unavailable") {
    return "unavailable";
  }

  return "unavailable";
}

function optionalExtensionStatusExplanation(status: OptionalExtensionStatus): string {
  switch (status) {
    case "enabled":
      return "The reviewed optional path is active for its bounded role and remains subordinate to authoritative workflow truth.";
    case "disabled_by_default":
      return "The reviewed runtime is operating on the mainline path without this optional extension, which is expected behavior.";
    case "unavailable":
      return "A reviewed prerequisite or binding is missing, but mainline queue, case, approval, execution, and reconciliation truth stay separate.";
    case "degraded":
      return "Subordinate optional context may be incomplete, stale, or delayed while mainline workflow truth remains separate.";
  }
}

export function buildOptionalExtensionDefinitionsFromPayload(
  optionalExtensions: unknown,
): OptionalExtensionDefinition[] {
  const extensionEntries = asRecord(asRecord(optionalExtensions)?.extensions);

  return OPTIONAL_EXTENSION_FAMILY_METADATA.map((family) => {
    const extension = asRecord(extensionEntries?.[family.key]);
    const status = deriveOptionalExtensionStatus(extension);
    const reason = humanizeReason(asString(extension?.reason));
    const description = [family.baseDescription, optionalExtensionStatusExplanation(status)];

    if (reason) {
      description.push(`Reviewed status source: ${reason}.`);
    }

    return {
      description: description.join(" "),
      status,
      title: family.title,
    };
  });
}

export function buildOptionalEvidenceDefinitionsFromPayload(
  optionalExtensions: unknown,
): OptionalExtensionDefinition[] {
  return buildOptionalExtensionDefinitionsFromPayload(optionalExtensions).filter((definition) =>
    ["Endpoint evidence", "Optional network evidence"].includes(definition.title),
  );
}

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

export function OptionalExtensionVisibilityPanel({
  definitions,
}: {
  definitions: readonly OptionalExtensionDefinition[];
}) {
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
        {definitions.map((definition) => (
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
