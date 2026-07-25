#!/bin/sh

set -eu

dsn_file="${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE:-}"
if [ -z "${dsn_file}" ] || [ ! -r "${dsn_file}" ]; then
  echo "Phase 67.1 control-plane DSN file is missing or unreadable: ${dsn_file}" >&2
  exit 1
fi

AEGISOPS_CONTROL_PLANE_POSTGRES_DSN="$(cat "${dsn_file}")"
if [ -z "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" ]; then
  echo "Phase 67.1 control-plane DSN file is empty: ${dsn_file}" >&2
  exit 1
fi
export AEGISOPS_CONTROL_PLANE_POSTGRES_DSN
unset AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE

# Let the reviewed first-boot entrypoint apply and prove its Phase 16 migration set,
# then return here instead of starting the server yet.
/opt/aegisops/bin/first-boot-entrypoint.sh /bin/true

migrations_dir="${AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR:-/opt/aegisops/postgres-migrations}"
for migration_path in \
  "${migrations_dir}"/0008_*.sql \
  "${migrations_dir}"/0009_*.sql \
  "${migrations_dir}"/0010_*.sql \
  "${migrations_dir}"/0011_*.sql \
  "${migrations_dir}"/0012_*.sql \
  "${migrations_dir}"/0013_*.sql \
  "${migrations_dir}"/0014_*.sql \
  "${migrations_dir}"/0015_*.sql
do
  if [ ! -f "${migration_path}" ]; then
    echo "Phase 67.1 current-runtime migration is missing: ${migration_path}" >&2
    exit 1
  fi

  migration_name="$(basename "${migration_path}")"
  migration_checksum="$(tr -d '\r' <"${migration_path}" | cksum | awk '{print $1 ":" $2}')"
  recorded_checksum="$(
    psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -tA -v ON_ERROR_STOP=1 \
      -c "SELECT migration_checksum FROM aegisops_control.schema_migration_bootstrap WHERE migration_name = '${migration_name}';" |
      tr -d '[:space:]'
  )"

  if [ -n "${recorded_checksum}" ]; then
    if [ "${recorded_checksum}" != "${migration_checksum}" ]; then
      echo "Phase 67.1 detected migration checksum drift: ${migration_name}" >&2
      exit 1
    fi
    continue
  fi

  psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -v ON_ERROR_STOP=1 \
    -f "${migration_path}" >/dev/null
  psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -v ON_ERROR_STOP=1 \
    -c "INSERT INTO aegisops_control.schema_migration_bootstrap (migration_name, migration_checksum) VALUES ('${migration_name}', '${migration_checksum}');" \
    >/dev/null
done

exec "$@"
