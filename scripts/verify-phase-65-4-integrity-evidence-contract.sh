#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-65-4-integrity-evidence-contract.md"
manifest_path="docs/deployment/release/phase-65-4-integrity-evidence.yaml"
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

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_manifest_path}" "${key}")")"
  count="$(yaml_top_level_scalar_count "${absolute_manifest_path}" "${key}")"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.4 integrity manifest value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" || "${actual}" != "${expected}" ]]; then
    echo "Invalid Phase 65.4 integrity manifest value: ${key}" >&2
    exit 1
  fi
}

require_top_level_present_once() {
  local key="$1"
  local actual count

  actual="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_manifest_path}" "${key}")")"
  count="$(yaml_top_level_scalar_count "${absolute_manifest_path}" "${key}")"
  if [[ "${count}" == "0" || "$(is_placeholder_or_missing "${actual}"; echo $?)" == "0" ]]; then
    echo "Missing Phase 65.4 integrity manifest value: ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.4 integrity manifest value: ${key}" >&2
    exit 1
  fi
}

require_top_level_sequence_key_once() {
  local key="$1"
  local count

  count="$(grep -Ec "^${key}:[[:space:]]*$" "${absolute_manifest_path}" || true)"
  if [[ "${count}" == "0" ]]; then
    echo "Missing Phase 65.4 integrity manifest ${key}" >&2
    exit 1
  fi
  if [[ "${count}" != "1" ]]; then
    echo "Invalid Phase 65.4 integrity manifest ${key}" >&2
    exit 1
  fi
}

require_repository_revision_resolves() {
  local repository_revision

  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_manifest_path}" "repository_revision")")"
  if [[ ! "${repository_revision}" =~ ^[0-9a-fA-F]{40}$ ]]; then
    if ! git -C "${repo_root}" check-ref-format --allow-onelevel "${repository_revision}" >/dev/null 2>&1 ||
      ! git -C "${repo_root}" show-ref --verify --quiet "refs/tags/${repository_revision}"; then
      echo "Invalid Phase 65.4 integrity manifest value: repository_revision must be a 40-character commit SHA or reviewed Git tag" >&2
      exit 1
    fi
  fi
  if ! git -C "${repo_root}" rev-parse --verify --quiet "${repository_revision}^{commit}" >/dev/null; then
    echo "Invalid Phase 65.4 integrity manifest value: repository_revision must resolve to a Git commit or tag" >&2
    exit 1
  fi
}

require_release_identifier_binding() {
  local release_bundle_identifier repository_revision

  release_bundle_identifier="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_manifest_path}" "release_bundle_identifier")")"
  repository_revision="$(normalize_yaml_scalar "$(yaml_top_level_scalar "${absolute_manifest_path}" "repository_revision")")"
  if [[ "${release_bundle_identifier}" != "aegisops-beta-${repository_revision}" ]]; then
    echo "Invalid Phase 65.4 integrity manifest value: release_bundle_identifier must bind to repository_revision" >&2
    exit 1
  fi
}

validate_top_level_manifest_keys() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      contract_identifier
      inventory_identifier
      release_bundle_identifier
      repository_revision
      integrity_evidence_owner
      inventory_reference
      phase51_gate_boundary_reference
      verifier_output_reference
      approval_record
      accepted_signing_posture
      authority_boundary
      non_claims
      artifacts
    );

    for my $line (split /\n/, $text) {
      if ($line =~ /^(<<)\s*:/) {
        die "Invalid Phase 65.4 integrity manifest top-level field: $1\n";
      }
      if ($line =~ /^\?\s*([^[:space:]].*?)\s*$/ || $line =~ /^:\s*([^[:space:]].*?)\s*$/) {
        die "Invalid Phase 65.4 integrity manifest top-level field: $1\n";
      }
      my $first = substr($line, 0, 1);
      if ($first eq "\"" || $first eq chr(39)) {
        my $quote = $first;
        if ($line =~ /^\Q$quote\E([^:]+)\Q$quote\E\s*:/) {
          die "Invalid Phase 65.4 integrity manifest top-level field: $1\n";
        }
      }
      next unless $line =~ /^([A-Za-z0-9_-]+):/;
      my $key = $1;
      die "Invalid Phase 65.4 integrity manifest top-level field: $key\n" unless $allowed{$key};
    }
  ' "${absolute_manifest_path}"
}

validate_non_claims_block() {
  perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my %allowed = map { $_ => 1 } qw(
      beta_readiness
      rc_readiness
      ga_readiness
      production_signing_infrastructure
      external_distribution_approval
      entitlement_enforcement
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
        die "Invalid Phase 65.4 integrity manifest value: non_claims\n";
      }
      if ($line =~ /^[^[:space:]]/ && $line !~ /^non_claims:/) {
        $in_non_claims = 0;
      }
      next unless $in_non_claims;
      next if $line =~ /^\s*$/;
      if ($line =~ /^  ([A-Za-z0-9_]+):\s*(.*?)\s*$/) {
        my ($key, $value) = ($1, $2);
        $value =~ s/^\s+|\s+$//g;
        die "Invalid Phase 65.4 integrity manifest value: $key\n" unless $allowed{$key};
        die "Invalid Phase 65.4 integrity manifest value: $key\n" unless $value eq "false";
        $seen{$key}++;
        next;
      }
      die "Invalid Phase 65.4 integrity manifest value: non_claims\n";
    }

    die "Missing Phase 65.4 integrity manifest value: non_claims\n" if $block_count == 0;
    die "Invalid Phase 65.4 integrity manifest value: non_claims\n" if $block_count != 1;
    for my $key (sort keys %allowed) {
      die "Missing Phase 65.4 integrity manifest value: $key\n" unless $seen{$key};
      die "Invalid Phase 65.4 integrity manifest value: $key\n" if $seen{$key} != 1;
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
    echo "Invalid Phase 65.4 integrity manifest ${description}: ${reference}" >&2
    exit 1
  fi
  macos_home_segment="/""Users/"
  linux_home_segment="/""home/"
  root_home_segment="/""root"
  if [[ "${reference}" =~ ^(C:|c:|[A-Za-z]:\\) || "${reference}" == *"${macos_home_segment}"* || "${reference}" == *"${linux_home_segment}"* || "${reference}" == "${root_home_segment}" || "${reference}" == "${root_home_segment}/"* ]]; then
    echo "Invalid Phase 65.4 integrity manifest ${description}: ${reference}" >&2
    exit 1
  fi
  if [[ "${lower_reference}" =~ (^|/)customer-private(/|$) || "${lower_reference}" =~ (^|/)customer_private(/|$) ]]; then
    echo "Invalid Phase 65.4 integrity manifest ${description}: ${reference}" >&2
    exit 1
  fi
}

validate_artifacts() {
  REPO_ROOT="${repo_root}" perl -Mstrict -Mwarnings -0 -e '
    my $text = <>;
    my $repo_root = $ENV{"REPO_ROOT"} // "";
    my @artifact_lines;
    my $artifact_key_count = 0;
    my $in_artifacts = 0;
    for my $line (split /\n/, $text) {
      if ($line =~ /^artifacts:\s*$/) {
        $artifact_key_count++;
        $in_artifacts = 1;
        next;
      }
      if ($in_artifacts && $line =~ /^[A-Za-z0-9_-]+:/) {
        $in_artifacts = 0;
      }
      push @artifact_lines, $line if $in_artifacts;
    }
    die "Missing Phase 65.4 integrity manifest artifacts\n" if $artifact_key_count == 0;
    die "Invalid Phase 65.4 integrity manifest artifacts\n" if $artifact_key_count != 1;

    my $artifact_text = "\n" . join("\n", @artifact_lines);
    for my $line (@artifact_lines) {
      die "Invalid Phase 65.4 integrity manifest artifacts\n" if $line =~ /^  -\s/ && $line !~ /^  - artifact_name:\s*/;
    }
    my @blocks = split /\n  - artifact_name:\s*/, $artifact_text;
    shift @blocks;
    my %expected = (
      "offline-install-bundle" => "Install artifact set",
      "release-channel-upgrade-manifest" => "Upgrade and rollback guidance artifact set",
      "release-notes" => "Release notes artifact set",
      "verification-output" => "Verification output artifact set",
    );
    my %expected_path = (
      "offline-install-bundle" => "<release-bundle-dir>/offline-install-bundle.tar",
      "release-channel-upgrade-manifest" => "docs/deployment/release/phase-65-3-upgrade-manifest.yaml",
      "release-notes" => "docs/release/phase-65-beta-release-notes.md",
      "verification-output" => "<evidence-dir>/phase-65-verification-output.txt",
    );
    my %seen;

    my @required = qw(
      artifact_class
      inventory_reference
      artifact_path
      sbom_reference
      sbom_format
      sbom_scope
      checksum_algorithm
      checksum_reference
      checksum_value
      signature_reference
      signing_posture
      signing_identity
    );
    my %allowed_artifact_field = map { $_ => 1 } @required;

    sub normalize_scalar {
      my ($value) = @_;
      $value =~ s/^\s+|\s+$//g;
      if ($value =~ /^"(.*)"$/s || $value =~ /^'\''(.*)'\''$/s) {
        $value = $1;
      }
      return $value;
    }

    sub artifact_fields {
      my ($block, $artifact_name) = @_;
      my %fields;
      for my $line (split /\n/, $block) {
        my $field_line = $line;
        next unless $field_line =~ s/^    //;
        if ($field_line =~ /^\?\s*([^[:space:]].*?)\s*$/ || $field_line =~ /^:\s*([^[:space:]].*?)\s*$/) {
          die "Invalid Phase 65.4 integrity manifest artifact field for $artifact_name: $1\n";
        }
        my $first = substr($field_line, 0, 1);
        if ($field_line =~ /^(<<)\s*:/) {
          die "Invalid Phase 65.4 integrity manifest artifact field for $artifact_name: $1\n";
        }
        if ($first eq "\"" || $first eq chr(39)) {
          my $quote = $first;
          if ($field_line =~ /^\Q$quote\E([^:]+)\Q$quote\E\s*:/) {
            die "Invalid Phase 65.4 integrity manifest artifact field for $artifact_name: $1\n";
          }
        }
        next unless $line =~ /^    ([A-Za-z0-9_-]+):\s*(.*?)\s*$/;
        my ($key, $value) = ($1, normalize_scalar($2));
        die "Invalid Phase 65.4 integrity manifest artifact field for $artifact_name: $key\n" unless $allowed_artifact_field{$key};
        die "Invalid Phase 65.4 integrity manifest duplicate artifact field for $artifact_name: $key\n" if exists $fields{$key};
        $fields{$key} = $value;
      }
      return %fields;
    }

    sub top_level_field {
      my ($name) = @_;
      return normalize_scalar($1) if $text =~ /^\Q$name\E:\s*(.*?)\s*$/m;
      return "";
    }

    sub require_path_like_artifact_reference {
      my ($fields, $name, $field_name, $description, $kind_pattern) = @_;
      my $value = $fields->{$field_name} // "";
      die "Missing Phase 65.4 $description evidence for $name\n" unless $value =~ /\Q$name\E/;
      die "Invalid Phase 65.4 integrity manifest $field_name for $name\n" unless $value =~ m{/};
      die "Invalid Phase 65.4 integrity manifest $field_name for $name\n" unless $value =~ m{(^|/)[^/]*\Q$name\E[^/]*\.[^/]+$};
      die "Invalid Phase 65.4 integrity manifest $field_name for $name\n" unless $value =~ $kind_pattern;
    }

    sub require_artifact_path_at_revision {
      my ($name, $repository_revision, $artifact_path) = @_;
      return if $artifact_path =~ /^</;
      my $revision_path = $repository_revision . "^{commit}:" . $artifact_path;
      my $status = system("git", "-C", $repo_root, "cat-file", "-e", $revision_path);
      die "Invalid Phase 65.4 integrity manifest artifact_path must exist at repository_revision for $name\n" unless $status == 0;
    }

    my $repository_revision = top_level_field("repository_revision");

    die "Missing Phase 65.4 integrity manifest artifacts\n" unless @blocks;
    for my $block (@blocks) {
      my ($name) = $block =~ /^([^\n]+)\n/;
      $name = normalize_scalar($name) if defined $name;
      die "Missing Phase 65.4 integrity manifest artifact_name\n" unless defined $name && length $name;
      die "Invalid Phase 65.4 integrity manifest artifact name: $name\n" unless exists $expected{$name};
      die "Invalid Phase 65.4 integrity manifest duplicate artifact: $name\n" if $seen{$name}++;
      my %fields = artifact_fields($block, $name);

      for my $required (@required) {
        my $value = $fields{$required} // "";
        die "Missing Phase 65.4 integrity manifest $required for $name\n" unless length $value;
        my $lower = lc $value;
        die "Missing Phase 65.4 integrity manifest $required for $name\n" if $lower =~ /^(todo|tbd|none|n\/a|na|sample|example|placeholder|unknown|missing|absent|latest|head|main|master)$/;
      }

      die "Invalid Phase 65.4 integrity manifest artifact_class for $name\n" unless $fields{"artifact_class"} eq $expected{$name};
      die "Invalid Phase 65.4 integrity manifest inventory_reference for $name\n" unless $fields{"inventory_reference"} eq "docs/phase-65-1-release-bundle-inventory.md";
      die "Invalid Phase 65.4 integrity manifest artifact_path for $name\n" unless $fields{"artifact_path"} eq $expected_path{$name};
      require_artifact_path_at_revision($name, $repository_revision, $fields{"artifact_path"});
      require_path_like_artifact_reference(\%fields, $name, "sbom_reference", "SBOM", qr/\.(sbom\.)?(cdx|spdx)\.json$/);
      require_path_like_artifact_reference(\%fields, $name, "checksum_reference", "checksum", qr/\.sha256$/);
      require_path_like_artifact_reference(\%fields, $name, "signature_reference", "signature", qr/\.(sig|sigstore-placeholder\.txt|signature)$/);
      my $checksum_value = $fields{"checksum_value"};
      die "Invalid Phase 65.4 artifact-name mismatch for $name\n" unless $checksum_value eq "<sha256:$name>" || $checksum_value =~ /^[0-9a-fA-F]{64}$/;
      die "Invalid Phase 65.4 checksum algorithm for $name\n" unless $fields{"checksum_algorithm"} eq "sha256";
      die "Invalid Phase 65.4 signing posture for $name\n" unless $fields{"signing_posture"} eq "beta-attestation-placeholder";
      die "Invalid Phase 65.4 signing identity for $name\n" unless $fields{"signing_identity"} eq "<beta-signing-identity>";
      die "Invalid Phase 65.4 SBOM format for $name\n" unless $fields{"sbom_format"} =~ /^(CycloneDX JSON|SPDX JSON)$/;
      my $sbom_scope = $fields{"sbom_scope"};
      die "Invalid Phase 65.4 SBOM scope for $name\n" unless length $repository_revision && $sbom_scope =~ /\Q$name\E/ && $sbom_scope =~ /\Q$repository_revision\E/;
      die "Invalid Phase 65.4 SBOM scope for $name\n" unless lc($sbom_scope) =~ /beta\/design-partner packaging review only/;
      die "Invalid Phase 65.4 SBOM scope for $name\n" if lc($sbom_scope) =~ /\b(rc|ga|commercial|production|external distribution|entitlement)\b/;
    }

    for my $name (sort keys %expected) {
      die "Missing Phase 65.4 integrity manifest artifact: $name\n" unless $seen{$name};
    }
  ' "${absolute_manifest_path}"

  while IFS= read -r reference; do
    reject_unsafe_reference "${reference}" "artifact reference"
  done < <(
    grep -E '^[[:space:]]+(artifact_path|sbom_reference|checksum_reference|signature_reference):' "${absolute_manifest_path}" |
      sed -E 's/^[[:space:]]+[A-Za-z_]+:[[:space:]]*//'
  )
}

reject_forbidden_claims() {
  local file="$1"
  local description="$2"
  local text

  text="$(visible_text "${file}" | tr '\n' ' ')"
  if grep -Eiq '(AegisOps|Phase 65\.4|integrity evidence|SBOM|checksum|signature|signing).{0,80}(proves?|satisfies?|approves?|completes?|grants?|confirms?|establishes?|unblocks?|passes?|clears?|certifies?|authorizes?|records?|marks?).{0,40}(Beta ready|Beta readiness|RC ready|RC readiness|GA ready|GA readiness|commercial replacement|production signing infrastructure|external distribution approved|entitlement enforcement)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence claim in ${description}: readiness or authority overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(AegisOps|Phase 65\.4|integrity evidence|SBOM|checksum|signature|signing).{0,80}(proves?|satisfies?|approves?|completes?|grants?|confirms?|establishes?|unblocks?|passes?|clears?|certifies?|authorizes?|records?|marks?).{0,60}(Pilot gate acceptance|Beta gate acceptance|RC gate acceptance|GA gate acceptance|Pilot gate approval|Beta gate approval|RC gate approval|GA gate approval|Pilot pass|Beta pass|RC pass|GA pass)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence claim in ${description}: gate acceptance overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(AegisOps|Phase 65\.4|integrity evidence|SBOM|checksum|signature|signing).{0,80}(is|are).{0,15}(Beta ready|RC ready|GA ready|commercially ready|production signed|externally distributable|entitlement approved)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence claim in ${description}: readiness or authority overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(AegisOps|Phase 65\.4|integrity evidence|SBOM|checksum|signature|signing).{0,80}(is|are).{0,30}(Pilot|Beta|RC|GA)[ -]*(gate[ -]*)?(accepted|approved|passed|ready|complete)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence claim in ${description}: gate acceptance overclaim" >&2
    exit 1
  fi
  if grep -Eiq '(verifier|issue-lint).{0,60}(is|are|becomes?|proves?|satisfies?|approves?).{0,40}(readiness truth|release truth|gate truth|RC readiness|GA readiness)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence claim in ${description}: verifier or issue-lint truth shortcut" >&2
    exit 1
  fi
  if grep -Eiq '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|password[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|secret[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|token[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+)' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence material in ${description}: production secret material" >&2
    exit 1
  fi
  if grep -Eiq '((customer-private|customer private).{0,40}(included|includes|packaged|embedded|allowed|contains?|containing|present|stored|retained|carries|holds)|(contains?|includes?|stores?|retains?|carries|holds).{0,40}(customer-private|customer private))' <<<"${text}"; then
    echo "Forbidden Phase 65.4 integrity evidence material in ${description}: customer-private data" >&2
    exit 1
  fi
}

require_file "${absolute_doc_path}" "Phase 65.4 integrity evidence contract"
require_file "${absolute_manifest_path}" "Phase 65.4 integrity evidence manifest"
require_file "${readme_path}" "README for Phase 65.4 integrity evidence link check"
require_file "${repo_root}/docs/phase-65-1-release-bundle-inventory.md" "Phase 65.1 release bundle inventory reference"
require_file "${repo_root}/docs/phase-65-2-offline-install-bundle-contract.md" "Phase 65.2 offline install bundle contract reference"
require_file "${repo_root}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md" "Phase 65.3 release channel and upgrade manifest contract reference"
require_file "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "Phase 51.3 gate contract reference"

require_phrase "${readme_path}" "- [Phase 65.4 integrity evidence contract](docs/phase-65-4-integrity-evidence-contract.md)" "README canonical cross-phase boundary bullet"

required_doc_phrases=()
while IFS= read -r phrase; do
  required_doc_phrases+=("${phrase}")
done <<'EOF_REQUIRED_DOC_PHRASES'
# Phase 65.4 Integrity Evidence Contract
**Status**: Accepted as the Phase 65 SBOM, checksum, and signing evidence contract for beta/design-partner packaging review only.
contract identifier `phase-65-integrity-evidence-contract-v1`
docs/deployment/release/phase-65-4-integrity-evidence.yaml
Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`
artifact identity fields for every required artifact;
SBOM evidence fields for every required artifact;
checksum evidence fields for every required artifact;
signing evidence fields for every required artifact;
| `artifact_name` | Exact bundle artifact name from the Phase 65.1 inventory consumer set. | Missing, placeholder, floating, mismatched, inferred, path-only, or sibling-derived names fail. |
| `sbom_reference` | Repo-relative or bundle-relative SBOM evidence path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling SBOM reuse fails. |
| `checksum_reference` | Repo-relative or bundle-relative checksum manifest path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling checksum reuse fails. |
| `signature_reference` | Repo-relative or bundle-relative signature evidence path for the same artifact name. | Missing, placeholder-only, external-only, artifact-name mismatch, or sibling signature reuse fails. |
| `signing_posture` | `beta-attestation-placeholder` for Phase 65 beta/design-partner packaging review. | Missing, production-signing, unsigned-as-valid, TODO, or inferred postures fail. |
| `offline-install-bundle` | Install artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to the offline install artifact set from Phase 65.2. |
| `release-channel-upgrade-manifest` | Upgrade and rollback guidance artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to `docs/deployment/release/phase-65-3-upgrade-manifest.yaml`. |
| `release-notes` | Release notes artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to `docs/release/phase-65-beta-release-notes.md`. |
| `verification-output` | Verification output artifact set | SBOM, SHA-256 checksum, and beta signing-attestation placeholder evidence bound to retained verifier output references. |
The beta signing posture is `beta-attestation-placeholder`.
Integrity evidence cannot approve release readiness, satisfy Pilot, Beta, RC, or GA gates, prove release truth, prove install truth, prove upgrade truth, approve external distribution, enforce entitlement, approve production signing, close workflows, reconcile actions, or replace Phase 51.3 gate evidence.
The verifier must reject:
missing SBOM evidence;
missing checksum evidence;
missing signature evidence;
artifact-name mismatch;
verifier-as-readiness-truth claims;
issue-lint-as-readiness-truth claims; and
bash scripts/verify-phase-65-4-integrity-evidence-contract.sh
bash scripts/test-verify-phase-65-4-integrity-evidence-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1383 --config <supervisor-config-path>
This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, external distribution approval, hosted update-service readiness, production signing infrastructure, production key custody, production trust-root publication, licensing approval, migration readiness, support readiness, or design-partner evidence completeness.
EOF_REQUIRED_DOC_PHRASES

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 65.4 integrity contract term"
done

require_top_level_equals_once "contract_identifier" "phase-65-integrity-evidence-contract-v1"
require_top_level_equals_once "inventory_identifier" "phase-65-release-bundle-inventory-v1"
require_top_level_equals_once "inventory_reference" "docs/phase-65-1-release-bundle-inventory.md"
require_top_level_equals_once "phase51_gate_boundary_reference" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
require_top_level_equals_once "verifier_output_reference" "bash scripts/verify-phase-65-4-integrity-evidence-contract.sh"
require_top_level_equals_once "accepted_signing_posture" "beta-attestation-placeholder"
require_top_level_present_once "release_bundle_identifier"
require_top_level_present_once "repository_revision"
require_repository_revision_resolves
require_release_identifier_binding
require_top_level_present_once "integrity_evidence_owner"
require_top_level_present_once "approval_record"
require_top_level_present_once "authority_boundary"
require_top_level_sequence_key_once "artifacts"
validate_top_level_manifest_keys
validate_non_claims_block
validate_artifacts

reject_forbidden_claims "${absolute_doc_path}" "${doc_path}"
reject_forbidden_claims "${absolute_manifest_path}" "${manifest_path}"
reject_forbidden_claims "${readme_path}" "README.md"

if bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/tmp/phase-65-4-path-hygiene.out 2>/tmp/phase-65-4-path-hygiene.err; then
  :
else
  cat /tmp/phase-65-4-path-hygiene.out >&2
  cat /tmp/phase-65-4-path-hygiene.err >&2
  echo "Phase 65.4 inherited publishable path hygiene verifier failed" >&2
  exit 1
fi

echo "Phase 65.4 integrity evidence contract preserves SBOM, checksum, signing evidence, artifact identity, and readiness boundaries."
