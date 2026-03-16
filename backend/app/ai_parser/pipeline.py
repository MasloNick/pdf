"""Hybrid AI parsing pipeline for Ukrainian court decisions.

Three-level approach:
  Level 1: Rule-based parser with keyword markers (~80% of decisions)
  Level 2: Local LLM (MamayLM-Gemma-2-9B) for complex cases
  Level 3: Claude API fallback for NEEDS_REVIEW (confidence < 0.65)
"""

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.court_case import CourtDecision

logger = logging.getLogger(__name__)

MISSING = "MISSING_IN_DECISION"


@dataclass
class ParseResult:
    """Structured result of parsing a court decision."""

    outcome: str | None = None  # satisfied / partial / rejected / returned
    awarded_total: Decimal | None = None
    awarded_principal: Decimal | None = None
    awarded_interest: Decimal | None = None
    awarded_penalties: Decimal | None = None
    awarded_court_fee: Decimal | None = None
    awarded_3percent: Decimal | None = None
    awarded_inflation: Decimal | None = None
    claimed_amount: Decimal | None = None
    rejection_reasons: list[str] = field(default_factory=list)
    key_findings: dict = field(default_factory=dict)
    confidence: float = 0.0
    parse_method: str = "rules"
    needs_review: bool = False
    review_reason: str | None = None


# ---------------------------------------------------------------------------
# Level 1: Rule-based markers
# ---------------------------------------------------------------------------

OUTCOME_MARKERS = {
    "позов задовольнити повністю": "satisfied",
    "позовні вимоги задовольнити": "satisfied",
    "позов задовольнити": "satisfied",
    "позов задовольнити частково": "partial",
    "позовні вимоги задовольнити частково": "partial",
    "у задоволенні позову відмовити": "rejected",
    "відмовити у задоволенні": "rejected",
    "позовну заяву повернути": "returned",
    "залишити без розгляду": "returned",
}

AMOUNT_PATTERNS = {
    "awarded_principal": [
        r"стягнути.*?(?:основн|тіл).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
    "awarded_interest": [
        r"(?:процент|відсотк).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
    "awarded_penalties": [
        r"(?:пен[яі]|штраф|неустойк).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
    "awarded_court_fee": [
        r"(?:судов\w+ збір|судовий збір).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
    "awarded_3percent": [
        r"(?:3\s*%|три відсотк).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
    "awarded_inflation": [
        r"(?:інфляц).*?(\d[\d\s]*[\.,]\d{2})\s*(?:грн|гривень)",
    ],
}


def _parse_amount(text: str) -> Decimal | None:
    """Convert matched amount text to Decimal."""
    cleaned = text.replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def rule_based_parse(text: str) -> ParseResult:
    """Level 1: Parse decision text using regex patterns and keyword markers."""
    result = ParseResult(parse_method="rules")
    text_lower = text.lower()

    # Determine outcome
    for marker, outcome in OUTCOME_MARKERS.items():
        if marker in text_lower:
            result.outcome = outcome
            result.confidence = 0.8
            break

    # Extract amounts
    for field_name, patterns in AMOUNT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount = _parse_amount(match.group(1))
                if amount is not None:
                    setattr(result, field_name, amount)
                break

    # Calculate total
    components = [
        result.awarded_principal,
        result.awarded_interest,
        result.awarded_penalties,
        result.awarded_court_fee,
        result.awarded_3percent,
        result.awarded_inflation,
    ]
    non_none = [c for c in components if c is not None]
    if non_none:
        result.awarded_total = sum(non_none, Decimal(0))

    # Determine if review needed
    if result.outcome is None:
        result.confidence = 0.3
        result.needs_review = True
        result.review_reason = "Could not determine outcome"
    elif result.awarded_total is None and result.outcome in ("satisfied", "partial"):
        result.confidence = 0.5
        result.needs_review = True
        result.review_reason = "Outcome found but no amounts extracted"

    return result


# ---------------------------------------------------------------------------
# Level 2: Local LLM (stub — implement with llama.cpp / vLLM)
# ---------------------------------------------------------------------------


def local_llm_parse(text: str) -> ParseResult:
    """Level 2: Parse using local MamayLM model. Returns NEEDS_REVIEW if not confident."""
    # TODO: Integrate with llama.cpp or vLLM server
    logger.info("Local LLM parse requested (not yet implemented)")
    result = ParseResult(
        parse_method="local_llm",
        confidence=0.0,
        needs_review=True,
        review_reason="Local LLM not yet configured",
    )
    return result


# ---------------------------------------------------------------------------
# Level 3: Claude API fallback
# ---------------------------------------------------------------------------


def claude_api_parse(text: str) -> ParseResult:
    """Level 3: Parse using Claude API for complex / low-confidence decisions."""
    if not settings.CLAUDE_API_KEY:
        logger.warning("Claude API key not configured")
        return ParseResult(
            parse_method="claude",
            confidence=0.0,
            needs_review=True,
            review_reason="Claude API key not configured",
        )

    # TODO: Implement Claude API call with structured output
    logger.info("Claude API parse requested (not yet implemented)")
    return ParseResult(
        parse_method="claude",
        confidence=0.0,
        needs_review=True,
        review_reason="Claude API integration pending",
    )


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------


def parse_decision_text(text: str) -> ParseResult:
    """Run the hybrid parsing pipeline on raw decision text."""
    # Level 1
    result = rule_based_parse(text)
    if result.confidence >= settings.AI_CONFIDENCE_THRESHOLD:
        return result

    # Level 2
    llm_result = local_llm_parse(text)
    if llm_result.confidence >= settings.AI_CONFIDENCE_THRESHOLD:
        return llm_result

    # Level 3
    claude_result = claude_api_parse(text)
    if claude_result.confidence >= settings.AI_CONFIDENCE_THRESHOLD:
        return claude_result

    # Return best available (prefer higher confidence)
    candidates = [result, llm_result, claude_result]
    return max(candidates, key=lambda r: r.confidence)


def parse_decision_by_id(decision_id: int) -> dict:
    """Load a CourtDecision from DB, parse it, and save results."""
    with SyncSessionLocal() as db:
        decision = db.execute(
            select(CourtDecision).where(CourtDecision.id == decision_id)
        ).scalar_one_or_none()

        if not decision:
            return {"error": "Decision not found"}

        if not decision.raw_text:
            return {"error": "No raw text to parse"}

        result = parse_decision_text(decision.raw_text)

        # Update decision record
        decision.outcome = result.outcome
        decision.awarded_total = result.awarded_total
        decision.awarded_principal = result.awarded_principal
        decision.awarded_interest = result.awarded_interest
        decision.awarded_penalties = result.awarded_penalties
        decision.awarded_court_fee = result.awarded_court_fee
        decision.awarded_3percent = result.awarded_3percent
        decision.awarded_inflation = result.awarded_inflation
        decision.claimed_amount = result.claimed_amount
        decision.confidence = result.confidence
        decision.parse_method = result.parse_method
        decision.needs_review = result.needs_review
        decision.review_reason = result.review_reason
        decision.rejection_reasons = (
            {"reasons": result.rejection_reasons} if result.rejection_reasons else None
        )
        decision.key_findings = result.key_findings or None

        db.commit()
        return {
            "decision_id": decision_id,
            "outcome": result.outcome,
            "confidence": result.confidence,
            "parse_method": result.parse_method,
            "needs_review": result.needs_review,
        }
