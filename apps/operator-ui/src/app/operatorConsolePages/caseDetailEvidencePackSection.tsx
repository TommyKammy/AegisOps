import {
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  asRecord,
  asString,
  EmptyState,
  formatValue,
  SectionCard,
  statusTone,
  type UnknownRecord,
} from "./shared";

export function EvidencePackReviewSection({
  evidencePacks,
}: {
  evidencePacks: UnknownRecord[];
}) {
  return (
    <SectionCard
      subtitle="Evidence packs show backend-reviewed freshness, custody, confidence, provenance, conflict, uncertainty, and source posture as subordinate review context only."
      title="Evidence pack review"
    >
      {evidencePacks.length > 0 ? (
        <Table aria-label="Linked evidence packs" size="small">
          <TableHead>
            <TableRow>
              <TableCell>Evidence pack</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Freshness</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Conflict</TableCell>
              <TableCell>Uncertainty</TableCell>
              <TableCell>Source state</TableCell>
              <TableCell>Custody</TableCell>
              <TableCell>Provenance</TableCell>
              <TableCell>Boundary</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {evidencePacks.map((pack, index) => (
              <EvidencePackReviewRow
                key={`${asString(pack.evidence_request_id) ?? "evidence-pack"}-${index}`}
                pack={pack}
              />
            ))}
          </TableBody>
        </Table>
      ) : (
        <EmptyState message="No linked evidence packs were returned for this case." />
      )}
    </SectionCard>
  );
}

function EvidencePackReviewRow({ pack }: { pack: UnknownRecord }) {
  const freshnessState = asString(pack.freshness_state);
  const conflictState = asString(pack.conflict_state);
  const sourceState = asString(pack.source_state);
  const custody = asRecord(pack.custody);
  const provenance = asRecord(pack.provenance);

  return (
    <TableRow>
      <TableCell>{formatValue(pack.evidence_request_id)}</TableCell>
      <TableCell>{formatValue(pack.source_id)}</TableCell>
      <TableCell>
        <Chip
          color={
            freshnessState === "stale_review_required"
              ? "warning"
              : statusTone(freshnessState)
          }
          label={freshnessState ?? "unknown"}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell>{formatValue(pack.confidence_state)}</TableCell>
      <TableCell>
        <Chip
          color={evidencePackConflictTone(conflictState)}
          label={conflictState ?? "unknown"}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell>{formatValue(pack.uncertainty_label)}</TableCell>
      <TableCell>
        <Chip
          color={evidencePackSourceTone(sourceState)}
          label={sourceState ?? "unknown"}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell>
        <Stack spacing={0.5}>
          <Typography variant="body2">{formatValue(pack.custody_state)}</Typography>
          <Typography color="text.secondary" variant="caption">
            {formatValue(
              custody?.aegisops_evidence_record_id ??
                custody?.enrichment_request_id ??
                custody?.collection_timestamp,
            )}
          </Typography>
        </Stack>
      </TableCell>
      <TableCell>
        <Stack spacing={0.5}>
          <Typography variant="body2">{formatValue(pack.provenance_state)}</Typography>
          <Typography color="text.secondary" variant="caption">
            {formatValue(
              provenance?.custody_reference ??
                provenance?.request_binding ??
                provenance?.source_id,
            )}
          </Typography>
        </Stack>
      </TableCell>
      <TableCell>
        <Typography color="text.secondary" variant="body2">
          Subordinate evidence context only
        </Typography>
      </TableCell>
    </TableRow>
  );
}

function evidencePackConflictTone(
  conflictState: string | null,
): ReturnType<typeof statusTone> {
  if (conflictState === "conflicting") {
    return "warning";
  }
  return statusTone(conflictState);
}

function evidencePackSourceTone(sourceState: string | null): ReturnType<typeof statusTone> {
  if (sourceState === "unavailable") {
    return "error";
  }
  if (sourceState === "degraded") {
    return "warning";
  }
  return statusTone(sourceState);
}
