"""Validation and normalization for LLM investigation responses."""

from typing import Any


REQUIRED_FIELDS = [
    "finding",
    "risk_indicators",
    "evidence_used",
    "triggered_rules",
    "risk_score",
    "recommendation",
]


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient retrieved evidence was provided to support "
    "a specific investigation finding."
)


def validate_response(
    generated: dict[str, Any],
    evidence: list[dict],
    triggered_rules: list[dict],
    risk_score: int,
) -> dict[str, Any]:
    """
    Validate and normalize a Phi-3 investigation response.

    The LLM generates the explanation and selects supporting evidence.
    Python remains authoritative for evidence IDs, rule IDs, risk score,
    and recommendation.

    When no evidence is available, Python prevents the LLM from making
    unsupported factual claims.
    """

    # ---------------------------------------------------------
    # 1. Validate required response fields
    # ---------------------------------------------------------

    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if field not in generated
    ]

    if missing_fields:
        raise ValueError(
            f"Missing fields in LLM response: {missing_fields}"
        )

    # ---------------------------------------------------------
    # 2. Validate basic response types
    # ---------------------------------------------------------

    if not isinstance(generated["finding"], str):
        raise ValueError(
            "LLM field 'finding' must be a string."
        )

    if not isinstance(generated["risk_indicators"], list):
        raise ValueError(
            "LLM field 'risk_indicators' must be a list."
        )

    if not isinstance(generated["evidence_used"], list):
        raise ValueError(
            "LLM field 'evidence_used' must be a list."
        )

    if not isinstance(generated["triggered_rules"], list):
        raise ValueError(
            "LLM field 'triggered_rules' must be a list."
        )

    # ---------------------------------------------------------
    # 3. Build authoritative evidence ID set
    # ---------------------------------------------------------

    valid_evidence_ids = {
        item.get("id")
        for item in evidence
        if item.get("id")
    }

    # Keep only evidence IDs that actually came from retrieval.
    generated["evidence_used"] = [
        evidence_id
        for evidence_id in generated["evidence_used"]
        if evidence_id in valid_evidence_ids
    ]

    # ---------------------------------------------------------
    # 4. Build authoritative rule ID set
    # ---------------------------------------------------------

    valid_rule_ids = {
        rule.get("id")
        for rule in triggered_rules
        if rule.get("id")
    }

    # Keep only rule IDs that actually came from the rule engine.
    generated["triggered_rules"] = [
        rule_id
        for rule_id in generated["triggered_rules"]
        if rule_id in valid_rule_ids
    ]

    # ---------------------------------------------------------
    # 5. Handle missing evidence
    # ---------------------------------------------------------

    if not evidence:
        generated["finding"] = INSUFFICIENT_EVIDENCE_MESSAGE
        generated["risk_indicators"] = []
        generated["evidence_used"] = []

    else:
        # Normalize risk indicators.
        generated["risk_indicators"] = [
            indicator
            for indicator in generated["risk_indicators"]
            if isinstance(indicator, str) and indicator.strip()
        ]

    # ---------------------------------------------------------
    # 6. Business-rule engine owns the risk score
    # ---------------------------------------------------------

    generated["risk_score"] = risk_score

    # ---------------------------------------------------------
    # 7. Business-rule engine owns the recommendation
    # ---------------------------------------------------------

    if triggered_rules:
        expected_recommendation = triggered_rules[0].get("action")

        if expected_recommendation:
            generated["recommendation"] = expected_recommendation

    return generated


def build_citations(evidence: list[dict]) -> list[str]:
    """Build citations from the actual retrieved evidence."""

    return [
        item.get("id", item.get("source", "unknown"))
        for item in evidence
    ]