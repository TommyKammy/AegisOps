from __future__ import annotations

from typing import Any, Mapping

from ..models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


class AITraceLifecycleService:
    """Owns AI trace linkage helpers used by advisory assembly."""

    def __init__(self, store: Any) -> None:
        self._store = store

    @staticmethod
    def ids_from_value(value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(item for item in value if isinstance(item, str))
        return ()

    def ids_from_mapping(
        self,
        mapping: Mapping[str, object],
        key: str,
    ) -> tuple[str, ...]:
        return self.ids_from_value(mapping.get(key))

    @staticmethod
    def merge_ids(
        existing_values: object,
        incoming_values: object,
    ) -> tuple[str, ...]:
        merged: list[str] = []
        if isinstance(existing_values, (list, tuple)):
            for value in existing_values:
                if isinstance(value, str) and value not in merged:
                    merged.append(value)
        if isinstance(incoming_values, (list, tuple)):
            for value in incoming_values:
                if isinstance(value, str) and value not in merged:
                    merged.append(value)
        elif isinstance(incoming_values, str) and incoming_values not in merged:
            merged.append(incoming_values)
        return tuple(merged)

    @staticmethod
    def primary_linked_id(linked_ids: tuple[str, ...]) -> str | None:
        return linked_ids[0] if linked_ids else None

    def action_lineage_ids(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        action_request_ids = self.ids_from_value(getattr(record, "action_request_id", None))
        approval_decision_ids = self.ids_from_value(
            getattr(record, "approval_decision_id", None)
        )
        action_execution_ids = self.ids_from_value(
            getattr(record, "action_execution_id", None)
        )
        delegation_ids = self.ids_from_value(getattr(record, "delegation_id", None))
        if isinstance(record, ReconciliationRecord):
            action_request_ids = self.merge_ids(
                action_request_ids,
                self.ids_from_mapping(record.subject_linkage, "action_request_ids"),
            )
            approval_decision_ids = self.merge_ids(
                approval_decision_ids,
                self.ids_from_mapping(record.subject_linkage, "approval_decision_ids"),
            )
            action_execution_ids = self.merge_ids(
                action_execution_ids,
                self.ids_from_mapping(record.subject_linkage, "action_execution_ids"),
            )
            delegation_ids = self.merge_ids(
                delegation_ids,
                self.ids_from_mapping(record.subject_linkage, "delegation_ids"),
            )
        return (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        )

    def merge_action_request_linkage(
        self,
        *,
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
        action_request: ActionRequestRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return (
            self.merge_ids(linked_alert_ids, action_request.alert_id),
            self.merge_ids(linked_case_ids, action_request.case_id),
            self.merge_ids(linked_finding_ids, action_request.finding_id),
        )

    def action_execution_for_delegation_id(
        self,
        delegation_id: str,
    ) -> ActionExecutionRecord | None:
        for execution in self._store.list(ActionExecutionRecord):
            if execution.delegation_id == delegation_id:
                return execution
        return None

    def ai_trace_records_for_context(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[AITraceRecord, ...]:
        records: list[AITraceRecord] = []
        seen_trace_ids: set[str] = set()

        def add_trace(trace: AITraceRecord | None) -> None:
            if trace is None or trace.ai_trace_id in seen_trace_ids:
                return
            seen_trace_ids.add(trace.ai_trace_id)
            records.append(trace)

        ai_trace_id = getattr(record, "ai_trace_id", None)
        if ai_trace_id is not None:
            add_trace(self._store.get(AITraceRecord, ai_trace_id))
        if isinstance(record, AITraceRecord):
            add_trace(record)

        record_recommendation_id = getattr(record, "recommendation_id", None)
        if record_recommendation_id is not None:
            for trace in self._store.list(AITraceRecord):
                if trace.ai_trace_id in seen_trace_ids:
                    continue
                if record_recommendation_id in self.ids_from_mapping(
                    trace.subject_linkage,
                    "recommendation_ids",
                ):
                    add_trace(trace)

        return tuple(records)

    def ai_trace_evidence_ids(
        self,
        ai_trace_record: AITraceRecord,
    ) -> tuple[str, ...]:
        linked_evidence_ids = self.ids_from_mapping(
            ai_trace_record.subject_linkage,
            "evidence_ids",
        )
        linked_evidence_ids = self.merge_ids(
            linked_evidence_ids,
            ai_trace_record.material_input_refs,
        )
        return tuple(
            evidence_id
            for evidence_id in linked_evidence_ids
            if self._store.get(EvidenceRecord, evidence_id) is not None
        )

    def linked_evidence_ids(self, record: ControlPlaneRecord) -> tuple[str, ...]:
        linked_evidence_ids = self.ids_from_value(getattr(record, "evidence_ids", ()))
        linked_evidence_ids = self.merge_ids(
            linked_evidence_ids,
            getattr(record, "supporting_evidence_ids", ()),
        )
        if isinstance(record, ActionExecutionRecord):
            linked_evidence_ids = self.merge_ids(
                linked_evidence_ids,
                self.ids_from_mapping(record.provenance, "evidence_ids"),
            )
        if isinstance(record, ReconciliationRecord):
            linked_evidence_ids = self.merge_ids(
                linked_evidence_ids,
                self.ids_from_mapping(record.subject_linkage, "evidence_ids"),
            )
        for ai_trace_record in self.ai_trace_records_for_context(record):
            linked_evidence_ids = self.merge_ids(
                linked_evidence_ids,
                self.ai_trace_evidence_ids(ai_trace_record),
            )
        return linked_evidence_ids

    def evidence_siblings(self, record: EvidenceRecord) -> tuple[str, ...]:
        evidence_records = self.evidence_records_for_context(
            alert_ids=self.ids_from_value(record.alert_id),
            case_ids=self.ids_from_value(record.case_id),
            evidence_ids=(),
            exclude_evidence_id=record.evidence_id,
        )
        return tuple(evidence.evidence_id for evidence in evidence_records)

    def evidence_records_for_context(
        self,
        *,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_evidence_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        records: list[EvidenceRecord] = []
        seen_ids: set[str] = set()
        for evidence_id in evidence_ids:
            evidence = self._store.get(EvidenceRecord, evidence_id)
            if evidence is None:
                continue
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            seen_ids.add(evidence.evidence_id)
            records.append(evidence)
        for evidence in self._store.list(EvidenceRecord):
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            if evidence.alert_id in alert_ids or (
                evidence.case_id is not None and evidence.case_id in case_ids
            ):
                seen_ids.add(evidence.evidence_id)
                records.append(evidence)
        records.sort(key=lambda evidence: evidence.evidence_id)
        return tuple(records)

    def recommendation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        ai_trace_records: tuple[AITraceRecord, ...],
        exclude_recommendation_id: str | None,
    ) -> tuple[RecommendationRecord, ...]:
        records: list[RecommendationRecord] = []
        lead_id = getattr(record, "lead_id", None)
        hunt_run_id = getattr(record, "hunt_run_id", None)
        ai_trace_id = getattr(record, "ai_trace_id", None)
        ai_trace_recommendation_ids: set[str] = set()
        for ai_trace_record in ai_trace_records:
            ai_trace_recommendation_ids.update(
                self.ids_from_mapping(
                    ai_trace_record.subject_linkage,
                    "recommendation_ids",
                )
            )
        for recommendation in self._store.list(RecommendationRecord):
            if (
                exclude_recommendation_id is not None
                and recommendation.recommendation_id == exclude_recommendation_id
            ):
                continue
            if recommendation.alert_id in alert_ids:
                records.append(recommendation)
                continue
            if recommendation.case_id is not None and recommendation.case_id in case_ids:
                records.append(recommendation)
                continue
            if lead_id is not None and recommendation.lead_id == lead_id:
                records.append(recommendation)
                continue
            if hunt_run_id is not None and recommendation.hunt_run_id == hunt_run_id:
                records.append(recommendation)
                continue
            if ai_trace_id is not None and recommendation.ai_trace_id == ai_trace_id:
                records.append(recommendation)
                continue
            if recommendation.recommendation_id in ai_trace_recommendation_ids:
                records.append(recommendation)
        records.sort(key=lambda recommendation: recommendation.recommendation_id)
        return tuple(records)

    def reconciliation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        finding_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_reconciliation_id: str | None,
    ) -> tuple[ReconciliationRecord, ...]:
        records: list[ReconciliationRecord] = []
        analytic_signal_id = getattr(record, "analytic_signal_id", None)
        finding_id = getattr(record, "finding_id", None)
        (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        ) = self.action_lineage_ids(record)
        linked_finding_ids = set(finding_ids)
        for reconciliation in self._store.list(ReconciliationRecord):
            if (
                exclude_reconciliation_id is not None
                and reconciliation.reconciliation_id == exclude_reconciliation_id
            ):
                continue
            subject_action_request_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            )
            if any(
                action_request_id in subject_action_request_ids
                for action_request_id in action_request_ids
            ):
                records.append(reconciliation)
                continue
            subject_approval_decision_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            )
            if any(
                approval_decision_id in subject_approval_decision_ids
                for approval_decision_id in approval_decision_ids
            ):
                records.append(reconciliation)
                continue
            subject_action_execution_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            if any(
                action_execution_id in subject_action_execution_ids
                for action_execution_id in action_execution_ids
            ):
                records.append(reconciliation)
                continue
            subject_delegation_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            )
            if any(delegation_id in subject_delegation_ids for delegation_id in delegation_ids):
                records.append(reconciliation)
                continue
            if reconciliation.alert_id is not None and reconciliation.alert_id in alert_ids:
                records.append(reconciliation)
                continue
            if (
                analytic_signal_id is not None
                and reconciliation.analytic_signal_id == analytic_signal_id
            ):
                records.append(reconciliation)
                continue
            subject_alert_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "alert_ids",
            )
            if any(alert_id in subject_alert_ids for alert_id in alert_ids):
                records.append(reconciliation)
                continue
            subject_analytic_signal_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "analytic_signal_ids",
            )
            if (
                analytic_signal_id is not None
                and analytic_signal_id in subject_analytic_signal_ids
            ):
                records.append(reconciliation)
                continue
            if finding_id is not None and reconciliation.finding_id == finding_id:
                records.append(reconciliation)
                continue
            if (
                reconciliation.finding_id is not None
                and reconciliation.finding_id in linked_finding_ids
            ):
                records.append(reconciliation)
                continue
            subject_finding_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "finding_ids",
            )
            if any(finding_id in subject_finding_ids for finding_id in linked_finding_ids):
                records.append(reconciliation)
                continue
            subject_case_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "case_ids",
            )
            if any(case_id in subject_case_ids for case_id in case_ids):
                records.append(reconciliation)
                continue
            subject_evidence_ids = self.ids_from_mapping(
                reconciliation.subject_linkage,
                "evidence_ids",
            )
            if any(evidence_id in subject_evidence_ids for evidence_id in evidence_ids):
                records.append(reconciliation)
        records.sort(key=lambda reconciliation: reconciliation.reconciliation_id)
        return tuple(records)
