from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Mapping, Protocol

from ..models import CaseRecord, EvidenceRecord, ObservationRecord


class OsqueryExternalEvidenceDependencies(Protocol):
    _store: object
    _osquery_host_context_adapter: object

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

    def _resolve_new_record_identifier(
        self,
        record_type: type,
        requested_identifier: str | None,
        field_name: str,
        prefix: str,
    ) -> str:
        ...

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


def require_case_host_identifier(case: CaseRecord) -> str:
    asset = case.reviewed_context.get("asset")
    if not isinstance(asset, Mapping):
        raise ValueError(
            "reviewed case asset.host_identifier must explicitly bind osquery host context"
        )
    host_identifier = asset.get("host_identifier")
    if not isinstance(host_identifier, str) or not host_identifier.strip():
        raise ValueError(
            "reviewed case asset.host_identifier must explicitly bind osquery host context"
        )
    return host_identifier


class OsqueryExternalEvidenceHelper:
    def __init__(self, service: OsqueryExternalEvidenceDependencies) -> None:
        self._service = service

    def attach_host_context(
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
        case_id = self._service._require_non_empty_string(case_id, "case_id")
        normalized_scope_statement = self._service._normalize_optional_string(
            observation_scope_statement,
            "observation_scope_statement",
        )
        if normalized_scope_statement is None and observation_id is not None:
            raise ValueError(
                "observation_id requires observation_scope_statement for osquery attachment"
            )
        with self._service._store.transaction(isolation_level="SERIALIZABLE"):
            case = self._service._require_reviewed_operator_case(case_id)
            authoritative_host_identifier = require_case_host_identifier(case)
            attachment = self._service._osquery_host_context_adapter.build_attachment(
                case_id=case.case_id,
                alert_id=case.alert_id,
                authoritative_host_identifier=authoritative_host_identifier,
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
            )
            resolved_evidence_id = self._service._resolve_new_record_identifier(
                EvidenceRecord,
                evidence_id,
                "evidence_id",
                "evidence",
            )
            evidence = self._service.persist_record(
                EvidenceRecord(
                    evidence_id=resolved_evidence_id,
                    source_record_id=attachment.source_record_id,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    source_system=attachment.source_system,
                    collector_identity=attachment.collector_identity,
                    acquired_at=attachment.acquired_at,
                    derivation_relationship=attachment.derivation_relationship,
                    lifecycle_state="linked",
                    provenance=attachment.provenance,
                    content=attachment.content,
                )
            )
            current_case = self._service._require_reviewed_operator_case(case.case_id)
            merged_case_evidence_ids = self._service._merge_linked_ids(
                current_case.evidence_ids,
                evidence.evidence_id,
            )
            if merged_case_evidence_ids != current_case.evidence_ids:
                self._service.persist_record(
                    replace(
                        current_case,
                        evidence_ids=merged_case_evidence_ids,
                    )
                )

            observation: ObservationRecord | None = None
            if normalized_scope_statement is not None:
                resolved_observation_id = self._service._resolve_new_record_identifier(
                    ObservationRecord,
                    observation_id,
                    "observation_id",
                    "observation",
                )
                observation = self._service.persist_record(
                    ObservationRecord(
                        observation_id=resolved_observation_id,
                        hunt_id=None,
                        hunt_run_id=None,
                        alert_id=current_case.alert_id,
                        case_id=current_case.case_id,
                        supporting_evidence_ids=(evidence.evidence_id,),
                        author_identity=self._service._require_non_empty_string(
                            reviewed_by,
                            "reviewed_by",
                        ),
                        observed_at=self._service._require_aware_datetime(
                            collected_at,
                            "collected_at",
                        ),
                        scope_statement=normalized_scope_statement,
                        lifecycle_state="confirmed",
                        provenance=attachment.observation_provenance,
                        content={
                            **attachment.observation_content,
                            "host_context_evidence_id": evidence.evidence_id,
                        },
                    )
                )
            return evidence, observation
