from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .models import ActionRequestRecord, EvidenceRecord, ObservationRecord


class ExternalEvidenceFacade:
    """Public external-evidence service methods backed by the boundary object."""

    def attach_osquery_host_context(
        self,
        *,
        case_id: str,
        host_identifier: str,
        query_name: str,
        query_sql: str,
        result_kind: str,
        rows: tuple[Mapping[str, object], ...],
        collected_at: datetime,
        reviewed_by: str,
        source_id: str,
        collection_path: str,
        query_context: Mapping[str, object] | None = None,
        evidence_id: str | None = None,
        observation_scope_statement: str | None = None,
        observation_id: str | None = None,
    ) -> tuple[EvidenceRecord, ObservationRecord | None]:
        return self._external_evidence_boundary.attach_osquery_host_context(
            case_id=case_id,
            host_identifier=host_identifier,
            query_name=query_name,
            query_sql=query_sql,
            result_kind=result_kind,
            rows=rows,
            collected_at=collected_at,
            reviewed_by=reviewed_by,
            source_id=source_id,
            collection_path=collection_path,
            query_context=query_context,
            evidence_id=evidence_id,
            observation_scope_statement=observation_scope_statement,
            observation_id=observation_id,
        )

    def attach_misp_context(
        self,
        *,
        case_id: str,
        admitting_evidence_id: str,
        queried_object_type: str,
        queried_object_value: str,
        looked_up_at: datetime,
        reviewed_by: str,
        event_id: str,
        event_info: str,
        event_published_at: datetime | None = None,
        iocs: tuple[Mapping[str, object], ...] = (),
        taxonomies: tuple[Mapping[str, object], ...] = (),
        warninglists: tuple[Mapping[str, object], ...] = (),
        galaxies: tuple[Mapping[str, object], ...] = (),
        sightings: tuple[Mapping[str, object], ...] = (),
        citation_url: str = "",
        staleness_marker: Mapping[str, object] | None = None,
        conflict_marker: Mapping[str, object] | None = None,
        evidence_id: str | None = None,
        observation_scope_statement: str | None = None,
        observation_id: str | None = None,
    ) -> tuple[EvidenceRecord, ObservationRecord | None]:
        return self._external_evidence_boundary.attach_misp_context(
            case_id=case_id,
            admitting_evidence_id=admitting_evidence_id,
            queried_object_type=queried_object_type,
            queried_object_value=queried_object_value,
            looked_up_at=looked_up_at,
            reviewed_by=reviewed_by,
            event_id=event_id,
            event_info=event_info,
            event_published_at=event_published_at,
            iocs=iocs,
            taxonomies=taxonomies,
            warninglists=warninglists,
            galaxies=galaxies,
            sightings=sightings,
            citation_url=citation_url,
            staleness_marker=staleness_marker,
            conflict_marker=conflict_marker,
            evidence_id=evidence_id,
            observation_scope_statement=observation_scope_statement,
            observation_id=observation_id,
        )

    def create_endpoint_evidence_collection_request(
        self,
        *,
        case_id: str,
        admitting_evidence_id: str,
        requester_identity: str,
        host_identifier: str,
        evidence_gap: str,
        artifact_classes: tuple[str, ...],
        expires_at: datetime,
        reviewed_gap_id: str | None = None,
        reviewed_follow_up_decision_id: str | None = None,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._external_evidence_boundary.create_endpoint_evidence_collection_request(
            case_id=case_id,
            admitting_evidence_id=admitting_evidence_id,
            requester_identity=requester_identity,
            host_identifier=host_identifier,
            evidence_gap=evidence_gap,
            artifact_classes=artifact_classes,
            expires_at=expires_at,
            reviewed_gap_id=reviewed_gap_id,
            reviewed_follow_up_decision_id=reviewed_follow_up_decision_id,
            action_request_id=action_request_id,
        )

    def ingest_endpoint_evidence_artifacts(
        self,
        *,
        action_request_id: str,
        artifacts: tuple[Mapping[str, object], ...],
        admitted_by: str,
    ) -> tuple[EvidenceRecord, ...]:
        return self._external_evidence_boundary.ingest_endpoint_evidence_artifacts(
            action_request_id=action_request_id,
            artifacts=artifacts,
            admitted_by=admitted_by,
        )
