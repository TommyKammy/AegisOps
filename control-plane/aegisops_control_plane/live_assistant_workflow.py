from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from typing import Any, Callable, Protocol

from .assistant_provider import (
    AssistantProviderAdapter,
    AssistantProviderFailure,
    AssistantProviderResult,
)
from .models import AITraceRecord, RecommendationRecord


class LiveAssistantWorkflowServiceDependencies(Protocol):
    _assistant_provider_adapter: object
    _store: object

    def inspect_assistant_context(self, record_family: str, record_id: str) -> object:
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

    def _require_reviewed_alert_scoped_queue_summary_read(
        self,
        context_snapshot: object,
    ) -> None:
        ...

    def _require_reviewed_case_scoped_advisory_read(
        self,
        context_snapshot: object,
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

    def _assistant_merge_ids(
        self,
        existing_values: tuple[str, ...],
        *incoming_values: str | None,
    ) -> tuple[str, ...]:
        ...

    def _assistant_ids_from_mapping(
        self,
        mapping: object,
        key: str,
    ) -> tuple[str, ...]:
        ...

    def _assistant_primary_linked_id(
        self,
        linked_ids: tuple[str, ...],
    ) -> str | None:
        ...


class LiveAssistantWorkflowCoordinator:
    """Owns live assistant workflow orchestration behind the service API."""

    def __init__(
        self,
        service: LiveAssistantWorkflowServiceDependencies,
        *,
        workflow_family: str,
        workflow_prompt_versions: dict[str, str],
        json_ready: Callable[[object], object],
        dedupe_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        advisory_scope_expansion_flags: Callable[[object], tuple[str, ...]],
        snapshot_factory: Callable[..., object],
        citations_from_context: Callable[[object], tuple[dict[str, object], ...]],
        unresolved_reasons_from_flags: Callable[[tuple[str, ...]], tuple[str, ...]],
        prompt_injection_flags: Callable[[object], tuple[str, ...]],
    ) -> None:
        self._service = service
        self._workflow_family = workflow_family
        self._workflow_prompt_versions = workflow_prompt_versions
        self._json_ready = json_ready
        self._dedupe_strings = dedupe_strings
        self._advisory_scope_expansion_flags = advisory_scope_expansion_flags
        self._snapshot_factory = snapshot_factory
        self._citations_from_context = citations_from_context
        self._unresolved_reasons_from_flags = unresolved_reasons_from_flags
        self._prompt_injection_flags = prompt_injection_flags

    def run_live_assistant_workflow(
        self,
        *,
        workflow_task: str,
        record_family: str,
        record_id: str,
    ) -> object:
        workflow_task = self._service._require_non_empty_string(
            workflow_task, "workflow_task"
        )
        record_family = self._service._require_non_empty_string(
            record_family, "record_family"
        )
        record_id = self._service._require_non_empty_string(record_id, "record_id")

        expected_record_family = {
            "case_summary": "case",
            "queue_triage_summary": "alert",
        }.get(workflow_task)
        if expected_record_family is None:
            raise ValueError(
                "workflow_task must be one of: case_summary, queue_triage_summary"
            )
        if record_family != expected_record_family:
            raise ValueError(
                f"workflow_task {workflow_task!r} requires record_family {expected_record_family!r}"
            )

        context_snapshot = self._service.inspect_assistant_context(record_family, record_id)
        if workflow_task == "queue_triage_summary":
            self._service._require_reviewed_alert_scoped_queue_summary_read(
                context_snapshot
            )
        else:
            self._service._require_reviewed_case_scoped_advisory_read(context_snapshot)

        advisory_output = dict(getattr(context_snapshot, "advisory_output"))
        reviewed_input_refs = self._dedupe_strings(
            (
                record_id,
                *getattr(context_snapshot, "linked_alert_ids"),
                *getattr(context_snapshot, "linked_case_ids"),
                *getattr(context_snapshot, "linked_evidence_ids"),
                *getattr(context_snapshot, "linked_recommendation_ids"),
                *getattr(context_snapshot, "linked_reconciliation_ids"),
            )
        )
        citations = self._citations_from_context(context_snapshot)
        trusted_summary = str(
            advisory_output.get("cited_summary", {}).get("text")
            or f"Reviewed {workflow_task.replace('_', ' ')} for {record_id} remains unresolved."
        )
        adapter = self._live_assistant_adapter_for_workflow_task(workflow_task)
        if advisory_output.get("status") != "ready":
            unresolved_reasons = self._unresolved_reasons_from_flags(
                advisory_output.get("uncertainty_flags", ())
            )
            if not unresolved_reasons:
                unresolved_reasons = ("required citations are missing",)
            snapshot = self._snapshot_factory(
                workflow_task=workflow_task,
                summary=trusted_summary,
                citations=citations,
                unresolved_reasons=unresolved_reasons,
            )
            self._persist_live_assistant_feedback_loop(
                record_family=record_family,
                record_id=record_id,
                context_snapshot=context_snapshot,
                workflow_snapshot=snapshot,
                provider_result=None,
                reviewed_input_refs=reviewed_input_refs,
                adapter=adapter,
            )
            return snapshot

        if adapter is None:
            raise ValueError("live assistant provider is not configured")

        transcript_payload = self._json_ready(
            {
                "record_family": record_family,
                "record_id": record_id,
                "reviewed_context": getattr(context_snapshot, "reviewed_context"),
                "linked_alert_ids": getattr(context_snapshot, "linked_alert_ids"),
                "linked_case_ids": getattr(context_snapshot, "linked_case_ids"),
                "linked_evidence_ids": getattr(context_snapshot, "linked_evidence_ids"),
                "linked_recommendation_ids": getattr(
                    context_snapshot, "linked_recommendation_ids"
                ),
                "linked_reconciliation_ids": getattr(
                    context_snapshot, "linked_reconciliation_ids"
                ),
                "advisory_output": advisory_output,
            }
        )
        provider_result = None
        unresolved_reasons: list[str] = []
        try:
            provider_result = adapter.generate(
                workflow_family=self._workflow_family,
                workflow_task=workflow_task,
                transcript=[
                    {
                        "role": "system",
                        "content": (
                            "Return a concise reviewed-only summary. Do not add approval, delegation, execution, or policy language."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(transcript_payload, sort_keys=True),
                    },
                ],
                reviewed_input_refs=reviewed_input_refs,
                metadata={
                    "record_family": record_family,
                    "record_id": record_id,
                    "bounded_summary_text": trusted_summary,
                },
            )
        except Exception:  # noqa: BLE001
            unresolved_reasons.extend(
                self._unresolved_reasons_from_flags(("provider_generation_failed",))
            )
        candidate_summary = trusted_summary
        provider_output_text: str | None = None
        if provider_result is not None:
            if provider_result.status != "ready":
                unresolved_reasons.extend(
                    self._unresolved_reasons_from_flags(("provider_generation_failed",))
                )
            elif (
                isinstance(provider_result.output_text, str)
                and provider_result.output_text.strip()
            ):
                provider_output_text = provider_result.output_text.strip()
                candidate_summary = provider_output_text
            else:
                unresolved_reasons.extend(
                    self._unresolved_reasons_from_flags(("provider_generation_failed",))
                )
        if provider_output_text is not None:
            unresolved_reasons.extend(
                self._unresolved_reasons_from_flags(
                    self._prompt_injection_flags(provider_output_text)
                )
            )
        unresolved_reasons.extend(
            self._unresolved_reasons_from_flags(
                self._advisory_scope_expansion_flags(candidate_summary)
            )
        )
        if not citations:
            unresolved_reasons.extend(
                self._unresolved_reasons_from_flags(("missing_supporting_citations",))
            )
        unresolved_reasons = self._dedupe_strings(tuple(unresolved_reasons))
        summary = trusted_summary if unresolved_reasons else candidate_summary
        snapshot = self._snapshot_factory(
            workflow_task=workflow_task,
            summary=summary,
            citations=citations,
            unresolved_reasons=unresolved_reasons,
        )
        self._persist_live_assistant_feedback_loop(
            record_family=record_family,
            record_id=record_id,
            context_snapshot=context_snapshot,
            workflow_snapshot=snapshot,
            provider_result=provider_result,
            reviewed_input_refs=reviewed_input_refs,
            adapter=adapter,
        )
        return snapshot

    def _live_assistant_adapter_for_workflow_task(
        self,
        workflow_task: str,
    ) -> object | None:
        adapter = self._service._assistant_provider_adapter
        if adapter is None:
            return None
        adapter_prompt_version = self._workflow_prompt_versions[workflow_task]
        if (
            isinstance(adapter, AssistantProviderAdapter)
            and getattr(adapter, "_prompt_version", None) != adapter_prompt_version
        ):
            return AssistantProviderAdapter(
                provider_identity=getattr(adapter, "_provider_identity", "reviewed_local"),
                model_identity=getattr(
                    adapter, "_model_identity", "bounded_reviewed_summary"
                ),
                prompt_version=adapter_prompt_version,
                request_timeout_seconds=float(
                    getattr(adapter, "_request_timeout_seconds", 5.0)
                ),
                max_attempts=int(getattr(adapter, "_max_attempts", 1)),
                transport=getattr(adapter, "_transport"),
            )
        return adapter

    def _persist_live_assistant_feedback_loop(
        self,
        *,
        record_family: str,
        record_id: str,
        context_snapshot: object,
        workflow_snapshot: object,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        reviewed_input_refs: tuple[str, ...],
        adapter: object,
    ) -> None:
        with self._service._store.transaction():
            ai_trace_record = self._build_live_assistant_ai_trace_record(
                record_family=record_family,
                record_id=record_id,
                context_snapshot=context_snapshot,
                workflow_snapshot=workflow_snapshot,
                provider_result=provider_result,
                reviewed_input_refs=reviewed_input_refs,
                adapter=adapter,
            )
            persisted_ai_trace = self._service.persist_record(ai_trace_record)
            recommendation_record = self._build_live_assistant_recommendation_record(
                context_snapshot=context_snapshot,
                workflow_snapshot=workflow_snapshot,
                ai_trace_record=persisted_ai_trace,
            )
            persisted_recommendation = self._service.persist_record(recommendation_record)

            updated_subject_linkage = dict(persisted_ai_trace.subject_linkage)
            updated_subject_linkage["recommendation_ids"] = (
                self._service._assistant_merge_ids(
                    self._service._assistant_ids_from_mapping(
                        persisted_ai_trace.subject_linkage,
                        "recommendation_ids",
                    ),
                    persisted_recommendation.recommendation_id,
                )
            )
            updated_advisory_draft = dict(persisted_ai_trace.assistant_advisory_draft)
            updated_advisory_draft["subject_linkage"] = updated_subject_linkage
            self._service.persist_record(
                replace(
                    persisted_ai_trace,
                    subject_linkage=updated_subject_linkage,
                    assistant_advisory_draft=updated_advisory_draft,
                )
            )

    def _build_live_assistant_ai_trace_record(
        self,
        *,
        record_family: str,
        record_id: str,
        context_snapshot: object,
        workflow_snapshot: Any,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        reviewed_input_refs: tuple[str, ...],
        adapter: object,
    ) -> AITraceRecord:
        subject_linkage = {
            "source_record_family": record_family,
            "source_record_id": record_id,
            "alert_ids": getattr(context_snapshot, "linked_alert_ids"),
            "case_ids": getattr(context_snapshot, "linked_case_ids"),
            "evidence_ids": getattr(context_snapshot, "linked_evidence_ids"),
            "recommendation_ids": getattr(context_snapshot, "linked_recommendation_ids"),
            "reconciliation_ids": getattr(
                context_snapshot, "linked_reconciliation_ids"
            ),
            "output_contract": {
                "workflow_family": workflow_snapshot.workflow_family,
                "workflow_task": workflow_snapshot.workflow_task,
                "status": workflow_snapshot.status,
            },
        }
        build_ai_trace_record = getattr(adapter, "build_ai_trace_record", None)
        ai_trace_record: AITraceRecord | None = None
        if provider_result is not None and callable(build_ai_trace_record):
            candidate_record = build_ai_trace_record(
                ai_trace_id=self._service._resolve_new_record_identifier(
                    AITraceRecord,
                    None,
                    "ai_trace_id",
                    "ai-trace",
                ),
                reviewer_identity="system://bounded-live-assistant",
                generated_at=provider_result.generated_at,
                result=provider_result,
                subject_linkage=subject_linkage,
            )
            if isinstance(candidate_record, AITraceRecord):
                ai_trace_record = candidate_record

        if ai_trace_record is None:
            generated_at = (
                provider_result.generated_at
                if provider_result is not None
                else datetime.now(timezone.utc)
            )
            ai_trace_record = AITraceRecord(
                ai_trace_id=self._service._resolve_new_record_identifier(
                    AITraceRecord,
                    None,
                    "ai_trace_id",
                    "ai-trace",
                ),
                subject_linkage=subject_linkage,
                model_identity=(
                    (
                        f"{provider_result.provider_identity}/"
                        f"{provider_result.model_identity}"
                    )
                    if provider_result is not None
                    else (
                        f"{getattr(adapter, '_provider_identity', 'reviewed_local')}/"
                        f"{getattr(adapter, '_model_identity', 'bounded_reviewed_summary')}"
                    )
                ),
                prompt_version=(
                    provider_result.prompt_version
                    if provider_result is not None
                    else str(
                        getattr(
                            adapter,
                            "_prompt_version",
                            self._workflow_prompt_versions[
                                workflow_snapshot.workflow_task
                            ],
                        )
                    )
                ),
                generated_at=generated_at,
                material_input_refs=reviewed_input_refs,
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
            )

        canonical_subject_linkage = dict(ai_trace_record.subject_linkage)
        canonical_subject_linkage.update(subject_linkage)

        return replace(
            ai_trace_record,
            subject_linkage=canonical_subject_linkage,
            material_input_refs=reviewed_input_refs,
            lifecycle_state="under_review",
            assistant_advisory_draft={
                **workflow_snapshot.to_dict(),
                "source_record_family": record_family,
                "source_record_id": record_id,
                "review_lifecycle_state": "under_review",
                "subject_linkage": canonical_subject_linkage,
                "reviewed_input_refs": reviewed_input_refs,
            },
        )

    def _build_live_assistant_recommendation_record(
        self,
        *,
        context_snapshot: object,
        workflow_snapshot: Any,
        ai_trace_record: AITraceRecord,
    ) -> RecommendationRecord:
        source_alert_id = (
            getattr(context_snapshot, "record_id")
            if getattr(context_snapshot, "record_family") == "alert"
            else self._service._assistant_primary_linked_id(
                getattr(context_snapshot, "linked_alert_ids")
            )
        )
        source_case_id = (
            getattr(context_snapshot, "record_id")
            if getattr(context_snapshot, "record_family") == "case"
            else self._service._assistant_primary_linked_id(
                getattr(context_snapshot, "linked_case_ids")
            )
        )
        return RecommendationRecord(
            recommendation_id=self._service._resolve_new_record_identifier(
                RecommendationRecord,
                None,
                "recommendation_id",
                "recommendation",
            ),
            lead_id=None,
            hunt_run_id=None,
            alert_id=source_alert_id,
            case_id=source_case_id,
            ai_trace_id=ai_trace_record.ai_trace_id,
            review_owner="system://bounded-live-assistant",
            intended_outcome=workflow_snapshot.summary,
            lifecycle_state="under_review",
            reviewed_context=getattr(context_snapshot, "reviewed_context"),
            assistant_advisory_draft={
                "workflow_family": workflow_snapshot.workflow_family,
                "workflow_task": workflow_snapshot.workflow_task,
                "status": workflow_snapshot.status,
                "cited_summary": {"text": workflow_snapshot.summary},
                "citations": workflow_snapshot.citations,
                "unresolved_reasons": workflow_snapshot.unresolved_reasons,
                "operator_follow_up": workflow_snapshot.operator_follow_up,
                "source_record_family": getattr(context_snapshot, "record_family"),
                "source_record_id": getattr(context_snapshot, "record_id"),
                "source_ai_trace_id": ai_trace_record.ai_trace_id,
                "review_lifecycle_state": "under_review",
                "linked_alert_ids": getattr(context_snapshot, "linked_alert_ids"),
                "linked_case_ids": getattr(context_snapshot, "linked_case_ids"),
                "linked_evidence_ids": getattr(context_snapshot, "linked_evidence_ids"),
                "linked_recommendation_ids": getattr(
                    context_snapshot, "linked_recommendation_ids"
                ),
                "linked_reconciliation_ids": getattr(
                    context_snapshot, "linked_reconciliation_ids"
                ),
            },
        )
