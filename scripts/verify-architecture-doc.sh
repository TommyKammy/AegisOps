#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="${repo_root}/docs/architecture.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Architecture Overview"
  "## 3. Component Responsibilities and Boundaries"
  "## 4. Control Plane vs Execution Plane"
  "## 5. Approved Access Model"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  "This document summarizes the approved baseline architecture for AegisOps."
  "This document describes the approved baseline only and does not introduce runtime changes."
  "AegisOps is a governed SecOps control plane above external detection and automation substrates."
  "The initial standard detection substrate is Wazuh."
  "The initial standard routine automation substrate is Shuffle."
  "The AegisOps control plane is the authoritative owner of policy-sensitive records, approval decisions, evidence linkage, action intent, and reconciliation truth across substrate boundaries."
  "The controlled execution surface is the isolated executor path for higher-risk actions that require tighter execution controls than routine automation should own."
  "\`Substrate Detection Record -> Analytic Signal -> Alert or Case -> Action Request -> Approval Decision -> Approved Automation Substrate or Executor -> Reconciliation\`"
  "Direct substrate-to-automation shortcuts must not become the policy-sensitive system-of-record path."
  "Detection substrates may emit substrate detection records and analytic signals, and automation substrates may perform delegated work, but neither may become the authority for alert truth, case truth, approval truth, action intent, evidence custody, or reconciliation truth."
  "OpenSearch, Sigma, and n8n may still appear in the repository structure as optional, transitional, or experimental components, but they are no longer the product core in the approved architecture baseline."
  "Detection, control, automation, and execution remain explicitly separated in the approved baseline."
  "All external UI access must traverse the approved reverse proxy."
  "Direct unaudited exposure of internal service ports is not part of the approved baseline."
  "This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing architecture overview document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing architecture heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing architecture statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Architecture overview document is present and covers the approved baseline roles and boundaries."
