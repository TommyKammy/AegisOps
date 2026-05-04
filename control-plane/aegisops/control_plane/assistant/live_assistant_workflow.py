from __future__ import annotations

from copy import copy
from dataclasses import replace
from datetime import datetime, timezone
import json
import re
from typing import Any, Callable, Iterable, Protocol

from .ai_trace_lifecycle import AITraceLifecycleService
from .assistant_context import require_ai_advisory_enabled
from .assistant_provider import (
    AssistantProviderAdapter,
    AssistantProviderAttemptFailure,
    AssistantProviderFailure,
    AssistantProviderResult,
    provider_exception_failure_metadata,
)
from ..models import AITraceRecord, RecommendationRecord
from ..runtime.service_snapshots import (
    AnalystAssistantContextSnapshot,
    LiveAssistantWorkflowSnapshot,
)

_PHASE24_WORKFLOW_FAMILY = "first_live_assistant_summary_family"


def _dedupe_strings(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def phase24_live_assistant_unresolved_reasons(
    uncertainty_flags: Iterable[str],
) -> tuple[str, ...]:
    mapping = {
        "missing_supporting_citations": "required citations are missing",
        "missing_evidence_citation": "linked evidence required for the summary is missing",
        "conflicting_reviewed_context": (
            "reviewed records conflict on lifecycle state, ownership, scope, or evidence-backed facts"
        ),
        "ambiguous_identity_alias_only": (
            "the requested summary would require the assistant to collapse identity ambiguity"
        ),
        "reviewed_casework_identity_ambiguity": (
            "reviewed multi-source casework still contains unresolved identity ambiguity"
        ),
        "authority_overreach": (
            "the requested summary would widen into approval, delegation, execution, or policy interpretation"
        ),
        "scope_expansion_attempt": (
            "the requested summary would widen beyond the reviewed record chain"
        ),
        "prompt_injection_attempt": (
            "the requested summary would follow prompt-injection or instruction-override text instead of reviewed records"
        ),
        "provider_generation_failed": (
            "the bounded live assistant did not return a trusted summary within the reviewed retry budget"
        ),
    }
    reasons: list[str] = []
    for flag in uncertainty_flags:
        reason = mapping.get(str(flag))
        if reason is not None and reason not in reasons:
            reasons.append(reason)
    return tuple(reasons)


def phase24_live_assistant_prompt_injection_flags(text: object) -> tuple[str, ...]:
    if not isinstance(text, str):
        return ()

    lowered = text.lower()
    normalized = re.sub(r"[\W_]+", " ", lowered)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    flags: list[str] = []
    prompt_injection_terms = (
        r"\bignore(?:\s+all)?\s+previous\s+instructions\b",
        r"\bdisregard\s+previous\s+instructions\b",
        r"\boverride\s+previous\s+instructions\b",
        r"\breveal\s+(?:the\s+)?hidden\s+system\s+prompt\b",
        r"\breveal\s+(?:the\s+)?system\s+prompt\b",
        r"\bshow\s+(?:the\s+)?system\s+prompt\b",
        r"\breveal\s+(?:the\s+)?developer\s+message\b",
    )
    if any(re.search(term, normalized) for term in prompt_injection_terms):
        flags.append("prompt_injection_attempt")
    return _dedupe_strings(tuple(flags))


def phase24_live_assistant_citations_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> tuple[dict[str, object], ...]:
    citations: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()

    def append_citation(
        *,
        record_family: str,
        record_id: str,
        claim: str,
        evidence_id: str | None,
        reviewed_context_field: str | None,
    ) -> None:
        key = (record_family, record_id, claim, evidence_id, reviewed_context_field)
        if key in seen:
            return
        seen.add(key)
        citations.append(
            {
                "record_family": record_family,
                "record_id": record_id,
                "claim": claim,
                "evidence_id": evidence_id,
                "reviewed_context_field": reviewed_context_field,
            }
        )

    if snapshot.record_family == "case":
        append_citation(
            record_family="case",
            record_id=snapshot.record_id,
            claim="Reviewed case lifecycle and scope remain anchored on the case record.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    elif snapshot.record_family == "alert":
        append_citation(
            record_family="alert",
            record_id=snapshot.record_id,
            claim="Reviewed alert lifecycle remains anchored on the alert record.",
            evidence_id=None,
            reviewed_context_field=None,
        )

    for alert_id in snapshot.linked_alert_ids:
        append_citation(
            record_family="alert",
            record_id=alert_id,
            claim="Reviewed alert linkage preserves the bounded live assistant chain.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    for case_id in snapshot.linked_case_ids:
        append_citation(
            record_family="case",
            record_id=case_id,
            claim="Reviewed case linkage preserves the bounded live assistant chain.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    for evidence_id in snapshot.linked_evidence_ids:
        append_citation(
            record_family="evidence",
            record_id=evidence_id,
            claim="Linked reviewed evidence supports the live assistant summary.",
            evidence_id=evidence_id,
            reviewed_context_field=None,
        )

    for context_field in ("asset", "identity", "privilege", "source", "provenance"):
        if context_field in snapshot.reviewed_context:
            append_citation(
                record_family=snapshot.record_family,
                record_id=snapshot.record_id,
                claim=(
                    f"Reviewed context field {context_field} remains within the reviewed record chain."
                ),
                evidence_id=None,
                reviewed_context_field=context_field,
            )

    return tuple(citations)


def phase24_live_assistant_snapshot(
    *,
    workflow_task: str,
    summary: str,
    citations: tuple[dict[str, object], ...],
    unresolved_reasons: tuple[str, ...],
) -> LiveAssistantWorkflowSnapshot:
    status = "unresolved" if unresolved_reasons else "ready"
    return LiveAssistantWorkflowSnapshot(
        workflow_family=_PHASE24_WORKFLOW_FAMILY,
        workflow_task=workflow_task,
        status=status,
        summary=summary,
        citations=citations,
        unresolved_reasons=unresolved_reasons,
        operator_follow_up=phase24_live_assistant_follow_up(status),
    )


def phase24_live_assistant_follow_up(status: str) -> str:
    if status == "ready":
        return (
            "Review the cited records before any approval, delegation, execution, or policy decision."
        )
    return (
        "Review the unresolved reasons against the cited records before any approval, delegation, execution, or policy decision."
    )


class LiveAssistantWorkflowServiceDependencies(Protocol):
    _assistant_context_assembler: object
    _assistant_provider_adapter: object
    _store: object

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
        ai_trace_lifecycle: AITraceLifecycleService,
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
        self._ai_trace_lifecycle = ai_trace_lifecycle

    def run_live_assistant_workflow(
        self,
        *,
        workflow_task: str,
        record_family: str,
        record_id: str,
    ) -> object:
        require_ai_advisory_enabled(self._service)
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

        context_snapshot = (
            self._service._assistant_context_assembler.inspect_assistant_context(
                record_family,
                record_id,
            )
        )
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
        except Exception as exc:  # noqa: BLE001
            provider_result = self._build_provider_exception_failure(
                adapter=adapter,
                workflow_task=workflow_task,
                record_family=record_family,
                record_id=record_id,
                reviewed_input_refs=reviewed_input_refs,
                exc=exc,
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
            and adapter._prompt_version != adapter_prompt_version
        ):
            workflow_adapter = copy(adapter)
            workflow_adapter._prompt_version = adapter_prompt_version
            return workflow_adapter
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
                self._ai_trace_lifecycle.merge_ids(
                    self._ai_trace_lifecycle.ids_from_mapping(
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
        provider_operability_linkage = self._provider_operability_linkage(
            adapter=adapter,
            provider_result=provider_result,
            workflow_snapshot=workflow_snapshot,
        )
        subject_linkage.update(provider_operability_linkage)
        trace_governance = self._trace_governance_evidence(
            context_snapshot=context_snapshot,
            workflow_snapshot=workflow_snapshot,
            provider_result=provider_result,
            provider_operability_linkage=provider_operability_linkage,
            adapter=adapter,
        )
        subject_linkage["trace_governance"] = trace_governance
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
        advisory_draft = dict(ai_trace_record.assistant_advisory_draft)
        advisory_draft.update(
            {
                **workflow_snapshot.to_dict(),
                "source_record_family": record_family,
                "source_record_id": record_id,
                "review_lifecycle_state": "under_review",
                "subject_linkage": canonical_subject_linkage,
                "reviewed_input_refs": reviewed_input_refs,
                "trace_governance": trace_governance,
            }
        )

        return replace(
            ai_trace_record,
            subject_linkage=canonical_subject_linkage,
            material_input_refs=reviewed_input_refs,
            lifecycle_state="under_review",
            assistant_advisory_draft=advisory_draft,
        )

    def _trace_governance_evidence(
        self,
        *,
        context_snapshot: object,
        workflow_snapshot: Any,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        provider_operability_linkage: dict[str, object],
        adapter: object,
    ) -> dict[str, object]:
        advisory_output = dict(getattr(context_snapshot, "advisory_output"))
        unresolved_reasons = tuple(workflow_snapshot.unresolved_reasons)
        provider_response_provenance = (
            dict(provider_result.response_provenance)
            if provider_result is not None
            else {}
        )
        provider_model_version = provider_response_provenance.get("model_version")
        if (
            not isinstance(provider_model_version, str)
            or not provider_model_version.strip()
        ):
            provider_model_version = None

        citation_failure_state = self._citation_failure_state(
            unresolved_reasons=unresolved_reasons,
            advisory_output=advisory_output,
            workflow_status=workflow_snapshot.status,
        )
        return {
            "prompt_version_evidence": {
                "prompt_version": (
                    provider_result.prompt_version
                    if provider_result is not None
                    else self._adapter_identity(
                        adapter,
                        "_prompt_version",
                        self._workflow_prompt_versions[workflow_snapshot.workflow_task],
                    )
                ),
                "workflow_family": workflow_snapshot.workflow_family,
                "workflow_task": workflow_snapshot.workflow_task,
                "source": "configured_live_assistant_prompt_manifest",
            },
            "model_provider_evidence": {
                "provider_identity": provider_operability_linkage["provider_identity"],
                "model_identity": provider_operability_linkage[
                    "provider_model_identity"
                ],
                "provider_status": provider_operability_linkage["provider_status"],
                "provider_model_version": provider_model_version,
            },
            "citation_state": {
                "completeness": (
                    "complete" if citation_failure_state is None else "incomplete"
                ),
                "failure_state": citation_failure_state,
                "citation_count": len(tuple(workflow_snapshot.citations)),
                "unresolved_reasons": unresolved_reasons,
            },
            "reviewed_context_conflicts": self._reviewed_context_conflicts(
                advisory_output
            ),
            "authority_mode": "advisory_only",
        }

    @staticmethod
    def _reviewed_context_conflicts(
        advisory_output: dict[str, object],
    ) -> tuple[str, ...]:
        raw_conflicts = advisory_output.get("reviewed_context_conflicts")
        if not isinstance(raw_conflicts, (list, tuple)):
            return ()
        conflicts: list[str] = []
        for conflict in raw_conflicts:
            if not isinstance(conflict, str):
                continue
            normalized_conflict = conflict.strip()
            if normalized_conflict and normalized_conflict not in conflicts:
                conflicts.append(normalized_conflict)
        return tuple(conflicts)

    @staticmethod
    def _citation_failure_state(
        *,
        unresolved_reasons: tuple[str, ...],
        advisory_output: dict[str, object],
        workflow_status: str,
    ) -> str | None:
        raw_uncertainty_flags = advisory_output.get("uncertainty_flags", ())
        uncertainty_flags = (
            tuple(str(flag) for flag in raw_uncertainty_flags)
            if isinstance(raw_uncertainty_flags, (list, tuple, set))
            else ()
        )
        if any("citation" in reason.casefold() for reason in unresolved_reasons):
            return "missing_supporting_citations"
        if "missing_supporting_citations" in uncertainty_flags:
            return "missing_supporting_citations"
        if "missing_evidence_citation" in uncertainty_flags:
            return "missing_evidence_citation"
        if workflow_status != "ready":
            return "unresolved"
        return None

    @staticmethod
    def _adapter_identity(
        adapter: object,
        attribute_name: str,
        default: str,
    ) -> str:
        value = getattr(adapter, attribute_name, default)
        return value if isinstance(value, str) and value.strip() else default

    def _build_provider_exception_failure(
        self,
        *,
        adapter: object,
        workflow_task: str,
        record_family: str,
        record_id: str,
        reviewed_input_refs: tuple[str, ...],
        exc: Exception,
    ) -> AssistantProviderFailure:
        provider_identity = self._adapter_identity(
            adapter,
            "_provider_identity",
            "unknown_provider",
        )
        model_identity = self._adapter_identity(
            adapter,
            "_model_identity",
            "unknown_model",
        )
        prompt_version = self._adapter_identity(
            adapter,
            "_prompt_version",
            self._workflow_prompt_versions[workflow_task],
        )
        failure_metadata = provider_exception_failure_metadata(exc)
        failure_kind = failure_metadata["failure_kind"]
        failure_detail = failure_metadata["detail"]
        failure = AssistantProviderAttemptFailure(
            attempt_number=1,
            failure_kind=failure_kind,
            detail=failure_detail,
        )
        return AssistantProviderFailure(
            status=failure_metadata["status"],
            provider_identity=provider_identity,
            model_identity=model_identity,
            prompt_version=prompt_version,
            workflow_family=self._workflow_family,
            workflow_task=workflow_task,
            generated_at=datetime.now(timezone.utc),
            reviewed_input_refs=reviewed_input_refs,
            output_text=None,
            attempt_count=1,
            request_provenance={
                "provider_identity": provider_identity,
                "model_identity": model_identity,
                "prompt_version": prompt_version,
                "workflow_family": self._workflow_family,
                "workflow_task": workflow_task,
                "reviewed_input_refs": reviewed_input_refs,
                "request_metadata": {
                    "record_family": record_family,
                    "record_id": record_id,
                },
                "error_source": "adapter.generate",
            },
            response_provenance={},
            failures=(failure,),
            failure_summary=(
                f"attempt {failure.attempt_number}: "
                f"{failure_kind}: {failure_detail}"
            ),
            operational_quality={
                "availability": "unavailable",
                "posture": failure_metadata["posture"],
                "retry_policy": "retry_exhausted",
                "terminal_failure_kind": failure_kind,
            },
        )

    def _provider_operability_linkage(
        self,
        *,
        adapter: object,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        workflow_snapshot: Any,
    ) -> dict[str, object]:
        if provider_result is None:
            return {
                "provider_identity": self._adapter_identity(
                    adapter,
                    "_provider_identity",
                    "not_configured",
                ),
                "provider_model_identity": self._adapter_identity(
                    adapter,
                    "_model_identity",
                    "not_configured",
                ),
                "provider_status": "not_requested",
                "provider_failure_summary": None,
                "provider_failures": (),
                "provider_operational_quality": {
                    "availability": "available",
                    "posture": "ready",
                    "retry_policy": "not_applicable",
                    "terminal_failure_kind": None,
                },
                "provider_workflow_family": self._workflow_family,
                "provider_workflow_task": workflow_snapshot.workflow_task,
            }

        operational_quality = dict(provider_result.operational_quality)
        if not operational_quality:
            if provider_result.status == "ready":
                operational_quality = {
                    "availability": "available",
                    "posture": "ready",
                    "retry_policy": "not_needed",
                    "terminal_failure_kind": None,
                }
            else:
                terminal_failure_kind = (
                    "timeout"
                    if provider_result.status == "timeout"
                    else "provider_error"
                )
                operational_quality = {
                    "availability": "unavailable",
                    "posture": (
                        "timeout"
                        if terminal_failure_kind == "timeout"
                        else "unavailable"
                    ),
                    "retry_policy": "retry_exhausted",
                    "terminal_failure_kind": terminal_failure_kind,
                }

        return {
            "provider_identity": provider_result.provider_identity,
            "provider_model_identity": provider_result.model_identity,
            "provider_request_provenance": dict(provider_result.request_provenance),
            "provider_response_provenance": dict(provider_result.response_provenance),
            "provider_failures": tuple(
                {
                    "attempt_number": failure.attempt_number,
                    "failure_kind": failure.failure_kind,
                    "detail": failure.detail,
                }
                for failure in provider_result.failures
            ),
            "provider_failure_summary": provider_result.failure_summary,
            "provider_status": provider_result.status,
            "provider_operational_quality": operational_quality,
            "provider_workflow_family": provider_result.workflow_family,
            "provider_workflow_task": provider_result.workflow_task,
        }

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
            else self._ai_trace_lifecycle.primary_linked_id(
                getattr(context_snapshot, "linked_alert_ids")
            )
        )
        source_case_id = (
            getattr(context_snapshot, "record_id")
            if getattr(context_snapshot, "record_family") == "case"
            else self._ai_trace_lifecycle.primary_linked_id(
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
                "trace_governance": ai_trace_record.subject_linkage["trace_governance"],
            },
        )
