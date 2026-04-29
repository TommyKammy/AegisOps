from __future__ import annotations

from collections import Counter
from contextlib import AbstractContextManager
from dataclasses import fields
from datetime import datetime
from typing import Mapping, Protocol, Type, TypeVar

from .audit_export import _redact_audit_export_value
from .models import CaseRecord, ControlPlaneRecord, EvidenceRecord
from .publishable_paths import is_workstation_local_path


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class PilotReportingExportStore(Protocol):
    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...


_UNSUPPORTED_PILOT_CLAIM_FRAGMENTS = (
    "compliance certification is complete",
    "compliance certified",
    "sla is promised",
    "sla guarantee",
    "24x7 support is promised",
    "autonomous response is approved",
    "autonomous-response marketing",
    "multi-customer rollout is approved",
)
_SECRET_LOOKING_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {field.name: getattr(record, field.name) for field in fields(record)}


def _validate_no_unsupported_pilot_claims(value: object) -> None:
    if isinstance(value, str):
        normalized = " ".join(value.lower().split())
        if any(
            fragment in normalized
            for fragment in _UNSUPPORTED_PILOT_CLAIM_FRAGMENTS
        ):
            raise ValueError("unsupported pilot executive summary claim")
        if is_workstation_local_path(value):
            raise ValueError("workstation-local pilot executive summary path")
        if any(
            f"{fragment}:" in normalized or f"{fragment}=" in normalized
            for fragment in _SECRET_LOOKING_KEY_FRAGMENTS
        ):
            raise ValueError("secret-looking pilot executive summary value")
        return
    if isinstance(value, Mapping):
        for item in value.values():
            _validate_no_unsupported_pilot_claims(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _validate_no_unsupported_pilot_claims(item)


def _case_matches_release(case: CaseRecord, release_identifier: str) -> bool:
    return case.reviewed_context.get("pilot_release_identifier") == release_identifier


def _subordinate_evidence_payload(evidence: EvidenceRecord) -> dict[str, object]:
    return {
        "authority_role": "subordinate_evidence",
        "promotion_allowed": False,
        "source_system": evidence.source_system,
        "source_record_id": evidence.source_record_id,
        "derivation_relationship": evidence.derivation_relationship,
        "lifecycle_state": evidence.lifecycle_state,
        "acquired_at": evidence.acquired_at.isoformat(),
        "provenance": _redact_audit_export_value(evidence.provenance),
        "content": _redact_audit_export_value(evidence.content),
    }


def _authoritative_case_payload(
    case: CaseRecord,
    *,
    evidence_by_id: Mapping[str, EvidenceRecord],
) -> dict[str, object]:
    payload = {
        key: _redact_audit_export_value(_json_ready(value), key=key)
        for key, value in _record_to_dict(case).items()
    }
    payload["authority_role"] = "authoritative_control_plane_record"
    payload["subordinate_evidence"] = [
        _subordinate_evidence_payload(evidence_by_id[evidence_id])
        for evidence_id in case.evidence_ids
        if evidence_id in evidence_by_id
    ]
    return payload


def export_pilot_executive_summary(
    *,
    store: PilotReportingExportStore,
    export_id: str,
    release_identifier: str,
    exported_at: datetime,
    executive_note: str | None = None,
) -> dict[str, object]:
    if not isinstance(export_id, str) or export_id.strip() == "":
        raise ValueError("export_id must be a non-empty string")
    if not isinstance(release_identifier, str) or release_identifier.strip() == "":
        raise ValueError("release_identifier must be a non-empty string")
    if not isinstance(exported_at, datetime) or exported_at.tzinfo is None:
        raise ValueError("exported_at must be a timezone-aware datetime")
    export_id = export_id.strip()
    release_identifier = release_identifier.strip()
    _validate_no_unsupported_pilot_claims(executive_note)

    with store.transaction(isolation_level="REPEATABLE READ"):
        evidence_by_id = {
            evidence.evidence_id: evidence
            for evidence in store.list(EvidenceRecord)
        }
        cases = tuple(
            case
            for case in store.list(CaseRecord)
            if _case_matches_release(case, release_identifier)
        )
        case_payloads = [
            _authoritative_case_payload(case, evidence_by_id=evidence_by_id)
            for case in cases
        ]

    _validate_no_unsupported_pilot_claims(case_payloads)

    return {
        "schema_version": "phase49.5.pilot-summary.v1",
        "export_id": export_id,
        "release_identifier": release_identifier,
        "exported_at": exported_at.isoformat(),
        "source_of_truth": "aegisops_authoritative_records",
        "executive_note": executive_note,
        "claim_boundaries": {
            "compliance_certification_claim": False,
            "sla_guarantee_claim": False,
            "autonomous_response_claim": False,
            "customer_portal_claim": False,
            "multi_tenant_reporting_claim": False,
        },
        "case_summary": {
            "total_cases": len(cases),
            "by_lifecycle_state": dict(
                sorted(Counter(case.lifecycle_state for case in cases).items())
            ),
        },
        "authoritative_records": {
            "cases": case_payloads,
        },
        "subordinate_evidence_policy": {
            "authority_role": "subordinate_evidence",
            "promotion_allowed": False,
            "label_required": True,
        },
    }
