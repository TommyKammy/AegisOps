from __future__ import annotations

import pathlib
import sys


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.service import AuthenticatedRuntimePrincipal


REVIEWED_PROXY_SERVICE_ACCOUNT = "svc-aegisops-proxy-control-plane"
REVIEWED_ANALYST_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="analyst-001",
    role="analyst",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)
REVIEWED_PLATFORM_ADMIN_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="platform-admin-001",
    role="platform_admin",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)

