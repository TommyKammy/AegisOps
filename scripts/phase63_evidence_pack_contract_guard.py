from __future__ import annotations

import ast
from dataclasses import dataclass, replace
import pathlib
import re
import sys
from types import MappingProxyType
from typing import Mapping


_LABEL_KEYS = (
    "consumer",
    "status",
    "freshness_state",
    "custody_state",
    "confidence_state",
    "provenance_state",
    "conflict_state",
    "source_state",
    "uncertainty_label",
)
_SHARED_LABEL_KEYS = tuple(key for key in _LABEL_KEYS if key != "consumer")
_AUTHORITY_TRUTH_DENIALS = frozenset(
    {
        "evidence_truth_creation",
        "source_truth_creation",
        "readiness_truth",
        "release_truth",
        "workflow_truth",
    }
)
_AI_GROUNDING_SINGLETON_LABEL_FIELDS = MappingProxyType(
    {
        "consumer": "consumer",
        "custody_state": "custody_state",
        "provenance_state": "provenance_state",
        "confidence_state": "confidence_state",
    }
)
_AI_GROUNDING_ALLOWED_LABEL_FIELDS = MappingProxyType(
    {
        "status": ("status", "_ALLOWED_STATUS"),
        "freshness_state": ("freshness_state", "_ALLOWED_FRESHNESS"),
        "conflict_state": ("conflict_state", "_ALLOWED_CONFLICT"),
        "source_state": ("source_state", "_ALLOWED_SOURCE_STATE"),
        "uncertainty_label": ("uncertainty_label", "_ALLOWED_UNCERTAINTY"),
    }
)
_BACKEND_NO_WORKFLOW_AUTHORITY_TARGETS = (
    ("subscript", "typed_values", "workflow_authority"),
    ("optional", "confidence", "source_native_score_authority"),
)
_BACKEND_SUBORDINATE_AUTHORITY_POSTURE_TARGETS = (
    ("subscript", "typed_values", "authority_posture"),
    ("optional", "provenance", "authority_posture"),
)
_AI_SUBORDINATE_AUTHORITY_POSTURE_TARGETS = (
    ("get", "projection", "authority_posture"),
    ("get", "provenance", "authority_posture"),
)
_STATE_REASON_CONSISTENCY_RULES = frozenset(
    {
        "available_status_has_no_reasons",
        "degraded_status_has_degraded_reasons_only",
        "unavailable_status_has_unavailable_reasons",
        "freshness_state_matches_stale_reputation",
        "conflict_state_matches_conflicting_enrichment",
        "source_state_matches_availability_reasons",
        "uncertainty_label_matches_state",
        "confidence_freshness_matches_freshness_state",
        "confidence_ambiguity_badge_matches_conflict",
    }
)


@dataclass(frozen=True)
class Phase63EvidencePackContract:
    labels: Mapping[str, frozenset[str]]
    degraded_reasons: frozenset[str]
    unavailable_reasons: frozenset[str]
    required_custody_fields: frozenset[str]
    required_provenance_fields: frozenset[str]
    required_confidence_fields: frozenset[str]
    contract_fields: frozenset[str]
    recognized_fields: frozenset[str]
    supported_source_ids: frozenset[str]
    subordinate_authority_posture: str
    no_workflow_authority: str
    authoritative_workflow_truth: bool
    operator_visible_truth: bool
    confidence_posture: str
    freshness_window_milliseconds: int
    state_reason_consistency_rules: frozenset[str]
    forbidden_projection_sources: frozenset[str]
    forbidden_readiness_claim_fields: frozenset[str]
    authority_truth_denials: frozenset[str]


def assert_phase63_evidence_pack_contract_aligned(
    repo_root: pathlib.Path | str | None = None,
    *,
    backend_contract: Phase63EvidencePackContract | None = None,
    operator_ui_contract: Phase63EvidencePackContract | None = None,
    ai_grounding_contract: Phase63EvidencePackContract | None = None,
) -> None:
    root = pathlib.Path(repo_root) if repo_root is not None else _default_repo_root()
    backend = backend_contract or _backend_contract(root)
    ui = operator_ui_contract or _operator_ui_contract(root)
    ai = ai_grounding_contract or _ai_grounding_contract(root)

    _assert_equal(
        "case-workbench consumer labels",
        backend.labels["consumer"],
        frozenset({"case_workbench"}),
    )
    _assert_equal(
        "operator-ui consumer labels",
        ui.labels["consumer"],
        backend.labels["consumer"],
    )
    _assert_equal(
        "AI grounding consumer labels",
        ai.labels["consumer"],
        frozenset({"ai_grounding"}),
    )
    for label_key in _SHARED_LABEL_KEYS:
        _assert_equal(
            f"{label_key} labels",
            backend.labels[label_key],
            ui.labels[label_key],
            ai.labels[label_key],
        )

    _assert_equal(
        "degraded reasons",
        backend.degraded_reasons,
        ui.degraded_reasons,
        ai.degraded_reasons,
    )
    _assert_equal(
        "unavailable reasons",
        backend.unavailable_reasons,
        ui.unavailable_reasons,
        ai.unavailable_reasons,
    )
    _assert_equal(
        "custody fields",
        backend.required_custody_fields,
        ui.required_custody_fields,
        ai.required_custody_fields,
    )
    _assert_equal(
        "provenance fields",
        backend.required_provenance_fields,
        ui.required_provenance_fields,
        ai.required_provenance_fields,
    )
    _assert_equal(
        "confidence fields",
        backend.required_confidence_fields,
        ui.required_confidence_fields,
        ai.required_confidence_fields,
    )
    _assert_equal("contract fields", backend.contract_fields, ui.contract_fields)
    _assert_equal("recognized fields", backend.recognized_fields, ui.recognized_fields)
    _assert_equal(
        "operator-visible truth boundary",
        backend.operator_visible_truth,
        ui.operator_visible_truth,
        True,
    )
    _assert_equal(
        "source IDs",
        backend.supported_source_ids,
        ui.supported_source_ids,
        ai.supported_source_ids,
    )
    _assert_equal(
        "freshness window",
        backend.freshness_window_milliseconds,
        ui.freshness_window_milliseconds,
        ai.freshness_window_milliseconds,
    )
    _assert_equal(
        "state/reason consistency rules",
        backend.state_reason_consistency_rules,
        ui.state_reason_consistency_rules,
        ai.state_reason_consistency_rules,
        _STATE_REASON_CONSISTENCY_RULES,
    )
    _assert_equal(
        "subordinate authority posture",
        backend.subordinate_authority_posture,
        ui.subordinate_authority_posture,
        ai.subordinate_authority_posture,
    )
    _assert_equal(
        "no workflow authority",
        backend.no_workflow_authority,
        ui.no_workflow_authority,
        ai.no_workflow_authority,
    )
    _assert_equal(
        "authoritative workflow truth denial",
        backend.authoritative_workflow_truth,
        ui.authoritative_workflow_truth,
        ai.authoritative_workflow_truth,
    )
    _assert_equal(
        "confidence posture",
        backend.confidence_posture,
        ui.confidence_posture,
        ai.confidence_posture,
    )
    _assert_equal(
        "forbidden projection sources",
        backend.forbidden_projection_sources,
        ui.forbidden_projection_sources,
    )
    _assert_equal(
        "readiness claim fields",
        backend.forbidden_readiness_claim_fields,
        ui.forbidden_readiness_claim_fields,
    )
    _assert_equal(
        "AI authority truth denial posture",
        _AUTHORITY_TRUTH_DENIALS,
        ai.authority_truth_denials & _AUTHORITY_TRUTH_DENIALS,
    )


def load_phase63_evidence_pack_contracts(
    repo_root: pathlib.Path | str | None = None,
) -> tuple[
    Phase63EvidencePackContract,
    Phase63EvidencePackContract,
    Phase63EvidencePackContract,
]:
    root = pathlib.Path(repo_root) if repo_root is not None else _default_repo_root()
    return (
        _backend_contract(root),
        _operator_ui_contract(root),
        _ai_grounding_contract(root),
    )


def _default_repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def _ensure_control_plane_path(repo_root: pathlib.Path) -> None:
    control_plane_root = repo_root / "control-plane"
    if str(control_plane_root) not in sys.path:
        sys.path.insert(0, str(control_plane_root))


def _backend_contract(repo_root: pathlib.Path) -> Phase63EvidencePackContract:
    _ensure_control_plane_path(repo_root)
    from aegisops.control_plane.evidence import (  # noqa: WPS433
        evidence_freshness_provenance_projection as source_projection,
    )
    from aegisops.control_plane.evidence.evidence_source_registry import (  # noqa: WPS433
        PHASE63_EVIDENCE_SOURCE_REGISTRY,
    )
    from aegisops.control_plane.inspection import (  # noqa: WPS433
        evidence_pack_projection as inspection_projection,
    )

    source_id = inspection_projection._EVIDENCE_PACK_SUPPORTED_SOURCE_ID
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id]
    validator_source = (
        repo_root
        / "control-plane"
        / "aegisops"
        / "control_plane"
        / "inspection"
        / "evidence_pack_projection.py"
    ).read_text(encoding="utf-8")
    labels = _py_backend_enforced_label_sets(validator_source, inspection_projection)
    reason_sets = _py_backend_enforced_reason_sets(
        validator_source,
        inspection_projection,
    )
    metadata_fields = _py_backend_enforced_metadata_fields(
        validator_source,
        inspection_projection,
    )
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=reason_sets["degraded_reasons"],
        unavailable_reasons=reason_sets["unavailable_reasons"],
        required_custody_fields=metadata_fields["custody"],
        required_provenance_fields=metadata_fields["provenance"],
        required_confidence_fields=metadata_fields["confidence"],
        contract_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS
        ),
        recognized_fields=_py_backend_recognized_fields_rejection(
            validator_source,
            inspection_projection,
        ),
        supported_source_ids=_py_rejected_string_values(
            validator_source,
            ("subscript", "values", "source_id"),
        ),
        subordinate_authority_posture=_backend_subordinate_authority_posture_rejection(
            validator_source
        ),
        no_workflow_authority=_backend_no_workflow_authority_rejection(
            validator_source
        ),
        authoritative_workflow_truth=_py_rejected_boolean_value(
            validator_source,
            ("get", "projection", "authoritative_workflow_truth"),
        ),
        operator_visible_truth=_py_rejected_optional_boolean_value(
            validator_source,
            ("get", "projection", "operator_visible"),
        ),
        confidence_posture=_backend_confidence_posture_rejection(
            validator_source,
            registry_entry.confidence_posture,
        ),
        freshness_window_milliseconds=(
            source_projection._parse_duration_seconds(registry_entry.freshness_window)
            * 1000
        ),
        state_reason_consistency_rules=_py_backend_state_reason_consistency_rules(
            validator_source
        ),
        forbidden_projection_sources=_py_backend_forbidden_projection_sources_rejection(
            validator_source,
            inspection_projection,
        ),
        forbidden_readiness_claim_fields=_py_backend_forbidden_readiness_claim_rejection(
            validator_source,
            inspection_projection,
        ),
        authority_truth_denials=frozenset(),
    )


def _ai_grounding_contract(repo_root: pathlib.Path) -> Phase63EvidencePackContract:
    _ensure_control_plane_path(repo_root)
    from aegisops.control_plane.assistant import ai_grounding_validation  # noqa: WPS433
    from aegisops.control_plane.evidence import (  # noqa: WPS433
        evidence_freshness_provenance_projection as source_projection,
    )
    from aegisops.control_plane.evidence.evidence_source_registry import (  # noqa: WPS433
        PHASE63_EVIDENCE_SOURCE_REGISTRY,
    )

    source_ids = frozenset(ai_grounding_validation._SUPPORTED_GROUNDING_SOURCE_IDS)
    if len(source_ids) != 1:
        raise AssertionError("AI grounding source IDs must stay explicit")
    source_id = next(iter(source_ids))
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[source_id]
    validator_source = (
        repo_root
        / "control-plane"
        / "aegisops"
        / "control_plane"
        / "assistant"
        / "ai_grounding_validation.py"
    ).read_text(encoding="utf-8")
    singleton_labels = _py_projection_get_string_rejection_labels(
        validator_source,
        _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
    )
    membership_labels = _py_projection_get_membership_labels(
        validator_source,
        _AI_GROUNDING_ALLOWED_LABEL_FIELDS,
        ai_grounding_validation,
    )
    metadata_fields = _py_enforced_metadata_fields(
        validator_source,
        ai_grounding_validation,
    )
    reason_sets = _py_ai_enforced_reason_sets(
        validator_source,
        ai_grounding_validation,
    )
    labels = {
        "consumer": singleton_labels["consumer"],
        "status": membership_labels["status"],
        "freshness_state": membership_labels["freshness_state"],
        "custody_state": singleton_labels["custody_state"],
        "confidence_state": singleton_labels["confidence_state"],
        "provenance_state": singleton_labels["provenance_state"],
        "conflict_state": membership_labels["conflict_state"],
        "source_state": membership_labels["source_state"],
        "uncertainty_label": membership_labels["uncertainty_label"],
    }
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=reason_sets["degraded_reasons"],
        unavailable_reasons=reason_sets["unavailable_reasons"],
        required_custody_fields=metadata_fields["custody"],
        required_provenance_fields=metadata_fields["provenance"],
        required_confidence_fields=metadata_fields["confidence"],
        contract_fields=frozenset(),
        recognized_fields=frozenset(),
        supported_source_ids=source_ids,
        subordinate_authority_posture=_ai_subordinate_authority_posture_rejection(
            validator_source
        ),
        no_workflow_authority=_ai_no_workflow_authority_rejection(
            validator_source
        ),
        authoritative_workflow_truth=_py_rejected_boolean_value(
            validator_source,
            ("get", "projection", "authoritative_workflow_truth"),
        ),
        operator_visible_truth=True,
        confidence_posture=_ai_confidence_posture_rejection(
            validator_source,
            registry_entry.confidence_posture,
        ),
        freshness_window_milliseconds=(
            source_projection._parse_duration_seconds(registry_entry.freshness_window)
            * 1000
        ),
        state_reason_consistency_rules=_py_ai_state_reason_consistency_rules(
            validator_source
        ),
        forbidden_projection_sources=frozenset(),
        forbidden_readiness_claim_fields=frozenset(),
        authority_truth_denials=frozenset(
            authority
            for authority in _AUTHORITY_TRUTH_DENIALS
            if ai_grounding_validation._scan_for_authority_claim(authority)
        ),
    )


def _operator_ui_contract(repo_root: pathlib.Path) -> Phase63EvidencePackContract:
    source = (
        repo_root
        / "apps"
        / "operator-ui"
        / "src"
        / "operatorDataProvider"
        / "linkedEvidencePackValidator.ts"
    ).read_text(encoding="utf-8")
    return _operator_ui_contract_from_source(source)


def _operator_ui_contract_from_source(source: str) -> Phase63EvidencePackContract:
    labels = _ts_allowed_labels(source)
    metadata_fields = _ts_enforced_metadata_fields(source)
    reason_sets = _ts_enforced_reason_sets(source)
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=reason_sets["degraded_reasons"],
        unavailable_reasons=reason_sets["unavailable_reasons"],
        required_custody_fields=metadata_fields["custody"],
        required_provenance_fields=metadata_fields["provenance"],
        required_confidence_fields=metadata_fields["confidence"],
        contract_fields=_ts_set(source, "EVIDENCE_PACK_CONTRACT_FIELDS"),
        recognized_fields=_ts_recognized_fields_rejection(
            source,
        ),
        supported_source_ids=frozenset(
            {_ts_rejected_pack_string_field(source, "source_id")}
        ),
        subordinate_authority_posture=_ts_subordinate_authority_posture_rejection(source),
        no_workflow_authority=_ts_no_workflow_authority_rejection(source),
        authoritative_workflow_truth=_ts_rejected_pack_boolean_field(
            source,
            "authoritative_workflow_truth",
        ),
        operator_visible_truth=_ts_rejected_optional_pack_boolean_field(
            source,
            "operator_visible",
        ),
        confidence_posture=_ts_rejected_mapping_string_field(
            source,
            "confidence",
            "posture",
        ),
        freshness_window_milliseconds=_ts_enforced_freshness_window_milliseconds(
            source
        ),
        state_reason_consistency_rules=_ts_state_reason_consistency_rules(source),
        forbidden_projection_sources=_ts_forbidden_projection_sources_rejection(source),
        forbidden_readiness_claim_fields=_ts_forbidden_defined_pack_fields(
            source,
            "cannot claim release readiness",
        ),
        authority_truth_denials=frozenset(),
    )


def _ts_allowed_labels(source: str) -> dict[str, frozenset[str]]:
    match = re.search(
        r"const EVIDENCE_PACK_ALLOWED_LABELS = \{(?P<body>.*?)\n\};",
        source,
        re.S,
    )
    if match is None:
        raise AssertionError("operator UI evidence-pack labels are not discoverable")
    body = match.group("body")
    labels = {
        key: frozenset(_string_literals(value_source))
        for key, value_source in re.findall(
            r"(\w+):\s*new Set\(\[(.*?)\]\),",
            body,
            re.S,
        )
    }
    enforced_labels = _ts_enforced_label_keys(source)
    if frozenset(labels) != enforced_labels:
        raise AssertionError("operator UI evidence-pack label enforcement drift")
    return labels


def _ts_enforced_label_keys(source: str) -> frozenset[str]:
    labels = frozenset(
        re.findall(r'\bvalidateEvidencePackLabel\(\s*"([^"]+)"\s*,', source)
    )
    if not labels:
        raise AssertionError(
            "operator UI evidence-pack label enforcement is not discoverable"
        )
    return labels


def _ts_enforced_reason_sets(source: str) -> dict[str, frozenset[str]]:
    reason_sets = {
        field_name: _ts_set(source, constant_name)
        for field_name, constant_name in _ts_validator_call_constants(
            source,
            "validateEvidencePackReasons",
            "pack",
        ).items()
    }
    expected_fields = frozenset({"degraded_reasons", "unavailable_reasons"})
    if frozenset(reason_sets) != expected_fields:
        raise AssertionError("operator UI evidence-pack reason enforcement drift")
    return reason_sets


def _ts_enforced_metadata_fields(source: str) -> dict[str, frozenset[str]]:
    metadata_fields = {
        field_name: _ts_set(source, constant_name)
        for field_name, constant_name in _ts_validator_call_constants(
            source,
            "validateEvidencePackMetadataMap",
            None,
        ).items()
    }
    expected_fields = frozenset({"custody", "provenance", "confidence"})
    if frozenset(metadata_fields) != expected_fields:
        raise AssertionError("operator UI evidence-pack metadata enforcement drift")
    return metadata_fields


def _ts_validator_call_constants(
    source: str,
    function_name: str,
    object_name: str | None,
) -> dict[str, str]:
    constants: dict[str, str] = {}
    for match in re.finditer(rf"\b{re.escape(function_name)}\s*\(", source):
        arguments = _split_ts_arguments(
            _extract_parenthesized(source, match.end() - 1)
        )
        if len(arguments) < 2:
            continue
        value_argument = arguments[0].strip()
        constant_argument = arguments[1].strip()
        if not re.fullmatch(r"EVIDENCE_PACK_[A-Z0-9_]+", constant_argument):
            continue
        if object_name is None:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value_argument):
                constants[value_argument] = constant_argument
            continue
        field_match = re.fullmatch(
            rf"{re.escape(object_name)}\.([A-Za-z0-9_]+)",
            value_argument,
        )
        if field_match is not None:
            constants[field_match.group(1)] = constant_argument
    return constants


def _split_ts_arguments(arguments_source: str) -> tuple[str, ...]:
    arguments: list[str] = []
    depth = 0
    string_quote: str | None = None
    escaped = False
    argument_start = 0
    for index, character in enumerate(arguments_source):
        if string_quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == string_quote:
                string_quote = None
            continue
        if character in {'"', "'", "`"}:
            string_quote = character
            continue
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth -= 1
        elif character == "," and depth == 0:
            arguments.append(arguments_source[argument_start:index])
            argument_start = index + 1
    arguments.append(arguments_source[argument_start:])
    return tuple(arguments)


def _backend_no_workflow_authority_rejection(source: str) -> str:
    values = frozenset(
        value
        for target in _BACKEND_NO_WORKFLOW_AUTHORITY_TARGETS
        for value in _py_rejected_string_values(source, target)
    )
    if len(values) != 1:
        raise AssertionError(
            "backend workflow authority rejection is not consistently discoverable"
        )
    return next(iter(values))


def _backend_subordinate_authority_posture_rejection(source: str) -> str:
    values: set[str] = set()
    try:
        for target in _BACKEND_SUBORDINATE_AUTHORITY_POSTURE_TARGETS:
            values.update(_py_rejected_string_values(source, target))
    except AssertionError as exc:
        raise AssertionError(
            "backend authority posture rejection is not consistently discoverable"
        ) from exc
    if len(values) != 1:
        raise AssertionError(
            "backend authority posture rejection is not consistently discoverable"
        )
    return next(iter(values))


def _ai_no_workflow_authority_rejection(source: str) -> str:
    targets = (
        ("get", "projection", "workflow_authority"),
        ("get", "confidence", "source_native_score_authority"),
    )
    values = frozenset(
        value
        for target in targets
        for value in _py_rejected_string_values(source, target)
    )
    if len(values) != 1:
        raise AssertionError(
            "AI workflow authority rejection is not consistently discoverable"
        )
    return next(iter(values))


def _ai_subordinate_authority_posture_rejection(source: str) -> str:
    values: set[str] = set()
    try:
        for target in _AI_SUBORDINATE_AUTHORITY_POSTURE_TARGETS:
            values.update(_py_rejected_string_values(source, target))
    except AssertionError as exc:
        raise AssertionError(
            "AI authority posture rejection is not consistently discoverable"
        ) from exc
    if len(values) != 1:
        raise AssertionError(
            "AI authority posture rejection is not consistently discoverable"
        )
    return next(iter(values))


def _backend_confidence_posture_rejection(
    source: str,
    registry_confidence_posture: str,
) -> str:
    values: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.NotEq):
            continue
        if len(node.comparators) != 1:
            continue
        if _py_rejection_target(node.left) != ("optional", "confidence", "posture"):
            continue
        compared_value = _py_string_constant(node.comparators[0])
        if compared_value is None and _py_registry_confidence_posture_reference(
            node.comparators[0]
        ):
            compared_value = registry_confidence_posture
        if compared_value is not None:
            values.add(compared_value)
    if len(values) != 1:
        raise AssertionError(
            "backend confidence posture rejection is not consistently discoverable"
        )
    return next(iter(values))


def _ai_confidence_posture_rejection(
    source: str,
    registry_confidence_posture: str,
) -> str:
    values: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.If):
            continue
        compared_value = _py_compare_rejection_value(
            node.test,
            ("get", "confidence", "posture"),
            registry_confidence_posture=registry_confidence_posture,
        )
        if compared_value is None:
            continue
        if not _py_body_contains_string(
            node.body,
            "grounding_confidence_posture_mismatch",
        ):
            continue
        values.add(compared_value)
    if len(values) != 1:
        raise AssertionError(
            "AI confidence posture rejection is not consistently discoverable"
        )
    return next(iter(values))


def _py_compare_rejection_value(
    node: ast.AST,
    target: tuple[str, str, str],
    *,
    registry_confidence_posture: str | None = None,
) -> str | None:
    if not isinstance(node, ast.Compare):
        return None
    if len(node.ops) != 1 or not isinstance(node.ops[0], ast.NotEq):
        return None
    if len(node.comparators) != 1:
        return None
    if _py_rejection_target(node.left) != target:
        return None
    compared_value = _py_string_constant(node.comparators[0])
    if (
        compared_value is None
        and registry_confidence_posture is not None
        and _py_registry_confidence_posture_reference(node.comparators[0])
    ):
        compared_value = registry_confidence_posture
    return compared_value


def _py_body_contains_string(body: list[ast.stmt], value: str) -> bool:
    return any(
        isinstance(child, ast.Constant) and child.value == value
        for statement in body
        for child in ast.walk(statement)
    )


def _py_registry_confidence_posture_reference(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "confidence_posture"
        and isinstance(node.value, ast.Name)
        and node.value.id == "registry_entry"
    )


def _py_projection_get_string_rejection_labels(
    source: str,
    label_fields: Mapping[str, str],
) -> dict[str, frozenset[str]]:
    labels: dict[str, frozenset[str]] = {}
    for label_key, field_name in label_fields.items():
        values = _py_rejected_string_values(source, ("get", "projection", field_name))
        if len(values) != 1:
            raise AssertionError(
                f"Python projection label {field_name} rejection is not singleton"
            )
        labels[label_key] = values
    return labels


def _py_projection_get_membership_labels(
    source: str,
    label_fields: Mapping[str, tuple[str, str]],
    namespace: object,
) -> dict[str, frozenset[str]]:
    labels: dict[str, frozenset[str]] = {}
    for label_key, (field_name, constant_name) in label_fields.items():
        values = _py_rejected_membership_values(
            source,
            ("get", "projection", field_name),
            constant_name,
            namespace,
        )
        if not values:
            raise AssertionError(
                f"Python projection label {field_name} membership check is not discoverable"
            )
        labels[label_key] = values
    return labels


def _py_enforced_metadata_fields(
    source: str,
    namespace: object,
) -> dict[str, frozenset[str]]:
    required_fields: dict[str, frozenset[str]] = {}
    allowed_fields: dict[str, frozenset[str]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id == "_mapping_has_non_empty_fields" and len(node.args) >= 2:
            value_argument = node.args[0]
            required_argument = node.args[1]
            if (
                isinstance(value_argument, ast.Name)
                and value_argument.id in {"custody", "provenance", "confidence"}
                and isinstance(required_argument, ast.Name)
            ):
                required_fields[value_argument.id] = frozenset(
                    getattr(namespace, required_argument.id)
                )
        if node.func.id == "_metadata_contract_reasons" and len(node.args) >= 2:
            value_argument = node.args[0]
            allowed_argument = node.args[1]
            if (
                isinstance(value_argument, ast.Name)
                and value_argument.id in {"custody", "provenance", "confidence"}
                and isinstance(allowed_argument, ast.Name)
            ):
                allowed_fields[value_argument.id] = frozenset(
                    getattr(namespace, allowed_argument.id)
                )
    expected_fields = frozenset({"custody", "provenance", "confidence"})
    if (
        frozenset(required_fields) != expected_fields
        or frozenset(allowed_fields) != expected_fields
        or required_fields != allowed_fields
    ):
        raise AssertionError("AI grounding metadata enforcement drift")
    return required_fields


def _py_backend_enforced_label_sets(
    source: str,
    namespace: object,
) -> dict[str, frozenset[str]]:
    body = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        body,
        (
            "for field_name, allowed_values in "
            "_EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS.items():",
            "values[field_name] not in allowed_values",
        ),
        "backend evidence-pack label enforcement",
    )
    labels = getattr(namespace, "_EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS")
    if frozenset(labels) != frozenset(_LABEL_KEYS):
        raise AssertionError("backend evidence-pack label enforcement drift")
    return {key: frozenset(labels[key]) for key in _LABEL_KEYS}


def _py_backend_enforced_reason_sets(
    source: str,
    namespace: object,
) -> dict[str, frozenset[str]]:
    body = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        body,
        (
            "reason not in _EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS",
            "for reason in degraded_reasons",
            "reason not in _EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS",
            "for reason in unavailable_reasons",
        ),
        "backend evidence-pack reason enforcement",
    )
    return {
        "degraded_reasons": frozenset(
            getattr(namespace, "_EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS")
        ),
        "unavailable_reasons": frozenset(
            getattr(namespace, "_EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS")
        ),
    }


def _py_backend_enforced_metadata_fields(
    source: str,
    namespace: object,
) -> dict[str, frozenset[str]]:
    metadata_fields: dict[str, frozenset[str]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "_required_metadata_map_fields" or len(node.args) < 2:
            continue
        value_argument = node.args[0]
        required_argument = node.args[1]
        if (
            isinstance(value_argument, ast.Name)
            and value_argument.id in {"custody", "provenance", "confidence"}
            and isinstance(required_argument, ast.Name)
        ):
            metadata_fields[value_argument.id] = frozenset(
                getattr(namespace, required_argument.id)
            )
    expected_fields = frozenset({"custody", "provenance", "confidence"})
    if frozenset(metadata_fields) != expected_fields:
        raise AssertionError("backend evidence-pack metadata enforcement drift")
    return metadata_fields


def _py_backend_recognized_fields_rejection(
    source: str,
    namespace: object,
) -> frozenset[str]:
    body = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        body,
        (
            "missing_fields = _EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS - frozenset(projection)",
            "if missing_fields:",
            "unexpected_fields =",
            "frozenset(projection) - _EVIDENCE_PACK_PROJECTION_RECOGNIZED_FIELDS",
            "if unexpected_fields:",
        ),
        "backend recognized-field rejection",
    )
    return frozenset(getattr(namespace, "_EVIDENCE_PACK_PROJECTION_RECOGNIZED_FIELDS"))


def _py_backend_forbidden_projection_sources_rejection(
    source: str,
    namespace: object,
) -> frozenset[str]:
    body = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        body,
        (
            "projection_source in _EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES",
            'raise ValueError("linked evidence-pack projection cannot be cache sourced")',
        ),
        "backend forbidden projection-source enforcement",
    )
    return frozenset(getattr(namespace, "_EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES"))


def _py_backend_forbidden_readiness_claim_rejection(
    source: str,
    namespace: object,
) -> frozenset[str]:
    body = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        body,
        (
            "claim_name in projection",
            "for claim_name in _EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS",
            'raise ValueError("linked evidence-pack projection cannot claim release readiness")',
        ),
        "backend readiness-claim rejection",
    )
    return frozenset(getattr(namespace, "_EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS"))


def _py_ai_enforced_reason_sets(
    source: str,
    namespace: object,
) -> dict[str, frozenset[str]]:
    grounding_body = _py_function_source(source, "_grounding_source_reasons")
    unsupported_body = _py_function_source(source, "_unsupported_projection_reason_reasons")
    _require_substrings(
        grounding_body,
        ("reasons.extend(_unsupported_projection_reason_reasons(projection))",),
        "AI reason vocabulary enforcement call",
    )
    _require_substrings(
        unsupported_body,
        (
            "reason not in _ALLOWED_DEGRADED_REASONS",
            "for reason in degraded_reasons",
            "reason not in _ALLOWED_UNAVAILABLE_REASONS",
            "for reason in unavailable_reasons",
        ),
        "AI reason vocabulary enforcement",
    )
    return {
        "degraded_reasons": frozenset(getattr(namespace, "_ALLOWED_DEGRADED_REASONS")),
        "unavailable_reasons": frozenset(
            getattr(namespace, "_ALLOWED_UNAVAILABLE_REASONS")
        ),
    }


def _py_rejected_string_values(
    source: str,
    target: tuple[str, str, str],
) -> frozenset[str]:
    string_constants = _py_source_string_constants(source)
    values: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.NotEq):
            continue
        if len(node.comparators) != 1:
            continue
        compared_value = _py_string_constant(node.comparators[0], string_constants)
        if compared_value is None:
            continue
        if _py_rejection_target(node.left) == target:
            values.add(compared_value)
    if not values:
        _, mapping_name, field_name = target
        raise AssertionError(
            f"Python string rejection for {mapping_name}.{field_name} is not discoverable"
        )
    return frozenset(values)


def _py_rejected_membership_values(
    source: str,
    target: tuple[str, str, str],
    expected_constant_name: str,
    namespace: object,
) -> frozenset[str]:
    values: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.NotIn):
            continue
        if len(node.comparators) != 1:
            continue
        if _py_rejection_target(node.left) != target:
            continue
        comparator = node.comparators[0]
        if not isinstance(comparator, ast.Name):
            continue
        if comparator.id != expected_constant_name:
            raise AssertionError(
                f"Python membership rejection for {target[1]}.{target[2]} "
                "uses an unexpected constant"
            )
        values.update(getattr(namespace, comparator.id))
    if not values:
        _, mapping_name, field_name = target
        raise AssertionError(
            f"Python membership rejection for {mapping_name}.{field_name} "
            "is not discoverable"
        )
    return frozenset(values)


def _py_rejected_boolean_value(
    source: str,
    target: tuple[str, str, str],
) -> bool:
    values: set[bool] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.IsNot, ast.NotEq)):
            continue
        if len(node.comparators) != 1:
            continue
        if _py_rejection_target(node.left) != target:
            continue
        compared_value = _py_boolean_constant(node.comparators[0])
        if compared_value is not None:
            values.add(compared_value)
    if len(values) != 1:
        _, mapping_name, field_name = target
        raise AssertionError(
            f"Python boolean rejection for {mapping_name}.{field_name} is not discoverable"
        )
    return next(iter(values))


def _py_rejected_optional_boolean_value(
    source: str,
    target: tuple[str, str, str],
) -> bool:
    values: set[bool] = set()
    has_none_guard = False
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.comparators) != 1 or _py_rejection_target(node.left) != target:
            continue
        comparator = node.comparators[0]
        if (
            len(node.ops) == 1
            and isinstance(node.ops[0], (ast.IsNot, ast.NotEq))
            and isinstance(comparator, ast.Constant)
            and comparator.value is None
        ):
            has_none_guard = True
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.IsNot, ast.NotEq)):
            continue
        compared_value = _py_boolean_constant(comparator)
        if compared_value is not None:
            values.add(compared_value)
    if len(values) != 1 or not has_none_guard:
        _, mapping_name, field_name = target
        raise AssertionError(
            "Python optional boolean rejection for "
            f"{mapping_name}.{field_name} is not discoverable"
        )
    return next(iter(values))


def _py_rejection_target(node: ast.AST) -> tuple[str, str, str] | None:
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        field_name = _py_subscript_key(node.slice)
        if field_name is not None:
            return ("subscript", node.value.id, field_name)
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.args
        ):
            field_name = _py_string_constant(node.args[0])
            if field_name is not None:
                return ("get", node.func.value.id, field_name)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "_optional_string_from_mapping"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
        ):
            field_name = _py_string_constant(node.args[1])
            if field_name is not None:
                return ("optional", node.args[0].id, field_name)
    return None


def _py_subscript_key(node: ast.AST) -> str | None:
    index_type = getattr(ast, "Index", None)
    if index_type is not None and isinstance(node, index_type):
        node = node.value
    return _py_string_constant(node)


def _py_string_constant(
    node: ast.AST,
    string_constants: Mapping[str, str] | None = None,
) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (
        isinstance(node, ast.Name)
        and string_constants is not None
        and node.id in string_constants
    ):
        return string_constants[node.id]
    return None


def _py_boolean_constant(node: ast.AST) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


def _py_source_string_constants(source: str) -> Mapping[str, str]:
    constants: dict[str, str] = {}
    if not source:
        return constants
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                value = _py_string_constant(node.value)
                if value is not None:
                    constants[target.id] = value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = _py_string_constant(node.value) if node.value is not None else None
            if value is not None:
                constants[node.target.id] = value
    return constants


def _py_backend_state_reason_consistency_rules(source: str) -> frozenset[str]:
    body = _py_function_source(source, "_validate_linked_evidence_pack_reason_consistency")
    call_source = _py_function_source(source, "_validated_linked_evidence_pack_projection")
    _require_substrings(
        call_source,
        ("_validate_linked_evidence_pack_reason_consistency(",),
        "backend state/reason consistency call",
    )
    return _state_reason_consistency_rules_from_requirements(
        {
            "available_status_has_no_reasons": (
                'values["status"] == "available"',
                "degraded_reasons or unavailable_reasons",
            ),
            "degraded_status_has_degraded_reasons_only": (
                'values["status"] == "degraded"',
                "not degraded_reasons or unavailable_reasons",
            ),
            "unavailable_status_has_unavailable_reasons": (
                'values["status"] == "unavailable"',
                "not unavailable_reasons",
            ),
            "freshness_state_matches_stale_reputation": (
                '"stale_reputation" in degraded_reasons',
                'values["freshness_state"] == "stale"',
            ),
            "conflict_state_matches_conflicting_enrichment": (
                "expected_conflict_state =",
                '"conflicting" if "conflicting_enrichment" in degraded_reasons else "none"',
            ),
            "source_state_matches_availability_reasons": (
                "expected_source_state =",
                '"source_stale" in degraded_reasons',
            ),
            "uncertainty_label_matches_state": (
                '_linked_evidence_pack_expected_uncertainty_label(',
                '"uncertainty_label"',
            ),
            "confidence_freshness_matches_freshness_state": (
                '"freshness",',
                'values["freshness_state"]',
            ),
            "confidence_ambiguity_badge_matches_conflict": (
                '"ambiguity_badge",',
                '"unresolved"',
                '"related-entity"',
            ),
        },
        body,
        "backend state/reason consistency",
    )


def _py_ai_state_reason_consistency_rules(source: str) -> frozenset[str]:
    projection_body = _py_function_source(source, "_projection_reasons")
    state_body = _py_function_source(source, "_state_consistency_reasons")
    uncertainty_body = _py_function_source(source, "_expected_uncertainty_label")
    _require_substrings(
        projection_body,
        (
            "reasons.extend(_uncertainty_state_reasons(projection))",
            "reasons.extend(_state_consistency_reasons(projection))",
        ),
        "AI state/reason consistency calls",
    )
    combined = state_body + "\n" + uncertainty_body
    return _state_reason_consistency_rules_from_requirements(
        {
            "available_status_has_no_reasons": (
                'status == "available"',
                "bool(degraded_reasons)",
                "bool(unavailable_reasons)",
            ),
            "degraded_status_has_degraded_reasons_only": (
                'status == "degraded"',
                "not degraded_reasons",
                "bool(unavailable_reasons)",
            ),
            "unavailable_status_has_unavailable_reasons": (
                'status == "unavailable"',
                "not unavailable_reasons",
            ),
            "freshness_state_matches_stale_reputation": (
                'freshness_state == "stale"',
                '"stale_reputation" not in degraded_reasons',
            ),
            "conflict_state_matches_conflicting_enrichment": (
                'conflict_state == "conflicting"',
                '"conflicting_enrichment" not in degraded_reasons',
            ),
            "source_state_matches_availability_reasons": (
                'source_state == "unavailable"',
                'source_state == "degraded"',
                '"source_stale" not in degraded_reasons',
            ),
            "uncertainty_label_matches_state": (
                'return "source_unavailable"',
                'return "unresolved_conflict"',
                'return "stale_review_required"',
                'return "related_entity_not_authoritative"',
            ),
            "confidence_freshness_matches_freshness_state": (
                'confidence.get("freshness") != freshness_state',
            ),
            "confidence_ambiguity_badge_matches_conflict": (
                "expected_badge =",
                '"unresolved"',
                '"related-entity"',
            ),
        },
        combined,
        "AI state/reason consistency",
    )


def _py_function_source(source: str, function_name: str) -> str:
    pattern = rf"^def {re.escape(function_name)}\("
    match = re.search(pattern, source, re.M)
    if match is None:
        raise AssertionError(f"Python function {function_name} is not discoverable")
    next_match = re.search(r"^def \w+\(", source[match.end() :], re.M)
    end = len(source) if next_match is None else match.end() + next_match.start()
    return source[match.start() : end]


def _ts_set(source: str, name: str) -> frozenset[str]:
    match = re.search(
        rf"const {re.escape(name)} = new Set\(\[(?P<body>.*?)\]\);",
        source,
        re.S,
    )
    if match is None:
        raise AssertionError(f"operator UI constant {name} is not discoverable")
    return frozenset(_string_literals(match.group("body")))


def _ts_set_with_spreads(
    source: str,
    name: str,
    *,
    seen: frozenset[str] = frozenset(),
) -> frozenset[str]:
    if name in seen:
        raise AssertionError(f"operator UI constant {name} has recursive spread")
    match = re.search(
        rf"const {re.escape(name)} = new Set\(\[(?P<body>.*?)\]\);",
        source,
        re.S,
    )
    if match is None:
        raise AssertionError(f"operator UI constant {name} is not discoverable")
    body = match.group("body")
    values = set(_string_literals(body))
    for spread_name in re.findall(r"\.\.\.(EVIDENCE_PACK_[A-Z0-9_]+)", body):
        values.update(
            _ts_set_with_spreads(source, spread_name, seen=seen | frozenset({name}))
        )
    return frozenset(values)


def _ts_string_constant(source: str, name: str) -> str:
    match = re.search(rf'const {re.escape(name)} =\s*"([^"]+)";', source)
    if match is None:
        raise AssertionError(f"operator UI constant {name} is not discoverable")
    return match.group(1)


def _ts_number_expression(source: str, name: str) -> int:
    match = re.search(rf"const {re.escape(name)} =\s*([0-9\s*+/()-]+);", source)
    if match is None:
        raise AssertionError(f"operator UI constant {name} is not discoverable")
    expression = match.group(1)
    if not re.fullmatch(r"[0-9\s*+/()-]+", expression):
        raise AssertionError(f"operator UI constant {name} is not a safe expression")
    return _safe_integer_expression(expression)


def _ts_enforced_freshness_window_milliseconds(source: str) -> int:
    function_body = _ts_function_body(source, "validateEvidencePackFreshnessWindow")
    _require_substrings(
        function_body,
        (
            "EVIDENCE_PACK_FRESHNESS_WINDOW_MS",
            'freshnessState === "fresh"',
            'freshnessState === "stale"',
        ),
        "operator UI freshness-window enforcement",
    )
    _ts_require_call(
        source,
        "validateEvidencePackFreshnessWindow",
        ("custody", "freshnessState", "evidenceRequestId"),
    )
    return _ts_number_expression(source, "EVIDENCE_PACK_FRESHNESS_WINDOW_MS")


def _ts_state_reason_consistency_rules(source: str) -> frozenset[str]:
    function_body = _ts_function_body(source, "validateEvidencePackReasonConsistency")
    _ts_require_call(
        source,
        "validateEvidencePackReasonConsistency",
        (
            "pack",
            "confidence",
            "{\n      status,\n      freshnessState,\n      conflictState,\n      sourceState,\n      uncertaintyLabel,\n    }",
        ),
    )
    return _state_reason_consistency_rules_from_requirements(
        {
            "available_status_has_no_reasons": (
                'labels.status === "available"',
                "degradedReasons.length > 0",
                "unavailableReasons.length > 0",
            ),
            "degraded_status_has_degraded_reasons_only": (
                'labels.status === "degraded"',
                "degradedReasons.length === 0",
                "unavailableReasons.length > 0",
            ),
            "unavailable_status_has_unavailable_reasons": (
                'labels.status === "unavailable"',
                "unavailableReasons.length === 0",
            ),
            "freshness_state_matches_stale_reputation": (
                'degradedReasons.includes("stale_reputation")',
                'labels.freshnessState === "stale"',
            ),
            "conflict_state_matches_conflicting_enrichment": (
                "expectedConflictState =",
                'degradedReasons.includes("conflicting_enrichment")',
                '"conflicting"',
                '"none"',
            ),
            "source_state_matches_availability_reasons": (
                "expectedSourceState =",
                'degradedReasons.includes("source_stale")',
                '"unavailable"',
                '"degraded"',
                '"available"',
            ),
            "uncertainty_label_matches_state": (
                "expectedEvidencePackUncertaintyLabel(",
                "labels.uncertaintyLabel",
            ),
            "confidence_freshness_matches_freshness_state": (
                "asString(confidence.freshness) !== labels.freshnessState",
            ),
            "confidence_ambiguity_badge_matches_conflict": (
                "asString(confidence.ambiguity_badge)",
                '"unresolved"',
                '"related-entity"',
            ),
        },
        function_body,
        "operator UI state/reason consistency",
    )


def _ts_rejected_pack_string_field(source: str, field_name: str) -> str:
    variable_name = _ts_pack_string_variable(source, field_name)
    match = re.search(
        rf"\b{re.escape(variable_name)}\s*!==\s*"
        r'(?:"([^\"]+)"|(EVIDENCE_PACK_[A-Z0-9_]+))',
        source,
    )
    if match is None:
        raise AssertionError(
            f"operator UI pack field {field_name} rejection is not discoverable"
        )
    literal_value, constant_name = match.groups()
    if literal_value is not None:
        return literal_value
    return _ts_string_constant(source, constant_name)


def _ts_no_workflow_authority_rejection(source: str) -> str:
    values = frozenset(
        {
            _ts_rejected_pack_string_field(source, "workflow_authority"),
            _ts_rejected_mapping_string_field(
                source,
                "confidence",
                "source_native_score_authority",
            ),
        }
    )
    if len(values) != 1:
        raise AssertionError(
            "operator UI workflow authority rejection is not consistently discoverable"
        )
    return next(iter(values))


def _ts_subordinate_authority_posture_rejection(source: str) -> str:
    try:
        values = frozenset(
            {
                _ts_rejected_pack_string_field(source, "authority_posture"),
                _ts_rejected_mapping_string_field(
                    source,
                    "provenance",
                    "authority_posture",
                ),
            }
        )
    except AssertionError as exc:
        raise AssertionError(
            "operator UI authority_posture rejection is not consistently discoverable"
        ) from exc
    if len(values) != 1:
        raise AssertionError(
            "operator UI authority_posture rejection is not consistently discoverable"
        )
    return next(iter(values))


def _ts_rejected_mapping_string_field(
    source: str,
    mapping_name: str,
    field_name: str,
) -> str:
    match = re.search(
        rf"\basString\({re.escape(mapping_name)}\.{re.escape(field_name)}\)"
        r'\s*!==\s*(?:"([^\"]+)"|(EVIDENCE_PACK_[A-Z0-9_]+))',
        source,
    )
    if match is None:
        raise AssertionError(
            "operator UI mapping field "
            f"{mapping_name}.{field_name} rejection is not discoverable"
        )
    literal_value, constant_name = match.groups()
    if literal_value is not None:
        return literal_value
    return _ts_string_constant(source, constant_name)


def _ts_pack_string_variable(source: str, field_name: str) -> str:
    match = re.search(
        rf"\bconst\s+(\w+)\s*=\s*asString\(pack\.{re.escape(field_name)}\);",
        source,
    )
    if match is None:
        raise AssertionError(f"operator UI pack field {field_name} is not discoverable")
    return match.group(1)


def _ts_rejected_pack_boolean_field(source: str, field_name: str) -> bool:
    match = re.search(
        rf"\bpack\.{re.escape(field_name)}\s*!==\s*(true|false)",
        source,
    )
    if match is None:
        raise AssertionError(
            f"operator UI pack field {field_name} boolean rejection is not discoverable"
        )
    return match.group(1) == "true"


def _ts_rejected_optional_pack_boolean_field(source: str, field_name: str) -> bool:
    variable = f"pack.{field_name}"
    condition = _ts_condition_for_error(source, "must stay operator visible")
    undefined_check = f"{variable} !== undefined"
    match = re.search(rf"\b{re.escape(variable)}\s*!==\s*(true|false)", condition)
    if undefined_check not in condition or match is None:
        raise AssertionError(
            f"operator UI pack field {field_name} optional boolean rejection is not discoverable"
        )
    return match.group(1) == "true"


def _ts_forbidden_defined_pack_fields(source: str, error_message: str) -> frozenset[str]:
    condition = _ts_condition_for_error(source, error_message)
    fields = frozenset(
        re.findall(r"\bpack\.([A-Za-z0-9_]+)\s*!==\s*undefined", condition)
    )
    if not fields:
        raise AssertionError(
            f"operator UI forbidden pack fields for {error_message} are not discoverable"
        )
    return fields


def _ts_recognized_fields_rejection(source: str) -> frozenset[str]:
    try:
        condition = _ts_condition_for_error(source, "unexpected evidence-pack fields")
        _require_substrings(
            condition,
            (
                "Object.keys(pack).some(",
                "(fieldName) => !EVIDENCE_PACK_RECOGNIZED_FIELDS.has(fieldName)",
            ),
            "operator UI recognized-field rejection",
        )
    except AssertionError as exc:
        raise AssertionError("operator UI recognized-field rejection drift") from exc
    return _ts_set_with_spreads(source, "EVIDENCE_PACK_RECOGNIZED_FIELDS")


def _ts_forbidden_projection_sources_rejection(source: str) -> frozenset[str]:
    projection_source_variable = _ts_pack_string_variable(source, "projection_source")
    condition = _ts_condition_for_error(
        source,
        "rejects cache or browser sourced evidence-pack truth",
    )
    expected_check = (
        "EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES.has("
        f'{projection_source_variable} ?? ""'
        ")"
    )
    if expected_check not in condition:
        raise AssertionError(
            "operator UI forbidden projection-source enforcement is not discoverable"
        )
    return _ts_set(source, "EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES")


def _ts_condition_for_error(source: str, error_message: str) -> str:
    message_index = source.find(error_message)
    if message_index == -1:
        raise AssertionError(
            f"operator UI rejection message {error_message} is not discoverable"
        )
    throw_index = source.rfind(
        "throw new OperatorDataProviderContractError",
        0,
        message_index,
    )
    if throw_index == -1:
        raise AssertionError(
            f"operator UI rejection for {error_message} is not discoverable"
        )
    if_index = source.rfind("if (", 0, throw_index)
    if if_index == -1:
        raise AssertionError(
            f"operator UI rejection condition for {error_message} is not discoverable"
        )
    return _extract_parenthesized(source, if_index + len("if "))


def _ts_function_body(source: str, function_name: str) -> str:
    match = re.search(rf"\bfunction\s+{re.escape(function_name)}\s*\(", source)
    if match is None:
        raise AssertionError(f"operator UI function {function_name} is not discoverable")
    arguments_source = _extract_parenthesized(source, source.find("(", match.start()))
    body_start = source.find("{", match.end() + len(arguments_source))
    if body_start == -1:
        raise AssertionError(f"operator UI function {function_name} body is not discoverable")
    return _extract_braced(source, body_start)


def _ts_require_call(
    source: str,
    function_name: str,
    expected_arguments: tuple[str, ...],
) -> None:
    expected_normalized = tuple(_normalize_ts_argument(arg) for arg in expected_arguments)
    for match in re.finditer(rf"\b{re.escape(function_name)}\s*\(", source):
        arguments = tuple(
            _normalize_ts_argument(argument)
            for argument in _split_ts_arguments(
                _extract_parenthesized(source, match.end() - 1)
            )
            if argument.strip()
        )
        if arguments == expected_normalized:
            return
    raise AssertionError(f"operator UI {function_name} call is not discoverable")


def _normalize_ts_argument(argument: str) -> str:
    return re.sub(r"\s+", " ", argument.strip())


def _extract_parenthesized(source: str, open_index: int) -> str:
    if open_index >= len(source) or source[open_index] != "(":
        raise AssertionError("operator UI condition is not parenthesized")
    depth = 0
    string_quote: str | None = None
    escaped = False
    condition_start = open_index + 1
    for index in range(open_index, len(source)):
        character = source[index]
        if string_quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == string_quote:
                string_quote = None
            continue
        if character in {'"', "'", "`"}:
            string_quote = character
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return source[condition_start:index]
    raise AssertionError("operator UI condition is not closed")


def _extract_braced(source: str, open_index: int) -> str:
    if open_index >= len(source) or source[open_index] != "{":
        raise AssertionError("operator UI block is not braced")
    depth = 0
    string_quote: str | None = None
    escaped = False
    body_start = open_index + 1
    for index in range(open_index, len(source)):
        character = source[index]
        if string_quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == string_quote:
                string_quote = None
            continue
        if character in {'"', "'", "`"}:
            string_quote = character
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[body_start:index]
    raise AssertionError("operator UI block is not closed")


def _state_reason_consistency_rules_from_requirements(
    requirements: Mapping[str, tuple[str, ...]],
    source: str,
    label: str,
) -> frozenset[str]:
    rules = {
        rule_name
        for rule_name, substrings in requirements.items()
        if all(substring in source for substring in substrings)
    }
    if frozenset(rules) != _STATE_REASON_CONSISTENCY_RULES:
        raise AssertionError(f"{label} drift")
    return frozenset(rules)


def _require_substrings(source: str, substrings: tuple[str, ...], label: str) -> None:
    if not all(substring in source for substring in substrings):
        raise AssertionError(f"{label} drift")


def _safe_integer_expression(expression: str) -> int:
    def evaluate(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(
            node.op,
            (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Div),
        ):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise AssertionError("operator UI numeric constant divides by zero")
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if left % right != 0:
                raise AssertionError("operator UI numeric constant is not integral")
            return left // right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -evaluate(node.operand)
        raise AssertionError("operator UI numeric constant is not a safe expression")

    return evaluate(ast.parse(expression, mode="eval"))


def _string_literals(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r'"([^"]+)"', value))


def _assert_equal(label: str, first: object, *others: object) -> None:
    for other in others:
        if first != other:
            raise AssertionError(f"Phase 63 evidence-pack contract drift: {label}")


def contract_with_drift(
    contract: Phase63EvidencePackContract,
    field_name: str,
    value: object,
) -> Phase63EvidencePackContract:
    return replace(contract, **{field_name: value})


def contract_with_label_drift(
    contract: Phase63EvidencePackContract,
    label_name: str,
    values: frozenset[str],
) -> Phase63EvidencePackContract:
    labels = dict(contract.labels)
    labels[label_name] = values
    return replace(contract, labels=MappingProxyType(labels))
