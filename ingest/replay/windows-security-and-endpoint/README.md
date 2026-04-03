# Windows Security and Endpoint Replay Fixtures

These fixtures are review artifacts only.

The normal fixture set preserves representative success-path records for the initial Phase 6 Windows use cases.

The edge fixture set preserves records with missing actor context or timestamp caveats that future parser validation must handle explicitly.

All fixtures in this directory are synthetic or redacted review examples and are not approvals for live source onboarding.

Directory layout:

| Path | Purpose |
| ---- | ------- |
| `raw/` | Source-shaped Windows event references used to review event-channel provenance, source field names, and redaction assumptions. |
| `normalized/` | Replay-oriented normalized records used to validate future parser and mapping behavior against the approved onboarding contract. |

Fixture provenance notes:

- The records are synthetic compositions of Windows administrative-security events chosen for reviewability.
- Host names, account names, domains, and SIDs are intentionally non-production placeholders.
- Timestamp caveats remain explicit in the fixture content and must not be normalized away in future parser work.
