import { Stack, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { PromoteAlertToCaseCard } from "../../taskActions/caseworkActionCards";
import { CaseDetailPageBody } from "./caseDetailSurfaces";
import {
  asRecord,
  asRecordArray,
  asString,
  AuditedRouteButton,
  EmptyState,
  ErrorState,
  formatValue,
  getPath,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  RecordWarnings,
  SectionCard,
  StatusStrip,
  SubordinateLinks,
  type UnknownRecord,
  useOperatorRecord,
  ValueList,
} from "./shared";

function AlertDetailPageBody({
  alertId,
  operatorIdentity,
}: {
  alertId: string;
  operatorIdentity: string;
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord("alerts", alertId, recordMeta);

  if (loading && !data) {
    return <LoadingState label="Loading alert detail" />;
  }

  if (error && !data) {
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
      <QueryStateNotice error={error} refreshing={refreshing} />
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
            <AuditedRouteButton
              label="Open case detail"
              to={`/operator/cases/${String(caseRecord.case_id)}`}
            >
              Open case detail
            </AuditedRouteButton>
          ) : null}
          <AuditedRouteButton
            label="Open assistant advisory"
            to={`/operator/assistant/alert/${alertId}`}
          >
            Open assistant advisory
          </AuditedRouteButton>
          <AuditedRouteButton
            label="Open provenance"
            to={`/operator/provenance/alerts/${alertId}`}
          >
            Open provenance
          </AuditedRouteButton>
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
            ["Current action review", getPath(data, "current_action_review.review_state")],
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
        <SubordinateLinks
          records={[...evidenceRecords, reconciliationRecord].filter(
            (record): record is UnknownRecord => record !== null,
          )}
        />
      </SectionCard>

      <PromoteAlertToCaseCard
        alertId={alertId}
        key={alertId}
        currentCaseId={asString(caseRecord?.case_id)}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />
    </Stack>
  );
}

export function AlertDetailPage({
  operatorIdentity,
}: {
  operatorIdentity: string;
}) {
  const params = useParams();
  const alertId = asString(params.alertId);

  return (
    <PageFrame
      subtitle="Read-only alert inspection keeps authoritative anchors, provenance, and subordinate evidence context explicitly separated."
      title="Alert Detail"
    >
      {alertId ? (
        <AlertDetailPageBody alertId={alertId} operatorIdentity={operatorIdentity} />
      ) : (
        <ErrorState error={new Error("Missing alert identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}

export function CaseDetailPage({
  operatorIdentity,
}: {
  operatorIdentity: string;
}) {
  const params = useParams();
  const caseId = asString(params.caseId);

  return (
    <PageFrame
      subtitle="Read-only case inspection keeps authoritative lifecycle state primary and preserves subordinate evidence lineage as secondary context."
      title="Case Detail"
    >
      {caseId ? (
        <CaseDetailPageBody caseId={caseId} operatorIdentity={operatorIdentity} />
      ) : (
        <ErrorState error={new Error("Missing case identifier in the operator route.")} />
      )}
    </PageFrame>
  );
}
