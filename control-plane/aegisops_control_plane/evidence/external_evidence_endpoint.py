from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Iterable, Mapping, Protocol

from . import external_evidence_osquery as _external_evidence_osquery
from ..actions.execution_coordinator import _approved_payload_binding_hash, _json_ready
from ..models import (
    ActionRequestRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    LifecycleTransitionRecord,
)


class _LifecycleTransitionHelper(Protocol):
    def build_lifecycle_transition_records(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...


class _DetectionIntakeBoundary(Protocol):
    lifecycle_transition_helper: _LifecycleTransitionHelper


class EndpointExternalEvidenceDependencies(Protocol):
    _store: object
    _endpoint_evidence_pack_adapter: object
    _detection_intake_service: _DetectionIntakeBoundary

    def persist_record(
        self,
        record: object,
        *,
        transitioned_at: datetime | None = None,
    ) -> object:
        ...

    def _require_non_empty_string(self, value: object, field_name: str) -> str:
        ...

    def _require_aware_datetime(self, value: object, field_name: str) -> datetime:
        ...

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
        ...

    def _validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        ...

    def _next_identifier(self, prefix: str) -> str:
        ...

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


class EndpointExternalEvidenceHelper:
    def __init__(self, service: EndpointExternalEvidenceDependencies) -> None:
        self._service = service

    def create_collection_request(
        self,
        *,
        case_id: str,
        admitting_evidence_id: str,
        requester_identity: str,
        host_identifier: str,
        evidence_gap: str,
        artifact_classes: tuple[str, ...],
        expires_at: datetime,
        reviewed_gap_id: str | None = None,
        reviewed_follow_up_decision_id: str | None = None,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        case_id = self._service._require_non_empty_string(case_id, "case_id")
        admitting_evidence_id = self._service._require_non_empty_string(
            admitting_evidence_id,
            "admitting_evidence_id",
        )
        requester_identity = self._service._require_non_empty_string(
            requester_identity,
            "requester_identity",
        )
        host_identifier = self._service._require_non_empty_string(
            host_identifier,
            "host_identifier",
        )
        evidence_gap = self._service._require_non_empty_string(
            evidence_gap,
            "evidence_gap",
        )
        expires_at = self._service._require_aware_datetime(expires_at, "expires_at")
        normalized_artifact_classes = (
            self._service._endpoint_evidence_pack_adapter.normalize_requested_artifact_classes(
                artifact_classes
            )
        )

        with self._service._store.transaction(isolation_level="SERIALIZABLE"):
            case = self._service._require_reviewed_operator_case(case_id)
            authoritative_host_identifier = (
                _external_evidence_osquery.require_case_host_identifier(case)
            )
            if host_identifier != authoritative_host_identifier:
                raise ValueError(
                    "host_identifier must match the authoritative reviewed case host binding"
                )
            self._service._validate_case_evidence_linkage(
                case=case,
                evidence_ids=(admitting_evidence_id,),
                field_name="admitting_evidence_id",
            )
            reviewed_gap_anchor = self._resolve_reviewed_gap_anchor(
                case=case,
                admitting_evidence_id=admitting_evidence_id,
                host_identifier=host_identifier,
                evidence_gap=evidence_gap,
                reviewed_gap_id=reviewed_gap_id,
            )
            reviewed_follow_up_anchor = self._resolve_reviewed_follow_up_decision_anchor(
                case=case,
                admitting_evidence_id=admitting_evidence_id,
                host_identifier=host_identifier,
                evidence_gap=evidence_gap,
                reviewed_follow_up_decision_id=reviewed_follow_up_decision_id,
            )
            if reviewed_gap_anchor is None and reviewed_follow_up_anchor is None:
                raise ValueError(
                    "reviewed endpoint evidence requests require an explicit reviewed gap anchor"
                )
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("expires_at must be in the future")

            requested_payload = {
                "action_type": "collect_endpoint_evidence_pack",
                "collection_mode": "read_only",
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "admitting_evidence_id": admitting_evidence_id,
                "host_identifier": host_identifier,
                "evidence_gap": evidence_gap,
                "reviewed_gap_id": (
                    reviewed_gap_anchor["reviewed_gap_id"]
                    if reviewed_gap_anchor is not None
                    else None
                ),
                "reviewed_follow_up_decision_id": (
                    reviewed_follow_up_anchor["reviewed_follow_up_decision_id"]
                    if reviewed_follow_up_anchor is not None
                    else None
                ),
                "artifact_classes": normalized_artifact_classes,
            }
            target_scope = {
                "case_id": case.case_id,
                "alert_id": case.alert_id,
                "finding_id": case.finding_id,
                "admitting_evidence_id": admitting_evidence_id,
                "host_identifier": host_identifier,
                "reviewed_gap_id": (
                    reviewed_gap_anchor["reviewed_gap_id"]
                    if reviewed_gap_anchor is not None
                    else None
                ),
                "reviewed_follow_up_decision_id": (
                    reviewed_follow_up_anchor["reviewed_follow_up_decision_id"]
                    if reviewed_follow_up_anchor is not None
                    else None
                ),
                "artifact_classes": normalized_artifact_classes,
            }
            payload_hash = _approved_payload_binding_hash(
                target_scope=target_scope,
                approved_payload=requested_payload,
                execution_surface_type="executor",
                execution_surface_id="isolated-executor",
            )
            requested_at = datetime.now(timezone.utc)
            if expires_at <= requested_at:
                raise ValueError("expires_at must be after requested_at")

            idempotency_material = json.dumps(
                _json_ready(
                    {
                        "payload_hash": payload_hash,
                        "requester_identity": requester_identity,
                        "expires_at": expires_at,
                    }
                ),
                sort_keys=True,
                separators=(",", ":"),
            )
            idempotency_key = (
                "endpoint-evidence-pack:"
                + hashlib.sha256(idempotency_material.encode("utf-8")).hexdigest()
            )
            normalized_action_request_id = self._service._normalize_optional_string(
                action_request_id,
                "action_request_id",
            ) or self._service._next_identifier("action-request")
            action_request_record = ActionRequestRecord(
                action_request_id=normalized_action_request_id,
                approval_decision_id=None,
                case_id=case.case_id,
                alert_id=case.alert_id,
                finding_id=case.finding_id,
                idempotency_key=idempotency_key,
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="pending_approval",
                requester_identity=requester_identity,
                requested_payload=requested_payload,
                policy_basis={
                    "severity": "medium",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "approval_requirement_override": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
            if action_request_id is not None:
                existing_action_request = self._service._store.get(
                    ActionRequestRecord,
                    normalized_action_request_id,
                )
                if existing_action_request is not None:
                    if (
                        existing_action_request.idempotency_key
                        != action_request_record.idempotency_key
                        or existing_action_request.payload_hash
                        != action_request_record.payload_hash
                    ):
                        raise ValueError(
                            "action_request_id already exists for a different action request payload"
                        )
                    return existing_action_request
            action_request, created = (
                self._service._store.create_action_request_if_absent(
                    action_request_record
                )
            )
            if created:
                transition_helper = (
                    self._service._detection_intake_service.lifecycle_transition_helper
                )
                for transition_record in transition_helper.build_lifecycle_transition_records(
                    action_request,
                    existing_record=None,
                    transitioned_at=requested_at,
                ):
                    self._service._store.save(transition_record)
            return action_request

    def ingest_artifacts(
        self,
        *,
        action_request_id: str,
        artifacts: tuple[Mapping[str, object], ...],
        admitted_by: str,
    ) -> tuple[EvidenceRecord, ...]:
        action_request_id = self._service._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        admitted_by = self._service._require_non_empty_string(
            admitted_by,
            "admitted_by",
        )
        if not isinstance(artifacts, tuple):
            raise ValueError("artifacts must be a tuple of artifact mappings")
        if not artifacts:
            raise ValueError("artifacts must contain at least one artifact mapping")

        with self._service._store.transaction(isolation_level="SERIALIZABLE"):
            action_request = self._service._store.get(
                ActionRequestRecord,
                action_request_id,
            )
            if action_request is None:
                raise LookupError(f"Missing action request {action_request_id!r}")
            if (
                action_request.requested_payload.get("action_type")
                != "collect_endpoint_evidence_pack"
            ):
                raise ValueError(
                    "action_request_id is not a reviewed endpoint evidence collection request"
                )
            if action_request.lifecycle_state not in {"approved", "executing"}:
                raise ValueError(
                    "endpoint evidence artifacts may only be admitted for approved or executing endpoint evidence requests"
                )
            now = datetime.now(timezone.utc)
            if action_request.expires_at is not None and now > action_request.expires_at:
                raise ValueError(
                    "endpoint evidence artifacts cannot be admitted after request expiry"
                )

            case_id = self._service._require_non_empty_string(
                action_request.case_id,
                "case_id",
            )
            case = self._service._require_reviewed_operator_case(case_id)
            authoritative_host_identifier = (
                _external_evidence_osquery.require_case_host_identifier(case)
            )
            approved_host_identifier = self._service._require_non_empty_string(
                action_request.target_scope.get("host_identifier"),
                "action_request.target_scope.host_identifier",
            )
            if approved_host_identifier != authoritative_host_identifier:
                raise ValueError(
                    "endpoint evidence request host binding drifted from the authoritative reviewed case host binding"
                )
            admitting_evidence_id = self._service._require_non_empty_string(
                action_request.requested_payload.get("admitting_evidence_id"),
                "action_request.requested_payload.admitting_evidence_id",
            )
            self._service._validate_case_evidence_linkage(
                case=case,
                evidence_ids=(admitting_evidence_id,),
                field_name="action_request.requested_payload.admitting_evidence_id",
            )
            requested_artifact_classes = (
                self._service._endpoint_evidence_pack_adapter.normalize_requested_artifact_classes(
                    action_request.requested_payload.get("artifact_classes")
                )
            )
            attachments = tuple(
                self._service._endpoint_evidence_pack_adapter.build_attachment(
                    action_request_id=action_request.action_request_id,
                    case_id=case.case_id,
                    alert_id=case.alert_id,
                    admitting_evidence_id=admitting_evidence_id,
                    authoritative_host_identifier=authoritative_host_identifier,
                    requested_artifact_classes=requested_artifact_classes,
                    artifact=artifact,
                    admitted_by=admitted_by,
                )
                for artifact in artifacts
            )
            if len({attachment.source_record_id for attachment in attachments}) != len(
                attachments
            ):
                raise ValueError(
                    "artifacts must not contain duplicate artifact_id values within one request"
                )
            seen_artifact_ids: set[str] = set()
            for attachment in attachments:
                artifact_id = self._service._normalize_optional_string(
                    attachment.provenance.get("artifact_id"),
                    "attachment.provenance.artifact_id",
                )
                if artifact_id is None:
                    continue
                if artifact_id in seen_artifact_ids:
                    raise ValueError(
                        "artifacts must not contain duplicate artifact_id values within one request"
                    )
                seen_artifact_ids.add(artifact_id)

            existing_by_source_record_id = {
                record.source_record_id: record
                for record in self._service._store.list(EvidenceRecord)
                if record.case_id == case.case_id
            }
            indexed_artifacts = self._index_request_artifacts(
                case_id=case.case_id,
                action_request_id=action_request.action_request_id,
                evidence_records=existing_by_source_record_id.values(),
            )
            persisted: list[EvidenceRecord] = []

            def artifact_class_for(attachment: object) -> str:
                return self._service._require_non_empty_string(
                    attachment.provenance.get("artifact_class"),
                    "attachment.provenance.artifact_class",
                )

            def persist_or_reuse_attachment(attachment: object) -> None:
                existing = existing_by_source_record_id.get(attachment.source_record_id)
                if existing is not None:
                    if (
                        existing.source_system != attachment.source_system
                        or existing.collector_identity != attachment.collector_identity
                        or existing.acquired_at != attachment.acquired_at
                        or existing.derivation_relationship
                        != attachment.derivation_relationship
                        or _json_ready(existing.provenance)
                        != _json_ready(attachment.provenance)
                        or _json_ready(existing.content)
                        != _json_ready(attachment.content)
                    ):
                        raise ValueError(
                            "artifact replay conflicted with previously admitted evidence"
                        )
                    persisted.append(existing)
                    return
                evidence = self._service.persist_record(
                    EvidenceRecord(
                        evidence_id=self._service._next_identifier("evidence"),
                        source_record_id=attachment.source_record_id,
                        alert_id=case.alert_id,
                        case_id=case.case_id,
                        source_system=attachment.source_system,
                        collector_identity=attachment.collector_identity,
                        acquired_at=attachment.acquired_at,
                        derivation_relationship=attachment.derivation_relationship,
                        lifecycle_state="linked",
                        provenance=attachment.provenance,
                        content=attachment.content,
                    )
                )
                persisted.append(evidence)
                existing_by_source_record_id[attachment.source_record_id] = evidence
                artifact_id = self._service._normalize_optional_string(
                    evidence.provenance.get("artifact_id"),
                    "evidence.provenance.artifact_id",
                )
                if artifact_id is not None:
                    indexed_artifacts[artifact_id] = evidence

            for attachment in attachments:
                if artifact_class_for(attachment) == "binary_analysis":
                    continue
                persist_or_reuse_attachment(attachment)
            for attachment in attachments:
                if artifact_class_for(attachment) != "binary_analysis":
                    continue
                persist_or_reuse_attachment(
                    self._resolve_binary_analysis_attachment(
                        attachment=attachment,
                        indexed_artifacts=indexed_artifacts,
                    )
                )
            current_case = self._service._require_reviewed_operator_case(case.case_id)
            merged_case_evidence_ids = current_case.evidence_ids
            for evidence in persisted:
                merged_case_evidence_ids = self._service._merge_linked_ids(
                    merged_case_evidence_ids,
                    evidence.evidence_id,
                )
            if merged_case_evidence_ids != current_case.evidence_ids:
                self._service.persist_record(
                    replace(current_case, evidence_ids=merged_case_evidence_ids)
                )
            return tuple(persisted)

    def _resolve_reviewed_gap_anchor(
        self,
        *,
        case: CaseRecord,
        admitting_evidence_id: str,
        host_identifier: str,
        evidence_gap: str,
        reviewed_gap_id: str | None,
    ) -> Mapping[str, str] | None:
        explicit_gap_id = self._service._normalize_optional_string(
            reviewed_gap_id,
            "reviewed_gap_id",
        )
        matching_anchors: list[dict[str, str]] = []
        endpoint_evidence = case.reviewed_context.get("endpoint_evidence")
        if not isinstance(endpoint_evidence, Mapping):
            return None
        reviewed_gap_anchors = endpoint_evidence.get("reviewed_gap_anchors")
        if not isinstance(reviewed_gap_anchors, (list, tuple)):
            return None

        for raw_anchor in reviewed_gap_anchors:
            if not isinstance(raw_anchor, Mapping):
                continue
            anchor_gap_id = self._service._normalize_optional_string(
                raw_anchor.get("reviewed_gap_id"),
                "case.reviewed_context.endpoint_evidence.reviewed_gap_id",
            )
            anchor_gap_text = self._service._normalize_optional_string(
                raw_anchor.get("evidence_gap"),
                "case.reviewed_context.endpoint_evidence.evidence_gap",
            )
            anchor_evidence_id = self._service._normalize_optional_string(
                raw_anchor.get("admitting_evidence_id"),
                "case.reviewed_context.endpoint_evidence.admitting_evidence_id",
            )
            anchor_host_identifier = self._service._normalize_optional_string(
                raw_anchor.get("host_identifier"),
                "case.reviewed_context.endpoint_evidence.host_identifier",
            )
            if (
                anchor_gap_id is None
                or anchor_gap_text is None
                or anchor_evidence_id is None
                or anchor_host_identifier is None
            ):
                continue
            if (
                anchor_gap_text != evidence_gap
                or anchor_evidence_id != admitting_evidence_id
                or anchor_host_identifier != host_identifier
            ):
                continue
            matching_anchors.append(
                {
                    "reviewed_gap_id": anchor_gap_id,
                    "evidence_gap": anchor_gap_text,
                    "admitting_evidence_id": anchor_evidence_id,
                    "host_identifier": anchor_host_identifier,
                }
            )

        if explicit_gap_id is None:
            if len(matching_anchors) == 1:
                return matching_anchors[0]
            if len(matching_anchors) > 1:
                raise ValueError(
                    "reviewed_gap_id is required when multiple reviewed endpoint gap anchors match the request"
                )
            return None

        for anchor in matching_anchors:
            if anchor["reviewed_gap_id"] == explicit_gap_id:
                return anchor
        raise ValueError(
            "reviewed_gap_id must reference a reviewed endpoint gap anchor on the authoritative case chain"
        )

    def _resolve_reviewed_follow_up_decision_anchor(
        self,
        *,
        case: CaseRecord,
        admitting_evidence_id: str,
        host_identifier: str,
        evidence_gap: str,
        reviewed_follow_up_decision_id: str | None,
    ) -> Mapping[str, str] | None:
        explicit_decision_id = self._service._normalize_optional_string(
            reviewed_follow_up_decision_id,
            "reviewed_follow_up_decision_id",
        )
        if explicit_decision_id is None:
            return None
        approval_decision = self._service._store.get(
            ApprovalDecisionRecord,
            explicit_decision_id,
        )
        if approval_decision is None:
            raise LookupError(f"Missing approval decision {explicit_decision_id!r}")
        if approval_decision.lifecycle_state not in {"approved", "rejected"}:
            raise ValueError(
                "reviewed_follow_up_decision_id must reference a recorded reviewed approval decision"
            )
        decision_rationale = self._service._normalize_optional_string(
            approval_decision.decision_rationale,
            "approval_decision.decision_rationale",
        )
        if decision_rationale is None or decision_rationale != evidence_gap:
            raise ValueError(
                "evidence_gap must match the reviewed follow-up decision rationale"
            )
        action_request = self._service._store.get(
            ActionRequestRecord,
            approval_decision.action_request_id,
        )
        if action_request is None:
            raise LookupError(
                "reviewed_follow_up_decision_id must reference a decision with an authoritative action request"
            )
        if action_request.case_id != case.case_id:
            raise ValueError(
                "reviewed_follow_up_decision_id must stay bound to the authoritative case chain"
            )
        decision_admitting_evidence_id = self._service._normalize_optional_string(
            action_request.target_scope.get("admitting_evidence_id"),
            "action_request.target_scope.admitting_evidence_id",
        )
        if decision_admitting_evidence_id != admitting_evidence_id:
            raise ValueError(
                "reviewed_follow_up_decision_id must stay bound to the authoritative admitting evidence anchor"
            )
        decision_host_identifier = self._service._normalize_optional_string(
            action_request.target_scope.get("host_identifier"),
            "action_request.target_scope.host_identifier",
        )
        if decision_host_identifier != host_identifier:
            raise ValueError(
                "reviewed_follow_up_decision_id must stay bound to the authoritative case host binding"
            )
        return {"reviewed_follow_up_decision_id": explicit_decision_id}

    def _index_request_artifacts(
        self,
        *,
        case_id: str,
        action_request_id: str,
        evidence_records: Iterable[EvidenceRecord],
    ) -> dict[str, EvidenceRecord]:
        indexed: dict[str, EvidenceRecord] = {}
        for record in evidence_records:
            if record.case_id != case_id:
                continue
            if (
                record.source_system
                != self._service._endpoint_evidence_pack_adapter.source_system
            ):
                continue
            request_id = self._service._normalize_optional_string(
                record.provenance.get("endpoint_request_id"),
                "evidence.provenance.endpoint_request_id",
            )
            if request_id != action_request_id:
                continue
            artifact_id = self._service._normalize_optional_string(
                record.provenance.get("artifact_id"),
                "evidence.provenance.artifact_id",
            )
            if artifact_id is None:
                continue
            indexed[artifact_id] = record
        return indexed

    def _resolve_binary_analysis_attachment(
        self,
        *,
        attachment: object,
        indexed_artifacts: Mapping[str, EvidenceRecord],
    ) -> object:
        derived_from_artifact_id = self._service._normalize_optional_string(
            attachment.provenance.get("derived_from_artifact_id"),
            "attachment.provenance.derived_from_artifact_id",
        )
        if derived_from_artifact_id is None:
            raise ValueError(
                "binary_analysis artifacts require derived_from_artifact_id"
            )
        source_artifact = indexed_artifacts.get(derived_from_artifact_id)
        if source_artifact is None:
            raise ValueError(
                "binary_analysis artifacts must derive from an admitted file_sample artifact"
            )
        source_artifact_class = self._service._normalize_optional_string(
            source_artifact.provenance.get("artifact_class"),
            "source_artifact.provenance.artifact_class",
        )
        if source_artifact_class != "file_sample":
            raise ValueError(
                "binary_analysis artifacts must derive from an admitted file_sample artifact"
            )
        source_artifact_id = self._service._normalize_optional_string(
            source_artifact.provenance.get("artifact_id"),
            "source_artifact.provenance.artifact_id",
        )
        if source_artifact_id != derived_from_artifact_id:
            raise ValueError(
                "binary_analysis artifacts must derive from an admitted file_sample artifact"
            )
        return replace(
            attachment,
            provenance={
                **dict(attachment.provenance),
                "derived_from_evidence_id": source_artifact.evidence_id,
                "derived_from_source_record_id": source_artifact.source_record_id,
            },
            content={
                **dict(attachment.content),
                "artifact": {
                    **dict(attachment.content.get("artifact", {})),
                    "derived_from_evidence_id": source_artifact.evidence_id,
                    "derived_from_source_record_id": source_artifact.source_record_id,
                },
            },
        )
