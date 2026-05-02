from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol

from .external_evidence_endpoint import EndpointExternalEvidenceHelper
from .external_evidence_misp import MispExternalEvidenceHelper
from .external_evidence_osquery import OsqueryExternalEvidenceHelper
from ..models import (
    ActionRequestRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
)


class ExternalEvidenceBoundaryServiceDependencies(Protocol):
    _store: object
    _endpoint_evidence_pack_adapter: object
    _misp_context_adapter: object
    _osquery_host_context_adapter: object

    def _build_lifecycle_transition_records(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...

    def persist_record(
        self,
        record: object,
        *,
        transitioned_at: datetime | None = None,
    ) -> object:
        ...

    def _require_non_empty_string(self, value: object, field_name: str) -> str:
        ...

    def _require_aware_datetime(self, value: object, field_name: str) -> datetime:
        ...

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
        ...

    def _validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        ...

    def _resolve_new_record_identifier(
        self,
        record_type: type,
        requested_identifier: str | None,
        field_name: str,
        prefix: str,
    ) -> str:
        ...

    def _next_identifier(self, prefix: str) -> str:
        ...

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


class ExternalEvidenceBoundary:
    """Coordinates external evidence flows behind the service facade."""

    def __init__(self, service: ExternalEvidenceBoundaryServiceDependencies) -> None:
        self._service = service
        self._misp_helper = MispExternalEvidenceHelper(service)
        self._osquery_helper = OsqueryExternalEvidenceHelper(service)
        self._endpoint_helper = EndpointExternalEvidenceHelper(service)

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
        return self._osquery_helper.attach_host_context(
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
        return self._misp_helper.attach_context(
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
        return self._endpoint_helper.create_collection_request(
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
        return self._endpoint_helper.ingest_artifacts(
            action_request_id=action_request_id,
            artifacts=artifacts,
            admitted_by=admitted_by,
        )
