#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-58-6-support-bundle-redaction-contract.md"

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 58.6 support bundle redaction contract: ${doc_path}" >&2
  exit 1
fi

doc_text="$(<"${doc_path}")"

required_phrases=(
  "# Phase 58.6 Support Bundle And Redaction Contract"
  "Phase 58.6 defines the support bundle contract for customer-safe diagnostic"
  "A support bundle is redacted diagnostic evidence only."
  "Support bundles cannot approve, execute, reconcile, release, close, restore, or"
  "replace authoritative AegisOps records."
  "No remote upload service, background collector, direct database export,"
  "- Contract verifier: \`bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh\`."
  "- Focused verifier regression: \`bash scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh\`."
  "- Path hygiene: \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "- Issue lint: \`node <codex-supervisor-root>/dist/index.js issue-lint 1241 --config <supervisor-config-path>\`."
  "| \`environment_class\` | Reviewed profile, deployment class, or lab class only; no tenant inference from path shape, ticket title, or host name. |"
  "| \`component_versions\` | AegisOps-owned component and package versions after reviewed redaction; no floating \`latest\` claims as evidence. |"
  "| \`doctor_summary\` | Phase 58.1 doctor output or summarized health state after redaction; not authoritative workflow or release truth. |"
  "| \`backup_restore_references\` | Links to Phase 58.3 backup custody evidence and Phase 58.4 restore dry-run evidence; not raw backup payloads. |"
  "| \`upgrade_rollback_references\` | Links to Phase 58.5 upgrade and rollback planning evidence; not proof of live upgrade or rollback completion. |"
  "| \`known_limitations\` | Reviewed limitations, non-goals, unsafe states, retained manual steps, and owner references. |"
  "| \`reproduction_steps\` | Operator-reviewed reproduction steps with customer names, private payloads, tickets, credentials, and workstation paths removed. |"
  "| \`bounded_metadata\` | Sanitized timestamps, record counts, schema versions, source families, and evidence identifiers directly linked to authoritative records. |"
  "| \`redaction_manifest\` | Redaction families applied, scan result, retained limitations, and explicit subordinate-evidence boundary. |"
  "| \`secrets\` | Reject or redact API keys, shared secrets, passwords, private keys, signing keys, bootstrap tokens, session material, and env-secret values. |"
  "| \`workstation_local_paths\` | Reject or redact macOS, Linux, and Windows user-profile paths; use repo-relative paths, documented env vars, or placeholders. |"
  "| \`customer_private_raw_payloads\` | Reject raw alerts, raw logs, raw tickets, raw webhook bodies, raw event payloads, and customer-private source payloads by default. |"
  "| \`ticket_private_content\` | Reject private ticket comments, customer names, customer screenshots, chat excerpts, support notes, and operator-only escalation text. |"
  "| \`tokens_and_headers\` | Reject authorization headers, cookies, bearer tokens, forwarded headers, raw host or tenant hints, and client-supplied identity fields. |"
  "| \`cert_material\` | Reject certificates, private keys, CSRs, keystores, truststores, and inline PEM blocks unless replaced with reviewed fingerprints. |"
  "| \`raw_credentials\` | Reject usernames paired with passwords, connection strings containing credentials, service-account secrets, and placeholder credentials. |"
  "| \`authority_claims\` | Reject bundle-as-workflow-truth, support-as-operator, support-as-approver, support-as-release-gate, or support-as-restore-truth claims. |"
  "| \`secret_values\` | Replace secret-looking values with \`[REDACTED:secret]\` and fail closed when the value remains recoverable in output. |"
  "| \`workstation_paths\` | Replace user-home absolute paths with \`[REDACTED:workstation-path]\`; retain only repo-relative paths or placeholders. |"
  "| \`private_payloads\` | Summarize payload type, source family, authoritative record link, and bounded counts; do not retain raw payload bodies by default. |"
  "| \`ticket_private_content\` | Replace private ticket text with \`[REDACTED:ticket-private-content]\` and retain only public ticket identifiers or reviewed references. |"
  "| \`tokens_and_headers\` | Remove authorization, cookie, forwarded, tenant, host, proto, and user-id headers unless a trusted boundary normalized them first. |"
  "| \`certs_and_keys\` | Replace cert and key material with reviewed fingerprints, expiry metadata, issuer class, or custody references. |"
  "| \`credentials\` | Remove usernames paired with passwords, credential-bearing URLs, DSNs, and placeholder credentials from retained output. |"
  "| \`customer_identifiers\` | Replace customer names, tenant names, account names, private host names, email addresses, and screenshots with reviewed placeholders. |"
  "| \`secret_leakage\` | Bundle output contains secret-looking values, tokens, auth headers, cookies, private keys, cert material, credential-bearing DSNs, or placeholder credentials. | Reject the bundle before retention or sharing. |"
  "| \`workstation_path_leakage\` | Bundle output contains macOS, Linux, or Windows workstation-local user-profile paths. | Reject the bundle and require repo-relative paths, env vars, or placeholders. |"
  "| \`private_payload_leakage\` | Bundle output contains raw customer payloads, raw logs, raw tickets, raw webhook bodies, screenshots, or private support notes. | Reject the bundle and retain bounded summaries only. |"
  "| \`authority_expansion\` | Bundle output is presented as workflow, release, gate, restore, audit, closeout, approval, execution, reconciliation, or operator truth. | Reject the bundle and preserve authoritative AegisOps record-chain truth. |"
  "| \`support_operator_expansion\` | Support collaborator access is treated as operator, approver, administrator, substrate operator, or direct backend authority. | Reject the bundle and require a reviewed authority contract. |"
  "| \`missing_redaction_manifest\` | Redaction families, scan result, subordinate boundary, or retained limitations are absent. | Reject the bundle until the manifest is complete. |"
  "| \`mixed_snapshot_bundle\` | Bundle assembles records from different committed snapshots without detecting or rejecting mixed-state evidence. | Reject the bundle before retention or sharing. |"
  "Support bundles are subordinate diagnostic evidence."
  "Support bundle validation cannot approve remediation, execute actions, reconcile"
  "When provenance, record linkage, snapshot consistency, redaction status,"
  "A retained support bundle must include a redaction manifest, scan result,"
  "secret-looking value scanning, workstation-local path scanning,"
  "- secret leakage;"
  "- workstation-local path leakage;"
  "- customer-private raw payload leakage;"
  "- ticket-private content leakage;"
  "- token and header leakage;"
  "- cert material leakage;"
  "- raw credential leakage;"
  "- missing redaction manifest;"
  "- support bundle as workflow, release, gate, restore, audit, or closeout truth;"
  "- support operator authority expansion;"
  "- mixed-snapshot bundle claims."
  "Phase 58.6 does not implement remote support upload, support portal workflow,"
  "support bundle output as authoritative workflow truth."
  "- \`bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh\`"
  "- \`bash scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh\`"
  "- \`bash scripts/verify-publishable-path-hygiene.sh\`"
  "- \`node <codex-supervisor-root>/dist/index.js issue-lint 1241 --config <supervisor-config-path>\`"
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_text}"; then
    echo "Missing Phase 58.6 support bundle redaction contract statement: ${phrase}" >&2
    exit 1
  fi
done

for forbidden in \
  "support bundle is workflow truth" \
  "support bundle is release truth" \
  "support bundle is gate truth" \
  "support bundle is restore truth" \
  "support bundle is audit truth" \
  "support bundle is closeout truth" \
  "support bundle output is authoritative workflow truth" \
  "support collaborator is an operator" \
  "support collaborator can approve actions" \
  "support collaborator can execute actions" \
  "support collaborator can reconcile actions" \
  "support collaborator can close cases" \
  "raw customer payloads are included by default" \
  "private ticket contents are included by default" \
  "authorization headers are retained" \
  "cert material is retained" \
  "raw credentials are retained" \
  "remote support upload is implemented" \
  "support portal workflow is implemented" \
  "direct backend access for support is implemented"; do
  if grep -Fqi -- "${forbidden}" <<<"${doc_text}"; then
    echo "Forbidden Phase 58.6 support bundle redaction contract claim: ${forbidden}" >&2
    exit 1
  fi
done

local_path_prefix="(^|[[:space:]\`\"'(<])"
unix_home_pattern="${local_path_prefix}/(Users|home)/"
windows_home_pattern="${local_path_prefix}[A-Za-z]:[\\\\/][Uu][Ss][Ee][Rr][Ss][\\\\/]"
file_uri_home_pattern="file://([^[:space:]\`\"'()<>]*/)?(Users|home)/"

if grep -Eiq "${unix_home_pattern}|${windows_home_pattern}|${file_uri_home_pattern}" <<<"${doc_text}"; then
  echo "Forbidden Phase 58.6 support bundle redaction contract claim: workstation-local path" >&2
  exit 1
fi

if DOC_TEXT="${doc_text}" python3 - <<'PY'
import os
import re
import sys

text = os.environ["DOC_TEXT"]
patterns = (
    re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9_+./=-]{12,}"),
    re.compile(
        r"""(?ix)
        (
            authorization|bearer|cookie|password|passwd|secret|
            api[_ -]?key|token|private[_ -]?key|client[_ -]?secret
        )
        \s*[:=]\s*
        ["']?[A-Za-z0-9_+./=-]{4,}
        """
    ),
    re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@]+:[^\s@]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"-----BEGIN CERTIFICATE-----"),
)

sys.exit(0 if any(pattern.search(text) for pattern in patterns) else 1)
PY
then
  echo "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value" >&2
  exit 1
fi

echo "Phase 58.6 support bundle redaction contract defines allowed contents, forbidden contents, redaction families, and subordinate authority boundaries."
