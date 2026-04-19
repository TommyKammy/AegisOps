from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence
from urllib.parse import quote


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _normalize_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _normalize_string_sequence(
    value: object,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    normalized: list[str] = []
    for index, item in enumerate(value):
        normalized.append(
            _require_non_empty_string(item, f"{field_name}[{index}]")
        )
    return tuple(normalized)


def _normalize_yara_matches(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(
            "binary_analysis artifacts for YARA require at least one structured match"
        )
    normalized_matches: list[dict[str, object]] = []
    for index, match in enumerate(value):
        normalized_match = _normalize_mapping(match, f"artifact.content.matches[{index}]")
        rule_name = _require_non_empty_string(
            normalized_match.get("rule_name"),
            f"artifact.content.matches[{index}].rule_name",
        )
        normalized: dict[str, object] = {"rule_name": rule_name}
        namespace = normalized_match.get("namespace")
        if namespace is not None:
            normalized["namespace"] = _require_non_empty_string(
                namespace,
                f"artifact.content.matches[{index}].namespace",
            )
        tags = normalized_match.get("tags")
        if tags is not None:
            normalized["tags"] = _normalize_string_sequence(
                tags,
                f"artifact.content.matches[{index}].tags",
            )
        normalized_matches.append(normalized)
    if not normalized_matches:
        raise ValueError(
            "binary_analysis artifacts for YARA require at least one structured match"
        )
    return tuple(normalized_matches)


@dataclass(frozen=True)
class EndpointEvidenceArtifactAttachment:
    source_record_id: str
    source_system: str
    collector_identity: str
    acquired_at: datetime
    derivation_relationship: str
    provenance: Mapping[str, object]
    content: Mapping[str, object]


@dataclass(frozen=True)
class EndpointEvidencePackAdapter:
    source_system: str = "endpoint_evidence_pack"
    allowed_artifact_classes: tuple[str, ...] = (
        "binary_analysis",
        "collection_manifest",
        "file_sample",
        "tool_output_receipt",
        "triage_bundle",
    )
    allowed_citation_kinds: tuple[str, ...] = (
        "bounded_derivative",
        "operator_authored_interpretation",
        "raw_collected_output",
    )
    allowed_binary_analysis_tools: tuple[str, ...] = ("capa", "yara")
    required_source_boundary: str = "endpoint_evidence_pack"

    def normalize_requested_artifact_classes(
        self,
        artifact_classes: object,
    ) -> tuple[str, ...]:
        if not isinstance(artifact_classes, Sequence) or isinstance(
            artifact_classes,
            (str, bytes),
        ):
            raise ValueError("artifact_classes must be a sequence of strings")
        normalized: list[str] = []
        for index, artifact_class in enumerate(artifact_classes):
            normalized_class = _require_non_empty_string(
                artifact_class,
                f"artifact_classes[{index}]",
            )
            if normalized_class not in self.allowed_artifact_classes:
                raise ValueError(
                    f"artifact_class must be one of {self.allowed_artifact_classes!r}"
                )
            if normalized_class not in normalized:
                normalized.append(normalized_class)
        if not normalized:
            raise ValueError("artifact_classes must contain at least one artifact class")
        return tuple(sorted(normalized))

    def build_attachment(
        self,
        *,
        action_request_id: str,
        case_id: str,
        alert_id: str | None,
        admitting_evidence_id: str,
        authoritative_host_identifier: str,
        requested_artifact_classes: tuple[str, ...],
        artifact: object,
        admitted_by: object,
    ) -> EndpointEvidenceArtifactAttachment:
        action_request_id = _require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        case_id = _require_non_empty_string(case_id, "case_id")
        admitting_evidence_id = _require_non_empty_string(
            admitting_evidence_id,
            "admitting_evidence_id",
        )
        authoritative_host_identifier = _require_non_empty_string(
            authoritative_host_identifier,
            "authoritative_host_identifier",
        )
        admitted_by = _require_non_empty_string(admitted_by, "admitted_by")
        normalized_artifact = _normalize_mapping(artifact, "artifact")
        artifact_class = _require_non_empty_string(
            normalized_artifact.get("artifact_class"),
            "artifact.artifact_class",
        )
        if artifact_class not in self.allowed_artifact_classes:
            raise ValueError(
                f"artifact_class must be one of {self.allowed_artifact_classes!r}"
            )
        if artifact_class not in requested_artifact_classes:
            raise ValueError(
                "artifact_class is outside the approved endpoint evidence request scope"
            )
        artifact_id = _require_non_empty_string(
            normalized_artifact.get("artifact_id"),
            "artifact.artifact_id",
        )
        source_artifact_id = _require_non_empty_string(
            normalized_artifact.get("source_artifact_id"),
            "artifact.source_artifact_id",
        )
        collected_at = _require_aware_datetime(
            normalized_artifact.get("collected_at"),
            "artifact.collected_at",
        )
        collector_identity = _require_non_empty_string(
            normalized_artifact.get("collector_identity"),
            "artifact.collector_identity",
        )
        tool_name = _require_non_empty_string(
            normalized_artifact.get("tool_name"),
            "artifact.tool_name",
        )
        source_boundary = _require_non_empty_string(
            normalized_artifact.get("source_boundary"),
            "artifact.source_boundary",
        )
        if source_boundary != self.required_source_boundary:
            raise ValueError(
                "artifact.source_boundary must match the reviewed endpoint evidence boundary"
            )
        citation_kind = _require_non_empty_string(
            normalized_artifact.get("citation_kind"),
            "artifact.citation_kind",
        )
        if citation_kind not in self.allowed_citation_kinds:
            raise ValueError(
                f"artifact.citation_kind must be one of {self.allowed_citation_kinds!r}"
            )
        description = _require_non_empty_string(
            normalized_artifact.get("description"),
            "artifact.description",
        )
        content = _normalize_mapping(normalized_artifact.get("content"), "artifact.content")

        artifact_host_identifier = normalized_artifact.get("host_identifier")
        if artifact_host_identifier is not None:
            artifact_host_identifier = _require_non_empty_string(
                artifact_host_identifier,
                "artifact.host_identifier",
            )
            if artifact_host_identifier != authoritative_host_identifier:
                raise ValueError(
                    "artifact.host_identifier must match the authoritative reviewed case host binding"
                )

        derived_from_artifact_id = normalized_artifact.get("derived_from_artifact_id")
        if derived_from_artifact_id is not None:
            derived_from_artifact_id = _require_non_empty_string(
                derived_from_artifact_id,
                "artifact.derived_from_artifact_id",
            )
        if artifact_class == "binary_analysis" and derived_from_artifact_id is None:
            raise ValueError(
                "binary_analysis artifacts require derived_from_artifact_id"
            )

        tool_version = normalized_artifact.get("tool_version")
        if tool_version is not None:
            tool_version = _require_non_empty_string(
                tool_version,
                "artifact.tool_version",
            )

        normalized_analysis_tool: str | None = None
        if artifact_class == "binary_analysis":
            normalized_analysis_tool = tool_name.strip().lower()
            if normalized_analysis_tool not in self.allowed_binary_analysis_tools:
                raise ValueError(
                    "binary_analysis artifacts must identify YARA or capa as the analysis tool"
                )
            if normalized_analysis_tool == "yara":
                content = {
                    **content,
                    "matches": _normalize_yara_matches(content.get("matches")),
                }
            else:
                content = {
                    **content,
                    "summary": _require_non_empty_string(
                        content.get("summary"),
                        "artifact.content.summary",
                    ),
                }

        source_record_id = (
            "endpoint-evidence://request/{}/artifact/{}".format(
                quote(action_request_id, safe=""),
                quote(artifact_id, safe=""),
            )
        )
        provenance = {
            "classification": (
                "reviewed-derived"
                if artifact_class == "binary_analysis"
                else "augmenting-evidence"
            ),
            "source_id": source_artifact_id,
            "timestamp": collected_at.isoformat(),
            "reviewed_by": admitted_by,
            "source_system": self.source_system,
            "source_boundary": source_boundary,
            "artifact_class": artifact_class,
            "artifact_id": artifact_id,
            "endpoint_request_id": action_request_id,
            "case_id": case_id,
            "admitting_evidence_id": admitting_evidence_id,
            "host_identifier": authoritative_host_identifier,
            "collector_identity": collector_identity,
            "tool_name": tool_name,
            "ambiguity_badge": "related-entity",
        }
        if tool_version is not None:
            provenance["tool_version"] = tool_version
        if derived_from_artifact_id is not None:
            provenance["derived_from_artifact_id"] = derived_from_artifact_id
        if normalized_analysis_tool is not None:
            provenance["analysis_tool"] = normalized_analysis_tool

        return EndpointEvidenceArtifactAttachment(
            source_record_id=source_record_id,
            source_system=self.source_system,
            collector_identity=collector_identity,
            acquired_at=collected_at,
            derivation_relationship=(
                "endpoint_evidence_pack_analysis"
                if artifact_class == "binary_analysis"
                else "endpoint_evidence_pack_artifact"
            ),
            provenance=provenance,
            content={
                "artifact_class": artifact_class,
                "description": description,
                "source_boundary": source_boundary,
                "citation": {
                    "kind": citation_kind,
                    "artifact_id": artifact_id,
                    "ready": True,
                },
                "artifact": {
                    "artifact_id": artifact_id,
                    "source_artifact_id": source_artifact_id,
                    "derived_from_artifact_id": derived_from_artifact_id,
                    "host_identifier": authoritative_host_identifier,
                    "tool_name": tool_name,
                    "tool_version": tool_version,
                    "analysis_tool": normalized_analysis_tool,
                },
                "payload": content,
                "scope": {
                    "case_id": case_id,
                    "alert_id": alert_id,
                    "admitting_evidence_id": admitting_evidence_id,
                    "action_request_id": action_request_id,
                },
            },
        )
