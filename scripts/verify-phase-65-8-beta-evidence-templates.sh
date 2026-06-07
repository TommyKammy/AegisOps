#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

readme_path="${repo_root}/README.md"
beta_template_path="docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
design_partner_template_path="docs/deployment/release/phase-65-8-design-partner-evidence-template.md"

templates=(
  "${beta_template_path}|beta known-limitations template|Beta Known-Limitations|phase-65-8-beta-known-limitations-template-v1|This beta known-limitations template does not claim real beta launch evidence, real design-partner evidence, support-bundle completion, limitation resolution, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness."
  "${design_partner_template_path}|design-partner evidence template|Design-Partner Evidence|phase-65-8-design-partner-evidence-template-v1|This design-partner evidence template does not claim real beta launch evidence, real design-partner evidence collection, support-bundle completion, limitation resolution, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness."
)

required_headings=(
  "## 1. Template Header"
  "## 4. Authority Boundary"
  "## 5. Validation"
  "## 6. Non-Claims"
)

required_common_phrases=(
  "- **Status**: Accepted as a Phase 65 beta/design-partner template only."
  "- **Related Issues**: #1378, #1379, #1386"
  "The template is planning and evidence-capture scaffolding only."
  '| Template owner | `<named-owner>` |'
  '| Review date | `<YYYY-MM-DD>` |'
  '| Next review date | `<YYYY-MM-DD>` |'
  '| Limitation source | `docs/phase-64-1-reviewed-limitation-ownership-records.md` |'
  '| Phase 64 limitation handoff reference | `docs/phase-64-5-phase66-limitation-handoff.md` |'
  '| Phase 66 RC proof boundary | `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md` |'
  '| Support-bundle posture | `<not-complete|tracked-separately|blocked-with-owner>` |'
  '| Upgrade posture | `<not-reviewed|reviewed-planning-only|blocked-with-owner>` |'
  '| Template authority boundary | `planning-and-evidence-capture-scaffold-only` |'
  "Every row must name an owner, review date"
  "limitation reference"
  "evidence reference"
  "Blocker disposition"
  "Accepted risk posture"
  "Support-bundle posture"
  "Upgrade posture"
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  "Phase 64 limitation records and Phase 64.5 Phase 66 handoff evidence remain subordinate limitation ownership inputs."
  "Phase 66 must still prove RC gates independently under the Phase 51.3 gate contract."
  "Verifier output and issue-lint output are validation and metadata evidence only."
  "bash scripts/verify-phase-65-8-beta-evidence-templates.sh"
  "bash scripts/test-verify-phase-65-8-beta-evidence-templates.sh"
  "bash scripts/verify-phase-64-5-phase66-limitation-handoff.sh"
  "bash scripts/verify-publishable-path-hygiene.sh"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1386 --config <supervisor-config-path>"
  "substitute evidence for the Phase 51.3 gate contract"
)

forbidden_lines=(
  "Support bundle evidence is complete for RC."
  "Support-bundle completion is accepted for RC."
  "Phase 65.8 proves RC readiness."
  "Phase 65.8 proves release-candidate readiness."
  "Phase 65.8 satisfies the RC gate."
  "Phase 65.8 proves GA readiness."
  "Phase 65.8 satisfies the GA gate."
  "AegisOps is commercially replacement ready."
  "Beta evidence is RC proof."
  "Design-partner evidence is GA proof."
  "Template output is readiness truth."
  "Verifier output is readiness truth."
  "Issue-lint output is readiness truth."
)

forbidden_patterns=(
  'support[- ]bundle[[:space:]]+(evidence[[:space:]]+)?(is|becomes|counts[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(complete|accepted|satisfied)'
  'phase[[:space:]]+65\.8[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)[^.[:cntrl:]]*(readiness|gate|acceptance)'
  'phase[[:space:]]+65\.8[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(readiness|gate|acceptance)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)'
  'beta[[:space:]]+evidence[[:space:]]+(is|becomes|counts[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(rc|release[- ]candidate)[^.[:cntrl:]]*proof'
  'design[- ]partner[[:space:]]+evidence[[:space:]]+(is|becomes|counts[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(ga|general[- ]availability)[^.[:cntrl:]]*proof'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*commercial(ly)?[[:space:]]+replacement[[:space:]]+ready'
  '(template|verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate|limitation|support)[[:space:]]+truth'
)

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing Phase 65.8 ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_text() {
  perl -0pe 's/<!--.*?-->//gs' "$@"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_text "${file}"); then
    echo "Missing Phase 65.8 ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_heading() {
  local file="$1"
  local heading="$2"
  local description="$3"

  if ! grep -Fxq -- "${heading}" < <(visible_text "${file}"); then
    echo "Missing Phase 65.8 ${description}: ${heading}" >&2
    exit 1
  fi
}

reject_forbidden_content() {
  local file="$1"
  local forbidden pattern

  for forbidden in "${forbidden_lines[@]}"; do
    if grep -Fiq -- "${forbidden}" < <(visible_text "${file}"); then
      echo "Forbidden Phase 65.8 template claim: ${forbidden}" >&2
      exit 1
    fi
  done

  for pattern in "${forbidden_patterns[@]}"; do
    if grep -Eiq -- "${pattern}" < <(visible_text "${file}"); then
      echo "Forbidden Phase 65.8 template claim matched: ${pattern}" >&2
      exit 1
    fi
  done
}

reject_publishable_hazards() {
  local file="$1"

  if grep -Eiq '(password|passwd|secret|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?' < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.8 template production secret material: ${file#"${repo_root}/"}" >&2
    exit 1
  fi
  if grep -Eiq '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.8 template customer-private data: ${file#"${repo_root}/"}" >&2
    exit 1
  fi

  local mac_user_home unix_user_home windows_user_profile_backslash windows_user_profile_slash path_token_boundary local_path_token
  mac_user_home="$(printf '/%s/' 'Users')"
  unix_user_home="$(printf '/%s/' 'home')"
  windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
  windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"
  path_token_boundary="(^|[[:space:]'\"(<{=])"
  local_path_token="(${mac_user_home}|${unix_user_home}|${windows_user_profile_backslash}|${windows_user_profile_slash})[^[:space:]'\" )>}]*"

  if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.8 template workstation-local absolute path: ${file#"${repo_root}/"}" >&2
    exit 1
  fi
}

require_readme_link() {
  local path="$1"
  local rendered

  require_file "${readme_path}" "README"
  rendered="$(
    awk '
      /^[[:space:]]*(```|~~~)/ {
        in_fenced_block = !in_fenced_block
        next
      }
      !in_fenced_block { print }
    ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
  )"

  if ! grep -Eq "\\[[^]]+\\]\\(${path}\\)" <<<"${rendered}"; then
    echo "Missing README Phase 65.8 template link: ${path}" >&2
    exit 1
  fi
}

validate_template() {
  local relative_path="$1"
  local description="$2"
  local title_fragment="$3"
  local template_identifier="$4"
  local non_claim_phrase="$5"
  local absolute_path="${repo_root}/${relative_path}"
  local heading phrase

  require_file "${absolute_path}" "${description}"
  require_phrase "${absolute_path}" "# Phase 65.8 ${title_fragment} Template" "${description} title"
  require_phrase "${absolute_path}" "| Template identifier | \`${template_identifier}\` |" "${description} identifier"
  require_phrase "${absolute_path}" "${non_claim_phrase}" "${description} non-claims"

  for heading in "${required_headings[@]}"; do
    require_heading "${absolute_path}" "${heading}" "${description} required section"
  done

  for phrase in "${required_common_phrases[@]}"; do
    require_phrase "${absolute_path}" "${phrase}" "${description} required statement"
  done

  if ! grep -Eq '^- \*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$' < <(visible_text "${absolute_path}"); then
    echo "Missing or invalid Phase 65.8 ${description} date line (- **Date**: YYYY-MM-DD)." >&2
    exit 1
  fi

  reject_forbidden_content "${absolute_path}"
  reject_publishable_hazards "${absolute_path}"
  require_readme_link "${relative_path}"
}

for template_spec in "${templates[@]}"; do
  IFS="|" read -r relative_path description title_fragment template_identifier non_claim_phrase <<<"${template_spec}"
  validate_template "${relative_path}" "${description}" "${title_fragment}" "${template_identifier}" "${non_claim_phrase}"
done

echo "Phase 65.8 beta known-limitations and design-partner evidence templates preserve required fields and authority boundaries."
