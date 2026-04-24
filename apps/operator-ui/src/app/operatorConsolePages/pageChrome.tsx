import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import ReportProblemOutlinedIcon from "@mui/icons-material/ReportProblemOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import type { ReactNode } from "react";
import { Link as ReactRouterLink } from "react-router-dom";
import { useOperatorUiEventLog } from "../operatorUiEvents";
import {
  asString,
  formatLabel,
  formatValue,
  getPath,
  isAllowedExternalHref,
  statusTone,
  type UnknownRecord,
} from "./recordUtils";

export function PageFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <Stack spacing={3} sx={{ p: { xs: 2, md: 3 } }}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h4">
          {title}
        </Typography>
        <Typography color="text.secondary" maxWidth={860} variant="body1">
          {subtitle}
        </Typography>
      </Stack>
      {children}
    </Stack>
  );
}

export function LoadingState({ label }: { label: string }) {
  return (
    <Box sx={{ display: "grid", minHeight: 280, placeItems: "center" }}>
      <Stack alignItems="center" spacing={2}>
        <CircularProgress aria-label={label} />
        <Typography color="text.secondary" variant="body2">
          Loading reviewed operator data.
        </Typography>
      </Stack>
    </Box>
  );
}

export function ErrorState({ error }: { error: Error }) {
  if (error.name === "OperatorDataProviderAuthorizationError") {
    return (
      <Alert severity="warning" variant="outlined">
        Reviewed backend authorization is required before this operator surface can render.
      </Alert>
    );
  }

  if (error.name === "OperatorDataProviderContractError") {
    return (
      <Alert severity="error" variant="outlined">
        Reviewed operator data could not be verified. The browser stayed fail-closed instead of rendering an untrusted record.
      </Alert>
    );
  }

  return (
    <Alert severity="error" variant="outlined">
      {error.message}
    </Alert>
  );
}

export function QueryStateNotice({
  error,
  refreshing,
}: {
  error: Error | null;
  refreshing: boolean;
}) {
  if (error) {
    return (
      <Alert severity="warning" variant="outlined">
        Showing the last verified operator data while refresh is unavailable.
        <br />
        {error.message}
      </Alert>
    );
  }

  if (refreshing) {
    return (
      <Alert severity="info" variant="outlined">
        Refreshing reviewed operator data while the last verified state remains visible.
      </Alert>
    );
  }

  return null;
}

export function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography variant="h6">{title}</Typography>
            {subtitle ? (
              <Typography color="text.secondary" variant="body2">
                {subtitle}
              </Typography>
            ) : null}
          </Stack>
          <Divider />
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function ValueList({
  entries,
}: {
  entries: Array<[string, unknown]>;
}) {
  return (
    <Stack divider={<Divider flexItem />} spacing={0}>
      {entries.map(([label, value]) => (
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          key={label}
          spacing={1}
          sx={{ py: 1 }}
        >
          <Typography color="text.secondary" variant="body2">
            {label}
          </Typography>
          <Typography sx={{ textAlign: { sm: "right" } }} variant="body2">
            {formatValue(value)}
          </Typography>
        </Stack>
      ))}
    </Stack>
  );
}

export function StatusStrip({
  values,
}: {
  values: Array<[string, string | null]>;
}) {
  return (
    <Stack direction="row" flexWrap="wrap" gap={1}>
      {values
        .filter(([, value]) => value !== null)
        .map(([label, value]) => (
          <Chip
            color={statusTone(value)}
            key={`${label}-${value}`}
            label={`${label}: ${value}`}
            size="small"
            variant={statusTone(value) === "default" ? "outlined" : "filled"}
          />
        ))}
    </Stack>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <Alert severity="info" variant="outlined">
      {message}
    </Alert>
  );
}

export function RecordWarnings({ record }: { record: UnknownRecord }) {
  const warnings: string[] = [];
  const reviewState = asString(record.review_state);
  const externalTicketStatus = asString(getPath(record, "external_ticket_reference.status"));

  if (
    reviewState !== null &&
    ["degraded", "rejected", "missing_anchor", "mismatch"].includes(reviewState)
  ) {
    warnings.push(`Review state remains ${reviewState}.`);
  }
  if (externalTicketStatus !== null && externalTicketStatus !== "present") {
    warnings.push(`Non-authoritative coordination reference is ${externalTicketStatus}.`);
  }
  if (asString(record.case_id) === null && asString(record.case_lifecycle_state) !== null) {
    warnings.push("Case lifecycle state is present without an authoritative case identifier.");
  }

  if (warnings.length === 0) {
    return null;
  }

  return (
    <Stack spacing={1}>
      {warnings.map((warning) => (
        <Alert
          icon={<ReportProblemOutlinedIcon fontSize="inherit" />}
          key={warning}
          severity="warning"
          variant="outlined"
        >
          {warning}
        </Alert>
      ))}
    </Stack>
  );
}

function extractSubordinateLinks(record: UnknownRecord): Array<{ href: string; label: string }> {
  const entries: Array<{ href: string; label: string }> = [];

  for (const [key, value] of Object.entries(record)) {
    const href = asString(value);
    if (href && isAllowedExternalHref(href)) {
      entries.push({
        href,
        label: formatLabel(key),
      });
    }
  }

  return entries;
}

export function SubordinateLinks({ records }: { records: UnknownRecord[] }) {
  const links = records.flatMap((record) => extractSubordinateLinks(record));
  const { recordBoundedExternalOpen } = useOperatorUiEventLog();

  if (links.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2">
        No substrate deep link was exposed by the reviewed backend payload.
      </Typography>
    );
  }

  return (
    <Stack direction="row" flexWrap="wrap" gap={1}>
      {links.map((link) => (
        <Button
          component={Link}
          endIcon={<OpenInNewOutlinedIcon />}
          href={link.href}
          key={`${link.label}-${link.href}`}
          onClick={() => {
            recordBoundedExternalOpen(link.label, link.href);
          }}
          rel="noreferrer"
          size="small"
          target="_blank"
          variant="outlined"
        >
          {link.label}
        </Button>
      ))}
    </Stack>
  );
}

export function AuditedRouteLink({
  children,
  label,
  to,
}: {
  children: ReactNode;
  label: string;
  to: string;
}) {
  const { recordNavigation } = useOperatorUiEventLog();

  return (
    <Link
      component={ReactRouterLink}
      onClick={() => {
        recordNavigation(label, to);
      }}
      to={to}
      underline="hover"
    >
      {children}
    </Link>
  );
}

export function AuditedRouteButton({
  children,
  label,
  to,
}: {
  children: ReactNode;
  label: string;
  to: string;
}) {
  const { recordNavigation } = useOperatorUiEventLog();

  return (
    <Button
      component={ReactRouterLink}
      endIcon={<LaunchOutlinedIcon />}
      onClick={() => {
        recordNavigation(label, to);
      }}
      to={to}
      variant="outlined"
    >
      {children}
    </Button>
  );
}
