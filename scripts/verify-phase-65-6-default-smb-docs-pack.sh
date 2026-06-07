#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-65-6-default-smb-documentation-pack.md"
manifest_path="docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
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

yaml_top_level_scalar() {
  local key="$1"

  perl -Mstrict -Mwarnings -0 -e '
    my $key = shift @ARGV;
    my $text = <>;
    for my $line (split /\n/, $text) {
      if ($line =~ /^\Q$key\E:\s*(.*?)\s*$/) {
        print "$1\n";
        last;
      }
    }
  ' "${key}" "${absolute_manifest_path}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

yaml_top_level_scalar_count() {
  local key="$1"

  grep -Ec "^${key}:[[:space:]]*" "${absolute_manifest_path}" || true
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

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${key}")")"
  count="$(yaml_top_level_scalar_count "${key}")"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.6 docs pack value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" || "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.6 docs pack value: ${key}" >&2
    exit 1
  fi
}

require_top_level_present_once() {
  local key="$1"
  local actual count

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${key}")")"
  count="$(yaml_top_level_scalar_count "${key}")"
  if [[ "${count}" == "0" || "$(is_placeholder_or_missing "${actual}"; echo $?)" == "0" ]]; then
    echo "Missing Phase 65.6 docs pack value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.6 docs pack value: ${key}" >&2
    exit 1
  fi
}

require_quoted_approval_record() {
  if ! grep -Fxq 'approval_record: "issue #1385"' "${absolute_manifest_path}"; then
    echo "Invalid Phase 65.6 docs pack value: approval_record must quote issue #1385" >&2
    exit 1
  fi
}

validate_top_level_keys() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      docs_pack_identifier
      inventory_identifier
      pack_owner
      reviewed_date
      beta_scope
      pack_contract_reference
      phase65_inventory_reference
      phase51_gate_boundary_reference
      support_bundle_boundary_reference
      upgrade_rollback_boundary_reference
      verifier_output_reference
      approval_record
      authority_boundary
      non_claims
      topics
    );
    my %seen;

    for my $line (split /\n/, $text) {
      if ($line =~ /^(<<)\s*:/) {
        die "Invalid Phase 65.6 docs pack top-level field: $1\n";
      }
      if ($line =~ /^\?\s*([^[:space:]].*?)\s*$/ || $line =~ /^:\s*([^[:space:]].*?)\s*$/) {
        die "Invalid Phase 65.6 docs pack top-level field: $1\n";
      }
      my $first = substr($line, 0, 1);
      if ($first eq "\"" || $first eq chr(39)) {
        my $quote = $first;
        if ($line =~ /^\Q$quote\E([^:]+)\Q$quote\E\s*:/) {
          die "Invalid Phase 65.6 docs pack top-level field: $1\n";
        }
      }
      next unless $line =~ /^([A-Za-z0-9_-]+):/;
      my $key = $1;
      die "Invalid Phase 65.6 docs pack top-level field: $key\n" unless $allowed{$key};
      die "Invalid Phase 65.6 docs pack duplicate top-level field: $key\n" if $seen{$key}++;
    }
  ' "${absolute_manifest_path}"
}

validate_non_claims_block() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      first_user_rc_success
      support_bundle_completion_for_rc
      production_support_readiness
      rc_readiness
      ga_readiness
      self_service_commercial_readiness
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
        die "Invalid Phase 65.6 docs pack value: non_claims\n";
      }
      if ($line =~ /^[^[:space:]]/ && $line !~ /^non_claims:/) {
        $in_non_claims = 0;
      }
      next unless $in_non_claims;
      next if $line =~ /^\s*$/;
      if ($line =~ /^  ([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        my ($key, $value) = ($1, $2);
        $value =~ s/^\s+|\s+$//g;
        die "Invalid Phase 65.6 docs pack value: $key\n" unless $allowed{$key};
        die "Invalid Phase 65.6 docs pack value: $key\n" unless $value eq "false";
        $seen{$key}++;
        next;
      }
      die "Invalid Phase 65.6 docs pack value: non_claims\n";
    }

    die "Missing Phase 65.6 docs pack value: non_claims\n" if $block_count == 0;
    die "Invalid Phase 65.6 docs pack value: non_claims\n" if $block_count != 1;
    for my $key (sort keys %allowed) {
      die "Missing Phase 65.6 docs pack value: $key\n" unless $seen{$key};
      die "Invalid Phase 65.6 docs pack value: $key\n" if $seen{$key} != 1;
    }
  ' "${absolute_manifest_path}"
}

reject_unsafe_reference() {
  local reference="$1"
  local description="$2"
  local lower_reference
  local macos_home_segment linux_home_segment root_home_segment

  reference="$(normalize_yaml_scalar "${reference}")"
  lower_reference="$(printf '%s' "${reference}" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "${reference}" || "${reference}" =~ ^[!\&] || "${reference}" =~ ^/ || "${reference}" =~ ^~ || "${reference}" =~ (^|/)\.\.(/|$) || "${lower_reference}" == *"%2e"* || "${lower_reference}" == *"%2f"* || "${reference}" == *"\\"* || "${lower_reference}" =~ ^[a-z][a-z0-9+.-]*: ]]; then
    echo "Invalid Phase 65.6 docs pack ${description}: ${reference}" >&2
    exit 1
  fi
  macos_home_segment="/""Users/"
  linux_home_segment="/""home/"
  root_home_segment="/""root"
  if [[ "${reference}" =~ ^(C:|c:|[A-Za-z]:\\) || "${reference}" == *"${macos_home_segment}"* || "${reference}" == *"${linux_home_segment}"* || "${reference}" == "${root_home_segment}" || "${reference}" == "${root_home_segment}/"* ]]; then
    echo "Invalid Phase 65.6 docs pack ${description}: ${reference}" >&2
    exit 1
  fi
  if [[ "${lower_reference}" =~ (^|/)customer-private(/|$) || "${lower_reference}" =~ (^|/)customer_private(/|$) ]]; then
    echo "Invalid Phase 65.6 docs pack ${description}: ${reference}" >&2
    exit 1
  fi
}

validate_topics() {
  REPO_ROOT="${repo_root}" perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my $repo_root = $ENV{"REPO_ROOT"} // "";
    my @topic_lines;
    my $topic_key_count = 0;
    my $in_topics = 0;
    for my $line (split /\n/, $text) {
      if ($line =~ /^topics:\s*$/) {
        $topic_key_count++;
        $in_topics = 1;
        next;
      }
      if ($in_topics && $line =~ /^[A-Za-z0-9_-]+:/) {
        $in_topics = 0;
      }
      push @topic_lines, $line if $in_topics;
    }
    die "Missing Phase 65.6 docs pack topics\n" if $topic_key_count == 0;
    die "Invalid Phase 65.6 docs pack topics\n" if $topic_key_count != 1;

    my $topic_text = "\n" . join("\n", @topic_lines);
    for my $line (@topic_lines) {
      die "Invalid Phase 65.6 docs pack topics\n" if $line =~ /^  -\s/ && $line !~ /^  - topic:\s*/;
    }
    my @blocks = split /\n  - topic:\s*/, $topic_text;
    shift @blocks;
    my %expected_primary = (
      "installation" => "docs/phase-65-2-offline-install-bundle-contract.md",
      "daily-operation" => "docs/runbook.md",
      "source-onboarding" => "docs/source-onboarding-contract.md",
      "automation-catalog" => "docs/phase-62-reviewed-automation-catalog-contract.md",
      "ai-usage" => "docs/phase-59-3-ai-trace-lifecycle-contract.md",
      "backup-and-restore" => "docs/phase-58-3-backup-command-contract.md",
      "support-bundle" => "docs/phase-58-6-support-bundle-redaction-contract.md",
      "upgrade-and-rollback" => "docs/phase-58-5-upgrade-rollback-plan-contract.md",
    );
    my %expected_supporting = (
      "installation" => "docs/deployment/first-user-stack.md",
      "daily-operation" => "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md",
      "source-onboarding" => "docs/phase-61-minimum-source-catalog-contract.md",
      "automation-catalog" => "docs/phase-62-5-manual-fallback-contract.md",
      "ai-usage" => "docs/phase-59-4-ai-disabled-degraded-mode-contract.md",
      "backup-and-restore" => "docs/phase-58-4-restore-dry-run-contract.md",
      "support-bundle" => "docs/deployment/operator-training-handoff-packet.md",
      "upgrade-and-rollback" => "docs/phase-65-3-release-channel-upgrade-manifest-contract.md",
    );
    my %seen;
    my @required = qw(owner primary_reference supporting_reference beta_scope boundary_note);
    my %allowed_field = map { $_ => 1 } @required;

    sub normalize_scalar {
      my ($value) = @_;
      $value =~ s/^\s+|\s+$//g;
      if ($value =~ /^"(.*)"$/s || $value =~ /^'\''(.*)'\''$/s) {
        $value = $1;
      }
      return $value;
    }

    sub topic_fields {
      my ($block, $topic) = @_;
      my %fields;
      for my $line (split /\n/, $block) {
        next unless $line =~ /^    ([A-Za-z0-9_-]+):\s*(.*?)\s*$/;
        my ($key, $value) = ($1, normalize_scalar($2));
        die "Invalid Phase 65.6 docs pack topic field for $topic: $key\n" unless $allowed_field{$key};
        die "Invalid Phase 65.6 docs pack duplicate topic field for $topic: $key\n" if exists $fields{$key};
        $fields{$key} = $value;
      }
      return %fields;
    }

    die "Missing Phase 65.6 docs pack topics\n" unless @blocks;
    for my $block (@blocks) {
      my ($topic) = $block =~ /^([^\n]+)\n/;
      $topic = normalize_scalar($topic) if defined $topic;
      die "Missing Phase 65.6 docs pack topic\n" unless defined $topic && length $topic;
      die "Invalid Phase 65.6 docs pack topic: $topic\n" unless exists $expected_primary{$topic};
      die "Invalid Phase 65.6 docs pack duplicate topic: $topic\n" if $seen{$topic}++;
      my %fields = topic_fields($block, $topic);

      for my $required (@required) {
        my $value = $fields{$required} // "";
        die "Missing Phase 65.6 docs pack $required for $topic\n" unless length $value;
        my $lower = lc $value;
        die "Missing Phase 65.6 docs pack $required for $topic\n" if $lower =~ /^(todo|tbd|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/;
      }

      die "Invalid Phase 65.6 docs pack primary_reference for $topic\n" unless $fields{"primary_reference"} eq $expected_primary{$topic};
      die "Invalid Phase 65.6 docs pack supporting_reference for $topic\n" unless $fields{"supporting_reference"} eq $expected_supporting{$topic};
      die "Invalid Phase 65.6 docs pack beta_scope for $topic\n" unless $fields{"beta_scope"} =~ /^beta-design-partner-/;
      die "Invalid Phase 65.6 docs pack boundary_note for $topic\n" unless lc($fields{"boundary_note"}) =~ /(not|cannot|do not)/;

      for my $reference ($fields{"primary_reference"}, $fields{"supporting_reference"}) {
        die "Missing Phase 65.6 docs pack referenced file for $topic: $reference\n" unless -s "$repo_root/$reference";
      }
    }

    for my $topic (sort keys %expected_primary) {
      die "Missing Phase 65.6 docs pack topic: $topic\n" unless $seen{$topic};
    }
  ' "${absolute_manifest_path}"

  while IFS= read -r reference; do
    reject_unsafe_reference "${reference}" "topic reference"
  done < <(
    grep -E '^[[:space:]]+(primary_reference|supporting_reference):' "${absolute_manifest_path}" |
      sed -E 's/^[[:space:]]+[A-Za-z_]+:[[:space:]]*//'
  )
}

reject_forbidden_claims() {
  local file="$1"
  local description="$2"
  local text

  if [[ "${description}" == "README.md" ]]; then
    text="$(visible_text "${file}" | grep -F "Phase 65.6 default SMB documentation pack" | tr '\n' ' ')"
  else
    text="$(visible_text "${file}" | tr '\n' ' ')"
  fi
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(not|without|does not claim|must not|cannot|do not|does not|no)\b[^.]{0,360}\b(first-user RC success|support-bundle completion for RC|production support readiness|RC readiness|GA readiness|self-service commercial readiness|commercial replacement readiness|readiness truth|release truth|gate truth|workflow truth|support truth|documentation truth)\b[^.]*//gi')"
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(not|without|must not|cannot|do not|does not|no)\b[^.]{0,220}\b(customer-private examples?|customer-private data|customer private examples?|customer private data|production secrets?|workstation-local absolute paths?)\b[^.]*//gi')"
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(non-claims? for|reject|rejects|must reject)\b[^.]{0,260}\b(inferred RC pass|inferred GA pass|production support readiness claims?|self-service commercial readiness claims?|RC readiness|GA readiness|commercial replacement readiness)\b[^.]*//gi')"
  text="$(printf '%s' "${text}" | perl -0pe 's/\b(non-claims? for|reject|rejects|must reject)\b[^.]{0,260}\b(customer-private examples?|customer-private data|customer private examples?|customer private data|production secrets?|workstation-local paths?)\b[^.]*//gi')"
  if grep -Eiq '(AegisOps|Phase 65\.6|documentation pack|docs pack|SMB docs|documentation).{0,80}(is|are|provides?|proves?|satisfies?|approves?|grants?|confirms?|establishes?|unblocks?|passes?|clears?|certifies?|authorizes?|marks?|completes?).{0,70}(first-user RC success|support-bundle completion for RC|production support readiness|RC ready|RC readiness|GA ready|GA readiness|self-service commercial readiness|commercial replacement|Beta gate acceptance|RC gate acceptance|GA gate acceptance)' <<<"${text}"; then
    echo "Forbidden Phase 65.6 docs pack claim in ${description}: readiness, support, or gate overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(verifier|issue-lint).{0,60}(is|are|becomes?|proves?|satisfies?|approves?).{0,50}(readiness truth|release truth|gate truth|workflow truth|support truth|documentation truth|RC readiness|GA readiness)' <<<"${text}"; then
    echo "Forbidden Phase 65.6 docs pack claim in ${description}: verifier or issue-lint truth shortcut" >&2
    exit 1
  fi
  if grep -Eiq '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|password[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|secret[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|token[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+)' <<<"${text}"; then
    echo "Forbidden Phase 65.6 docs pack material in ${description}: production secret material" >&2
    exit 1
  fi
  if grep -Eiq '((customer-private|customer private).{0,40}(included|includes|packaged|embedded|allowed|contains?|containing|present|stored|retained|carries|holds|example)|(contains?|includes?|stores?|retains?|carries|holds).{0,40}(customer-private|customer private))' <<<"${text}"; then
    echo "Forbidden Phase 65.6 docs pack material in ${description}: customer-private data" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.6 default SMB documentation pack"
require_file "${absolute_manifest_path}" "Phase 65.6 default SMB documentation pack manifest"
require_file "${readme_path}" "README for Phase 65.6 docs pack link check"
require_file "${repo_root}/docs/phase-65-1-release-bundle-inventory.md" "Phase 65.1 release bundle inventory reference"
require_file "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "Phase 51.3 gate contract reference"
require_file "${repo_root}/docs/phase-58-5-upgrade-rollback-plan-contract.md" "Phase 58.5 upgrade rollback contract reference"
require_file "${repo_root}/docs/phase-58-6-support-bundle-redaction-contract.md" "Phase 58.6 support bundle contract reference"

require_phrase "${readme_path}" "- [Phase 65.6 default SMB documentation pack](docs/phase-65-6-default-smb-documentation-pack.md)" "README canonical cross-phase boundary bullet"

required_doc_phrases=()
while IFS= read -r phrase; do
  required_doc_phrases+=("${phrase}")
done <<'EOF_REQUIRED_DOC_PHRASES'
# Phase 65.6 Default SMB Documentation Pack
**Status**: Accepted as the Phase 65 default SMB documentation pack contract for beta/design-partner packaging review only.
documentation pack identifier `phase-65-default-smb-docs-pack-v1`
docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml
topic coverage for installation, daily operation, source onboarding, automation catalog, AI usage, backup and restore, support bundle, upgrade, and rollback;
| Installation | `docs/phase-65-2-offline-install-bundle-contract.md` | `docs/deployment/first-user-stack.md` |
| Daily operation | `docs/runbook.md` | `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` |
| Source onboarding | `docs/source-onboarding-contract.md` | `docs/phase-61-minimum-source-catalog-contract.md` |
| Automation catalog | `docs/phase-62-reviewed-automation-catalog-contract.md` | `docs/phase-62-5-manual-fallback-contract.md` |
| AI usage | `docs/phase-59-3-ai-trace-lifecycle-contract.md` | `docs/phase-59-4-ai-disabled-degraded-mode-contract.md` |
| Backup and restore | `docs/phase-58-3-backup-command-contract.md` | `docs/phase-58-4-restore-dry-run-contract.md` |
| Support bundle | `docs/phase-58-6-support-bundle-redaction-contract.md` | `docs/deployment/operator-training-handoff-packet.md` |
| Upgrade and rollback | `docs/phase-58-5-upgrade-rollback-plan-contract.md` | `docs/phase-65-3-release-channel-upgrade-manifest-contract.md` |
Migration guidance remains a dedicated Phase 65.7 issue.
Beta known-limitations and design-partner evidence templates remain a dedicated Phase 65.8 issue.
Documentation, manifest entries, screenshots, examples, generated indexes, verifier output, issue-lint output, release notes, support notes, AI text, ticket text, browser state, UI cache, Wazuh state, Shuffle state, and operator-facing summaries are subordinate guidance or packaging evidence only.
bash scripts/verify-phase-65-6-default-smb-docs-pack.sh
bash scripts/test-verify-phase-65-6-default-smb-docs-pack.sh
bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1385 --config <supervisor-config-path>
The verifier must reject missing install docs, missing daily-ops docs, missing source-onboarding docs, missing automation docs, missing AI-usage docs, missing backup/restore docs, missing support-bundle docs, missing upgrade/rollback docs, workstation-local paths, secrets, customer-private examples, inferred RC pass, inferred GA pass, production support readiness claims, and self-service commercial readiness claims.
This documentation pack does not claim first-user RC success, support-bundle completion for RC, production support readiness, Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, live install success, live backup success, live restore success, live upgrade success, live rollback success, migration completion, beta evidence template completion, production entitlement enforcement, billing readiness, or hosted update-service readiness.
EOF_REQUIRED_DOC_PHRASES

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.6 docs pack term in ${doc_path}"
done

require_top_level_equals_once "docs_pack_identifier" "phase-65-default-smb-docs-pack-v1"
require_top_level_equals_once "inventory_identifier" "phase-65-release-bundle-inventory-v1"
require_top_level_present_once "pack_owner"
require_top_level_present_once "reviewed_date"
require_top_level_equals_once "beta_scope" "beta-design-partner-documentation-packaging-review-only"
require_top_level_equals_once "pack_contract_reference" "${doc_path}"
require_top_level_equals_once "phase65_inventory_reference" "docs/phase-65-1-release-bundle-inventory.md"
require_top_level_equals_once "phase51_gate_boundary_reference" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
require_top_level_equals_once "support_bundle_boundary_reference" "docs/phase-58-6-support-bundle-redaction-contract.md"
require_top_level_equals_once "upgrade_rollback_boundary_reference" "docs/phase-58-5-upgrade-rollback-plan-contract.md"
require_top_level_equals_once "verifier_output_reference" "bash scripts/verify-phase-65-6-default-smb-docs-pack.sh"
require_top_level_equals_once "approval_record" "issue #1385"
require_quoted_approval_record
require_top_level_present_once "authority_boundary"

reviewed_date="$(normalize_yaml_scalar "$(yaml_top_level_scalar "reviewed_date")")"
if [[ ! "${reviewed_date}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid Phase 65.6 docs pack value: reviewed_date" >&2
  exit 1
fi

validate_top_level_keys
validate_non_claims_block
validate_topics

while IFS= read -r reference; do
  reject_unsafe_reference "${reference}" "top-level reference"
done < <(
  grep -E '^[A-Za-z0-9_]+_reference:' "${absolute_manifest_path}" |
    sed -E 's/^[A-Za-z0-9_]+_reference:[[:space:]]*//'
)

reject_forbidden_claims "${absolute_doc_path}" "${doc_path}"
reject_forbidden_claims "${absolute_manifest_path}" "${manifest_path}"
reject_forbidden_claims "${readme_path}" "README.md"

echo "Phase 65.6 default SMB documentation pack verification passed"
