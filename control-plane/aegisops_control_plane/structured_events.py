from __future__ import annotations

import ipaddress
from typing import Mapping

from .service_snapshots import _json_ready


def _classify_network_identifier(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "missing"
    try:
        peer_ip = ipaddress.ip_address(value.strip())
    except ValueError:
        return "invalid"
    if peer_ip.is_loopback:
        return "loopback"
    if peer_ip.is_private:
        return "private"
    if peer_ip.is_global:
        return "public"
    return "special"


def _count_identity_values(value: object) -> int:
    if isinstance(value, (tuple, list)):
        return sum(
            1 for item in value if isinstance(item, str) and item.strip()
        )
    if isinstance(value, str) and value.strip():
        return 1
    return 0


def sanitize_structured_event_fields(
    fields: Mapping[str, object],
) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in fields.items():
        normalized_key = str(key)
        if normalized_key == "peer_addr":
            sanitized["peer_addr_class"] = _classify_network_identifier(value)
            continue
        if normalized_key.endswith("_identity"):
            sanitized[f"{normalized_key}_present"] = (
                _count_identity_values(value) > 0
            )
            continue
        if normalized_key.endswith("_identities"):
            sanitized[f"{normalized_key}_count"] = _count_identity_values(value)
            continue
        sanitized[normalized_key] = _json_ready(value)
    return sanitized


__all__ = [
    "sanitize_structured_event_fields",
]
