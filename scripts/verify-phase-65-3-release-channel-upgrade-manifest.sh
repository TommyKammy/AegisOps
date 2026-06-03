#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"
revision_repo_root="${PHASE_65_3_REVISION_REPO_ROOT:-${repo_root}}"

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

yaml_top_level_scalar() {
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

yaml_top_level_scalar_count() {
  local file="$1"
  local key="$2"

  grep -Ec "^${key}:[[:space:]]*" "${file}" || true
}

is_placeholder_or_missing() {
  local value="$1"
  local normalized

  normalized="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [[ "${normalized}" =~ \<[^[:space:]]+\> ]] && return 0
  [[ -z "${normalized}" || "${normalized}" =~ ^(todo|tbd|none|n/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$ ]]
}

require_yaml_scalar() {
  local key="$1"
  local value count

  value="$(yaml_top_level_scalar "${absolute_manifest_path}" "${key}")"
  count="$(yaml_top_level_scalar_count "${absolute_manifest_path}" "${key}")"
  if is_placeholder_or_missing "${value}"; then
    echo "Missing Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.3 upgrade manifest value: ${key}" >&2
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

require_yaml_scalar_equals_once() {
  local key="$1"
  local expected="$2"
  local actual count

  actual="$(yaml_scalar "${absolute_manifest_path}" "${key}")"
  count="$(grep -Ec "^[[:space:]]*${key}:[[:space:]]*" "${absolute_manifest_path}")"
  if [[ "${count}" != "1" || "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
}

require_top_level_yaml_scalar_equals_once() {
  local key="$1"
  local expected="$2"
  local actual count

  actual="$(yaml_top_level_scalar "${absolute_manifest_path}" "${key}")"
  count="$(yaml_top_level_scalar_count "${absolute_manifest_path}" "${key}")"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" || "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.3 upgrade manifest value: ${key}" >&2
    exit 1
  fi
}

require_non_claim_false_once() {
  local key="$1"

  perl -Mstrict -Mwarnings -0 -e '
    my $key = shift @ARGV;
    my $text = <>;
    my $in_non_claims = 0;
    my $non_claims_count = 0;
    my $count = 0;
    my $value = "";

    for my $line (split /\n/, $text) {
      if ($line =~ /^non_claims:\s*$/) {
        $in_non_claims = 1;
        $non_claims_count++;
        next;
      }
      if ($line =~ /^[^[:space:]]/ && $line !~ /^non_claims:/) {
        $in_non_claims = 0;
      }
      if ($in_non_claims && $line =~ /^  \Q$key\E:\s*(.*?)\s*$/) {
        $count++;
        $value = $1;
        $value =~ s/^\s+|\s+$//g;
      }
      if (!$in_non_claims && $line =~ /^\s*\Q$key\E:\s*/) {
        die "Invalid Phase 65.3 upgrade manifest value: $key\n";
      }
    }

    die "Missing Phase 65.3 upgrade manifest value: non_claims\n" if $non_claims_count == 0;
    die "Invalid Phase 65.3 upgrade manifest value: non_claims\n" if $non_claims_count != 1;
    die "Invalid Phase 65.3 upgrade manifest value: $key\n" if $count != 1 || $value ne "false";
  ' "${key}" "${absolute_manifest_path}" || {
    local status=$?
    return "${status}"
  }
}

require_manifest_pattern() {
  local pattern="$1"
  local description="$2"

  if ! grep -Eiq -- "${pattern}" "${absolute_manifest_path}"; then
    echo "Missing Phase 65.3 upgrade manifest content: ${description}" >&2
    exit 1
  fi
}

reject_unsafe_repo_relative_reference() {
  local reference="$1"
  local description="$2"

  if [[ -z "${reference}" ||
    "${reference}" = /* ||
    "${reference}" == *"\\"* ||
    "${reference}" == *"//"* ||
    "${reference}" == "." ||
    "${reference}" == ".." ||
    "${reference}" == ./* ||
    "${reference}" == ../* ||
    "${reference}" == */./* ||
    "${reference}" == */../* ||
    "${reference}" == */. ||
    "${reference}" == */.. ]]; then
    echo "Invalid Phase 65.3 upgrade manifest ${description}" >&2
    exit 1
  fi
}

validate_repository_revision() {
  local revision="$1"
  local normalized_revision resolved_revision normalized_resolved_revision current_revision

  normalized_revision="$(printf '%s' "${revision}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${normalized_revision}" =~ ^(head|main|master|trunk|develop|development|latest)$ ]]; then
    echo "Invalid Phase 65.3 upgrade manifest repository revision: ${revision} is mutable" >&2
    exit 1
  fi

  if [[ "${revision}" =~ ^[0-9A-Fa-f]{7,40}$ ]]; then
    resolved_revision="$(git -C "${revision_repo_root}" rev-parse --verify --quiet "${revision}^{commit}" || true)"
    normalized_resolved_revision="$(printf '%s' "${resolved_revision}" | tr '[:upper:]' '[:lower:]')"
    if [[ -n "${resolved_revision}" && "${normalized_resolved_revision}" == "${normalized_revision}"* ]]; then
      current_revision="$(git -C "${revision_repo_root}" rev-parse --verify --quiet HEAD^{commit} || true)"
      if [[ -z "${current_revision}" ]] || ! git -C "${revision_repo_root}" merge-base --is-ancestor "${resolved_revision}" "${current_revision}"; then
        echo "Invalid Phase 65.3 upgrade manifest repository revision: ${revision} is not reachable from repository head" >&2
        exit 1
      fi
      return
    fi
  fi

  if git -C "${revision_repo_root}" show-ref --verify --quiet "refs/tags/${revision}" &&
    git -C "${revision_repo_root}" rev-parse --verify --quiet "refs/tags/${revision}^{commit}" >/dev/null; then
    resolved_revision="$(git -C "${revision_repo_root}" rev-parse --verify --quiet "refs/tags/${revision}^{commit}" || true)"
    current_revision="$(git -C "${revision_repo_root}" rev-parse --verify --quiet HEAD^{commit} || true)"
    if [[ -z "${resolved_revision}" || -z "${current_revision}" ]] || ! git -C "${revision_repo_root}" merge-base --is-ancestor "${resolved_revision}" "${current_revision}"; then
      echo "Invalid Phase 65.3 upgrade manifest repository revision: ${revision} is not reachable from repository head" >&2
      exit 1
    fi
    return
  fi

  echo "Invalid Phase 65.3 upgrade manifest repository revision: ${revision} does not resolve in repository" >&2
  exit 1
}

reject_mixed_negated_positive_claim() {
  local description="$1"
  local normalized_text="$2"

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    my $positive_terms = qr{silent[ -]+auto[ -]+upgrade|silent[ -]+update|automatic[ -]+(?:migration|rollback)|hosted[ -]+update[ -]+service|network[ -]+update[ -]+service|production[ -]+rollout|(?:production[ -]+)?entitlement enforcement|billing|(?:self-service commercial|commercial replacement)[ -]+readiness|design-partner evidence completeness|(?:pilot|beta|(?:phase[ -]+66[ -]+)?rc|(?:phase[ -]+67[ -]+)?ga)[ -]+(?:readiness|pass|proof|gate|gates|gate acceptance)|(?:release-channel metadata|upgrade manifest|manifest|metadata|verifier(?: output)?|issue-lint(?: output)?)[^.?!;]*(?:release|upgrade|rollback|readiness|gate|workflow)[ -]+truth|(?:release-channel metadata|upgrade manifest|manifest|metadata)[^.?!;]*(?:live upgrade success|rollback success|substrate mutation|workflow closure|reconciliation)}i;
    my $positive_state = qr{\b(?:is|are|becomes|become|provides|provide|includes|include|contains|support|supports|enables|enable|delivers|deliver|proves|prove|satisfies|satisfy|passes|pass|implements|implement|approves|approve|accepts|accept|establishes|establish|enabled|implemented|included|available|ready|required|assumed|approved|complete|completed|supported|provided|satisfied|proven|delivered|accepted|done|allowed|proceeds|runs|executes)\b}i;
    my $negated = qr{(?:does|do|must|can|is|are)[ -]+not|cannot|can not|unsupported|excludes|manual or unsupported|false}i;
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      while ($sentence =~ /$negated\b.*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;)(.*)/ig) {
        my $tail = $1;
        exit 1 if $tail =~ /$positive_terms[^.?!;]*$positive_state|$positive_state[[:space:]-]+$positive_terms/i;
      }
      if ($sentence =~ /$negated\b(.*)$/i) {
        my @clauses = split /,/, $1;
        shift @clauses;
        for my $clause (@clauses) {
          exit 1 if $clause =~ /$positive_terms[^,.;?!]*$positive_state|$positive_state[[:space:]-]+$positive_terms/i;
        }
      }
    }
  '; then
    echo "Forbidden ${description}: positive claim after negated boundary detected" >&2
    exit 1
  fi
}

validate_compatibility_cases() {
  local expected_target_version="$1"

  perl -Mstrict -Mwarnings -0 -e '
    my $expected_target_version = shift @ARGV;
    my $text = <>;
    my @cases;
    my $current;
    my $in_cases = 0;
    my $active_list;
    my $compatibility_case_block_count = 0;

    sub finish_case {
      my ($case) = @_;
      push @cases, $case if defined $case;
    }

    sub record_field {
      my ($case, $field, $value) = @_;
      my $id = $case->{case_identifier} // "<unknown>";
      die "Invalid Phase 65.3 upgrade manifest compatibility case field: $id.$field\n" if exists $case->{$field};
      $case->{$field} = $value;
    }

    for my $line (split /\n/, $text) {
      if ($line =~ /^compatibility_cases:\s*(.*?)\s*$/) {
        $compatibility_case_block_count++;
        $in_cases = 1;
        next;
      }
      next unless $in_cases;
      last if $line =~ /^[^[:space:]]/ && $line !~ /^compatibility_cases:/;

      if ($line =~ /^  -\s+([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        finish_case($current);
        $current = {};
        $active_list = undef;
        record_field($current, $1, $2);
        next;
      }
      if (defined $current && $line =~ /^    (required_checks|known_limitation_references):\s*$/) {
        my $list = $1;
        record_field($current, $list, "");
        $active_list = $list;
        next;
      }
      if (defined $current && defined $active_list && $line =~ /^      -\s*(.*?)\s*$/) {
        my $value = $1;
        $value =~ s/^\s+|\s+$//g;
        $current->{$active_list} .= "\n$value";
        next;
      }
      if (defined $current && $line =~ /^    ([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        $active_list = undef;
        record_field($current, $1, $2);
        next;
      }
    }
    finish_case($current);

    die "Invalid Phase 65.3 upgrade manifest content: compatibility cases\n" if $compatibility_case_block_count != 1;

    sub bad {
      my ($value) = @_;
      return 1 if !defined $value;
      $value =~ s/^\s+|\s+$//g;
      return 1 if $value eq "";
      return 1 if $value =~ /<[^>]+>/;
      return 1 if $value =~ /^(todo|tbd|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/i;
      return 0;
    }

    sub has_list_item {
      my ($value, $pattern) = @_;
      return 0 if bad($value);
      for my $item (split /\n/, $value) {
        $item =~ s/^\s+|\s+$//g;
        return 1 if $item =~ $pattern;
      }
      return 0;
    }

    sub invalid_semantic_value {
      my ($field, $value) = @_;
      return 1 if bad($value);
      my $normalized = lc $value;
      $normalized =~ s/_/ /g;
      $normalized =~ s/[[:space:]-]+/ /g;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /\b(?:rc|ga)\b/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /(?:^|[^a-z0-9])(?:rc|ga)[0-9]*(?:[^a-z0-9]|$)/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /\bbeta only\b/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /\binferred\b/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /\blatest\b/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /^(?:develop|development|trunk)$/;
      return 1 if $field =~ /^(source_version|target_version)$/ && $normalized =~ /\b(?:floating|branch only|branch)\b/;
      return 1 if $field eq "rollback_expectation" && $normalized =~ /\bautomatic rollback\b/;
      return 1 if $field eq "rollback_expectation" && $normalized =~ /\bbroad operator discretion\b/;
      return 1 if $field eq "rollback_expectation" && $value !~ /\brollback_owner=[^;]+/;
      return 1 if $field eq "rollback_expectation" && $value !~ /\brollback_trigger=[^;]+/;
      return 1 if $field eq "rollback_expectation" && $value !~ /\brollback_target=[^;]+/;
      return 1 if $field eq "rollback_expectation" && $value !~ /\brollback_evidence_reference=docs\/phase-58-5-upgrade-rollback-plan-contract\.md\b/;
      return 1 if $field eq "compatibility_reason" && $normalized =~ /\b(?:same as previous|same as above|same as compatible|same as incompatible|see previous|see above|previous case|sibling|derived from sibling)\b/;
      return 1 if $field eq "compatibility_reason" && $normalized =~ /^(?:compatible|incompatible|reviewed|valid|ok|okay|approved|supported|blocked|manual)$/;
      return 0;
    }

    sub has_forbidden_required_check {
      my ($value) = @_;
      return 1 if bad($value);
      for my $item (split /\n/, $value) {
        $item =~ s/^\s+|\s+$//g;
        next if $item eq "";
        return 1 if $item =~ /(?:production|commercial|readiness|entitlement|billing|support|migration|pilot|beta|rc|ga|gate|issue-lint|truth)/i;
      }
      return 0;
    }

    sub has_forbidden_limitation_reference {
      my ($value) = @_;
      return 1 if bad($value);
      for my $item (split /\n/, $value) {
        $item =~ s/^\s+|\s+$//g;
        next if $item eq "";
        return 1 unless $item eq "docs/phase-64-5-phase66-limitation-handoff.md";
      }
      return 0;
    }

    die "Missing Phase 65.3 upgrade manifest content: compatibility cases\n" if @cases < 2;

    my @required = qw(case_identifier source_version target_version compatibility_posture compatibility_reason upgrade_action rollback_expectation required_checks known_limitation_references phase58_upgrade_plan_reference phase51_gate_boundary_reference);
    my %seen_posture;
    for my $case (@cases) {
      my $id = $case->{case_identifier} // "<unknown>";
      for my $field (@required) {
        die "Missing Phase 65.3 upgrade manifest compatibility case field: $id.$field\n" if bad($case->{$field});
        die "Invalid Phase 65.3 upgrade manifest compatibility case field: $id.$field\n" if invalid_semantic_value($field, $case->{$field});
      }

      my $posture = $case->{compatibility_posture};
      die "Invalid Phase 65.3 upgrade manifest compatibility posture: $id\n" unless $posture =~ /^(compatible|incompatible)$/;
      $seen_posture{$posture} = 1;

      die "Invalid Phase 65.3 upgrade manifest target version: $id\n" unless $case->{target_version} eq $expected_target_version;
      die "Invalid Phase 65.3 upgrade manifest Phase 58 reference: $id\n" unless $case->{phase58_upgrade_plan_reference} eq "docs/phase-58-5-upgrade-rollback-plan-contract.md";
      die "Invalid Phase 65.3 upgrade manifest Phase 51 reference: $id\n" unless $case->{phase51_gate_boundary_reference} eq "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md";
      die "Missing Phase 65.3 upgrade manifest required check reference: $id.phase58_upgrade_plan_reference\n" unless has_list_item($case->{required_checks}, qr{^bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract\.sh$});
      die "Missing Phase 65.3 upgrade manifest required check reference: $id.publishable_path_hygiene\n" unless has_list_item($case->{required_checks}, qr{^bash scripts/verify-publishable-path-hygiene\.sh$});
      die "Missing Phase 65.3 upgrade manifest required check reference: $id.phase65_3_verifier\n" unless has_list_item($case->{required_checks}, qr{^bash scripts/verify-phase-65-3-release-channel-upgrade-manifest\.sh$});
      die "Invalid Phase 65.3 upgrade manifest required check reference: $id.required_checks\n" if has_forbidden_required_check($case->{required_checks});
      die "Missing Phase 65.3 upgrade manifest limitation reference: $id.known_limitation_references\n" unless has_list_item($case->{known_limitation_references}, qr{^docs/phase-64-5-phase66-limitation-handoff\.md$});
      die "Invalid Phase 65.3 upgrade manifest limitation reference: $id.known_limitation_references\n" if has_forbidden_limitation_reference($case->{known_limitation_references});

      if ($posture eq "compatible" && $case->{upgrade_action} ne "manual-upgrade-review") {
        die "Invalid Phase 65.3 upgrade manifest compatible upgrade action: $id\n";
      }
      if ($posture eq "incompatible" && $case->{upgrade_action} ne "blocked-pending-reviewed-migration") {
        die "Invalid Phase 65.3 upgrade manifest incompatible upgrade action: $id\n";
      }
    }

    die "Missing Phase 65.3 upgrade manifest content: compatible version posture case\n" unless $seen_posture{compatible};
    die "Missing Phase 65.3 upgrade manifest content: incompatible version posture case\n" unless $seen_posture{incompatible};
  ' "${expected_target_version}" "${absolute_manifest_path}" || {
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
      if ($line =~ /\bAuthorization\s*:\s*Bearer\s+("[^"]*"|'\''[^'\'']*'\''|[^[:space:]]+)/i) {
        my $value = $1;
        $value =~ s/^["'\'']//;
        $value =~ s/["'\'']$//;
        next if $value =~ /\A(<[^>]+>|todo|tbd|none|n\/a|na|placeholder|sample|example|false)\z/i;
        exit 1;
      }
      while ($line =~ /(^|[^[:alnum:]_-])["'\'']?([A-Za-z0-9_-]*(?:password|private[_-]?key|secret(?:[_-]?key)?|api[_-]?key|access[_-]?token|auth[_-]?token|bearer[_-]?token|client[_-]?secret|credential)[A-Za-z0-9_-]*)["'\'']?[[:space:]]*[:=][[:space:]]*("[^"]*"|'\''[^'\'']*'\''|[^[:space:]]+)/ig) {
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

  if grep -Eiq -- '(customer-private|customer private|customer-confidential|customer confidential)[[:space:]-]+(data|payload|record|records)([[:space:]]*[:=]|\b[[:space:]]+(includes?|contains?|has|with|is|are)\b)' <<<"${decoded_text}"; then
    echo "Forbidden ${description}: customer-private data detected" >&2
    exit 1
  fi

  reject_mixed_negated_positive_claim "${description}" "${normalized_text}"

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false|manual or unsupported).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
      if ($sentence =~ /(?:silent[ -]+auto[ -]+upgrade|silent[ -]+update)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|proceeds|runs|executes)\b/) {
        exit 1;
      }
      if ($sentence =~ /automatic[ -]+(?:migration|rollback)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|proceeds|runs|executes)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:migration|rollback)[^.?!;]*(?:runs?|happens?|executes?|proceeds|starts?|occurs)[^.?!;]*(?:automatically|automatic)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:migration|rollback)[^.?!;]*(?:automatically|automatic)\b/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: silent auto-upgrade or automatic migration claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false|manual or unsupported).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
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
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false|manual or unsupported|phase 66 remains rc|phase 67 remains ga).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
      if ($sentence =~ /(?:pilot|beta|(?:phase[ -]+66[ -]+)?rc|(?:phase[ -]+67[ -]+)?ga)[ -]+(?:readiness|pass|proof|gate acceptance|gates?)[^.?!;]*(?:proven|complete|satisfied|accepted|passed|ready|claimed)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:pilot|beta|(?:phase[ -]+66[ -]+)?rc|(?:phase[ -]+67[ -]+)?ga)[[:space:]-]+(?:is|are|becomes|become)[[:space:]-]+(?:ready|accepted|passed|complete|satisfied)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:release-channel metadata|upgrade manifest|manifest|metadata)[^.?!;]*(?:proves|satisfies|passes|accepts)[^.?!;]*(?:pilot|beta|rc|ga)[ -]+(?:readiness|gates?|pass|proof|gate acceptance)/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: inferred RC/GA readiness claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
      if ($sentence =~ /(?:metadata|manifest|verifier(?: output)?|issue-lint(?: output)?)[^.?!;]*(?:is|becomes|satisfies|proves|serves as)[^.?!;]*(?:release|upgrade|rollback|readiness|gate|workflow)[ -]+truth/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: metadata, manifest, verifier, or issue-lint truth claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false|manual or unsupported).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
      if ($sentence =~ /production[ -]+rollout[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available|satisfied|provided)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:entitlement[ -]+enforcement|billing|self-service commercial readiness|commercial replacement readiness)[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available|satisfied|provided)\b/) {
        exit 1;
      }
      if ($sentence =~ /(?:support|migration)[ -]+readiness[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available|satisfied)\b/) {
        exit 1;
      }
      if ($sentence =~ /design-partner evidence completeness[^.?!;]*(?:enabled|implemented|ready|supported|allowed|proven|complete|available|satisfied)\b/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: entitlement, billing, or commercial readiness claim" >&2
    exit 1
  fi

  if ! printf '%s' "${normalized_text}" | perl -0ne '
    for my $sentence (split /(?<=[.?!;])\s*/, $_) {
      $sentence =~ s/(?:does not|do not|must not|cannot|can not|is not|are not|must reject|forbidden|non-claims|false).*?(?:\band\b|\bbut\b|\byet\b|\bhowever\b|\bthough\b|\balthough\b|;|$)//ig;
      if ($sentence =~ /(?:release-channel metadata|upgrade manifest|manifest|metadata)[^.?!;]*(?:proves|prove|approves|approve|accepts|accept|satisfies|satisfy|enables|enable|implements|implement)[^.?!;]*(?:live upgrade success|rollback success|substrate mutation|workflow closure|action reconciliation|reconciliation|runtime execution)/) {
        exit 1;
      }
      if ($sentence =~ /(?:release-channel metadata|upgrade manifest|manifest|metadata)[^.?!;]*(?:is|are|becomes|become|serves as)[^.?!;]*(?:runtime execution|workflow|upgrade|rollback|readiness|gate)[ -]+authority/) {
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: authority-boundary success claim" >&2
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
  "inventory_reference|docs/phase-65-1-release-bundle-inventory.md"
  "offline_bundle_reference|docs/phase-65-2-offline-install-bundle-contract.md"
  "verifier_output_reference|bash scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
  "approval_record|issue #1380"
)

for entry in "${required_manifest_values[@]}"; do
  key="${entry%%|*}"
  expected="${entry#*|}"
  require_top_level_yaml_scalar_equals_once "${key}" "${expected}"
done

release_bundle_identifier="$(require_yaml_scalar "release_bundle_identifier")"
repository_revision="$(require_yaml_scalar "repository_revision")"
if [[ "${release_bundle_identifier}" != "aegisops-beta-${repository_revision}" ]]; then
  echo "Invalid Phase 65.3 upgrade manifest release binding: ${release_bundle_identifier} does not match repository revision ${repository_revision}" >&2
  exit 1
fi
validate_repository_revision "${repository_revision}"

release_notes_reference="$(require_yaml_scalar "release_notes_reference")"
reject_unsafe_repo_relative_reference "${release_notes_reference}" "release notes reference"
release_notes_name="${release_notes_reference#docs/release/}"
release_notes_reference_lc="$(printf '%s' "${release_notes_reference}" | tr '[:upper:]' '[:lower:]')"
if [[ "${release_notes_reference}" != docs/release/* ||
  "${release_notes_name}" == */* ||
  "${release_notes_name}" != *release-notes*.md ]]; then
  echo "Invalid Phase 65.3 upgrade manifest release notes reference" >&2
  exit 1
fi
if [[ "${release_notes_reference_lc}" == *readiness* ]]; then
  echo "Invalid Phase 65.3 upgrade manifest release notes reference" >&2
  exit 1
fi
require_file "${repo_root}/${release_notes_reference}" "Phase 65.3 release notes reference"
require_file "${repo_root}/docs/phase-65-1-release-bundle-inventory.md" "Phase 65.1 release bundle inventory reference"
require_file "${repo_root}/docs/phase-65-2-offline-install-bundle-contract.md" "Phase 65.2 offline install bundle contract reference"
require_file "${repo_root}/docs/phase-58-5-upgrade-rollback-plan-contract.md" "Phase 58.5 upgrade and rollback evidence reference"
require_file "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "Phase 51.3 gate boundary reference"
require_file "${repo_root}/docs/phase-64-5-phase66-limitation-handoff.md" "Phase 64.5 limitation handoff reference"
require_file "${repo_root}/scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh" "Phase 58.5 upgrade and rollback verifier script reference"
require_file "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "publishable path hygiene verifier script reference"
require_file "${repo_root}/scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh" "Phase 65.3 release channel and upgrade manifest verifier script reference"

require_non_claim_false_once "silent_auto_upgrade"
require_non_claim_false_once "hosted_update_service"
require_non_claim_false_once "automatic_migration"
require_non_claim_false_once "automatic_rollback"
require_non_claim_false_once "rc_readiness"
require_non_claim_false_once "ga_readiness"
require_non_claim_false_once "commercial_replacement_readiness"

authority_boundary="$(require_yaml_scalar "authority_boundary")"
if [[ "${authority_boundary}" != *"subordinate packaging and planning evidence only"* || "${authority_boundary}" != *"Phase 51.3 gate contract"* ]]; then
  echo "Missing Phase 65.3 upgrade manifest authority boundary" >&2
  exit 1
fi

validate_compatibility_cases "${release_bundle_identifier}"

scan_forbidden_text "Phase 65.3 release channel and upgrade manifest guidance" "${absolute_doc_path}" "${absolute_manifest_path}" "${repo_root}/${release_notes_reference}" "${readme_path}"

echo "Phase 65.3 release channel metadata and upgrade manifest are present and fail-closed."
