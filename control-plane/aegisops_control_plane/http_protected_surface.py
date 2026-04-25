from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from typing import Callable

from .entrypoint_support import require_loopback_operator_request
from .service import AegisOpsControlPlaneService


READ_ONLY_PROTECTED_ROLES = ("analyst", "approver", "platform_admin")
PLATFORM_ADMIN_ROLES = ("platform_admin",)
OPERATOR_ANALYST_ROLES = ("analyst",)
OPERATOR_APPROVER_ROLES = ("approver",)

PROTECTED_READ_ROLES_BY_PATH: dict[str, tuple[str, ...]] = {
    "/runtime": PLATFORM_ADMIN_ROLES,
    "/diagnostics/readiness": READ_ONLY_PROTECTED_ROLES,
    "/admin/bootstrap-status": PLATFORM_ADMIN_ROLES,
    "/inspect-records": READ_ONLY_PROTECTED_ROLES,
    "/inspect-reconciliation-status": READ_ONLY_PROTECTED_ROLES,
    "/inspect-analyst-queue": READ_ONLY_PROTECTED_ROLES,
    "/inspect-alert-detail": READ_ONLY_PROTECTED_ROLES,
    "/inspect-case-detail": READ_ONLY_PROTECTED_ROLES,
    "/inspect-action-review": READ_ONLY_PROTECTED_ROLES,
    "/inspect-assistant-context": READ_ONLY_PROTECTED_ROLES,
    "/inspect-advisory-output": READ_ONLY_PROTECTED_ROLES,
    "/render-recommendation-draft": READ_ONLY_PROTECTED_ROLES,
}

OPERATOR_ANALYST_PATHS = {
    "/operator/promote-alert-to-case",
    "/operator/record-case-observation",
    "/operator/record-case-lead",
    "/operator/record-case-recommendation",
    "/operator/record-case-handoff",
    "/operator/record-case-disposition",
    "/operator/record-action-review-manual-fallback",
    "/operator/record-action-review-escalation-note",
    "/operator/create-reviewed-action-request",
}
OPERATOR_APPROVER_PATHS = {
    "/operator/record-action-approval-decision",
}


def protected_read_roles(request_path: str) -> tuple[str, ...] | None:
    return PROTECTED_READ_ROLES_BY_PATH.get(request_path)


def protected_write_roles(request_path: str) -> tuple[str, ...] | None:
    if request_path in OPERATOR_ANALYST_PATHS:
        return OPERATOR_ANALYST_ROLES
    if request_path in OPERATOR_APPROVER_PATHS:
        return OPERATOR_APPROVER_ROLES
    if request_path.startswith("/admin/"):
        return PLATFORM_ADMIN_ROLES
    return None


def authenticate_protected_read(
    *,
    service: AegisOpsControlPlaneService,
    handler: BaseHTTPRequestHandler,
    allowed_roles: tuple[str, ...],
) -> object:
    return _authenticate_protected_surface(
        service=service,
        handler=handler,
        allowed_roles=allowed_roles,
    )


def authenticate_protected_write(
    *,
    service: AegisOpsControlPlaneService,
    handler: BaseHTTPRequestHandler,
    request_path: str,
    require_loopback_operator_request_fn: Callable[
        [BaseHTTPRequestHandler],
        None,
    ] = require_loopback_operator_request,
) -> object | None:
    allowed_roles = protected_write_roles(request_path)
    if allowed_roles is None:
        return None

    if request_path in OPERATOR_ANALYST_PATHS | OPERATOR_APPROVER_PATHS:
        require_loopback_operator_request_fn(handler)

    return _authenticate_protected_surface(
        service=service,
        handler=handler,
        allowed_roles=allowed_roles,
    )


def require_matching_authenticated_identity(
    *,
    authenticated_identity: str | None,
    asserted_identity: str,
) -> None:
    if (authenticated_identity or "").strip() != asserted_identity.strip():
        raise PermissionError(
            "authenticated identity header must match the asserted control-plane identity"
        )


def require_reviewed_proxy_identity_match(
    *,
    principal: object,
    asserted_identity: str,
) -> None:
    if getattr(principal, "access_path", "") != "reviewed_reverse_proxy":
        return
    require_matching_authenticated_identity(
        authenticated_identity=getattr(principal, "identity", None),
        asserted_identity=asserted_identity,
    )


def _authenticate_protected_surface(
    *,
    service: AegisOpsControlPlaneService,
    handler: BaseHTTPRequestHandler,
    allowed_roles: tuple[str, ...],
) -> object:
    return service.authenticate_protected_surface_request(
        peer_addr=handler.client_address[0] if handler.client_address else None,
        forwarded_proto=handler.headers.get("X-Forwarded-Proto"),
        reverse_proxy_secret_header=handler.headers.get("X-AegisOps-Proxy-Secret"),
        proxy_service_account_header=handler.headers.get(
            "X-AegisOps-Proxy-Service-Account"
        ),
        authenticated_identity_provider_header=handler.headers.get(
            "X-AegisOps-Authenticated-IdP"
        ),
        authenticated_subject_header=handler.headers.get(
            "X-AegisOps-Authenticated-Subject"
        ),
        authenticated_identity_header=handler.headers.get(
            "X-AegisOps-Authenticated-Identity"
        ),
        authenticated_role_header=handler.headers.get("X-AegisOps-Authenticated-Role"),
        allowed_roles=allowed_roles,
    )


__all__ = [
    "OPERATOR_ANALYST_PATHS",
    "OPERATOR_APPROVER_PATHS",
    "PROTECTED_READ_ROLES_BY_PATH",
    "READ_ONLY_PROTECTED_ROLES",
    "authenticate_protected_read",
    "authenticate_protected_write",
    "protected_read_roles",
    "protected_write_roles",
    "require_matching_authenticated_identity",
    "require_reviewed_proxy_identity_match",
]
