from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Queue
import threading
from typing import Mapping, Protocol

from .models import AITraceRecord


class AssistantProviderTransport(Protocol):
    def send_request(self, *, request: Mapping[str, object]) -> Mapping[str, object]:
        """Send a provider request and return the provider response payload."""


class AssistantProviderTimeout(RuntimeError):
    """Raised when the provider transport exceeds the reviewed timeout budget."""


@dataclass(frozen=True)
class AssistantProviderAttemptFailure:
    attempt_number: int
    failure_kind: str
    detail: str


@dataclass(frozen=True)
class AssistantProviderResult:
    status: str
    provider_identity: str
    model_identity: str
    prompt_version: str
    workflow_family: str
    workflow_task: str
    generated_at: datetime
    reviewed_input_refs: tuple[str, ...]
    output_text: str | None
    attempt_count: int
    request_provenance: Mapping[str, object]
    response_provenance: Mapping[str, object]
    failures: tuple[AssistantProviderAttemptFailure, ...]
    failure_summary: str | None
    operational_quality: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantProviderFailure(AssistantProviderResult):
    pass


class AssistantProviderAdapter:
    def __init__(
        self,
        *,
        provider_identity: str,
        model_identity: str,
        prompt_version: str,
        request_timeout_seconds: float,
        max_attempts: int,
        transport: AssistantProviderTransport,
    ) -> None:
        if request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than zero")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self._provider_identity = provider_identity
        self._model_identity = model_identity
        self._prompt_version = prompt_version
        self._request_timeout_seconds = float(request_timeout_seconds)
        self._max_attempts = max_attempts
        self._transport = transport

    def generate(
        self,
        *,
        workflow_family: str,
        workflow_task: str,
        transcript: list[Mapping[str, object]],
        reviewed_input_refs: tuple[str, ...],
        metadata: Mapping[str, object],
    ) -> AssistantProviderResult:
        generated_at = datetime.now(timezone.utc)
        failures: list[AssistantProviderAttemptFailure] = []
        request_provenance = {
            "provider_identity": self._provider_identity,
            "model_identity": self._model_identity,
            "prompt_version": self._prompt_version,
            "workflow_family": workflow_family,
            "workflow_task": workflow_task,
            "memory_policy": "no_memory",
            "allow_provider_memory": False,
            "timeout_seconds": self._request_timeout_seconds,
            "max_attempts": self._max_attempts,
            "transcript_messages": len(transcript),
            "reviewed_input_refs": tuple(reviewed_input_refs),
            "request_metadata": dict(metadata),
        }

        for attempt_number in range(1, self._max_attempts + 1):
            try:
                request = deepcopy(request_provenance)
                request["transcript"] = tuple(dict(message) for message in transcript)
                response = self._send_request_with_timeout(request=request)
                output_text = self._require_non_empty_string(
                    response.get("output_text"),
                    "provider response output_text",
                )
                response_provenance = {
                    "provider_request_id": self._string_or_none(
                        response.get("provider_request_id")
                    ),
                    "provider_response_id": self._string_or_none(
                        response.get("provider_response_id")
                    ),
                    "provider_transcript_id": self._string_or_none(
                        response.get("provider_transcript_id")
                    ),
                    "model_version": self._string_or_none(response.get("model_version"))
                    or self._model_identity,
                }
                return AssistantProviderResult(
                    status="ready",
                    provider_identity=self._provider_identity,
                    model_identity=self._model_identity,
                    prompt_version=self._prompt_version,
                    workflow_family=workflow_family,
                    workflow_task=workflow_task,
                    generated_at=generated_at,
                    reviewed_input_refs=tuple(reviewed_input_refs),
                    output_text=output_text,
                    attempt_count=attempt_number,
                    request_provenance=request_provenance,
                    response_provenance=response_provenance,
                    failures=tuple(failures),
                    failure_summary=None,
                    operational_quality=self._operational_quality_for_success(
                        failures=tuple(failures)
                    ),
                )
            except AssistantProviderTimeout as exc:
                failures.append(
                    AssistantProviderAttemptFailure(
                        attempt_number=attempt_number,
                        failure_kind="timeout",
                        detail=str(exc),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    AssistantProviderAttemptFailure(
                        attempt_number=attempt_number,
                        failure_kind="provider_error",
                        detail=str(exc),
                    )
                )

        failure_summary = "; ".join(
            f"attempt {failure.attempt_number}: {failure.failure_kind}: {failure.detail}"
            for failure in failures
        )
        terminal_failure_kind = (
            failures[-1].failure_kind if failures else "provider_error"
        )
        status = "timeout" if terminal_failure_kind == "timeout" else "failed"
        return AssistantProviderFailure(
            status=status,
            provider_identity=self._provider_identity,
            model_identity=self._model_identity,
            prompt_version=self._prompt_version,
            workflow_family=workflow_family,
            workflow_task=workflow_task,
            generated_at=generated_at,
            reviewed_input_refs=tuple(reviewed_input_refs),
            output_text=None,
            attempt_count=self._max_attempts,
            request_provenance=request_provenance,
            response_provenance={},
            failures=tuple(failures),
            failure_summary=failure_summary,
            operational_quality=self._operational_quality_for_failure(
                terminal_failure_kind=terminal_failure_kind
            ),
        )

    def _send_request_with_timeout(
        self,
        *,
        request: Mapping[str, object],
    ) -> Mapping[str, object]:
        result_queue: Queue[tuple[str, object]] = Queue(maxsize=1)

        def run_transport() -> None:
            try:
                response = self._transport.send_request(request=request)
            except Exception as exc:  # noqa: BLE001
                result_queue.put(("error", exc))
                return
            result_queue.put(("response", response))

        worker = threading.Thread(
            target=run_transport,
            name="assistant-provider-request",
            daemon=True,
        )
        worker.start()
        worker.join(timeout=self._request_timeout_seconds)
        if worker.is_alive():
            raise AssistantProviderTimeout(
                f"provider request timed out after {self._request_timeout_seconds:g} seconds"
            )
        outcome_kind, outcome_value = result_queue.get_nowait()
        if outcome_kind == "error":
            raise outcome_value  # type: ignore[misc]
        if not isinstance(outcome_value, Mapping):
            raise TypeError("provider response must be a mapping")
        return outcome_value

    def build_ai_trace_record(
        self,
        *,
        ai_trace_id: str,
        reviewer_identity: str,
        generated_at: datetime,
        result: AssistantProviderResult,
        subject_linkage: Mapping[str, object],
    ) -> AITraceRecord:
        linked_subjects = dict(subject_linkage)
        linked_subjects.update(
            {
                "provider_identity": result.provider_identity,
                "provider_model_identity": result.model_identity,
                "provider_request_provenance": dict(result.request_provenance),
                "provider_response_provenance": dict(result.response_provenance),
                "provider_failures": tuple(
                    {
                        "attempt_number": failure.attempt_number,
                        "failure_kind": failure.failure_kind,
                        "detail": failure.detail,
                    }
                    for failure in result.failures
                ),
                "provider_failure_summary": result.failure_summary,
                "provider_status": result.status,
                "provider_operational_quality": dict(result.operational_quality),
                "provider_workflow_family": result.workflow_family,
                "provider_workflow_task": result.workflow_task,
            }
        )
        return AITraceRecord(
            ai_trace_id=ai_trace_id,
            subject_linkage=linked_subjects,
            model_identity=f"{result.provider_identity}/{result.model_identity}",
            prompt_version=result.prompt_version,
            generated_at=generated_at,
            material_input_refs=result.reviewed_input_refs,
            reviewer_identity=reviewer_identity,
            lifecycle_state="generated" if result.status == "ready" else "under_review",
        )

    @staticmethod
    def _operational_quality_for_success(
        *,
        failures: tuple[AssistantProviderAttemptFailure, ...],
    ) -> Mapping[str, object]:
        if failures:
            return {
                "availability": "available",
                "posture": "degraded",
                "retry_policy": "retried",
                "terminal_failure_kind": None,
            }
        return {
            "availability": "available",
            "posture": "ready",
            "retry_policy": "not_needed",
            "terminal_failure_kind": None,
        }

    @staticmethod
    def _operational_quality_for_failure(
        *,
        terminal_failure_kind: str,
    ) -> Mapping[str, object]:
        posture = "timeout" if terminal_failure_kind == "timeout" else "unavailable"
        return {
            "availability": "unavailable",
            "posture": posture,
            "retry_policy": "retry_exhausted",
            "terminal_failure_kind": terminal_failure_kind,
        }

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _string_or_none(value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return value
        return None
