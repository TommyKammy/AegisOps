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
      if ($line =~ /^\s*\Q$key\E:\s*(.*?)\s*$/) {
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

require_yaml_scalar_equals() {
  local key="$1"
  local expected="$2"
  local actual

  actual="$(yaml_scalar "${absolute_manifest_path}" "${key}")"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
}

require_manifest_pattern() {
  local pattern="$1"
  local description="$2"

  if ! grep -Eiq -- "${pattern}" "${absolute_manifest_path}"; then
    echo "Missing Phase 65.3 upgrade manifest content: ${description}" >&2
    exit 1
  fi
}

reject_mixed_negated_positive_claim() {
  local description="$1"
  local normalized_text="$2"

  local negated_boundary positive_claim_terms positive_verbs positive_states
  negated_boundary='((does|do|must|can|is|are)[ -]+not|cannot|can not|unsupported|excludes)[^.?!;]*(;[[:space:]]*| and | but | yet | however | though | although )'
  positive_claim_terms='silent[ -]+auto[ -]+upgrade|silent[ -]+update|automatic[ -]+(migration|rollback)|hosted[ -]+update[ -]+service|network[ -]+update[ -]+service|production[ -]+entitlement enforcement|billing|commercial replacement readiness|(phase[ -]+66[ -]+)?rc[ -]+(readiness|pass|proof|gate|gates|gate acceptance)|(phase[ -]+67[ -]+)?ga[ -]+(readiness|pass|proof|gate|gates|gate acceptance)|(release-channel metadata|upgrade manifest|manifest|metadata|verifier output|issue-lint output)[^.?!;]*(release|upgrade|rollback|readiness|gate|workflow)[ -]+truth'
  positive_verbs='(is|are|becomes|become|provides|provide|includes|include|contains|support|supports|enables|enable|delivers|deliver|proves|prove|satisfies|satisfy|passes|pass|implements|implement|approves|approve|accepts|accept|establishes|establish)'
  positive_states='(enabled|implemented|included|available|ready|required|assumed|approved|complete|completed|supported|provided|satisfied|proven|delivered|accepted|done)'

  if grep -Eiq -- "${negated_boundary}[^.?!;]*(${positive_claim_terms})[^.?!;]*(${positive_verbs}|${positive_states})|${negated_boundary}[^.?!;]*${positive_verbs}[[:space:]-]+(${positive_claim_terms})" <<<"${normalized_text}"; then
    echo "Forbidden ${description}: positive claim after negated boundary detected" >&2
    exit 1
  fi
}

validate_compatibility_cases() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my @cases;
    my $current;
    my $in_cases = 0;

    sub finish_case {
      my ($case) = @_;
      push @cases, $case if defined $case;
    }

    for my $line (split /\n/, $text) {
      if ($line =~ /^compatibility_cases:\s*$/) {
        $in_cases = 1;
        next;
      }
      next unless $in_cases;
      last if $line =~ /^[^[:space:]]/ && $line !~ /^compatibility_cases:/;

      if ($line =~ /^  -\s+([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        finish_case($current);
        $current = {};
        $current->{$1} = $2;
        next;
      }
      if (defined $current && $line =~ /^    (required_checks|known_limitation_references):\s*$/) {
        my $list = $1;
        $current->{$list} = "__list__";
        next;
      }
      if (defined $current && $line =~ /^    ([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        $current->{$1} = $2;
        next;
      }
    }
    finish_case($current);

    sub bad {
      my ($value) = @_;
      return 1 if !defined $value;
      $value =~ s/^\s+|\s+$//g;
      return 1 if $value eq "";
      return 1 if $value =~ /^(todo|tbd|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/i;
      return 0;
    }

    die "Missing Phase 65.3 upgrade manifest content: compatibility cases\n" if @cases < 2;

    my @required = qw(case_identifier source_version target_version compatibility_posture compatibility_reason upgrade_action rollback_expectation required_checks known_limitation_references phase58_upgrade_plan_reference phase51_gate_boundary_reference);
    my %seen_posture;
    for my $case (@cases) {
      my $id = $case->{case_identifier} // "<unknown>";
      for my $field (@required) {
        die "Missing Phase 65.3 upgrade manifest compatibility case field: $id.$field\n" if bad($case->{$field});
      }

      my $posture = $case->{compatibility_posture};
      die "Invalid Phase 65.3 upgrade manifest compatibility posture: $id\n" unless $posture =~ /^(compatible|incompatible)$/;
      $seen_posture{$posture} = 1;

      if ($posture eq "compatible" && $case->{upgrade_action} ne "manual-upgrade-review") {
        die "Invalid Phase 65.3 upgrade manifest compatible upgrade action: $id\n";
      }
      if ($posture eq "incompatible" && $case->{upgrade_action} ne "blocked-pending-reviewed-migration") {
        die "Invalid Phase 65.3 upgrade manifest incompatible upgrade action: $id\n";
      }
    }

    die "Missing Phase 65.3 upgrade manifest content: compatible version posture case\n" unless $seen_posture{compatible};
    die "Missing Phase 65.3 upgrade manifest content: incompatible version posture case\n" unless $seen_posture{incompatible};
  ' "${absolute_manifest_path}" || {
    local status=$?
    return "${status}"
  }
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

  reject_mixed_negated_positive_claim "${description}" "${normalized_text}"

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
  "channel_scope|beta/design-partner packaging review only; not RC, GA, production rollout, entitlement, billing, support readiness, or commercial replacement readiness."
  "release_bundle_identifier|aegisops-beta-<repository-revision>"
  "repository_revision|<repository-revision>"
  "inventory_reference|docs/phase-65-1-release-bundle-inventory.md"
  "offline_bundle_reference|docs/phase-65-2-offline-install-bundle-contract.md"
  "verifier_output_reference|bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "approval_record|issue #1380"
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
require_file "${repo_root}/${release_notes_reference}" "Phase 65.3 release notes reference"

require_yaml_scalar_equals "silent_auto_upgrade" "false"
require_yaml_scalar_equals "hosted_update_service" "false"
require_yaml_scalar_equals "automatic_migration" "false"
require_yaml_scalar_equals "automatic_rollback" "false"
require_yaml_scalar_equals "rc_readiness" "false"
require_yaml_scalar_equals "ga_readiness" "false"
require_yaml_scalar_equals "commercial_replacement_readiness" "false"

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
validate_compatibility_cases

scan_forbidden_text "Phase 65.3 release channel and upgrade manifest guidance" "${absolute_doc_path}" "${absolute_manifest_path}" "${readme_path}"

echo "Phase 65.3 release channel metadata and upgrade manifest are present and fail-closed."
