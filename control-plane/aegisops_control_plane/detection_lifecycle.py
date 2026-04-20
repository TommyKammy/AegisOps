from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Mapping
import uuid

from .models import (
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    CaseRecord,
    EvidenceRecord,
    FindingAlertIngestResult,
    NativeDetectionRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from .service import AegisOpsControlPlaneService, NativeDetectionRecordAdapter


class DetectionLifecycleService:
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

    def ingest_finding_alert(
        self,
        *,
        finding_id: str,
        analytic_signal_id: str | None,
        substrate_detection_record_id: str | None = None,
        correlation_key: str,
        first_seen_at: datetime,
        last_seen_at: datetime,
        materially_new_work: bool = False,
        reviewed_context: Mapping[str, object] | None = None,
    ) -> FindingAlertIngestResult:
        return self.ingest_analytic_signal_admission(
            AnalyticSignalAdmission(
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                substrate_detection_record_id=substrate_detection_record_id,
                correlation_key=correlation_key,
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                materially_new_work=materially_new_work,
                reviewed_context=reviewed_context or {},
            )
        )

    def promote_alert_to_case(
        self,
        alert_id: str,
        *,
        case_id: str | None = None,
        case_lifecycle_state: str = "open",
    ) -> CaseRecord:
        service = self._service
        alert_id = service._require_non_empty_string(alert_id, "alert_id")
        requested_case_id = service._normalize_optional_string(case_id, "case_id")
        case_lifecycle_state = service._require_non_empty_string(
            case_lifecycle_state,
            "case_lifecycle_state",
        )
        with service._store.transaction():
            alert = service._store.get(AlertRecord, alert_id)
            if alert is None:
                raise LookupError(f"Missing alert {alert_id!r}")

            if alert.case_id is not None:
                resolved_case_id = alert.case_id
                if (
                    requested_case_id is not None
                    and requested_case_id != resolved_case_id
                ):
                    raise ValueError(
                        f"Alert {alert_id!r} is already linked to case {resolved_case_id!r}"
                    )
            else:
                resolved_case_id = requested_case_id or service._next_identifier("case")

            existing_case = service._store.get(CaseRecord, resolved_case_id)
            if alert.case_id is not None and existing_case is None:
                raise LookupError(
                    f"Alert {alert_id!r} references missing case {resolved_case_id!r}"
                )

            evidence_records = service._list_alert_evidence_records(
                alert_id=alert.alert_id,
                case_id=resolved_case_id,
            )
            if not evidence_records:
                raise ValueError(
                    f"Alert {alert_id!r} has no linked evidence to promote into a case"
                )

            merged_evidence_ids: tuple[str, ...] = ()
            for evidence in evidence_records:
                merged_evidence_ids = service._merge_linked_ids(
                    merged_evidence_ids,
                    evidence.evidence_id,
                )
                updated_lifecycle_state = (
                    "linked"
                    if evidence.lifecycle_state == "collected"
                    else evidence.lifecycle_state
                )
                if (
                    evidence.case_id == resolved_case_id
                    and updated_lifecycle_state == evidence.lifecycle_state
                ):
                    continue
                service.persist_record(
                    EvidenceRecord(
                        evidence_id=evidence.evidence_id,
                        source_record_id=evidence.source_record_id,
                        alert_id=evidence.alert_id,
                        case_id=resolved_case_id,
                        source_system=evidence.source_system,
                        collector_identity=evidence.collector_identity,
                        acquired_at=evidence.acquired_at,
                        derivation_relationship=evidence.derivation_relationship,
                        lifecycle_state=updated_lifecycle_state,
                        provenance=evidence.provenance,
                        content=evidence.content,
                    )
                )

            if existing_case is not None:
                if (
                    existing_case.alert_id is not None
                    and existing_case.alert_id != alert.alert_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to alert {existing_case.alert_id!r}"
                    )
                if (
                    existing_case.finding_id is not None
                    and existing_case.finding_id != alert.finding_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to finding {existing_case.finding_id!r}"
                    )
            merged_case_evidence_ids = service._merge_linked_ids(
                existing_case.evidence_ids if existing_case is not None else (),
                None,
            )
            for evidence_id in merged_evidence_ids:
                merged_case_evidence_ids = service._merge_linked_ids(
                    merged_case_evidence_ids,
                    evidence_id,
                )

            promoted_case = service.persist_record(
                replace(
                    existing_case,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    reviewed_context=self._merge_reviewed_context(
                        existing_case.reviewed_context,
                        alert.reviewed_context,
                    ),
                )
                if existing_case is not None
                else CaseRecord(
                    case_id=resolved_case_id,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    lifecycle_state=case_lifecycle_state,
                    reviewed_context=alert.reviewed_context,
                )
            )
            promoted_alert = service.persist_record(
                replace(
                    alert,
                    case_id=promoted_case.case_id,
                    lifecycle_state="escalated_to_case",
                )
            )
            if promoted_alert.analytic_signal_id is not None:
                service._link_case_to_analytic_signals(
                    (promoted_alert.analytic_signal_id,),
                    promoted_case.case_id,
                )
            service._link_case_to_alert_reconciliations(
                alert_id=promoted_alert.alert_id,
                case_id=promoted_case.case_id,
                evidence_ids=merged_evidence_ids,
            )
            return promoted_case

    def ingest_native_detection_record(
        self,
        adapter: NativeDetectionRecordAdapter,
        record: NativeDetectionRecord,
    ) -> FindingAlertIngestResult:
        service = self._service
        record = service._with_native_detection_admission_provenance(
            record,
            admission_kind="replay",
            admission_channel="fixture_replay",
        )
        adapter_substrate_key = service._require_non_empty_string(
            adapter.substrate_key,
            "adapter.substrate_key",
        )
        record_substrate_key = service._require_non_empty_string(
            record.substrate_key,
            "record.substrate_key",
        )
        if record_substrate_key != adapter_substrate_key:
            raise ValueError(
                "native detection record substrate does not match adapter boundary "
                f"({record_substrate_key!r} != {adapter_substrate_key!r})"
            )
        admission = adapter.build_analytic_signal_admission(record)
        admission_provenance = self._normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            admission = AnalyticSignalAdmission(
                finding_id=admission.finding_id,
                analytic_signal_id=admission.analytic_signal_id,
                substrate_detection_record_id=admission.substrate_detection_record_id,
                correlation_key=admission.correlation_key,
                first_seen_at=admission.first_seen_at,
                last_seen_at=admission.last_seen_at,
                materially_new_work=admission.materially_new_work,
                reviewed_context=self._merge_reviewed_context(
                    admission.reviewed_context,
                    {"provenance": admission_provenance},
                ),
            )
        raw_substrate_detection_record_id = service._require_non_empty_string(
            admission.substrate_detection_record_id or record.native_record_id,
            "substrate_detection_record_id/native_record_id",
        )
        substrate_detection_record_id = service._normalize_substrate_detection_record_id(
            record_substrate_key,
            raw_substrate_detection_record_id,
        )
        admission = AnalyticSignalAdmission(
            finding_id=admission.finding_id,
            analytic_signal_id=admission.analytic_signal_id,
            substrate_detection_record_id=substrate_detection_record_id,
            correlation_key=admission.correlation_key,
            first_seen_at=admission.first_seen_at,
            last_seen_at=admission.last_seen_at,
            materially_new_work=admission.materially_new_work,
            reviewed_context=admission.reviewed_context,
        )
        with service._store.transaction():
            result = self.ingest_analytic_signal_admission(admission)
            return self.attach_native_detection_context(
                record=record,
                ingest_result=result,
                substrate_detection_record_id=substrate_detection_record_id,
            )

    def ingest_analytic_signal_admission(
        self,
        admission: AnalyticSignalAdmission,
    ) -> FindingAlertIngestResult:
        service = self._service
        finding_id = service._require_non_empty_string(
            admission.finding_id,
            "finding_id",
        )
        analytic_signal_id = service._normalize_optional_string(
            admission.analytic_signal_id,
            "analytic_signal_id",
        )
        substrate_detection_record_id = service._normalize_optional_string(
            admission.substrate_detection_record_id,
            "substrate_detection_record_id",
        )
        correlation_key = service._require_non_empty_string(
            admission.correlation_key,
            "correlation_key",
        )
        first_seen_at = service._require_aware_datetime(
            admission.first_seen_at,
            "first_seen_at",
        )
        last_seen_at = service._require_aware_datetime(
            admission.last_seen_at,
            "last_seen_at",
        )
        if last_seen_at < first_seen_at:
            raise ValueError(
                "last_seen_at must be greater than or equal to first_seen_at"
            )
        materially_new_work = admission.materially_new_work
        reviewed_context = self._merge_reviewed_context({}, admission.reviewed_context)
        with service._store.transaction():
            latest_reconciliation = service._store.latest_reconciliation_for_correlation_key(
                correlation_key,
                require_alert_id=True,
            )
            analytic_signal_id = service._resolve_analytic_signal_id(
                analytic_signal_id=analytic_signal_id,
                finding_id=finding_id,
                correlation_key=correlation_key,
                substrate_detection_record_id=substrate_detection_record_id,
                latest_reconciliation=latest_reconciliation,
            )

            if latest_reconciliation is None:
                alert = service.persist_record(
                    AlertRecord(
                        alert_id=service._next_identifier("alert"),
                        finding_id=finding_id,
                        analytic_signal_id=analytic_signal_id,
                        case_id=None,
                        lifecycle_state="new",
                        reviewed_context=reviewed_context,
                    )
                )
                disposition = "created"
                linked_finding_ids = (finding_id,)
                linked_signal_ids = (
                    (analytic_signal_id,) if analytic_signal_id is not None else tuple()
                )
                linked_substrate_detection_ids = service._merge_linked_ids(
                    (),
                    substrate_detection_record_id,
                )
                linked_case_ids = service._merge_linked_ids((), alert.case_id)
                persisted_first_seen = first_seen_at
                persisted_last_seen = last_seen_at
            else:
                alert = service._store.get(AlertRecord, latest_reconciliation.alert_id)
                if alert is None:
                    raise LookupError(
                        f"Missing alert {latest_reconciliation.alert_id!r} for correlation key {correlation_key!r}"
                    )
                merged_reviewed_context = self._merge_reviewed_context(
                    alert.reviewed_context,
                    admission.reviewed_context,
                )
                existing_finding_ids = latest_reconciliation.subject_linkage.get("finding_ids")
                existing_signal_ids = latest_reconciliation.subject_linkage.get(
                    "analytic_signal_ids"
                )
                existing_substrate_detection_ids = latest_reconciliation.subject_linkage.get(
                    "substrate_detection_record_ids"
                )
                existing_case_ids = latest_reconciliation.subject_linkage.get("case_ids")
                linked_finding_ids = service._merge_linked_ids(
                    existing_finding_ids,
                    finding_id,
                )
                linked_signal_ids = service._merge_linked_ids(
                    existing_signal_ids,
                    analytic_signal_id,
                )
                linked_substrate_detection_ids = service._merge_linked_ids(
                    existing_substrate_detection_ids,
                    substrate_detection_record_id,
                )
                linked_case_ids = service._merge_linked_ids(
                    existing_case_ids,
                    alert.case_id,
                )
                persisted_first_seen = min(
                    latest_reconciliation.first_seen_at or first_seen_at,
                    first_seen_at,
                )
                persisted_last_seen = max(
                    latest_reconciliation.last_seen_at or last_seen_at,
                    last_seen_at,
                )
                already_linked = (
                    service._linked_id_exists(existing_finding_ids, finding_id)
                    and (
                        analytic_signal_id is None
                        or service._linked_id_exists(
                            existing_signal_ids,
                            analytic_signal_id,
                        )
                    )
                    and (
                        substrate_detection_record_id is None
                        or service._linked_id_exists(
                            existing_substrate_detection_ids,
                            substrate_detection_record_id,
                        )
                    )
                )
                if materially_new_work:
                    alert = service.persist_record(
                        replace(
                            alert,
                            finding_id=finding_id,
                            analytic_signal_id=analytic_signal_id,
                            reviewed_context=merged_reviewed_context,
                        )
                    )
                    disposition = "updated"
                elif merged_reviewed_context != alert.reviewed_context:
                    alert = service.persist_record(
                        replace(
                            alert,
                            reviewed_context=merged_reviewed_context,
                        )
                    )
                    disposition = "updated"
                elif analytic_signal_id != alert.analytic_signal_id:
                    alert = service.persist_record(
                        replace(
                            alert,
                            analytic_signal_id=analytic_signal_id,
                        )
                    )
                    disposition = "restated"
                elif already_linked:
                    disposition = "deduplicated"
                else:
                    disposition = "restated"

                if alert.case_id is not None:
                    existing_case = service._store.get(CaseRecord, alert.case_id)
                    if existing_case is None:
                        raise LookupError(
                            f"Alert {alert.alert_id!r} references missing case {alert.case_id!r}"
                        )
                    merged_case_reviewed_context = self._merge_reviewed_context(
                        existing_case.reviewed_context,
                        alert.reviewed_context,
                    )
                    if (
                        existing_case.finding_id != alert.finding_id
                        or merged_case_reviewed_context != existing_case.reviewed_context
                    ):
                        service.persist_record(
                            replace(
                                existing_case,
                                finding_id=alert.finding_id,
                                reviewed_context=merged_case_reviewed_context,
                            )
                        )

            if analytic_signal_id is not None:
                existing_signal = service._store.get(
                    AnalyticSignalRecord,
                    analytic_signal_id,
                )
                if existing_signal is not None:
                    if existing_signal.correlation_key != correlation_key:
                        raise ValueError(
                            f"Analytic signal {analytic_signal_id!r} already belongs to "
                            f"correlation key {existing_signal.correlation_key!r}"
                        )
                signal_reviewed_context = self._merge_reviewed_context(
                    alert.reviewed_context,
                    admission.reviewed_context,
                )
                signal_alert_ids = service._merge_linked_ids(
                    existing_signal.alert_ids if existing_signal is not None else (),
                    alert.alert_id,
                )
                signal_case_ids = service._merge_linked_ids(
                    existing_signal.case_ids if existing_signal is not None else (),
                    alert.case_id,
                )
                signal_first_seen = first_seen_at
                if existing_signal is not None and existing_signal.first_seen_at is not None:
                    signal_first_seen = min(existing_signal.first_seen_at, first_seen_at)
                signal_last_seen = last_seen_at
                if existing_signal is not None and existing_signal.last_seen_at is not None:
                    signal_last_seen = max(existing_signal.last_seen_at, last_seen_at)
                service.persist_record(
                    AnalyticSignalRecord(
                        analytic_signal_id=analytic_signal_id,
                        substrate_detection_record_id=(
                            substrate_detection_record_id
                            if substrate_detection_record_id is not None
                            else (
                                existing_signal.substrate_detection_record_id
                                if existing_signal is not None
                                else None
                            )
                        ),
                        finding_id=finding_id,
                        alert_ids=signal_alert_ids,
                        case_ids=signal_case_ids,
                        correlation_key=correlation_key,
                        first_seen_at=signal_first_seen,
                        last_seen_at=signal_last_seen,
                        lifecycle_state="active",
                        reviewed_context=signal_reviewed_context,
                    )
                )

            service._link_case_to_analytic_signals(linked_signal_ids, alert.case_id)

            subject_linkage = (
                dict(latest_reconciliation.subject_linkage)
                if latest_reconciliation is not None
                else {}
            )
            subject_linkage.update(
                {
                    "alert_ids": (alert.alert_id,),
                    "case_ids": linked_case_ids,
                    "substrate_detection_record_ids": linked_substrate_detection_ids,
                    "finding_ids": linked_finding_ids,
                    "analytic_signal_ids": linked_signal_ids,
                }
            )
            reconciliation = service.persist_record(
                ReconciliationRecord(
                    reconciliation_id=service._next_identifier("reconciliation"),
                    subject_linkage=subject_linkage,
                    alert_id=alert.alert_id,
                    finding_id=finding_id,
                    analytic_signal_id=analytic_signal_id,
                    execution_run_id=None,
                    linked_execution_run_ids=(),
                    correlation_key=correlation_key,
                    first_seen_at=persisted_first_seen,
                    last_seen_at=persisted_last_seen,
                    ingest_disposition=disposition,
                    mismatch_summary=f"{disposition} upstream analytic signal into alert lifecycle",
                    compared_at=datetime.now(timezone.utc),
                    lifecycle_state="matched",
                )
            )

            return FindingAlertIngestResult(
                alert=alert,
                reconciliation=reconciliation,
                disposition=disposition,
            )

    def attach_native_detection_context(
        self,
        *,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        substrate_detection_record_id: str,
    ) -> FindingAlertIngestResult:
        service = self._service
        source_system = service._normalize_optional_string(
            record.metadata.get("source_system"),
            "metadata.source_system",
        ) or record.substrate_key
        evidence_id = f"evidence-{uuid.uuid5(uuid.NAMESPACE_URL, substrate_detection_record_id)}"
        case_id = ingest_result.alert.case_id
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                source_record_id=substrate_detection_record_id,
                alert_id=ingest_result.alert.alert_id,
                case_id=case_id,
                source_system=source_system,
                collector_identity=f"{record.substrate_key}-native-detection-adapter",
                acquired_at=service._require_aware_datetime(
                    record.first_seen_at,
                    "record.first_seen_at",
                ),
                derivation_relationship="native_detection_record",
                lifecycle_state="linked" if case_id is not None else "collected",
                provenance={},
                content={},
            )
        )

        if case_id is not None:
            existing_case = service._store.get(CaseRecord, case_id)
            if existing_case is not None:
                merged_case_evidence_ids = service._merge_linked_ids(
                    existing_case.evidence_ids,
                    evidence.evidence_id,
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

        subject_linkage = dict(ingest_result.reconciliation.subject_linkage)
        subject_linkage["evidence_ids"] = service._merge_linked_ids(
            subject_linkage.get("evidence_ids"),
            evidence.evidence_id,
        )
        subject_linkage["source_systems"] = service._merge_linked_ids(
            subject_linkage.get("source_systems"),
            source_system,
        )

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

        reviewed_correlation_context = record.metadata.get("reviewed_correlation_context")
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
