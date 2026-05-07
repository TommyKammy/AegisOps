from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ..runtime.doctor_contract import build_doctor_snapshot

if TYPE_CHECKING:
    from ..service import AegisOpsControlPlaneService


RUNTIME_READ_PATHS = frozenset(
    {
        "/runtime",
        "/diagnostics/readiness",
        "/diagnostics/doctor",
        "/admin/bootstrap-status",
    }
)


def runtime_read_response(
    *,
    service: AegisOpsControlPlaneService,
    request_path: str,
) -> tuple[HTTPStatus, dict[str, object]] | None:
    if request_path == "/runtime":
        return HTTPStatus.OK, service.describe_runtime().to_dict()

    if request_path == "/diagnostics/readiness":
        return HTTPStatus.OK, service.inspect_readiness_diagnostics().to_dict()

    if request_path == "/diagnostics/doctor":
        return HTTPStatus.OK, build_doctor_snapshot(
            config=service._config,
            readiness_payload=service.inspect_readiness_diagnostics().to_dict(),
        ).to_dict()

    if request_path == "/admin/bootstrap-status":
        return HTTPStatus.OK, _admin_bootstrap_status_payload(service)

    return None


def _admin_bootstrap_status_payload(
    service: AegisOpsControlPlaneService,
) -> dict[str, object]:
    return {
        "contract": "reviewed_admin_bootstrap",
        "bootstrap_token_configured": bool(service._config.admin_bootstrap_token.strip()),
        "break_glass_token_configured": bool(service._config.break_glass_token.strip()),
        "protected_surface_proxy_service_account": (
            service._config.protected_surface_proxy_service_account
        ),
        "break_glass_max_ttl_minutes": 60,
    }


__all__ = [
    "RUNTIME_READ_PATHS",
    "runtime_read_response",
]
