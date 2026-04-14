from __future__ import annotations

from typing import Callable, Mapping, Protocol

from .models import AlertRecord, CaseRecord, LeadRecord, ReconciliationRecord


REVIEWED_LIVE_SOURCE_FAMILIES = frozenset({"github_audit", "entra_id"})
REVIEWED_LIVE_SLICE_LABEL = "Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"


class ReviewedSlicePolicyServiceDependencies(Protocol):
    _store: object

    def _require_case_record(self, case_id: str) -> CaseRecord:
        ...

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...

    def _latest_detection_reconciliation_for_alert(
        self,
        alert_id: str,
    ) -> ReconciliationRecord | None:
        ...

    def _reconciliation_is_wazuh_origin(
        self,
        reconciliation: ReconciliationRecord,
    ) -> bool:
        ...

    def _linked_id_exists(self, values: object, expected_id: str) -> bool:
        ...


class ReviewedSlicePolicy:
    """Encapsulates the approved reviewed live-slice access rules."""

    def __init__(
        self,
        service: ReviewedSlicePolicyServiceDependencies,
        *,
        normalize_admission_provenance: Callable[
            [object], dict[str, str] | None
        ],
    ) -> None:
        self._service = service
        self._normalize_admission_provenance = normalize_admission_provenance

    def require_operator_case(self, case_id: str) -> CaseRecord:
        case = self._service._require_case_record(case_id)
        return self.require_operator_case_record(case)

    def require_case_scoped_advisory_read(self, context_snapshot: object) -> None:
        record_family = str(getattr(context_snapshot, "record_family"))
        record_id = str(getattr(context_snapshot, "record_id"))
        error_message = self.case_scoped_read_error(record_family, record_id)

        if record_family == "case":
            self.require_operator_case(record_id)
            return

        linked_case_ids = tuple(getattr(context_snapshot, "linked_case_ids"))
        if not linked_case_ids:
            raise ValueError(error_message)

        approved_cases = {
            case_id: self.require_operator_case(case_id) for case_id in linked_case_ids
        }

        if record_family == "recommendation":
            self.require_case_scoped_recommendation_payload(
                getattr(context_snapshot, "record"),
                approved_cases=approved_cases,
                error_message=error_message,
            )
        elif record_family == "ai_trace":
            subject_linkage = getattr(context_snapshot, "record").get("subject_linkage")
            if self.context_explicitly_declares_provenance(
                subject_linkage
            ) and self.context_declares_out_of_scope_provenance(subject_linkage):
                raise ValueError(error_message)

            linked_recommendation_records = tuple(
                getattr(context_snapshot, "linked_recommendation_records")
            )
            if not linked_recommendation_records:
                raise ValueError(error_message)
            for recommendation in linked_recommendation_records:
                self.require_case_scoped_recommendation_payload(
                    recommendation,
                    approved_cases=approved_cases,
                    error_message=error_message,
                )

    @staticmethod
    def case_scoped_read_error(record_family: str, record_id: str) -> str:
        return (
            f"{record_family} {record_id!r} is outside the approved "
            f"{REVIEWED_LIVE_SLICE_LABEL}"
        )

    def require_case_scoped_recommendation_payload(
        self,
        payload: Mapping[str, object],
        *,
        approved_cases: Mapping[str, CaseRecord],
        error_message: str,
    ) -> None:
        case_id = self._service._normalize_optional_string(payload.get("case_id"), "case_id")
        if case_id is None:
            raise ValueError(error_message)
        approved_case = approved_cases.get(case_id)
        if approved_case is None:
            raise ValueError(error_message)

        alert_id = self._service._normalize_optional_string(payload.get("alert_id"), "alert_id")
        if alert_id is not None and approved_case.alert_id != alert_id:
            raise ValueError(error_message)

        lead_id = self._service._normalize_optional_string(payload.get("lead_id"), "lead_id")
        if lead_id is not None:
            lead = self._service._store.get(LeadRecord, lead_id)
            if lead is None or lead.case_id != case_id:
                raise ValueError(error_message)

        reviewed_context = payload.get("reviewed_context")
        if self.context_explicitly_declares_provenance(
            reviewed_context
        ) and self.context_declares_out_of_scope_provenance(reviewed_context):
            raise ValueError(error_message)

    def require_operator_case_record(self, case: CaseRecord) -> CaseRecord:
        if not self.case_is_in_operator_slice(case):
            raise ValueError(
                f"Case {case.case_id!r} is outside the approved "
                f"{REVIEWED_LIVE_SLICE_LABEL}"
            )
        return case

    def case_is_in_operator_slice(self, case: CaseRecord) -> bool:
        alert_id = self._service._normalize_optional_string(case.alert_id, "case.alert_id")
        if alert_id is None:
            return False

        alert = self._service._store.get(AlertRecord, alert_id)
        if alert is None:
            return False
        if alert.case_id != case.case_id:
            return False

        reconciliation = self._service._latest_detection_reconciliation_for_alert(
            alert.alert_id
        )
        if reconciliation is None or not self._service._reconciliation_is_wazuh_origin(
            reconciliation
        ):
            return False
        if not self._service._linked_id_exists(
            reconciliation.subject_linkage.get("alert_ids"),
            alert.alert_id,
        ):
            return False
        if not self._service._linked_id_exists(
            reconciliation.subject_linkage.get("case_ids"),
            case.case_id,
        ):
            return False

        admission_provenance = (
            self._normalize_admission_provenance(
                reconciliation.subject_linkage.get("admission_provenance")
            )
            or self._normalize_admission_provenance(case.reviewed_context.get("provenance"))
            or self._normalize_admission_provenance(alert.reviewed_context.get("provenance"))
        )
        if admission_provenance != {
            "admission_kind": "live",
            "admission_channel": "live_wazuh_webhook",
        }:
            return False

        return (
            self.source_family(case.reviewed_context)
            or self.source_family(alert.reviewed_context)
            or self.source_family(reconciliation.subject_linkage.get("reviewed_source_profile"))
        ) in REVIEWED_LIVE_SOURCE_FAMILIES

    @staticmethod
    def source_family(context: object) -> str | None:
        if not isinstance(context, Mapping):
            return None

        source_context = context.get("source")
        if isinstance(source_context, Mapping):
            source_family = source_context.get("source_family")
            if isinstance(source_family, str):
                normalized_source_family = source_family.strip()
                if normalized_source_family:
                    return normalized_source_family

        source_family = context.get("source_family")
        if isinstance(source_family, str):
            normalized_source_family = source_family.strip()
            if normalized_source_family:
                return normalized_source_family

        return None

    def context_declares_out_of_scope_provenance(self, context: object) -> bool:
        if not isinstance(context, Mapping):
            return True

        source_family = self.source_family(context) or self.source_family(
            context.get("reviewed_source_profile")
        )
        if source_family not in REVIEWED_LIVE_SOURCE_FAMILIES:
            return True

        admission_provenance = self._normalize_admission_provenance(
            context.get("provenance")
        ) or self._normalize_admission_provenance(context.get("admission_provenance"))
        return (
            admission_provenance is not None
            and admission_provenance
            != {
                "admission_kind": "live",
                "admission_channel": "live_wazuh_webhook",
            }
        )

    @staticmethod
    def context_explicitly_declares_provenance(context: object) -> bool:
        if not isinstance(context, Mapping):
            return context is not None
        if "source_family" in context or "source" in context:
            return True
        if "reviewed_source_profile" in context:
            return True
        return "provenance" in context or "admission_provenance" in context
