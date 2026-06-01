#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-65-1-release-bundle-inventory.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
phase51_gate_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
phase51_gap_path="${repo_root}/docs/phase-51-5-competitive-gap-matrix.md"
phase64_closeout_path="${repo_root}/docs/phase-64-closeout-evaluation.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_markdown_text() {
  local file="$1"

  perl -0pe 's/<!--.*?-->//gs' "${file}"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_markdown_text "${file}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.1 release bundle inventory"
require_file "${readme_path}" "README for Phase 65.1 inventory link check"
require_file "${phase51_gate_path}" "Phase 51.3 gate contract"
require_file "${phase51_gap_path}" "Phase 51.5 competitive gap matrix"
require_file "${phase64_closeout_path}" "Phase 64 closeout evaluation"

require_phrase "${readme_path}" "- [Phase 65.1 release bundle inventory](docs/phase-65-1-release-bundle-inventory.md)" "README canonical cross-phase boundary bullet"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 65.1 Release Bundle Inventory
**Status**: Accepted as the Phase 65 beta/design-partner bundle inventory contract before offline packaging, hosted release metadata, SBOM/signing, licensing, migration, template, RC, GA, and commercial replacement claims.
The inventory identifier is `phase-65-release-bundle-inventory-v1`.
release bundle identifier in the form `aegisops-beta-<repository-revision>`;
artifact-set owner;
per-artifact owner;
evidence reference for every required artifact class;
verifier output reference;
explicit exclusion review reference;
The inventory preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, and Phase 66 remains RC while Phase 67 remains GA.
The inventory preserves Phase 64 limitation ownership: known limitation records, mitigation posture, handoff notes, verifier output, issue-lint output, UI text, readiness projections, and AI summaries remain subordinate planning evidence only.
AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.
Missing owner, missing version identifier, missing evidence reference, missing required artifact class, missing exclusion review, placeholder credential, production secret material, customer-private data, workstation-local absolute path, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, or issue-lint-as-readiness-truth must block the release bundle record until the prerequisite is corrected.
The Phase 65.1 inventory explicitly excludes:
production secret material;
customer-private data;
workstation-local absolute paths;
hosted update service behavior;
silent auto-upgrade behavior;
billing;
production entitlement enforcement;
full offline install packaging implementation;
release channel implementation;
SBOM generation, checksum generation, or signing implementation;
OSS licensing conclusion or redistribution approval;
migration guide implementation;
beta known-limitations template implementation;
design-partner evidence template implementation;
RC gate acceptance;
GA readiness;
self-service commercial readiness; and
broad SIEM/SOAR replacement readiness.
bash scripts/verify-phase-65-1-release-bundle-inventory.sh
bash scripts/test-verify-phase-65-1-release-bundle-inventory.sh
bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1379 --config <supervisor-config-path>
The verifier must reject missing version identifier, missing artifact owner, missing required artifact class, missing evidence reference, missing exclusion list, workstation-local absolute paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.
This inventory does not claim Phase 66 RC readiness, Phase 67 GA readiness, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, billing readiness, release-channel readiness, offline install completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, beta template completeness, or design-partner evidence completeness.
This inventory is a root packaging contract for later Phase 65 work. It is not workflow authority, support authority, release gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, UI truth, AI truth, or substitute evidence for the Phase 51.3 gate contract.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.1 inventory term in ${doc_path}"
done

required_artifact_rows=(
  "| Install artifact set | Platform maintainers | Install entrypoint, profile selection, runtime env sample, preflight output, and bounded install evidence reference. | \`install-artifacts:<repository-revision>\` | Phase 65.2 offline install bundle contract. |"
  "| Runtime configuration artifact set | Platform maintainers | Reviewed runtime config keys, secret-source placeholders, proxy boundary, certificate custody, and fail-closed config validation evidence. | \`runtime-config:<repository-revision>\` | Phase 65.2 and Phase 65.3 packaging and upgrade metadata. |"
  "| Documentation artifact set | IT Operations, Information Systems Department | Default SMB documentation pack index for installation, daily operation, source onboarding, automation catalog, AI usage, backup and restore, support bundle, upgrade, and rollback. | \`docs-pack:<repository-revision>\` | Phase 65.6 default SMB documentation pack. |"
  "| Supportability evidence artifact set | IT Operations, Information Systems Department | Doctor, backup, restore dry-run, support bundle redaction, support handoff, and safe support-bundle submission evidence references. | \`supportability:<repository-revision>\` | Phase 65.8 beta known-limitations and design-partner evidence templates. |"
  "| Release notes artifact set | AegisOps maintainers | Release notes reference naming changes, known limitations, operator verification, rollback pointer, and support-bundle pointer. | \`release-notes:<repository-revision>\` | Phase 65.3 release channel metadata. |"
  "| Upgrade and rollback guidance artifact set | Platform maintainers | Upgrade plan, rollback trigger, migration owner, rollback owner, clean-state validation, and post-rollback smoke evidence references. | \`upgrade-rollback:<repository-revision>\` | Phase 65.3 release channel and upgrade manifest. |"
  "| Known limitation evidence artifact set | AegisOps maintainers | Phase 64 limitation ownership record references, Phase 66 handoff notes, owner, mitigation posture, blocker, accepted-risk posture, and next review date. | \`limitations:<repository-revision>\` | Phase 65.8 beta known-limitations template and Phase 66 planning evidence. |"
  "| Verification output artifact set | Platform maintainers | Focused Phase 65 inventory verifier output, publishable path hygiene output, Phase 51.3 gate verifier output, and issue-lint output reference. | \`verification:<repository-revision>\` | Phase 65.9 closeout evaluation. |"
)

for artifact_row in "${required_artifact_rows[@]}"; do
  require_phrase "${absolute_doc_path}" "${artifact_row}" "Phase 65.1 artifact inventory row with owner, evidence, and version binding"
done

required_version_identifiers=(
  "install-artifacts:<repository-revision>"
  "runtime-config:<repository-revision>"
  "docs-pack:<repository-revision>"
  "supportability:<repository-revision>"
  "release-notes:<repository-revision>"
  "upgrade-rollback:<repository-revision>"
  "limitations:<repository-revision>"
  "verification:<repository-revision>"
)

for version_identifier in "${required_version_identifiers[@]}"; do
  require_phrase "${absolute_doc_path}" "${version_identifier}" "Phase 65.1 artifact version identifier"
done

forbidden_claims=(
  "phase 65.1 proves rc readiness"
  "phase 65.1 proves ga readiness"
  "phase 65.1 is rc ready"
  "phase 65.1 is ga ready"
  "phase 65.1 proves commercial replacement readiness"
  "phase 65.1 satisfies phase 66 rc gates"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "release bundle inventory is readiness truth"
  "release bundle inventory is gate truth"
  "release bundle inventory is workflow truth"
  "verifier output is readiness truth"
  "verifier output is release truth"
  "issue-lint output is readiness truth"
  "issue-lint output is release truth"
)

normalized_visible_text="$(visible_markdown_text "${absolute_doc_path}" | tr '\n' ' ' | tr '[:upper:]' '[:lower:]' | sed -E 's/[[:space:]]+/ /g')"

for claim in "${forbidden_claims[@]}"; do
  if [[ "${normalized_visible_text}" == *"${claim}"* ]]; then
    echo "Forbidden Phase 65.1 release bundle inventory claim: ${claim}" >&2
    exit 1
  fi
done

if grep -Eiq -- '(AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|password[[:space:]]*[:=][[:space:]]*[^[:space:]]+|secret[[:space:]]*[:=][[:space:]]*[^[:space:]]+)' "${absolute_doc_path}"; then
  echo "Forbidden Phase 65.1 release bundle inventory: production secret-looking value detected" >&2
  exit 1
fi

if grep -Eiq -- 'customer-private[[:space:]]+[^[:space:];:=]+[[:space:]]*[:=][[:space:]]*[^[:space:]]+' "${absolute_doc_path}"; then
  echo "Forbidden Phase 65.1 release bundle inventory: customer-private data detected" >&2
  exit 1
fi

macos_home_pattern='/'"Users"'/[^[:space:])>]+'
linux_home_pattern='/'"home"'/[^[:space:])>]+'
windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

if grep -Eq "${workstation_local_path_pattern}" "${absolute_doc_path}"; then
  echo "Forbidden Phase 65.1 release bundle inventory absolute path usage detected" >&2
  exit 1
fi

if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/tmp/phase65-path-hygiene.out 2>/tmp/phase65-path-hygiene.err; then
  cat /tmp/phase65-path-hygiene.out >&2
  cat /tmp/phase65-path-hygiene.err >&2
  echo "Forbidden Phase 65.1 release bundle inventory absolute path usage detected" >&2
  exit 1
fi

echo "Phase 65.1 release bundle inventory is present, versioned, bounded, and fail-closed."
