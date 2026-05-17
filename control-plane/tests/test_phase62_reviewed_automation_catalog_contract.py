from __future__ import annotations

from collections import Counter
import pathlib
import re
import unittest


EXPECTED_CATALOG_COLUMNS = 10
CATALOG_SECTION_HEADING = "## 3. Approved Default Catalog Entries"
CATALOG_SECTION_END_HEADING = "## 4. Catalog Boundedness Rules"
ALLOWED_DEFAULT_FAMILIES = {"Read", "Notify", "Soft Write"}
DISALLOWED_DEFAULT_FAMILIES = {"Controlled Write", "Hard Write"}
FORBIDDEN_OVERCLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "broad SOAR marketplace coverage is implemented",
        re.compile(r"\bbroad\s+soar\s+marketplace\s+coverage\s+is\s+implemented\b", re.I),
    ),
    (
        "arbitrary SOAR connector marketplace import is approved",
        re.compile(
            r"\barbitrary\s+soar\s+connector\s+marketplace\s+import\s+is\s+approved\b",
            re.I,
        ),
    ),
    (
        "template marketplace import is approved",
        re.compile(
            r"\b(?:workflow\s+)?template\s+marketplace\s+imports?\s+"
            r"(?:is|are)\s+(?:approved|available|enabled|implemented|permitted)\b",
            re.I,
        ),
    ),
    (
        "template import from marketplace is approved",
        re.compile(
            r"\btemplate\s+imports?\s+from\s+(?:the\s+)?marketplace\s+"
            r"(?:is|are)\s+(?:approved|available|enabled|implemented|permitted)\b",
            re.I,
        ),
    ),
    (
        "Phase 62.1 claims Beta",
        re.compile(r"\bphase\s+62\.1\b.*\bclaims?\s+beta(?:\s+readiness)?\b", re.I),
    ),
    (
        "Phase 62.1 claims RC",
        re.compile(r"\bphase\s+62\.1\b.*\bclaims?\s+rc(?:\s+readiness)?\b", re.I),
    ),
    (
        "Phase 62.1 claims GA",
        re.compile(r"\bphase\s+62\.1\b.*\bclaims?\s+ga(?:\s+readiness)?\b", re.I),
    ),
    (
        "Phase 62.1 claims commercial readiness",
        re.compile(
            r"\bphase\s+62\.1\b.*\bclaims?\s+commercial"
            r"(?:\s+replacement)?\s+readiness\b",
            re.I,
        ),
    ),
    (
        "Phase 62.1 claims broad SOAR replacement readiness",
        re.compile(
            r"\bphase\s+62\.1\b.*\bclaims?\s+broad\s+soar\s+replacement"
            r"\s+readiness\b",
            re.I,
        ),
    ),
    (
        "Phase 62.1 is or claims standalone replacement readiness",
        re.compile(
            r"\bphase\s+62\.1\b.*\b(?:is|claims?)\s+(?:a\s+)?standalone\s+replacement"
            r"(?:\s+readiness)?\b",
            re.I,
        ),
    ),
    (
        "standalone replacement claim appears",
        re.compile(r"\bstandalone\s+replacement\b", re.I),
    ),
    (
        "standalone replacement claims are approved",
        re.compile(r"\bstandalone\s+replacement\s+claims?\s+are\s+approved\b", re.I),
    ),
    (
        "Phase 62.1 implements Phase 63 evidence expansion",
        re.compile(
            r"\bphase\s+62\.1\s+implements\s+phase\s+63\s+evidence\s+expansion\b",
            re.I,
        ),
    ),
    (
        "Phase 62.1 implements Phase 66 RC proof",
        re.compile(r"\bphase\s+62\.1\s+implements\s+phase\s+66\s+rc\s+proof\b", re.I),
    ),
    (
        "Controlled Write is a default Phase 62.1 catalog entry",
        re.compile(
            r"\bcontrolled\s+write\s+is\s+a\s+default\s+phase\s+62\.1\s+catalog\s+entry\b",
            re.I,
        ),
    ),
    (
        "Hard Write is a default Phase 62.1 catalog entry",
        re.compile(
            r"\bhard\s+write\s+is\s+a\s+default\s+phase\s+62\.1\s+catalog\s+entry\b",
            re.I,
        ),
    ),
)
FORBIDDEN_SETUP_TRUST_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "placeholder credentials are valid",
        re.compile(
            r"\b(?:treats?\s+)?placeholder\s+(?:shuffle\s+)?"
            r"(?:api\s+keys?|secrets?|credentials?|tokens?)\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "sample credentials are valid",
        re.compile(
            r"\b(?:treats?\s+)?sample\s+(?:secrets?|credentials?|tokens?)\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "fake values are valid",
        re.compile(
            r"\b(?:treats?\s+)?fake\s+values?\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "TODO values are valid",
        re.compile(
            r"\b(?:treats?\s+)?todo\s+values?\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "unsigned tokens are valid",
        re.compile(
            r"\b(?:treats?\s+)?unsigned\s+tokens?\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "inline secrets are valid",
        re.compile(
            r"\b(?:treats?\s+)?inline\s+secrets?\s+"
            r"(?:(?:are|is)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:are|is)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
    (
        "raw forwarded headers are trusted",
        re.compile(
            r"\b(?:treats?\s+)?raw\s+forwarded\s+headers?\s+"
            r"(?:(?:are|is)\s+trusted|(?:are|is)\s+treated\s+as\s+trusted"
            r"(?:\s+(?:identity|setup\s+state))?|as\s+trusted\s+identity)\b",
            re.I,
        ),
    ),
    (
        "inferred linkage is valid",
        re.compile(
            r"\b(?:treats?\s+)?inferred\s+(?:tenant|source|delegation)\s+linkage\s+"
            r"(?:(?:is|are)\s+(?:valid|trusted|approved|accepted)|"
            r"(?:is|are)\s+treated\s+as\s+(?:valid|trusted|approved|accepted)"
            r"(?:\s+setup\s+state)?|as\s+(?:valid|trusted|approved|accepted)"
            r"\s+setup\s+state)\b",
            re.I,
        ),
    ),
)
FORBIDDEN_AUTHORITY_PROMOTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "subordinate source is treated as AegisOps truth",
        re.compile(
            r"\b(?:treats?\s+)?(?:shuffle\s+workflow\s+state|workflow\s+state|"
            r"shuffle\s+workflow\s+success|shuffle\s+workflow\s+failure|workflow\s+"
            r"failure|workflow\s+status|shuffle\s+callback\s+payload|callback\s+"
            r"payload|simulator\s+state|ticket\s+state|ticket\s+status|ui\s+cache|"
            r"browser\s+state|ai\s+output|source-native\s+status|verifier\s+"
            r"output|issue-lint\s+output|admin\s+configuration|admin\s+ui\s+state)"
            r"\s+"
            r"(?:(?:is|are|becomes?|become)\s+|as\s+)aegisops\s+"
            r"(?:(?:action|case|reconciliation|execution\s+receipt|policy|"
            r"release|gate|limitation|closeout)\s+)?truth\b",
            re.I,
        ),
    ),
    (
        "direct ad-hoc Shuffle launch is approved",
        re.compile(r"\bdirect\s+ad-?hoc\s+shuffle\s+launch\s+is\s+approved\b", re.I),
    ),
    (
        "Shuffle workflow success is AegisOps reconciliation truth",
        re.compile(
            r"\bshuffle\s+workflow\s+success\s+is\s+aegisops\s+reconciliation\s+truth\b",
            re.I,
        ),
    ),
    (
        "Shuffle callback payload is AegisOps execution receipt truth",
        re.compile(
            r"\bshuffle\s+callback\s+payload\s+is\s+aegisops\s+execution\s+receipt\s+truth\b",
            re.I,
        ),
    ),
    (
        "Shuffle workflow status closes AegisOps cases",
        re.compile(
            r"\bshuffle\s+workflow\s+status\s+closes\s+aegisops\s+cases\b",
            re.I,
        ),
    ),
    (
        "ticket status is AegisOps case truth",
        re.compile(r"\bticket\s+status\s+is\s+aegisops\s+case\s+truth\b", re.I),
    ),
    (
        "ticket close is AegisOps reconciliation truth",
        re.compile(
            r"\bticket\s+close\s+is\s+aegisops\s+reconciliation\s+truth\b",
            re.I,
        ),
    ),
    (
        "UI cache is AegisOps action policy truth",
        re.compile(
            r"\bui\s+cache\s+is\s+aegisops\s+action\s+policy\s+truth\b",
            re.I,
        ),
    ),
    (
        "browser state is AegisOps truth",
        re.compile(
            r"\bbrowser\s+state\s+is\s+aegisops\s+"
            r"(?:(?:action|case|reconciliation|release|gate)\s+)?truth\b",
            re.I,
        ),
    ),
    (
        "admin configuration is AegisOps truth",
        re.compile(
            r"\badmin\s+(?:configuration|ui\s+state)\s+is\s+aegisops\s+"
            r"(?:(?:action|case|reconciliation|release|gate)\s+)?truth\b",
            re.I,
        ),
    ),
    (
        "AI output approves automation",
        re.compile(r"\bai\s+output\s+approves\s+automation\b", re.I),
    ),
    (
        "source-native status reconciles automation",
        re.compile(r"\bsource-native\s+status\s+reconciles\s+automation\b", re.I),
    ),
    (
        "verifier output gates production readiness",
        re.compile(r"\bverifier\s+output\s+gates\s+production\s+readiness\b", re.I),
    ),
    (
        "issue-lint output gates production readiness",
        re.compile(r"\bissue-lint\s+output\s+gates\s+production\s+readiness\b", re.I),
    ),
)
FORBIDDEN_BYPASS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "default entry permits direct workflow launch",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|catalog\s+(?:allows?|enables?)|"
            r"direct\s+(?:ad-?hoc\s+)?shuffle\s+launch\s+is)\s+"
            r"(?:direct\s+(?:ad-?hoc\s+)?shuffle\s+launch|allowed|approved|"
            r"enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "autonomous approval is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|autonomous\s+approval\s+is)\s+"
            r"(?:autonomous\s+approval|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "autonomous remediation is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|autonomous\s+remediation\s+is)\s+"
            r"(?:autonomous\s+remediation|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "protected target mutation is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|protected\s+target\s+mutation\s+is)\s+"
            r"(?:protected\s+target\s+mutation|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "case closure is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|case\s+closure\s+is)\s+"
            r"(?:case\s+closure|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "ticket closure is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|ticket\s+closure\s+is)\s+"
            r"(?:ticket\s+closure|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "detector activation is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|detector\s+activation\s+is)\s+"
            r"(?:detector\s+activation|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "suppression activation is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|suppression\s+activation\s+is)\s+"
            r"(?:suppression\s+activation|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "approval bypass is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|approval\s+bypass\s+is)\s+"
            r"(?:approval\s+bypass|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
    (
        "reconciliation bypass is permitted",
        re.compile(
            r"\b(?:default\s+entr(?:y|ies)\s+permits?|reconciliation\s+bypass\s+is)\s+"
            r"(?:reconciliation\s+bypass|allowed|approved|enabled|permitted)\b",
            re.I,
        ),
    ),
)
FAIL_CLOSED_REJECTION_ITEM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bmissing\b", re.I),
    re.compile(r"\bdoes\s+not\s+include\b", re.I),
    re.compile(r"\buses\s+(?:controlled\s+write|hard\s+write)\b", re.I),
    re.compile(r"\bpermits\s+", re.I),
    re.compile(r"\bpromotes\s+.*\baegisops\s+truth\b", re.I),
    re.compile(r"\bclaims?\s+appear\s+outside\s+explicit\s+rejection\b", re.I),
    re.compile(r"\btreated\s+as\s+valid\s+setup\s+state\b", re.I),
    re.compile(r"\buses\s+workstation-local\s+absolute\s+paths\b", re.I),
)
PLACEHOLDER_CELL_PATTERN = re.compile(
    r"^(?:-|todo|tbd|placeholder|sample|fake)(?:\b|[:\s-])",
    re.I,
)
LIMITATION_BOUNDARY_TERMS = (
    "account disablement",
    "approval decision",
    "automatic approval",
    "autonomous remediation",
    "broad escalation marketplace",
    "broad notification marketplace",
    "case closure",
    "case-close authority",
    "credential change",
    "credential rotation",
    "detector activation",
    "direct source actioning",
    "group membership change",
    "marketplace expansion",
    "protected target mutation",
    "readiness claim",
    "support-authority override",
    "suppression activation",
    "ticket closure",
    "ticket-close authority",
    "workflow state mutation",
)


def _doc_path(relative_path: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / relative_path


def _catalog_rows(catalog_text: str) -> list[list[str]]:
    in_section = False
    seen_header = False
    rows: list[list[str]] = []
    for line in catalog_text.splitlines():
        stripped_line = line.strip()
        if stripped_line == CATALOG_SECTION_HEADING:
            in_section = True
            continue
        if stripped_line == CATALOG_SECTION_END_HEADING:
            break
        if not in_section:
            continue
        if stripped_line.startswith("| Catalog action | Family | Owner |"):
            seen_header = True
            continue
        if not seen_header or not stripped_line.startswith("|"):
            continue
        if re.fullmatch(r"\|[ \-:|]+\|", stripped_line):
            continue
        cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
        rows.append(cells)
    return rows


def _is_forbidden_claims_heading(line: str) -> bool:
    return bool(re.fullmatch(r"##\s+\d+\.\s+Forbidden Claims", line.strip()))


def _is_non_goals_heading(line: str) -> bool:
    return bool(re.fullmatch(r"##\s+\d+\.\s+Non-Goals", line.strip()))


def _is_validation_rules_heading(line: str) -> bool:
    return bool(re.fullmatch(r"##\s+\d+\.\s+Validation Rules", line.strip()))


def _is_section_heading(line: str) -> bool:
    return bool(re.fullmatch(r"##\s+\d+\..*", line.strip()))


def _is_rejection_context(
    line: str,
    in_forbidden_claims: bool,
    in_non_goals: bool,
    in_fail_closed_rule_list: bool,
) -> bool:
    if in_forbidden_claims or in_non_goals:
        return True

    stripped = line.strip()
    normalized = stripped.casefold()
    if in_fail_closed_rule_list and stripped.startswith("- "):
        item_text = stripped[2:].strip()
        return any(pattern.search(item_text) for pattern in FAIL_CLOSED_REJECTION_ITEM_PATTERNS)

    explicit_negation_patterns = (
        r"^(?:[-*]\s*)?no\b",
        r"\bdoes\s+not\s+(?:broaden|claim|dispatch|enable|grant|implement|import|"
        r"launch|let|replace)\b",
        r"\bdo\s+not\b",
        r"\bmust\s+fail\s+closed\b",
        r"\bmust\s+be\s+rejected\b",
        r"\b(?:is|are)\s+rejected\b",
        r"\brejected\s+when\b",
        r"\bremain\s+blocked\b",
        r"\bnon-goals?\b",
        r"\bout\s+of\s+scope\b",
        r"\boutside\s+explicit\s+rejection\s+or\s+non-goal\s+context\b",
        r"\bcannot\s+(?:approve|become|claim|close|execute|gate|reconcile|replace)\b",
    )
    return any(re.search(pattern, normalized) for pattern in explicit_negation_patterns)


def _non_rejection_segments(catalog_text: str) -> list[str]:
    in_forbidden_claims = False
    in_non_goals = False
    in_validation_rules = False
    in_fail_closed_rule_list = False
    segments: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            segments.append(" ".join(current_lines))
            current_lines.clear()

    for line in catalog_text.splitlines():
        if _is_forbidden_claims_heading(line):
            flush()
            in_forbidden_claims = True
            in_non_goals = False
            in_validation_rules = False
            in_fail_closed_rule_list = False
            continue
        if _is_non_goals_heading(line):
            flush()
            in_forbidden_claims = False
            in_non_goals = True
            in_validation_rules = False
            in_fail_closed_rule_list = False
            continue
        if _is_validation_rules_heading(line):
            flush()
            in_forbidden_claims = False
            in_non_goals = False
            in_validation_rules = True
            in_fail_closed_rule_list = False
            continue
        if (
            in_forbidden_claims or in_non_goals or in_validation_rules
        ) and _is_section_heading(line):
            flush()
            in_forbidden_claims = False
            in_non_goals = False
            in_validation_rules = False
            in_fail_closed_rule_list = False

        if in_validation_rules and "must fail closed when" in line.casefold():
            flush()
            in_fail_closed_rule_list = True
            continue

        if _is_rejection_context(
            line,
            in_forbidden_claims,
            in_non_goals,
            in_fail_closed_rule_list,
        ):
            flush()
            continue

        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append(" ")
            continue
        current_lines.append(re.sub(r"^[-*]\s+", "", stripped))

    flush()
    return segments


def _is_placeholder_cell(cell: str) -> bool:
    normalized = cell.strip().strip("`").strip()
    return not normalized or bool(PLACEHOLDER_CELL_PATTERN.search(normalized))


def _catalog_validation_errors(catalog_text: str) -> list[str]:
    rows = _catalog_rows(catalog_text)
    errors: list[str] = []
    required_families = {"Read", "Notify", "Soft Write"}
    seen_families: set[str] = set()
    seen_actions: set[str] = set()
    required_columns = (
        "action",
        "family",
        "owner",
        "substrate mapping need",
        "approval posture",
        "receipt shape",
        "reconciliation expectation",
        "allowed roles",
        "idempotency posture",
        "explicit limitations",
    )

    if not rows:
        errors.append("missing catalog rows")

    for row in rows:
        action = row[0].strip("`") if row else "<missing action>"
        if len(row) != EXPECTED_CATALOG_COLUMNS:
            errors.append(
                f"{action} malformed catalog row has {len(row)} columns; "
                f"expected {EXPECTED_CATALOG_COLUMNS}"
            )
            continue

        if action in seen_actions:
            errors.append(f"{action} duplicate catalog action")
        seen_actions.add(action)

        family = row[1]
        seen_families.add(family)
        for index, column_name in enumerate(required_columns):
            if _is_placeholder_cell(row[index]):
                errors.append(f"{action} missing {column_name}")
        if family in DISALLOWED_DEFAULT_FAMILIES:
            errors.append(f"{action} uses disallowed default family {family}")
        elif family not in ALLOWED_DEFAULT_FAMILIES:
            errors.append(f"{action} uses unknown default family {family}")
        if "owner" in row[2].lower() and "missing" in row[2].lower():
            errors.append(f"{action} missing owner")
        if "direct ad-hoc Shuffle launch" not in row[3]:
            errors.append(f"{action} missing direct Shuffle launch rejection")
        if "AegisOps" not in row[4] or "action request" not in row[4]:
            errors.append(f"{action} missing action request approval posture")
        if "AegisOps execution receipt" not in row[5]:
            errors.append(f"{action} missing AegisOps receipt expectation")
        if "cannot" not in row[6].lower():
            errors.append(f"{action} missing reconciliation limitation")
        if "`analyst`" not in row[7] or "`approver`" not in row[7]:
            errors.append(f"{action} missing role boundary")
        if "Idempotency key" not in row[8]:
            errors.append(f"{action} missing idempotency posture")
        limitation = row[9]
        normalized_limitation = limitation.casefold()
        if not re.search(r"\bno\b", normalized_limitation):
            errors.append(f"{action} missing explicit negative limitation")
        if not any(term in normalized_limitation for term in LIMITATION_BOUNDARY_TERMS):
            errors.append(f"{action} missing limitation boundary semantics")

    for family in required_families - seen_families:
        errors.append(f"missing required family {family}")

    for segment in _non_rejection_segments(catalog_text):
        for claim, pattern in FORBIDDEN_OVERCLAIM_PATTERNS:
            if pattern.search(segment):
                errors.append(f"forbidden overclaim outside rejection context: {claim}")
        for claim, pattern in FORBIDDEN_SETUP_TRUST_PATTERNS:
            if pattern.search(segment):
                errors.append(f"forbidden setup trust outside rejection context: {claim}")
        for claim, pattern in FORBIDDEN_AUTHORITY_PROMOTION_PATTERNS:
            if pattern.search(segment):
                errors.append(
                    f"forbidden authority promotion outside rejection context: {claim}"
                )
        for claim, pattern in FORBIDDEN_BYPASS_PATTERNS:
            if pattern.search(segment):
                errors.append(
                    f"forbidden action boundary bypass outside rejection context: {claim}"
                )
    return errors


class Phase62ReviewedAutomationCatalogContractTests(unittest.TestCase):
    catalog_doc = _doc_path("docs/phase-62-reviewed-automation-catalog-contract.md")
    validation_doc = _doc_path(
        "docs/phase-62-1-reviewed-automation-catalog-validation.md"
    )
    phase54_closeout = _doc_path("docs/phase-54-closeout-evaluation.md")
    phase56_closeout = _doc_path("docs/phase-56-closeout-evaluation.md")
    phase57_closeout = _doc_path("docs/phase-57-closeout-evaluation.md")
    phase61_closeout = _doc_path("docs/phase-61-closeout-evaluation.md")
    policy_doc = _doc_path("docs/phase-51-6-authority-boundary-negative-test-policy.md")

    def test_required_artifacts_exist(self) -> None:
        for path in (
            self.catalog_doc,
            self.validation_doc,
            self.phase54_closeout,
            self.phase56_closeout,
            self.phase57_closeout,
            self.phase61_closeout,
            self.policy_doc,
        ):
            self.assertTrue(path.exists(), f"expected {path} to exist")

    def test_catalog_covers_default_read_notify_soft_write_entries(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        rows = _catalog_rows(catalog_text)
        actions = [row[0].strip("`") for row in rows]
        action_counts = Counter(actions)
        duplicate_actions = sorted(
            action for action, count in action_counts.items() if count > 1
        )

        self.assertEqual([], duplicate_actions)
        self.assertEqual(
            {
                "enrichment_only_lookup",
                "operator_notification",
                "manual_escalation_request",
                "create_tracking_ticket",
            },
            set(actions),
        )
        self.assertEqual(4, len(rows))
        by_action = {row[0].strip("`"): row for row in rows}
        self.assertEqual("Read", by_action["enrichment_only_lookup"][1])
        self.assertEqual("Notify", by_action["operator_notification"][1])
        self.assertEqual("Notify", by_action["manual_escalation_request"][1])
        self.assertEqual("Soft Write", by_action["create_tracking_ticket"][1])

    def test_catalog_parser_uses_approved_section_and_all_section_rows(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        fake_table = "\n".join(
            (
                "| Catalog action | Family | Owner | Substrate mapping need | Required approval posture | Expected receipt shape | Reconciliation expectation | Allowed roles | Idempotency posture | Explicit limitations |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| `fake_pre_section_action` | Hard Write | Fake owner | Fake mapping | Fake approval | Fake receipt | Fake reconciliation | Fake role | Fake idempotency | Fake limitation |",
                "",
            )
        )
        prefixed_text = catalog_text.replace(CATALOG_SECTION_HEADING, fake_table + CATALOG_SECTION_HEADING)
        operator_notification_row = next(
            line
            for line in catalog_text.splitlines()
            if line.startswith("| `operator_notification` |")
        )
        extra_section_row = catalog_text.replace(
            CATALOG_SECTION_END_HEADING,
            f"{operator_notification_row}\n\n{CATALOG_SECTION_END_HEADING}",
        )
        indented_section_row = catalog_text.replace(
            operator_notification_row,
            f"    {operator_notification_row}",
        )

        self.assertEqual(4, len(_catalog_rows(prefixed_text)))
        self.assertIn(
            "operator_notification",
            [row[0].strip("`") for row in _catalog_rows(indented_section_row)],
        )
        self.assertIn(
            "operator_notification duplicate catalog action",
            _catalog_validation_errors(extra_section_row),
        )

    def test_catalog_rows_have_required_contract_fields(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        self.assertEqual([], _catalog_validation_errors(catalog_text))

    def test_catalog_references_reviewed_shuffle_without_direct_launch(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        required_terms = (
            "reviewed Phase 54 Shuffle profile",
            "reviewed Phase 54 Shuffle `enrichment_only_lookup` template contract",
            "reviewed Phase 54 Shuffle `operator_notification` template contract",
            "reviewed Phase 54 Shuffle `manual_escalation_request` template contract",
            "reviewed Phase 54 Shuffle `create_tracking_ticket` template import contract",
            "No direct ad-hoc Shuffle launch.",
        )
        for term in required_terms:
            self.assertIn(term, catalog_text)

    def test_rejects_controlled_and_hard_write_default_entries(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        controlled_text = catalog_text.replace(
            "| `operator_notification` | Notify |",
            "| `operator_notification` | Controlled Write |",
        )
        hard_text = catalog_text.replace(
            "| `create_tracking_ticket` | Soft Write |",
            "| `create_tracking_ticket` | Hard Write |",
        )

        self.assertIn(
            "operator_notification uses disallowed default family Controlled Write",
            _catalog_validation_errors(controlled_text),
        )
        self.assertIn(
            "create_tracking_ticket uses disallowed default family Hard Write",
            _catalog_validation_errors(hard_text),
        )

    def test_rejects_unknown_default_catalog_family(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        unknown_family_text = catalog_text.replace(
            "| `operator_notification` | Notify |",
            "| `operator_notification` | Autonomous Write |",
        )

        self.assertIn(
            "operator_notification uses unknown default family Autonomous Write",
            _catalog_validation_errors(unknown_family_text),
        )

    def test_rejects_malformed_and_duplicate_catalog_rows(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        malformed_text = catalog_text.replace(
            "| `operator_notification` | Notify | AegisOps maintainers and IT Operations, Information Systems Department |",
            "| `operator_notification` | Notify | AegisOps maintainers\n",
        )
        duplicate_text = catalog_text.replace(
            "| `manual_escalation_request` | Notify |",
            "| `operator_notification` | Notify |",
        )

        self.assertIn(
            "operator_notification malformed catalog row has 3 columns; expected 10",
            _catalog_validation_errors(malformed_text),
        )
        self.assertIn(
            "operator_notification duplicate catalog action",
            _catalog_validation_errors(duplicate_text),
        )

    def test_rejects_missing_owner_receipt_and_limitation(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        missing_owner = catalog_text.replace(
            "| `enrichment_only_lookup` | Read | AegisOps maintainers and IT Operations, Information Systems Department |",
            "| `enrichment_only_lookup` | Read | TODO |",
        )
        missing_receipt = catalog_text.replace(
            "AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, `started_at`, `finished_at`, `status`, and subordinate lookup evidence reference.",
            "TODO",
        )
        missing_limitation = catalog_text.replace(
            "Read-only enrichment context. No protected target mutation, credential change, ticket mutation, case closure, detector activation, suppression activation, direct source actioning, or marketplace expansion.",
            "TODO",
        )

        self.assertIn(
            "enrichment_only_lookup missing owner",
            _catalog_validation_errors(missing_owner),
        )
        self.assertIn(
            "enrichment_only_lookup missing receipt shape",
            _catalog_validation_errors(missing_receipt),
        )
        self.assertIn(
            "enrichment_only_lookup missing explicit limitations",
            _catalog_validation_errors(missing_limitation),
        )

    def test_rejects_limitation_without_boundary_semantics(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        weak_limitation = catalog_text.replace(
            "Read-only enrichment context. No protected target mutation, credential change, ticket mutation, case closure, detector activation, suppression activation, direct source actioning, or marketplace expansion.",
            "No delay.",
        )

        self.assertIn(
            "enrichment_only_lookup missing limitation boundary semantics",
            _catalog_validation_errors(weak_limitation),
        )

    def test_rejects_placeholder_required_columns_case_insensitively(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        missing_owner = catalog_text.replace(
            "| `enrichment_only_lookup` | Read | AegisOps maintainers and IT Operations, Information Systems Department |",
            "| `enrichment_only_lookup` | Read | todo owner to wire later |",
        )
        missing_receipt = catalog_text.replace(
            "AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, `started_at`, `finished_at`, `status`, and subordinate lookup evidence reference.",
            "ToDo: add receipt shape after implementation",
        )
        missing_limitation = catalog_text.replace(
            "Read-only enrichment context. No protected target mutation, credential change, ticket mutation, case closure, detector activation, suppression activation, direct source actioning, or marketplace expansion.",
            "tbd - add explicit limitation text",
        )

        self.assertIn(
            "enrichment_only_lookup missing owner",
            _catalog_validation_errors(missing_owner),
        )
        self.assertIn(
            "enrichment_only_lookup missing receipt shape",
            _catalog_validation_errors(missing_receipt),
        )
        self.assertIn(
            "enrichment_only_lookup missing explicit limitations",
            _catalog_validation_errors(missing_limitation),
        )

    def test_rejects_marketplace_and_readiness_overclaim_outside_forbidden_context(
        self,
    ) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "Phase 62.1 records the default reviewed automation catalog",
            "Phase 62.1 records that broad SOAR marketplace coverage is implemented and the default reviewed automation catalog",
        )

        self.assertIn(
            "forbidden overclaim outside rejection context: broad SOAR marketplace coverage is implemented",
            _catalog_validation_errors(overclaim_text),
        )

    def test_rejects_template_marketplace_import_overclaim(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "Phase 62.1 records the default reviewed automation catalog",
            "Phase 62.1 records that template marketplace import is approved and the default reviewed automation catalog",
        )
        marketplace_source_text = catalog_text.replace(
            "Phase 62.1 records the default reviewed automation catalog",
            "Phase 62.1 records that template imports from the marketplace are enabled and the default reviewed automation catalog",
        )

        self.assertIn(
            "forbidden overclaim outside rejection context: template marketplace import is approved",
            _catalog_validation_errors(overclaim_text),
        )
        self.assertIn(
            "forbidden overclaim outside rejection context: template import from marketplace is approved",
            _catalog_validation_errors(marketplace_source_text),
        )

    def test_scans_non_rejection_validation_rules_lines_for_overclaims(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "The Phase 62.1 reviewed automation catalog verifier must fail closed when:",
            "The verifier reports Phase 62.1 claims GA readiness.\n\n"
            "The Phase 62.1 reviewed automation catalog verifier must fail closed when:",
        )
        bullet_overclaim_text = catalog_text.replace(
            "- the catalog contract or validation record is missing;",
            "- Phase 62.1 claims GA readiness.\n"
            "- the catalog contract or validation record is missing;",
        )

        self.assertIn(
            "forbidden overclaim outside rejection context: Phase 62.1 claims GA",
            _catalog_validation_errors(overclaim_text),
        )
        self.assertIn(
            "forbidden overclaim outside rejection context: Phase 62.1 claims GA",
            _catalog_validation_errors(bullet_overclaim_text),
        )

    def test_rejects_overclaims_with_not_marker_and_line_wrapping(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        not_marker_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 claims RC, not just Beta\n## 8. Non-Goals",
        )
        does_not_marker_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 does not just claim RC readiness; it claims GA readiness\n"
            "## 8. Non-Goals",
        )
        wrapped_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 claims\nRC readiness\n## 8. Non-Goals",
        )
        blank_wrapped_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 claims\n\nRC readiness\n## 8. Non-Goals",
        )
        bullet_blank_wrapped_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 claims\n\n- RC readiness\n## 8. Non-Goals",
        )
        long_wrapped_text = catalog_text.replace(
            "## 8. Non-Goals",
            "Phase 62.1 "
            + "records reviewed catalog scope without expanding authority " * 5
            + "claims RC readiness\n## 8. Non-Goals",
        )
        cannot_marker_text = catalog_text.replace(
            "## 8. Non-Goals",
            "The catalog cannot hide that Phase 62.1 claims GA readiness.\n"
            "## 8. Non-Goals",
        )

        expected = "forbidden overclaim outside rejection context: Phase 62.1 claims RC"
        self.assertIn(expected, _catalog_validation_errors(not_marker_text))
        self.assertIn(expected, _catalog_validation_errors(does_not_marker_text))
        self.assertIn(expected, _catalog_validation_errors(wrapped_text))
        self.assertIn(expected, _catalog_validation_errors(blank_wrapped_text))
        self.assertIn(expected, _catalog_validation_errors(bullet_blank_wrapped_text))
        self.assertIn(expected, _catalog_validation_errors(long_wrapped_text))
        self.assertIn(
            "forbidden overclaim outside rejection context: Phase 62.1 claims GA",
            _catalog_validation_errors(cannot_marker_text),
        )

    def test_rejects_case_insensitive_readiness_and_later_phase_overclaims(
        self,
    ) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "## 8. Non-Goals",
            "\n".join(
                (
                    "Phase 62.1 CLAIMS rc",
                    "Phase 62.1 claims RC readiness",
                    "Phase 62.1 claims GA readiness",
                    "Phase 62.1 claims commercial replacement readiness",
                    "Phase 62.1 implements Phase 63 evidence expansion",
                    "Phase 62.1 implements Phase 66 RC proof",
                    "## 8. Non-Goals",
                )
            ),
        )
        validation_errors = _catalog_validation_errors(overclaim_text)

        for expected in (
            "forbidden overclaim outside rejection context: Phase 62.1 claims RC",
            "forbidden overclaim outside rejection context: Phase 62.1 claims GA",
            "forbidden overclaim outside rejection context: Phase 62.1 claims commercial readiness",
            "forbidden overclaim outside rejection context: Phase 62.1 implements Phase 63 evidence expansion",
            "forbidden overclaim outside rejection context: Phase 62.1 implements Phase 66 RC proof",
        ):
            self.assertIn(expected, validation_errors)

    def test_rejects_standalone_replacement_claims_outside_rejection_context(
        self,
    ) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "## 8. Non-Goals",
            "\n".join(
                (
                    "Phase 62.1 is a standalone replacement.",
                    "Phase 62.1 claims standalone replacement readiness",
                    "Standalone replacement is implemented for this catalog.",
                    "This catalog includes standalone replacement readiness.",
                    "Standalone replacement claims are approved",
                    "## 8. Non-Goals",
                )
            ),
        )
        validation_errors = _catalog_validation_errors(overclaim_text)

        self.assertIn(
            "forbidden overclaim outside rejection context: Phase 62.1 is or claims standalone replacement readiness",
            validation_errors,
        )
        self.assertIn(
            "forbidden overclaim outside rejection context: standalone replacement claim appears",
            validation_errors,
        )
        self.assertIn(
            "forbidden overclaim outside rejection context: standalone replacement claims are approved",
            validation_errors,
        )

    def test_rejects_setup_trust_claims_outside_rejection_context(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        trust_claim_text = catalog_text.replace(
            "## 8. Non-Goals",
            "\n".join(
                (
                    "Phase 62.1 treats placeholder Shuffle API keys as valid setup state.",
                    "Placeholder Shuffle API keys are valid credentials.",
                    "Placeholder credentials are treated as valid setup state.",
                    "Sample credentials are accepted.",
                    "Sample tokens are treated as trusted setup state.",
                    "Fake values are valid setup state.",
                    "Fake values are treated as approved setup state.",
                    "TODO values are valid setup state.",
                    "TODO values are treated as accepted setup state.",
                    "Unsigned tokens are trusted.",
                    "Unsigned tokens are treated as valid setup state.",
                    "Inline secrets are approved.",
                    "Inline secrets are treated as trusted setup state.",
                    "Raw forwarded headers are trusted callback identity.",
                    "Raw forwarded headers are treated as trusted identity.",
                    "Inferred tenant linkage is valid.",
                    "Inferred source linkage is treated as valid setup state.",
                    "## 8. Non-Goals",
                )
            ),
        )
        validation_errors = _catalog_validation_errors(trust_claim_text)

        for expected in (
            "forbidden setup trust outside rejection context: placeholder credentials are valid",
            "forbidden setup trust outside rejection context: sample credentials are valid",
            "forbidden setup trust outside rejection context: fake values are valid",
            "forbidden setup trust outside rejection context: TODO values are valid",
            "forbidden setup trust outside rejection context: unsigned tokens are valid",
            "forbidden setup trust outside rejection context: inline secrets are valid",
            "forbidden setup trust outside rejection context: raw forwarded headers are trusted",
            "forbidden setup trust outside rejection context: inferred linkage is valid",
        ):
            self.assertIn(expected, validation_errors)

    def test_rejects_authority_promotion_claims_outside_rejection_context(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        authority_claim_text = catalog_text.replace(
            "## 8. Non-Goals",
            "\n".join(
                (
                    "Direct ad-hoc Shuffle launch is approved.",
                    "Shuffle workflow success is AegisOps reconciliation truth.",
                    "Shuffle workflow state is AegisOps reconciliation truth.",
                    "Workflow failure becomes AegisOps gate truth.",
                    "Shuffle callback payload is AegisOps execution receipt truth.",
                    "Simulator state is AegisOps case truth.",
                    "Shuffle workflow status closes AegisOps cases.",
                    "Ticket status is AegisOps case truth.",
                    "Phase 62.1 treats ticket status as AegisOps case truth.",
                    "Ticket close is AegisOps reconciliation truth.",
                    "UI cache is AegisOps action policy truth.",
                    "Browser state is AegisOps case truth.",
                    "Browser state becomes AegisOps release truth.",
                    "Phase 62.1 treats browser state as AegisOps action truth.",
                    "Admin configuration is AegisOps action truth.",
                    "Admin UI state becomes AegisOps gate truth.",
                    "Phase 62.1 treats admin configuration as AegisOps reconciliation truth.",
                    "AI output approves automation.",
                    "Source-native status reconciles automation.",
                    "Verifier output gates production readiness.",
                    "Issue-lint output gates production readiness.",
                    "## 8. Non-Goals",
                )
            ),
        )
        validation_errors = _catalog_validation_errors(authority_claim_text)

        for expected in (
            "forbidden authority promotion outside rejection context: subordinate source is treated as AegisOps truth",
            "forbidden authority promotion outside rejection context: direct ad-hoc Shuffle launch is approved",
            "forbidden authority promotion outside rejection context: Shuffle workflow success is AegisOps reconciliation truth",
            "forbidden authority promotion outside rejection context: Shuffle callback payload is AegisOps execution receipt truth",
            "forbidden authority promotion outside rejection context: Shuffle workflow status closes AegisOps cases",
            "forbidden authority promotion outside rejection context: ticket status is AegisOps case truth",
            "forbidden authority promotion outside rejection context: ticket close is AegisOps reconciliation truth",
            "forbidden authority promotion outside rejection context: UI cache is AegisOps action policy truth",
            "forbidden authority promotion outside rejection context: browser state is AegisOps truth",
            "forbidden authority promotion outside rejection context: admin configuration is AegisOps truth",
            "forbidden authority promotion outside rejection context: AI output approves automation",
            "forbidden authority promotion outside rejection context: source-native status reconciles automation",
            "forbidden authority promotion outside rejection context: verifier output gates production readiness",
            "forbidden authority promotion outside rejection context: issue-lint output gates production readiness",
        ):
            self.assertIn(expected, validation_errors)

    def test_rejects_action_boundary_bypass_claims_outside_rejection_context(
        self,
    ) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        bypass_claim_text = catalog_text.replace(
            "## 8. Non-Goals",
            "\n".join(
                (
                    "Default entry permits direct ad-hoc Shuffle launch.",
                    "Autonomous approval is enabled.",
                    "Autonomous remediation is approved.",
                    "Protected target mutation is permitted.",
                    "Case closure is allowed.",
                    "Ticket closure is allowed.",
                    "Detector activation is enabled.",
                    "Suppression activation is approved.",
                    "Approval bypass is permitted.",
                    "Reconciliation bypass is permitted.",
                    "## 8. Non-Goals",
                )
            ),
        )
        validation_errors = _catalog_validation_errors(bypass_claim_text)

        for expected in (
            "forbidden action boundary bypass outside rejection context: default entry permits direct workflow launch",
            "forbidden action boundary bypass outside rejection context: autonomous approval is permitted",
            "forbidden action boundary bypass outside rejection context: autonomous remediation is permitted",
            "forbidden action boundary bypass outside rejection context: protected target mutation is permitted",
            "forbidden action boundary bypass outside rejection context: case closure is permitted",
            "forbidden action boundary bypass outside rejection context: ticket closure is permitted",
            "forbidden action boundary bypass outside rejection context: detector activation is permitted",
            "forbidden action boundary bypass outside rejection context: suppression activation is permitted",
            "forbidden action boundary bypass outside rejection context: approval bypass is permitted",
            "forbidden action boundary bypass outside rejection context: reconciliation bypass is permitted",
        ):
            self.assertIn(expected, validation_errors)

    def test_validation_file_states_pass_and_handoff_limitations(self) -> None:
        validation_text = self.validation_doc.read_text(encoding="utf-8")

        required_terms = (
            "# Phase 62.1 Reviewed Automation Catalog Contract Validation",
            "- Validation status: PASS",
            "Read: `enrichment_only_lookup`",
            "Notify: `operator_notification`, `manual_escalation_request`",
            "Soft Write: `create_tracking_ticket`",
            "Controlled Write and Hard Write default entries",
            "No deviations.",
            "Controlled Write and Hard Write remain blocked from default enablement",
        )
        for term in required_terms:
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
