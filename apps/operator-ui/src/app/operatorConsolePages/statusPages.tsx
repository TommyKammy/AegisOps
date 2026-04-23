import { Stack, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  OptionalExtensionVisibilityPanel,
  buildOptionalEvidenceDefinitionsFromPayload,
} from "../optionalExtensionVisibility";
import {
  asRecord,
  asString,
  EmptyState,
  ErrorState,
  formatValue,
  getPath,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  SectionCard,
  StatusStrip,
  useOperatorList,
  useOperatorRecord,
  ValueList,
} from "./shared";

function ProvenanceAlertBody({ alertId }: { alertId: string }) {
  const { data, error, loading, refreshing } = useOperatorRecord("alerts", alertId);

  if (loading && !data) {
    return <LoadingState label="Loading alert provenance" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Alert provenance is unavailable." />;
  }

  const lineage = asRecord(data.lineage);

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
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
    </Stack>
  );
}

function ProvenanceCaseBody({ caseId }: { caseId: string }) {
  const { data, error, loading, refreshing } = useOperatorRecord("cases", caseId);

  if (loading && !data) {
    return <LoadingState label="Loading case provenance" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Case provenance is unavailable." />;
  }

  const provenanceSummary = asRecord(data.provenance_summary);
  const authoritativeAnchor = asRecord(getPath(provenanceSummary, "authoritative_anchor"));

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
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
    </Stack>
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
        <ErrorState
          error={
            new Error(
              "Unsupported provenance route. Use alerts or cases with an authoritative identifier.",
            )
          }
        />
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
  const { data, error, loading, refreshing } = useOperatorList(
    "runtimeReadiness",
    filter,
    sort,
    1,
  );

  const record = data?.[0] ?? null;
  const reviewPathHealth = asRecord(getPath(record, "metrics.review_path_health"));
  const sourceHealth = asRecord(getPath(record, "metrics.source_health"));
  const automationHealth = asRecord(getPath(record, "metrics.automation_substrate_health"));
  const optionalEvidenceDefinitions = buildOptionalEvidenceDefinitionsFromPayload(
    getPath(record, "metrics.optional_extensions"),
  );

  return (
    <PageFrame
      subtitle="Readiness remains a reviewed status surface. It does not become a hidden write console or override authoritative backend state."
      title="Readiness"
    >
      {loading && !record ? <LoadingState label="Loading readiness diagnostics" /> : null}
      {error && !record ? <ErrorState error={error} /> : null}
      {record ? <QueryStateNotice error={error} refreshing={refreshing} /> : null}
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
                [
                  "Latest reconciliation",
                  getPath(record, "latest_reconciliation.reconciliation_id"),
                ],
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
          <SectionCard
            subtitle="Optional endpoint and network evidence paths stay visibly subordinate to authoritative alerts, cases, evidence anchors, and workflow records."
            title="Optional evidence posture"
          >
            <OptionalExtensionVisibilityPanel definitions={optionalEvidenceDefinitions} />
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
  const { data, error, loading, refreshing } = useOperatorList("reconciliations", filter, sort);

  return (
    <PageFrame
      subtitle="Reconciliation surfaces keep mismatch and linkage problems visible instead of collapsing them into generic success dashboards."
      title="Reconciliation"
    >
      {loading && !data ? <LoadingState label="Loading reconciliation status" /> : null}
      {error && !data ? <ErrorState error={error} /> : null}
      {data ? <QueryStateNotice error={error} refreshing={refreshing} /> : null}
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
