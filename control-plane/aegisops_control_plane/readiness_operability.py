from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from . import action_review_projection as _action_review_projection
from .action_review_projection import _ActionReviewRecordIndex
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)
from .readiness_contracts import (
    ReadinessDiagnosticsAggregates,
    ReadinessReviewPathRecords,
)
from .runtime_boundary import _is_missing_runtime_binding

_LIVE_OPTIONAL_EXTENSION_REVIEW_STATES = frozenset(
    {
        "pending",
        "approved",
        "executing",
        "unresolved",
    }
)


class ReadinessOperabilityHelper:
    def __init__(
        self,
        *,
        service: Any,
        config: Any,
        store: Any,
        action_review_inspection_boundary: Any,
    ) -> None:
        self._service = service
        self._config = config
        self._store = store
        self._action_review_inspection_boundary = action_review_inspection_boundary

    def __getattr__(self, name: str) -> Any:
        return getattr(self._service, name)

    @staticmethod
    def _mapping_or_empty(value: object) -> Mapping[str, object]:
        return value if isinstance(value, Mapping) else {}

    @staticmethod
    def _action_request_is_review_bound(action_request: ActionRequestRecord) -> bool:
        policy_evaluation = ReadinessOperabilityHelper._mapping_or_empty(
            action_request.policy_evaluation
        )
        return not (
            policy_evaluation.get("approval_requirement") == "policy_authorized"
            and action_request.approval_decision_id is None
        )

    def _build_readiness_review_path_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        review_path_health = [
            snapshot["path_health"] for snapshot in readiness_review_snapshots
        ]

        if not review_path_health:
            return {
                "review_count": 0,
                "overall_state": "healthy",
                "summary": "no active reviewed execution visibility gaps",
                "paths": {
                    path_name: {
                        "state": "healthy",
                        "reason": "no_reviewed_paths_tracked",
                        "affected_reviews": 0,
                        "by_state": {
                            "healthy": 0,
                            "delayed": 0,
                            "degraded": 0,
                            "failed": 0,
                        },
                    }
                    for path_name in ("ingest", "delegation", "provider", "persistence")
                },
            }

        paths = {
            path_name: self._aggregate_readiness_path_health(
                path_name=path_name,
                review_path_health=review_path_health,
            )
            for path_name in ("ingest", "delegation", "provider", "persistence")
        }
        overall_state = self._action_review_inspection_boundary.overall_path_state(
            paths.values()
        )
        return {
            "review_count": len(review_path_health),
            "overall_state": overall_state,
            "summary": self._action_review_inspection_boundary.path_health_summary(
                overall_state=overall_state,
                paths=paths,
            ),
            "paths": paths,
        }

    def _collect_readiness_review_snapshots(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
    ) -> list[dict[str, object]]:
        execution_ids = set(readiness_aggregates.active_action_execution_ids)
        execution_ids.update(readiness_aggregates.terminal_action_execution_ids)
        candidate_action_request_ids: set[str] = set()
        unresolved_delegation_ids: set[str] = set()

        for action_request_id in readiness_aggregates.active_action_request_ids:
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if action_request is None:
                continue
            if action_request.lifecycle_state in {
                "approved",
                "executing",
                "unresolved",
            }:
                candidate_action_request_ids.add(action_request_id)

        for action_request_id in (
            readiness_aggregates.terminal_review_outcome_action_request_ids
        ):
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if (
                action_request is not None
                and action_request.approval_decision_id is not None
                and self._action_request_is_review_bound(action_request)
            ):
                candidate_action_request_ids.add(action_request_id)

        for reconciliation_id in readiness_aggregates.unresolved_reconciliation_ids:
            reconciliation = self._store.get(ReconciliationRecord, reconciliation_id)
            if reconciliation is None:
                continue
            candidate_action_request_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "action_request_ids",
                )
            )
            for approval_decision_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            ):
                approval_decision = self._store.get(
                    ApprovalDecisionRecord,
                    approval_decision_id,
                )
                if approval_decision is not None:
                    candidate_action_request_ids.add(approval_decision.action_request_id)
            execution_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "action_execution_ids",
                )
            )
            unresolved_delegation_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "delegation_ids",
                )
            )

        candidate_action_request_ids.update(
            self._readiness_candidate_action_request_ids_for_delegations(
                unresolved_delegation_ids
            )
        )

        executions_by_action_request_id: dict[str, ActionExecutionRecord] = {}
        for action_execution_id in execution_ids:
            action_execution = self._store.get(ActionExecutionRecord, action_execution_id)
            if action_execution is None:
                continue
            candidate_action_request_ids.add(action_execution.action_request_id)
            existing_execution = executions_by_action_request_id.get(
                action_execution.action_request_id
            )
            if existing_execution is None or (
                action_execution.delegated_at,
                action_execution.action_execution_id,
            ) > (
                existing_execution.delegated_at,
                existing_execution.action_execution_id,
            ):
                executions_by_action_request_id[action_execution.action_request_id] = (
                    action_execution
                )

        candidate_action_requests: dict[str, ActionRequestRecord] = {}
        approval_decisions_by_action_request_id: dict[str, ApprovalDecisionRecord] = {}
        for action_request_id in sorted(candidate_action_request_ids):
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if action_request is None or not self._action_request_is_review_bound(
                action_request
            ):
                continue
            candidate_action_requests[action_request_id] = action_request
            if action_request.approval_decision_id is None:
                continue
            approval_decision = self._store.get(
                ApprovalDecisionRecord,
                action_request.approval_decision_id,
            )
            if approval_decision is not None:
                approval_decisions_by_action_request_id[action_request_id] = (
                    approval_decision
                )

        targeted_record_index = self._build_readiness_review_record_index(
            action_requests=tuple(candidate_action_requests.values()),
            approval_decisions=tuple(approval_decisions_by_action_request_id.values()),
        )
        reconciliations_by_action_request_id: dict[str, ReconciliationRecord] = {}
        if targeted_record_index is not None:
            executions_by_action_request_id = {}
            for action_request_id, execution_records in (
                targeted_record_index.executions_by_action_request_id.items()
            ):
                executions_by_action_request_id[action_request_id] = max(
                    execution_records,
                    key=lambda record: (
                        record.delegated_at,
                        record.action_execution_id,
                    ),
                )
            for action_request_id, action_request in candidate_action_requests.items():
                approval_decision = approval_decisions_by_action_request_id.get(
                    action_request_id
                )
                action_execution = executions_by_action_request_id.get(action_request_id)
                reconciliation = (
                    self._action_review_inspection_boundary.latest_reconciliation(
                        action_request=action_request,
                        approval_decision=approval_decision,
                        action_execution=action_execution,
                        record_index=targeted_record_index,
                    )
                )
                if reconciliation is not None:
                    reconciliations_by_action_request_id[action_request_id] = reconciliation

        if targeted_record_index is None and candidate_action_requests:
            current_execution_request_ids_by_execution_id: dict[str, str] = {}
            current_execution_request_ids_by_delegation_id: dict[str, str] = {}
            approval_action_request_ids_by_id = {
                approval_decision.approval_decision_id: action_request_id
                for action_request_id, approval_decision in (
                    approval_decisions_by_action_request_id.items()
                )
            }
            for action_execution in self._store.list(ActionExecutionRecord):
                if action_execution.action_request_id not in candidate_action_requests:
                    continue
                existing_execution = executions_by_action_request_id.get(
                    action_execution.action_request_id
                )
                if existing_execution is None or (
                    action_execution.delegated_at,
                    action_execution.action_execution_id,
                ) > (
                    existing_execution.delegated_at,
                    existing_execution.action_execution_id,
                ):
                    executions_by_action_request_id[action_execution.action_request_id] = (
                        action_execution
                    )

            for action_request_id, action_execution in executions_by_action_request_id.items():
                current_execution_request_ids_by_execution_id[
                    action_execution.action_execution_id
                ] = action_request_id
                current_execution_request_ids_by_delegation_id[
                    action_execution.delegation_id
                ] = action_request_id

            for reconciliation in self._store.list(ReconciliationRecord):
                matched_action_request_ids = {
                    action_request_id
                    for action_request_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "action_request_ids",
                    )
                    if action_request_id in candidate_action_requests
                }
                matched_action_request_ids.update(
                    approval_action_request_ids_by_id[approval_decision_id]
                    for approval_decision_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "approval_decision_ids",
                    )
                    if approval_decision_id in approval_action_request_ids_by_id
                )
                matched_action_request_ids.update(
                    current_execution_request_ids_by_execution_id[action_execution_id]
                    for action_execution_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "action_execution_ids",
                    )
                    if action_execution_id in current_execution_request_ids_by_execution_id
                )
                matched_action_request_ids.update(
                    current_execution_request_ids_by_delegation_id[delegation_id]
                    for delegation_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "delegation_ids",
                    )
                    if delegation_id in current_execution_request_ids_by_delegation_id
                )
                for action_request_id in matched_action_request_ids:
                    existing_reconciliation = reconciliations_by_action_request_id.get(
                        action_request_id
                    )
                    if existing_reconciliation is None or (
                        reconciliation.compared_at,
                        reconciliation.reconciliation_id,
                    ) > (
                        existing_reconciliation.compared_at,
                        existing_reconciliation.reconciliation_id,
                    ):
                        reconciliations_by_action_request_id[action_request_id] = (
                            reconciliation
                        )

        readiness_review_snapshots: list[dict[str, object]] = []
        path_health_as_of = datetime.now(timezone.utc)
        for action_request_id, action_request in sorted(candidate_action_requests.items()):
            policy_evaluation = self._mapping_or_empty(
                action_request.policy_evaluation
            )
            requested_payload = self._mapping_or_empty(
                action_request.requested_payload
            )
            approval_decision = approval_decisions_by_action_request_id.get(action_request_id)
            action_execution = executions_by_action_request_id.get(action_request_id)
            reconciliation = reconciliations_by_action_request_id.get(action_request_id)
            approval_state = _action_review_projection._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = _action_review_projection._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=action_execution,
            )
            reviewed_context = (
                self._action_review_inspection_boundary.visibility_context(
                    action_request
                )
            )
            path_health = self._action_review_inspection_boundary.path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                action_execution=action_execution,
                reconciliation=reconciliation,
                review_state=review_state,
                as_of=path_health_as_of,
            )
            readiness_review_snapshots.append(
                {
                    "action_request_id": action_request_id,
                    "review_state": review_state,
                    "source_family": (
                        self._reviewed_operator_source_family(reviewed_context)
                        if reviewed_context is not None
                        else None
                    ),
                    "ingest_expected": (
                        action_execution is not None or reconciliation is not None
                    ),
                    "execution_surface_type": (
                        action_execution.execution_surface_type
                        if action_execution is not None
                        else policy_evaluation.get("execution_surface_type")
                    ),
                    "execution_surface_id": (
                        action_execution.execution_surface_id
                        if action_execution is not None
                        else policy_evaluation.get("execution_surface_id")
                    ),
                    "requested_action_type": requested_payload.get("action_type"),
                    "path_health": path_health,
                }
            )
        return readiness_review_snapshots

    def _build_readiness_source_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        source_reviews: defaultdict[str, list[Mapping[str, object]]] = defaultdict(list)
        for snapshot in readiness_review_snapshots:
            if not snapshot.get("ingest_expected", False):
                continue
            source_family = snapshot.get("source_family")
            normalized_source_family = (
                str(source_family).strip()
                if isinstance(source_family, str) and source_family.strip()
                else "unknown_reviewed_source"
            )
            source_reviews[normalized_source_family].append(snapshot["path_health"])

        if not source_reviews:
            return {
                "tracked_sources": 0,
                "overall_state": "healthy",
                "summary": "no reviewed source health tracked",
                "sources": {},
            }

        sources: dict[str, dict[str, object]] = {}
        for source_family, review_path_health in sorted(source_reviews.items()):
            ingest_path = self._aggregate_readiness_path_health(
                path_name="ingest",
                review_path_health=review_path_health,
            )
            sources[source_family] = {
                "state": ingest_path["state"],
                "reason": ingest_path["reason"],
                "tracked_reviews": len(review_path_health),
                "affected_reviews": ingest_path["affected_reviews"],
                "by_state": ingest_path["by_state"],
            }

        overall_state = self._action_review_inspection_boundary.overall_path_state(
            sources.values()
        )
        return {
            "tracked_sources": len(sources),
            "overall_state": overall_state,
            "summary": self._readiness_surface_health_summary(
                overall_state=overall_state,
                entries=sources,
                kind="source",
            ),
            "sources": sources,
        }

    def _build_readiness_automation_substrate_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        surface_reviews: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
        surface_metadata: dict[str, tuple[str, str]] = {}
        for snapshot in readiness_review_snapshots:
            execution_surface_type = snapshot.get("execution_surface_type")
            if execution_surface_type != "automation_substrate":
                continue
            execution_surface_id = snapshot.get("execution_surface_id")
            normalized_surface_id = (
                str(execution_surface_id).strip()
                if isinstance(execution_surface_id, str) and execution_surface_id.strip()
                else "unknown"
            )
            surface_key = f"automation_substrate:{normalized_surface_id}"
            surface_reviews[surface_key].append(snapshot)
            surface_metadata[surface_key] = ("automation_substrate", normalized_surface_id)

        if not surface_reviews:
            return {
                "tracked_surfaces": 0,
                "overall_state": "healthy",
                "summary": "no reviewed automation substrate health tracked",
                "surfaces": {},
            }

        surfaces: dict[str, dict[str, object]] = {}
        for surface_key, surface_review_snapshots in sorted(surface_reviews.items()):
            review_path_health = [
                snapshot["path_health"] for snapshot in surface_review_snapshots
            ]
            aggregated_paths = {
                path_name: self._aggregate_readiness_path_health(
                    path_name=path_name,
                    review_path_health=review_path_health,
                )
                for path_name in ("delegation", "provider", "persistence")
            }
            overall_state = self._action_review_inspection_boundary.overall_path_state(
                aggregated_paths.values()
            )
            execution_surface_type, execution_surface_id = surface_metadata[surface_key]
            surfaces[surface_key] = {
                "execution_surface_type": execution_surface_type,
                "execution_surface_id": execution_surface_id,
                "state": overall_state,
                "reason": self._readiness_dominant_reason(
                    aggregated_paths.values(),
                    overall_state=overall_state,
                ),
                "tracked_reviews": len(surface_review_snapshots),
                "affected_reviews": self._count_readiness_affected_reviews(
                    surface_review_snapshots,
                    path_names=("delegation", "provider", "persistence"),
                ),
                "paths": aggregated_paths,
            }

        overall_state = self._action_review_inspection_boundary.overall_path_state(
            surfaces.values()
        )
        return {
            "tracked_surfaces": len(surfaces),
            "overall_state": overall_state,
            "summary": self._readiness_surface_health_summary(
                overall_state=overall_state,
                entries=surfaces,
                kind="automation substrate",
            ),
            "surfaces": surfaces,
        }

    def _build_optional_extension_operability(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )

        extensions = {
            "assistant": self._build_assistant_provider_operability(),
            "endpoint_evidence": self._build_endpoint_evidence_operability(
                readiness_review_snapshots
            ),
            "network_evidence": {
                "enablement": "disabled_by_default",
                "availability": "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "augmenting_evidence",
                "mainline_dependency": "non_blocking",
                "reason": "reviewed_network_evidence_extension_not_activated",
            },
            "ml_shadow": {
                "enablement": "disabled_by_default",
                "availability": "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "shadow_only",
                "mainline_dependency": "non_blocking",
                "reason": "reviewed_ml_shadow_extension_not_activated",
            },
        }
        overall_state = "ready"
        if any(entry["readiness"] == "degraded" for entry in extensions.values()):
            overall_state = "degraded"
        elif any(entry["readiness"] == "delayed" for entry in extensions.values()):
            overall_state = "delayed"
        return {
            "tracked_extensions": len(extensions),
            "overall_state": overall_state,
            "summary": self._optional_extension_operability_summary(
                extensions=extensions,
                overall_state=overall_state,
            ),
            "extensions": extensions,
        }

    def _build_assistant_provider_operability(self) -> dict[str, object]:
        latest_trace_reader = getattr(self._store, "latest_ai_trace_record", None)
        latest_trace = (
            latest_trace_reader() if callable(latest_trace_reader) else None
        )
        base = {
            "enablement": "enabled",
            "availability": "available",
            "readiness": "ready",
            "authority_mode": "advisory_only",
            "mainline_dependency": "non_blocking",
            "reason": "bounded_reviewed_summary_provider_available",
        }
        if latest_trace is None:
            return base

        subject_linkage_raw = latest_trace.subject_linkage
        subject_linkage = self._mapping_or_empty(subject_linkage_raw)
        quality = subject_linkage.get("provider_operational_quality")
        advisory_draft = latest_trace.assistant_advisory_draft
        unresolved_reasons = ()
        if isinstance(advisory_draft, Mapping):
            unresolved_reasons = tuple(
                str(reason)
                for reason in advisory_draft.get("unresolved_reasons", ())
                if isinstance(reason, str) and reason.strip()
            )
        if not isinstance(quality, Mapping):
            if unresolved_reasons:
                return self._assistant_unresolved_operability(
                    base=base,
                    latest_trace=latest_trace,
                    unresolved_reasons=unresolved_reasons,
                )
            if not isinstance(subject_linkage_raw, Mapping):
                return {
                    **base,
                    "readiness": "degraded",
                    "reason": "assistant_provider_degraded",
                    "latest_ai_trace_id": latest_trace.ai_trace_id,
                }
            return base

        availability = str(quality.get("availability") or "available")
        posture = str(quality.get("posture") or "ready")
        retry_policy = str(quality.get("retry_policy") or "not_recorded")
        if availability == "available" and posture == "ready":
            if unresolved_reasons:
                return self._assistant_unresolved_operability(
                    base={
                        **base,
                        "provider_status": str(
                            subject_linkage.get("provider_status") or "ready"
                        ),
                        "retry_policy": retry_policy,
                    },
                    latest_trace=latest_trace,
                    unresolved_reasons=unresolved_reasons,
                )
            return {
                **base,
                "provider_status": str(subject_linkage.get("provider_status") or "ready"),
                "retry_policy": retry_policy,
            }

        reason_by_posture = {
            "timeout": "assistant_provider_timeout",
            "degraded": "assistant_provider_degraded",
            "unavailable": "assistant_provider_unavailable",
        }
        return {
            **base,
            "availability": availability,
            "readiness": "degraded",
            "reason": reason_by_posture.get(posture, "assistant_provider_degraded"),
            "provider_status": str(subject_linkage.get("provider_status") or posture),
            "retry_policy": retry_policy,
            "failure_summary": subject_linkage.get("provider_failure_summary"),
            "latest_ai_trace_id": latest_trace.ai_trace_id,
        }

    @staticmethod
    def _assistant_unresolved_operability(
        *,
        base: Mapping[str, object],
        latest_trace: AITraceRecord,
        unresolved_reasons: tuple[str, ...],
    ) -> dict[str, object]:
        reason = (
            "assistant_citation_failure"
            if any(
                "citation" in unresolved_reason.casefold()
                for unresolved_reason in unresolved_reasons
            )
            else "assistant_advisory_unresolved"
        )
        return {
            **base,
            "availability": str(base.get("availability") or "available"),
            "readiness": "degraded",
            "reason": reason,
            "unresolved_reasons": unresolved_reasons,
            "latest_ai_trace_id": latest_trace.ai_trace_id,
        }

    def _build_endpoint_evidence_operability(
        self,
        readiness_review_snapshots: Iterable[Mapping[str, object]],
    ) -> dict[str, object]:
        endpoint_review_snapshots = [
            snapshot
            for snapshot in readiness_review_snapshots
            if (
                snapshot.get("requested_action_type") == "collect_endpoint_evidence_pack"
                and snapshot.get("review_state") in _LIVE_OPTIONAL_EXTENSION_REVIEW_STATES
            )
        ]
        executor_available = not _is_missing_runtime_binding(
            self._config.isolated_executor_base_url
        )
        if not endpoint_review_snapshots:
            return {
                "enablement": "disabled_by_default",
                "availability": "available" if executor_available else "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "augmenting_evidence",
                "mainline_dependency": "non_blocking",
                "reason": (
                    "no_reviewed_endpoint_evidence_requests"
                    if executor_available
                    else "isolated_executor_runtime_not_configured"
                ),
            }

        review_path_health = [
            snapshot["path_health"] for snapshot in endpoint_review_snapshots
        ]
        aggregated_paths = {
            path_name: self._aggregate_readiness_path_health(
                path_name=path_name,
                review_path_health=review_path_health,
            )
            for path_name in ("delegation", "provider", "persistence")
        }
        overall_state = self._action_review_inspection_boundary.overall_path_state(
            aggregated_paths.values()
        )
        if overall_state == "healthy":
            readiness = "ready"
            reason = "reviewed_endpoint_evidence_path_healthy"
        elif overall_state == "delayed":
            readiness = "delayed"
            reason = "reviewed_endpoint_evidence_path_delayed"
        else:
            readiness = "degraded"
            reason = self._readiness_dominant_reason(
                aggregated_paths.values(),
                overall_state=overall_state,
            )
        if not executor_available:
            readiness = "degraded"
            reason = "isolated_executor_runtime_not_configured"
        return {
            "enablement": "enabled",
            "availability": "available" if executor_available else "unavailable",
            "readiness": readiness,
            "authority_mode": "augmenting_evidence",
            "mainline_dependency": "non_blocking",
            "reason": reason,
        }

    @staticmethod
    def _optional_extension_operability_summary(
        *,
        extensions: Mapping[str, Mapping[str, object]],
        overall_state: str,
    ) -> str:
        degraded_extensions = [
            f"{extension_name} {extension['reason'].replace('_', ' ')}"
            for extension_name, extension in extensions.items()
            if extension.get("readiness") == "degraded"
        ]
        if degraded_extensions:
            return (
                f"{overall_state} optional extension operability: "
                + "; ".join(degraded_extensions[:2])
            )
        delayed_extensions = [
            f"{extension_name} {extension['reason'].replace('_', ' ')}"
            for extension_name, extension in extensions.items()
            if extension.get("readiness") == "delayed"
        ]
        if delayed_extensions:
            return (
                f"{overall_state} optional extension operability: "
                + "; ".join(delayed_extensions[:2])
            )
        disabled_extensions = [
            extension_name
            for extension_name, extension in extensions.items()
            if extension.get("enablement") == "disabled_by_default"
        ]
        if disabled_extensions:
            return (
                "ready optional extension operability: "
                + ", ".join(disabled_extensions[:3])
                + " remain disabled by default or unavailable"
            )
        return "all reviewed optional extensions are ready"

    @staticmethod
    def _readiness_dominant_reason(
        paths: Iterable[Mapping[str, object]],
        *,
        overall_state: str,
    ) -> str:
        reason_counts: Counter[str] = Counter()
        for path in paths:
            if path.get("state") != overall_state:
                continue
            by_state = path.get("by_state")
            weight = (
                int(by_state.get(overall_state, 0))
                if isinstance(by_state, Mapping)
                else int(path.get("affected_reviews", 0))
            )
            reason_counts[str(path["reason"])] += max(weight, 1)
        if not reason_counts:
            return f"{overall_state}_reason_unknown"
        return sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]

    def _readiness_surface_health_summary(
        self,
        *,
        overall_state: str,
        entries: Mapping[str, Mapping[str, object]],
        kind: str,
    ) -> str:
        active_entries = [
            f"{entry_name} {entry['reason'].replace('_', ' ')}"
            for entry_name, entry in entries.items()
            if entry.get("state") != "healthy"
        ]
        if not active_entries:
            return f"all reviewed {kind} health surfaces are healthy"
        return f"{overall_state} {kind} health: {'; '.join(active_entries[:2])}"

    def _readiness_candidate_action_request_ids_for_delegations(
        self,
        delegation_ids: set[str],
    ) -> set[str]:
        if not delegation_ids:
            return set()

        record_reader = getattr(self._store, "inspect_readiness_review_path_records", None)
        if callable(record_reader):
            readiness_records: ReadinessReviewPathRecords = record_reader(
                action_request_ids=(),
                approval_decision_ids=(),
                delegation_ids=tuple(sorted(delegation_ids)),
            )
            return {
                action_execution.action_request_id
                for action_execution in readiness_records.action_executions
            }

        pending_delegation_ids = set(delegation_ids)
        candidate_action_request_ids: set[str] = set()
        for action_execution in self._store.list(ActionExecutionRecord):
            if action_execution.delegation_id not in pending_delegation_ids:
                continue
            candidate_action_request_ids.add(action_execution.action_request_id)
            pending_delegation_ids.discard(action_execution.delegation_id)
            if not pending_delegation_ids:
                break
        return candidate_action_request_ids

    def _build_readiness_review_record_index(
        self,
        *,
        action_requests: tuple[ActionRequestRecord, ...],
        approval_decisions: tuple[ApprovalDecisionRecord, ...],
    ) -> _ActionReviewRecordIndex | None:
        if not action_requests:
            return None
        record_reader = getattr(self._store, "inspect_readiness_review_path_records", None)
        if not callable(record_reader):
            return None
        readiness_records: ReadinessReviewPathRecords = record_reader(
            action_request_ids=tuple(
                sorted(
                    {
                        action_request.action_request_id
                        for action_request in action_requests
                    }
                )
            ),
            approval_decision_ids=tuple(
                sorted(
                    {
                        approval_decision.approval_decision_id
                        for approval_decision in approval_decisions
                    }
                )
            ),
        )
        executions_by_action_request_id: defaultdict[
            str,
            list[ActionExecutionRecord],
        ] = defaultdict(list)
        for action_execution in readiness_records.action_executions:
            executions_by_action_request_id[action_execution.action_request_id].append(
                action_execution
            )

        reconciliations_by_action_request_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_approval_decision_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_action_execution_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_delegation_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        for reconciliation in readiness_records.reconciliations:
            for action_request_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            ):
                reconciliations_by_action_request_id[action_request_id].append(
                    reconciliation
                )
            for approval_decision_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            ):
                reconciliations_by_approval_decision_id[approval_decision_id].append(
                    reconciliation
                )
            for action_execution_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            ):
                reconciliations_by_action_execution_id[action_execution_id].append(
                    reconciliation
                )
            for delegation_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            ):
                reconciliations_by_delegation_id[delegation_id].append(reconciliation)

        return _ActionReviewRecordIndex(
            requests_by_case_id={},
            requests_by_alert_id={},
            requests_by_scope={},
            approvals_by_id={
                approval_decision.approval_decision_id: approval_decision
                for approval_decision in approval_decisions
            },
            approvals_by_action_request_id={},
            executions_by_action_request_id={
                key: tuple(records)
                for key, records in executions_by_action_request_id.items()
            },
            reconciliations_by_action_request_id={
                key: tuple(records)
                for key, records in reconciliations_by_action_request_id.items()
            },
            reconciliations_by_approval_decision_id={
                key: tuple(records)
                for key, records in reconciliations_by_approval_decision_id.items()
            },
            reconciliations_by_action_execution_id={
                key: tuple(records)
                for key, records in reconciliations_by_action_execution_id.items()
            },
            reconciliations_by_delegation_id={
                key: tuple(records)
                for key, records in reconciliations_by_delegation_id.items()
            },
        )

    def _aggregate_readiness_path_health(
        self,
        *,
        path_name: str,
        review_path_health: Iterable[Mapping[str, object]],
    ) -> dict[str, object]:
        path_snapshots = [
            path_health["paths"][path_name]
            for path_health in review_path_health
        ]
        state_counts = Counter(
            str(path_snapshot["state"]) for path_snapshot in path_snapshots
        )
        overall_state = self._action_review_inspection_boundary.overall_path_state(
            path_snapshots
        )
        reason_counts = Counter(
            str(path_snapshot["reason"])
            for path_snapshot in path_snapshots
            if path_snapshot["state"] == overall_state
        )
        if reason_counts:
            reason = sorted(
                reason_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[0][0]
        else:
            reason = f"{overall_state}_reason_unknown"
        return {
            "state": overall_state,
            "reason": reason,
            "affected_reviews": sum(
                count for state, count in state_counts.items() if state != "healthy"
            ),
            "by_state": {
                "healthy": state_counts.get("healthy", 0),
                "delayed": state_counts.get("delayed", 0),
                "degraded": state_counts.get("degraded", 0),
                "failed": state_counts.get("failed", 0),
            },
        }

    @staticmethod
    def _count_readiness_affected_reviews(
        readiness_review_snapshots: Iterable[Mapping[str, object]],
        *,
        path_names: Iterable[str],
    ) -> int:
        relevant_path_names = tuple(path_names)
        return len(
            {
                str(snapshot["action_request_id"])
                for snapshot in readiness_review_snapshots
                if any(
                    snapshot["path_health"]["paths"][path_name]["state"] != "healthy"
                    for path_name in relevant_path_names
                )
            }
        )



__all__ = ["ReadinessOperabilityHelper"]
