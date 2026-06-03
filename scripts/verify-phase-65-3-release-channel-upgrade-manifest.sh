#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
manifest_path="docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
readme_path="${repo_root}/README.md"
absolute_doc_path="${repo_root}/${doc_path}"
absolute_manifest_path="${repo_root}/${manifest_path}"

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

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_text "${file}"); then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

yaml_scalar() {
  local file="$1"
  local key="$2"

  perl -Mstrict -Mwarnings -0 -e '
    my $key = shift @ARGV;
    my $text = <>;
    for my $line (split /\n/, $text) {
      if ($line =~ /^\Q$key\E:\s*(.*?)\s*$/) {
        print "$1\n";
        last;
      }
    }
  ' "${key}" "${file}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

is_placeholder_or_missing() {
  local value="$1"
  local normalized

  normalized="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [[ -z "${normalized}" || "${normalized}" =~ ^(todo|tbd|none|n/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$ ]]
}

require_yaml_scalar() {
  local key="$1"
  local value

  value="$(yaml_scalar "${absolute_manifest_path}" "${key}")"
  if is_placeholder_or_missing "${value}"; then
    echo "Missing Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
  printf '%s' "${value}"
}

require_manifest_pattern() {
  local pattern="$1"
  local description="$2"

  if ! grep -Eiq -- "${pattern}" "${absolute_manifest_path}"; then
    echo "Missing Phase 65.3 upgrade manifest content: ${description}" >&2
    exit 1
  fi
}

scan_forbidden_text() {
  local description="$1"
  shift

  local decoded_text normalized_text
  decoded_text="$(perl -0pe 's/%([0-9A-Fa-f]{2})/chr(hex($1))/eg; s{\\/}{/}g' "$@")"
  normalized_text="$(printf '%s' "${decoded_text}" | tr '\n' ' ' | tr '[:upper:]' '[:lower:]' | sed -E 's/[[:space:]]+/ /g')"

  if ! printf '%s' "${decoded_text}" | perl -Mstrict -Mwarnings -0ne '
    my $text = $_;
    my $slash = "/";
    my $mac_home = "Users";
    my $linux_home = "home";
    my $root_home = "root";
    my $file_home_re = qr{\bfile://+(?:[A-Za-z]:[\\\/]+)?(?:\Q$mac_home\E|\Q$linux_home\E|\Q$root_home\E)[\\\/]+}i;
    my $windows_home_re = qr{(^|[^A-Za-z0-9_.\/\\-])([A-Za-z]:[\\\/]+\Q$mac_home\E[\\\/]+[^\\\/\s]+)}i;
    my $unix_home_re = qr{(^|[^A-Za-z0-9_.\/\\-])\Q$slash\E(?:\Q$mac_home\E|\Q$linux_home\E)\Q$slash\E[^/\s]+(?:/[^\s]*)?};
    my $root_home_re = qr{(^|[^A-Za-z0-9_.\/\\-])\Q$slash\E\Q$root_home\E\Q$slash\E[^\s]*};
    exit 1 if $text =~ $file_home_re;
    exit 1 if $text =~ $windows_home_re;
    exit 1 if $text =~ $unix_home_re;
    exit 1 if $text =~ $root_home_re;
  '; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi

  if ! printf '%s' "${decoded_text}" | perl -Mstrict -Mwarnings -0ne '
    my $text = $_;
    exit 1 if $text =~ /(AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})/i;
    for my $line (split /\n/, $text) {
      while ($line =~ /(^|[^[:alnum:]_-])["'\'']?([A-Za-z0-9_-]*(?:password|private[_-]?key|secret(?:[_-]?key)?|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|credential)[A-Za-z0-9_-]*)["'\'']?[[:space:]]*[:=][[:space:]]*("[^"]*"|'\''[^'\'']*'\''|[^[:space:]]+)/ig) {
        my $value = $3;
        $value =~ s/^["'\'']//;
        $value =~ s/["'\'']$//;
        next if $value =~ /\A(<[^>]+>|todo|tbd|none|n\/a|na|placeholder|sample|example|false)\z/i;
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: production secret-looking value detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(customer-private|customer private|customer-confidential|customer confidential)[[:space:]-]+(data|payload|record|records)[[:space:]]*[:=]' <<<"${decoded_text}"; then
    echo "Forbidden ${description}: customer-private data detected" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      next if $sentence =~ /(?:does not|do not|must not|cannot|can not|must reject|forbidden|non-claims|false|manual or unsupported)/;
      if ($sentence =~ /(?:silent[ -]+auto[ -]+upgrade|silent[ -]+update)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|proceeds|runs|executes)\b/) {
        exit 1;
      }
      if ($sentence =~ /automatic[ -]+(?:migration|rollback)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|proceeds|runs|executes)\b/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: silent auto-upgrade or automatic migration claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      next if $sentence =~ /(?:does not|do not|must not|cannot|can not|must reject|forbidden|non-claims|false|manual or unsupported)/;
      if ($sentence =~ /(?:hosted|network)[ -]+update[ -]+service[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available)\b/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: hosted update-service claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      next if $sentence =~ /(?:does not|do not|must not|cannot|can not|must reject|forbidden|non-claims|false|manual or unsupported|phase 66 remains rc|phase 67 remains ga)/;
      if ($sentence =~ /(?:(?:phase[ -]+66[ -]+)?rc|(?:phase[ -]+67[ -]+)?ga)[ -]+(?:readiness|pass|proof|gate acceptance|gates?)[^.?!;]*(?:proven|complete|satisfied|accepted|passed|ready)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:release-channel metadata|upgrade manifest|manifest|metadata)[^.?!;]*(?:proves|satisfies|passes|accepts)[^.?!;]*(?:rc|ga)[ -]+(?:readiness|gates?|pass|proof)/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: inferred RC/GA readiness claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      next if $sentence =~ /(?:does not|do not|must not|cannot|can not|must reject|forbidden|non-claims|false)/;
      if ($sentence =~ /(?:metadata|manifest|verifier output|issue-lint output)[^.?!;]*(?:is|becomes|satisfies|proves|serves as)[^.?!;]*(?:release|upgrade|rollback|readiness|gate|workflow)[ -]+truth/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: metadata, manifest, verifier, or issue-lint truth claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      next if $sentence =~ /(?:does not|do not|must not|cannot|can not|must reject|forbidden|non-claims|false|manual or unsupported)/;
      if ($sentence =~ /(?:production[ -]+entitlement enforcement|billing|commercial replacement readiness)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available|satisfied)\b/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: entitlement, billing, or commercial readiness claim" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.3 release channel and upgrade manifest contract"
require_file "${absolute_manifest_path}" "Phase 65.3 upgrade manifest artifact"
require_file "${readme_path}" "README for Phase 65.3 contract link check"

require_phrase "${readme_path}" "- [Phase 65.3 release channel and upgrade manifest contract](docs/phase-65-3-release-channel-upgrade-manifest-contract.md)" "README canonical cross-phase boundary bullet"

required_doc_phrases=(
  "# Phase 65.3 Release Channel And Upgrade Manifest Contract"
  "The contract identifier is \`phase-65-release-channel-upgrade-manifest-contract-v1\`."
  "The required structured artifact is \`docs/deployment/release/phase-65-3-upgrade-manifest.yaml\`."
  "release channel \`beta-design-partner\`;"
  "source version;"
  "target version;"
  "compatibility posture;"
  "rollback expectation;"
  "required checks;"
  "known limitation references;"
  "silent auto-upgrade, hosted update-service behavior, production rollout, automatic rollback, RC gate acceptance, GA gate acceptance"
  "| \`source_version\` | Reviewed source package, profile, or repository version before upgrade review. | Missing, floating, latest, TODO, sample, beta-only, RC, GA, or inferred versions fail. |"
  "| \`target_version\` | Reviewed target package, profile, or repository version represented by the bundle. | Missing, floating, latest, TODO, sample, beta-only, RC, GA, or inferred versions fail. |"
  "| \`compatibility_posture\` | One of \`compatible\` or \`incompatible\`. | Missing, placeholder, inferred, ambiguous, or convenience-summary posture fails. |"
  "| \`rollback_expectation\` | Reviewed rollback owner, trigger, target, and evidence reference expectation. | Missing, placeholder, automatic rollback, or broad operator discretion fails. |"
  "The manifest must include at least one compatible version case and at least one incompatible version case."
  "The verifier must reject:"
  "- missing source version;"
  "- missing target version;"
  "- missing compatibility posture;"
  "- missing rollback expectation;"
  "- silent auto-upgrade claims;"
  "- hosted update-service claims;"
  "- inferred RC pass;"
  "- inferred GA pass;"
  "bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "bash scripts/test-verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1380 --config <supervisor-config-path>"
  "This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness"
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.3 contract term in ${doc_path}"
done

required_manifest_values=(
  "contract_identifier|phase-65-release-channel-upgrade-manifest-contract-v1"
  "inventory_identifier|phase-65-release-bundle-inventory-v1"
  "offline_bundle_contract_identifier|phase-65-offline-install-bundle-contract-v1"
  "release_channel|beta-design-partner"
  "release_bundle_identifier|aegisops-beta-<repository-revision>"
  "repository_revision|<repository-revision>"
  "inventory_reference|docs/phase-65-1-release-bundle-inventory.md"
  "offline_bundle_reference|docs/phase-65-2-offline-install-bundle-contract.md"
  "verifier_output_reference|bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
)

for entry in "${required_manifest_values[@]}"; do
  key="${entry%%|*}"
  expected="${entry#*|}"
  actual="$(yaml_scalar "${absolute_manifest_path}" "${key}")"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "Missing Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
done

release_notes_reference="$(require_yaml_scalar "release_notes_reference")"
if [[ "${release_notes_reference}" != docs/* ]]; then
  echo "Invalid Phase 65.3 upgrade manifest release notes reference" >&2
  exit 1
fi

authority_boundary="$(require_yaml_scalar "authority_boundary")"
if [[ "${authority_boundary}" != *"subordinate packaging and planning evidence only"* || "${authority_boundary}" != *"Phase 51.3 gate contract"* ]]; then
  echo "Missing Phase 65.3 upgrade manifest authority boundary" >&2
  exit 1
fi

require_manifest_pattern 'compatibility_posture:[[:space:]]*compatible' "compatible version posture case"
require_manifest_pattern 'compatibility_posture:[[:space:]]*incompatible' "incompatible version posture case"
require_manifest_pattern 'source_version:[[:space:]]*[^[:space:]]' "source version"
require_manifest_pattern 'target_version:[[:space:]]*[^[:space:]]' "target version"
require_manifest_pattern 'rollback_expectation:[[:space:]]*[^[:space:]]' "rollback expectation"
require_manifest_pattern 'required_checks:' "required checks"
require_manifest_pattern 'known_limitation_references:' "known limitation references"
require_manifest_pattern 'phase58_upgrade_plan_reference:[[:space:]]*docs/phase-58-5-upgrade-rollback-plan-contract[.]md' "Phase 58 upgrade plan reference"
require_manifest_pattern 'phase51_gate_boundary_reference:[[:space:]]*docs/phase-51-3-pilot-beta-rc-ga-gate-contract[.]md' "Phase 51 gate boundary reference"
require_manifest_pattern 'upgrade_action:[[:space:]]*manual-upgrade-review' "compatible manual upgrade review action"
require_manifest_pattern 'upgrade_action:[[:space:]]*blocked-pending-reviewed-migration' "incompatible blocked migration action"

scan_forbidden_text "Phase 65.3 release channel and upgrade manifest guidance" "${absolute_doc_path}" "${absolute_manifest_path}" "${readme_path}"

echo "Phase 65.3 release channel metadata and upgrade manifest are present and fail-closed."
