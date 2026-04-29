from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Mapping, Protocol

from .models import CaseRecord, EvidenceRecord, ObservationRecord


class MispExternalEvidenceDependencies(Protocol):
    _store: object
    _misp_context_adapter: object

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

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


def _normalize_misp_indicator_type(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if normalized == "":
        return None
    return normalized.lower()


def _normalize_misp_indicator_value(
    object_type: str,
    value: object,
) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if normalized == "":
        return None
    if object_type in {"domain", "ip", "sha1", "sha256", "md5"}:
        return normalized.lower()
    return normalized


def _mapping_matches_misp_indicator(
    mapping: Mapping[str, object],
    *,
    queried_object_type: str,
    queried_object_value: str,
) -> bool:
    direct_type = _normalize_misp_indicator_type(mapping.get("type"))
    direct_value = _normalize_misp_indicator_value(
        queried_object_type,
        mapping.get("value"),
    )
    if direct_type == queried_object_type and direct_value == queried_object_value:
        return True

    indicator_type = _normalize_misp_indicator_type(mapping.get("indicator_type"))
    indicator_value = _normalize_misp_indicator_value(
        queried_object_type,
        mapping.get("indicator_value"),
    )
    return (
        indicator_type == queried_object_type
        and indicator_value == queried_object_value
    )


def _container_explicitly_cites_misp_indicator(
    value: object,
    *,
    queried_object_type: str,
    queried_object_value: str,
) -> bool:
    if isinstance(value, Mapping):
        if _mapping_matches_misp_indicator(
            value,
            queried_object_type=queried_object_type,
            queried_object_value=queried_object_value,
        ):
            return True
        return any(
            _container_explicitly_cites_misp_indicator(
                child,
                queried_object_type=queried_object_type,
                queried_object_value=queried_object_value,
            )
            for child in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _container_explicitly_cites_misp_indicator(
                item,
                queried_object_type=queried_object_type,
                queried_object_value=queried_object_value,
            )
            for item in value
        )
    return False


def _require_explicit_misp_anchor_binding(
    *,
    case: CaseRecord,
    admitting_evidence: EvidenceRecord,
    queried_object_type: object,
    queried_object_value: object,
) -> None:
    if not isinstance(queried_object_type, str) or not queried_object_type.strip():
        raise ValueError("queried_object_type must be a non-empty string")
    normalized_type = queried_object_type.strip().lower()
    normalized_value = _normalize_misp_indicator_value(
        normalized_type,
        queried_object_value,
    )
    if normalized_value is None:
        raise ValueError("queried_object_value must be a non-empty string")
    if _container_explicitly_cites_misp_indicator(
        admitting_evidence.content,
        queried_object_type=normalized_type,
        queried_object_value=normalized_value,
    ):
        return
    if _container_explicitly_cites_misp_indicator(
        admitting_evidence.provenance,
        queried_object_type=normalized_type,
        queried_object_value=normalized_value,
    ):
        return
    if _container_explicitly_cites_misp_indicator(
        case.reviewed_context,
        queried_object_type=normalized_type,
        queried_object_value=normalized_value,
    ):
        return
    raise ValueError(
        "queried_object must be explicitly cited by the reviewed case or admitting evidence anchor"
    )


class MispExternalEvidenceHelper:
    def __init__(self, service: MispExternalEvidenceDependencies) -> None:
        self._service = service

    def attach_context(
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
        case_id = self._service._require_non_empty_string(case_id, "case_id")
        admitting_evidence_id = self._service._require_non_empty_string(
            admitting_evidence_id,
            "admitting_evidence_id",
        )
        normalized_scope_statement = self._service._normalize_optional_string(
            observation_scope_statement,
            "observation_scope_statement",
        )
        if normalized_scope_statement is None and observation_id is not None:
            raise ValueError(
                "observation_id requires observation_scope_statement for MISP attachment"
            )
        if not self._service._misp_context_adapter.enabled:
            raise ValueError("MISP subordinate enrichment is disabled")

        with self._service._store.transaction(isolation_level="SERIALIZABLE"):
            case = self._service._require_reviewed_operator_case(case_id)
            self._service._validate_case_evidence_linkage(
                case=case,
                evidence_ids=(admitting_evidence_id,),
                field_name="admitting_evidence_id",
            )
            admitting_evidence = self._service._store.get(
                EvidenceRecord,
                admitting_evidence_id,
            )
            if admitting_evidence is None:
                raise LookupError(f"Missing evidence {admitting_evidence_id!r}")
            if admitting_evidence.derivation_relationship == "misp_context_attachment":
                raise ValueError(
                    "admitting_evidence_id must reference reviewed evidence, not previously attached MISP context"
                )
            _require_explicit_misp_anchor_binding(
                case=case,
                admitting_evidence=admitting_evidence,
                queried_object_type=queried_object_type,
                queried_object_value=queried_object_value,
            )
            attachment = self._service._misp_context_adapter.build_attachment(
                case_id=case.case_id,
                alert_id=case.alert_id,
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
                    replace(current_case, evidence_ids=merged_case_evidence_ids)
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
                            looked_up_at,
                            "looked_up_at",
                        ),
                        scope_statement=normalized_scope_statement,
                        lifecycle_state="confirmed",
                        provenance=attachment.observation_provenance,
                        content={
                            **attachment.observation_content,
                            "misp_context_evidence_id": evidence.evidence_id,
                        },
                    )
                )
            return evidence, observation
