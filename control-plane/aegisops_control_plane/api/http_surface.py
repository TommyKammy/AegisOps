from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from typing import Callable, TextIO
from urllib.parse import parse_qs, urlsplit

from .entrypoint_support import (
    MAX_WAZUH_INGEST_BODY_BYTES,
    RequestTooLargeError,
    json_ready,
    normalize_alert_id,
    normalize_case_id,
    normalize_optional_string,
    normalize_record_family,
    normalize_record_id,
    read_json_request_body,
    require_json_datetime,
    require_json_string,
    require_json_string_sequence,
    require_loopback_operator_request,
)
from .http_protected_surface import (
    authenticate_protected_read,
    authenticate_protected_write,
    protected_read_roles,
    require_matching_authenticated_identity,
    require_reviewed_proxy_identity_match,
)
from .http_runtime_surface import runtime_read_response
from ..runtime.readiness_contracts import resolve_readyz_runtime_status
from ..service import AegisOpsControlPlaneService


@dataclass(frozen=True)
class HttpSurfaceContext:
    service: AegisOpsControlPlaneService
    runtime_snapshot: dict[str, object]


GetRouteHandler = Callable[[BaseHTTPRequestHandler, HttpSurfaceContext, object], None]
PostRouteHandler = Callable[[BaseHTTPRequestHandler, HttpSurfaceContext, object], None]


def _query_value(handler: BaseHTTPRequestHandler, name: str) -> str:
    return parse_qs(urlsplit(handler.path).query).get(name, [""])[0]


def _write_json(
    handler: BaseHTTPRequestHandler,
    status: HTTPStatus,
    payload: dict[str, object],
) -> None:
    handler._write_json(status, payload)  # type: ignore[attr-defined]


def _write_lookup_or_bad_request(
    handler: BaseHTTPRequestHandler,
    exc: LookupError | ValueError,
) -> None:
    handler._write_lookup_or_bad_request(exc)  # type: ignore[attr-defined]


def _write_permission_or_bad_request(
    handler: BaseHTTPRequestHandler,
    exc: LookupError | PermissionError | ValueError,
) -> None:
    handler._write_permission_or_bad_request(exc)  # type: ignore[attr-defined]


def _handle_request_too_large(
    handler: BaseHTTPRequestHandler,
    exc: RequestTooLargeError,
) -> None:
    _write_json(
        handler,
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        {
            "error": "request_too_large",
            "message": str(exc),
        },
    )


def _handle_healthz(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    _write_json(
        handler,
        HTTPStatus.OK,
        {
            "service_name": context.runtime_snapshot["service_name"],
            "status": "ok",
        },
    )


def _handle_readyz(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    readiness_payload = context.service.inspect_readiness_diagnostics().to_dict()
    runtime_status = resolve_readyz_runtime_status(readiness_payload)
    _write_json(
        handler,
        runtime_status.http_status,
        runtime_status.to_readyz_payload(
            service_name=str(context.runtime_snapshot["service_name"]),
            persistence_mode=str(context.runtime_snapshot["persistence_mode"]),
        ),
    )


def _handle_runtime_read(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    request_path = urlsplit(handler.path).path
    runtime_response = runtime_read_response(
        service=context.service,
        request_path=request_path,
    )
    if runtime_response is None:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "path": request_path,
            },
        )
        return
    status, payload = runtime_response
    _write_json(handler, status, payload)


def _handle_inspect_records(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    family = _query_value(handler, "family")
    if not family:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "family query parameter is required",
            },
        )
        return
    try:
        payload = context.service.inspect_records(family).to_dict()
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return
    _write_json(handler, HTTPStatus.OK, payload)


def _handle_inspect_reconciliation_status(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    _write_json(
        handler,
        HTTPStatus.OK,
        context.service.inspect_reconciliation_status().to_dict(),
    )


def _handle_inspect_analyst_queue(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    _write_json(handler, HTTPStatus.OK, context.service.inspect_analyst_queue().to_dict())


def _handle_inspect_alert_detail(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    alert_id = normalize_alert_id(_query_value(handler, "alert_id"))
    if not alert_id:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "alert_id query parameter is required",
            },
        )
        return
    try:
        payload = context.service.inspect_alert_detail(alert_id).to_dict()
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return
    except LookupError as exc:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "message": str(exc),
            },
        )
        return
    _write_json(handler, HTTPStatus.OK, payload)


def _handle_inspect_case_detail(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    case_id = normalize_case_id(_query_value(handler, "case_id"))
    if not case_id:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "case_id query parameter is required",
            },
        )
        return
    try:
        payload = context.service.inspect_case_detail(case_id).to_dict()
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return
    except LookupError as exc:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "message": str(exc),
            },
        )
        return
    _write_json(handler, HTTPStatus.OK, payload)


def _handle_inspect_action_review(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    action_request_id = normalize_record_id(_query_value(handler, "action_request_id"))
    if not action_request_id:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "action_request_id query parameter is required",
            },
        )
        return
    try:
        payload = context.service.inspect_action_review_detail(action_request_id).to_dict()
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return
    except LookupError as exc:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "message": str(exc),
            },
        )
        return
    _write_json(handler, HTTPStatus.OK, payload)


def _handle_assistant_context_family(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    request_path = urlsplit(handler.path).path
    family = normalize_record_family(_query_value(handler, "family"))
    if not family:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "family query parameter is required",
            },
        )
        return
    record_id = normalize_record_id(_query_value(handler, "record_id"))
    if not record_id:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "record_id query parameter is required",
            },
        )
        return
    try:
        if request_path == "/inspect-assistant-context":
            payload = context.service.inspect_assistant_context(family, record_id).to_dict()
        elif request_path == "/inspect-advisory-output":
            payload = context.service.inspect_advisory_output(family, record_id).to_dict()
        else:
            payload = context.service.render_recommendation_draft(
                family,
                record_id,
            ).to_dict()
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return
    except LookupError as exc:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "message": str(exc),
            },
        )
        return
    _write_json(handler, HTTPStatus.OK, payload)


HTTP_GET_ROUTES: dict[str, GetRouteHandler] = {
    "/healthz": _handle_healthz,
    "/readyz": _handle_readyz,
    "/runtime": _handle_runtime_read,
    "/diagnostics/readiness": _handle_runtime_read,
    "/admin/bootstrap-status": _handle_runtime_read,
    "/inspect-records": _handle_inspect_records,
    "/inspect-reconciliation-status": _handle_inspect_reconciliation_status,
    "/inspect-analyst-queue": _handle_inspect_analyst_queue,
    "/inspect-alert-detail": _handle_inspect_alert_detail,
    "/inspect-case-detail": _handle_inspect_case_detail,
    "/inspect-action-review": _handle_inspect_action_review,
    "/inspect-assistant-context": _handle_assistant_context_family,
    "/inspect-advisory-output": _handle_assistant_context_family,
    "/render-recommendation-draft": _handle_assistant_context_family,
}


def dispatch_get_request(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
) -> None:
    request_path = urlsplit(handler.path).path
    if allowed_roles := protected_read_roles(request_path):
        try:
            authenticate_protected_read(
                service=context.service,
                handler=handler,
                allowed_roles=allowed_roles,
            )
        except PermissionError as exc:
            handler._write_forbidden(str(exc))  # type: ignore[attr-defined]
            return

    route_handler = HTTP_GET_ROUTES.get(request_path)
    if route_handler is None:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "path": request_path,
            },
        )
        return
    route_handler(handler, context, None)


def _handle_promote_alert_to_case(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        promoted_case = context.service.promote_alert_to_case(
            normalize_alert_id(require_json_string(payload, "alert_id")),
            case_id=normalize_optional_string(payload.get("case_id")),
            case_lifecycle_state=require_json_string(payload, "case_lifecycle_state")
            if "case_lifecycle_state" in payload
            else "open",
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(promoted_case))


def _handle_record_case_observation(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "author_identity"),
        )
        observation = context.service.record_case_observation(
            case_id=normalize_case_id(require_json_string(payload, "case_id")),
            author_identity=require_json_string(payload, "author_identity"),
            observed_at=require_json_datetime(payload, "observed_at"),
            scope_statement=require_json_string(payload, "scope_statement"),
            supporting_evidence_ids=require_json_string_sequence(
                payload,
                "supporting_evidence_ids",
            ),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(observation))


def _handle_record_case_lead(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "triage_owner"),
        )
        lead = context.service.record_case_lead(
            case_id=normalize_case_id(require_json_string(payload, "case_id")),
            triage_owner=require_json_string(payload, "triage_owner"),
            triage_rationale=require_json_string(payload, "triage_rationale"),
            observation_id=normalize_optional_string(payload.get("observation_id")),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(lead))


def _handle_record_case_recommendation(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "review_owner"),
        )
        recommendation = context.service.record_case_recommendation(
            case_id=normalize_case_id(require_json_string(payload, "case_id")),
            review_owner=require_json_string(payload, "review_owner"),
            intended_outcome=require_json_string(payload, "intended_outcome"),
            lead_id=normalize_optional_string(payload.get("lead_id")),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(recommendation))


def _handle_record_case_handoff(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "handoff_owner"),
        )
        case_record = context.service.record_case_handoff(
            case_id=normalize_case_id(require_json_string(payload, "case_id")),
            handoff_at=require_json_datetime(payload, "handoff_at"),
            handoff_owner=require_json_string(payload, "handoff_owner"),
            handoff_note=require_json_string(payload, "handoff_note"),
            follow_up_evidence_ids=require_json_string_sequence(
                payload,
                "follow_up_evidence_ids",
            ),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(case_record))


def _handle_record_case_disposition(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        case_record = context.service.record_case_disposition(
            case_id=normalize_case_id(require_json_string(payload, "case_id")),
            disposition=require_json_string(payload, "disposition"),
            rationale=require_json_string(payload, "rationale"),
            recorded_at=require_json_datetime(payload, "recorded_at"),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(case_record))


def _handle_record_action_review_manual_fallback(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "fallback_actor_identity"),
        )
        context_record = context.service.record_action_review_manual_fallback(
            action_request_id=require_json_string(payload, "action_request_id"),
            fallback_at=require_json_datetime(payload, "fallback_at"),
            fallback_actor_identity=require_json_string(
                payload,
                "fallback_actor_identity",
            ),
            authority_boundary=require_json_string(payload, "authority_boundary"),
            reason=require_json_string(payload, "reason"),
            action_taken=require_json_string(payload, "action_taken"),
            verification_evidence_ids=require_json_string_sequence(
                payload,
                "verification_evidence_ids",
            ),
            residual_uncertainty=normalize_optional_string(
                payload.get("residual_uncertainty")
            ),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except PermissionError as exc:
        _write_permission_or_bad_request(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(context_record))


def _handle_record_action_review_escalation_note(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "escalated_by_identity"),
        )
        context_record = context.service.record_action_review_escalation_note(
            action_request_id=require_json_string(payload, "action_request_id"),
            escalated_at=require_json_datetime(payload, "escalated_at"),
            escalated_by_identity=require_json_string(payload, "escalated_by_identity"),
            escalated_to=require_json_string(payload, "escalated_to"),
            note=require_json_string(payload, "note"),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except PermissionError as exc:
        _write_permission_or_bad_request(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(context_record))


def _handle_record_action_approval_decision(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        if getattr(principal, "role", None) != "approver":
            raise PermissionError("approval decisions require approver role authority")
        payload = read_json_request_body(handler)
        approver_identity = require_json_string(payload, "approver_identity")
        authenticated_approver_identity = getattr(principal, "identity", None)
        if authenticated_approver_identity is None:
            raise PermissionError(
                "approval decisions require an authenticated approver identity"
            )
        require_matching_authenticated_identity(
            authenticated_identity=authenticated_approver_identity,
            asserted_identity=approver_identity,
        )
        approval_decision = context.service.record_action_approval_decision(
            action_request_id=require_json_string(payload, "action_request_id"),
            approver_identity=authenticated_approver_identity,
            authenticated_approver_identity=authenticated_approver_identity,
            decision=require_json_string(payload, "decision"),
            decision_rationale=require_json_string(payload, "decision_rationale"),
            decided_at=require_json_datetime(payload, "decided_at"),
            approval_decision_id=normalize_optional_string(
                payload.get("approval_decision_id")
            ),
        )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except PermissionError as exc:
        _write_permission_or_bad_request(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(approval_decision))


def _handle_create_reviewed_action_request(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=require_json_string(payload, "requester_identity"),
        )
        action_type = (
            require_json_string(payload, "action_type")
            if "action_type" in payload
            else "notify_identity_owner"
        )
        if action_type == "notify_identity_owner":
            action_request = context.service.create_reviewed_action_request_from_advisory(
                record_family=require_json_string(payload, "family"),
                record_id=require_json_string(payload, "record_id"),
                requester_identity=require_json_string(payload, "requester_identity"),
                recipient_identity=require_json_string(payload, "recipient_identity"),
                message_intent=require_json_string(payload, "message_intent"),
                escalation_reason=require_json_string(payload, "escalation_reason"),
                expires_at=require_json_datetime(payload, "expires_at"),
                action_request_id=normalize_optional_string(
                    payload.get("action_request_id")
                ),
            )
        elif action_type == "create_tracking_ticket":
            action_request = (
                context.service.create_reviewed_tracking_ticket_request_from_advisory(
                    record_family=require_json_string(payload, "family"),
                    record_id=require_json_string(payload, "record_id"),
                    requester_identity=require_json_string(
                        payload,
                        "requester_identity",
                    ),
                    coordination_reference_id=require_json_string(
                        payload,
                        "coordination_reference_id",
                    ),
                    coordination_target_type=require_json_string(
                        payload,
                        "coordination_target_type",
                    ),
                    ticket_title=require_json_string(payload, "ticket_title"),
                    ticket_description=require_json_string(
                        payload,
                        "ticket_description",
                    ),
                    ticket_severity=require_json_string(payload, "ticket_severity")
                    if "ticket_severity" in payload
                    else "medium",
                    expires_at=require_json_datetime(payload, "expires_at"),
                    action_request_id=normalize_optional_string(
                        payload.get("action_request_id")
                    ),
                )
            )
        else:
            raise ValueError("action_type is outside the reviewed action request scope")
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, ValueError) as exc:
        _write_lookup_or_bad_request(handler, exc)
        return
    _write_json(handler, HTTPStatus.OK, json_ready(action_request))


def _handle_admin_bootstrap_claim(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        admin_identity = require_json_string(payload, "admin_identity")
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=admin_identity,
        )
        context.service.require_admin_bootstrap_token(
            require_json_string(payload, "bootstrap_token")
        )
        bootstrap_reason = require_json_string(payload, "bootstrap_reason")
        service_account_name = require_json_string(payload, "service_account_name")
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, PermissionError, ValueError) as exc:
        _write_permission_or_bad_request(handler, exc)
        return
    _write_json(
        handler,
        HTTPStatus.OK,
        {
            "mode": "admin_bootstrap",
            "admin_identity": admin_identity,
            "service_account_name": service_account_name,
            "bootstrap_reason": bootstrap_reason,
            "access_path": getattr(principal, "access_path", "unknown"),
            "claimed_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def _handle_admin_break_glass_activate(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        payload = read_json_request_body(handler)
        admin_identity = require_json_string(payload, "admin_identity")
        require_reviewed_proxy_identity_match(
            principal=principal,
            asserted_identity=admin_identity,
        )
        context.service.require_break_glass_token(
            require_json_string(payload, "break_glass_token")
        )
        reason = require_json_string(payload, "reason")
        ticket_id = require_json_string(payload, "ticket_id")
        expires_at = require_json_datetime(payload, "expires_at")
        now = datetime.now(timezone.utc)
        if expires_at <= now:
            raise ValueError("expires_at must be in the future")
        if expires_at > now + timedelta(minutes=60):
            raise ValueError(
                "break-glass expiry must be within the reviewed 60 minute window"
            )
    except RequestTooLargeError as exc:
        _handle_request_too_large(handler, exc)
        return
    except (LookupError, PermissionError, ValueError) as exc:
        _write_permission_or_bad_request(handler, exc)
        return
    _write_json(
        handler,
        HTTPStatus.OK,
        {
            "mode": "break_glass",
            "admin_identity": admin_identity,
            "reason": reason,
            "ticket_id": ticket_id,
            "expires_at": expires_at.isoformat(),
            "access_path": getattr(principal, "access_path", "unknown"),
            "activated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def _handle_wazuh_intake(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    principal: object,
) -> None:
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "Content-Length must be an integer",
            },
        )
        return
    if content_length <= 0:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": "request body is required",
            },
        )
        return
    if content_length > MAX_WAZUH_INGEST_BODY_BYTES:
        _write_json(
            handler,
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            {
                "error": "request_too_large",
                "message": "request body exceeds the reviewed Wazuh ingest size limit",
            },
        )
        return

    try:
        raw_payload = handler.rfile.read(content_length).decode("utf-8")
    except UnicodeDecodeError:
        _write_json(
            handler,
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
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": f"request body must be valid JSON: {exc.msg}",
            },
        )
        return

    try:
        ingest_result = context.service.ingest_wazuh_alert(
            raw_alert=alert,
            authorization_header=handler.headers.get("Authorization"),
            forwarded_proto=handler.headers.get("X-Forwarded-Proto"),
            reverse_proxy_secret_header=handler.headers.get("X-AegisOps-Proxy-Secret"),
            peer_addr=handler.client_address[0] if handler.client_address else None,
        )
    except PermissionError as exc:
        _write_json(
            handler,
            HTTPStatus.FORBIDDEN,
            {
                "error": "forbidden",
                "message": str(exc),
            },
        )
        return
    except ValueError as exc:
        _write_json(
            handler,
            HTTPStatus.BAD_REQUEST,
            {
                "error": "invalid_request",
                "message": str(exc),
            },
        )
        return

    _write_json(
        handler,
        HTTPStatus.ACCEPTED,
        {
            "disposition": ingest_result.disposition,
            "finding_id": ingest_result.alert.finding_id,
            "alert": json_ready(ingest_result.alert),
            "reconciliation": json_ready(ingest_result.reconciliation),
        },
    )


HTTP_POST_ROUTES: dict[str, PostRouteHandler] = {
    "/operator/promote-alert-to-case": _handle_promote_alert_to_case,
    "/operator/record-case-observation": _handle_record_case_observation,
    "/operator/record-case-lead": _handle_record_case_lead,
    "/operator/record-case-recommendation": _handle_record_case_recommendation,
    "/operator/record-case-handoff": _handle_record_case_handoff,
    "/operator/record-case-disposition": _handle_record_case_disposition,
    "/operator/record-action-review-manual-fallback": (
        _handle_record_action_review_manual_fallback
    ),
    "/operator/record-action-review-escalation-note": (
        _handle_record_action_review_escalation_note
    ),
    "/operator/record-action-approval-decision": (
        _handle_record_action_approval_decision
    ),
    "/operator/create-reviewed-action-request": _handle_create_reviewed_action_request,
    "/admin/bootstrap/claim": _handle_admin_bootstrap_claim,
    "/admin/break-glass/activate": _handle_admin_break_glass_activate,
    "/intake/wazuh": _handle_wazuh_intake,
}


def dispatch_post_request(
    handler: BaseHTTPRequestHandler,
    context: HttpSurfaceContext,
    *,
    require_loopback_operator_request_fn: Callable[
        [BaseHTTPRequestHandler],
        None,
    ] = require_loopback_operator_request,
) -> None:
    request_path = urlsplit(handler.path).path
    try:
        principal = authenticate_protected_write(
            service=context.service,
            handler=handler,
            request_path=request_path,
            require_loopback_operator_request_fn=require_loopback_operator_request_fn,
        )
    except PermissionError as exc:
        handler._write_forbidden(str(exc))  # type: ignore[attr-defined]
        return

    route_handler = HTTP_POST_ROUTES.get(request_path)
    if route_handler is None:
        _write_json(
            handler,
            HTTPStatus.NOT_FOUND,
            {
                "error": "not_found",
                "path": request_path,
            },
        )
        return
    route_handler(handler, context, principal)


def build_handler_class(
    *,
    service: AegisOpsControlPlaneService,
    runtime_snapshot: dict[str, object],
    stderr: TextIO,
    require_loopback_operator_request_fn=require_loopback_operator_request,
) -> type[BaseHTTPRequestHandler]:
    context = HttpSurfaceContext(
        service=service,
        runtime_snapshot=runtime_snapshot,
    )

    class RequestHandler(BaseHTTPRequestHandler):
        server_version = "AegisOpsControlPlane/1.0"

        def _write_forbidden(self, message: str) -> None:
            self._write_json(
                HTTPStatus.FORBIDDEN,
                {
                    "error": "forbidden",
                    "message": message,
                },
            )

        def _require_authenticated_surface_access(
            self,
            *,
            allowed_roles: tuple[str, ...],
        ) -> object:
            return authenticate_protected_read(
                service=service,
                handler=self,
                allowed_roles=allowed_roles,
            )

        def do_GET(self) -> None:  # noqa: N802
            dispatch_get_request(self, context)

        def do_POST(self) -> None:  # noqa: N802
            dispatch_post_request(
                self,
                context,
                require_loopback_operator_request_fn=require_loopback_operator_request_fn,
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

        def _write_lookup_or_bad_request(self, exc: LookupError | ValueError) -> None:
            status = (
                HTTPStatus.NOT_FOUND
                if isinstance(exc, LookupError)
                else HTTPStatus.BAD_REQUEST
            )
            self._write_json(
                status,
                {
                    "error": "not_found" if status == HTTPStatus.NOT_FOUND else "invalid_request",
                    "message": str(exc),
                },
            )

        def _write_permission_or_bad_request(
            self,
            exc: LookupError | PermissionError | ValueError,
        ) -> None:
            status = (
                HTTPStatus.FORBIDDEN
                if isinstance(exc, PermissionError)
                else HTTPStatus.BAD_REQUEST
            )
            self._write_json(
                status,
                {
                    "error": "forbidden" if status == HTTPStatus.FORBIDDEN else "invalid_request",
                    "message": str(exc),
                },
            )

        def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return RequestHandler


def run_control_plane_service(
    service: AegisOpsControlPlaneService,
    *,
    stderr: TextIO | None = None,
    server_class: type[ThreadingHTTPServer] = ThreadingHTTPServer,
    require_loopback_operator_request_fn=require_loopback_operator_request,
) -> int:
    service.validate_wazuh_ingest_runtime()
    service.validate_protected_surface_runtime()
    runtime_snapshot = service.describe_runtime().to_dict()
    stderr = stderr or sys.stderr
    handler_class = build_handler_class(
        service=service,
        runtime_snapshot=runtime_snapshot,
        stderr=stderr,
        require_loopback_operator_request_fn=require_loopback_operator_request_fn,
    )
    server = server_class(
        (str(runtime_snapshot["bind_host"]), int(runtime_snapshot["bind_port"])),
        handler_class,
    )

    try:
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
