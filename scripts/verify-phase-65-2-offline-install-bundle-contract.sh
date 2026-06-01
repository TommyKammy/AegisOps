#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${default_repo_root}"
bundle_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle-dir)
      bundle_dir="${2:-}"
      if [[ -z "${bundle_dir}" ]]; then
        echo "Missing value for --bundle-dir" >&2
        exit 1
      fi
      shift 2
      ;;
    --repo-root)
      repo_root="${2:-}"
      if [[ -z "${repo_root}" ]]; then
        echo "Missing value for --repo-root" >&2
        exit 1
      fi
      shift 2
      ;;
    *)
      repo_root="$1"
      shift
      ;;
  esac
done

doc_path="docs/phase-65-2-offline-install-bundle-contract.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"
phase65_inventory_path="${repo_root}/docs/phase-65-1-release-bundle-inventory.md"
phase51_gate_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
first_user_stack_path="${repo_root}/docs/deployment/first-user-stack.md"
host_preflight_path="${repo_root}/docs/deployment/host-preflight-contract.md"
clean_host_smoke_path="${repo_root}/docs/deployment/clean-host-smoke-skeleton.md"
env_contract_path="${repo_root}/docs/deployment/env-secrets-certs-contract.md"
runbook_path="${repo_root}/docs/runbook.md"

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

markdown_section_text() {
  local file="$1"
  local heading="$2"

  visible_markdown_text "${file}" | awk -v heading="${heading}" '
    $0 == heading {
      in_section = 1
      print
      next
    }
    /^## / && in_section {
      exit
    }
    in_section {
      print
    }
  '
}

scan_forbidden_text() {
  local description="$1"
  shift

  local decoded_text normalized_text claim_scan_text
  decoded_text="$(perl -0pe 's/%([0-9A-Fa-f]{2})/chr(hex($1))/eg' "$@")"
  normalized_text="$(printf '%s' "${decoded_text}" | tr '\n' ' ' | tr '[:upper:]' '[:lower:]' | sed -E 's/[[:space:]]+/ /g')"
  claim_scan_text="$(
    printf '%s' "${normalized_text}" |
      sed -E \
        -e 's/[^.?!;]*(does|do|must|can|cannot|can not|is|are)[ -]+not[^.?!;]*(claim|claims|prove|proves|satisfy|satisfies|ready|readiness|truth|authority|gate|gates|hosted|silent|production)[^.?!;]*[.?!;]/ /g' \
        -e 's/[^.?!;]*(unsupported|excludes|manual)[^.?!;]*(hosted|silent|production|entitlement|billing|rc|ga|readiness)[^.?!;]*[.?!;]/ /g'
  )"

  local mac_home_fragment linux_home_fragment windows_home_fragment encoded_mac_home_fragment encoded_windows_home_fragment workstation_path_pattern
  mac_home_fragment="/""Users/"
  linux_home_fragment="/""home/[^/[:space:]]+"
  windows_home_fragment="C:""\\""Users""\\"
  encoded_mac_home_fragment="%2f""Users%2f"
  encoded_windows_home_fragment="%5c""Users%5c"
  workstation_path_pattern="(^|[^[:alnum:]_.-])(${mac_home_fragment}|${linux_home_fragment}|${windows_home_fragment}|${encoded_mac_home_fragment}|${encoded_windows_home_fragment})"

  if grep -Eiq -- "${workstation_path_pattern}" <<<"${decoded_text}"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(AKIA[0-9A-Z]{16}|aws_secret_access_key|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|password[[:space:]]*[:=][[:space:]]*[^[:space:]]+|secret[[:space:]]*[:=][[:space:]]*[^[:space:]]+|access[_-]?token[[:space:]]*[:=][[:space:]]*[^[:space:]]+|auth[_-]?token[[:space:]]*[:=][[:space:]]*[^[:space:]]+|(^|[^[:alnum:]_-])token[[:space:]]*[:=][[:space:]]*[^[:space:]]+|api[_-]?key[[:space:]]*[:=][[:space:]]*[^[:space:]]+|credential[[:space:]]*[:=][[:space:]]*[^[:space:]]+|client[_-]?secret[[:space:]]*[:=][[:space:]]*[^[:space:]]+)' <<<"${decoded_text}"; then
    echo "Forbidden ${description}: production secret-looking value detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(customer-private|customer private|customer-confidential|customer confidential)[[:space:]-]+(data|payload|record|records)[[:space:]-]+(included|packaged|present|bundled|provided)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: customer-private data claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(hidden hosted dependency|hosted update service|network update service|silent update|silent auto-upgrade|silent auto upgrade|production installer|production entitlement enforcement|commercial billing)[[:space:]-]+(is[[:space:]-]+)?(enabled|implemented|included|available|ready|required|assumed|approved)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: hosted, silent update, production installer, entitlement, or billing claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(offline install bundle|offline bundle|bundle manifest|install output|smoke output|verifier output|issue-lint output)[^.?!;]*(proves|satisfies|passes|claims|approves|accepts|creates|establishes|infers)[^.?!;]*(beta|rc|ga)[[:space:]-]+(pass|readiness|gate|gates|gate acceptance)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: inferred Beta/RC/GA readiness claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(verifier output|issue-lint output|install output|smoke output|bundle files|manifest entries)[[:space:]-]+(is|are|acts as|serve as|serves as|becomes|become|establishes|prove|proves|satisfies)[[:space:]-]+([[:alnum:] /-]+[[:space:]-]+)?(readiness|release|gate|workflow|limitation|install|smoke)[[:space:]-]+truth' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: verifier, issue-lint, install, or smoke truth claim detected" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.2 offline install bundle contract"
require_file "${readme_path}" "README for Phase 65.2 contract link check"
require_file "${phase65_inventory_path}" "Phase 65.1 release bundle inventory"
require_file "${phase51_gate_path}" "Phase 51.3 gate contract"
require_file "${first_user_stack_path}" "first-user stack install guidance"
require_file "${host_preflight_path}" "host preflight contract"
require_file "${clean_host_smoke_path}" "clean-host smoke skeleton"
require_file "${env_contract_path}" "env secrets certs contract"
require_file "${runbook_path}" "runbook"

require_phrase "${readme_path}" "- [Phase 65.2 offline install bundle contract](docs/phase-65-2-offline-install-bundle-contract.md)" "README canonical cross-phase boundary bullet"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 65.2 Offline Install Bundle Contract
**Status**: Accepted as the Phase 65 offline install bundle contract for beta/design-partner packaging review only.
The contract identifier is `phase-65-offline-install-bundle-contract-v1`.
docs/phase-65-1-release-bundle-inventory.md
docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md
docs/deployment/first-user-stack.md
docs/deployment/host-preflight-contract.md
docs/deployment/clean-host-smoke-skeleton.md
docs/deployment/env-secrets-certs-contract.md
docs/runbook.md
Every offline install bundle record must include:
contract identifier `phase-65-offline-install-bundle-contract-v1`;
Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
release bundle identifier in the form `aegisops-beta-<repository-revision>`;
repository revision or reviewed tag;
bundle owner;
per-artifact owner;
bundle creation timestamp;
reviewed environment assumption `offline-beta-design-partner`;
required artifact manifest path `BUNDLE-MANIFEST.md`;
verifier output reference for `bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>`;
explicit exclusion review reference;
issue or change record that approved the offline bundle for beta/design-partner packaging review.
Offline bundle records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<runtime-env-file>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.
The offline install bundle must contain these required files:
The bundle must not assume hidden hosted downloads, network update services, silent auto-upgrade, background entitlement checks, production billing, customer-private data, production secrets, or workstation-local absolute paths.
The verifier must reject:
missing bundle metadata;
missing required artifact;
workstation-local absolute paths;
production secret material;
placeholder credentials treated as valid auth;
customer-private data;
hidden hosted dependency claim;
hosted update service claim;
silent update or silent auto-upgrade claim;
production installer claim;
production entitlement enforcement claim;
inferred Beta pass;
inferred RC pass;
inferred GA pass;
verifier-as-readiness-truth claim; and
issue-lint-as-readiness-truth claim.
The offline install bundle contract preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, Phase 66 remains RC, and Phase 67 remains GA.
Bundle files, manifest entries, install output, smoke output, verifier output, issue-lint output, docs, release notes, operator-facing summaries, and downstream receipts cannot satisfy Beta gates, RC gates, GA gates, workflow truth, release truth, gate truth, limitation truth, or readiness truth by themselves.
bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh
bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>
bash scripts/test-verify-phase-65-2-offline-install-bundle-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1384 --config <supervisor-config-path>
This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, release-channel readiness, production installer completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, support readiness, or design-partner evidence completeness.
This contract is an offline packaging contract for beta/design-partner review only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, install truth, smoke truth, or substitute evidence for the Phase 51.3 gate contract.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.2 offline bundle contract term in ${doc_path}"
done

required_bundle_rows=(
  "| \`BUNDLE-MANIFEST.md\` | AegisOps maintainers | Contract identifier, inventory identifier, release bundle identifier, repository revision, owner, creation timestamp, environment assumption, exclusion review, and verifier output reference. | Reject the bundle before beta/design-partner handoff. |"
  "| \`install/README.md\` | Platform maintainers | Reviewed offline install entry command, selected profile, dependency assumptions, and manual prerequisites. | Reject the bundle because install entrypoint evidence is absent. |"
  "| \`config/runtime.env.sample\` | Platform maintainers | Placeholder-only runtime configuration keys and secret-source instructions that cite \`docs/deployment/env-secrets-certs-contract.md\`. | Reject the bundle because runtime configuration custody is not inspectable. |"
  "| \`evidence/install-preflight-output.txt\` | Platform maintainers | Retained host preflight output reference for the same release bundle identifier and repository revision. | Reject the bundle because install completeness evidence is absent. |"
  "| \`docs/phase-65-2-offline-install-bundle-contract.md\` | AegisOps maintainers | This contract, copied from the reviewed repository revision. | Reject the bundle because the offline contract is not carried with the artifact set. |"
  "| \`docs/phase-65-1-release-bundle-inventory.md\` | AegisOps maintainers | Phase 65 inventory consumed by this contract. | Reject the bundle because the Phase 65 inventory reference is absent. |"
  "| \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\` | AegisOps maintainers | Pilot, Beta, RC, and GA gate boundary. | Reject the bundle because release-gate non-claims are not carried with the artifact set. |"
  "| \`docs/deployment/first-user-stack.md\` | Platform maintainers | Reviewed first-user install and operating guidance. | Reject the bundle because install guidance is absent. |"
  "| \`docs/deployment/host-preflight-contract.md\` | Platform maintainers | Reviewed host preflight expectations. | Reject the bundle because host assumptions are not inspectable. |"
  "| \`docs/deployment/clean-host-smoke-skeleton.md\` | Platform maintainers | Reviewed clean-host smoke skeleton and false-success rejection posture. | Reject the bundle because clean-host smoke expectations are absent. |"
  "| \`docs/runbook.md\` | IT Operations, Information Systems Department | Startup, shutdown, evidence capture, and operator handoff guidance. | Reject the bundle because operator runbook guidance is absent. |"
)

bundle_files_section_text="$(markdown_section_text "${absolute_doc_path}" "## 2. Required Offline Bundle Files")"

for bundle_row in "${required_bundle_rows[@]}"; do
  if ! grep -Fq -- "${bundle_row}" <<<"${bundle_files_section_text}"; then
    echo "Missing Phase 65.2 required bundle file row: ${bundle_row}" >&2
    exit 1
  fi
done

metadata_section_text="$(markdown_section_text "${absolute_doc_path}" "## 1. Bundle Identifier And Metadata")"
required_metadata_fields=(
  "contract identifier \`phase-65-offline-install-bundle-contract-v1\`;"
  "Phase 65.1 inventory identifier \`phase-65-release-bundle-inventory-v1\`;"
  "release bundle identifier in the form \`aegisops-beta-<repository-revision>\`;"
  "repository revision or reviewed tag;"
  "bundle owner;"
  "per-artifact owner;"
  "bundle creation timestamp;"
  "reviewed environment assumption \`offline-beta-design-partner\`;"
  "required artifact manifest path \`BUNDLE-MANIFEST.md\`;"
  "verifier output reference for \`bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>\`;"
  "explicit exclusion review reference; and"
  "issue or change record that approved the offline bundle for beta/design-partner packaging review."
)

for metadata_field in "${required_metadata_fields[@]}"; do
  if ! grep -Fq -- "${metadata_field}" <<<"${metadata_section_text}"; then
    echo "Missing Phase 65.2 bundle metadata field: ${metadata_field}" >&2
    exit 1
  fi
done

verification_section_text="$(markdown_section_text "${absolute_doc_path}" "## 6. Verification")"
if ! grep -Fq -- "The verifier must reject missing bundle metadata, missing required artifact, workstation-local absolute paths, production secrets, customer-private data, hidden hosted dependency, silent update claim, inferred RC pass, and inferred GA pass." <<<"${verification_section_text}"; then
  echo "Missing Phase 65.2 verifier negative coverage statement in Verification section" >&2
  exit 1
fi

non_claims_section_text="$(markdown_section_text "${absolute_doc_path}" "## 7. Non-Claims")"
if ! grep -Fq -- "This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, release-channel readiness, production installer completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, support readiness, or design-partner evidence completeness." <<<"${non_claims_section_text}"; then
  echo "Missing Phase 65.2 non-claim statement in Non-Claims section" >&2
  exit 1
fi

scan_forbidden_text "Phase 65.2 offline install bundle contract guidance" "${absolute_doc_path}" "${readme_path}"

if [[ -n "${bundle_dir}" ]]; then
  required_bundle_files=(
    "BUNDLE-MANIFEST.md"
    "install/README.md"
    "config/runtime.env.sample"
    "evidence/install-preflight-output.txt"
    "docs/phase-65-2-offline-install-bundle-contract.md"
    "docs/phase-65-1-release-bundle-inventory.md"
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
    "docs/deployment/first-user-stack.md"
    "docs/deployment/host-preflight-contract.md"
    "docs/deployment/clean-host-smoke-skeleton.md"
    "docs/runbook.md"
  )

  for bundle_file in "${required_bundle_files[@]}"; do
    if [[ ! -s "${bundle_dir}/${bundle_file}" ]]; then
      echo "Missing offline install bundle required artifact: ${bundle_file}" >&2
      exit 1
    fi
  done

  bundle_manifest="${bundle_dir}/BUNDLE-MANIFEST.md"
  required_manifest_phrases=(
    "contract identifier: phase-65-offline-install-bundle-contract-v1"
    "inventory identifier: phase-65-release-bundle-inventory-v1"
    "release bundle identifier: aegisops-beta-<repository-revision>"
    "repository revision: <repository-revision>"
    "bundle owner:"
    "per-artifact owner:"
    "bundle creation timestamp:"
    "environment assumption: offline-beta-design-partner"
    "exclusion review:"
    "verifier output: bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>"
  )

  for manifest_phrase in "${required_manifest_phrases[@]}"; do
    if ! grep -Fq -- "${manifest_phrase}" "${bundle_manifest}"; then
      echo "Missing offline install bundle metadata: ${manifest_phrase}" >&2
      exit 1
    fi
  done

  bundle_scan_files=()
  while IFS= read -r -d '' bundle_scan_file; do
    bundle_scan_files+=("${bundle_scan_file}")
  done < <(find "${bundle_dir}" -type f -print0)
  scan_forbidden_text "offline install bundle content" "${bundle_scan_files[@]}"
fi

echo "Phase 65.2 offline install bundle contract is present and fail-closed."
