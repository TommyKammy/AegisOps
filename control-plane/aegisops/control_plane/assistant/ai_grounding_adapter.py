from __future__ import annotations

from datetime import datetime

from .ai_grounding_payload import (
    build_base_payload,
    build_blocked_payload,
    build_fallback_payload,
    build_grounded_payload,
)
from .ai_grounding_prompt_validation import prompt_pressure_flags
from .ai_grounding_validation import (
    _trusted_grounded_at as _validation_trusted_grounded_at,
    _validated_grounding_payload,
)


def build_ai_grounding_adapter(
    *,
    grounding_context_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    validation = _validated_grounding_payload(
        grounding_context_payload,
        trusted_grounded_at=_trusted_grounded_at(),
    )
    base = build_base_payload(
        anchor_id=validation["anchor_id"],
        projections=() if validation["reasons"] else validation["projections"],
    )
    prompt_flags = prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return build_blocked_payload(base, prompt_flags)
    if validation["reasons"]:
        return build_fallback_payload(
            base,
            mode="ai_grounding_untrusted",
            unresolved_reasons=validation["reasons"],
        )
    if ai_enablement_posture == "disabled":
        return build_fallback_payload(
            base,
            mode="ai_disabled",
            unresolved_reasons=("ai_advisory_disabled",),
        )
    if ai_enablement_posture == "degraded":
        return build_fallback_payload(
            base,
            mode="ai_degraded",
            unresolved_reasons=("ai_advisory_degraded",),
        )
    if ai_enablement_posture != "enabled":
        return build_fallback_payload(
            base,
            mode="ai_enablement_untrusted",
            unresolved_reasons=("malformed_ai_enablement_posture",),
        )

    return build_grounded_payload(
        base,
        anchor_id=validation["anchor_id"],
        projections=validation["projections"],
    )


def _trusted_grounded_at() -> datetime:
    return _validation_trusted_grounded_at()
