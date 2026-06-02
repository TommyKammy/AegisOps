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

if [[ -n "${bundle_dir}" ]]; then
  while [[ "${bundle_dir}" != "/" && "${bundle_dir}" == */ ]]; do
    bundle_dir="${bundle_dir%/}"
  done
fi

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

manifest_value() {
  local file="$1"
  local label="$2"

  perl -Mstrict -Mwarnings -0 -e '
    my $label = shift @ARGV;
    my $text = <>;
    $text =~ s/<!--.*?-->//gs;
    for my $line (split /\n/, $text) {
      if ($line =~ /^\s*\Q$label\E\s*:\s*(.*?)\s*$/i) {
        print "$1\n";
        last;
      }
    }
  ' "${label}" "${file}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

is_placeholder_value() {
  local value="$1"
  local normalized_value

  normalized_value="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [[ -z "${normalized_value}" || "${normalized_value}" =~ ^(<[^>]+>|todo|tbd|none|n/a|na|placeholder|sample|example|changeme|change-me|replace-me)$ ]]
}

require_manifest_value() {
  local manifest="$1"
  local label="$2"
  local value

  value="$(manifest_value "${manifest}" "${label}")"
  if is_placeholder_value "${value}"; then
    echo "Missing offline install bundle metadata value: ${label}" >&2
    exit 1
  fi

  printf '%s' "${value}"
}

validate_utc_timestamp() {
  local timestamp="$1"

  python3 - "${timestamp}" <<'PY'
import datetime
import sys

value = sys.argv[1]
for timestamp_format in ("%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%SZ"):
    try:
        parsed = datetime.datetime.strptime(value, timestamp_format)
    except ValueError:
        continue

    if parsed.strftime(timestamp_format) == value:
        sys.exit(0)

sys.exit(1)
PY
}

require_bundle_file_pattern() {
  local bundle_root="$1"
  local relative_path="$2"
  local pattern="$3"
  local description="$4"

  if ! grep -Eiq -- "${pattern}" < <(visible_markdown_text "${bundle_root}/${relative_path}"); then
    echo "Missing offline install bundle artifact content in ${relative_path}: ${description}" >&2
    exit 1
  fi
}

reject_bundle_file_pattern() {
  local bundle_root="$1"
  local relative_path="$2"
  local pattern="$3"
  local description="$4"

  if grep -Eiq -- "${pattern}" < <(visible_markdown_text "${bundle_root}/${relative_path}"); then
    echo "Forbidden offline install bundle artifact content in ${relative_path}: ${description}" >&2
    exit 1
  fi
}

escape_extended_regex() {
  local value="$1"

  printf '%s' "${value}" | sed -E 's/[][(){}.^$*+?|\\]/\\&/g'
}

require_bundle_doc_matches_repo() {
  local bundle_root="$1"
  local relative_path="$2"

  if ! cmp -s "${repo_root}/${relative_path}" "${bundle_root}/${relative_path}"; then
    echo "Invalid offline install bundle inherited document content: ${relative_path}" >&2
    exit 1
  fi
}

require_bundle_doc_phrase() {
  local bundle_root="$1"
  local relative_path="$2"
  local phrase="$3"
  local description="$4"

  require_phrase "${bundle_root}/${relative_path}" "${phrase}" "offline install bundle inherited document content in ${relative_path}: ${description}"
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
  normalized_text="$(
    printf '%s' "${decoded_text}" |
      tr '\n' ' ' |
      tr '[:upper:]' '[:lower:]' |
      sed -E \
        -e 's/[[:space:]]+/ /g' \
        -e 's/([,;][[:space:]]*)?(and|but)[[:space:]]+((hidden hosted dependenc(y|ies)|hidden hosted downloads?|hosted update services?([[:space:]-]+readiness)?|network update services?|silent update|silent auto-upgrade|silent auto upgrade|production installer|production entitlement enforcement|commercial billing|automatic[[:space:]-]+support-bundle[[:space:]-]+submission|support-bundle[[:space:]-]+(automation|submission)|sbom|checksum|signing|licensing|migration|support|design-partner evidence|release notes?)[^,.?!;]*(is|are)[^,.?!;]*(enabled|implemented|included|available|ready|required|assumed|approved|complete|supported|provided|satisfied|proven|delivered|accepted))/. \3/g'
  )"
  claim_scan_text="$(
    printf '%s' "${normalized_text}" |
      sed -E \
        -e 's/[^.?!;]*((does|do|must|can|is|are)[ -]+not|cannot|can not)[^.?!;]*(claim|claims|prove|proves|satisfy|satisfies|ready|readiness|truth|authority|gate|gates|hosted|silent|production)[^.?!;]*[.?!;]/ /g' \
        -e 's/[^.?!;]*(unsupported|excludes|manual)[^.?!;]*(hosted|silent|production|entitlement|billing|rc|ga|readiness)[^.?!;]*[.?!;]/ /g'
  )"

  if ! printf '%s' "${decoded_text}" | perl -Mstrict -Mwarnings -0ne '
    my @candidates = ($_);
    (my $json_unescaped = $_) =~ s{\\/}{/}g;
    push @candidates, $json_unescaped if $json_unescaped ne $_;

    for my $text (@candidates) {
      if ($text =~ /(^|[^A-Za-z0-9_.\/\\-])([A-Za-z]:[\\\/]+Users[\\\/]+[^\\\/\s]+(?:[\\\/][^\s]*)?)/i) {
        exit 1;
      }

      my $mac_home_prefix = "/" . "Users" . "/";
      my $linux_home_prefix = "/" . "home" . "/";
      my $root_home_prefix = "/" . "root";
      my $unix_home_re = qr{(?:\Q$mac_home_prefix\E|\Q$linux_home_prefix\E)[^/\s]+(?:/[^\s]*)?|\Q$root_home_prefix\E/[^\s]*};
      while ($text =~ /$unix_home_re/g) {
        my $start = $-[0];
        next if $start > 0 && substr($text, $start - 1, 1) =~ /[A-Za-z0-9_.\/\\-]/;
        next if substr($text, $start, length($mac_home_prefix)) eq $mac_home_prefix && substr($text, 0, $start) =~ /(?:^|[^A-Za-z0-9_])[A-Za-z]:$/;
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi

  if ! printf '%s' "${decoded_text}" | perl -Mstrict -Mwarnings -0ne '
      my $text = $_;
      exit 1 if $text =~ /(AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})/i;
      exit 1 if $text =~ /\bauthorization\s*:\s*(?:bearer|basic)\s+(?!<[^>]+>)[A-Za-z0-9_+\.\/=-]{12,}/i;
      exit 1 if $text =~ m{\b[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:(?!<[^>]+>@)[^/\s@]{8,}@}i;

      for my $line (split /\n/, $text) {
      while ($line =~ /(^|[^[:alnum:]_-])["'\'']?((?:secret|token|credential)|[A-Za-z0-9_-]*(?:password|secret[_-]?key|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|credential|aws_secret_access_key)[A-Za-z0-9_-]*)["'\'']?[[:space:]]*[:=][[:space:]]*("[^"]*"|'\''[^'\'']*'\''|[^[:space:]]+)/ig) {
        my $value = $3;
        $value =~ s/^["'\'']//;
        $value =~ s/["'\'']$//;
        next if $value =~ /\A(<[^>]+>|todo|tbd|none|n\/a|na|placeholder|sample|example|changeme|change-me|replace-me)\z/i;
        exit 1;
      }
    }
  '; then
    echo "Forbidden ${description}: production secret-looking value detected" >&2
    exit 1
  fi

  if ! printf '%s' "${decoded_text}" | perl -0ne '
    my $text = $_;
    my $offset = 0;
    for my $sentence (split /(?<=[.?!;\n])\s*/, $text) {
      my $claim = lc $sentence;
      my $start = index($text, $sentence, $offset);
      $start = $offset if $start < 0;
      $offset = $start + length($sentence);
      my $context_start = $start > 1200 ? $start - 1200 : 0;
      my $context = lc substr($text, $context_start, $start - $context_start);
      next unless $claim =~ /(?:placeholder|sample|fake|todo)/;
      next unless $claim =~ /(?:secret|credential|password|token|api[ -]?key)/;
      next unless $claim =~ /(?:(?:are|is|count as|counts as|may be|can be|remain|stays|accepted as|allowed as)[^.?!;\n]*(?:valid|trusted|accepted|production|auth|authenticated|credential)|(?:are|is)[^.?!;\n]*treated as[^.?!;\n]*(?:valid|trusted|accepted|production|auth|authenticated|credential))/;
      next if $claim =~ /(must reject|must not|cannot|can not|do not|does not|invalid|must fail|must block|not be)/;
      next if $context =~ /(must reject|must fail closed when|validation must fail closed when|must fail when):?[^#]*$/s;
      exit 1;
    }
  '; then
    echo "Forbidden ${description}: placeholder credentials accepted as valid auth detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(customer-private|customer private|customer-confidential|customer confidential)[[:space:]-]+(data|payload|record|records)[[:space:]-]+((is|are)[[:space:]-]+)?(included|packaged|present|bundled|provided|required|assumed)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: customer-private data claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(production[[:space:]-]+secrets?|production[[:space:]-]+secret[[:space:]-]+material)[[:space:]-]+((is|are)[[:space:]-]+)?(included|packaged|present|bundled|provided|available|required|assumed|approved|supported)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: production secret material claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(customer[[:space:]-]+specific[[:space:]-]+(secret[[:space:]-]+provisioning|secrets?|secret[[:space:]-]+material|credentials?))[^.?!;]*((is|are)[[:space:]-]+)?(supported|included|packaged|present|bundled|provided|available|required|assumed|approved|complete|enabled)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: customer-specific secret provisioning claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(offline install bundle|offline bundle|bundle manifest|bundle files|this bundle)[^.?!;]*(supports|provides|includes|contains|enables|delivers)[^.?!;]*customer[[:space:]-]+specific[[:space:]-]+(secret[[:space:]-]+provisioning|secrets?|secret[[:space:]-]+material|credentials?)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: customer-specific secret provisioning claim detected" >&2
    exit 1
  fi

    if grep -Eiq -- '(hidden hosted dependenc(y|ies)|hidden hosted downloads?|hosted update services?([[:space:]-]+readiness)?|network update services?|silent update|silent auto-upgrade|silent auto upgrade|background entitlement checks?|production installer([[:space:]-]+(behavior|completeness))?|(production[[:space:]-]+)?entitlement enforcement|billing|production billing|commercial billing|release[[:space:]-]+channel([[:space:]-]+(behavior|services?|updates?|readiness))?)[[:space:]-]+((is|are)[[:space:]-]+)?(enabled|implemented|included|available|ready|required|assumed|approved|complete|supported|provided|satisfied|proven|delivered)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: hosted, silent update, production installer, entitlement, or billing claim detected" >&2
      exit 1
    fi

  if grep -Eiq -- '(offline install bundle|offline bundle|bundle manifest|bundle files|this bundle)[^.?!;]*(provides|delivers|establishes|proves|satisfies|includes|contains)[^.?!;]*(production installer|production installer completeness|hosted update services?([[:space:]-]+readiness)?|network update services?|silent auto-upgrade|silent auto upgrade|background entitlement checks?|(production[[:space:]-]+)?entitlement enforcement|production billing|commercial billing|release[[:space:]-]+channel([[:space:]-]+(behavior|services?|updates?|readiness))?)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: hosted, silent update, production installer, entitlement, or billing claim detected" >&2
    exit 1
  fi

    if grep -Eiq -- '(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|install output|smoke output|verifier output|issue-lint output|docs|release notes?|operator-facing summaries|downstream receipts)[^.?!;]*(prove|proves|satisfy|satisfies|pass|passes|claim|claims|approve|approves|accept|accepts|create|creates|establish|establishes|infer|infers|provide|provides|deliver|delivers|include|includes)[^.?!;]*(beta|rc|ga)[[:space:]-]+(pass|proof|readiness|gate|gates|gate acceptance)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: inferred Beta/RC/GA readiness claim detected" >&2
      exit 1
    fi

    if grep -Eiq -- '(beta|rc|ga)[[:space:]-]+(pass|proof|readiness|gate|gates|gate acceptance)[^.?!;]*(is|are|becomes|become)[^.?!;]*(proven|satisfied|passed|approved|accepted|created|established|provided|delivered|included)[^.?!;]*(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|install output|smoke output|verifier output|issue-lint output|docs|release notes?|operator-facing summaries|downstream receipts)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: inferred Beta/RC/GA readiness claim detected" >&2
      exit 1
    fi

    if grep -Eiq -- '(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|install output|smoke output|verifier output|issue-lint output|docs|release notes?|operator-facing summaries|downstream receipts)[^.?!;]*(prove|proves|satisfy|satisfies|pass|passes|claim|claims|approve|approves|accept|accepts|create|creates|establish|establishes|infer|infers|provide|provides|deliver|delivers|include|includes|support|supports|implement|implements)[^.?!;]*((sbom|checksum|signing)[[:space:]-]+(completeness|generation)|(licensing[[:space:]-]+(approval|conclusions?))|(migration[[:space:]-]+(readiness|guide[[:space:]-]+implementation|implementation))|support[[:space:]-]+readiness|(self-service[[:space:]-]+commercial|commercial[[:space:]-]+replacement)[[:space:]-]+readiness|design-partner[[:space:]-]+evidence[[:space:]-]+completeness)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: unsupported completeness, approval, or readiness claim detected" >&2
      exit 1
    fi

    if grep -Eiq -- '((sbom|checksum|signing)[[:space:]-]+(completeness|generation)|(licensing[[:space:]-]+(approval|conclusions?))|(migration[[:space:]-]+(readiness|guide[[:space:]-]+implementation|implementation))|support[[:space:]-]+readiness|(self-service[[:space:]-]+commercial|commercial[[:space:]-]+replacement)[[:space:]-]+readiness|design-partner[[:space:]-]+evidence[[:space:]-]+completeness)[^.?!;]*(is|are|becomes|become)[^.?!;]*(proven|satisfied|passed|approved|accepted|created|established|provided|delivered|included|supported|implemented)[^.?!;]*(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|install output|smoke output|verifier output|issue-lint output|docs|release notes?|operator-facing summaries|downstream receipts)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: unsupported completeness, approval, or readiness claim detected" >&2
      exit 1
    fi

  if grep -Eiq -- '(verifier output|issue-lint output|install output|smoke output|offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|docs|release notes?|operator-facing summaries|downstream receipts)[[:space:]-]+(is|are|acts as|serve as|serves as|becomes|become|establishes|prove|proves|satisfies)[[:space:]-]+([[:alnum:] /-]+[[:space:]-]+)?(readiness|release|gate|workflow|limitation|install|smoke)[[:space:]-]+truth' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: verifier, issue-lint, install, or smoke truth claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(readiness|release|gate|workflow|limitation|install|smoke)[[:space:]-]+truth[^.?!;]*(is|are|becomes|become|comes from|depends on|is satisfied by|are satisfied by|is proven by|are proven by|established by|created by)[^.?!;]*(verifier output|issue-lint output|install output|smoke output|offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|docs|release notes?|operator-facing summaries|downstream receipts)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: verifier, issue-lint, install, or smoke truth claim detected" >&2
    exit 1
  fi

  if grep -Eiq -- '(automatic[[:space:]-]+support-bundle[[:space:]-]+submission|support-bundle[[:space:]-]+(automation|submission))[^.?!;]*(is|are)[^.?!;]*(enabled|implemented|included|available|ready|required|assumed|approved|complete|supported|provided|delivered)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: unsupported support-bundle automation claim detected" >&2
    exit 1
  fi

    if grep -Eiq -- '(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|this contract)[^.?!;]*(is|are|acts as|serve as|serves as|becomes|become|provides|establishes|creates)[^.?!;]*(workflow|support|runtime[[:space:]-]+execution|release[[:space:]-]+gate|beta[[:space:]-]+gate|rc[[:space:]-]+gate|ga[[:space:]-]+gate|entitlement|billing)[[:space:]-]+authority' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: bundle authority claim detected" >&2
      exit 1
    fi

    if grep -Eiq -- '(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|this contract)[^.?!;]*(is|are|acts as|serve as|serves as|becomes|become|provides|establishes|creates)[^.?!;]*(substitute[[:space:]-]+evidence|evidence[[:space:]-]+substitute)[^.?!;]*(phase[[:space:]-]+51[.]3[[:space:]-]+gate[[:space:]-]+contract|gate[[:space:]-]+contract)' <<<"${claim_scan_text}"; then
      echo "Forbidden ${description}: bundle authority claim detected" >&2
      exit 1
    fi

  if grep -Eiq -- '(workflow|support|runtime[[:space:]-]+execution|release[[:space:]-]+gate|beta[[:space:]-]+gate|rc[[:space:]-]+gate|ga[[:space:]-]+gate|entitlement|billing)[[:space:]-]+authority[^.?!;]*(is|are|becomes|become|comes from|depends on|is satisfied by|are satisfied by|is proven by|are proven by|established by|created by)[^.?!;]*(offline install bundle|offline bundle|this bundle|bundle manifest|bundle files|manifest entries|this contract)' <<<"${claim_scan_text}"; then
    echo "Forbidden ${description}: bundle authority claim detected" >&2
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

baseline_contract_terms=(
  "${phase65_inventory_path}|The inventory identifier is \`phase-65-release-bundle-inventory-v1\`.|Phase 65.1 inventory identifier"
  "${phase65_inventory_path}|The inventory preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, and Phase 66 remains RC while Phase 67 remains GA.|Phase 65.1 gate boundary carry-forward"
  "${phase51_gate_path}|# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract|Phase 51.3 gate contract heading"
  "${phase51_gate_path}|Phase 66 is RC and must not be described as GA.|Phase 51.3 RC boundary"
  "${phase51_gate_path}|Phase 67 is GA and must not be materialized until the GA gate evidence exists.|Phase 51.3 GA boundary"
  "${first_user_stack_path}|# Phase 52.9 First-User Stack Overview|first-user stack heading"
  "${first_user_stack_path}|First-user docs are operator guidance only.|first-user operator guidance boundary"
  "${host_preflight_path}|# Phase 52.6 Host Preflight Contract|host preflight heading"
  "${host_preflight_path}|The host preflight contract gives later setup commands one fail-closed checklist for host prerequisites before the executable first-user stack is started.|host preflight purpose"
  "${clean_host_smoke_path}|# Phase 52.8 Clean-Host Smoke Skeleton|clean-host smoke heading"
  "${clean_host_smoke_path}|Each mocked or skipped step must include the command, the missing prerequisite, the later closing phase, and a safe next action.|clean-host false-success boundary"
  "${env_contract_path}|# Phase 52.5 Env, Secrets, and Cert Generation Contract|env secrets certs heading"
  "${env_contract_path}|AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.|env secrets certs authority boundary"
  "${runbook_path}|# AegisOps Runbook|runbook heading"
  "${runbook_path}|This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.|runbook reviewed procedure boundary"
)

for baseline_contract_term in "${baseline_contract_terms[@]}"; do
  IFS='|' read -r baseline_contract_path baseline_contract_phrase baseline_contract_description <<<"${baseline_contract_term}"
  require_phrase "${baseline_contract_path}" "${baseline_contract_phrase}" "inherited baseline contract term in ${baseline_contract_path#"${repo_root}/"}: ${baseline_contract_description}"
done

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
  "| \`docs/deployment/env-secrets-certs-contract.md\` | Platform maintainers | Reviewed placeholder-only runtime env, secret-source, and certificate custody contract cited by the runtime sample. | Reject the bundle because secret-source custody guidance is absent. |"
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
    "docs/deployment/env-secrets-certs-contract.md"
    "docs/runbook.md"
  )

  symlink_path="$(find "${bundle_dir}" -type l -print -quit)"
  if [[ -n "${symlink_path}" ]]; then
    echo "Invalid offline install bundle artifact: symlink is not allowed: ${symlink_path#"${bundle_dir}/"}" >&2
    exit 1
  fi

  for bundle_file in "${required_bundle_files[@]}"; do
    if [[ ! -s "${bundle_dir}/${bundle_file}" ]]; then
      echo "Missing offline install bundle required artifact: ${bundle_file}" >&2
      exit 1
    fi
  done

  bundle_manifest="${bundle_dir}/BUNDLE-MANIFEST.md"
  contract_identifier="$(require_manifest_value "${bundle_manifest}" "contract identifier")"
  inventory_identifier="$(require_manifest_value "${bundle_manifest}" "inventory identifier")"
  release_bundle_identifier="$(require_manifest_value "${bundle_manifest}" "release bundle identifier")"
  repository_revision="$(require_manifest_value "${bundle_manifest}" "repository revision")"
  bundle_owner="$(require_manifest_value "${bundle_manifest}" "bundle owner")"
  per_artifact_owner="$(require_manifest_value "${bundle_manifest}" "per-artifact owner")"
  bundle_creation_timestamp="$(require_manifest_value "${bundle_manifest}" "bundle creation timestamp")"
  environment_assumption="$(require_manifest_value "${bundle_manifest}" "environment assumption")"
  required_artifact_manifest_path="$(require_manifest_value "${bundle_manifest}" "required artifact manifest path")"
  exclusion_review="$(require_manifest_value "${bundle_manifest}" "exclusion review")"
  verifier_output="$(require_manifest_value "${bundle_manifest}" "verifier output")"
  approval_record="$(require_manifest_value "${bundle_manifest}" "approval record")"

  if [[ "${contract_identifier}" != "phase-65-offline-install-bundle-contract-v1" ]]; then
    echo "Invalid offline install bundle contract identifier: ${contract_identifier}" >&2
    exit 1
  fi

  if [[ "${inventory_identifier}" != "phase-65-release-bundle-inventory-v1" ]]; then
    echo "Invalid offline install bundle inventory identifier: ${inventory_identifier}" >&2
    exit 1
  fi

  placeholder_marker_pattern='<[^>]+>'
  if [[ "${release_bundle_identifier}" =~ ${placeholder_marker_pattern} || ! "${release_bundle_identifier}" =~ ^aegisops-beta-[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Invalid offline install bundle release identifier: ${release_bundle_identifier}" >&2
    exit 1
  fi

  if [[ "${repository_revision}" =~ ${placeholder_marker_pattern} || ! "${repository_revision}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Invalid offline install bundle repository revision: ${repository_revision}" >&2
    exit 1
  fi

  if [[ "${release_bundle_identifier}" != "aegisops-beta-${repository_revision}" ]]; then
    echo "Invalid offline install bundle release binding: ${release_bundle_identifier} does not match repository revision ${repository_revision}" >&2
    exit 1
  fi

  if [[ ! "${bundle_creation_timestamp}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z$ ]] || ! validate_utc_timestamp "${bundle_creation_timestamp}"; then
    echo "Invalid offline install bundle creation timestamp: ${bundle_creation_timestamp}" >&2
    exit 1
  fi

  if [[ "${environment_assumption}" != "offline-beta-design-partner" ]]; then
    echo "Invalid offline install bundle environment assumption: ${environment_assumption}" >&2
    exit 1
  fi

  if [[ "${required_artifact_manifest_path}" != "BUNDLE-MANIFEST.md" ]]; then
    echo "Invalid offline install bundle required artifact manifest path: ${required_artifact_manifest_path}" >&2
    exit 1
  fi

  if [[ "${verifier_output}" != *"bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir"* ]]; then
    echo "Invalid offline install bundle verifier output reference: ${verifier_output}" >&2
    exit 1
  fi

  if [[ -z "${bundle_owner}" || -z "${per_artifact_owner}" || -z "${exclusion_review}" || -z "${approval_record}" ]]; then
    echo "Missing offline install bundle metadata value: owner, exclusion review, or approval record" >&2
    exit 1
  fi

  escaped_release_bundle_identifier="$(escape_extended_regex "${release_bundle_identifier}")"
  escaped_repository_revision="$(escape_extended_regex "${repository_revision}")"

  reject_bundle_file_pattern "${bundle_dir}" "install/README.md" '(^|[^[:alnum:]_-])((does|do|is|are)[ -]+not|cannot|can not|no|missing|absent|without|omits?|unavailable)([^[:alnum:]_-]|$)[^.?!;\n]*(offline[[:space:]-]+install|entrypoint|entry[[:space:]-]+command|install[[:space:]-]+command|selected[[:space:]-]+profile|profile|dependency[[:space:]-]+assumptions?|manual[[:space:]-]+prerequisites?|prerequisites?)' "negated install guidance"
  reject_bundle_file_pattern "${bundle_dir}" "install/README.md" '(offline[[:space:]-]+install|entrypoint|entry[[:space:]-]+command|install[[:space:]-]+command|selected[[:space:]-]+profile|profile|dependency[[:space:]-]+assumptions?|manual[[:space:]-]+prerequisites?|prerequisites?)[^.?!;\n]*((is|are)[ -]+not|cannot|can not|missing|absent|omitted|unavailable|not[[:space:]-]+provided|not[[:space:]-]+documented|not[[:space:]-]+selected)' "negated install guidance"
  require_bundle_file_pattern "${bundle_dir}" "install/README.md" 'offline[[:space:]-]+install' "offline install entry guidance"
  require_bundle_file_pattern "${bundle_dir}" "install/README.md" '(entrypoint|entry[[:space:]-]+command|install[[:space:]-]+command)' "install entry command"
  require_bundle_file_pattern "${bundle_dir}" "install/README.md" 'aegisops[[:space:]]+(init|up|doctor)[^`\n]*(--profile[[:space:]]+smb-single-node[^`\n]*--runtime-env[[:space:]]+<runtime-env-file>|--runtime-env[[:space:]]+<runtime-env-file>[^`\n]*--profile[[:space:]]+smb-single-node)' "concrete install command"
  require_bundle_file_pattern "${bundle_dir}" "install/README.md" '(selected[[:space:]-]+profile|profile)' "selected profile"
  require_bundle_file_pattern "${bundle_dir}" "install/README.md" '(dependency[[:space:]-]+assumptions?|manual[[:space:]-]+prerequisites?|prerequisites?)' "dependency assumptions and manual prerequisites"
  require_bundle_file_pattern "${bundle_dir}" "config/runtime.env.sample" 'docs/deployment/env-secrets-certs-contract[.]md' "secret-source contract citation"
  require_bundle_file_pattern "${bundle_dir}" "config/runtime.env.sample" '^[[:space:]]*AEGISOPS_PROFILE[[:space:]]*=' "runtime configuration key"
    require_bundle_file_pattern "${bundle_dir}" "config/runtime.env.sample" '^[[:space:]]*AEGISOPS_RUNTIME_ENV[[:space:]]*=[[:space:]]*<runtime-env-file>([[:space:]]|$)' "placeholder runtime env key"
  require_bundle_file_pattern "${bundle_dir}" "config/runtime.env.sample" '^[[:space:]]*AEGISOPS_SECRET_SOURCE_DOC[[:space:]]*=[[:space:]]*docs/deployment/env-secrets-certs-contract[.]md([[:space:]]|$)' "secret-source contract key"
  require_bundle_file_pattern "${bundle_dir}" "evidence/install-preflight-output.txt" "^[[:space:]]*release bundle identifier:[[:space:]]*${escaped_release_bundle_identifier}([[:space:]]|\$)" "matching release bundle identifier"
  require_bundle_file_pattern "${bundle_dir}" "evidence/install-preflight-output.txt" "^[[:space:]]*repository revision:[[:space:]]*${escaped_repository_revision}([[:space:]]|\$)" "matching repository revision"

  bundled_repo_docs=(
    "docs/phase-65-2-offline-install-bundle-contract.md"
    "docs/phase-65-1-release-bundle-inventory.md"
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
    "docs/deployment/first-user-stack.md"
    "docs/deployment/host-preflight-contract.md"
    "docs/deployment/clean-host-smoke-skeleton.md"
    "docs/deployment/env-secrets-certs-contract.md"
    "docs/runbook.md"
  )

  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-65-2-offline-install-bundle-contract.md" "The contract identifier is \`phase-65-offline-install-bundle-contract-v1\`." "Phase 65.2 contract identifier"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-65-2-offline-install-bundle-contract.md" "This contract does not claim Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, production entitlement enforcement, hosted update service readiness, release-channel readiness, production installer completeness, SBOM completeness, checksum completeness, signing completeness, licensing approval, migration readiness, support readiness, or design-partner evidence completeness." "Phase 65.2 non-claim boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-65-1-release-bundle-inventory.md" "The inventory identifier is \`phase-65-release-bundle-inventory-v1\`." "Phase 65.1 inventory identifier"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-65-1-release-bundle-inventory.md" "The inventory preserves the Phase 51.3 gate boundary: Pilot, Beta, RC, and GA evidence must remain distinct, and Phase 66 remains RC while Phase 67 remains GA." "Phase 65.1 gate boundary carry-forward"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract" "Phase 51.3 gate contract heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "Phase 66 is RC and must not be described as GA." "Phase 51.3 RC boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "Phase 67 is GA and must not be materialized until the GA gate evidence exists." "Phase 51.3 GA boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/first-user-stack.md" "# Phase 52.9 First-User Stack Overview" "first-user stack heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/first-user-stack.md" "First-user docs are operator guidance only." "first-user operator guidance boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/host-preflight-contract.md" "# Phase 52.6 Host Preflight Contract" "host preflight heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/host-preflight-contract.md" "The host preflight contract gives later setup commands one fail-closed checklist for host prerequisites before the executable first-user stack is started." "host preflight purpose"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/clean-host-smoke-skeleton.md" "# Phase 52.8 Clean-Host Smoke Skeleton" "clean-host smoke heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/clean-host-smoke-skeleton.md" "Each mocked or skipped step must include the command, the missing prerequisite, the later closing phase, and a safe next action." "clean-host false-success boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/env-secrets-certs-contract.md" "# Phase 52.5 Env, Secrets, and Cert Generation Contract" "env secrets certs heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/deployment/env-secrets-certs-contract.md" "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth." "env secrets certs authority boundary"
  require_bundle_doc_phrase "${bundle_dir}" "docs/runbook.md" "# AegisOps Runbook" "runbook heading"
  require_bundle_doc_phrase "${bundle_dir}" "docs/runbook.md" "This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path." "runbook reviewed procedure boundary"

  for bundled_repo_doc in "${bundled_repo_docs[@]}"; do
    require_bundle_doc_matches_repo "${bundle_dir}" "${bundled_repo_doc}"
  done

  bundle_scan_files=()
  while IFS= read -r -d '' bundle_scan_file; do
    relative_bundle_scan_file="${bundle_scan_file#"${bundle_dir}/"}"
    skip_exact_repo_doc=false
    for bundled_repo_doc in "${bundled_repo_docs[@]}"; do
      if [[ "${relative_bundle_scan_file}" == "${bundled_repo_doc}" ]]; then
        skip_exact_repo_doc=true
        break
      fi
    done
    if [[ "${skip_exact_repo_doc}" == true ]]; then
      continue
    fi
    bundle_scan_files+=("${bundle_scan_file}")
  done < <(find "${bundle_dir}" -type f -print0)
  scan_forbidden_text "offline install bundle content" "${bundle_scan_files[@]}"
fi

echo "Phase 65.2 offline install bundle contract is present and fail-closed."
