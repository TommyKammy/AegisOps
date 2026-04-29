import {
  createContext,
  useEffect,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Card, CardContent, Chip, Stack, Typography } from "@mui/material";

type OperatorUiEventKind =
  | "route_view"
  | "operator_navigation"
  | "bounded_external_open";

export interface OperatorUiEventRecord {
  id: number;
  kind: OperatorUiEventKind;
  label: string;
  recordedAt: string;
  route: string;
  target?: string;
}

export type OperatorUiEventLogObserver = (
  entries: OperatorUiEventRecord[],
) => void;

interface OperatorUiEventLogContextValue {
  entries: OperatorUiEventRecord[];
  recordBoundedExternalOpen: (label: string, href: string) => void;
  recordNavigation: (label: string, target: string) => void;
  recordRouteView: (route: string) => void;
}

const MAX_EVENT_LOG_ENTRIES = 12;
const REDACTED_PATH_SUFFIX = "<redacted-path-suffix>";
const SECRET_LIKE_PATH_SEGMENT_PATTERN =
  /(?:auth|bearer|credential|jwt|key|secret|session|sig|signed|signature|token)/i;
const OPAQUE_PATH_SEGMENT_PATTERN = /^[A-Za-z0-9_-]{32,}$/;
const OperatorUiEventLogContext =
  createContext<OperatorUiEventLogContextValue | null>(null);

function trimUnsafeSuffixes(value: string) {
  const [withoutHash] = value.split("#", 1);
  const [withoutQuery] = withoutHash.split("?", 1);
  return withoutQuery || "/";
}

function sanitizeRoute(value: string) {
  const trimmed = trimUnsafeSuffixes(value.trim());
  return trimmed.length > 0 ? trimmed : "/";
}

function redactUnsafePathSuffix(pathname: string) {
  const path = sanitizeRoute(pathname);
  const segments = path.split("/");
  const redactionIndex = segments.findIndex((segment) => (
    SECRET_LIKE_PATH_SEGMENT_PATTERN.test(segment) ||
    OPAQUE_PATH_SEGMENT_PATTERN.test(segment)
  ));

  if (redactionIndex < 0) {
    return path;
  }

  const visiblePrefix = segments.slice(0, redactionIndex).join("/") || "/";
  return visiblePrefix.endsWith("/")
    ? `${visiblePrefix}${REDACTED_PATH_SUFFIX}`
    : `${visiblePrefix}/${REDACTED_PATH_SUFFIX}`;
}

function sanitizeTarget(value: string) {
  try {
    const parsed = new URL(value, "https://operator-ui.invalid");
    const path = redactUnsafePathSuffix(parsed.pathname);

    if (parsed.origin === "https://operator-ui.invalid") {
      return path;
    }

    return `${parsed.origin}${path}`;
  } catch {
    return redactUnsafePathSuffix(value);
  }
}

function appendEntry(
  previous: OperatorUiEventRecord[],
  nextEntry: OperatorUiEventRecord,
) {
  return [nextEntry, ...previous].slice(0, MAX_EVENT_LOG_ENTRIES);
}

export function OperatorUiEventLogProvider({
  children,
  now = () => new Date(),
  onEntriesChange,
}: {
  children: ReactNode;
  now?: () => Date;
  onEntriesChange?: OperatorUiEventLogObserver;
}) {
  const [entries, setEntries] = useState<OperatorUiEventRecord[]>([]);
  const nextId = useRef(1);

  useEffect(() => {
    onEntriesChange?.(entries);
  }, [entries, onEntriesChange]);

  const value = useMemo<OperatorUiEventLogContextValue>(
    () => ({
      entries,
      recordBoundedExternalOpen(label, href) {
        setEntries((previous) =>
          appendEntry(previous, {
            id: nextId.current++,
            kind: "bounded_external_open",
            label,
            recordedAt: now().toISOString(),
            route: "browser",
            target: sanitizeTarget(href),
          }),
        );
      },
      recordNavigation(label, target) {
        setEntries((previous) =>
          appendEntry(previous, {
            id: nextId.current++,
            kind: "operator_navigation",
            label,
            recordedAt: now().toISOString(),
            route: sanitizeRoute(target),
            target: sanitizeRoute(target),
          }),
        );
      },
      recordRouteView(route) {
        const sanitizedRoute = sanitizeRoute(route);

        setEntries((previous) => {
          const latest = previous[0];
          if (
            latest?.kind === "route_view" &&
            latest.route === sanitizedRoute
          ) {
            return previous;
          }

          return appendEntry(previous, {
            id: nextId.current++,
            kind: "route_view",
            label: "Route view",
            recordedAt: now().toISOString(),
            route: sanitizedRoute,
          });
        });
      },
    }),
    [entries, now],
  );

  return (
    <OperatorUiEventLogContext.Provider value={value}>
      {children}
    </OperatorUiEventLogContext.Provider>
  );
}

export function useOperatorUiEventLog() {
  const value = useContext(OperatorUiEventLogContext);

  if (value === null) {
    throw new Error("Operator UI event log context is not available.");
  }

  return value;
}

function eventKindLabel(kind: OperatorUiEventKind) {
  switch (kind) {
    case "bounded_external_open":
      return "External open";
    case "operator_navigation":
      return "Navigation";
    case "route_view":
      return "Route view";
    default:
      return kind;
  }
}

export function OperatorUiEventLogPanel() {
  const { entries } = useOperatorUiEventLog();

  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography component="h2" variant="h6">
              Reviewed UI event log
            </Typography>
            <Typography color="text.secondary" variant="body2">
              Browser-side traces stay advisory-only. Query strings, fragments,
              and secret-like URL suffixes are excluded from this review aid.
            </Typography>
          </Stack>
          {entries.length === 0 ? (
            <Typography color="text.secondary" variant="body2">
              No reviewed UI events recorded yet.
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {entries.map((entry) => (
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  justifyContent="space-between"
                  key={entry.id}
                  spacing={1}
                >
                  <Stack spacing={0.75}>
                    <Stack direction="row" flexWrap="wrap" gap={1}>
                      <Chip
                        color="primary"
                        label={eventKindLabel(entry.kind)}
                        size="small"
                        variant="outlined"
                      />
                      <Typography variant="body2">{entry.label}</Typography>
                    </Stack>
                    <Typography variant="body2">Route: {entry.route}</Typography>
                    {entry.target ? (
                      <Typography color="text.secondary" variant="caption">
                        Target: {entry.target}
                      </Typography>
                    ) : null}
                  </Stack>
                  <Typography color="text.secondary" variant="caption">
                    {entry.recordedAt}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
