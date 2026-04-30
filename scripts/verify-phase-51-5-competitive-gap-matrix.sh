#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-51-5-competitive-gap-matrix.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 51.5 Competitive Gap Matrix"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Competitive Gap Matrix"
  "## 4. P0 and P1 Gap Closure Map"
  "## 5. Target-State Boundaries"
  "## 6. Validation"
  "## 7. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Related Issues**: #1041, #1042, #1046"
  "This matrix is competitive and product-planning documentation only. It does not implement SIEM, SOAR, Wazuh, Shuffle, AI, admin, packaging, supportability, installer, operator UI, report export, restore, upgrade, or release-gate behavior."
  "AegisOps owns reviewed operating truth for admitted alerts, cases, evidence, recommendations, approvals, action requests, execution receipts, reconciliation, audit, release gates, and known limitations."
  "AegisOps does not replace every Wazuh detector, every Shuffle integration, every manual approval decision, or every enterprise SIEM/SOAR capability."
  "| Standalone Wazuh operations |"
  "| Standalone Shuffle operations |"
  "| Manual SOC/ticket workflow |"
  "| Common SMB SIEM/SOAR expectations |"
  "AegisOps current state is pre-GA and must not be described as already closing Beta, RC, or GA gaps."
  "Beta target gaps must remain explicitly open until later phases produce evidence."
  "RC target gaps must remain explicitly open until Phase 66 evidence exists."
  "GA target gaps must remain explicitly open until Phase 67 real-user or design-partner evidence exists."
  "| P0 | Guided setup and deployment path | Current state is not a self-service replacement because install, profile selection, and first-use onboarding still need a reviewed guided path. | Phase 52 setup and guided onboarding, Phase 53 install profile |"
  "| P0 | Wazuh signal admission from replacement profile | Current state does not yet prove the replacement operating experience for Wazuh-backed SMB signal intake across the intended profile. | Phase 54 Wazuh signal intake |"
  "| P0 | Daily operator queue and handoff ergonomics | Current state does not yet prove the daily replacement workflow for part-time SMB operators. | Phase 55 daily operator queue |"
  "| P0 | Approval, delegated execution, and reconciliation operating path | Current state has reviewed foundations, but the replacement target still needs end-to-end approval ergonomics, Shuffle delegation evidence, and reconciliation closure. | Phase 56 approval ergonomics, Phase 59 delegated execution, Phase 60 reconciliation |"
  "| P0 | Restore, support, limitations, RC, and GA evidence chain | Current state cannot claim replacement readiness until restore, support bundle, known limitation ownership, RC evidence, and GA evidence are complete. | Phase 61 restore dry-run, Phase 63 support bundle, Phase 64 limitation ownership, Phase 66 RC evidence packet, Phase 67 GA launch evidence |"
  "| P1 | Advisory AI trace, reporting, admin custody, and upgrade plan | Current state does not yet provide the replacement-grade advisory trace, leadership reporting, admin secret custody, or upgrade evidence expected by SMB buyers. | Phase 57 AI advisory trace, Phase 58 admin and secret custody, Phase 62 report export, Phase 65 upgrade plan |"
  "| P1 | Enterprise SIEM/SOAR parity | Deferred: broad enterprise SIEM/SOAR parity, broad source coverage, 24x7 SOC services, HA/multi-tenant enterprise operations, and every vendor integration remain outside the Phase 52-67 SMB replacement target unless a later roadmap explicitly accepts them. | Explicitly deferred beyond Phase 67 |"
  'Run `bash scripts/verify-phase-51-5-competitive-gap-matrix.sh`.'
  'Run `bash scripts/test-verify-phase-51-5-competitive-gap-matrix.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1046 --config <supervisor-config-path>`.'
)

forbidden_lines=(
  "AegisOps is already GA."
  "AegisOps is already a self-service commercial replacement."
  "AegisOps fully replaces enterprise SIEM."
  "AegisOps fully replaces enterprise SOAR."
  "AegisOps provides full enterprise SIEM parity."
  "AegisOps provides full enterprise SOAR parity."
  "AegisOps replaces every Wazuh detector."
  "AegisOps replaces every Shuffle integration."
  "AegisOps is authoritative because Wazuh emitted alerts."
  "AegisOps is authoritative because Shuffle ran workflows."
  "Wazuh is authoritative for AegisOps records."
  "Shuffle is authoritative for AegisOps records."
  "Tickets are authoritative for AegisOps records."
  "AI is authoritative for AegisOps records."
)

authority_verb_pattern="(is|are|becomes|become|remains|may[[:space:]]+be|can[[:space:]]+be|serves[[:space:]]+as|acts[[:space:]]+as)"

forbidden_patterns=(
  "fully[[:space:]]+replaces[[:space:]]+enterprise[[:space:]]+siem"
  "fully[[:space:]]+replaces[[:space:]]+enterprise[[:space:]]+soar"
  "full[[:space:]]+enterprise[[:space:]]+siem[[:space:]]+parity"
  "full[[:space:]]+enterprise[[:space:]]+soar[[:space:]]+parity"
  "^aegisops[^.]*replaces[[:space:]]+every[[:space:]]+wazuh[[:space:]]+detector"
  "^aegisops[^.]*replaces[[:space:]]+every[[:space:]]+shuffle[[:space:]]+integration"
  "(^|[^[:alnum:]_])wazuh[[:space:]]+${authority_verb_pattern}[[:space:]]+authoritative[[:space:]]+for[[:space:]]+aegisops"
  "(^|[^[:alnum:]_])shuffle[[:space:]]+${authority_verb_pattern}[[:space:]]+authoritative[[:space:]]+for[[:space:]]+aegisops"
  "(^|[^[:alnum:]_])tickets?[[:space:]]+${authority_verb_pattern}[[:space:]]+authoritative[[:space:]]+for[[:space:]]+aegisops"
  "(^|[^[:alnum:]_])ai[[:space:]]+${authority_verb_pattern}[[:space:]]+authoritative[[:space:]]+for[[:space:]]+aegisops"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 51.5 competitive gap matrix: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 51.5 competitive gap matrix heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 51.5 competitive gap matrix statement: ${phrase}" >&2
    exit 1
  fi
done

if ! grep -Eq '^- \*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "${doc_path}"; then
  echo "Missing or invalid Phase 51.5 competitive gap matrix date line (- **Date**: YYYY-MM-DD)." >&2
  exit 1
fi

for line in "${forbidden_lines[@]}"; do
  if grep -Fiq -- "${line}" "${doc_path}"; then
    echo "Forbidden Phase 51.5 competitive gap matrix claim: ${line}" >&2
    exit 1
  fi
done

for pattern in "${forbidden_patterns[@]}"; do
  if grep -Eiq -- "${pattern}" "${doc_path}"; then
    echo "Forbidden Phase 51.5 competitive gap matrix claim matched: ${pattern}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"

if grep -Eq "(${mac_user_home}[^[:space:]]*|${unix_user_home}[^[:space:]]*|${windows_user_profile_backslash}[^[:space:]]*|${windows_user_profile_slash}[^[:space:]]*)" "${doc_path}"; then
  echo "Forbidden Phase 51.5 competitive gap matrix: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 51.5 competitive gap matrix link check: ${readme_path}" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/phase-51-5-competitive-gap-matrix\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 51.5 competitive gap matrix." >&2
  exit 1
fi

echo "Phase 51.5 competitive gap matrix is present and preserves replacement-scope, phase-mapping, and authority boundaries."
