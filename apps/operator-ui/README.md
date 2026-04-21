# Operator UI

This workspace introduces the reviewed operator-facing browser shell for AegisOps.

It is intentionally narrow:

- React-Admin provides the protected layout, navigation skeleton, and session-aware shell.
- The browser consumes backend-reviewed session state only.
- Read-only placeholder pages exist so later adapter and page issues can land without replacing the auth boundary.
- No write-capable flows, optimistic mutations, or UI-owned role authority are introduced here.

## Local OIDC wiring

The shell expects the reviewed reverse-proxy and backend session contract to provide these routes:

- `VITE_OPERATOR_SESSION_PATH` for the normalized operator session payload. Default: `/api/operator/session`
- `VITE_OPERATOR_LOGIN_PATH` for the reviewed OIDC sign-in entrypoint. Default: `/auth/oidc/login`
- `VITE_OPERATOR_LOGOUT_PATH` for backend session revocation. Default: `/api/operator/logout`

Environment overrides are optional. The frontend fails closed if the session payload is missing the reviewed provider, subject, identity, or role claims.

## Validation and mock strategy

The Vitest suite uses mocked `fetch` responses instead of placeholder credentials or fake tokens.

- `401` from the session endpoint proves protected routes redirect to the reviewed login path.
- `200` with unsupported roles proves the shell rejects unauthorized sessions and routes to the forbidden view.
- Login and logout coverage asserts redirect and backend-session calls without bypassing the reviewed boundary.
