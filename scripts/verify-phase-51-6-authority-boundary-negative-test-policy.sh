#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 51.6 Authority-Boundary Negative-Test Policy"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Required Negative-Test Classes"
  "## 4. Later-Issue Citation Rule"
  "## 5. Forbidden Shortcuts"
  "## 6. Validation"
  "## 7. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Related Issues**: #1041, #1042, #1047"
  "This policy defines cross-phase negative-test expectations only. It does not implement AI, Wazuh, Shuffle, ticket, evidence, browser, UI, downstream receipt, demo-data, SIEM, SOAR, installer, release, or runtime behavior."
  "Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence, recommendations, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state."
  "Every subordinate surface must fail closed when asked to become approval, execution, reconciliation, case closure, source truth, gate truth, or production truth."
  "The subordinate surfaces covered by this policy are AI, Wazuh, Shuffle, tickets, endpoint evidence, network evidence, external evidence systems, browser state, UI cache, downstream receipts, and demo data."
  "Missing, malformed, placeholder-backed, mixed-snapshot, unsigned, unbound, stale, inferred, or partially trusted subordinate signals must reject the path, keep the guard in place, or surface an explicit prerequisite. They must not silently succeed, degrade to allow, or substitute guessed context."
  "Later breadth issues must include the narrowest negative test at the real enforcement boundary for each subordinate surface they touch."
  "| AI | AI output, tool suggestions, summaries, or recommendations are presented as approval, execution, reconciliation, case closure, detector activation, or source truth. | Reject the shortcut and require an explicit AegisOps record, human decision, or reviewed prerequisite. |"
  "| Wazuh | Wazuh alert, rule, manager, decoder, status, or timestamp state is presented as AegisOps alert, case, evidence, reconciliation, release, or gate truth without explicit admission and linkage. | Reject the shortcut and require an admitted AegisOps record linked to the Wazuh signal. |"
  "| Shuffle | Shuffle workflow success, failure, retry, payload, or callback state is presented as AegisOps execution receipt, reconciliation, case closure, release, or gate truth without AegisOps approval, action intent, receipt, and reconciliation records. | Reject the shortcut and keep reconciliation open or mismatched until the AegisOps record chain closes it. |"
  "| Tickets | Ticket open, closed, escalated, assigned, commented, or SLA state is presented as AegisOps case, approval, reconciliation, limitation, release, or gate truth. | Reject the shortcut and treat the ticket as coordination context linked to an authoritative AegisOps record. |"
  "| Endpoint evidence | Endpoint evidence, host facts, agent state, file paths, process data, or local collector status is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |"
  "| Network evidence | Network evidence, flow state, packet metadata, proxy logs, Suricata output, or external telemetry is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |"
  "| Evidence systems | External evidence-system status, retention, export, report, or custody text is presented as AegisOps evidence, release, gate, or production truth without explicit binding to the AegisOps evidence record. | Reject the shortcut and repair or refuse the projection instead of redefining truth around the external system. |"
  "| Browser state | Browser URL, route state, local storage, session storage, cookie state, DOM text, or client navigation state is presented as AegisOps workflow truth. | Reject the shortcut and reload or recalculate from authoritative AegisOps records. |"
  "| UI cache | Client cache, optimistic update, badge, counter, detail DTO, projection, or stale refresh result is presented as AegisOps workflow truth. | Reject the shortcut and repair the derived surface from authoritative AegisOps records. |"
  "| Downstream receipts | Downstream receipt, webhook acknowledgement, adapter response, export receipt, support bundle receipt, or delivery receipt is presented as AegisOps reconciliation or closeout truth without AegisOps reconciliation. | Reject the shortcut and require the AegisOps reconciliation record or mismatch path. |"
  "| Demo data | Seed data, sample fixture, demo persona, synthetic event, example receipt, fake secret, TODO value, or placeholder credential is presented as production truth. | Reject the shortcut and require trusted production binding, real credential custody, or an explicit demo-only refusal. |"
  "Any later issue that adds breadth for AI, Wazuh, Shuffle, tickets, endpoint evidence, network evidence, external evidence systems, browser state, UI cache, downstream receipts, or demo data must cite this policy and name the exact negative-test class it preserves."
  "Phase 54 Wazuh signal intake must cite this policy for Wazuh status shortcut rejection and explicit AegisOps admission linkage."
  "Phase 57 AI advisory trace must cite this policy for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal."
  "Phase 59 delegated execution must cite this policy for Shuffle workflow-success shortcut rejection and AegisOps receipt linkage."
  "Phase 60 reconciliation must cite this policy for downstream receipt shortcut rejection and durable reconciliation linkage."
  "Phase 62 report export and Phase 63 support bundle work must cite this policy when derived reports, exports, bundles, or external evidence systems are present."
  "Phase 66 RC and Phase 67 GA evidence packets must cite this policy when gate evidence includes browser state, UI cache, downstream receipts, demo data, tickets, Wazuh, Shuffle, AI, endpoint evidence, network evidence, or external evidence-system context."
  "using AI recommendation text as approval, execution, reconciliation, case closure, detector activation, or source truth;"
  "using Wazuh alert status to close, reconcile, release, or gate an AegisOps record;"
  "using Shuffle workflow success to close, reconcile, release, or gate an AegisOps record;"
  "using ticket status to close, approve, reconcile, release, or gate an AegisOps record;"
  "using endpoint or network telemetry as authoritative evidence without reviewed custody, parser, scope, and AegisOps evidence-record linkage;"
  "using browser state, UI cache, optimistic updates, badges, counters, or detail projections as workflow truth;"
  "using downstream receipts without AegisOps reconciliation linkage as closeout truth;"
  "using demo data, placeholders, fake secrets, TODO values, or sample credentials as production truth."
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/test-verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1047 --config <supervisor-config-path>`.'
)

forbidden_lines=(
  "AI may approve actions."
  "AI may execute actions."
  "AI may reconcile execution."
  "AI may close cases."
  "AI may activate detectors."
  "AI may become source truth."
  "Wazuh alert status may close AegisOps records."
  "Wazuh alert status may reconcile AegisOps records."
  "Shuffle workflow success may close AegisOps records."
  "Shuffle workflow success may reconcile AegisOps records."
  "Ticket status may close AegisOps records."
  "Browser state is workflow truth."
  "UI cache is workflow truth."
  "Downstream receipts are reconciliation truth."
  "Demo data is production truth."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 51.6 authority-boundary negative-test policy: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 51.6 authority-boundary negative-test policy heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 51.6 authority-boundary negative-test policy statement: ${phrase}" >&2
    exit 1
  fi
done

if ! grep -Eq '^- \*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "${doc_path}"; then
  echo "Missing or invalid Phase 51.6 authority-boundary negative-test policy date line (- **Date**: YYYY-MM-DD)." >&2
  exit 1
fi

for line in "${forbidden_lines[@]}"; do
  if grep -Fiq -- "${line}" "${doc_path}"; then
    echo "Forbidden Phase 51.6 authority-boundary negative-test policy claim: ${line}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"
path_token_boundary="(^|[[:space:]'\"(<{=])"
local_path_token="(${mac_user_home}|${unix_user_home}|${windows_user_profile_backslash}|${windows_user_profile_slash})[^[:space:]'\" )>}]*"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 51.6 authority-boundary negative-test policy: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 51.6 authority-boundary negative-test policy link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/phase-51-6-authority-boundary-negative-test-policy\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 51.6 authority-boundary negative-test policy." >&2
  exit 1
fi

echo "Phase 51.6 authority-boundary negative-test policy is present and preserves subordinate-surface fail-closed expectations."
