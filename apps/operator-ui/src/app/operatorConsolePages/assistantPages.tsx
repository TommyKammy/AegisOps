import {
  Alert,
  Card,
  CardContent,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  AdvisoryContextList,
  advisoryContextEntries,
  advisoryDetailRows,
  advisoryRecommendations,
  advisorySummary,
  advisoryUncertaintyLabel,
  advisoryUncertaintyMessage,
  asString,
  asStringArray,
  AuditedRouteButton,
  EmptyState,
  ErrorState,
  formatLabel,
  formatValue,
  LoadingState,
  PageFrame,
  QueryStateNotice,
  SectionCard,
  StatusStrip,
  supportedAnchorRoute,
  SUPPORTED_ADVISORY_RECORD_FAMILIES,
  type UnknownRecord,
  useOperatorRecord,
  ValueList,
} from "./shared";

function AdvisoryDetailTable({ record }: { record: UnknownRecord }) {
  const rows = advisoryDetailRows(record);

  if (rows.length === 0) {
    return <EmptyState message="No additional advisory fields were returned for this record." />;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Field</TableCell>
          <TableCell>Value</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map(([key, value]) => (
          <TableRow key={key}>
            <TableCell>{formatLabel(key)}</TableCell>
            <TableCell>{formatValue(value)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function AssistantAdvisoryPageBody({
  recordFamily,
  recordId,
}: {
  recordFamily: string;
  recordId: string;
}) {
  const advisoryId = `${recordFamily}:${recordId}`;
  const meta = useMemo(
    () => ({
      recordFamily,
      recordId,
    }),
    [recordFamily, recordId],
  );
  const { data, error, loading, refreshing } = useOperatorRecord(
    "advisoryOutput",
    advisoryId,
    meta,
  );
  const anchorLink = supportedAnchorRoute(recordFamily, recordId);

  if (loading && !data) {
    return <LoadingState label="Loading assistant advisory" />;
  }
  if (error && !data) {
    return <ErrorState error={error} />;
  }
  if (!data) {
    return <EmptyState message="Assistant advisory is unavailable." />;
  }

  const summary = advisorySummary(data);
  const recommendationDrafts = advisoryRecommendations(data).filter(
    (entry): entry is { citations: string[]; text: string } => entry.text !== null,
  );
  const keyObservations = advisoryContextEntries(data, "key_observations");
  const unresolvedQuestions = advisoryContextEntries(data, "unresolved_questions");
  const citations = asStringArray(data.citations);
  const uncertaintyFlags = asStringArray(data.uncertainty_flags);
  const showsRecommendationDraft =
    asString(data.output_kind) === "recommendation_draft" || recommendationDrafts.length > 0;
  const hasCitationFailure =
    uncertaintyFlags.includes("missing_supporting_citations") ||
    uncertaintyFlags.includes("missing_evidence_citation");
  const hasUnresolvedState = asString(data.status) === "unresolved";
  const hasReviewedContextConflict = uncertaintyFlags.includes("conflicting_reviewed_context");
  const hasFailureVisibility =
    hasCitationFailure || hasUnresolvedState || hasReviewedContextConflict;

  return (
    <Stack spacing={3}>
      <QueryStateNotice error={error} refreshing={refreshing} />
      <SectionCard
        subtitle="Assistant output stays subordinate to the selected authoritative record and remains read-only inside the reviewed shell."
        title="Authoritative advisory anchor"
      >
        <StatusStrip
          values={[
            ["Status", asString(data.status)],
            ["Output", asString(data.output_kind)],
          ]}
        />
        <ValueList
          entries={[
            ["Record family", asString(data.record_family) ?? recordFamily],
            ["Record id", asString(data.record_id) ?? recordId],
            ["Read only", formatValue(data.read_only)],
          ]}
        />
        {anchorLink ? (
          <AuditedRouteButton label={anchorLink.label} to={anchorLink.to}>
            {anchorLink.label}
          </AuditedRouteButton>
        ) : null}
        <Alert severity="warning" variant="outlined">
          Assistant output does not approve, execute, or reconcile workflow state.
        </Alert>
      </SectionCard>

      {hasFailureVisibility ? (
        <SectionCard
          subtitle="Citation failures, unresolved grounding, and reviewed-context conflicts stay explicit instead of being normalized into a cleaner assistant summary."
          title="Advisory failure visibility"
        >
          <Stack spacing={2}>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {uncertaintyFlags.map((flag) => (
                <Chip
                  color={flag === "advisory_only" ? "warning" : "error"}
                  key={flag}
                  label={advisoryUncertaintyLabel(flag)}
                  size="small"
                  variant={flag === "advisory_only" ? "outlined" : "filled"}
                />
              ))}
            </Stack>
            {hasUnresolvedState ? (
              <Alert severity="error" variant="outlined">
                Assistant advisory remains unresolved because required citation or reviewed-context checks failed.
              </Alert>
            ) : null}
            {hasCitationFailure ? (
              <Alert severity="error" variant="outlined">
                Missing citation support is visible here so uncited assistant prose does not resemble reviewed workflow truth.
              </Alert>
            ) : null}
            {hasReviewedContextConflict ? (
              <Alert severity="warning" variant="outlined">
                Conflicting reviewed context remains visible here; the browser does not silently pick one record as authoritative support for assistant output.
              </Alert>
            ) : null}
            <Stack spacing={1}>
              {uncertaintyFlags.map((flag) => (
                <Alert
                  key={`uncertainty-${flag}`}
                  severity={
                    flag === "advisory_only"
                      ? "info"
                      : flag === "conflicting_reviewed_context"
                        ? "warning"
                        : "error"
                  }
                  variant="outlined"
                >
                  {advisoryUncertaintyMessage(flag)}
                </Alert>
              ))}
            </Stack>
          </Stack>
        </SectionCard>
      ) : null}

      <SectionCard
        subtitle="Citation-led assistant output stays visibly subordinate to the authoritative anchor and remains advisory only."
        title="Cited advisory output"
      >
        {summary.text ? (
          <Stack spacing={2}>
            <Alert
              severity={hasCitationFailure || hasUnresolvedState ? "warning" : "info"}
              variant="outlined"
            >
              {summary.text}
            </Alert>
            {summary.citations.length > 0 ? (
              <Stack direction="row" flexWrap="wrap" gap={1}>
                {summary.citations.map((citation) => (
                  <Chip key={citation} label={citation} size="small" variant="outlined" />
                ))}
              </Stack>
            ) : (
              <EmptyState message="No cited summary anchors were returned for this advisory output." />
            )}
          </Stack>
        ) : (
          <EmptyState message="No assistant summary text was returned for this record." />
        )}
      </SectionCard>

      <SectionCard
        subtitle="Reviewed context, linked evidence, and unresolved grounding questions stay inspectable here instead of collapsing into a cleaner assistant answer."
        title="Assistant context explorer"
      >
        <Stack spacing={3}>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Reviewed context</Typography>
            <AdvisoryContextList
              emptyMessage="No reviewed context observations were returned for this advisory output."
              entries={keyObservations}
            />
          </Stack>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Unresolved grounding</Typography>
            <AdvisoryContextList
              emptyMessage="No unresolved grounding questions were returned for this advisory output."
              entries={unresolvedQuestions}
            />
          </Stack>
        </Stack>
      </SectionCard>

      {showsRecommendationDraft ? (
        <SectionCard
          subtitle="Recommendation proposals remain explicit assistant drafts and do not replace reviewed workflow state."
          title="Recommendation draft"
        >
          <Stack spacing={2}>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              <Chip color="warning" label="Draft only" size="small" />
              {uncertaintyFlags.map((flag) => (
                <Chip key={flag} label={formatLabel(flag)} size="small" variant="outlined" />
              ))}
            </Stack>
            <Alert severity="warning" variant="outlined">
              Assistant output does not approve, execute, or reconcile workflow state.
            </Alert>
            {recommendationDrafts.length > 0 ? (
              <Stack spacing={2}>
                {recommendationDrafts.map((draft, index) => (
                  <Card
                    elevation={0}
                    key={`${draft.text}-${index}`}
                    sx={{ border: "1px solid", borderColor: "divider" }}
                  >
                    <CardContent>
                      <Stack spacing={2}>
                        <Typography variant="body1">{draft.text}</Typography>
                        {draft.citations.length > 0 ? (
                          <Stack direction="row" flexWrap="wrap" gap={1}>
                            {draft.citations.map((citation) => (
                              <Chip
                                key={`${draft.text}-${citation}`}
                                label={citation}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Stack>
                        ) : (
                          <EmptyState message="This recommendation draft did not include supporting citations." />
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            ) : (
              <EmptyState message="No recommendation draft proposals were returned for this advisory output." />
            )}
          </Stack>
        </SectionCard>
      ) : null}

      <SectionCard
        subtitle="Evidence citations stay visible as directly linked support for this advisory output."
        title="Evidence anchors"
      >
        {citations.length > 0 ? (
          <Stack direction="row" flexWrap="wrap" gap={1}>
            {citations.map((citation) => (
              <Chip key={citation} label={citation} size="small" variant="outlined" />
            ))}
          </Stack>
        ) : (
          <EmptyState message="No advisory citations were returned for this record." />
        )}
      </SectionCard>

      <SectionCard
        subtitle="Additional reviewed advisory fields remain readable here until richer advisory-specific rendering lands."
        title="Advisory detail"
      >
        <AdvisoryDetailTable record={data} />
      </SectionCard>
    </Stack>
  );
}

export function AssistantAdvisoryPage() {
  const params = useParams();
  const recordFamily = asString(params.recordFamily);
  const recordId = asString(params.recordId);
  const hasSupportedAdvisoryBinding =
    recordFamily !== null && SUPPORTED_ADVISORY_RECORD_FAMILIES.has(recordFamily);

  return (
    <PageFrame
      subtitle="Assistant advisory stays a dedicated read surface anchored to one authoritative record. It does not become a generic assistant chat or mutable workflow console."
      title="Assistant Advisory"
    >
      {hasSupportedAdvisoryBinding && recordId ? (
        <AssistantAdvisoryPageBody recordFamily={recordFamily} recordId={recordId} />
      ) : (
        <>
          {recordFamily === null || recordId === null ? (
            <SectionCard
              subtitle="Open assistant advisory from alert, case, or action-review detail so the route stays grounded in one authoritative record."
              title="Select advisory context"
            >
              <EmptyState message="No authoritative record is selected for assistant advisory yet." />
            </SectionCard>
          ) : (
            <ErrorState
              error={
                new Error(
                  "Unsupported assistant advisory route. Use alert, case, recommendation, approval decision, or reconciliation with an authoritative identifier.",
                )
              }
            />
          )}
        </>
      )}
    </PageFrame>
  );
}
