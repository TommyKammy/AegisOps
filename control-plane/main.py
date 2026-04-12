#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import sys
from typing import Mapping, Sequence, TextIO
from urllib.parse import parse_qs, urlsplit

from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
)

MAX_WAZUH_INGEST_BODY_BYTES = 1_048_576


class RequestTooLargeError(ValueError):
    """Raised when a reviewed request body exceeds the allowed size limit."""


def _normalize_alert_id(value: str) -> str:
    return value.strip()


def _normalize_case_id(value: str) -> str:
    return value.strip()


def _normalize_record_family(value: str) -> str:
    return value.strip()


def _normalize_record_id(value: str) -> str:
    return value.strip()


def _normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("optional string fields must be JSON strings when provided")
    normalized = value.strip()
    return normalized or None


def _require_json_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_json_string_sequence(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name, ())
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array of non-empty strings")
    normalized_values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must be a JSON array of non-empty strings")
        normalized_values.append(item.strip())
    return tuple(normalized_values)


def _parse_datetime_arg(value: str, field_name: str) -> datetime:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO 8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def _require_json_datetime(payload: Mapping[str, object], field_name: str) -> datetime:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
    return _parse_datetime_arg(value, field_name)


def _read_json_request_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer") from exc
    if content_length <= 0:
        raise ValueError("request body is required")
    if content_length > MAX_WAZUH_INGEST_BODY_BYTES:
        raise RequestTooLargeError("request body exceeds the reviewed size limit")
    try:
        raw_payload = handler.rfile.read(content_length).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("request body must be valid UTF-8 JSON") from exc
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"request body must be valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    return payload


def _peer_addr_is_loopback(peer_addr: str | None) -> bool:
    if peer_addr is None or peer_addr.strip() == "":
        return False
    try:
        return ipaddress.ip_address(peer_addr.strip()).is_loopback
    except ValueError:
        return False


def _require_loopback_operator_request(handler: BaseHTTPRequestHandler) -> None:
    peer_addr = handler.client_address[0] if handler.client_address else None
    if _peer_addr_is_loopback(peer_addr):
        return
    raise PermissionError(
        "operator write surface only accepts loopback callers until a reviewed operator auth boundary exists"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the reviewed control-plane runtime service or render read-only "
            "runtime, record, and reconciliation inspection views."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "serve",
        help="Run the reviewed long-running control-plane runtime service.",
    )
    subparsers.add_parser("runtime", help="Render the current runtime snapshot.")

    inspect_records = subparsers.add_parser(
        "inspect-records",
        help="Render a read-only view of one control-plane record family.",
    )
    inspect_records.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect.",
    )

    subparsers.add_parser(
        "inspect-reconciliation-status",
        help="Render a read-only reconciliation status summary.",
    )
    subparsers.add_parser(
        "inspect-analyst-queue",
        help="Render the business-hours analyst review queue view.",
    )
    inspect_alert_detail = subparsers.add_parser(
        "inspect-alert-detail",
        help="Render the reviewed Wazuh-backed alert detail view for one alert.",
    )
    inspect_alert_detail.add_argument(
        "--alert-id",
        required=True,
        help="Control-plane alert identifier to inspect.",
    )
    inspect_case_detail = subparsers.add_parser(
        "inspect-case-detail",
        help="Render the approved case detail view for one case.",
    )
    inspect_case_detail.add_argument(
        "--case-id",
        required=True,
        help="Control-plane case identifier to inspect.",
    )
    promote_alert_to_case = subparsers.add_parser(
        "promote-alert-to-case",
        help="Promote one reviewed alert into durable bounded casework.",
    )
    promote_alert_to_case.add_argument(
        "--alert-id",
        required=True,
        help="Control-plane alert identifier to promote.",
    )
    promote_alert_to_case.add_argument(
        "--case-id",
        help="Optional case identifier to reuse when linking the alert.",
    )
    promote_alert_to_case.add_argument(
        "--case-lifecycle-state",
        default="open",
        help="Lifecycle state to apply when the case is first created.",
    )
    record_case_observation = subparsers.add_parser(
        "record-case-observation",
        help="Record a bounded reviewed case observation.",
    )
    record_case_observation.add_argument("--case-id", required=True)
    record_case_observation.add_argument("--author-identity", required=True)
    record_case_observation.add_argument("--observed-at", required=True)
    record_case_observation.add_argument("--scope-statement", required=True)
    record_case_observation.add_argument(
        "--supporting-evidence-id",
        action="append",
        default=[],
        help="Supporting evidence identifier to link; may be repeated.",
    )
    record_case_lead = subparsers.add_parser(
        "record-case-lead",
        help="Record a bounded reviewed triage lead for a case.",
    )
    record_case_lead.add_argument("--case-id", required=True)
    record_case_lead.add_argument("--triage-owner", required=True)
    record_case_lead.add_argument("--triage-rationale", required=True)
    record_case_lead.add_argument(
        "--observation-id",
        help="Optional observation identifier to anchor the lead.",
    )
    record_case_recommendation = subparsers.add_parser(
        "record-case-recommendation",
        help="Record a bounded reviewed recommendation for a case.",
    )
    record_case_recommendation.add_argument("--case-id", required=True)
    record_case_recommendation.add_argument("--review-owner", required=True)
    record_case_recommendation.add_argument("--intended-outcome", required=True)
    record_case_recommendation.add_argument(
        "--lead-id",
        help="Optional lead identifier to anchor the recommendation.",
    )
    record_case_handoff = subparsers.add_parser(
        "record-case-handoff",
        help="Record a bounded business-hours handoff note for a case.",
    )
    record_case_handoff.add_argument("--case-id", required=True)
    record_case_handoff.add_argument("--handoff-at", required=True)
    record_case_handoff.add_argument("--handoff-owner", required=True)
    record_case_handoff.add_argument("--handoff-note", required=True)
    record_case_handoff.add_argument(
        "--follow-up-evidence-id",
        action="append",
        default=[],
        help="Follow-up evidence identifier to link; may be repeated.",
    )
    record_case_disposition = subparsers.add_parser(
        "record-case-disposition",
        help="Record a bounded reviewed case disposition or closure state.",
    )
    record_case_disposition.add_argument("--case-id", required=True)
    record_case_disposition.add_argument("--disposition", required=True)
    record_case_disposition.add_argument("--rationale", required=True)
    record_case_disposition.add_argument("--recorded-at", required=True)
    inspect_assistant_context = subparsers.add_parser(
        "inspect-assistant-context",
        help="Render a read-only analyst-assistant context view for one record.",
    )
    inspect_assistant_context.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for assistant context.",
    )
    inspect_assistant_context.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for assistant context.",
    )
    inspect_advisory_output = subparsers.add_parser(
        "inspect-advisory-output",
        help="Render the cited advisory-output contract for one reviewed record.",
    )
    inspect_advisory_output.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for advisory output.",
    )
    inspect_advisory_output.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for advisory output.",
    )
    render_recommendation_draft = subparsers.add_parser(
        "render-recommendation-draft",
        help="Render cited recommendation-draft output for one reviewed record.",
    )
    render_recommendation_draft.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to render for recommendation drafting.",
    )
    render_recommendation_draft.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to render for recommendation drafting.",
    )
    return parser


def run_control_plane_service(
    service: AegisOpsControlPlaneService,
    *,
    stderr: TextIO | None = None,
) -> int:
    service.validate_wazuh_ingest_runtime()
    runtime_snapshot = service.describe_runtime().to_dict()
    stderr = stderr or sys.stderr

    class _RequestHandler(BaseHTTPRequestHandler):
        server_version = "AegisOpsControlPlane/1.0"

        def do_GET(self) -> None:  # noqa: N802
            request_target = urlsplit(self.path)
            request_path = request_target.path

            if request_path == "/healthz":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service_name": runtime_snapshot["service_name"],
                        "status": "ok",
                    },
                )
                return

            if request_path == "/readyz":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service_name": runtime_snapshot["service_name"],
                        "status": "ready",
                        "persistence_mode": runtime_snapshot["persistence_mode"],
                    },
                )
                return

            if request_path == "/runtime":
                self._write_json(HTTPStatus.OK, service.describe_runtime().to_dict())
                return

            if request_path == "/inspect-records":
                family = parse_qs(request_target.query).get("family", [""])[0]
                if not family:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "family query parameter is required",
                        },
                    )
                    return

                try:
                    payload = service.inspect_records(family).to_dict()
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            if request_path == "/inspect-reconciliation-status":
                self._write_json(
                    HTTPStatus.OK,
                    service.inspect_reconciliation_status().to_dict(),
                )
                return

            if request_path == "/inspect-analyst-queue":
                self._write_json(HTTPStatus.OK, service.inspect_analyst_queue().to_dict())
                return

            if request_path == "/inspect-alert-detail":
                alert_id = _normalize_alert_id(
                    parse_qs(request_target.query).get("alert_id", [""])[0]
                )
                if not alert_id:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "alert_id query parameter is required",
                        },
                    )
                    return
                try:
                    payload = service.inspect_alert_detail(alert_id).to_dict()
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                except LookupError as exc:
                    self._write_json(
                        HTTPStatus.NOT_FOUND,
                        {
                            "error": "not_found",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            if request_path == "/inspect-case-detail":
                case_id = _normalize_case_id(
                    parse_qs(request_target.query).get("case_id", [""])[0]
                )
                if not case_id:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "case_id query parameter is required",
                        },
                    )
                    return
                try:
                    payload = service.inspect_case_detail(case_id).to_dict()
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                except LookupError as exc:
                    self._write_json(
                        HTTPStatus.NOT_FOUND,
                        {
                            "error": "not_found",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            if request_path in {
                "/inspect-assistant-context",
                "/inspect-advisory-output",
                "/render-recommendation-draft",
            }:
                family = _normalize_record_family(
                    parse_qs(request_target.query).get("family", [""])[0]
                )
                if not family:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "family query parameter is required",
                        },
                    )
                    return
                record_id = _normalize_record_id(
                    parse_qs(request_target.query).get("record_id", [""])[0]
                )
                if not record_id:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "record_id query parameter is required",
                        },
                    )
                    return
                try:
                    if request_path == "/inspect-assistant-context":
                        payload = service.inspect_assistant_context(
                            family,
                            record_id,
                        ).to_dict()
                    elif request_path == "/inspect-advisory-output":
                        payload = service.inspect_advisory_output(
                            family,
                            record_id,
                        ).to_dict()
                    else:
                        payload = service.render_recommendation_draft(
                            family,
                            record_id,
                        ).to_dict()
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                except LookupError as exc:
                    self._write_json(
                        HTTPStatus.NOT_FOUND,
                        {
                            "error": "not_found",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            self._write_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "not_found",
                    "path": request_path,
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            request_target = urlsplit(self.path)
            request_path = request_target.path

            if request_path.startswith("/operator/"):
                try:
                    _require_loopback_operator_request(self)
                except PermissionError as exc:
                    self._write_json(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": "forbidden",
                            "message": str(exc),
                        },
                    )
                    return

            if request_path == "/operator/promote-alert-to-case":
                try:
                    payload = _read_json_request_body(self)
                    promoted_case = service.promote_alert_to_case(
                        _normalize_alert_id(_require_json_string(payload, "alert_id")),
                        case_id=_normalize_optional_string(payload.get("case_id")),
                        case_lifecycle_state=_require_json_string(
                            payload,
                            "case_lifecycle_state",
                        )
                        if "case_lifecycle_state" in payload
                        else "open",
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(promoted_case))
                return

            if request_path == "/operator/record-case-observation":
                try:
                    payload = _read_json_request_body(self)
                    observation = service.record_case_observation(
                        case_id=_normalize_case_id(_require_json_string(payload, "case_id")),
                        author_identity=_require_json_string(payload, "author_identity"),
                        observed_at=_require_json_datetime(payload, "observed_at"),
                        scope_statement=_require_json_string(payload, "scope_statement"),
                        supporting_evidence_ids=_require_json_string_sequence(
                            payload,
                            "supporting_evidence_ids",
                        ),
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(observation))
                return

            if request_path == "/operator/record-case-lead":
                try:
                    payload = _read_json_request_body(self)
                    lead = service.record_case_lead(
                        case_id=_normalize_case_id(_require_json_string(payload, "case_id")),
                        triage_owner=_require_json_string(payload, "triage_owner"),
                        triage_rationale=_require_json_string(payload, "triage_rationale"),
                        observation_id=_normalize_optional_string(
                            payload.get("observation_id")
                        ),
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(lead))
                return

            if request_path == "/operator/record-case-recommendation":
                try:
                    payload = _read_json_request_body(self)
                    recommendation = service.record_case_recommendation(
                        case_id=_normalize_case_id(_require_json_string(payload, "case_id")),
                        review_owner=_require_json_string(payload, "review_owner"),
                        intended_outcome=_require_json_string(payload, "intended_outcome"),
                        lead_id=_normalize_optional_string(payload.get("lead_id")),
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(recommendation))
                return

            if request_path == "/operator/record-case-handoff":
                try:
                    payload = _read_json_request_body(self)
                    case_record = service.record_case_handoff(
                        case_id=_normalize_case_id(_require_json_string(payload, "case_id")),
                        handoff_at=_require_json_datetime(payload, "handoff_at"),
                        handoff_owner=_require_json_string(payload, "handoff_owner"),
                        handoff_note=_require_json_string(payload, "handoff_note"),
                        follow_up_evidence_ids=_require_json_string_sequence(
                            payload,
                            "follow_up_evidence_ids",
                        ),
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(case_record))
                return

            if request_path == "/operator/record-case-disposition":
                try:
                    payload = _read_json_request_body(self)
                    case_record = service.record_case_disposition(
                        case_id=_normalize_case_id(_require_json_string(payload, "case_id")),
                        disposition=_require_json_string(payload, "disposition"),
                        rationale=_require_json_string(payload, "rationale"),
                        recorded_at=_require_json_datetime(payload, "recorded_at"),
                    )
                except RequestTooLargeError as exc:
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    status = (
                        HTTPStatus.NOT_FOUND
                        if isinstance(exc, LookupError)
                        else HTTPStatus.BAD_REQUEST
                    )
                    self._write_json(
                        status,
                        {
                            "error": "not_found"
                            if status == HTTPStatus.NOT_FOUND
                            else "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, _json_ready(case_record))
                return

            if request_path != "/intake/wazuh":
                self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": "not_found",
                        "path": request_path,
                    },
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "Content-Length must be an integer",
                    },
                )
                return
            if content_length <= 0:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "request body is required",
                    },
                )
                return
            if content_length > MAX_WAZUH_INGEST_BODY_BYTES:
                self._write_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {
                        "error": "request_too_large",
                        "message": "request body exceeds the reviewed Wazuh ingest size limit",
                    },
                )
                return

            try:
                raw_payload = self.rfile.read(content_length).decode("utf-8")
            except UnicodeDecodeError:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "request body must be valid UTF-8 JSON",
                    },
                )
                return

            try:
                alert = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": f"request body must be valid JSON: {exc.msg}",
                    },
                )
                return

            try:
                ingest_result = service.ingest_wazuh_alert(
                    raw_alert=alert,
                    authorization_header=self.headers.get("Authorization"),
                    forwarded_proto=self.headers.get("X-Forwarded-Proto"),
                    reverse_proxy_secret_header=self.headers.get(
                        "X-AegisOps-Proxy-Secret"
                    ),
                    peer_addr=self.client_address[0] if self.client_address else None,
                )
            except PermissionError as exc:
                self._write_json(
                    HTTPStatus.FORBIDDEN,
                    {
                        "error": "forbidden",
                        "message": str(exc),
                    },
                )
                return
            except ValueError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": str(exc),
                    },
                )
                return

            self._write_json(
                HTTPStatus.ACCEPTED,
                {
                    "disposition": ingest_result.disposition,
                    "finding_id": ingest_result.alert.finding_id,
                    "alert": _json_ready(ingest_result.alert),
                    "reconciliation": _json_ready(ingest_result.reconciliation),
                },
            )

        def log_message(self, format: str, *args: object) -> None:
            print(
                "%s - - [%s] %s"
                % (
                    self.address_string(),
                    self.log_date_time_string(),
                    format % args,
                ),
                file=stderr,
            )

        def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(
        (str(runtime_snapshot["bind_host"]), int(runtime_snapshot["bind_port"])),
        _RequestHandler,
    )

    try:
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        raw = {
            field.name: getattr(value, field.name)
            for field in fields(value)
        }
    else:
        raw = value
    if isinstance(raw, Mapping):
        return {str(key): _json_ready(item) for key, item in raw.items()}
    if isinstance(raw, dict):
        return {key: _json_ready(item) for key, item in raw.items()}
    if isinstance(raw, tuple):
        return [_json_ready(item) for item in raw]
    if isinstance(raw, list):
        return [_json_ready(item) for item in raw]
    if hasattr(raw, "isoformat"):
        try:
            return raw.isoformat()
        except TypeError:
            return raw
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return raw


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    service: AegisOpsControlPlaneService | None = None,
) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(list(argv) if argv is not None else None)
    command = parsed.command or "runtime"
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    service = service or build_runtime_service()

    if command == "serve":
        return run_control_plane_service(service, stderr=stderr)
    if command == "runtime":
        payload = service.describe_runtime().to_dict()
    else:
        if command == "inspect-records":
            try:
                payload = service.inspect_records(parsed.family).to_dict()
            except ValueError as exc:
                parser.error(str(exc))
        elif command == "inspect-assistant-context":
            try:
                payload = service.inspect_assistant_context(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "inspect-case-detail":
            case_id = parsed.case_id.strip()
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = service.inspect_case_detail(case_id).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "promote-alert-to-case":
            alert_id = _normalize_alert_id(parsed.alert_id)
            if not alert_id:
                parser.error("alert_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.promote_alert_to_case(
                        alert_id,
                        case_id=_normalize_optional_string(parsed.case_id),
                        case_lifecycle_state=parsed.case_lifecycle_state.strip(),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "record-case-observation":
            case_id = _normalize_case_id(parsed.case_id)
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.record_case_observation(
                        case_id=case_id,
                        author_identity=parsed.author_identity.strip(),
                        observed_at=_parse_datetime_arg(
                            parsed.observed_at,
                            "observed_at",
                        ),
                        scope_statement=parsed.scope_statement.strip(),
                        supporting_evidence_ids=tuple(
                            evidence_id.strip()
                            for evidence_id in parsed.supporting_evidence_id
                        ),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "record-case-lead":
            case_id = _normalize_case_id(parsed.case_id)
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.record_case_lead(
                        case_id=case_id,
                        triage_owner=parsed.triage_owner.strip(),
                        triage_rationale=parsed.triage_rationale.strip(),
                        observation_id=_normalize_optional_string(parsed.observation_id),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "record-case-recommendation":
            case_id = _normalize_case_id(parsed.case_id)
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.record_case_recommendation(
                        case_id=case_id,
                        review_owner=parsed.review_owner.strip(),
                        intended_outcome=parsed.intended_outcome.strip(),
                        lead_id=_normalize_optional_string(parsed.lead_id),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "record-case-handoff":
            case_id = _normalize_case_id(parsed.case_id)
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.record_case_handoff(
                        case_id=case_id,
                        handoff_at=_parse_datetime_arg(
                            parsed.handoff_at,
                            "handoff_at",
                        ),
                        handoff_owner=parsed.handoff_owner.strip(),
                        handoff_note=parsed.handoff_note.strip(),
                        follow_up_evidence_ids=tuple(
                            evidence_id.strip()
                            for evidence_id in parsed.follow_up_evidence_id
                        ),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "record-case-disposition":
            case_id = _normalize_case_id(parsed.case_id)
            if not case_id:
                parser.error("case_id must be a non-empty string")
            try:
                payload = _json_ready(
                    service.record_case_disposition(
                        case_id=case_id,
                        disposition=parsed.disposition.strip(),
                        rationale=parsed.rationale.strip(),
                        recorded_at=_parse_datetime_arg(
                            parsed.recorded_at,
                            "recorded_at",
                        ),
                    )
                )
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "inspect-advisory-output":
            try:
                payload = service.inspect_advisory_output(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "render-recommendation-draft":
            try:
                payload = service.render_recommendation_draft(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "inspect-reconciliation-status":
            payload = service.inspect_reconciliation_status().to_dict()
        elif command == "inspect-analyst-queue":
            payload = service.inspect_analyst_queue().to_dict()
        elif command == "inspect-alert-detail":
            alert_id = _normalize_alert_id(parsed.alert_id)
            if not alert_id:
                parser.error("alert_id must be a non-empty string")
            try:
                payload = service.inspect_alert_detail(alert_id).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        else:
            raise AssertionError(f"Unhandled command: {command}")

    print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
