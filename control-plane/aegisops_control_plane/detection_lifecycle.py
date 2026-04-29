from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Mapping

from .detection_native_context import NativeDetectionContextAttacher
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


@dataclass(frozen=True)
class _AnalyticSignalAdmissionInputs:
    finding_id: str
    analytic_signal_id: str | None
    substrate_detection_record_id: str | None
    correlation_key: str
    first_seen_at: datetime
    last_seen_at: datetime
    materially_new_work: bool
    reviewed_context: dict[str, object]


@dataclass(frozen=True)
class _AnalyticSignalAdmissionState:
    alert: AlertRecord
    disposition: str
    linked_finding_ids: tuple[str, ...]
    linked_signal_ids: tuple[str, ...]
    linked_substrate_detection_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    persisted_first_seen: datetime
    persisted_last_seen: datetime
    subject_linkage: dict[str, object]


class DetectionIntakeService:
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
        case_lifecycle_state_by_triage_disposition: Mapping[str, str],
    ) -> None:
        self._service = service
        self._merge_reviewed_context = merge_reviewed_context
        self._normalize_admission_provenance = normalize_admission_provenance
        self._case_lifecycle_state_by_triage_disposition = dict(
            case_lifecycle_state_by_triage_disposition
        )
        self._native_context_attacher = NativeDetectionContextAttacher(
            service,
            merge_reviewed_context=merge_reviewed_context,
            normalize_admission_provenance=normalize_admission_provenance,
        )

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

            evidence_records = self._list_alert_evidence_records(
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
                self._link_case_to_analytic_signals(
                    (promoted_alert.analytic_signal_id,),
                    promoted_case.case_id,
                )
            self._link_case_to_alert_reconciliations(
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
        inputs = self._resolve_admission_inputs(admission)
        with service._store.transaction():
            latest_reconciliation = service._store.latest_reconciliation_for_correlation_key(
                inputs.correlation_key,
                require_alert_id=True,
            )
            inputs = _AnalyticSignalAdmissionInputs(
                finding_id=inputs.finding_id,
                analytic_signal_id=service._resolve_analytic_signal_id(
                    analytic_signal_id=inputs.analytic_signal_id,
                    finding_id=inputs.finding_id,
                    correlation_key=inputs.correlation_key,
                    substrate_detection_record_id=inputs.substrate_detection_record_id,
                    latest_reconciliation=latest_reconciliation,
                ),
                substrate_detection_record_id=inputs.substrate_detection_record_id,
                correlation_key=inputs.correlation_key,
                first_seen_at=inputs.first_seen_at,
                last_seen_at=inputs.last_seen_at,
                materially_new_work=inputs.materially_new_work,
                reviewed_context=inputs.reviewed_context,
            )

            state = (
                self._admit_new_alert(inputs)
                if latest_reconciliation is None
                else self._merge_existing_alert_admission(
                    inputs,
                    latest_reconciliation=latest_reconciliation,
                    admission_reviewed_context=admission.reviewed_context,
                )
            )
            self._persist_analytic_signal_admission(
                inputs,
                alert=state.alert,
                admission_reviewed_context=admission.reviewed_context,
            )
            self._link_case_to_analytic_signals(
                state.linked_signal_ids,
                state.alert.case_id,
            )
            reconciliation = self._persist_admission_reconciliation(
                inputs,
                latest_reconciliation=latest_reconciliation,
                state=state,
            )
            return FindingAlertIngestResult(
                alert=state.alert,
                reconciliation=reconciliation,
                disposition=state.disposition,
            )

    def _resolve_admission_inputs(
        self,
        admission: AnalyticSignalAdmission,
    ) -> _AnalyticSignalAdmissionInputs:
        service = self._service
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
        return _AnalyticSignalAdmissionInputs(
            finding_id=service._require_non_empty_string(
                admission.finding_id,
                "finding_id",
            ),
            analytic_signal_id=service._normalize_optional_string(
                admission.analytic_signal_id,
                "analytic_signal_id",
            ),
            substrate_detection_record_id=service._normalize_optional_string(
                admission.substrate_detection_record_id,
                "substrate_detection_record_id",
            ),
            correlation_key=service._require_non_empty_string(
                admission.correlation_key,
                "correlation_key",
            ),
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
            materially_new_work=admission.materially_new_work,
            reviewed_context=self._merge_reviewed_context(
                {},
                admission.reviewed_context,
            ),
        )

    def _admit_new_alert(
        self,
        inputs: _AnalyticSignalAdmissionInputs,
    ) -> _AnalyticSignalAdmissionState:
        service = self._service
        alert = service.persist_record(
            AlertRecord(
                alert_id=service._next_identifier("alert"),
                finding_id=inputs.finding_id,
                analytic_signal_id=inputs.analytic_signal_id,
                case_id=None,
                lifecycle_state="new",
                reviewed_context=inputs.reviewed_context,
            )
        )
        return _AnalyticSignalAdmissionState(
            alert=alert,
            disposition="created",
            linked_finding_ids=(inputs.finding_id,),
            linked_signal_ids=(
                (inputs.analytic_signal_id,)
                if inputs.analytic_signal_id is not None
                else tuple()
            ),
            linked_substrate_detection_ids=service._merge_linked_ids(
                (),
                inputs.substrate_detection_record_id,
            ),
            linked_case_ids=service._merge_linked_ids((), alert.case_id),
            persisted_first_seen=inputs.first_seen_at,
            persisted_last_seen=inputs.last_seen_at,
            subject_linkage={},
        )

    def _merge_existing_alert_admission(
        self,
        inputs: _AnalyticSignalAdmissionInputs,
        *,
        latest_reconciliation: ReconciliationRecord,
        admission_reviewed_context: Mapping[str, object],
    ) -> _AnalyticSignalAdmissionState:
        service = self._service
        alert = service._store.get(AlertRecord, latest_reconciliation.alert_id)
        if alert is None:
            raise LookupError(
                f"Missing alert {latest_reconciliation.alert_id!r} "
                f"for correlation key {inputs.correlation_key!r}"
            )
        merged_reviewed_context = self._merge_reviewed_context(
            alert.reviewed_context,
            admission_reviewed_context,
        )
        existing_finding_ids = latest_reconciliation.subject_linkage.get("finding_ids")
        existing_signal_ids = latest_reconciliation.subject_linkage.get(
            "analytic_signal_ids"
        )
        existing_substrate_detection_ids = latest_reconciliation.subject_linkage.get(
            "substrate_detection_record_ids"
        )
        existing_case_ids = latest_reconciliation.subject_linkage.get("case_ids")
        already_linked = (
            service._linked_id_exists(existing_finding_ids, inputs.finding_id)
            and (
                inputs.analytic_signal_id is None
                or service._linked_id_exists(
                    existing_signal_ids,
                    inputs.analytic_signal_id,
                )
            )
            and (
                inputs.substrate_detection_record_id is None
                or service._linked_id_exists(
                    existing_substrate_detection_ids,
                    inputs.substrate_detection_record_id,
                )
            )
        )
        alert, disposition = self._persist_existing_admission_alert(
            alert=alert,
            inputs=inputs,
            merged_reviewed_context=merged_reviewed_context,
            already_linked=already_linked,
        )
        self._merge_existing_alert_case_context(alert)
        return _AnalyticSignalAdmissionState(
            alert=alert,
            disposition=disposition,
            linked_finding_ids=service._merge_linked_ids(
                existing_finding_ids,
                inputs.finding_id,
            ),
            linked_signal_ids=service._merge_linked_ids(
                existing_signal_ids,
                inputs.analytic_signal_id,
            ),
            linked_substrate_detection_ids=service._merge_linked_ids(
                existing_substrate_detection_ids,
                inputs.substrate_detection_record_id,
            ),
            linked_case_ids=service._merge_linked_ids(existing_case_ids, alert.case_id),
            persisted_first_seen=min(
                latest_reconciliation.first_seen_at or inputs.first_seen_at,
                inputs.first_seen_at,
            ),
            persisted_last_seen=max(
                latest_reconciliation.last_seen_at or inputs.last_seen_at,
                inputs.last_seen_at,
            ),
            subject_linkage=dict(latest_reconciliation.subject_linkage),
        )

    def _persist_existing_admission_alert(
        self,
        *,
        alert: AlertRecord,
        inputs: _AnalyticSignalAdmissionInputs,
        merged_reviewed_context: dict[str, object],
        already_linked: bool,
    ) -> tuple[AlertRecord, str]:
        service = self._service
        if inputs.materially_new_work:
            return (
                service.persist_record(
                    replace(
                        alert,
                        finding_id=inputs.finding_id,
                        analytic_signal_id=inputs.analytic_signal_id,
                        reviewed_context=merged_reviewed_context,
                    )
                ),
                "updated",
            )
        if merged_reviewed_context != alert.reviewed_context:
            return (
                service.persist_record(
                    replace(alert, reviewed_context=merged_reviewed_context)
                ),
                "updated",
            )
        if inputs.analytic_signal_id != alert.analytic_signal_id:
            return (
                service.persist_record(
                    replace(alert, analytic_signal_id=inputs.analytic_signal_id)
                ),
                "restated",
            )
        return alert, "deduplicated" if already_linked else "restated"

    def _merge_existing_alert_case_context(self, alert: AlertRecord) -> None:
        if alert.case_id is None:
            return
        service = self._service
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

    def _persist_analytic_signal_admission(
        self,
        inputs: _AnalyticSignalAdmissionInputs,
        *,
        alert: AlertRecord,
        admission_reviewed_context: Mapping[str, object],
    ) -> None:
        if inputs.analytic_signal_id is None:
            return
        service = self._service
        existing_signal = service._store.get(
            AnalyticSignalRecord,
            inputs.analytic_signal_id,
        )
        if (
            existing_signal is not None
            and existing_signal.correlation_key != inputs.correlation_key
        ):
            raise ValueError(
                f"Analytic signal {inputs.analytic_signal_id!r} already belongs to "
                f"correlation key {existing_signal.correlation_key!r}"
            )
        signal_first_seen = inputs.first_seen_at
        if existing_signal is not None and existing_signal.first_seen_at is not None:
            signal_first_seen = min(existing_signal.first_seen_at, inputs.first_seen_at)
        signal_last_seen = inputs.last_seen_at
        if existing_signal is not None and existing_signal.last_seen_at is not None:
            signal_last_seen = max(existing_signal.last_seen_at, inputs.last_seen_at)
        service.persist_record(
            AnalyticSignalRecord(
                analytic_signal_id=inputs.analytic_signal_id,
                substrate_detection_record_id=(
                    inputs.substrate_detection_record_id
                    if inputs.substrate_detection_record_id is not None
                    else (
                        existing_signal.substrate_detection_record_id
                        if existing_signal is not None
                        else None
                    )
                ),
                finding_id=inputs.finding_id,
                alert_ids=service._merge_linked_ids(
                    existing_signal.alert_ids if existing_signal is not None else (),
                    alert.alert_id,
                ),
                case_ids=service._merge_linked_ids(
                    existing_signal.case_ids if existing_signal is not None else (),
                    alert.case_id,
                ),
                correlation_key=inputs.correlation_key,
                first_seen_at=signal_first_seen,
                last_seen_at=signal_last_seen,
                lifecycle_state="active",
                reviewed_context=self._merge_reviewed_context(
                    alert.reviewed_context,
                    admission_reviewed_context,
                ),
            )
        )

    def _persist_admission_reconciliation(
        self,
        inputs: _AnalyticSignalAdmissionInputs,
        *,
        latest_reconciliation: ReconciliationRecord | None,
        state: _AnalyticSignalAdmissionState,
    ) -> ReconciliationRecord:
        subject_linkage = dict(state.subject_linkage)
        subject_linkage.update(
            {
                "alert_ids": (state.alert.alert_id,),
                "case_ids": state.linked_case_ids,
                "substrate_detection_record_ids": state.linked_substrate_detection_ids,
                "finding_ids": state.linked_finding_ids,
                "analytic_signal_ids": state.linked_signal_ids,
            }
        )
        return self._service.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._service._next_identifier("reconciliation"),
                subject_linkage=subject_linkage,
                alert_id=state.alert.alert_id,
                finding_id=inputs.finding_id,
                analytic_signal_id=inputs.analytic_signal_id,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=inputs.correlation_key,
                first_seen_at=state.persisted_first_seen,
                last_seen_at=state.persisted_last_seen,
                ingest_disposition=state.disposition,
                mismatch_summary=(
                    f"{state.disposition} upstream analytic signal into alert lifecycle"
                ),
                compared_at=datetime.now(timezone.utc),
                lifecycle_state="matched",
            )
        )

    def attach_native_detection_context(
        self,
        *,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        substrate_detection_record_id: str,
    ) -> FindingAlertIngestResult:
        return self._native_context_attacher.attach_native_detection_context(
            record=record,
            ingest_result=ingest_result,
            substrate_detection_record_id=substrate_detection_record_id,
        )

    def reviewed_context_transitioned_at(
        self,
        record: AlertRecord | CaseRecord,
    ) -> datetime | None:
        reviewed_context = getattr(record, "reviewed_context", None)
        if not isinstance(reviewed_context, Mapping):
            return None
        triage = reviewed_context.get("triage")
        if not isinstance(triage, Mapping):
            return None
        if not self.triage_disposition_matches_current_state(
            record,
            triage.get("disposition"),
        ):
            return None
        raw_recorded_at = triage.get("recorded_at")
        if not isinstance(raw_recorded_at, str) or not raw_recorded_at.strip():
            return None
        try:
            parsed = datetime.fromisoformat(raw_recorded_at)
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed

    def _link_case_to_analytic_signals(
        self,
        analytic_signal_ids: tuple[str, ...],
        case_id: str | None,
    ) -> None:
        if case_id is None:
            return

        service = self._service
        for analytic_signal_id in analytic_signal_ids:
            existing_signal = service._store.get(
                AnalyticSignalRecord,
                analytic_signal_id,
            )
            if existing_signal is None:
                continue
            linked_case_ids = service._merge_linked_ids(
                existing_signal.case_ids,
                case_id,
            )
            if linked_case_ids == existing_signal.case_ids:
                continue
            service.persist_record(
                AnalyticSignalRecord(
                    analytic_signal_id=existing_signal.analytic_signal_id,
                    substrate_detection_record_id=(
                        existing_signal.substrate_detection_record_id
                    ),
                    finding_id=existing_signal.finding_id,
                    alert_ids=existing_signal.alert_ids,
                    case_ids=linked_case_ids,
                    correlation_key=existing_signal.correlation_key,
                    first_seen_at=existing_signal.first_seen_at,
                    last_seen_at=existing_signal.last_seen_at,
                    lifecycle_state=existing_signal.lifecycle_state,
                    reviewed_context=existing_signal.reviewed_context,
                )
            )

    def _list_alert_evidence_records(
        self,
        *,
        alert_id: str,
        case_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        evidence_records: list[EvidenceRecord] = []
        for evidence in self._service._store.list(EvidenceRecord):
            if evidence.alert_id == alert_id or (
                case_id is not None and evidence.case_id == case_id
            ):
                evidence_records.append(evidence)
        return tuple(evidence_records)

    def _link_case_to_alert_reconciliations(
        self,
        *,
        alert_id: str,
        case_id: str,
        evidence_ids: tuple[str, ...],
    ) -> None:
        service = self._service
        for reconciliation in service._store.list(ReconciliationRecord):
            if reconciliation.alert_id != alert_id:
                continue
            subject_linkage = dict(reconciliation.subject_linkage)
            updated_case_ids = service._merge_linked_ids(
                subject_linkage.get("case_ids"),
                case_id,
            )
            updated_evidence_ids = service._merge_linked_ids(
                subject_linkage.get("evidence_ids"),
                None,
            )
            for evidence_id in evidence_ids:
                updated_evidence_ids = service._merge_linked_ids(
                    updated_evidence_ids,
                    evidence_id,
                )
            if (
                tuple(subject_linkage.get("case_ids", ())) == updated_case_ids
                and tuple(subject_linkage.get("evidence_ids", ()))
                == updated_evidence_ids
            ):
                continue
            subject_linkage["case_ids"] = updated_case_ids
            subject_linkage["evidence_ids"] = updated_evidence_ids
            service.persist_record(
                ReconciliationRecord(
                    reconciliation_id=reconciliation.reconciliation_id,
                    subject_linkage=subject_linkage,
                    alert_id=reconciliation.alert_id,
                    finding_id=reconciliation.finding_id,
                    analytic_signal_id=reconciliation.analytic_signal_id,
                    execution_run_id=reconciliation.execution_run_id,
                    linked_execution_run_ids=(
                        reconciliation.linked_execution_run_ids
                    ),
                    correlation_key=reconciliation.correlation_key,
                    first_seen_at=reconciliation.first_seen_at,
                    last_seen_at=reconciliation.last_seen_at,
                    ingest_disposition=reconciliation.ingest_disposition,
                    mismatch_summary=reconciliation.mismatch_summary,
                    compared_at=reconciliation.compared_at,
                    lifecycle_state=reconciliation.lifecycle_state,
                )
            )

    def triage_disposition_matches_current_state(
        self,
        record: AlertRecord | CaseRecord,
        disposition: object,
    ) -> bool:
        triage_lifecycle_state = self.case_lifecycle_state_for_triage_disposition(
            disposition
        )
        if triage_lifecycle_state is None:
            return False
        if isinstance(record, AlertRecord):
            return record.lifecycle_state == "closed" and triage_lifecycle_state == "closed"
        return record.lifecycle_state == triage_lifecycle_state

    def case_lifecycle_state_for_triage_disposition(
        self,
        disposition: object,
    ) -> str | None:
        if not isinstance(disposition, str) or not disposition.strip():
            return None
        return self._case_lifecycle_state_by_triage_disposition.get(disposition)

    def case_lifecycle_for_disposition(self, disposition: str) -> str:
        lifecycle_state = self.case_lifecycle_state_for_triage_disposition(disposition)
        if lifecycle_state is not None:
            return lifecycle_state
        raise ValueError(f"Unsupported case disposition {disposition!r}")


DetectionLifecycleService = DetectionIntakeService
