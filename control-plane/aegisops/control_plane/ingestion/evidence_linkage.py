from __future__ import annotations

from typing import Callable, Protocol

from ..models import AlertRecord, CaseRecord, EvidenceRecord


class EvidenceLinkageStore(Protocol):
    def get(
        self,
        record_type: type[EvidenceRecord],
        record_id: str,
    ) -> EvidenceRecord | None:
        ...


class EvidenceLinkageService:
    def __init__(
        self,
        *,
        store: EvidenceLinkageStore,
        require_non_empty_string: Callable[[object, str], str],
        merge_linked_ids: Callable[[object, str | None], tuple[str, ...]],
    ) -> None:
        self._store = store
        self._require_non_empty_string = require_non_empty_string
        self._merge_linked_ids = merge_linked_ids

    def normalize_linked_record_ids(
        self,
        record_ids: tuple[str, ...],
        field_name: str,
    ) -> tuple[str, ...]:
        normalized_ids: tuple[str, ...] = ()
        for record_id in record_ids:
            normalized_id = self._require_non_empty_string(record_id, field_name)
            normalized_ids = self._merge_linked_ids(normalized_ids, normalized_id)
        return normalized_ids

    def validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        for evidence_id in evidence_ids:
            evidence = self._require_evidence(evidence_id)
            if evidence.case_id not in {None, case.case_id}:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} linked to "
                    f"different case {evidence.case_id!r}"
                )
            if evidence.case_id is None and evidence.alert_id != case.alert_id:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} that is not "
                    f"linked to case {case.case_id!r} or its source alert"
                )

    def validate_alert_evidence_linkage(
        self,
        *,
        alert: AlertRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        for evidence_id in evidence_ids:
            evidence = self._require_evidence(evidence_id)
            shares_alert = evidence.alert_id == alert.alert_id
            shares_case = alert.case_id is not None and evidence.case_id == alert.case_id
            if not shares_alert and not shares_case:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} that is not "
                    f"linked to alert {alert.alert_id!r}"
                )

    def _require_evidence(self, evidence_id: str) -> EvidenceRecord:
        evidence = self._store.get(EvidenceRecord, evidence_id)
        if evidence is None:
            raise LookupError(f"Missing evidence {evidence_id!r}")
        return evidence
