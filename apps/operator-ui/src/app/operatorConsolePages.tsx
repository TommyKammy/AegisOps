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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import { Link as ReactRouterLink, useParams } from "react-router-dom";
import { useDataProvider } from "react-admin";

type UnknownRecord = Record<string, unknown>;

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

function asRecord(value: unknown): UnknownRecord | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as UnknownRecord;
}

function asRecordArray(value: unknown): UnknownRecord[] {
  return Array.isArray(value)
    ? value.map((entry) => asRecord(entry)).filter((entry): entry is UnknownRecord => entry !== null)
    : [];
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value
        .map((entry) => asString(entry))
        .filter((entry): entry is string => entry !== null)
    : [];
}

function getPath(record: UnknownRecord | null, path: string): unknown {
  if (record === null) {
    return undefined;
  }

  return path.split(".").reduce<unknown>((value, segment) => {
    const next = asRecord(value);
    return next?.[segment];
  }, record);
}

function formatLabel(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not available";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const flattened = value
      .map((entry) => formatValue(entry))
      .filter((entry) => entry !== "Not available");
    return flattened.length > 0 ? flattened.join(", ") : "Not available";
  }

  return JSON.stringify(value);
}

function statusTone(
  status: string | null,
): "default" | "error" | "info" | "success" | "warning" {
  if (status === null) {
    return "default";
  }

  const normalized = status.toLowerCase();
  if (
    normalized.includes("failed") ||
    normalized.includes("forbidden") ||
    normalized.includes("mismatch") ||
    normalized.includes("missing") ||
    normalized.includes("rejected")
  ) {
    return "error";
  }
  if (
    normalized.includes("degraded") ||
    normalized.includes("pending") ||
    normalized.includes("delayed") ||
    normalized.includes("expired")
  ) {
    return "warning";
  }
  if (
    normalized.includes("matched") ||
    normalized.includes("healthy") ||
    normalized.includes("ready") ||
    normalized.includes("open")
  ) {
    return "success";
  }
  if (normalized.includes("review") || normalized.includes("triage")) {
    return "info";
  }

  return "default";
}

function useOperatorList(
  resource: string,
  filter: Record<string, unknown>,
  sort: { field: string; order: "ASC" | "DESC" },
  perPage = 25,
): QueryState<UnknownRecord[]> {
  const dataProvider = useDataProvider();
  const [state, setState] = useState<QueryState<UnknownRecord[]>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let active = true;

    setState({
      data: null,
      error: null,
      loading: true,
    });

    void dataProvider
      .getList(resource, {
        filter,
        pagination: {
          page: 1,
          perPage,
        },
        sort,
      })
      .then((result) => {
        if (!active) {
          return;
        }
        setState({
          data: result.data.map((record) => record as UnknownRecord),
          error: null,
          loading: false,
        });
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setState({
          data: null,
          error: error instanceof Error ? error : new Error("Unknown operator list error."),
          loading: false,
        });
      });

    return () => {
      active = false;
    };
  }, [dataProvider, filter, perPage, resource, sort]);

  return state;
}

function useOperatorRecord(
  resource: string,
  id: string,
  meta?: Record<string, unknown>,
): QueryState<UnknownRecord> {
  const dataProvider = useDataProvider();
  const [state, setState] = useState<QueryState<UnknownRecord>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let active = true;

    setState({
      data: null,
      error: null,
      loading: true,
    });

    void dataProvider
      .getOne(resource, { id, meta })
      .then((result) => {
        if (!active) {
          return;
        }
        setState({
          data: result.data as UnknownRecord,
          error: null,
          loading: false,
        });
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setState({
          data: null,
          error: error instanceof Error ? error : new Error("Unknown operator record error."),
          loading: false,
        });
      });

    return () => {
      active = false;
    };
  }, [dataProvider, id, meta, resource]);

  return state;
}

function PageFrame({
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

function LoadingState({ label }: { label: string }) {
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

function ErrorState({ error }: { error: Error }) {
  return (
    <Alert severity="error" variant="outlined">
      {error.message}
    </Alert>
  );
}

function SectionCard({
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

function ValueList({
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

function StatusStrip({
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

function EmptyState({ message }: { message: string }) {
  return (
    <Alert severity="info" variant="outlined">
      {message}
    </Alert>
  );
}

function RecordWarnings({ record }: { record: UnknownRecord }) {
  const warnings: string[] = [];
  const reviewState = asString(record.review_state);
  const externalTicketStatus = asString(getPath(record, "external_ticket_reference.status"));

  if (reviewState !== null && ["degraded", "rejected", "missing_anchor", "mismatch"].includes(reviewState)) {
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
        <Alert icon={<ReportProblemOutlinedIcon fontSize="inherit" />} key={warning} severity="warning" variant="outlined">
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
    if (href && /^https?:\/\//.test(href)) {
      entries.push({
        href,
        label: formatLabel(key),
      });
    }
  }

  return entries;
}

function SubordinateLinks({ records }: { records: UnknownRecord[] }) {
  const links = records.flatMap((record) => extractSubordinateLinks(record));

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

export function QueuePage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "last_seen_at",
      order: "DESC" as const,
    }),
    [],
  );
  const { data, error, loading } = useOperatorList("queue", filter, sort);

  return (
    <PageFrame
      subtitle="Primary review surface; substrate links stay secondary. AegisOps queue records remain the authoritative selection surface for operator review."
      title="Analyst Queue"
    >
      {loading ? <LoadingState label="Loading analyst queue" /> : null}
      {error ? <ErrorState error={error} /> : null}
      {data ? (
        data.length > 0 ? (
          <SectionCard
            subtitle="Explicit degraded, pending, and mismatch states remain visible instead of being smoothed away."
            title="Queue records"
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Alert</TableCell>
                  <TableCell>Review state</TableCell>
                  <TableCell>Case</TableCell>
                  <TableCell>Source family</TableCell>
                  <TableCell>Action review</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((record) => {
                  const alertId = asString(record.alert_id) ?? "Unknown alert";
                  const caseId = asString(record.case_id);
                  const sourceFamily = asString(
                    getPath(record, "reviewed_context.source.source_family"),
                  );
                  const actionReviewState = asString(
                    getPath(record, "current_action_review.review_state"),
                  );
                  return (
                    <TableRow hover key={String(record.id ?? alertId)}>
                      <TableCell>
                        <Stack spacing={0.75}>
                          <Link
                            component={ReactRouterLink}
                            to={`/operator/alerts/${alertId}`}
                            underline="hover"
                          >
                            {alertId}
                          </Link>
                          <Typography color="text.secondary" variant="caption">
                            {formatValue(record.queue_selection)}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <StatusStrip values={[["Review", asString(record.review_state)]]} />
                      </TableCell>
                      <TableCell>
                        {caseId ? (
                          <Link
                            component={ReactRouterLink}
                            to={`/operator/cases/${caseId}`}
                            underline="hover"
                          >
                            {caseId}
                          </Link>
                        ) : (
                          <Typography color="text.secondary" variant="body2">
                            No case anchor
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{sourceFamily ?? "Not available"}</TableCell>
                      <TableCell>{actionReviewState ?? "No active review"}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </SectionCard>
        ) : (
          <EmptyState message="The reviewed analyst queue is empty." />
        )
      ) : null}

      {data?.map((record) => (
        <SectionCard
          key={`queue-summary-${String(record.id ?? record.alert_id)}`}
          subtitle="AegisOps-owned queue state stays primary. Subordinate source hints remain secondary below it."
          title={`Queue summary: ${formatValue(record.alert_id)}`}
        >
          <StatusStrip
            values={[
              ["Review", asString(record.review_state)],
              ["Case", asString(record.case_lifecycle_state)],
              ["Escalation", asString(record.escalation_boundary)],
              [
                "Action review",
                asString(getPath(record, "current_action_review.review_state")),
              ],
            ]}
          />
          <RecordWarnings record={record} />
          <ValueList
            entries={[
              ["Accountable identities", asStringArray(record.accountable_source_identities)],
              ["Subordinate detection ids", asStringArray(record.substrate_detection_record_ids)],
              ["Correlation key", record.correlation_key],
            ]}
          />
        </SectionCard>
      ))}
    </PageFrame>
  );
}

function AlertDetailPageBody({ alertId }: { alertId: string }) {
  const { data, error, loading } = useOperatorRecord("alerts", alertId);

  if (loading) {
    return <LoadingState label="Loading alert detail" />;
  }

  if (error) {
    return <ErrorState error={error} />;
  }

  if (!data) {
    return <EmptyState message="Alert detail is unavailable." />;
  }

  const alertRecord = asRecord(data.alert);
  const caseRecord = asRecord(data.case_record);
  const lineage = asRecord(data.lineage);
  const evidenceRecords = asRecordArray(data.linked_evidence_records);
  const reconciliationRecord = asRecord(data.latest_reconciliation);

  return (
    <Stack spacing={3}>
      <SectionCard
        subtitle="Authoritative anchor records stay primary even when subordinate substrate context disagrees or is missing."
        title="Authoritative anchor"
      >
        <StatusStrip
          values={[
            ["Lifecycle", asString(alertRecord?.lifecycle_state)],
            ["Review", asString(data.review_state)],
            ["Escalation", asString(data.escalation_boundary)],
          ]}
        />
        <RecordWarnings record={data} />
        <ValueList
          entries={[
            ["Alert id", alertRecord?.alert_id ?? data.alert_id],
            ["Case id", caseRecord?.case_id],
            ["Finding id", lineage?.finding_id],
            ["Analytic signal", lineage?.analytic_signal_id],
          ]}
        />
        <Stack direction="row" gap={1}>
          {caseRecord?.case_id ? (
            <Button
              component={ReactRouterLink}
              endIcon={<LaunchOutlinedIcon />}
              to={`/operator/cases/${String(caseRecord.case_id)}`}
              variant="outlined"
            >
              Open case detail
            </Button>
          ) : null}
          <Button
            component={ReactRouterLink}
            endIcon={<LaunchOutlinedIcon />}
            to={`/operator/provenance/alerts/${alertId}`}
            variant="outlined"
          >
            Open provenance
          </Button>
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Admission path and authoritative lineage stay explicit. Missing or partial linkage is not hidden."
        title="Provenance"
      >
        <ValueList
          entries={[
            ["Admission kind", getPath(data, "provenance.admission_kind")],
            ["Admission channel", getPath(data, "provenance.admission_channel")],
            ["Source system", data.source_system],
            ["Source families", lineage?.source_systems],
            ["Accountable identities", lineage?.accountable_source_identities],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="These surfaces stay secondary to the authoritative alert record and preserve mismatches instead of smoothing them away."
        title="Subordinate evidence context"
      >
        <ValueList
          entries={[
            ["Latest reconciliation", reconciliationRecord?.reconciliation_id],
            ["Detection ids", lineage?.substrate_detection_record_ids],
            ["Evidence ids", lineage?.evidence_ids],
            [
              "Current action review",
              getPath(data, "current_action_review.review_state"),
            ],
          ]}
        />
        {evidenceRecords.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Evidence</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Relationship</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {evidenceRecords.map((record) => (
                <TableRow key={String(record.evidence_id)}>
                  <TableCell>{formatValue(record.evidence_id)}</TableCell>
                  <TableCell>{formatValue(record.source_system)}</TableCell>
                  <TableCell>{formatValue(record.derivation_relationship)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No subordinate evidence records were linked." />
        )}
        <SubordinateLinks records={[...evidenceRecords, reconciliationRecord].filter((record): record is UnknownRecord => record !== null)} />
      </SectionCard>
    </Stack>
  );
}

export function AlertDetailPage() {
  const params = useParams();
  const alertId = asString(params.alertId);

  return (
    <PageFrame
      subtitle="Read-only alert inspection keeps authoritative anchors, provenance, and subordinate evidence context explicitly separated."
      title="Alert Detail"
    >
      {alertId ? (
        <AlertDetailPageBody alertId={alertId} />
      ) : (
        <ErrorState error={new Error("Missing alert identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}

function CaseDetailPageBody({ caseId }: { caseId: string }) {
  const { data, error, loading } = useOperatorRecord("cases", caseId);

  if (loading) {
    return <LoadingState label="Loading case detail" />;
  }

  if (error) {
    return <ErrorState error={error} />;
  }

  if (!data) {
    return <EmptyState message="Case detail is unavailable." />;
  }

  const caseRecord = asRecord(data.case_record);
  const provenanceSummary = asRecord(data.provenance_summary);
  const authoritativeAnchor = asRecord(getPath(provenanceSummary, "authoritative_anchor"));
  const reconciliationRecords = asRecordArray(data.linked_reconciliation_records);
  const alertRecords = asRecordArray(data.linked_alert_records);
  const evidenceRecords = asRecordArray(data.linked_evidence_records);
  const timelineEntries = asRecordArray(data.cross_source_timeline);

  return (
    <Stack spacing={3}>
      <SectionCard
        subtitle="Case lifecycle state and linked identifiers come from the authoritative AegisOps case record, not from summaries or substrate convenience surfaces."
        title="Authoritative anchor"
      >
        <StatusStrip
          values={[
            ["Lifecycle", asString(caseRecord?.lifecycle_state)],
            ["Current action review", asString(getPath(data, "current_action_review.review_state"))],
            ["Coordination reference", asString(getPath(data, "external_ticket_reference.status"))],
          ]}
        />
        <RecordWarnings record={data} />
        <ValueList
          entries={[
            ["Case id", caseRecord?.case_id ?? data.case_id],
            ["Alert ids", data.linked_alert_ids],
            ["Observation ids", data.linked_observation_ids],
            ["Recommendation ids", data.linked_recommendation_ids],
          ]}
        />
        <Stack direction="row" gap={1}>
          <Button
            component={ReactRouterLink}
            endIcon={<LaunchOutlinedIcon />}
            to={`/operator/provenance/cases/${caseId}`}
            variant="outlined"
          >
            Open provenance
          </Button>
        </Stack>
      </SectionCard>

      <SectionCard
        subtitle="Cross-source lineage stays anchored to the reviewed case record. Only directly linked context is pulled into this surface."
        title="Provenance summary"
      >
        <ValueList
          entries={[
            ["Anchor record family", authoritativeAnchor?.record_family],
            ["Anchor record id", authoritativeAnchor?.record_id],
            ["Anchor source family", authoritativeAnchor?.source_family],
            ["Provenance classification", authoritativeAnchor?.provenance_classification],
            ["Linked evidence ids", data.linked_evidence_ids],
            ["Linked reconciliation ids", data.linked_reconciliation_ids],
          ]}
        />
      </SectionCard>

      <SectionCard
        subtitle="Subordinate alert, evidence, and reconciliation context stays visible but secondary to the authoritative case state."
        title="Subordinate evidence context"
      >
        <ValueList
          entries={[
            ["Alert records", alertRecords.length],
            ["Evidence records", evidenceRecords.length],
            ["Reconciliation records", reconciliationRecords.length],
          ]}
        />
        {timelineEntries.length > 0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Record family</TableCell>
                <TableCell>Record id</TableCell>
                <TableCell>Source family</TableCell>
                <TableCell>Classification</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timelineEntries.map((entry, index) => (
                <TableRow key={`${String(entry.record_id ?? index)}-${index}`}>
                  <TableCell>{formatValue(entry.record_family)}</TableCell>
                  <TableCell>{formatValue(entry.record_id)}</TableCell>
                  <TableCell>{formatValue(entry.source_family)}</TableCell>
                  <TableCell>{formatValue(entry.provenance_classification)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState message="No subordinate cross-source timeline entries were returned." />
        )}
        <SubordinateLinks
          records={[
            ...alertRecords,
            ...evidenceRecords,
            ...reconciliationRecords,
          ]}
        />
      </SectionCard>
    </Stack>
  );
}

export function CaseDetailPage() {
  const params = useParams();
  const caseId = asString(params.caseId);

  return (
    <PageFrame
      subtitle="Read-only case inspection keeps authoritative lifecycle state primary and preserves subordinate evidence lineage as secondary context."
      title="Case Detail"
    >
      {caseId ? (
        <CaseDetailPageBody caseId={caseId} />
      ) : (
        <ErrorState error={new Error("Missing case identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}

function ProvenanceAlertBody({ alertId }: { alertId: string }) {
  const { data, error, loading } = useOperatorRecord("alerts", alertId);

  if (loading) {
    return <LoadingState label="Loading alert provenance" />;
  }
  if (error) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Alert provenance is unavailable." />;
  }

  const lineage = asRecord(data.lineage);

  return (
    <SectionCard
      subtitle="This page is provenance-focused but still anchored to the reviewed alert record rather than to substrate-native summaries."
      title="Alert provenance"
    >
      <ValueList
        entries={[
          ["Alert id", data.alert_id],
          ["Reconciliation id", lineage?.reconciliation_id],
          ["Detection ids", lineage?.substrate_detection_record_ids],
          ["Accountable identities", lineage?.accountable_source_identities],
          ["First seen", lineage?.first_seen_at],
          ["Last seen", lineage?.last_seen_at],
        ]}
      />
    </SectionCard>
  );
}

function ProvenanceCaseBody({ caseId }: { caseId: string }) {
  const { data, error, loading } = useOperatorRecord("cases", caseId);

  if (loading) {
    return <LoadingState label="Loading case provenance" />;
  }
  if (error) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Case provenance is unavailable." />;
  }

  const provenanceSummary = asRecord(data.provenance_summary);
  const authoritativeAnchor = asRecord(getPath(provenanceSummary, "authoritative_anchor"));

  return (
    <SectionCard
      subtitle="Only directly linked case lineage is shown here. Neighbor or sibling lineage is not widened by inference."
      title="Case provenance"
    >
      <ValueList
        entries={[
          ["Case id", data.case_id],
          ["Anchor family", authoritativeAnchor?.record_family],
          ["Anchor id", authoritativeAnchor?.record_id],
          ["Anchor source family", authoritativeAnchor?.source_family],
          ["Linked reconciliation ids", data.linked_reconciliation_ids],
          ["Linked evidence ids", data.linked_evidence_ids],
        ]}
      />
    </SectionCard>
  );
}

export function ProvenancePage() {
  const params = useParams();
  const family = asString(params.family);
  const recordId = asString(params.recordId);

  return (
    <PageFrame
      subtitle="Provenance stays a dedicated inspection surface so anchor linkage, lineage, and subordinate context can be reviewed without collapsing them together."
      title="Provenance"
    >
      {family === "alerts" && recordId ? <ProvenanceAlertBody alertId={recordId} /> : null}
      {family === "cases" && recordId ? <ProvenanceCaseBody caseId={recordId} /> : null}
      {(family !== "alerts" && family !== "cases") || recordId === null ? (
        <ErrorState error={new Error("Unsupported provenance route. Use alerts or cases with an authoritative identifier.")} />
      ) : null}
    </PageFrame>
  );
}

export function ReadinessPage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "status",
      order: "ASC" as const,
    }),
    [],
  );
  const { data, error, loading } = useOperatorList("runtimeReadiness", filter, sort, 1);

  const record = data?.[0] ?? null;
  const reviewPathHealth = asRecord(getPath(record, "metrics.review_path_health"));
  const sourceHealth = asRecord(getPath(record, "metrics.source_health"));
  const automationHealth = asRecord(getPath(record, "metrics.automation_substrate_health"));

  return (
    <PageFrame
      subtitle="Readiness remains a reviewed status surface. It does not become a hidden write console or override authoritative backend state."
      title="Readiness"
    >
      {loading ? <LoadingState label="Loading readiness diagnostics" /> : null}
      {error ? <ErrorState error={error} /> : null}
      {record ? (
        <Stack spacing={3}>
          <SectionCard
            subtitle="Degraded or missing prerequisite signals remain explicit here."
            title="Readiness status"
          >
            <StatusStrip
              values={[
                ["Status", asString(record.status)],
                ["Booted", String(formatValue(record.booted))],
                ["Startup", String(formatValue(getPath(record, "startup.startup_ready")))],
                ["Shutdown", String(formatValue(getPath(record, "shutdown.shutdown_ready")))],
              ]}
            />
            <ValueList
              entries={[
                ["Persistence mode", record.persistence_mode],
                ["Latest reconciliation", getPath(record, "latest_reconciliation.reconciliation_id")],
                ["Action requests approved", getPath(record, "metrics.action_requests.approved")],
                ["Terminal executions", getPath(record, "metrics.action_executions.terminal")],
              ]}
            />
          </SectionCard>
          <SectionCard
            subtitle="Operator-facing health summaries are derived surfaces and stay subordinate to the authoritative diagnostic payload."
            title="Diagnostic breakdown"
          >
            <ValueList
              entries={[
                ["Review path overall state", reviewPathHealth?.overall_state],
                ["Review count", reviewPathHealth?.review_count],
                ["Tracked sources", sourceHealth?.tracked_sources],
                ["Tracked automation surfaces", automationHealth?.tracked_surfaces],
              ]}
            />
          </SectionCard>
        </Stack>
      ) : null}
    </PageFrame>
  );
}

export function ReconciliationPage() {
  const filter = useMemo(() => ({}), []);
  const sort = useMemo(
    () => ({
      field: "latest_compared_at",
      order: "DESC" as const,
    }),
    [],
  );
  const { data, error, loading } = useOperatorList("reconciliations", filter, sort);

  return (
    <PageFrame
      subtitle="Reconciliation surfaces keep mismatch and linkage problems visible instead of collapsing them into generic success dashboards."
      title="Reconciliation"
    >
      {loading ? <LoadingState label="Loading reconciliation status" /> : null}
      {error ? <ErrorState error={error} /> : null}
      {data ? (
        data.length > 0 ? (
          <Stack spacing={3}>
            <SectionCard
              subtitle="Records are sorted from the latest comparison so unresolved mismatches stay visible first."
              title="Reconciliation records"
            >
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Reconciliation</TableCell>
                    <TableCell>Lifecycle</TableCell>
                    <TableCell>Ingest disposition</TableCell>
                    <TableCell>Mismatch summary</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.map((record) => (
                    <TableRow key={String(record.id ?? record.reconciliation_id)}>
                      <TableCell>{formatValue(record.reconciliation_id)}</TableCell>
                      <TableCell>{formatValue(record.lifecycle_state)}</TableCell>
                      <TableCell>{formatValue(record.ingest_disposition)}</TableCell>
                      <TableCell>{formatValue(record.mismatch_summary)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </SectionCard>
            {data.map((record) => (
              <SectionCard
                key={`reconciliation-${String(record.id ?? record.reconciliation_id)}`}
                subtitle="Authoritative reconciliation state stays primary. Subject linkage remains subordinate context and is shown without payload expansion."
                title={`Reconciliation detail: ${formatValue(record.reconciliation_id)}`}
              >
                <StatusStrip
                  values={[
                    ["Lifecycle", asString(record.lifecycle_state)],
                    ["Disposition", asString(record.ingest_disposition)],
                  ]}
                />
                <ValueList
                  entries={[
                    ["Compared at", record.compared_at],
                    ["Latest compared at", record.latest_compared_at],
                    ["Mismatch summary", record.mismatch_summary],
                    ["Subject linkage", record.subject_linkage],
                  ]}
                />
              </SectionCard>
            ))}
          </Stack>
        ) : (
          <EmptyState message="No reconciliation records are currently available." />
        )
      ) : null}
    </PageFrame>
  );
}
