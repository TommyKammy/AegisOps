from __future__ import annotations


_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS = (
    ("shuffle", "result"),
    ("shuffle", "state"),
    ("shuffle", "output"),
    ("workflow", "result"),
    ("workflow", "state"),
    ("workflow", "output"),
    ("ticket", "output"),
    ("ticket", "state"),
    ("ticket", "report"),
    ("ui", "cache"),
    ("ui", "state"),
    ("ui", "output"),
    ("browser", "state"),
    ("browser", "output"),
    ("ai", "output"),
    ("ai", "result"),
    ("verifier", "output"),
    ("verifier", "result"),
    ("issue", "lint", "output"),
    ("issue", "lint", "report"),
    ("operator", "note"),
)
_NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS = tuple(
    dict.fromkeys(
        (
            *_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS,
            *(
                (source_terms[-1], *source_terms[:-1])
                for source_terms in _NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS
                if len(source_terms) > 1
            ),
        )
    )
)
_AUTHORITY_PROOF_VERBS = (
    "confirm",
    "confirms",
    "confirmed",
    "confirming",
    "prove",
    "proves",
    "proved",
    "proven",
    "proving",
    "validate",
    "validates",
    "validated",
    "validating",
)
_AUTHORITY_PROOF_OBJECTS = ("execution", "receipt", "reconciliation")
_AUTHORITY_PROOF_NOUNS = ("proof", "confirmation", "validation")
_APPROVAL_BYPASS_TERMS = ("bypass", "bypasses", "bypassed", "bypassing")
_CLOSURE_AUTHORITY_TERM_GROUPS = (
    ("close", "case"),
    ("closed", "case"),
    ("closes", "case"),
    ("closing", "case"),
    ("case", "close"),
    ("case", "closed"),
    ("case", "closes"),
    ("case", "closing"),
    ("case", "closure"),
    ("closure", "case"),
    ("close", "cases"),
    ("closed", "cases"),
    ("closes", "cases"),
    ("closing", "cases"),
    ("case", "closures"),
    ("cases", "close"),
    ("cases", "closed"),
    ("cases", "closes"),
    ("cases", "closing"),
    ("cases", "closure"),
    ("cases", "closures"),
    ("closure", "cases"),
    ("closures", "case"),
    ("closures", "cases"),
    ("close", "ticket"),
    ("closed", "ticket"),
    ("closes", "ticket"),
    ("closing", "ticket"),
    ("ticket", "close"),
    ("ticket", "closes"),
    ("ticket", "closed"),
    ("ticket", "closing"),
    ("ticket", "closure"),
    ("closure", "ticket"),
    ("close", "tickets"),
    ("closed", "tickets"),
    ("closes", "tickets"),
    ("closing", "tickets"),
    ("ticket", "closures"),
    ("tickets", "close"),
    ("tickets", "closed"),
    ("tickets", "closes"),
    ("tickets", "closing"),
    ("tickets", "closure"),
    ("tickets", "closures"),
    ("closure", "tickets"),
    ("closures", "ticket"),
    ("closures", "tickets"),
)
_AUTHORITY_PROOF_TERM_GROUPS = tuple(
    dict.fromkeys(
        (
            *(
                (verb, proof_object)
                for verb in _AUTHORITY_PROOF_VERBS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_object, verb)
                for verb in _AUTHORITY_PROOF_VERBS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_noun, proof_object)
                for proof_noun in _AUTHORITY_PROOF_NOUNS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_object, proof_noun)
                for proof_noun in _AUTHORITY_PROOF_NOUNS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
        )
    )
)
_EXECUTION_SUCCESS_TERM_GROUPS = (
    ("execution", "succeed"),
    ("execution", "succeeds"),
    ("execution", "succeeding"),
    ("execution", "success"),
    ("execution", "successful"),
    ("execution", "succeeded"),
    ("succeed", "execution"),
    ("succeeds", "execution"),
    ("succeeding", "execution"),
    ("success", "execution"),
    ("successful", "execution"),
    ("succeeded", "execution"),
)
_NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS = (
    ("authoritative",),
    ("authority",),
    ("truth",),
    *_AUTHORITY_PROOF_TERM_GROUPS,
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
)
_AUTHORITY_PROMOTING_TERM_GROUPS = (
    *((term,) for term in _APPROVAL_BYPASS_TERMS),
    *_AUTHORITY_PROOF_TERM_GROUPS,
    ("execution", "authority"),
    ("execution", "authoritative"),
    ("authority", "execution"),
    ("authoritative", "execution"),
    ("execution", "truth"),
    ("receipt", "truth"),
    ("reconciliation", "truth"),  # manual fallback notes cannot become truth records
    ("approval", "truth"),
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
    *_CLOSURE_AUTHORITY_TERM_GROUPS,
    *_EXECUTION_SUCCESS_TERM_GROUPS,
)
_FOLLOW_UP_LAUNCH_READINESS_TERMS = (
    "commercial",
    "beta",
    "rc",
    "ga",
)
_FOLLOW_UP_COMPLETION_OR_READINESS_TERMS = (
    "complete",
    "completes",
    "completed",
    "completing",
    "succeed",
    "succeeds",
    "succeeded",
    "succeeding",
    "success",
    "successful",
    "closes",
    "closure",
    "closed",
    "close",
    "closing",
    "ready",
    "readiness",
    "reconcile",
    "reconciles",
    "reconciled",
    "reconciling",
    "reconciliation",
    *_FOLLOW_UP_LAUNCH_READINESS_TERMS,
)
_NEGATION_TERMS = (
    "not",
    "no",
    "never",
    "cannot",
    "cant",
    "wont",
    "isnt",
    "arent",
    "wasnt",
    "werent",
    "dont",
    "doesnt",
    "didnt",
    "hasnt",
    "havent",
    "hadnt",
    "couldnt",
    "shouldnt",
    "wouldnt",
    "without",
)
_TERM_BOUNDARY = "boundary"
_TERM_COMMA_BOUNDARY = "comma_boundary"
_NEGATION_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    "and",
    "but",
    "however",
    "though",
    "although",
    "yet",
    "whereas",
    "while",
    "instead",
    "then",
    "or",
}
_TERM_GROUP_MAX_INTERVENING_TERMS = 6
_NEGATION_SCAN_WINDOW = 8
_SOURCE_AUTHORITY_ASSERTION_LINK_TERMS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "being",
    "been",
    "become",
    "becomes",
    "became",
    "can",
    "could",
    "show",
    "showed",
    "shows",
    "shown",
    "say",
    "said",
    "says",
    "state",
    "stated",
    "states",
    "will",
    "would",
}
_NEGATION_HARD_BOUNDARY_TERMS = {_TERM_BOUNDARY}
_NEGATION_CONTRAST_BOUNDARY_TERMS = {
    "although",
    "but",
    "however",
    "instead",
    "then",
    "though",
    "whereas",
    "while",
    "yet",
}
_NEGATION_LIST_BOUNDARY_TERMS = {"and", "or"}
_AUTHORITY_LINK_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_BOUNDARY_TERMS,
}
_AUTHORITY_CLAIM_CLAUSE_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_CONTRAST_BOUNDARY_TERMS,
}
_NEGATION_LIST_SUBJECT_TERMS = tuple(
    dict.fromkeys(
        term
        for term_group in (
            *_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS,
            ("approval",),
            ("case",),
            ("execution",),
            ("receipt",),
            ("reconciliation",),
            ("ticket",),
        )
        for term in term_group
    )
)



_SIMULATOR_PRODUCTION_ARTIFACT_TRUTH_TERMS = (
    ("production", "execution", "receipt", "truth"),
    ("production", "execution", "receipt"),
    ("production", "reconciliation", "truth"),
    ("production", "receipt"),
    ("production", "reconciliation", "state"),
    ("execution", "receipt", "truth"),
    ("reconciliation", "truth"),
    ("production", "truth"),
)
_SIMULATOR_AUTHORITY_TRUTH_TERMS = (
    ("authority",),
    ("authoritative",),
    ("authoritatively",),
    ("authoritative", "execution"),
    ("authoritative", "receipt"),
    ("authoritative", "reconciliation"),
    ("authoritative", "truth"),
)
_SIMULATOR_CLOSURE_TRUTH_TERMS = (
    ("closure",),
    ("closed",),
    ("closing",),
    ("case", "truth"),
    ("case", "closure"),
    ("close", "case"),
    ("closes", "case"),
    ("closed", "case"),
    ("closing", "case"),
    ("case", "closed"),
    ("case", "closing"),
    ("ticket", "truth"),
    ("ticket", "closure"),
    ("close", "ticket"),
    ("closes", "ticket"),
    ("closed", "ticket"),
    ("closing", "ticket"),
    ("ticket", "closed"),
    ("ticket", "closing"),
)
_SIMULATOR_WORKFLOW_TRUTH_TERMS = (
    ("production", "workflow", "delegation"),
    ("production", "workflow", "delegate"),
    ("production", "workflow", "delegated"),
    ("delegation", "production", "workflow"),
    ("delegate", "production", "workflow"),
    ("delegate", "workflow", "production"),
    ("delegated", "production", "workflow"),
    ("delegated", "workflow", "production"),
    ("delegating", "production", "workflow"),
    ("delegating", "workflow", "production"),
    ("workflow", "delegation", "production"),
    ("workflow", "delegate", "production"),
    ("workflow", "delegated", "production"),
    ("workflow", "delegating", "production"),
    ("production", "workflow", "launch"),
    ("production", "workflow", "launched"),
    ("production", "workflow", "launching"),
    ("launch", "production", "workflow"),
    ("launch", "workflow", "production"),
    ("launched", "production", "workflow"),
    ("launched", "workflow", "production"),
    ("launching", "production", "workflow"),
    ("launching", "workflow", "production"),
    ("workflow", "launch", "production"),
    ("workflow", "launched", "production"),
    ("workflow", "launching", "production"),
)
_SIMULATOR_AD_HOC_EXECUTION_TRUTH_TERMS = (
    ("direct", "ad", "hoc", "execution"),
    ("ad", "hoc", "execution"),
    ("execution", "ad", "hoc"),
    ("direct", "execution"),
)
_SIMULATOR_READINESS_TRUTH_TERMS = (
    ("ready",),
    ("readied",),
    ("readying",),
    ("readiness",),
)
_SIMULATOR_POST_TERM_CLAIM_DENIAL_TERMS = {
    "asserted",
    "claim",
    "claimed",
    "included",
    "part",
    "used",
}
_SIMULATOR_POST_TERM_CLAIM_DENIAL_FILLER_TERMS = {
    "a",
    "an",
    "of",
    "output",
    "simulator",
    "the",
}
_SIMULATOR_PRODUCTION_CONTEXT_TERMS = {"production"}
_SIMULATOR_WORKFLOW_CONTEXT_TERMS = {"workflow", "workflows"}
_SIMULATOR_WORKFLOW_ACTION_TERMS = {
    "delegate",
    "delegates",
    "delegated",
    "delegating",
    "delegation",
    "launch",
    "launches",
    "launched",
    "launching",
    "start",
    "starts",
    "started",
    "starting",
    "trigger",
    "triggers",
    "triggered",
    "triggering",
    "initiate",
    "initiates",
    "initiated",
    "initiating",
    "invoke",
    "invokes",
    "invoked",
    "invoking",
    "run",
    "runs",
    "ran",
    "running",
}
_SIMULATOR_CLOSURE_CONTEXT_TERMS = {
    "case",
    "cases",
    "ticket",
    "tickets",
}
_SIMULATOR_CLOSURE_ACTION_TERMS = {
    "close",
    "closes",
    "closed",
    "closing",
    "closure",
}
_SIMULATOR_RECEIPT_CONTEXT_TERMS = {
    "receipt",
    "receipts",
}
_SIMULATOR_RECONCILIATION_CONTEXT_TERMS = {
    "reconciliation",
    "reconciliations",
}
_SIMULATOR_STATE_CONTEXT_TERMS = {
    "state",
    "states",
}
_SIMULATOR_ARTIFACT_ASSERTION_TERMS = {
    "create",
    "creates",
    "created",
    "creating",
    "generate",
    "generates",
    "generated",
    "generating",
    "set",
    "sets",
    "setting",
    "write",
    "writes",
    "wrote",
    "writing",
}
_SIMULATOR_PRODUCTION_TRUTH_TERMS = (
    *_SIMULATOR_PRODUCTION_ARTIFACT_TRUTH_TERMS,
    *_SIMULATOR_AUTHORITY_TRUTH_TERMS,
    *_SIMULATOR_CLOSURE_TRUTH_TERMS,
    *_SIMULATOR_WORKFLOW_TRUTH_TERMS,
    *_SIMULATOR_AD_HOC_EXECUTION_TRUTH_TERMS,
    *_SIMULATOR_READINESS_TRUTH_TERMS,
)
_SIMULATOR_EXCLUDABLE_PRODUCTION_TRUTH_TERMS = (
    ("production", "execution", "receipt", "truth"),
    ("production", "execution", "receipt"),
    ("production", "reconciliation", "truth"),
    ("production", "receipt"),
    ("execution", "receipt", "truth"),
    ("reconciliation", "truth"),
    ("production", "truth"),
)
_SIMULATOR_EXCLUSION_CONTEXT_TERMS = (
    "exclude",
    "excludes",
    "excluded",
    "excluding",
    "exclusion",
)
_SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS = (
    ("production", "execution", "receipt"),
    ("reconciliation", "truth"),
)
_SIMULATOR_EXCLUSION_CLAIM_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_CONTRAST_BOUNDARY_TERMS,
    "therefore",
    "thus",
}
_SIMULATOR_CONTEXT_CLAUSE_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    *_NEGATION_CONTRAST_BOUNDARY_TERMS,
}
_SIMULATOR_WORKFLOW_CONTEXT_CLAUSE_BOUNDARY_TERMS = {
    *_SIMULATOR_CONTEXT_CLAUSE_BOUNDARY_TERMS,
    *_NEGATION_LIST_BOUNDARY_TERMS,
}
_SIMULATOR_CONTEXT_SCAN_WINDOW = _NEGATION_SCAN_WINDOW * 2

def promotes_non_authoritative_evidence(value: str) -> bool:
    terms = text_terms(value)
    for source_terms in _NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS:
        source_matches = _term_group_matches(terms, source_terms)
        if not source_matches:
            continue
        if any(
            _sourcepromotes_non_authoritative_evidence(
                terms=terms,
                source_match=source_match,
            )
            for source_match in source_matches
        ):
            return True
    return False


def _sourcepromotes_non_authoritative_evidence(
    *,
    terms: tuple[str, ...],
    source_match: tuple[int, ...],
) -> bool:
    source_index = source_match[0]
    source_end = source_match[-1] + 1
    for authority_terms in _NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS:
        for authority_match in _term_group_matches(terms, authority_terms):
            authority_index = authority_match[0]
            if any(
                _has_recent_negation(terms, match_index, window=3)
                for match_index in authority_match
            ):
                continue
            if _has_source_scoped_negation_before_authority(
                terms=terms,
                source_index=source_index,
                source_end=source_end,
                authority_index=authority_index,
            ):
                continue
            if _authority_claim_matches_source(
                terms=terms,
                source_index=source_index,
                source_end=source_end,
                authority_index=authority_index,
                authority_terms=authority_terms,
            ):
                return True
    return False


def _has_source_scoped_negation_before_authority(
    *,
    terms: tuple[str, ...],
    source_index: int,
    source_end: int,
    authority_index: int,
) -> bool:
    if authority_index <= source_end:
        return False
    for negation_index in range(authority_index - 1, source_end - 1, -1):
        term = terms[negation_index]
        if term in _NEGATION_BOUNDARY_TERMS:
            return False
        if term in _NEGATION_TERMS:
            return not _is_not_only_phrase(terms, negation_index, authority_index)
    return False


def _authority_claim_matches_source(
    *,
    terms: tuple[str, ...],
    source_index: int,
    source_end: int,
    authority_index: int,
    authority_terms: tuple[str, ...],
) -> bool:
    authority_end = authority_index + len(authority_terms)
    if source_index <= authority_index:
        between = terms[source_end:authority_index]
        if any(term in _AUTHORITY_CLAIM_CLAUSE_BOUNDARY_TERMS for term in between):
            return False
        list_boundaries = [
            index for index, term in enumerate(between) if term in {"and", "or"}
        ]
        if list_boundaries and any(
            term in _NEGATION_LIST_SUBJECT_TERMS
            for term in between[list_boundaries[-1] + 1 :]
        ):
            return False
        targets_aegisops_receipt = _authority_claim_targets_aegisops_receipt(
            terms=terms,
            source_end=source_end,
            authority_index=authority_index,
            authority_end=authority_end,
        )
        if targets_aegisops_receipt and not _source_is_directly_asserted_as_authority(
            between
        ):
            return False
        if source_end == authority_index:
            return True
        if list_boundaries:
            return True
        return _source_is_directly_asserted_as_authority(between)

    between = terms[authority_end:source_index]
    if any(
        term in {_TERM_COMMA_BOUNDARY, *_NEGATION_BOUNDARY_TERMS}
        for term in between
    ):
        return False
    if source_index - authority_end <= 3 and not any(
        term in {"aegisops", "bound"} for term in terms[authority_index:source_end]
    ):
        return True
    return any(
        term
        in {
            "from",
            "via",
            "using",
            "through",
            "by",
            "based",
            "comes",
            "come",
            "coming",
            "derived",
        }
        for term in between
    )


def _authority_claim_targets_aegisops_receipt(
    *,
    terms: tuple[str, ...],
    source_end: int,
    authority_index: int,
    authority_end: int,
) -> bool:
    authority_anchor_start = max(source_end, authority_index - 3)
    authority_anchor = terms[
        authority_anchor_start : min(len(terms), authority_end + 4)
    ]
    return any(term in {"aegisops", "bound"} for term in authority_anchor)


def _source_is_directly_asserted_as_authority(
    between_source_and_authority: tuple[str, ...],
) -> bool:
    if any(
        term in _AUTHORITY_LINK_BOUNDARY_TERMS
        for term in between_source_and_authority
    ):
        return False
    return any(
        term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
        for term in between_source_and_authority
    )


def _blocked_reason_matches_declared_failure_category(
    *,
    fallback_state: str,
    blocked_reason: str,
) -> bool:
    terms = text_terms(blocked_reason)
    return any(
        contains_unnegated_term_group(
            terms,
            (category_terms,),
        )
        for category_terms in _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES[
            fallback_state
        ]
    )


def contains_unnegated_term_group(
    terms: tuple[str, ...],
    term_groups: tuple[tuple[str, ...], ...],
) -> bool:
    for term_group in term_groups:
        if any(
            not any(
                _has_recent_negation(terms, index, window=_NEGATION_SCAN_WINDOW)
                for index in match
            )
            for match in _term_group_matches(terms, term_group)
        ):
            return True
    return False


def contains_simulator_production_truth_overclaim(terms: tuple[str, ...]) -> bool:
    if _contains_simulator_contextual_truth_overclaim(terms):
        return True
    for term_group in _SIMULATOR_PRODUCTION_TRUTH_TERMS:
        if term_group in _SIMULATOR_WORKFLOW_TRUTH_TERMS:
            continue
        for match in _term_group_matches(terms, term_group):
            if any(
                _has_recent_negation(terms, index, window=_NEGATION_SCAN_WINDOW)
                for index in match
            ):
                continue
            if _has_local_post_term_negation(terms, match):
                continue
            if term_group in {
                ("authority",),
                ("authoritative",),
                ("authoritatively",),
            } and _has_non_authoritative_prefix(terms, match[0]):
                continue
            if (
                term_group in _SIMULATOR_EXCLUDABLE_PRODUCTION_TRUTH_TERMS
                and _match_is_required_simulator_exclusion_statement(terms, match)
            ):
                continue
            return True
    return False


def _contains_simulator_contextual_truth_overclaim(
    terms: tuple[str, ...],
) -> bool:
    return (
        _contains_simulator_workflow_contextual_claim(
            terms,
        )
        or _contains_simulator_contextual_claim(
            terms,
            anchor_terms=_SIMULATOR_CLOSURE_ACTION_TERMS,
            required_context_terms=(_SIMULATOR_CLOSURE_CONTEXT_TERMS,),
        )
        or _contains_simulator_contextual_claim(
            terms,
            anchor_terms=_SIMULATOR_ARTIFACT_ASSERTION_TERMS,
            required_context_terms=(
                _SIMULATOR_RECEIPT_CONTEXT_TERMS,
                _SIMULATOR_PRODUCTION_CONTEXT_TERMS,
            ),
        )
        or _contains_simulator_contextual_claim(
            terms,
            anchor_terms=_SIMULATOR_ARTIFACT_ASSERTION_TERMS,
            required_context_terms=(
                _SIMULATOR_RECONCILIATION_CONTEXT_TERMS,
                _SIMULATOR_STATE_CONTEXT_TERMS,
                _SIMULATOR_PRODUCTION_CONTEXT_TERMS,
            ),
        )
    )


def _contains_simulator_contextual_claim(
    terms: tuple[str, ...],
    *,
    anchor_terms: set[str],
    required_context_terms: tuple[set[str], ...],
) -> bool:
    for anchor_index, term in enumerate(terms):
        if term not in anchor_terms:
            continue
        match_indexes = (anchor_index,)
        for context_terms in required_context_terms:
            context_index = _nearest_simulator_context_index(
                terms,
                anchor_index=anchor_index,
                context_terms=context_terms,
            )
            if context_index is None:
                break
            match_indexes = (*match_indexes, context_index)
        else:
            match = tuple(sorted(set(match_indexes)))
            if _simulator_contextual_match_is_negated(terms, match):
                continue
            return True
    return False


def _contains_simulator_workflow_contextual_claim(
    terms: tuple[str, ...],
) -> bool:
    if _contains_simulator_ordered_workflow_claim(terms):
        return True
    for start, stop in _simulator_context_spans(
        terms,
        boundary_terms=_SIMULATOR_WORKFLOW_CONTEXT_CLAUSE_BOUNDARY_TERMS,
    ):
        production_indexes = tuple(
            index
            for index in range(start, stop)
            if terms[index] in _SIMULATOR_PRODUCTION_CONTEXT_TERMS
        )
        if not production_indexes:
            continue
        workflow_indexes = tuple(
            index
            for index in range(start, stop)
            if terms[index] in _SIMULATOR_WORKFLOW_CONTEXT_TERMS
        )
        if not workflow_indexes:
            continue

        for anchor_index in range(start, stop):
            if terms[anchor_index] not in _SIMULATOR_WORKFLOW_ACTION_TERMS:
                continue
            workflow_index = min(
                workflow_indexes,
                key=lambda index: abs(index - anchor_index),
            )
            if abs(workflow_index - anchor_index) > _SIMULATOR_CONTEXT_SCAN_WINDOW:
                continue
            production_index = min(
                production_indexes,
                key=lambda index: abs(index - anchor_index),
            )
            match = tuple(sorted({anchor_index, workflow_index, production_index}))
            if _simulator_contextual_match_is_negated(terms, match):
                continue
            return True
    return False


def _contains_simulator_ordered_workflow_claim(terms: tuple[str, ...]) -> bool:
    for start, stop in _simulator_context_spans(
        terms,
        boundary_terms=_SIMULATOR_CONTEXT_CLAUSE_BOUNDARY_TERMS,
    ):
        production_indexes = tuple(
            index
            for index in range(start, stop)
            if terms[index] in _SIMULATOR_PRODUCTION_CONTEXT_TERMS
        )
        workflow_indexes = tuple(
            index
            for index in range(start, stop)
            if terms[index] in _SIMULATOR_WORKFLOW_CONTEXT_TERMS
        )
        action_indexes = tuple(
            index
            for index in range(start, stop)
            if terms[index] in _SIMULATOR_WORKFLOW_ACTION_TERMS
        )
        for production_index in production_indexes:
            for workflow_index in workflow_indexes:
                if workflow_index <= production_index:
                    continue
                for action_index in action_indexes:
                    if action_index <= workflow_index:
                        continue
                    match = (production_index, workflow_index, action_index)
                    if _simulator_contextual_match_is_negated(terms, match):
                        continue
                    return True
    return False


def _simulator_context_spans(
    terms: tuple[str, ...],
    *,
    boundary_terms: set[str],
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    start = 0
    for index, term in enumerate(terms):
        if term not in boundary_terms:
            continue
        if start < index:
            spans.append((start, index))
        start = index + 1
    if start < len(terms):
        spans.append((start, len(terms)))
    return tuple(spans)


def _nearest_simulator_context_index(
    terms: tuple[str, ...],
    *,
    anchor_index: int,
    context_terms: set[str],
) -> int | None:
    start = max(0, anchor_index - _SIMULATOR_CONTEXT_SCAN_WINDOW)
    stop = min(len(terms), anchor_index + _SIMULATOR_CONTEXT_SCAN_WINDOW + 1)
    candidates = (
        index
        for index in range(start, stop)
        if terms[index] in context_terms
        and not _simulator_context_boundary_between(
            terms,
            anchor_index=anchor_index,
            context_index=index,
        )
    )
    return min(candidates, key=lambda index: abs(index - anchor_index), default=None)


def _simulator_context_boundary_between(
    terms: tuple[str, ...],
    *,
    anchor_index: int,
    context_index: int,
) -> bool:
    lower = min(anchor_index, context_index)
    upper = max(anchor_index, context_index)
    boundary_terms = {
        *_SIMULATOR_CONTEXT_CLAUSE_BOUNDARY_TERMS,
    }
    return any(
        term in boundary_terms
        for term in terms[lower + 1 : upper]
    )


def _simulator_contextual_match_is_negated(
    terms: tuple[str, ...],
    match: tuple[int, ...],
) -> bool:
    return any(
        _has_recent_negation(terms, index, window=_NEGATION_SCAN_WINDOW)
        for index in match
    ) or _has_local_post_term_negation(terms, match)


def _has_local_post_term_negation(
    terms: tuple[str, ...],
    match: tuple[int, ...],
) -> bool:
    start = match[-1] + 1
    stop = min(len(terms), start + 5)
    for index in range(start, stop):
        term = terms[index]
        if term in {
            _TERM_BOUNDARY,
            _TERM_COMMA_BOUNDARY,
            *_NEGATION_CONTRAST_BOUNDARY_TERMS,
        }:
            return False
        if term in _NEGATION_TERMS:
            if _is_not_only_phrase(terms, index, stop):
                continue
            return _post_term_negation_denies_claim(
                terms,
                negation_index=index,
                stop=stop,
            )
    return False


def _post_term_negation_denies_claim(
    terms: tuple[str, ...],
    *,
    negation_index: int,
    stop: int,
) -> bool:
    if terms[negation_index] != "not":
        return False
    for term in terms[negation_index + 1 : stop]:
        if term in {
            _TERM_BOUNDARY,
            _TERM_COMMA_BOUNDARY,
            *_NEGATION_CONTRAST_BOUNDARY_TERMS,
        }:
            return False
        if term in _SIMULATOR_POST_TERM_CLAIM_DENIAL_FILLER_TERMS:
            continue
        return term in _SIMULATOR_POST_TERM_CLAIM_DENIAL_TERMS
    return False


def _has_non_authoritative_prefix(
    terms: tuple[str, ...],
    target_index: int,
) -> bool:
    return target_index > 0 and terms[target_index - 1] == "non"


def _match_is_required_simulator_exclusion_statement(
    terms: tuple[str, ...],
    match: tuple[int, ...],
) -> bool:
    if not match:
        return False
    target_index = match[0]
    start = 0
    for context_index in range(target_index - 1, start - 1, -1):
        term = terms[context_index]
        if term == _TERM_COMMA_BOUNDARY:
            if any(
                link_term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
                for link_term in terms[context_index + 1 : target_index]
            ):
                return False
            continue
        if term in _SIMULATOR_EXCLUSION_CLAIM_BOUNDARY_TERMS:
            return False
        if term in _SIMULATOR_EXCLUSION_CONTEXT_TERMS:
            if any(
                link_term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
                for link_term in terms[context_index + 1 : target_index]
            ):
                return False
            return _match_falls_within_required_exclusion_span(
                terms=terms,
                match=match,
                context_index=context_index,
            )
    return False


def _required_exclusion_groups_are_conjunctive(terms: tuple[str, ...]) -> bool:
    first_group, second_group = _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS
    for first_match in _required_exclusion_term_group_matches(terms, first_group):
        for second_match in _required_exclusion_term_group_matches(terms, second_group):
            if _required_exclusion_matches_are_conjoined(
                terms,
                first_match=first_match,
                second_match=second_match,
            ):
                return True
    return False


def _required_exclusion_matches_are_conjoined(
    terms: tuple[str, ...],
    *,
    first_match: tuple[int, ...],
    second_match: tuple[int, ...],
) -> bool:
    if first_match[0] <= second_match[0]:
        left_match = first_match
        right_match = second_match
    else:
        left_match = second_match
        right_match = first_match
    if left_match[-1] >= right_match[0]:
        return False
    between = terms[left_match[-1] + 1 : right_match[0]]
    if "or" in between:
        return False
    if any(
        term in {_TERM_BOUNDARY, *_NEGATION_CONTRAST_BOUNDARY_TERMS}
        for term in between
    ):
        return False
    return "and" in between


def _match_falls_within_required_exclusion_span(
    *,
    terms: tuple[str, ...],
    match: tuple[int, ...],
    context_index: int,
) -> bool:
    required_group_orders = (
        _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS,
        tuple(reversed(_SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS)),
    )
    for first_group, second_group in required_group_orders:
        for first_match in _required_exclusion_term_group_matches(
            terms,
            first_group,
        ):
            if first_match[0] <= context_index:
                continue
            if _required_exclusion_group_between_context_and_span_start(
                terms=terms,
                context_index=context_index,
                span_start=first_match[0],
            ):
                continue
            for second_match in _required_exclusion_term_group_matches(
                terms,
                second_group,
            ):
                if second_match[0] <= first_match[-1]:
                    continue
                if not _required_exclusion_matches_are_conjoined(
                    terms,
                    first_match=first_match,
                    second_match=second_match,
                ):
                    continue
                if first_match[0] <= match[0] and match[-1] <= second_match[-1]:
                    return True
    return False


def _required_exclusion_group_between_context_and_span_start(
    *,
    terms: tuple[str, ...],
    context_index: int,
    span_start: int,
) -> bool:
    return any(
        context_index < group_match[0] < span_start
        for term_group in _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS
        for group_match in _required_exclusion_term_group_matches(terms, term_group)
    )


def _required_exclusion_term_group_matches(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        match
        for match in _term_group_matches(terms, required_terms)
        if not any(
            term in _NEGATION_LIST_BOUNDARY_TERMS
            for term in terms[match[0] + 1 : match[-1]]
        )
    )


def contains_unnegated_single_term(
    terms: tuple[str, ...],
    target_terms: tuple[str, ...],
) -> bool:
    for index, term in enumerate(terms):
        if term in target_terms and not _has_recent_negation(
            terms,
            index,
            window=_NEGATION_SCAN_WINDOW,
        ):
            return True
    return False


def _term_group_starts(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[int, ...]:
    return tuple(match[0] for match in _term_group_matches(terms, required_terms))


def _term_group_matches(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[tuple[int, ...], ...]:
    if not required_terms or len(required_terms) > len(terms):
        return ()
    matches: list[tuple[int, ...]] = []

    def matches_from(
        term_index: int,
        required_index: int,
        matched_indexes: tuple[int, ...],
    ) -> None:
        if required_index == len(required_terms):
            matches.append(matched_indexes)
            return
        next_term = required_terms[required_index]
        max_next_index = min(
            len(terms),
            term_index + _TERM_GROUP_MAX_INTERVENING_TERMS + 2,
        )
        for next_index in range(term_index + 1, max_next_index):
            if terms[next_index] in {_TERM_BOUNDARY, _TERM_COMMA_BOUNDARY}:
                break
            if _term_matches_required(terms[next_index], next_term):
                matches_from(
                    next_index,
                    required_index + 1,
                    (*matched_indexes, next_index),
                )

    for index, term in enumerate(terms):
        if not _term_matches_required(term, required_terms[0]):
            continue
        matches_from(index, 1, (index,))
    return tuple(matches)


def _term_matches_required(term: str, required_term: str) -> bool:
    if term == required_term:
        return True
    if len(required_term) <= 2 or required_term.endswith("s"):
        return False
    if term == f"{required_term}s":
        return True
    if required_term.endswith(("s", "x", "ch", "sh")) and term == f"{required_term}es":
        return True
    if required_term.endswith("y") and term == f"{required_term[:-1]}ies":
        return True
    return False


def _has_recent_negation(
    terms: tuple[str, ...],
    index: int,
    *,
    window: int,
) -> bool:
    start = max(0, index - window)
    for negation_index in range(index - 1, start - 1, -1):
        term = terms[negation_index]
        if term in _NEGATION_HARD_BOUNDARY_TERMS:
            return False
        if term in _NEGATION_CONTRAST_BOUNDARY_TERMS:
            return False
        if (
            term in {_TERM_COMMA_BOUNDARY, *_NEGATION_LIST_BOUNDARY_TERMS}
            and _list_boundary_starts_new_subject(
                terms=terms,
                boundary_index=negation_index,
                target_index=index,
            )
        ):
            return False
        if term in _NEGATION_TERMS:
            if _is_not_only_phrase(terms, negation_index, index):
                continue
            return True
    return False


def _is_not_only_phrase(
    terms: tuple[str, ...],
    negation_index: int,
    target_index: int,
) -> bool:
    return (
        terms[negation_index] == "not"
        and negation_index + 1 < target_index
        and terms[negation_index + 1] == "only"
    )


def _list_boundary_starts_new_subject(
    *,
    terms: tuple[str, ...],
    boundary_index: int,
    target_index: int,
) -> bool:
    if terms[boundary_index] == "and" and _TERM_COMMA_BOUNDARY not in terms[
        max(0, boundary_index - _NEGATION_SCAN_WINDOW) : boundary_index
    ]:
        return True
    if any(
        term in {_TERM_COMMA_BOUNDARY, *_NEGATION_LIST_BOUNDARY_TERMS}
        for term in terms[boundary_index + 1 : target_index]
    ):
        return False
    return any(
        term in _NEGATION_LIST_SUBJECT_TERMS
        for term in terms[boundary_index + 1 : target_index + 1]
    )


def text_terms(value: str) -> tuple[str, ...]:
    normalized = (
        value.lower()
        .replace("n't", " not")
        .replace("n\u2019t", " not")
        .replace("n\u2018t", " not")
    )
    return _tokenize_with_boundaries(normalized)


def _tokenize_with_boundaries(value: str) -> tuple[str, ...]:
    characters: list[str] = []
    for char in value:
        if char.isalnum():
            characters.append(char)
        elif char == ",":
            characters.append(f" {_TERM_COMMA_BOUNDARY} ")
        elif char in ".;:!?":
            characters.append(f" {_TERM_BOUNDARY} ")
        else:
            characters.append(" ")
    return tuple("".join(characters).split())

