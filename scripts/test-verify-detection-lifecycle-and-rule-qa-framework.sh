#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-detection-lifecycle-and-rule-qa-framework.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/detection-lifecycle-and-rule-qa-framework.md"
  git -C "${target}" add docs/detection-lifecycle-and-rule-qa-framework.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# AegisOps Detection Lifecycle and Rule QA Framework

## 1. Purpose

This document defines the baseline lifecycle states and minimum quality-assurance evidence required before AegisOps detection content can move from proposal to activation, deprecation, and retirement.

It applies to Sigma detection rules, OpenSearch detector artifacts, supporting validation notes, and future detection metadata that govern whether reviewed content is ready for activation decisions.

This framework defines review and readiness expectations only. It does not authorize live detector activation, bypass staging, or approve production rollout without separate implementation work.

## 2. Scope and Non-Goals

The lifecycle must distinguish at least `draft`, `candidate`, `staging`, `active`, `deprecated`, and `retired` detection content states.

## 3. Lifecycle States

| State | Expectation |
| ---- | ---- |
| `draft` | Initial proposal or substantial rewrite that is not yet eligible for activation review. |
| `candidate` | Reviewable detection content with assigned ownership and documented intent, but not yet approved for staging activation. |
| `staging` | Content approved for controlled validation in a staging environment or test index only. |
| `active` | Content approved for production activation with documented evidence and follow-up obligations. |
| `deprecated` | Content that remains deployed or historically referenced temporarily while replacement or removal is coordinated. |
| `retired` | Content removed from active use and preserved only for audit, history, or reference. |

## 4. State Transition Expectations

Detection content must not move to `staging` until source prerequisites, field coverage expectations, replay data, and review ownership are explicitly documented.

Detection content must not move to `active` until replay or staged validation evidence, expected-volume review, and false-positive review are recorded and reviewable.

Staging readiness is sufficient for controlled translation and validation only when source prerequisites and activation-gating field dependencies are explicit and reviewable.

Production activation requires detection-ready source evidence for activation-gating dependencies and must not rely on schema-reviewed coverage alone.

## 5. Minimum QA Evidence Before Activation

Activation readiness requires evidence for source prerequisite checks, canonical field coverage checks, replay or staged tests, expected alert volume review, and false-positive review.

Source prerequisite checks must confirm that the required source family is admitted under the source onboarding contract, that required indices or datasets exist, and that the rule does not depend on undeclared telemetry.

Field coverage checks must identify the match-required fields, triage-required fields, activation-gating fields, confidence-degrading gaps, and whether each missing field blocks staging or active use.

Replay or staged test evidence must show that the detection logic was exercised against representative data before activation decisions are made.

Expected-volume review must document whether the projected finding or alert volume is acceptable for the initial operating model and what assumptions were used.

False-positive review must record known benign triggers, planned tuning or suppression constraints, and whether analyst review load is acceptable.

## 6. Ownership, Review, and Expiry Expectations

Each detection change must declare an owner, a required reviewer, an expiry or next-review date, and the rollback expectation for disabling or reverting the change if post-deploy behavior is unacceptable.

## 7. Post-Deploy Review and Rollback Expectations

Post-deploy review must verify observed behavior after activation, compare actual volume against the staged expectation, and confirm whether tuning, suppression, deprecation, or retirement is required.

Rollback expectations must preserve the ability to disable or revert a detection change without implying autonomous response or staging bypass.

## 8. Baseline Alignment Notes

This framework remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, `docs/sigma-to-opensearch-translation-strategy.md`, and `docs/secops-domain-model.md`.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing detection lifecycle and rule QA framework document:"

missing_state_repo="${workdir}/missing-state"
create_repo "${missing_state_repo}"
write_doc "${missing_state_repo}" '# AegisOps Detection Lifecycle and Rule QA Framework

## 1. Purpose

This document defines the baseline lifecycle states and minimum quality-assurance evidence required before AegisOps detection content can move from proposal to activation, deprecation, and retirement.

It applies to Sigma detection rules, OpenSearch detector artifacts, supporting validation notes, and future detection metadata that govern whether reviewed content is ready for activation decisions.

This framework defines review and readiness expectations only. It does not authorize live detector activation, bypass staging, or approve production rollout without separate implementation work.

## 2. Scope and Non-Goals

## 3. Lifecycle States

| State | Expectation |
| ---- | ---- |
| `draft` | Initial proposal or substantial rewrite that is not yet eligible for activation review. |
| `candidate` | Reviewable detection content with assigned ownership and documented intent, but not yet approved for staging activation. |
| `staging` | Content approved for controlled validation in a staging environment or test index only. |
| `active` | Content approved for production activation with documented evidence and follow-up obligations. |
| `deprecated` | Content that remains deployed or historically referenced temporarily while replacement or removal is coordinated. |
| `retired` | Content removed from active use and preserved only for audit, history, or reference. |

## 4. State Transition Expectations

Detection content must not move to `staging` until source prerequisites, field coverage expectations, replay data, and review ownership are explicitly documented.

Detection content must not move to `active` until replay or staged validation evidence, expected-volume review, and false-positive review are recorded and reviewable.

## 5. Minimum QA Evidence Before Activation

Activation readiness requires evidence for source prerequisite checks, canonical field coverage checks, replay or staged tests, expected alert volume review, and false-positive review.

Source prerequisite checks must confirm that the required source family is admitted under the source onboarding contract, that required indices or datasets exist, and that the rule does not depend on undeclared telemetry.

Field coverage checks must identify the required normalized fields, any optional fields, known gaps, and whether missing fields block staging or active use.

Replay or staged test evidence must show that the detection logic was exercised against representative data before activation decisions are made.

Expected-volume review must document whether the projected finding or alert volume is acceptable for the initial operating model and what assumptions were used.

False-positive review must record known benign triggers, planned tuning or suppression constraints, and whether analyst review load is acceptable.

## 6. Ownership, Review, and Expiry Expectations

Each detection change must declare an owner, a required reviewer, an expiry or next-review date, and the rollback expectation for disabling or reverting the change if post-deploy behavior is unacceptable.

## 7. Post-Deploy Review and Rollback Expectations

Post-deploy review must verify observed behavior after activation, compare actual volume against the staged expectation, and confirm whether tuning, suppression, deprecation, or retirement is required.

Rollback expectations must preserve the ability to disable or revert a detection change without implying autonomous response or staging bypass.

## 8. Baseline Alignment Notes

This framework remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, `docs/sigma-to-opensearch-translation-strategy.md`, and `docs/secops-domain-model.md`.'
commit_fixture "${missing_state_repo}"
assert_fails_with "${missing_state_repo}" 'The lifecycle must distinguish at least `draft`, `candidate`, `staging`, `active`, `deprecated`, and `retired` detection content states.'

echo "verify-detection-lifecycle-and-rule-qa-framework tests passed"
