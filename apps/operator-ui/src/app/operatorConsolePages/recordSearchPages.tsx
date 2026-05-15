import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  Button,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { FormEvent, useMemo, useState } from "react";
import {
  asString,
  AuditedRouteLink,
  EmptyState,
  ErrorState,
  formatValue,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  type UnknownRecord,
  useOperatorList,
} from "./shared";

const RECORD_SEARCH_SORT = {
  field: "record_family",
  order: "ASC",
} as const;

const SOURCE_FAMILY_OPTIONS = [
  ["", "All reviewed sources"],
  ["wazuh_detection", "Wazuh detection"],
  ["github_audit", "GitHub audit"],
  ["microsoft_365_audit", "Microsoft 365 audit"],
  ["entra_id", "Entra ID"],
  ["windows_security_endpoint", "Windows endpoint"],
] as const;

function RecordSearchTable({ records }: { records: UnknownRecord[] }) {
  if (records.length === 0) {
    return <EmptyState message="No reviewed AegisOps records matched the current search." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Record</TableCell>
          <TableCell>Source</TableCell>
          <TableCell>Lifecycle</TableCell>
          <TableCell>Authority</TableCell>
          <TableCell>Summary</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {records.map((record) => {
          const recordFamily = asString(record.record_family);
          const recordId = asString(record.record_id);
          const route = asString(record.route);
          const label = `${recordFamily ?? "record"}:${recordId ?? String(record.id)}`;

          return (
            <TableRow key={String(record.id)} hover>
              <TableCell>
                {route ? (
                  <AuditedRouteLink label="Open reviewed record" to={route}>
                    {label}
                  </AuditedRouteLink>
                ) : (
                  label
                )}
              </TableCell>
              <TableCell>{formatValue(record.source_family)}</TableCell>
              <TableCell>{formatValue(record.lifecycle_state)}</TableCell>
              <TableCell>{formatValue(record.authority)}</TableCell>
              <TableCell>{formatValue(record.summary)}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function RecordSearchPage() {
  const [draftQuery, setDraftQuery] = useState("github");
  const [draftSourceFamily, setDraftSourceFamily] = useState("");
  const [criteria, setCriteria] = useState({
    q: "github",
    source_family: "",
  });
  const filter = useMemo(
    () => ({
      q: criteria.q,
      source_family: criteria.source_family,
    }),
    [criteria],
  );
  const results = useOperatorList(
    "recordSearch",
    filter,
    RECORD_SEARCH_SORT,
    25,
  );

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCriteria({
      q: draftQuery,
      source_family: draftSourceFamily,
    });
  }

  if (results.loading && results.data === null) {
    return <LoadingState label="Loading reviewed record search" />;
  }

  return (
    <PageFrame
      subtitle="Search is a read-only navigation aid over reviewed AegisOps records. Results cannot close cases, approve detectors, suppress signals, reconcile outcomes, or promote raw source data into workflow truth."
      title="Record Search"
    >
      {results.error && results.data === null ? (
        <ErrorState error={results.error} />
      ) : (
        <Stack spacing={2}>
          <Stack
            component="form"
            direction={{ xs: "column", md: "row" }}
            onSubmit={submitSearch}
            spacing={2}
          >
            <TextField
              label="Search reviewed records"
              onChange={(event) => setDraftQuery(event.target.value)}
              size="small"
              value={draftQuery}
            />
            <TextField
              label="Source family"
              onChange={(event) => setDraftSourceFamily(event.target.value)}
              select
              size="small"
              value={draftSourceFamily}
              sx={{ minWidth: 220 }}
            >
              {SOURCE_FAMILY_OPTIONS.map(([value, label]) => (
                <MenuItem key={value || "all"} value={value}>
                  {label}
                </MenuItem>
              ))}
            </TextField>
            <Button startIcon={<SearchIcon />} type="submit" variant="contained">
              Search
            </Button>
          </Stack>
          <QueryStateNotice
            error={results.error}
            refreshing={results.refreshing}
          />
          <Alert severity="info" variant="outlined">
            Results route back to reviewed record surfaces and stay subordinate to backend lifecycle records.
          </Alert>
          <RecordSearchTable records={results.data ?? []} />
        </Stack>
      )}
    </PageFrame>
  );
}
