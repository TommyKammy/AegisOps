from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Callable, Mapping
import uuid

from ..models import (
    CaseRecord,
    EvidenceRecord,
    FindingAlertIngestResult,
    NativeDetectionRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from ..service import AegisOpsControlPlaneService


class NativeDetectionContextAttacher:
    def __init__(
        self,
        service: AegisOpsControlPlaneService,
        *,
        merge_reviewed_context: Callable[
            [Mapping[str, object], Mapping[str, object]],
            dict[str, object],
        ],
        normalize_admission_provenance: Callable[
            [object],
            dict[str, str] | None,
        ],
    ) -> None:
        self._service = service
        self._merge_reviewed_context = merge_reviewed_context
        self._normalize_admission_provenance = normalize_admission_provenance

    def attach_native_detection_context(
        self,
        *,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        substrate_detection_record_id: str,
    ) -> FindingAlertIngestResult:
        service = self._service
        with service._store.transaction():
            source_system = service._normalize_optional_string(
                record.metadata.get("source_system"),
                "metadata.source_system",
            ) or record.substrate_key
            evidence_id = (
                f"evidence-{uuid.uuid5(uuid.NAMESPACE_URL, substrate_detection_record_id)}"
            )
            case_id = ingest_result.alert.case_id
            existing_case = None
            if case_id is not None:
                existing_case = service._store.get(CaseRecord, case_id)
                if existing_case is None:
                    raise LookupError(
                        f"Alert {ingest_result.alert.alert_id!r} "
                        f"references missing case {case_id!r}"
                    )
            evidence = self._persist_native_context_evidence(
                evidence_id=evidence_id,
                substrate_detection_record_id=substrate_detection_record_id,
                record=record,
                ingest_result=ingest_result,
                case_id=case_id,
                source_system=source_system,
            )
            if existing_case is not None:
                self._merge_case_context(
                    existing_case=existing_case,
                    evidence_id=evidence.evidence_id,
                    ingest_result=ingest_result,
                )

            subject_linkage = dict(ingest_result.reconciliation.subject_linkage)
            subject_linkage["evidence_ids"] = service._merge_linked_ids(
                subject_linkage.get("evidence_ids"),
                evidence.evidence_id,
            )
            subject_linkage["source_systems"] = service._merge_linked_ids(
                subject_linkage.get("source_systems"),
                source_system,
            )
            self._attach_native_source_metadata(
                subject_linkage=subject_linkage,
                record=record,
            )
            reconciliation = service.persist_record(
                ReconciliationRecord(
                    reconciliation_id=ingest_result.reconciliation.reconciliation_id,
                    subject_linkage=subject_linkage,
                    alert_id=ingest_result.reconciliation.alert_id,
                    finding_id=ingest_result.reconciliation.finding_id,
                    analytic_signal_id=ingest_result.reconciliation.analytic_signal_id,
                    execution_run_id=ingest_result.reconciliation.execution_run_id,
                    linked_execution_run_ids=(
                        ingest_result.reconciliation.linked_execution_run_ids
                    ),
                    correlation_key=ingest_result.reconciliation.correlation_key,
                    first_seen_at=ingest_result.reconciliation.first_seen_at,
                    last_seen_at=ingest_result.reconciliation.last_seen_at,
                    ingest_disposition=ingest_result.reconciliation.ingest_disposition,
                    mismatch_summary=ingest_result.reconciliation.mismatch_summary,
                    compared_at=ingest_result.reconciliation.compared_at,
                    lifecycle_state=ingest_result.reconciliation.lifecycle_state,
                )
            )
            return FindingAlertIngestResult(
                alert=ingest_result.alert,
                reconciliation=reconciliation,
                disposition=ingest_result.disposition,
            )

    def _persist_native_context_evidence(
        self,
        *,
        evidence_id: str,
        substrate_detection_record_id: str,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        case_id: str | None,
        source_system: str,
    ) -> EvidenceRecord:
        service = self._service
        existing_evidence = service._store.get(EvidenceRecord, evidence_id)
        evidence_fields = {
            "source_record_id": substrate_detection_record_id,
            "alert_id": ingest_result.alert.alert_id,
            "case_id": case_id,
            "source_system": source_system,
            "collector_identity": f"{record.substrate_key}-native-detection-adapter",
            "acquired_at": service._require_aware_datetime(
                record.first_seen_at,
                "record.first_seen_at",
            ),
            "derivation_relationship": "native_detection_record",
            "lifecycle_state": "linked" if case_id is not None else "collected",
        }
        if existing_evidence is not None:
            return service.persist_record(
                replace(
                    existing_evidence,
                    **evidence_fields,
                )
            )
        return service.persist_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                provenance={},
                content={},
                **evidence_fields,
            )
        )

    def _merge_case_context(
        self,
        *,
        existing_case: CaseRecord,
        evidence_id: str,
        ingest_result: FindingAlertIngestResult,
    ) -> None:
        service = self._service
        merged_case_evidence_ids = service._merge_linked_ids(
            existing_case.evidence_ids,
            evidence_id,
        )
        merged_case_reviewed_context = self._merge_reviewed_context(
            existing_case.reviewed_context,
            ingest_result.alert.reviewed_context,
        )
        if (
            merged_case_evidence_ids != existing_case.evidence_ids
            or merged_case_reviewed_context != existing_case.reviewed_context
        ):
            service.persist_record(
                replace(
                    existing_case,
                    evidence_ids=merged_case_evidence_ids,
                    reviewed_context=merged_case_reviewed_context,
                )
            )

    def _attach_native_source_metadata(
        self,
        *,
        subject_linkage: dict[str, object],
        record: NativeDetectionRecord,
    ) -> None:
        service = self._service
        source_provenance = record.metadata.get("source_provenance")
        if isinstance(source_provenance, Mapping):
            accountable_source_identity = service._normalize_optional_string(
                source_provenance.get("accountable_source_identity"),
                "metadata.source_provenance.accountable_source_identity",
            )
            if accountable_source_identity is not None:
                subject_linkage["accountable_source_identities"] = (
                    service._merge_linked_ids(
                        subject_linkage.get("accountable_source_identities"),
                        accountable_source_identity,
                    )
                )

        native_rule = record.metadata.get("native_rule")
        if isinstance(native_rule, Mapping):
            native_rule_id = service._normalize_optional_string(
                native_rule.get("id"),
                "metadata.native_rule.id",
            )
            native_rule_description = service._normalize_optional_string(
                native_rule.get("description"),
                "metadata.native_rule.description",
            )
            rule_level = native_rule.get("level")
            subject_linkage["latest_native_rule"] = {
                "id": native_rule_id,
                "level": rule_level if isinstance(rule_level, int) else None,
                "description": native_rule_description,
            }

        reviewed_correlation_context = record.metadata.get(
            "reviewed_correlation_context"
        )
        if isinstance(reviewed_correlation_context, Mapping):
            subject_linkage["reviewed_correlation_context"] = {
                str(field_name): field_value
                for field_name, field_value in reviewed_correlation_context.items()
                if isinstance(field_value, str) and field_value.strip()
            }

        reviewed_source_profile = record.metadata.get("reviewed_source_profile")
        if isinstance(reviewed_source_profile, Mapping):
            subject_linkage["reviewed_source_profile"] = dict(reviewed_source_profile)

        raw_alert = record.metadata.get("raw_alert")
        if isinstance(raw_alert, Mapping):
            subject_linkage["latest_native_payload"] = dict(raw_alert)

        admission_provenance = self._normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            subject_linkage["admission_provenance"] = admission_provenance
