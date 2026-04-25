import { Stack, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { useMemo, useState } from "react";
import { CreateReviewedActionRequestCard } from "../../taskActions/actionRequestActionCards";
import {
  RecordActionReviewEscalationNoteCard,
  RecordActionReviewManualFallbackCard,
} from "../../taskActions/actionReviewActionCards";
import {
  RecordCaseLeadCard,
  RecordCaseObservationCard,
  RecordCaseRecommendationCard,
} from "../../taskActions/caseworkActionCards";
import {
  asRecord,
  asRecordArray,
  asString,
  asStringArray,
  AuditedRouteButton,
  CoordinationVisibilitySection,
  EmptyState,
  ErrorState,
  formatValue,
  getPath,
  LoadingState,
  QueryStateNotice,
  RecordWarnings,
  SectionCard,
  StatusStrip,
  SubordinateLinks,
  type UnknownRecord,
  useOperatorRecord,
  ValueList,
} from "./shared";

export function CaseDetailPageBody({
  caseId,
  operatorIdentity,
}: {
  caseId: string;
  operatorIdentity: string;
}) {
  const [reloadToken, setReloadToken] = useState(0);
  const recordMeta = useMemo(() => ({ reloadToken }), [reloadToken]);
  const { data, error, loading, refreshing } = useOperatorRecord("cases", caseId, recordMeta);

  if (loading && !data) {
    return <LoadingState label="Loading case detail" />;
  }

  if (error && !data) {
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
  const currentActionReview = asRecord(data.current_action_review);
  const linkedEvidenceIds = asStringArray(data.linked_evidence_ids);
  const linkedObservationIds = asStringArray(data.linked_observation_ids);
  const linkedLeadIds = asStringArray(data.linked_lead_ids);
  const linkedRecommendationIds = asStringArray(data.linked_recommendation_ids);
  const currentActionRequestId = asString(currentActionReview?.action_request_id);
  const currentReviewState = asString(currentActionReview?.review_state);
  const nextExpectedAction = asString(currentActionReview?.next_expected_action);

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
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
            ["Current action request", currentActionRequestId],
            ["Alert ids", data.linked_alert_ids],
            ["Observation ids", data.linked_observation_ids],
            ["Lead ids", data.linked_lead_ids],
            ["Recommendation ids", data.linked_recommendation_ids],
          ]}
        />
        <Stack direction="row" gap={1}>
          {currentActionRequestId ? (
            <AuditedRouteButton
              label="Open action review"
              to={`/operator/action-review/${currentActionRequestId}`}
            >
              Open action review
            </AuditedRouteButton>
          ) : null}
          <AuditedRouteButton
            label="Open assistant advisory"
            to={`/operator/assistant/case/${caseId}`}
          >
            Open assistant advisory
          </AuditedRouteButton>
          <AuditedRouteButton
            label="Open provenance"
            to={`/operator/provenance/cases/${caseId}`}
          >
            Open provenance
          </AuditedRouteButton>
        </Stack>
      </SectionCard>

      <CoordinationVisibilitySection actionReview={currentActionReview} />

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
          records={[...alertRecords, ...evidenceRecords, ...reconciliationRecords]}
        />
      </SectionCard>

      <RecordCaseObservationCard
        caseId={caseId}
        key={`observation-${caseId}`}
        linkedEvidenceIds={linkedEvidenceIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      <RecordCaseLeadCard
        caseId={caseId}
        key={`lead-${caseId}`}
        linkedObservationIds={linkedObservationIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      <RecordCaseRecommendationCard
        caseId={caseId}
        key={`recommendation-${caseId}`}
        linkedLeadIds={linkedLeadIds}
        onSubmitted={() => {
          setReloadToken((current) => current + 1);
        }}
        operatorIdentity={operatorIdentity}
      />

      {linkedRecommendationIds.length > 0 ? (
        <CreateReviewedActionRequestCard
          caseId={caseId}
          key={`action-request-${caseId}`}
          linkedRecommendationIds={linkedRecommendationIds}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
        />
      ) : null}

      {currentActionRequestId ? (
        <RecordActionReviewManualFallbackCard
          actionRequestId={currentActionRequestId}
          caseId={caseId}
          key={`manual-fallback-${caseId}-${currentActionRequestId}`}
          linkedEvidenceIds={linkedEvidenceIds}
          nextExpectedAction={nextExpectedAction}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
          reviewState={currentReviewState}
        />
      ) : null}

      {currentActionRequestId ? (
        <RecordActionReviewEscalationNoteCard
          actionRequestId={currentActionRequestId}
          caseId={caseId}
          key={`escalation-note-${caseId}-${currentActionRequestId}`}
          nextExpectedAction={nextExpectedAction}
          onSubmitted={() => {
            setReloadToken((current) => current + 1);
          }}
          operatorIdentity={operatorIdentity}
          reviewState={currentReviewState}
        />
      ) : null}
    </Stack>
  );
}
