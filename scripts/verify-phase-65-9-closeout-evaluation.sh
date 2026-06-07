#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-65-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-5-competitive-gap-matrix.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-64-closeout-evaluation.md"
  "docs/phase-65-1-release-bundle-inventory.md"
  "docs/phase-65-2-offline-install-bundle-contract.md"
  "docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
  "docs/phase-65-4-integrity-evidence-contract.md"
  "docs/phase-65-5-oss-licensing-redistribution-checklist.md"
  "docs/phase-65-6-default-smb-documentation-pack.md"
  "docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
  "docs/deployment/release/phase-65-4-integrity-evidence.yaml"
  "docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
  "docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
  "docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
  "docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
  "docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
  "docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
  "docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-65-1-release-bundle-inventory.sh"
  "scripts/test-verify-phase-65-1-release-bundle-inventory.sh"
  "scripts/verify-phase-65-2-offline-install-bundle-contract.sh"
  "scripts/test-verify-phase-65-2-offline-install-bundle-contract.sh"
  "scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "scripts/test-verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "scripts/verify-phase-65-4-integrity-evidence-contract.sh"
  "scripts/test-verify-phase-65-4-integrity-evidence-contract.sh"
  "scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh"
  "scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh"
  "scripts/verify-phase-65-6-default-smb-docs-pack.sh"
  "scripts/test-verify-phase-65-6-default-smb-docs-pack.sh"
  "scripts/verify-phase-65-7-migration-guides.sh"
  "scripts/test-verify-phase-65-7-migration-guides.sh"
  "scripts/verify-phase-65-8-beta-evidence-templates.sh"
  "scripts/test-verify-phase-65-8-beta-evidence-templates.sh"
  "scripts/verify-phase-65-9-closeout-evaluation.sh"
  "scripts/test-verify-phase-65-9-closeout-evaluation.sh"
  "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"
  "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "scripts/verify-maintainability-hotspots.sh"
  "scripts/verify-publishable-path-hygiene.sh"
)

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_text() {
  perl -0pe 's/<!--.*?-->//gs' "$@"
}

visible_paragraph_text() {
  perl -0pe 's/<!--.*?-->//gs; s/\r\n?/\n/g; s/[ \t]*\n[ \t]*/ /g; s/[ \t]+/ /g' "$@"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_text "${file}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_section_phrase() {
  local section="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(perl -0pe 's/<!--.*?-->//gs' <<<"${section}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

section_text() {
  local file="$1"
  local heading="$2"
  local next_heading="$3"

  awk -v heading="${heading}" -v next_heading="${next_heading}" '
    {
      line = $0
      sub(/^[[:space:]]+/, "", line)
    }
    line == heading { in_section = 1 }
    in_section {
      if (next_heading != "" && (line == next_heading || index(line, next_heading) == 1)) {
        exit
      }
      print
    }
  ' "${file}"
}

require_file "${absolute_doc_path}" "Phase 65 closeout evaluation"
require_file "${readme_path}" "README for Phase 65 closeout link check"
for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 65 closeout reference ${reference_path}"
done
for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 65 verifier script ${verifier_script}"
done

require_phrase "${readme_path}" "- [Phase 65.9 closeout evaluation](docs/phase-65-closeout-evaluation.md) records the Commercial Packaging and Beta boundary outcomes, subordinate authority posture, verifier evidence, issue-lint evidence, accepted limitations, and bounded Phase 66 handoff without RC, GA, real design-partner success, or commercial replacement claims." "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 65.9 closeout evaluation is defined by the [Phase 65.9 closeout evaluation](docs/phase-65-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 65 Closeout Evaluation
**Status**: Accepted as Commercial Packaging and Beta Readiness packaging evidence before Phase 66 RC proof, Phase 67 GA proof, real design-partner success, and commercial replacement-readiness claims.
**Related Issues**: #1378, #1379, #1384, #1380, #1383, #1382, #1385, #1381, #1386, #1387
Phase 65 Commercial Packaging and Beta Readiness is accepted for versioned release bundle inventory, offline install bundle contract, release channel and upgrade manifest, SBOM/checksum/signing integrity evidence, OSS licensing and redistribution review checklist, default SMB documentation pack, migration guides, beta known-limitations template, design-partner evidence template, and closeout evidence.
AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.
Phase 65 closeout text, release artifacts, docs, manifests, checklists, templates, verifier output, and issue-lint output remain subordinate release and planning evidence only. They cannot approve, execute, reconcile, close, gate, prove support operations, resolve limitations, accept RC gates, accept GA gates, or claim readiness by themselves.
Phase 65 must reject missing child outcomes, missing verifier evidence, missing issue-lint evidence, missing accepted limitations, missing Phase 66 handoff, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, self-service commercial readiness claims, broad SIEM/SOAR replacement claims, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.
This closeout does not claim Phase 66 RC readiness, Phase 67 GA readiness, real beta launch evidence, real design-partner success, support-bundle completion, production rollout readiness, self-service commercial readiness, commercial replacement readiness, broad SIEM/SOAR replacement readiness, or Phase 66 RC gate acceptance.
Focused Phase 65 and closeout verifiers that must pass:
Issue-lint evidence:
Each command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none` before Phase 65 is considered fully closed.
Issue-lint output is planning and metadata evidence only. It does not become release truth, closeout truth, workflow truth, support truth, limitation truth, gate truth, or readiness truth.
Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output.
Phase 66 can consume Phase 65 as subordinate RC packet planning input for packaging inventory, offline install package shape, release-channel metadata, upgrade/rollback posture, integrity evidence, licensing checklist posture, documentation coverage, migration guidance, known limitation template shape, design-partner evidence template shape, verifier coverage, and issue-lint coverage.
Phase 66 must still prove RC gates independently under `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`
Phase 65 closeout is release and planning evidence only.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65 closeout term in ${doc_path}"
done

child_issue_outcomes="$(section_text "${absolute_doc_path}" "## Child Issue Outcomes" "## Changed Files")"
required_child_rows=(
  "| #1378 | Epic: Phase 65 Commercial Packaging and Beta Readiness | Open until #1387 lands; accepted when this closeout, focused Phase 65 verifiers, authority-boundary checks, maintainability check, publishable path hygiene, and issue-lint pass. |"
  "| #1379 | Phase 65.1 versioned release bundle inventory | Closed. \`docs/phase-65-1-release-bundle-inventory.md\` and focused inventory verifier define artifact classes, owners, evidence references, exclusions, and verifier coverage without RC, GA, entitlement, billing, or commercial replacement claims. |"
  "| #1384 | Phase 65.2 offline install bundle contract | Closed. \`docs/phase-65-2-offline-install-bundle-contract.md\` and focused offline-bundle verifier define bounded offline packaging shape, manifest expectations, smoke reference, and non-claims without production installer or hosted-update behavior. |"
  "| #1380 | Phase 65.3 release channel and upgrade manifest | Closed. \`docs/phase-65-3-release-channel-upgrade-manifest-contract.md\`, \`docs/deployment/release/phase-65-3-upgrade-manifest.yaml\`, and focused upgrade-manifest verifier define beta/design-partner channel metadata and upgrade/rollback posture without silent auto-upgrade, hosted update service, RC, or GA claims. |"
  "| #1383 | Phase 65.4 SBOM, checksums, and signing evidence contract | Closed. \`docs/phase-65-4-integrity-evidence-contract.md\`, \`docs/deployment/release/phase-65-4-integrity-evidence.yaml\`, and focused integrity verifier define SBOM, checksum, and signing placeholder evidence with artifact identity binding and no production signing, entitlement, RC, or GA claims. |"
  "| #1382 | Phase 65.5 OSS licensing and redistribution review checklist | Closed. \`docs/phase-65-5-oss-licensing-redistribution-checklist.md\`, \`docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml\`, and focused licensing verifier define licensing and redistribution review posture without legal advice, production distribution approval, entitlement, RC, or GA claims. |"
  "| #1385 | Phase 65.6 default SMB documentation pack | Closed. \`docs/phase-65-6-default-smb-documentation-pack.md\`, \`docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml\`, and focused docs-pack verifier define install, daily operation, source onboarding, automation, AI, backup/restore, support bundle, upgrade, and rollback documentation coverage while preserving RC, GA, and production-support non-claims. |"
  "| #1381 | Phase 65.7 migration guides | Closed. \`docs/migration/phase-65-7-standalone-wazuh-migration-guide.md\`, \`docs/migration/phase-65-7-standalone-shuffle-migration-guide.md\`, \`docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md\`, and focused migration verifier define migration planning guidance without automated migration, production customer-data import, source-native truth, RC, GA, or broad SIEM/SOAR parity claims. |"
  "| #1386 | Phase 65.8 beta known-limitations and design-partner evidence templates | Closed. \`docs/deployment/release/phase-65-8-beta-known-limitations-template.md\`, \`docs/deployment/release/phase-65-8-design-partner-evidence-template.md\`, and focused template verifier define beta/design-partner evidence-capture scaffolds without real beta evidence, real design-partner evidence collection, support-bundle completion, RC, GA, or commercial replacement readiness claims. |"
  "| #1387 | Phase 65.9 Phase 65 closeout evaluation | Open until this document and focused closeout verifier land. |"
)

for row in "${required_child_rows[@]}"; do
  require_section_phrase "${child_issue_outcomes}" "${row}" "Phase 65 child issue outcome row in Child Issue Outcomes table"
done

verifier_evidence="$(section_text "${absolute_doc_path}" "## Verifier Evidence" "## Issue-Lint Summary")"
required_verifier_lines=(
  "- \`bash scripts/verify-phase-65-1-release-bundle-inventory.sh\`"
  "- \`bash scripts/test-verify-phase-65-1-release-bundle-inventory.sh\`"
  "- \`bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh\`"
  "- \`bash scripts/test-verify-phase-65-2-offline-install-bundle-contract.sh\`"
  "- \`bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh\`"
  "- \`bash scripts/test-verify-phase-65-3-release-channel-upgrade-manifest.sh\`"
  "- \`bash scripts/verify-phase-65-4-integrity-evidence-contract.sh\`"
  "- \`bash scripts/test-verify-phase-65-4-integrity-evidence-contract.sh\`"
  "- \`bash scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh\`"
  "- \`bash scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh\`"
  "- \`bash scripts/verify-phase-65-6-default-smb-docs-pack.sh\`"
  "- \`bash scripts/test-verify-phase-65-6-default-smb-docs-pack.sh\`"
  "- \`bash scripts/verify-phase-65-7-migration-guides.sh\`"
  "- \`bash scripts/test-verify-phase-65-7-migration-guides.sh\`"
  "- \`bash scripts/verify-phase-65-8-beta-evidence-templates.sh\`"
  "- \`bash scripts/test-verify-phase-65-8-beta-evidence-templates.sh\`"
  "- \`bash scripts/verify-phase-65-9-closeout-evaluation.sh\`"
  "- \`bash scripts/test-verify-phase-65-9-closeout-evaluation.sh\`"
  "- \`bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh\`"
  "- \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`"
  "- \`bash scripts/verify-maintainability-hotspots.sh\`"
  "- \`bash scripts/verify-publishable-path-hygiene.sh\`"
)

for line in "${required_verifier_lines[@]}"; do
  require_section_phrase "${verifier_evidence}" "${line}" "Phase 65 verifier evidence line in Verifier Evidence section"
done

issue_lint_evidence="$(section_text "${absolute_doc_path}" "Issue-lint evidence:" "Each command should report")"
for issue_number in 1378 1379 1384 1380 1383 1382 1385 1381 1386 1387; do
  issue_lint_line="- \`node <codex-supervisor-root>/dist/index.js issue-lint ${issue_number} --config <supervisor-config-path>\`"
  require_section_phrase "${issue_lint_evidence}" "${issue_lint_line}" "Phase 65 issue-lint evidence line in Issue-lint evidence section"
done

accepted_limitations="$(section_text "${absolute_doc_path}" "## Accepted Limitations" "## Phase 66 Handoff")"
require_section_phrase "${accepted_limitations}" "Phase 65 does not collect real beta launch evidence, conduct real design-partner interviews, prove real design-partner success, accept RC gates, accept GA gates, assemble Phase 66 RC packets, collect Phase 67 GA evidence, or approve production commercial distribution." "Phase 65 accepted limitations beta/RC/GA boundary"
require_section_phrase "${accepted_limitations}" "Phase 65 does not implement production installer behavior, hosted update service behavior, silent auto-upgrade behavior, entitlement enforcement, billing, production signing infrastructure, production support operations, support-bundle completion, or live migration tooling." "Phase 65 accepted limitations packaging boundary"
require_section_phrase "${accepted_limitations}" "Phase 65 does not resolve limitations, promote Wazuh, Shuffle, tickets, docs, templates, release notes, support notes, screenshots, verifier output, issue-lint output, or operator-facing summaries into AegisOps workflow, support, release, gate, limitation, readiness, RC, GA, or commercial replacement truth." "Phase 65 accepted limitations authority boundary"

phase66_handoff="$(section_text "${absolute_doc_path}" "## Phase 66 Handoff" "")"
require_section_phrase "${phase66_handoff}" "Phase 66 can consume Phase 65 as subordinate RC packet planning input for packaging inventory, offline install package shape, release-channel metadata, upgrade/rollback posture, integrity evidence, licensing checklist posture, documentation coverage, migration guidance, known limitation template shape, design-partner evidence template shape, verifier coverage, and issue-lint coverage." "Phase 66 handoff consumption note"
require_section_phrase "${phase66_handoff}" "Phase 66 must still prove RC gates independently under \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`" "Phase 66 independent RC proof note"
require_section_phrase "${phase66_handoff}" "Phase 66 must not infer RC gate acceptance from Phase 65 issue closure, owner assignment, release bundle inventory presence, manifest presence, template presence, docs coverage, migration guidance, checklist wording, verifier success, issue-lint success, support-bundle posture, upgrade posture, limitation references, design-partner placeholders, or this closeout date." "Phase 66 no inference note"

forbidden_patterns=(
  'phase[[:space:]]+65[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)[^.[:cntrl:]]*(readiness|gate|acceptance|proof)'
  'phase[[:space:]]+65[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(readiness|gate|acceptance|proof)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)'
  'support[- ]bundle[[:space:]]+(evidence[[:space:]]+)?(is|becomes|counts[[:space:]]+as|serves[[:space:]]+as)[^.[:cntrl:]]*(complete|accepted|satisfied)'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(self[- ]service[[:space:]]+commercial|commercial[[:space:]]+replacement|broad[[:space:]]+siem|broad[[:space:]]+soar)'
  '(verifier|issue-lint)[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate|workflow|support|limitation)[[:space:]]+truth'
)

while IFS= read -r paragraph || [[ -n "${paragraph}" ]]; do
  for pattern in "${forbidden_patterns[@]}"; do
    if grep -Eiq -- "${pattern}" <<<"${paragraph}"; then
      echo "Forbidden Phase 65 closeout evaluation claim matched: ${pattern}" >&2
      exit 1
    fi
  done
done < <(visible_paragraph_text "${absolute_doc_path}")

if grep -Eiq -- 'authorization[[:space:]]*:[[:space:]]*bearer[[:space:]]+[A-Za-z0-9_./+=-]{12,}|(password|passwd|secret|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*`?[^[:space:]`<>]+`?|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}' < <(visible_text "${absolute_doc_path}"); then
  echo "Forbidden Phase 65 closeout evaluation: production secret-looking value detected" >&2
  exit 1
fi

while IFS= read -r line; do
  line_lower="$(printf '%s' "${line}" | tr '[:upper:]' '[:lower:]')"
  if grep -Eiq -- '(includes|contains|embeds|carries)[^.[:cntrl:]]*(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line}"; then
    echo "Forbidden Phase 65 closeout evaluation: customer-private data detected" >&2
    exit 1
  fi
  if [[ "${line_lower}" =~ (reject|without|must[[:space:]]+reject|does[[:space:]]+not|cannot) ]]; then
    continue
  fi
  if grep -Eiq -- '(includes|contains|embeds|carries)[[:space:]]+(customer[-_ ]private|raw[[:space:]]+customer[[:space:]]+data|unredacted[[:space:]]+customer)|customer[-_ ]private[[:space:]]+(example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+customer[[:space:]]+(ticket|alert|log|chat|payload|export|data)' <<<"${line}"; then
    echo "Forbidden Phase 65 closeout evaluation: customer-private data detected" >&2
    exit 1
  fi
done < <(visible_text "${absolute_doc_path}")

path_hygiene_stderr="${repo_root}/.tmp-phase65-9-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 65 closeout evaluation absolute path usage detected" >&2
  exit 1
fi

echo "Phase 65.9 closeout evaluation contract and focused negative checks pass."
