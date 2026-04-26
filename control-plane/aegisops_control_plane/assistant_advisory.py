from __future__ import annotations

from typing import Any, Protocol

from .models import AITraceRecord, RecommendationRecord


class AssistantAdvisoryAssembler(Protocol):
    def inspect_advisory_output(self, record_family: str, record_id: str) -> Any:
        ...

    def render_recommendation_draft(self, record_family: str, record_id: str) -> Any:
        ...

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        ...


class AssistantAdvisoryCoordinator:
    """Coordinates advisory-only assembly behind the service API."""

    def __init__(self, assembler: AssistantAdvisoryAssembler) -> None:
        self._assembler = assembler

    def inspect_advisory_output(self, record_family: str, record_id: str) -> Any:
        return self._assembler.inspect_advisory_output(record_family, record_id)

    def render_recommendation_draft(self, record_family: str, record_id: str) -> Any:
        return self._assembler.render_recommendation_draft(record_family, record_id)

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        return self._assembler.attach_assistant_advisory_draft(record_family, record_id)
