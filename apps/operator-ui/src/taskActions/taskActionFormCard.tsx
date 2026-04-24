import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import { type ReactNode, useState } from "react";
import {
  taskActionStatusMessage,
  type TaskActionSubmissionController,
} from "./taskActionSubmission";

function TaskActionStatusBanner<TAcknowledgement>({
  submission,
}: {
  submission: TaskActionSubmissionController<TAcknowledgement>;
}) {
  const { error, phase, refreshRecords } = submission.state;

  if (phase === "idle") {
    return null;
  }

  if (phase === "submitting" || phase === "refreshing") {
    return (
      <Alert
        icon={<CircularProgress aria-label="Submitting reviewed task action" size={18} />}
        severity="info"
        variant="outlined"
      >
        {phase === "submitting"
          ? "Submitting the reviewed task action."
          : "Re-reading authoritative backend state after submit."}
      </Alert>
    );
  }

  if (phase === "success") {
    return (
      <Alert severity="success" variant="outlined">
        Authoritative refresh completed from the reviewed backend record.
        {refreshRecords.length > 0 ? ` Refreshed: ${refreshRecords.map((record) => record.label).join(", ")}.` : ""}
      </Alert>
    );
  }

  if (phase === "degraded") {
    return (
      <Alert
        icon={<WarningAmberOutlinedIcon fontSize="inherit" />}
        severity="warning"
        variant="outlined"
      >
        Authoritative re-read did not complete after submit. Treat the result as unresolved until the reviewed record is refreshed. {taskActionStatusMessage(error)}
      </Alert>
    );
  }

  return (
    <Alert severity="error" variant="outlined">
      {taskActionStatusMessage(error)}
    </Alert>
  );
}

function MetadataList({
  entries,
  title,
}: {
  entries: Array<[string, string]>;
  title: string;
}) {
  return (
    <Stack spacing={1}>
      <Typography variant="subtitle2">{title}</Typography>
      <Stack divider={<Divider flexItem />} spacing={0}>
        {entries.map(([label, value]) => (
          <Stack
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            key={`${title}-${label}`}
            spacing={1}
            sx={{ py: 0.75 }}
          >
            <Typography color="text.secondary" variant="body2">
              {label}
            </Typography>
            <Typography sx={{ textAlign: { sm: "right" } }} variant="body2">
              {value}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}

export function TaskActionFormCard<TAcknowledgement>({
  actor,
  binding,
  children,
  confirmLabel = "I confirm this reviewed task action should be submitted.",
  provenance,
  submission,
  submitLabel,
  subtitle,
  title,
}: {
  actor: Array<[string, string]>;
  binding: Array<[string, string]>;
  children: ReactNode;
  confirmLabel?: string;
  provenance: Array<[string, string]>;
  submission: TaskActionSubmissionController<TAcknowledgement>;
  submitLabel: string;
  subtitle: string;
  title: string;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const busy =
    submission.state.phase === "submitting" ||
    submission.state.phase === "refreshing";

  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={3}>
          <Stack spacing={1}>
            <Typography variant="h6">{title}</Typography>
            <Typography color="text.secondary" variant="body2">
              {subtitle}
            </Typography>
          </Stack>

          <Divider />

          <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
            <Box flex={1}>
              <MetadataList entries={actor} title="Actor context" />
            </Box>
            <Box flex={1}>
              <MetadataList entries={binding} title="Authoritative binding" />
            </Box>
            <Box flex={1}>
              <MetadataList entries={provenance} title="Provenance context" />
            </Box>
          </Stack>

          <Divider />

          {children}

          <TaskActionStatusBanner submission={submission} />

          <Stack
            direction={{ xs: "column", sm: "row" }}
            justifyContent="space-between"
            spacing={2}
          >
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmed}
                  onChange={(event) => {
                    setConfirmed(event.target.checked);
                  }}
                />
              }
              label={confirmLabel}
            />
            <Button disabled={!confirmed || busy} type="submit" variant="contained">
              {busy ? "Working..." : submitLabel}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
