#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-65-5-oss-licensing-redistribution-checklist.md"
checklist_path="docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
readme_path="${repo_root}/README.md"
absolute_doc_path="${repo_root}/${doc_path}"
absolute_checklist_path="${repo_root}/${checklist_path}"

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

normalize_yaml_scalar() {
  local value="$1"

  value="$(printf '%s' "${value}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  if [[ "${#value}" -ge 2 ]]; then
    case "${value:0:1}${value: -1}" in
      \"\"|\'\') value="${value:1:${#value}-2}" ;;
    esac
  fi
  printf '%s' "${value}"
}

is_placeholder_or_missing() {
  local value="$1"
  local normalized block_scalar_marker_regex

  normalized="$(normalize_yaml_scalar "${value}" | tr '[:upper:]' '[:lower:]')"
  block_scalar_marker_regex='^[>|][+-]?$'
  [[ -z "${normalized}" || "${normalized}" =~ ${block_scalar_marker_regex} || "${normalized}" =~ ^(~|null|todo|tbd|none|n/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$ ]]
}

require_top_level_equals_once() {
  local key="$1"
  local expected="$2"
  local actual count

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "${key}")")"
  count="$(yaml_top_level_scalar_count "${absolute_checklist_path}" "${key}")"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.5 licensing checklist value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" || "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.5 licensing checklist value: ${key}" >&2
    exit 1
  fi
}

require_top_level_present_once() {
  local key="$1"
  local actual count

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "${key}")")"
  count="$(yaml_top_level_scalar_count "${absolute_checklist_path}" "${key}")"
  if [[ "${count}" == "0" || "$(is_placeholder_or_missing "${actual}"; echo $?)" == "0" ]]; then
    echo "Missing Phase 65.5 licensing checklist value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.5 licensing checklist value: ${key}" >&2
    exit 1
  fi
}

require_top_level_sequence_key_once() {
  local key="$1"
  local count

  count="$(grep -Ec "^${key}:[[:space:]]*$" "${absolute_checklist_path}" || true)"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.5 licensing checklist ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.5 licensing checklist ${key}" >&2
    exit 1
  fi
}

require_repository_revision_resolves() {
  local repository_revision

  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "repository_revision")")"
  if [[ ! "${repository_revision}" =~ ^[0-9a-fA-F]{40}$ ]]; then
    if ! git -C "${repo_root}" check-ref-format --allow-onelevel "${repository_revision}" >/dev/null 2>&1 ||
      ! git -C "${repo_root}" show-ref --verify --quiet "refs/tags/${repository_revision}"; then
      echo "Invalid Phase 65.5 licensing checklist value: repository_revision must be a 40-character commit SHA or reviewed Git tag" >&2
      exit 1
    fi
  fi
  if ! git -C "${repo_root}" rev-parse --verify --quiet "${repository_revision}^{commit}" >/dev/null; then
    echo "Invalid Phase 65.5 licensing checklist value: repository_revision must resolve to a Git commit or tag" >&2
    exit 1
  fi
}

require_repository_revision_contains_checklist_evidence() {
  local repository_revision required_path

  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "repository_revision")")"
  for required_path in \
    "README.md" \
    "${doc_path}" \
    "${checklist_path}" \
    "scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh" \
    "scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh"; do
    if ! git -C "${repo_root}" cat-file -e "${repository_revision}^{commit}:${required_path}" >/dev/null 2>&1; then
      echo "Invalid Phase 65.5 licensing checklist value: repository_revision must contain ${required_path}" >&2
      exit 1
    fi
  done

  if ! git -C "${repo_root}" grep -F -- "Phase 65.5 OSS licensing and redistribution review checklist" "${repository_revision}^{commit}" -- README.md >/dev/null 2>&1; then
    echo "Invalid Phase 65.5 licensing checklist value: repository_revision must contain the Phase 65.5 README link" >&2
    exit 1
  fi
}

require_repository_revision_matches_current_record() {
  local repository_revision required_path referenced_blob current_blob

  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "repository_revision")")"
  for required_path in \
    "${doc_path}" \
    "${checklist_path}" \
    "scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh" \
    "scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh"; do
    referenced_blob="$(git -C "${repo_root}" show "${repository_revision}^{commit}:${required_path}")"
    current_blob="$(cat "${repo_root}/${required_path}")"
    if [[ "${referenced_blob}" != "${current_blob}" ]]; then
      echo "Invalid Phase 65.5 licensing checklist value: repository_revision must reproduce current ${required_path}" >&2
      exit 1
    fi
  done
}

require_release_identifier_binding() {
  local release_bundle_identifier repository_revision

  release_bundle_identifier="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "release_bundle_identifier")")"
  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "repository_revision")")"
  if [[ "${release_bundle_identifier}" != "aegisops-beta-${repository_revision}" ]]; then
    echo "Invalid Phase 65.5 licensing checklist value: release_bundle_identifier must bind to repository_revision" >&2
    exit 1
  fi
}

require_quoted_approval_record() {
  if ! grep -Fxq 'approval_record: "issue #1382"' "${absolute_checklist_path}"; then
    echo "Invalid Phase 65.5 licensing checklist value: approval_record must quote issue #1382" >&2
    exit 1
  fi
}

validate_top_level_checklist_keys() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      checklist_identifier
      inventory_identifier
      release_bundle_identifier
      repository_revision
      review_owner
      reviewed_date
      phase65_inventory_reference
      competitive_gap_reference
      wazuh_profile_reference
      shuffle_profile_reference
      verifier_output_reference
      approval_record
      wazuh_boundary
      shuffle_boundary
      blocker_disposition
      conclusion
      non_claims
      artifact_scope
    );
    my %seen;

    for my $line (split /\n/, $text) {
      if ($line =~ /^(<<)\s*:/) {
        die "Invalid Phase 65.5 licensing checklist top-level field: $1\n";
      }
      if ($line =~ /^\?\s*([^[:space:]].*?)\s*$/ || $line =~ /^:\s*([^[:space:]].*?)\s*$/) {
        die "Invalid Phase 65.5 licensing checklist top-level field: $1\n";
      }
      my $first = substr($line, 0, 1);
      if ($first eq "\"" || $first eq chr(39)) {
        my $quote = $first;
        if ($line =~ /^\Q$quote\E([^:]+)\Q$quote\E\s*:/) {
          die "Invalid Phase 65.5 licensing checklist top-level field: $1\n";
        }
      }
      next unless $line =~ /^([A-Za-z0-9_-]+):/;
      my $key = $1;
      die "Invalid Phase 65.5 licensing checklist top-level field: $key\n" unless $allowed{$key};
      die "Invalid Phase 65.5 licensing checklist duplicate top-level field: $key\n" if $seen{$key}++;
    }
  ' "${absolute_checklist_path}"
}

validate_named_mapping() {
  local block="$1"
  shift
  local required_keys=("$@")

  BLOCK="${block}" REQUIRED_KEYS="$(IFS=","; printf '%s' "${required_keys[*]}")" perl -Mstrict -Mwarnings -e '
    my $text = $ENV{"BLOCK"} // "";
    my @required = split /,/, ($ENV{"REQUIRED_KEYS"} // "");
    my %seen;
    for my $line (split /\n/, $text) {
      next unless $line =~ /^  ([A-Za-z0-9_]+):\s*(.*?)\s*$/;
      my ($key, $value) = ($1, $2);
      $value =~ s/^\s+|\s+$//g;
      die "Missing Phase 65.5 licensing checklist value: $key\n" if $value eq "" || $value =~ /^[>|][+-]?$/ || lc($value) =~ /^(todo|tbd|null|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/;
      $seen{$key}++;
    }
    for my $key (@required) {
      die "Missing Phase 65.5 licensing checklist value: $key\n" unless $seen{$key};
      die "Invalid Phase 65.5 licensing checklist value: $key\n" if $seen{$key} != 1;
    }
  '
}

mapping_block() {
  local key="$1"

  awk -v key="${key}" '
    $0 == key ":" {
      in_block = 1
      print
      next
    }
    in_block && /^[A-Za-z0-9_-]+:/ {
      exit
    }
    in_block {
      print
    }
  ' "${absolute_checklist_path}"
}

validate_non_claims_block() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      legal_advice
      production_distribution_approval
      external_distribution_approval
      upstream_redistribution_approval
      upstream_license_modification
      entitlement_enforcement
      rc_readiness
      ga_readiness
      commercial_replacement_readiness
    );
    my %seen;
    my $in_non_claims = 0;
    my $block_count = 0;

    for my $line (split /\n/, $text) {
      if ($line =~ /^non_claims:\s*$/) {
        $in_non_claims = 1;
        $block_count++;
        next;
      }
      if ($line =~ /^non_claims:\s*\S/) {
        die "Invalid Phase 65.5 licensing checklist value: non_claims\n";
      }
      if ($line =~ /^[^[:space:]]/ && $line !~ /^non_claims:/) {
        $in_non_claims = 0;
      }
      next unless $in_non_claims;
      next if $line =~ /^\s*$/;
      if ($line =~ /^  ([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        my ($key, $value) = ($1, $2);
        $value =~ s/^\s+|\s+$//g;
        die "Invalid Phase 65.5 licensing checklist value: $key\n" unless $allowed{$key};
        die "Invalid Phase 65.5 licensing checklist value: $key\n" unless $value eq "false";
        $seen{$key}++;
        next;
      }
      die "Invalid Phase 65.5 licensing checklist value: non_claims\n";
    }

    die "Missing Phase 65.5 licensing checklist value: non_claims\n" if $block_count == 0;
    die "Invalid Phase 65.5 licensing checklist value: non_claims\n" if $block_count != 1;
    for my $key (sort keys %allowed) {
      die "Missing Phase 65.5 licensing checklist value: $key\n" unless $seen{$key};
      die "Invalid Phase 65.5 licensing checklist value: $key\n" if $seen{$key} != 1;
    }
  ' "${absolute_checklist_path}"
}

reject_unsafe_reference() {
  local reference="$1"
  local description="$2"
  local lower_reference
  local macos_home_segment linux_home_segment root_home_segment

  reference="$(normalize_yaml_scalar "${reference}")"
  lower_reference="$(printf '%s' "${reference}" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "${reference}" || "${reference}" =~ ^[!\&] || "${reference}" =~ ^/ || "${reference}" =~ ^~ || "${reference}" =~ (^|/)\.\.(/|$) || "${lower_reference}" == *"%2e"* || "${lower_reference}" == *"%2f"* || "${reference}" == *"\\"* || "${lower_reference}" =~ ^[a-z][a-z0-9+.-]*: ]]; then
    echo "Invalid Phase 65.5 licensing checklist ${description}: ${reference}" >&2
    exit 1
  fi
  macos_home_segment="/""Users/"
  linux_home_segment="/""home/"
  root_home_segment="/""root"
  if [[ "${reference}" =~ ^(C:|c:|[A-Za-z]:\\) || "${reference}" == *"${macos_home_segment}"* || "${reference}" == *"${linux_home_segment}"* || "${reference}" == "${root_home_segment}" || "${reference}" == "${root_home_segment}/"* ]]; then
    echo "Invalid Phase 65.5 licensing checklist ${description}: ${reference}" >&2
    exit 1
  fi
  if [[ "${lower_reference}" =~ (^|/)customer-private(/|$) || "${lower_reference}" =~ (^|/)customer_private(/|$) ]]; then
    echo "Invalid Phase 65.5 licensing checklist ${description}: ${reference}" >&2
    exit 1
  fi
}

validate_artifact_scope() {
  REPO_ROOT="${repo_root}" perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my @scope_lines;
    my $scope_key_count = 0;
    my $in_scope = 0;
    for my $line (split /\n/, $text) {
      if ($line =~ /^artifact_scope:\s*$/) {
        $scope_key_count++;
        $in_scope = 1;
        next;
      }
      if ($in_scope && $line =~ /^[A-Za-z0-9_-]+:/) {
        $in_scope = 0;
      }
      push @scope_lines, $line if $in_scope;
    }
    die "Missing Phase 65.5 licensing checklist artifact_scope\n" if $scope_key_count == 0;
    die "Invalid Phase 65.5 licensing checklist artifact_scope\n" if $scope_key_count != 1;

    my $scope_text = "\n" . join("\n", @scope_lines);
    for my $line (@scope_lines) {
      die "Invalid Phase 65.5 licensing checklist artifact_scope\n" if $line =~ /^  -\s/ && $line !~ /^  - artifact_class:\s*/;
    }
    my @blocks = split /\n  - artifact_class:\s*/, $scope_text;
    shift @blocks;
    my %expected_owner = (
      "aegisops-code-docs" => "AegisOps maintainers",
      "wazuh-profile-package" => "Platform maintainers",
      "shuffle-profile-package" => "Platform maintainers",
      "workflow-templates" => "IT Operations, Information Systems Department",
      "generated-artifacts" => "Platform maintainers",
      "third-party-dependencies" => "Platform maintainers",
      "support-bundle-examples" => "IT Operations, Information Systems Department",
    );
    my %expected_reference = (
      "aegisops-code-docs" => "docs/phase-65-1-release-bundle-inventory.md",
      "wazuh-profile-package" => "docs/deployment/wazuh-smb-single-node-profile-contract.md",
      "shuffle-profile-package" => "docs/deployment/shuffle-smb-single-node-profile-contract.md",
      "workflow-templates" => "docs/deployment/shuffle-reviewed-workflow-template-contract.md",
      "generated-artifacts" => "docs/phase-65-4-integrity-evidence-contract.md",
      "third-party-dependencies" => "docs/phase-65-2-offline-install-bundle-contract.md",
      "support-bundle-examples" => "docs/phase-58-6-support-bundle-redaction-contract.md",
    );
    my %seen;
    my @required = qw(scope_owner scope_reference redistribution_posture blocker_status boundary_note);
    my %allowed_field = map { $_ => 1 } @required;

    sub normalize_scalar {
      my ($value) = @_;
      $value =~ s/^\s+|\s+$//g;
      if ($value =~ /^"(.*)"$/s || $value =~ /^'\''(.*)'\''$/s) {
        $value = $1;
      }
      return $value;
    }

    sub scope_fields {
      my ($block, $artifact_class) = @_;
      my %fields;
      for my $line (split /\n/, $block) {
        next unless $line =~ /^    ([A-Za-z0-9_-]+):\s*(.*?)\s*$/;
        my ($key, $value) = ($1, normalize_scalar($2));
        die "Invalid Phase 65.5 licensing checklist artifact field for $artifact_class: $key\n" unless $allowed_field{$key};
        die "Invalid Phase 65.5 licensing checklist duplicate artifact field for $artifact_class: $key\n" if exists $fields{$key};
        $fields{$key} = $value;
      }
      return %fields;
    }

    die "Missing Phase 65.5 licensing checklist artifact_scope\n" unless @blocks;
    for my $block (@blocks) {
      my ($artifact_class) = $block =~ /^([^\n]+)\n/;
      $artifact_class = normalize_scalar($artifact_class) if defined $artifact_class;
      die "Missing Phase 65.5 licensing checklist artifact_class\n" unless defined $artifact_class && length $artifact_class;
      die "Invalid Phase 65.5 licensing checklist artifact_class: $artifact_class\n" unless exists $expected_owner{$artifact_class};
      die "Invalid Phase 65.5 licensing checklist duplicate artifact_class: $artifact_class\n" if $seen{$artifact_class}++;
      my %fields = scope_fields($block, $artifact_class);

      for my $required (@required) {
        my $value = $fields{$required} // "";
        die "Missing Phase 65.5 licensing checklist $required for $artifact_class\n" unless length $value;
        my $lower = lc $value;
        die "Missing Phase 65.5 licensing checklist $required for $artifact_class\n" if $lower =~ /^(todo|tbd|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/;
      }

      die "Invalid Phase 65.5 licensing checklist scope_owner for $artifact_class\n" unless $fields{"scope_owner"} eq $expected_owner{$artifact_class};
      die "Invalid Phase 65.5 licensing checklist scope_reference for $artifact_class\n" unless $fields{"scope_reference"} eq $expected_reference{$artifact_class};
      die "Invalid Phase 65.5 licensing checklist blocker_status for $artifact_class\n" unless $fields{"blocker_status"} =~ /^(none_for_checklist_record|blocked:[A-Za-z0-9_.-]+)$/;
      die "Invalid Phase 65.5 licensing checklist redistribution_posture for $artifact_class\n" unless lc($fields{"redistribution_posture"}) =~ /(license|upstream|repo-owned|generated|dependency|redacted|attribution|review)/;
      die "Invalid Phase 65.5 licensing checklist boundary_note for $artifact_class\n" unless lc($fields{"boundary_note"}) =~ /(evidence|truth|readiness|approval|authority|release|gate|workflow|redistribution)/;
    }

    for my $artifact_class (sort keys %expected_owner) {
      die "Missing Phase 65.5 licensing checklist artifact_class: $artifact_class\n" unless $seen{$artifact_class};
    }
  ' "${absolute_checklist_path}"

  while IFS= read -r reference; do
    reject_unsafe_reference "${reference}" "scope reference"
  done < <(
    grep -E '^[[:space:]]+scope_reference:' "${absolute_checklist_path}" |
      sed -E 's/^[[:space:]]+scope_reference:[[:space:]]*//'
  )
}

reject_forbidden_claims() {
  local file="$1"
  local description="$2"
  local text

  if [[ "${description}" == "README.md" ]]; then
    text="$(visible_text "${file}" | grep -F "Phase 65.5 OSS licensing and redistribution review checklist" | tr '\n' ' ')"
  else
    text="$(visible_text "${file}" | tr '\n' ' ')"
  fi
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(not|without|does not claim|must not|cannot|no)\b[^.]{0,320}\b(legal advice|production distribution approval|external distribution approval|upstream redistribution approval|RC readiness|GA readiness|commercial replacement readiness|entitlement enforcement|verifier truth|issue-lint truth|readiness truth|release truth|gate truth|legal truth|license truth|redistribution truth)\b[^.]*//gi')"
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(non-claims? for|reject|rejects|must reject)\b[^.]{0,220}\b(legal[- ]advice claims?|production distribution approval claims?|external distribution approval claims?|inferred RC pass|inferred GA pass|verifier-as-readiness-truth claims?|issue-lint-as-readiness-truth claims?|RC readiness|GA readiness|commercial replacement readiness)\b[^.]*//gi')"
  if grep -Eiq '(AegisOps|Phase 65\.5|licensing|redistribution|checklist|Wazuh|Shuffle).{0,80}(is|are|provides?|proves?|satisfies?|approves?|grants?|confirms?|establishes?|unblocks?|passes?|clears?|certifies?|authorizes?|marks?).{0,60}(legal advice|production distribution approved|production distribution approval|external distribution approved|external distribution approval|upstream redistribution approved|RC ready|RC readiness|GA ready|GA readiness|commercial replacement|entitlement enforcement)' <<<"${text}"; then
    echo "Forbidden Phase 65.5 licensing checklist claim in ${description}: legal, redistribution, readiness, or authority overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(AegisOps|Phase 65\.5|licensing|redistribution|checklist|Wazuh|Shuffle).{0,80}(is|are).{0,30}(Beta|RC|GA)[ -]*(gate[ -]*)?(accepted|approved|passed|ready|complete)' <<<"${text}"; then
    echo "Forbidden Phase 65.5 licensing checklist claim in ${description}: gate acceptance overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(verifier|issue-lint).{0,60}(is|are|becomes?|proves?|satisfies?|approves?).{0,40}(readiness truth|release truth|gate truth|legal truth|license truth|redistribution truth|RC readiness|GA readiness)' <<<"${text}"; then
    echo "Forbidden Phase 65.5 licensing checklist claim in ${description}: verifier or issue-lint truth shortcut" >&2
    exit 1
  fi
  if grep -Eiq '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|password[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|secret[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|token[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+)' <<<"${text}"; then
    echo "Forbidden Phase 65.5 licensing checklist material in ${description}: production secret material" >&2
    exit 1
  fi
  if grep -Eiq '((customer-private|customer private).{0,40}(included|includes|packaged|embedded|allowed|contains?|containing|present|stored|retained|carries|holds)|(contains?|includes?|stores?|retains?|carries|holds).{0,40}(customer-private|customer private))' <<<"${text}"; then
    echo "Forbidden Phase 65.5 licensing checklist material in ${description}: customer-private data" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.5 OSS licensing and redistribution review checklist"
require_file "${absolute_checklist_path}" "Phase 65.5 OSS licensing and redistribution checklist record"
require_file "${readme_path}" "README for Phase 65.5 checklist link check"
require_file "${repo_root}/docs/phase-65-1-release-bundle-inventory.md" "Phase 65.1 release bundle inventory reference"
require_file "${repo_root}/docs/phase-65-2-offline-install-bundle-contract.md" "Phase 65.2 offline install bundle contract reference"
require_file "${repo_root}/docs/phase-65-4-integrity-evidence-contract.md" "Phase 65.4 integrity evidence contract reference"
require_file "${repo_root}/docs/phase-51-5-competitive-gap-matrix.md" "Phase 51.5 competitive gap matrix reference"
require_file "${repo_root}/docs/phase-58-6-support-bundle-redaction-contract.md" "Phase 58.6 support bundle redaction contract reference"
require_file "${repo_root}/docs/deployment/wazuh-smb-single-node-profile-contract.md" "Wazuh profile contract reference"
require_file "${repo_root}/docs/deployment/shuffle-smb-single-node-profile-contract.md" "Shuffle profile contract reference"
require_file "${repo_root}/docs/deployment/shuffle-reviewed-workflow-template-contract.md" "Shuffle reviewed workflow template contract reference"

require_phrase "${readme_path}" "- [Phase 65.5 OSS licensing and redistribution review checklist](docs/phase-65-5-oss-licensing-redistribution-checklist.md)" "README canonical cross-phase boundary bullet"

required_doc_phrases=()
while IFS= read -r phrase; do
  required_doc_phrases+=("${phrase}")
done <<'EOF_REQUIRED_DOC_PHRASES'
# Phase 65.5 OSS Licensing And Redistribution Review Checklist
**Status**: Accepted as the Phase 65 OSS licensing and redistribution review checklist for beta/design-partner packaging review only.
checklist identifier `phase-65-oss-licensing-redistribution-checklist-v1`
docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml
Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`
review owner;
reviewed date;
artifact scope for every reviewed class;
redistribution posture for every reviewed class;
Wazuh packaging boundary notes;
Shuffle packaging boundary notes;
blocker disposition;
conclusion;
| `wazuh-profile-package` | Platform maintainers | Wazuh profile files, version pins, and setup references may be included as AegisOps-authored configuration evidence only; upstream Wazuh images, binaries, dashboards, rules, and license text require separate reviewed upstream redistribution approval before inclusion. | Wazuh remains a subordinate detection substrate and does not become AegisOps release, gate, workflow, or readiness truth. |
| `shuffle-profile-package` | Platform maintainers | Shuffle profile files, workflow template contracts, and setup references may be included as AegisOps-authored configuration evidence only; upstream Shuffle images, app bundles, workflow exports, dependencies, and license text require separate reviewed upstream redistribution approval before inclusion. | Shuffle remains a subordinate routine automation substrate and does not become AegisOps release, gate, execution, reconciliation, or readiness truth. |
Missing owner, reviewed date, artifact scope, redistribution posture, Wazuh posture, Shuffle posture, blocker disposition, conclusion, verifier output reference, or non-claim signal must block the checklist record.
AegisOps must not embed, mirror, sublicense, or imply redistribution approval for upstream Wazuh images, binaries, dashboards, rules, generated configs, or license text without a separate reviewed upstream redistribution record.
AegisOps must not embed, mirror, sublicense, or imply redistribution approval for upstream Shuffle images, app bundles, workflow exports, dependencies, generated configs, or license text without a separate reviewed upstream redistribution record.
bash scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh
bash scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1382 --config <supervisor-config-path>
The verifier must reject missing owner, missing reviewed date, missing Wazuh posture, missing Shuffle posture, missing conclusion, missing blocker disposition, legal-advice claims, production distribution approval claims, external distribution approval claims, inferred RC pass, inferred GA pass, verifier-as-readiness-truth claims, and issue-lint-as-readiness-truth claims.
This checklist does not claim legal advice, production distribution approval, external distribution approval, upstream redistribution approval, upstream license modification, production entitlement enforcement, billing readiness, Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production signing approval, production support readiness, or design-partner evidence completeness.
EOF_REQUIRED_DOC_PHRASES

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.5 licensing checklist term in ${doc_path}"
done

require_top_level_equals_once "checklist_identifier" "phase-65-oss-licensing-redistribution-checklist-v1"
require_top_level_equals_once "inventory_identifier" "phase-65-release-bundle-inventory-v1"
require_top_level_present_once "release_bundle_identifier"
require_top_level_present_once "repository_revision"
require_top_level_present_once "review_owner"
require_top_level_present_once "reviewed_date"
require_top_level_equals_once "phase65_inventory_reference" "docs/phase-65-1-release-bundle-inventory.md"
require_top_level_equals_once "competitive_gap_reference" "docs/phase-51-5-competitive-gap-matrix.md"
require_top_level_equals_once "wazuh_profile_reference" "docs/deployment/wazuh-smb-single-node-profile-contract.md"
require_top_level_equals_once "shuffle_profile_reference" "docs/deployment/shuffle-smb-single-node-profile-contract.md"
require_top_level_equals_once "verifier_output_reference" "bash scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh"
require_top_level_equals_once "approval_record" "issue #1382"
require_quoted_approval_record
require_top_level_present_once "conclusion"
require_top_level_sequence_key_once "artifact_scope"

reviewed_date="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "reviewed_date")")"
if [[ ! "${reviewed_date}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid Phase 65.5 licensing checklist value: reviewed_date" >&2
  exit 1
fi

require_repository_revision_resolves
require_repository_revision_contains_checklist_evidence
require_release_identifier_binding
validate_top_level_checklist_keys
validate_named_mapping "$(mapping_block "wazuh_boundary")" "redistribution_posture" "package_boundary_notes" "authority_boundary"
validate_named_mapping "$(mapping_block "shuffle_boundary")" "redistribution_posture" "package_boundary_notes" "authority_boundary"
validate_named_mapping "$(mapping_block "blocker_disposition")" "open_blockers" "disposition"
validate_non_claims_block
validate_artifact_scope

wazuh_block="$(mapping_block "wazuh_boundary" | tr '\n' ' ')"
if ! grep -Eiq 'upstream Wazuh.*separate reviewed upstream redistribution approval' <<<"${wazuh_block}" ||
  ! grep -Eiq 'subordinate detection substrate' <<<"${wazuh_block}"; then
  echo "Missing Phase 65.5 licensing checklist Wazuh posture" >&2
  exit 1
fi

shuffle_block="$(mapping_block "shuffle_boundary" | tr '\n' ' ')"
if ! grep -Eiq 'upstream Shuffle.*separate reviewed upstream redistribution approval' <<<"${shuffle_block}" ||
  ! grep -Eiq 'subordinate routine automation substrate' <<<"${shuffle_block}"; then
  echo "Missing Phase 65.5 licensing checklist Shuffle posture" >&2
  exit 1
fi

conclusion="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_checklist_path}" "conclusion")")"
if ! grep -Eiq 'beta/design-partner packaging review only' <<<"${conclusion}"; then
  echo "Invalid Phase 65.5 licensing checklist value: conclusion" >&2
  exit 1
fi
if grep -Eiq '(legal advice|production distribution approval|external distribution approval|RC readiness|GA readiness|commercial replacement readiness)' <<<"${conclusion}"; then
  echo "Forbidden Phase 65.5 licensing checklist claim in checklist record: conclusion overclaim" >&2
  exit 1
fi

while IFS= read -r reference; do
  reject_unsafe_reference "${reference}" "top-level reference"
done < <(
  grep -E '^[A-Za-z0-9_]+_reference:' "${absolute_checklist_path}" |
    sed -E 's/^[A-Za-z0-9_]+_reference:[[:space:]]*//'
)

reject_forbidden_claims "${absolute_doc_path}" "${doc_path}"
reject_forbidden_claims "${absolute_checklist_path}" "${checklist_path}"
reject_forbidden_claims "${readme_path}" "README.md"

require_repository_revision_matches_current_record

echo "Phase 65.5 OSS licensing and redistribution checklist verification passed"
