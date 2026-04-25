#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/operations-zammad-live-pilot-boundary.md"
test_path="${repo_root}/control-plane/tests/test_issue812_zammad_live_pilot_boundary_docs.py"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_regex() {
  local path="$1"
  local regex="$2"
  local description="$3"

  if grep -Eiq -- "${regex}" "${path}"; then
    echo "Forbidden ${description}: ${path}" >&2
    exit 1
  fi
}

require_file "${doc_path}" "Zammad live pilot boundary document"
require_file "${test_path}" "issue 812 Zammad live pilot docs unittest"

required_headings=(
  "# Operations Zammad-First Live Pilot Boundary and Credential Custody"
  "## 1. Purpose"
  "## 2. Pilot Scope and Non-Authority Boundary"
  "## 3. Credential Custody and Rotation"
  "## 4. Endpoint and Proxy Assumptions"
  "## 5. Unavailable and Degraded Operator Behavior"
  "## 6. Verification Expectations"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "Zammad live pilot boundary heading"
done

required_phrases=(
  "Zammad is the only approved live coordination substrate for the first pilot."
  "GLPI remains a documented fallback only after a separate reviewed change rejects Zammad for the pilot."
  "The pilot is link-first and coordination-only."
  "AegisOps remains authoritative for case, action, approval, execution, and reconciliation records."
  "Ticket state, SLA state, comments, assignee, queue, priority, escalation, or closure in Zammad must not become AegisOps case, action, approval, execution, or reconciliation authority."
  "multi-ITSM abstraction"
  "bidirectional sync"
  "ticket-system authority"
  "Zammad live-pilot credentials must resolve only from the reviewed managed-secret boundary."
  "\`AEGISOPS_ZAMMAD_BASE_URL\`"
  "\`AEGISOPS_ZAMMAD_TOKEN_FILE\`"
  "\`AEGISOPS_ZAMMAD_OPENBAO_PATH\`"
  "No Zammad credential, bearer token, API key, session cookie, customer secret, or environment-specific endpoint credential may be committed to Git"
  "Placeholder, sample, fake, TODO, unsigned, empty, stale, or human-mailbox credentials are invalid."
  "Rotation must be documented before pilot activation, after suspected exposure, after custodian or scope change, and after any break-glass use."
  "If the reviewed secret source is unavailable, unreadable, empty, stale, or only placeholder-backed, the pilot remains unavailable and fails closed."
  "Zammad access for the pilot must use the reviewed outbound integration path and the documented endpoint in \`AEGISOPS_ZAMMAD_BASE_URL\`."
  "Operators must not trust raw \`X-Forwarded-*\`, \`Forwarded\`, host, proto, tenant, or user identity hints from Zammad"
  "The AegisOps backend and operator UI must not expose a direct inbound Zammad webhook authority path for this pilot."
  "\`available\`"
  "\`degraded\`"
  "\`unavailable\`"
  "When Zammad is unavailable or credentials fail custody validation, operators may continue AegisOps case review, approval, execution, and reconciliation from AegisOps records."
  "Operators must not infer ticket existence, approval, execution, reconciliation, closure, or customer notification from a missing, stale, unreachable, or mismatched Zammad record."
  "No failed Zammad write, stale read, timeout, proxy failure, auth failure, or degraded ticket payload may create an orphan AegisOps authority record or mark an AegisOps lifecycle step complete."
  "missing credential source, placeholder credential source, unreachable endpoint, stale ticket read, mismatched ticket identifier, and missing explicit AegisOps linkage"
  "bash scripts/verify-zammad-live-pilot-boundary.sh"
  "python3 -m unittest control-plane.tests.test_issue812_zammad_live_pilot_boundary_docs"
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "Zammad live pilot boundary statement"
done

for forbidden in \
  "ticket system is authoritative" \
  "tickets are authoritative" \
  "Zammad is authoritative" \
  "ticket-driven approval is approved" \
  "ticket-driven execution is approved" \
  "bidirectional sync is approved" \
  "multi-ITSM abstraction is approved" \
  "placeholder credentials are valid" \
  "fake credentials are valid" \
  "sample credentials are valid" \
  "use a personal Zammad session" \
  "trust raw forwarded headers"; do
  reject_phrase "${doc_path}" "${forbidden}" "Zammad live pilot boundary statement"
done

reject_regex "${doc_path}" '(^|[^[:alnum:]_./-])(~[/\\]|/Users/[^[:space:])>]+|/home/[^[:space:])>]+|[A-Za-z]:\\Users\\[^[:space:])>]+)' "workstation-local absolute path"

echo "Zammad live pilot boundary document, credential custody posture, and degraded-state expectations are present."
