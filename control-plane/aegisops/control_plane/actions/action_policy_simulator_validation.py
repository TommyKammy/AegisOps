from __future__ import annotations

from typing import Mapping

from .action_policy_authority_scanning import (
    _NEGATION_SCAN_WINDOW,
    _SIMULATOR_EXCLUSION_CONTEXT_TERMS,
    _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS,
    _SIMULATOR_PRODUCTION_TRUTH_TERMS,
    _has_recent_negation,
    _required_exclusion_groups_are_conjunctive,
    contains_simulator_production_truth_overclaim,
    contains_unnegated_term_group,
    text_terms,
)
from .action_policy_catalog import (
    PHASE62_SIMULATOR_CONTRACTS,
    _SIMULATOR_ALLOWED_DATA_CLASSIFICATIONS,
)
from .action_policy_types import SimulatorValidationErrors


def _non_blank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_phase62_simulator_output(
    *,
    catalog_action: str,
    output: Mapping[str, object],
) -> SimulatorValidationErrors:
    """Return fail-closed Phase 62.6 errors for demo/test simulator output."""
    contract = PHASE62_SIMULATOR_CONTRACTS.get(catalog_action)
    if contract is None:
        return ("unsupported_action",)

    errors: list[str] = []
    for field in contract.required_output_fields:
        if not _non_blank_string(output.get(field)):
            errors.append(f"missing_{field}")

    mode = output.get("mode")
    if _non_blank_string(mode):
        if mode not in contract.allowed_modes:
            errors.append("unsupported_mode")

    output_catalog_action = output.get("catalog_action")
    if _non_blank_string(output_catalog_action):
        if output_catalog_action != contract.catalog_action:
            errors.append("catalog_action_mismatch")

    reviewed_template_version = output.get("reviewed_template_version")
    if _non_blank_string(reviewed_template_version):
        if reviewed_template_version != contract.reviewed_template_version:
            errors.append("reviewed_template_version_mismatch")

    simulated_status = output.get("simulated_status")
    if _non_blank_string(simulated_status):
        if simulated_status not in contract.allowed_statuses:
            errors.append("unsupported_simulated_status")
        if contains_unnegated_term_group(
            text_terms(str(simulated_status)),
            _SIMULATOR_PRODUCTION_TRUTH_TERMS,
        ):
            errors.append("simulated_status_promotes_production_truth")

    demo_test_label = output.get("demo_test_label")
    if _non_blank_string(demo_test_label):
        label_terms = text_terms(str(demo_test_label))
        if not (
            {"demo", "test"} & set(label_terms)
            and "evidence" in label_terms
            and any(
                term in {"only", "non", "non_authoritative"} for term in label_terms
            )
        ):
            errors.append("missing_demo_test_label")
        if contains_simulator_production_truth_overclaim(label_terms):
            errors.append("demo_test_label_promotes_production_truth")

    production_exclusion = output.get("production_exclusion")
    if _non_blank_string(production_exclusion):
        exclusion_terms = text_terms(str(production_exclusion))
        has_unnegated_exclusion_term = any(
            term in _SIMULATOR_EXCLUSION_CONTEXT_TERMS
            and not _has_recent_negation(
                exclusion_terms,
                index,
                window=_NEGATION_SCAN_WINDOW,
            )
            for index, term in enumerate(exclusion_terms)
        )
        has_production_exclusion_context = (
            has_unnegated_exclusion_term
            and "production" in exclusion_terms
            and all(
                contains_unnegated_term_group(exclusion_terms, (term_group,))
                for term_group in _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS
            )
            and _required_exclusion_groups_are_conjunctive(exclusion_terms)
        )
        if not has_production_exclusion_context:
            errors.append("missing_production_exclusion")
        if contains_simulator_production_truth_overclaim(exclusion_terms):
            errors.append("production_exclusion_promotes_production_truth")

    authority_posture = output.get("authority_posture")
    if _non_blank_string(authority_posture):
        if authority_posture != contract.authority_posture:
            errors.append("authority_posture_mismatch")

    live_secret_ref = output.get("live_secret_ref")
    if _non_blank_string(live_secret_ref) and live_secret_ref != "not_used":
        errors.append("live_secret_ref_forbidden")

    customer_data_classification = output.get("customer_data_classification")
    if _non_blank_string(customer_data_classification):
        if (
            customer_data_classification
            not in _SIMULATOR_ALLOWED_DATA_CLASSIFICATIONS
        ):
            errors.append("customer_data_forbidden")

    return tuple(dict.fromkeys(errors))


def require_phase62_simulator_output(
    *,
    catalog_action: str,
    output: Mapping[str, object],
) -> None:
    errors = validate_phase62_simulator_output(
        catalog_action=catalog_action,
        output=output,
    )
    if errors:
        raise ValueError(
            "simulator output violates Phase 62.6 contract: " + ", ".join(errors)
        )
