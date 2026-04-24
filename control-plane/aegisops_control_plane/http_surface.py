from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from typing import TextIO
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
)
from .service import AegisOpsControlPlaneService


def build_handler_class(
    *,
    service: AegisOpsControlPlaneService,
    runtime_snapshot: dict[str, object],
    stderr: TextIO,
    require_loopback_operator_request_fn=require_loopback_operator_request,
) -> type[BaseHTTPRequestHandler]:
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

        @staticmethod
        def _require_matching_identity(
            authenticated_identity: str,
            asserted_identity: str,
        ) -> None:
            if authenticated_identity.strip() != asserted_identity.strip():
                raise PermissionError(
                    "authenticated identity header must match the asserted control-plane identity"
                )

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

            if allowed_roles := protected_read_roles(request_path):
                try:
                    self._require_authenticated_surface_access(
                        allowed_roles=allowed_roles,
                    )
                except PermissionError as exc:
                    self._write_forbidden(str(exc))
                    return

            if request_path == "/runtime":
                self._write_json(HTTPStatus.OK, service.describe_runtime().to_dict())
                return

            if request_path == "/diagnostics/readiness":
                self._write_json(
                    HTTPStatus.OK,
                    service.inspect_readiness_diagnostics().to_dict(),
                )
                return

            if request_path == "/admin/bootstrap-status":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "contract": "reviewed_admin_bootstrap",
                        "bootstrap_token_configured": bool(
                            service._config.admin_bootstrap_token.strip()
                        ),
                        "break_glass_token_configured": bool(
                            service._config.break_glass_token.strip()
                        ),
                        "protected_surface_proxy_service_account": (
                            service._config.protected_surface_proxy_service_account
                        ),
                        "break_glass_max_ttl_minutes": 60,
                    },
                )
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
                alert_id = normalize_alert_id(
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
                case_id = normalize_case_id(
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

            if request_path == "/inspect-action-review":
                action_request_id = normalize_record_id(
                    parse_qs(request_target.query).get("action_request_id", [""])[0]
                )
                if not action_request_id:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "action_request_id query parameter is required",
                        },
                    )
                    return
                try:
                    payload = service.inspect_action_review_detail(action_request_id).to_dict()
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
                family = normalize_record_family(
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
                record_id = normalize_record_id(
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

            try:
                principal = authenticate_protected_write(
                    service=service,
                    handler=self,
                    request_path=request_path,
                    require_loopback_operator_request_fn=(
                        require_loopback_operator_request_fn
                    ),
                )
            except PermissionError as exc:
                self._write_forbidden(str(exc))
                return

            if request_path == "/operator/promote-alert-to-case":
                try:
                    payload = read_json_request_body(self)
                    promoted_case = service.promote_alert_to_case(
                        normalize_alert_id(require_json_string(payload, "alert_id")),
                        case_id=normalize_optional_string(payload.get("case_id")),
                        case_lifecycle_state=require_json_string(
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
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(promoted_case))
                return

            if request_path == "/operator/record-case-observation":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "author_identity"),
                        )
                    observation = service.record_case_observation(
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
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(observation))
                return

            if request_path == "/operator/record-case-lead":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "triage_owner"),
                        )
                    lead = service.record_case_lead(
                        case_id=normalize_case_id(require_json_string(payload, "case_id")),
                        triage_owner=require_json_string(payload, "triage_owner"),
                        triage_rationale=require_json_string(payload, "triage_rationale"),
                        observation_id=normalize_optional_string(
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
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(lead))
                return

            if request_path == "/operator/record-case-recommendation":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "review_owner"),
                        )
                    recommendation = service.record_case_recommendation(
                        case_id=normalize_case_id(require_json_string(payload, "case_id")),
                        review_owner=require_json_string(payload, "review_owner"),
                        intended_outcome=require_json_string(payload, "intended_outcome"),
                        lead_id=normalize_optional_string(payload.get("lead_id")),
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
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(recommendation))
                return

            if request_path == "/operator/record-case-handoff":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "handoff_owner"),
                        )
                    case_record = service.record_case_handoff(
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
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, ValueError) as exc:
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(case_record))
                return

            if request_path == "/operator/record-case-disposition":
                try:
                    payload = read_json_request_body(self)
                    case_record = service.record_case_disposition(
                        case_id=normalize_case_id(require_json_string(payload, "case_id")),
                        disposition=require_json_string(payload, "disposition"),
                        rationale=require_json_string(payload, "rationale"),
                        recorded_at=require_json_datetime(payload, "recorded_at"),
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
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(case_record))
                return

            if request_path == "/operator/record-action-review-manual-fallback":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "fallback_actor_identity"),
                        )
                    context_record = service.record_action_review_manual_fallback(
                        action_request_id=require_json_string(payload, "action_request_id"),
                        fallback_at=require_json_datetime(payload, "fallback_at"),
                        fallback_actor_identity=require_json_string(
                            payload,
                            "fallback_actor_identity",
                        ),
                        authority_boundary=require_json_string(
                            payload,
                            "authority_boundary",
                        ),
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
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except PermissionError as exc:
                    self._write_permission_or_bad_request(exc)
                    return
                except (LookupError, ValueError) as exc:
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(context_record))
                return

            if request_path == "/operator/record-action-review-escalation-note":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "escalated_by_identity"),
                        )
                    context_record = service.record_action_review_escalation_note(
                        action_request_id=require_json_string(payload, "action_request_id"),
                        escalated_at=require_json_datetime(payload, "escalated_at"),
                        escalated_by_identity=require_json_string(
                            payload,
                            "escalated_by_identity",
                        ),
                        escalated_to=require_json_string(payload, "escalated_to"),
                        note=require_json_string(payload, "note"),
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
                except PermissionError as exc:
                    self._write_permission_or_bad_request(exc)
                    return
                except (LookupError, ValueError) as exc:
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(context_record))
                return

            if request_path == "/operator/record-action-approval-decision":
                try:
                    if getattr(principal, "role", None) != "approver":
                        raise PermissionError(
                            "approval decisions require approver role authority"
                        )
                    payload = read_json_request_body(self)
                    approver_identity = require_json_string(
                        payload,
                        "approver_identity",
                    )
                    authenticated_approver_identity = getattr(
                        principal,
                        "identity",
                        None,
                    )
                    if authenticated_approver_identity is None:
                        raise PermissionError(
                            "approval decisions require an authenticated approver identity"
                        )
                    self._require_matching_identity(
                        authenticated_approver_identity,
                        approver_identity,
                    )
                    approval_decision = service.record_action_approval_decision(
                        action_request_id=require_json_string(payload, "action_request_id"),
                        approver_identity=authenticated_approver_identity,
                        authenticated_approver_identity=authenticated_approver_identity,
                        decision=require_json_string(payload, "decision"),
                        decision_rationale=require_json_string(
                            payload,
                            "decision_rationale",
                        ),
                        decided_at=require_json_datetime(payload, "decided_at"),
                        approval_decision_id=normalize_optional_string(
                            payload.get("approval_decision_id")
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
                except PermissionError as exc:
                    self._write_permission_or_bad_request(exc)
                    return
                except (LookupError, ValueError) as exc:
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(approval_decision))
                return

            if request_path == "/operator/create-reviewed-action-request":
                try:
                    payload = read_json_request_body(self)
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(
                            principal.identity,
                            require_json_string(payload, "requester_identity"),
                        )
                    action_type = (
                        require_json_string(payload, "action_type")
                        if "action_type" in payload
                        else "notify_identity_owner"
                    )
                    if action_type == "notify_identity_owner":
                        action_request = service.create_reviewed_action_request_from_advisory(
                            record_family=require_json_string(payload, "family"),
                            record_id=require_json_string(payload, "record_id"),
                            requester_identity=require_json_string(
                                payload,
                                "requester_identity",
                            ),
                            recipient_identity=require_json_string(
                                payload,
                                "recipient_identity",
                            ),
                            message_intent=require_json_string(payload, "message_intent"),
                            escalation_reason=require_json_string(
                                payload,
                                "escalation_reason",
                            ),
                            expires_at=require_json_datetime(payload, "expires_at"),
                            action_request_id=normalize_optional_string(
                                payload.get("action_request_id")
                            ),
                        )
                    elif action_type == "create_tracking_ticket":
                        action_request = service.create_reviewed_tracking_ticket_request_from_advisory(
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
                            ticket_severity=(
                                require_json_string(payload, "ticket_severity")
                                if "ticket_severity" in payload
                                else "medium"
                            ),
                            expires_at=require_json_datetime(payload, "expires_at"),
                            action_request_id=normalize_optional_string(
                                payload.get("action_request_id")
                            ),
                        )
                    else:
                        raise ValueError(
                            "action_type is outside the reviewed action request scope"
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
                    self._write_lookup_or_bad_request(exc)
                    return
                self._write_json(HTTPStatus.OK, json_ready(action_request))
                return

            if request_path == "/admin/bootstrap/claim":
                try:
                    payload = read_json_request_body(self)
                    admin_identity = require_json_string(payload, "admin_identity")
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(principal.identity, admin_identity)
                    service.require_admin_bootstrap_token(
                        require_json_string(payload, "bootstrap_token")
                    )
                    bootstrap_reason = require_json_string(payload, "bootstrap_reason")
                    service_account_name = require_json_string(
                        payload,
                        "service_account_name",
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
                except (LookupError, PermissionError, ValueError) as exc:
                    self._write_permission_or_bad_request(exc)
                    return
                self._write_json(
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
                return

            if request_path == "/admin/break-glass/activate":
                try:
                    payload = read_json_request_body(self)
                    admin_identity = require_json_string(payload, "admin_identity")
                    if getattr(principal, "access_path", "") == "reviewed_reverse_proxy":
                        self._require_matching_identity(principal.identity, admin_identity)
                    service.require_break_glass_token(
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
                    self._write_json(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        {
                            "error": "request_too_large",
                            "message": str(exc),
                        },
                    )
                    return
                except (LookupError, PermissionError, ValueError) as exc:
                    self._write_permission_or_bad_request(exc)
                    return
                self._write_json(
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
                    "alert": json_ready(ingest_result.alert),
                    "reconciliation": json_ready(ingest_result.reconciliation),
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
