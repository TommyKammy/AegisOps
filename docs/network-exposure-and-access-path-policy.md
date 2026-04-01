# AegisOps Network Exposure and Access Path Policy

This document defines the approved network exposure boundaries and access paths for AegisOps services.

It supplements the networking rules in `docs/requirements-baseline.md` and records the expected access model for reviewers and future implementation work.

This document defines policy only and does not change runtime networking.

## 1. Purpose

The network policy exists to make approved service exposure explicit before runtime implementation work expands access.

It defines:

- the approved reverse proxy access path for user-facing access,
- which internal services may or may not be exposed directly,
- the minimum protection expected for webhook endpoints,
- the approved administrative access expectations, and
- the review rule for outbound dependencies.

## 2. Approved Reverse Proxy Access Model

All user-facing UI access must traverse the approved reverse proxy.

Policy rules:

- The reverse proxy is the approved ingress point for AegisOps user interfaces.
- TLS termination for user-facing access must occur at the approved reverse proxy or an equivalently approved access layer.
- OpenSearch Dashboards, n8n UI, and any future user-facing web interface must not be published as independently exposed front doors without explicit approval.
- Access controls, logging expectations, and future hardening assumptions should be anchored to this ingress model rather than to direct service exposure.

## 3. Internal Service Exposure Policy

Direct exposure of internal service ports is prohibited unless explicitly approved through ADR or equivalent architecture approval.

Internal services must bind only to private or otherwise approved internal interfaces.

Policy rules:

- OpenSearch cluster interfaces, PostgreSQL, Redis, ingest services, and similar backend components are internal services by default.
- Direct unaudited publication of service ports to general user networks or the public internet is not approved.
- Temporary troubleshooting access, if ever required, must be controlled, documented, and removed after the approved administrative activity is complete.
- Network exposure changes must remain reviewable as explicit configuration rather than hidden convenience defaults.

## 4. Webhook Protection Policy

Webhook endpoints must require an authentication or integrity control such as a token, signature, or equivalent approved mechanism.

Policy rules:

- Unauthenticated webhook endpoints are not an approved default for AegisOps.
- Webhook protection must be documented alongside the contract or integration that depends on it.
- A webhook must not be treated as trusted solely because it originates from an internal network location.
- Any exception to authenticated or integrity-protected webhook handling requires explicit approval and risk documentation.

## 5. Administrative Access Path Policy

Administrative access must use documented approved paths rather than ad-hoc direct exposure of product service ports.

Policy rules:

- Administrative SSH or console access must be limited to approved operator paths and management networks.
- Administrative use of product UIs must still follow the reverse proxy model unless a separately approved management path exists.
- Port-forwarding, temporary firewall openings, or direct service publication must not become the de facto operations model.
- Administrative paths must remain attributable, reviewable, and consistent with the auditability expectations in the baseline.

## 6. Outbound Dependency Review Rule

Any new always-on outbound dependency must be documented and reviewed for both security and operational impact before adoption.

Policy rules:

- External API calls, SaaS callbacks, update channels, and similar outbound integrations must be identified before they become required runtime dependencies.
- Reviews must consider business continuity, failure modes, data handling, and least-privilege network posture.
- Deny-by-default remains the expected posture for outbound internet access unless an approved need is documented.
- This rule governs approval and documentation only; it does not itself authorize new network egress.
