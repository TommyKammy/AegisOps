#!/usr/bin/env sh

set -eu

# Phase 16 first-boot skeleton only.
# This entrypoint validates the reviewed required bootstrap contract,
# reserves a hook point for migration bootstrap, and then hands off to
# the runtime command. Live health endpoints and production image
# implementation remain out of scope for this repository skeleton.

require_non_empty() {
  var_name="$1"
  var_value="${2:-}"

  if [ -z "${var_value}" ] || [ "${var_value}" = "<set-me>" ]; then
    echo "Missing required first-boot setting: ${var_name}" >&2
    exit 1
  fi
}

require_non_empty "AEGISOPS_CONTROL_PLANE_HOST" "${AEGISOPS_CONTROL_PLANE_HOST:-}"
require_non_empty "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN" "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:-}"

dsn_value="${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:-}"
case "${dsn_value}" in
  postgresql://*|postgres://*)
    ;;
  *)
    echo "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN must be a PostgreSQL DSN for the first-boot skeleton." >&2
    exit 1
    ;;
esac

port_value="${AEGISOPS_CONTROL_PLANE_PORT:-8080}"
case "${port_value}" in
  ''|*[!0-9]*)
    echo "AEGISOPS_CONTROL_PLANE_PORT must be an integer for the first-boot skeleton." >&2
    exit 1
    ;;
esac

# migration bootstrap remains skeletal here: reviewed migrations stay under
# postgres/control-plane/migrations/ and later runtime work must replace this
# placeholder with real forward-only migration execution before readiness is
# allowed to succeed.

# readiness remains a later-phase runtime concern. This skeleton only enforces
# that required bootstrap state exists before the control-plane process starts.

# OpenSearch, n8n, the full analyst-assistant surface, and executor wiring remain deferred.

exec "$@"
