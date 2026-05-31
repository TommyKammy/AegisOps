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


@dataclass(frozen=True)
class Phase63EvidencePackContract:
    labels: Mapping[str, frozenset[str]]
    degraded_reasons: frozenset[str]
    unavailable_reasons: frozenset[str]
    required_custody_fields: frozenset[str]
    required_provenance_fields: frozenset[str]
    required_confidence_fields: frozenset[str]
    contract_fields: frozenset[str]
    supported_source_ids: frozenset[str]
    subordinate_authority_posture: str
    no_workflow_authority: str
    confidence_posture: str
    freshness_window_seconds: int
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
    _assert_equal(
        "source IDs",
        backend.supported_source_ids,
        ui.supported_source_ids,
        ai.supported_source_ids,
    )
    _assert_equal(
        "freshness window",
        backend.freshness_window_seconds,
        ui.freshness_window_seconds,
        ai.freshness_window_seconds,
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
    labels = {
        key: frozenset(
            inspection_projection._EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS[key]
        )
        for key in _LABEL_KEYS
    }
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=frozenset(
            inspection_projection._EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS
        ),
        unavailable_reasons=frozenset(
            inspection_projection._EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS
        ),
        required_custody_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS
        ),
        required_provenance_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS
        ),
        required_confidence_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS
        ),
        contract_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS
        ),
        supported_source_ids=frozenset({source_id}),
        subordinate_authority_posture=(
            inspection_projection._EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE
        ),
        no_workflow_authority=source_projection._NO_WORKFLOW_AUTHORITY,
        confidence_posture=registry_entry.confidence_posture,
        freshness_window_seconds=source_projection._parse_duration_seconds(
            registry_entry.freshness_window
        ),
        forbidden_projection_sources=frozenset(
            inspection_projection._EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES
        ),
        forbidden_readiness_claim_fields=frozenset(
            inspection_projection._EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS
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
    labels = {
        "consumer": frozenset({"ai_grounding"}),
        "status": frozenset(ai_grounding_validation._ALLOWED_STATUS),
        "freshness_state": frozenset(ai_grounding_validation._ALLOWED_FRESHNESS),
        "custody_state": frozenset({"complete"}),
        "confidence_state": frozenset({"present"}),
        "provenance_state": frozenset({"bound"}),
        "conflict_state": frozenset(ai_grounding_validation._ALLOWED_CONFLICT),
        "source_state": frozenset(ai_grounding_validation._ALLOWED_SOURCE_STATE),
        "uncertainty_label": frozenset(ai_grounding_validation._ALLOWED_UNCERTAINTY),
    }
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=frozenset(ai_grounding_validation._ALLOWED_DEGRADED_REASONS),
        unavailable_reasons=frozenset(
            ai_grounding_validation._ALLOWED_UNAVAILABLE_REASONS
        ),
        required_custody_fields=frozenset(
            ai_grounding_validation._REQUIRED_CUSTODY_FIELDS
        ),
        required_provenance_fields=frozenset(
            ai_grounding_validation._REQUIRED_PROVENANCE_FIELDS
        ),
        required_confidence_fields=frozenset(
            ai_grounding_validation._REQUIRED_CONFIDENCE_FIELDS
        ),
        contract_fields=frozenset(),
        supported_source_ids=source_ids,
        subordinate_authority_posture=(
            ai_grounding_validation._SUBORDINATE_AUTHORITY_POSTURE
        ),
        no_workflow_authority=ai_grounding_validation._NO_WORKFLOW_AUTHORITY,
        confidence_posture=registry_entry.confidence_posture,
        freshness_window_seconds=source_projection._parse_duration_seconds(
            registry_entry.freshness_window
        ),
        forbidden_projection_sources=frozenset(),
        forbidden_readiness_claim_fields=frozenset(),
        authority_truth_denials=frozenset(ai_grounding_validation._NEGATIVE_AUTHORITY),
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
    labels = _ts_allowed_labels(source)
    freshness_window_ms = _ts_number_expression(
        source,
        "EVIDENCE_PACK_FRESHNESS_WINDOW_MS",
    )
    return Phase63EvidencePackContract(
        labels=MappingProxyType(labels),
        degraded_reasons=_ts_set(source, "EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS"),
        unavailable_reasons=_ts_set(
            source,
            "EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS",
        ),
        required_custody_fields=_ts_set(
            source,
            "EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS",
        ),
        required_provenance_fields=_ts_set(
            source,
            "EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS",
        ),
        required_confidence_fields=_ts_set(
            source,
            "EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS",
        ),
        contract_fields=_ts_set(source, "EVIDENCE_PACK_CONTRACT_FIELDS"),
        supported_source_ids=frozenset(
            {_ts_string_constant(source, "EVIDENCE_PACK_SUPPORTED_SOURCE_ID")}
        ),
        subordinate_authority_posture=_ts_string_constant(
            source,
            "EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE",
        ),
        no_workflow_authority="none",
        confidence_posture=_ts_string_constant(
            source,
            "EVIDENCE_PACK_CONFIDENCE_POSTURE",
        ),
        freshness_window_seconds=freshness_window_ms // 1000,
        forbidden_projection_sources=_ts_set(
            source,
            "EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES",
        ),
        forbidden_readiness_claim_fields=frozenset(
            {
                "release_readiness_claim",
                "rc_readiness_claim",
                "gate_readiness_claim",
            }
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
    return {
        key: frozenset(_string_literals(value_source))
        for key, value_source in re.findall(
            r"(\w+):\s*new Set\(\[(.*?)\]\),",
            body,
            re.S,
        )
    }


def _ts_set(source: str, name: str) -> frozenset[str]:
    match = re.search(
        rf"const {re.escape(name)} = new Set\(\[(?P<body>.*?)\]\);",
        source,
        re.S,
    )
    if match is None:
        raise AssertionError(f"operator UI constant {name} is not discoverable")
    return frozenset(_string_literals(match.group("body")))


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
