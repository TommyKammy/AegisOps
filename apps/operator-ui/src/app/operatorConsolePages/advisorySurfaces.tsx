import { Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import {
  asRecord,
  asRecordArray,
  asString,
  asStringArray,
  formatLabel,
  type UnknownRecord,
} from "./recordUtils";
import { EmptyState } from "./pageChrome";

const ADVISORY_SUMMARY_FIELDS = ["summary", "message", "output_text", "advisory_text"] as const;
const ADVISORY_DETAIL_EXCLUDED_FIELDS = [
  "id",
  "record_family",
  "record_id",
  "output_kind",
  "status",
  "read_only",
  "cited_summary",
  "candidate_recommendations",
  "uncertainty_flags",
  "citations",
  ...ADVISORY_SUMMARY_FIELDS,
] as const;

export const SUPPORTED_ADVISORY_RECORD_FAMILIES = new Set([
  "alert",
  "case",
  "recommendation",
  "approval_decision",
  "reconciliation",
]);

export function advisorySummary(record: UnknownRecord) {
  const citedSummary = asRecord(record.cited_summary);
  const citedText = asString(citedSummary?.text);
  const citedCitations = asStringArray(citedSummary?.citations);
  const fallbackText =
    ADVISORY_SUMMARY_FIELDS.map((key) => asString(record[key])).find(
      (value): value is string => value !== null,
    ) ?? null;

  return {
    citations: citedText ? citedCitations : [],
    text: citedText ?? fallbackText,
  };
}

export function advisoryRecommendations(record: UnknownRecord) {
  return asRecordArray(record.candidate_recommendations).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

export function advisoryContextEntries(
  record: UnknownRecord,
  field: "key_observations" | "unresolved_questions",
) {
  return asRecordArray(record[field]).map((entry) => ({
    citations: asStringArray(entry.citations),
    text: asString(entry.text),
  }));
}

export function advisoryUncertaintyMessage(flag: string): string {
  switch (flag) {
    case "missing_supporting_citations":
      return "Required reviewed citations are missing, so this advisory output remains fail-closed.";
    case "missing_evidence_citation":
      return "Linked evidence citations required for this advisory output are missing.";
    case "conflicting_reviewed_context":
      return "Reviewed context conflicts remain unresolved and must stay visible before any operator action.";
    case "provider_generation_failed":
      return "The bounded assistant provider did not return a trusted summary, so the reviewed advisory remains unresolved.";
    case "ambiguous_identity_alias_only":
      return "Alias-style identity context is still unresolved; stable reviewed identifiers are still required.";
    case "reviewed_casework_identity_ambiguity":
      return "Reviewed casework identity ambiguity remains open across linked records and evidence.";
    case "scope_authority_pressure":
      return "Assistant output tried to imply scope or authority beyond the reviewed record boundary.";
    case "approval_authority_pressure":
      return "Assistant output must not imply approval authority.";
    case "execution_authority_pressure":
      return "Assistant output must not imply execution authority.";
    case "reconciliation_authority_pressure":
      return "Assistant output must not imply reconciliation authority.";
    case "advisory_only":
      return "Assistant output remains advisory-only and subordinate to the authoritative record.";
    default:
      return `${formatLabel(flag)} remains visible on this advisory output.`;
  }
}

export function advisoryUncertaintyLabel(flag: string): string {
  switch (flag) {
    case "missing_supporting_citations":
      return "Missing citation support";
    case "missing_evidence_citation":
      return "Missing evidence citation";
    case "conflicting_reviewed_context":
      return "Conflicting reviewed context";
    case "provider_generation_failed":
      return "Provider degraded";
    case "ambiguous_identity_alias_only":
      return "Alias-only identity ambiguity";
    case "reviewed_casework_identity_ambiguity":
      return "Reviewed casework identity ambiguity";
    case "scope_authority_pressure":
      return "Scope authority pressure";
    case "approval_authority_pressure":
      return "Approval authority pressure";
    case "execution_authority_pressure":
      return "Execution authority pressure";
    case "reconciliation_authority_pressure":
      return "Reconciliation authority pressure";
    case "advisory_only":
      return "Advisory only";
    default:
      return formatLabel(flag);
  }
}

export function advisoryDetailRows(record: UnknownRecord) {
  return Object.entries(record).filter(([key]) => {
    return !ADVISORY_DETAIL_EXCLUDED_FIELDS.includes(
      key as (typeof ADVISORY_DETAIL_EXCLUDED_FIELDS)[number],
    );
  });
}

export function AdvisoryContextList({
  entries,
  emptyMessage,
}: {
  entries: Array<{ citations: string[]; text: string | null }>;
  emptyMessage: string;
}) {
  const populatedEntries = entries.filter(
    (entry): entry is { citations: string[]; text: string } => entry.text !== null,
  );

  if (populatedEntries.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <Stack spacing={2}>
      {populatedEntries.map((entry, index) => (
        <Card
          elevation={0}
          key={`${entry.text}-${index}`}
          sx={{ border: "1px solid", borderColor: "divider" }}
        >
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="body1">{entry.text}</Typography>
              {entry.citations.length > 0 ? (
                <Stack direction="row" flexWrap="wrap" gap={1}>
                  {entry.citations.map((citation) => (
                    <Chip
                      key={`${entry.text}-${citation}`}
                      label={citation}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              ) : (
                <EmptyState message="No reviewed citations were attached to this context entry." />
              )}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

export function supportedAnchorRoute(
  recordFamily: string | null,
  recordId: string | null,
): { label: string; to: string } | null {
  if (recordFamily === null || recordId === null) {
    return null;
  }

  if (recordFamily === "alert") {
    return {
      label: "Open alert detail",
      to: `/operator/alerts/${recordId}`,
    };
  }

  if (recordFamily === "case") {
    return {
      label: "Open case detail",
      to: `/operator/cases/${recordId}`,
    };
  }

  return null;
}
