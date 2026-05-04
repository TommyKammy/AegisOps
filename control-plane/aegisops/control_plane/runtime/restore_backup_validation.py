from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Type

from ..models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from ..record_validation import _validate_lifecycle_state, _validate_record


@dataclass(frozen=True)
class _RestoreRecordFamilies:
    analytic_signals: tuple[AnalyticSignalRecord, ...]
    alerts: tuple[AlertRecord, ...]
    evidence: tuple[EvidenceRecord, ...]
    observations: tuple[ObservationRecord, ...]
    leads: tuple[LeadRecord, ...]
    cases: tuple[CaseRecord, ...]
    recommendations: tuple[RecommendationRecord, ...]
    lifecycle_transitions: tuple[LifecycleTransitionRecord, ...]
    approval_decisions: tuple[ApprovalDecisionRecord, ...]
    action_requests: tuple[ActionRequestRecord, ...]
    action_executions: tuple[ActionExecutionRecord, ...]
    hunts: tuple[HuntRecord, ...]
    hunt_runs: tuple[HuntRunRecord, ...]
    ai_traces: tuple[AITraceRecord, ...]
    reconciliations: tuple[ReconciliationRecord, ...]

    @property
    def by_family(self) -> tuple[tuple[str, tuple[ControlPlaneRecord, ...]], ...]:
        return (
            ("analytic_signal", self.analytic_signals),
            ("alert", self.alerts),
            ("evidence", self.evidence),
            ("observation", self.observations),
            ("lead", self.leads),
            ("case", self.cases),
            ("recommendation", self.recommendations),
            ("lifecycle_transition", self.lifecycle_transitions),
            ("approval_decision", self.approval_decisions),
            ("action_request", self.action_requests),
            ("action_execution", self.action_executions),
            ("hunt", self.hunts),
            ("hunt_run", self.hunt_runs),
            ("ai_trace", self.ai_traces),
            ("reconciliation", self.reconciliations),
        )


@dataclass(frozen=True)
class _RestoreRecordIndexes:
    analytic_signals: Mapping[str, AnalyticSignalRecord]
    alerts: Mapping[str, AlertRecord]
    evidence: Mapping[str, EvidenceRecord]
    observations: Mapping[str, ObservationRecord]
    leads: Mapping[str, LeadRecord]
    cases: Mapping[str, CaseRecord]
    recommendations: Mapping[str, RecommendationRecord]
    approval_decisions: Mapping[str, ApprovalDecisionRecord]
    action_requests: Mapping[str, ActionRequestRecord]
    action_executions: Mapping[str, ActionExecutionRecord]
    hunts: Mapping[str, HuntRecord]
    hunt_runs: Mapping[str, HuntRunRecord]
    ai_traces: Mapping[str, AITraceRecord]
    action_executions_by_run_id: Mapping[str, ActionExecutionRecord]
    reconciliations: Mapping[str, ReconciliationRecord]

    @property
    def authoritative_subject_ids_by_family(self) -> dict[str, set[str]]:
        return {
            "analytic_signal": set(self.analytic_signals),
            "alert": set(self.alerts),
            "evidence": set(self.evidence),
            "observation": set(self.observations),
            "lead": set(self.leads),
            "case": set(self.cases),
            "recommendation": set(self.recommendations),
            "approval_decision": set(self.approval_decisions),
            "action_request": set(self.action_requests),
            "action_execution": set(self.action_executions),
            "hunt": set(self.hunts),
            "hunt_run": set(self.hunt_runs),
            "ai_trace": set(self.ai_traces),
            "reconciliation": set(self.reconciliations),
        }

    @property
    def authoritative_subject_records_by_family(
        self,
    ) -> dict[str, Mapping[str, ControlPlaneRecord]]:
        return {
            "analytic_signal": self.analytic_signals,
            "alert": self.alerts,
            "evidence": self.evidence,
            "observation": self.observations,
            "lead": self.leads,
            "case": self.cases,
            "recommendation": self.recommendations,
            "approval_decision": self.approval_decisions,
            "action_request": self.action_requests,
            "action_execution": self.action_executions,
            "hunt": self.hunts,
            "hunt_run": self.hunt_runs,
            "ai_trace": self.ai_traces,
            "reconciliation": self.reconciliations,
        }

class RestoreValidationBoundary:
    def __init__(
        self,
        *,
        authoritative_primary_id_field_by_family: Mapping[str, str],
        find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        assistant_ids_from_mapping: Callable[[Mapping[str, object], str], tuple[str, ...]],
    ) -> None:
        self._authoritative_primary_id_field_by_family = (
            authoritative_primary_id_field_by_family
        )
        self._find_duplicate_strings = find_duplicate_strings
        self._assistant_ids_from_mapping = assistant_ids_from_mapping

    def _duplicate_restore_count_suffix(
        self,
        family: str,
        restored_record_counts: Mapping[str, int] | None,
    ) -> str:
        if restored_record_counts is None:
            return ""
        return (
            "; restored_record_counts"
            f"[{family!r}]={restored_record_counts.get(family)!r}"
        )

    def _require_restore_family_records(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        family: str,
        expected_type: Type[ControlPlaneRecord],
    ) -> tuple[ControlPlaneRecord, ...]:
        family_records = tuple(records_by_family.get(family, ()))
        unexpected_types = tuple(
            type(record).__name__
            for record in family_records
            if not isinstance(record, expected_type)
        )
        if unexpected_types:
            raise ValueError(
                "restore payload contains unexpected record types for "
                f"{family!r}: {unexpected_types!r}"
            )
        return family_records

    def _collect_restore_record_families(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
    ) -> _RestoreRecordFamilies:
        return _RestoreRecordFamilies(
            analytic_signals=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "analytic_signal",
                    AnalyticSignalRecord,
                )
            ),
            alerts=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "alert",
                    AlertRecord,
                )
            ),
            evidence=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "evidence",
                    EvidenceRecord,
                )
            ),
            observations=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "observation",
                    ObservationRecord,
                )
            ),
            leads=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "lead",
                    LeadRecord,
                )
            ),
            cases=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "case",
                    CaseRecord,
                )
            ),
            recommendations=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "recommendation",
                    RecommendationRecord,
                )
            ),
            lifecycle_transitions=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "lifecycle_transition",
                    LifecycleTransitionRecord,
                )
            ),
            approval_decisions=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "approval_decision",
                    ApprovalDecisionRecord,
                )
            ),
            action_requests=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "action_request",
                    ActionRequestRecord,
                )
            ),
            action_executions=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "action_execution",
                    ActionExecutionRecord,
                )
            ),
            hunts=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "hunt",
                    HuntRecord,
                )
            ),
            hunt_runs=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "hunt_run",
                    HuntRunRecord,
                )
            ),
            ai_traces=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "ai_trace",
                    AITraceRecord,
                )
            ),
            reconciliations=tuple(
                self._require_restore_family_records(
                    records_by_family,
                    "reconciliation",
                    ReconciliationRecord,
                )
            ),
        )

    def _reject_duplicate_restore_identifiers(
        self,
        families: _RestoreRecordFamilies,
        *,
        restored_record_counts: Mapping[str, int] | None,
    ) -> None:
        for family, records in families.by_family:
            duplicates = self._find_duplicate_strings(
                tuple(
                    getattr(record, self._authoritative_primary_id_field_by_family[family])
                    for record in records
                )
            )
            if duplicates:
                raise ValueError(
                    "restore payload contains duplicate "
                    f"{family} identifiers {duplicates!r}"
                    f"{self._duplicate_restore_count_suffix(family, restored_record_counts)}"
                )

        duplicate_execution_run_ids = self._find_duplicate_strings(
            tuple(
                record.execution_run_id
                for record in families.action_executions
                if record.execution_run_id is not None
            )
        )
        if duplicate_execution_run_ids:
            raise ValueError(
                "restore payload contains duplicate action_execution "
                f"execution_run_id values {duplicate_execution_run_ids!r}"
                f"{self._duplicate_restore_count_suffix('action_execution', restored_record_counts)}"
            )

    def _validate_restore_record_shapes(
        self,
        families: _RestoreRecordFamilies,
    ) -> None:
        for record in (
            *families.observations,
            *families.leads,
            *families.recommendations,
        ):
            _validate_record(record)

    def _build_restore_record_indexes(
        self,
        families: _RestoreRecordFamilies,
    ) -> _RestoreRecordIndexes:
        return _RestoreRecordIndexes(
            analytic_signals={
                record.analytic_signal_id: record
                for record in families.analytic_signals
            },
            alerts={record.alert_id: record for record in families.alerts},
            evidence={record.evidence_id: record for record in families.evidence},
            observations={
                record.observation_id: record for record in families.observations
            },
            leads={record.lead_id: record for record in families.leads},
            cases={record.case_id: record for record in families.cases},
            recommendations={
                record.recommendation_id: record
                for record in families.recommendations
            },
            approval_decisions={
                record.approval_decision_id: record
                for record in families.approval_decisions
            },
            action_requests={
                record.action_request_id: record
                for record in families.action_requests
            },
            action_executions={
                record.action_execution_id: record
                for record in families.action_executions
            },
            hunts={record.hunt_id: record for record in families.hunts},
            hunt_runs={
                record.hunt_run_id: record for record in families.hunt_runs
            },
            ai_traces={record.ai_trace_id: record for record in families.ai_traces},
            action_executions_by_run_id={
                record.execution_run_id: record
                for record in families.action_executions
                if record.execution_run_id is not None
            },
            reconciliations={
                record.reconciliation_id: record
                for record in families.reconciliations
            },
        )

    def _validate_restore_record_links(
        self,
        families: _RestoreRecordFamilies,
        indexes: _RestoreRecordIndexes,
    ) -> None:
        for alert in indexes.alerts.values():
            if alert.analytic_signal_id and alert.analytic_signal_id not in indexes.analytic_signals:
                raise ValueError(
                    f"missing analytic_signal record {alert.analytic_signal_id!r} required by alert "
                    f"{alert.alert_id!r}"
                )
            if (
                alert.analytic_signal_id
                and alert.alert_id
                not in indexes.analytic_signals[alert.analytic_signal_id].alert_ids
            ):
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match analytic signal binding "
                    f"{alert.analytic_signal_id!r}"
                )
            if alert.case_id and alert.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {alert.case_id!r} required by alert {alert.alert_id!r}"
                )
            if alert.case_id and indexes.cases[alert.case_id].alert_id != alert.alert_id:
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match case binding {alert.case_id!r}"
                )

        for analytic_signal in indexes.analytic_signals.values():
            for alert_id in analytic_signal.alert_ids:
                if alert_id not in indexes.alerts:
                    raise ValueError(
                        f"missing alert record {alert_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )
                if indexes.alerts[alert_id].analytic_signal_id != analytic_signal.analytic_signal_id:
                    raise ValueError(
                        f"analytic signal {analytic_signal.analytic_signal_id!r} does not match "
                        f"alert binding {alert_id!r}"
                    )
            for case_id in analytic_signal.case_ids:
                if case_id not in indexes.cases:
                    raise ValueError(
                        f"missing case record {case_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )

        for evidence in indexes.evidence.values():
            if evidence.alert_id and evidence.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {evidence.alert_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )
            if evidence.case_id and evidence.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {evidence.case_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )

        for observation in indexes.observations.values():
            if observation.hunt_id and observation.hunt_id not in indexes.hunts:
                raise ValueError(
                    f"missing hunt record {observation.hunt_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.hunt_run_id and observation.hunt_run_id not in indexes.hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {observation.hunt_run_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.alert_id and observation.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {observation.alert_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.case_id and observation.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {observation.case_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            for evidence_id in observation.supporting_evidence_ids:
                if evidence_id not in indexes.evidence:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by observation "
                        f"{observation.observation_id!r}"
                    )

        for lead in indexes.leads.values():
            if lead.observation_id and lead.observation_id not in indexes.observations:
                raise ValueError(
                    f"missing observation record {lead.observation_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.hunt_run_id and lead.hunt_run_id not in indexes.hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {lead.hunt_run_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.alert_id and lead.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {lead.alert_id!r} required by lead {lead.lead_id!r}"
                )
            if lead.case_id and lead.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {lead.case_id!r} required by lead {lead.lead_id!r}"
                )

        for case in indexes.cases.values():
            if case.alert_id and case.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {case.alert_id!r} required by case {case.case_id!r}"
                )
            if case.alert_id and indexes.alerts[case.alert_id].case_id != case.case_id:
                raise ValueError(
                    f"case {case.case_id!r} does not match alert binding {case.alert_id!r}"
                )
            for evidence_id in case.evidence_ids:
                if evidence_id not in indexes.evidence:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by case {case.case_id!r}"
                    )

        for recommendation in indexes.recommendations.values():
            if recommendation.lead_id and recommendation.lead_id not in indexes.leads:
                raise ValueError(
                    "missing lead record "
                    f"{recommendation.lead_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.hunt_run_id and recommendation.hunt_run_id not in indexes.hunt_runs:
                raise ValueError(
                    "missing hunt_run record "
                    f"{recommendation.hunt_run_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.alert_id and recommendation.alert_id not in indexes.alerts:
                raise ValueError(
                    "missing alert record "
                    f"{recommendation.alert_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.case_id and recommendation.case_id not in indexes.cases:
                raise ValueError(
                    "missing case record "
                    f"{recommendation.case_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.ai_trace_id and recommendation.ai_trace_id not in indexes.ai_traces:
                raise ValueError(
                    "missing ai_trace record "
                    f"{recommendation.ai_trace_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )

        for hunt in indexes.hunts.values():
            if hunt.alert_id and hunt.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {hunt.alert_id!r} required by hunt {hunt.hunt_id!r}"
                )
            if hunt.case_id and hunt.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {hunt.case_id!r} required by hunt {hunt.hunt_id!r}"
                )

        for hunt_run in indexes.hunt_runs.values():
            if hunt_run.hunt_id not in indexes.hunts:
                raise ValueError(
                    f"missing hunt record {hunt_run.hunt_id!r} required by hunt_run "
                    f"{hunt_run.hunt_run_id!r}"
                )

        self._validate_restore_approval_and_execution_links(indexes)
        self._validate_restore_reconciliation_links(families, indexes)

    def _validate_restore_approval_and_execution_links(
        self,
        indexes: _RestoreRecordIndexes,
    ) -> None:
        for approval_decision in indexes.approval_decisions.values():
            action_request = indexes.action_requests.get(approval_decision.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {approval_decision.action_request_id!r} required by "
                    f"approval decision {approval_decision.approval_decision_id!r}"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request payload binding"
                )

        for action_request in indexes.action_requests.values():
            if action_request.case_id and action_request.case_id not in indexes.cases:
                raise ValueError(
                    f"missing case record {action_request.case_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if action_request.alert_id and action_request.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {action_request.alert_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if (
                action_request.approval_decision_id
                and action_request.approval_decision_id not in indexes.approval_decisions
            ):
                raise ValueError(
                    f"missing approval_decision record {action_request.approval_decision_id!r} "
                    f"required by action request {action_request.action_request_id!r}"
                )
            approval_decision = indexes.approval_decisions.get(action_request.approval_decision_id)
            if approval_decision is None:
                continue
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision payload binding"
                )

        for action_execution in indexes.action_executions.values():
            action_request = indexes.action_requests.get(action_execution.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {action_execution.action_request_id!r} required by "
                    f"action execution {action_execution.action_execution_id!r}"
                )
            if action_execution.approval_decision_id not in indexes.approval_decisions:
                raise ValueError(
                    f"missing approval_decision record {action_execution.approval_decision_id!r} "
                    f"required by action execution {action_execution.action_execution_id!r}"
                )
            approval_decision = indexes.approval_decisions[action_execution.approval_decision_id]
            if action_request.approval_decision_id != action_execution.approval_decision_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    f"request approval binding"
                )
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision binding"
                )
            if action_execution.idempotency_key != action_request.idempotency_key:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request idempotency binding"
                )
            if action_execution.target_scope != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request target binding"
                )
            if action_execution.approved_payload != action_request.requested_payload:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request approved payload binding"
                )
            if action_execution.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request payload binding"
                )
            policy_evaluation = action_request.policy_evaluation
            if (
                policy_evaluation.get("execution_surface_type")
                != action_execution.execution_surface_type
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if (
                policy_evaluation.get("execution_surface_id")
                != action_execution.execution_surface_id
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision payload binding"
                )
            if approval_decision.approved_expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision expiry binding"
                )
            if action_execution.expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request expiry binding"
                )
            if (
                approval_decision.approved_expires_at is not None
                and action_execution.delegated_at > approval_decision.approved_expires_at
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} exceeds approval "
                    "expiry binding"
                )

    def _validate_restore_reconciliation_links(
        self,
        families: _RestoreRecordFamilies,
        indexes: _RestoreRecordIndexes,
    ) -> None:
        for reconciliation in families.reconciliations:
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            subject_execution_run_ids = {
                indexes.action_executions[action_execution_id].execution_run_id
                for action_execution_id in subject_action_execution_ids
                if action_execution_id in indexes.action_executions
                and indexes.action_executions[action_execution_id].execution_run_id is not None
            }
            if reconciliation.alert_id and reconciliation.alert_id not in indexes.alerts:
                raise ValueError(
                    f"missing alert record {reconciliation.alert_id!r} required by reconciliation "
                    f"{reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.analytic_signal_id
                and reconciliation.analytic_signal_id not in indexes.analytic_signals
            ):
                raise ValueError(
                    f"missing analytic_signal record {reconciliation.analytic_signal_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id
                and reconciliation.execution_run_id not in indexes.action_executions_by_run_id
            ):
                raise ValueError(
                    f"missing action execution run {reconciliation.execution_run_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id is not None
                and subject_execution_run_ids
                and reconciliation.execution_run_id not in subject_execution_run_ids
            ):
                raise ValueError(
                    f"reconciliation {reconciliation.reconciliation_id!r} does not match its action "
                    "execution run binding"
                )
            for linked_execution_run_id in reconciliation.linked_execution_run_ids:
                if linked_execution_run_id not in indexes.action_executions_by_run_id:
                    raise ValueError(
                        f"missing action execution run {linked_execution_run_id!r} required by "
                        f"reconciliation {reconciliation.reconciliation_id!r}"
                    )
                if (
                    subject_execution_run_ids
                    and linked_execution_run_id not in subject_execution_run_ids
                ):
                    raise ValueError(
                        f"reconciliation {reconciliation.reconciliation_id!r} does not match its linked "
                        "action execution runs"
                    )
            for field_name, known_ids in (
                ("analytic_signal_ids", indexes.analytic_signals),
                ("alert_ids", indexes.alerts),
                ("case_ids", indexes.cases),
                ("evidence_ids", indexes.evidence),
                ("approval_decision_ids", indexes.approval_decisions),
                ("action_request_ids", indexes.action_requests),
                ("action_execution_ids", indexes.action_executions),
            ):
                for linked_id in self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    field_name,
                ):
                    if linked_id not in known_ids:
                        singular_name = (
                            field_name[:-4]
                            if field_name.endswith("_ids")
                            else field_name
                        )
                        raise ValueError(
                            f"missing {singular_name} record {linked_id!r} required by reconciliation "
                            f"{reconciliation.reconciliation_id!r}"
                        )

    def _validate_restore_lifecycle_transitions(
        self,
        families: _RestoreRecordFamilies,
        indexes: _RestoreRecordIndexes,
        *,
        require_lifecycle_transition_history: bool,
    ) -> None:
        lifecycle_transitions_by_subject: dict[
            tuple[str, str], list[LifecycleTransitionRecord]
        ] = {}
        authoritative_subject_ids_by_family = indexes.authoritative_subject_ids_by_family
        for transition in families.lifecycle_transitions:
            subject_ids = authoritative_subject_ids_by_family.get(
                transition.subject_record_family
            )
            if subject_ids is None:
                raise ValueError(
                    "lifecycle transition "
                    f"{transition.transition_id!r} references unsupported subject_record_family "
                    f"{transition.subject_record_family!r}"
                )
            if transition.subject_record_id not in subject_ids:
                raise ValueError(
                    "missing "
                    f"{transition.subject_record_family} record {transition.subject_record_id!r} "
                    f"required by lifecycle transition {transition.transition_id!r}"
                )
            _validate_lifecycle_state(transition)
            lifecycle_transitions_by_subject.setdefault(
                (
                    transition.subject_record_family,
                    transition.subject_record_id,
                ),
                [],
            ).append(transition)

        authoritative_subject_records_by_family = (
            indexes.authoritative_subject_records_by_family
        )
        if require_lifecycle_transition_history:
            for subject_family, subject_records in authoritative_subject_records_by_family.items():
                for subject_id, subject_record in subject_records.items():
                    subject_lifecycle_state = getattr(
                        subject_record,
                        "lifecycle_state",
                        None,
                    )
                    if (
                        not isinstance(subject_lifecycle_state, str)
                        or not subject_lifecycle_state.strip()
                    ):
                        continue
                    if (subject_family, subject_id) not in lifecycle_transitions_by_subject:
                        raise ValueError(
                            f"missing lifecycle transition history for {subject_family} "
                            f"record {subject_id!r}"
                        )

        for (subject_family, subject_id), subject_transitions in (
            lifecycle_transitions_by_subject.items()
        ):
            ordered_transitions = sorted(
                subject_transitions,
                key=lambda transition: (
                    transition.transitioned_at,
                    transition.transition_id,
                ),
            )
            first_transition = ordered_transitions[0]
            if first_transition.previous_lifecycle_state is not None:
                raise ValueError(
                    "lifecycle transition chain for "
                    f"{subject_family} record {subject_id!r} must start with a "
                    "creation anchor: "
                    f"{first_transition.transition_id!r} has previous_lifecycle_state "
                    f"{first_transition.previous_lifecycle_state!r}"
                )
            prior_transition: LifecycleTransitionRecord | None = None
            for transition in ordered_transitions:
                if (
                    prior_transition is not None
                    and transition.previous_lifecycle_state
                    != prior_transition.lifecycle_state
                ):
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} is inconsistent: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} does not match prior "
                        f"lifecycle_state {prior_transition.lifecycle_state!r}"
                    )
                if transition.previous_lifecycle_state == transition.lifecycle_state:
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} contains no-op transition: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} matches lifecycle_state "
                        f"{transition.lifecycle_state!r}"
                    )
                prior_transition = transition

            latest_transition = ordered_transitions[-1]
            subject_record = authoritative_subject_records_by_family[subject_family][
                subject_id
            ]
            subject_lifecycle_state = getattr(subject_record, "lifecycle_state", None)
            if subject_lifecycle_state != latest_transition.lifecycle_state:
                raise ValueError(
                    f"{subject_family} record {subject_id!r} lifecycle_state "
                    f"{subject_lifecycle_state!r} does not match latest lifecycle transition "
                    f"{latest_transition.transition_id!r} state "
                    f"{latest_transition.lifecycle_state!r}"
                )

    def validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        require_lifecycle_transition_history: bool = True,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        families = self._collect_restore_record_families(records_by_family)
        self._reject_duplicate_restore_identifiers(
            families,
            restored_record_counts=restored_record_counts,
        )
        self._validate_restore_record_shapes(families)
        indexes = self._build_restore_record_indexes(families)
        self._validate_restore_record_links(families, indexes)
        self._validate_restore_lifecycle_transitions(
            families,
            indexes,
            require_lifecycle_transition_history=require_lifecycle_transition_history,
        )
