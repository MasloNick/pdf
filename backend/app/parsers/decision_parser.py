"""Hybrid 3-level court decision parser.

Level 1: Rule-based parser with marker dictionary (~80%, fast, stable)
Level 2: Local LLM (MamayLM-Gemma-2-9B) via llama.cpp/vLLM
Level 3: Claude API fallback for low-confidence results

Principle: NEVER guess. If data is missing → MISSING_IN_DECISION.
If confidence < threshold → NEEDS_REVIEW with reason.
"""

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

logger = logging.getLogger(__name__)


class ParseMethod(StrEnum):
    RULES = "rules"
    LOCAL_LLM = "local_llm"
    CLAUDE_API = "claude_api"


@dataclass
class ParseResult:
    result: str = "MISSING_IN_DECISION"
    awarded_principal: Decimal | None = None
    awarded_interest: Decimal | None = None
    awarded_penalties: Decimal | None = None
    awarded_court_fee: Decimal | None = None
    awarded_total: Decimal | None = None
    denial_reason: str | None = None
    summary: str | None = None
    confidence: float = 0.0
    method: ParseMethod = ParseMethod.RULES
    needs_review: bool = False
    review_reason: str | None = None
    raw_data: dict = field(default_factory=dict)


# ── Ukrainian legal markers ─────────────────────────────────
SATISFACTION_MARKERS = [
    r"позов(?:ні вимоги)?\s+задовольнити",
    r"позов\s+задоволити",
    r"стягнути\s+з\s+відповідача",
    r"вирішив[:\s]*задовольнити",
    r"ухвалив[:\s]*стягнути",
]

PARTIAL_MARKERS = [
    r"задовольнити\s+частково",
    r"позов\s+задоволити\s+частково",
    r"частково\s+задовольнити",
]

DENIAL_MARKERS = [
    r"у задоволенні\s+(?:позову\s+)?відмовити",
    r"відмовити\s+у\s+задоволенні",
    r"позов(?:ні вимоги)?\s+залишити\s+без\s+задоволення",
]

AMOUNT_PATTERN = re.compile(
    r"(\d[\d\s]*[\d])[,.](\d{2})\s*(?:грн|гривень|UAH)",
    re.IGNORECASE,
)

COURT_FEE_PATTERN = re.compile(
    r"судов(?:ий|ого)\s+збор(?:у|)\s*(?:в розмірі|у сумі|)\s*"
    r"(\d[\d\s]*[\d])[,.](\d{2})\s*(?:грн|гривень)",
    re.IGNORECASE,
)


def _extract_amount(text: str) -> Decimal | None:
    """Extract the first monetary amount from text."""
    match = AMOUNT_PATTERN.search(text)
    if match:
        integer_part = match.group(1).replace(" ", "")
        decimal_part = match.group(2)
        return Decimal(f"{integer_part}.{decimal_part}")
    return None


def _extract_court_fee(text: str) -> Decimal | None:
    """Extract court fee amount."""
    match = COURT_FEE_PATTERN.search(text)
    if match:
        integer_part = match.group(1).replace(" ", "")
        decimal_part = match.group(2)
        return Decimal(f"{integer_part}.{decimal_part}")
    return None


class RuleBasedParser:
    """Level 1: Fast rule-based parser using regex markers."""

    def parse(self, text: str) -> ParseResult:
        result = ParseResult(method=ParseMethod.RULES)
        text_lower = text.lower()

        # Determine outcome
        for pattern in PARTIAL_MARKERS:
            if re.search(pattern, text_lower):
                result.result = "partially_satisfied"
                result.confidence = 0.80
                break
        else:
            for pattern in SATISFACTION_MARKERS:
                if re.search(pattern, text_lower):
                    result.result = "satisfied"
                    result.confidence = 0.85
                    break
            else:
                for pattern in DENIAL_MARKERS:
                    if re.search(pattern, text_lower):
                        result.result = "denied"
                        result.confidence = 0.85
                        break

        # Extract amounts from operative part
        operative = self._extract_operative_part(text)
        if operative:
            result.awarded_total = _extract_amount(operative)
            result.awarded_court_fee = _extract_court_fee(operative)

        if result.result == "MISSING_IN_DECISION":
            result.confidence = 0.0
            result.needs_review = True
            result.review_reason = "Could not determine decision outcome from text"

        return result

    def _extract_operative_part(self, text: str) -> str | None:
        """Extract the operative (резолютивна) part of the decision."""
        markers = ["ВИРІШИВ", "УХВАЛИВ", "ПОСТАНОВИВ"]
        for marker in markers:
            idx = text.upper().find(marker)
            if idx != -1:
                return text[idx:]
        return None


class LocalLLMParser:
    """Level 2: Local LLM (MamayLM-Gemma-2-9B-IT) for complex decisions."""

    def __init__(self, api_url: str, model: str):
        self.api_url = api_url
        self.model = model

    def parse(self, text: str) -> ParseResult:
        """Send text to local LLM and parse structured response."""
        # TODO: Implement OpenAI-compatible API call to local vLLM/llama.cpp
        # Prompt should request JSON output with specific fields
        logger.info("Local LLM parsing requested (not yet implemented)")
        return ParseResult(
            method=ParseMethod.LOCAL_LLM,
            needs_review=True,
            review_reason="Local LLM integration pending implementation",
        )


class ClaudeAPIParser:
    """Level 3: Claude API fallback for NEEDS_REVIEW cases."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def parse(self, text: str) -> ParseResult:
        """Send to Claude API as fallback."""
        # TODO: Implement Anthropic SDK call
        logger.info("Claude API parsing requested (not yet implemented)")
        return ParseResult(
            method=ParseMethod.CLAUDE_API,
            needs_review=True,
            review_reason="Claude API integration pending implementation",
        )


class DecisionParserPipeline:
    """3-level hybrid parsing pipeline."""

    def __init__(self):
        from app.core.config import settings

        self.rule_parser = RuleBasedParser()
        self.local_llm = LocalLLMParser(settings.LOCAL_LLM_URL, settings.LOCAL_LLM_MODEL)
        self.claude_parser = ClaudeAPIParser(settings.CLAUDE_API_KEY, settings.CLAUDE_MODEL)
        self.confidence_threshold = settings.AI_CONFIDENCE_THRESHOLD

    def parse(self, decision_id: str) -> dict:
        """Run decision through the pipeline.

        1. Try rules first (fast)
        2. If confidence < threshold → try local LLM
        3. If still low → fall back to Claude API
        """
        # TODO: Load decision text from database
        text = ""  # placeholder

        # Level 1: Rules
        result = self.rule_parser.parse(text)
        if result.confidence >= self.confidence_threshold:
            return self._to_dict(result)

        logger.info("Rule-based confidence %.2f < %.2f, escalating to local LLM",
                     result.confidence, self.confidence_threshold)

        # Level 2: Local LLM
        result = self.local_llm.parse(text)
        if result.confidence >= self.confidence_threshold:
            return self._to_dict(result)

        logger.info("Local LLM confidence %.2f < %.2f, escalating to Claude API",
                     result.confidence, self.confidence_threshold)

        # Level 3: Claude API
        if self.claude_parser.api_key:
            result = self.claude_parser.parse(text)

        return self._to_dict(result)

    def _to_dict(self, result: ParseResult) -> dict:
        return {
            "result": result.result,
            "awarded_principal": str(result.awarded_principal) if result.awarded_principal else None,
            "awarded_interest": str(result.awarded_interest) if result.awarded_interest else None,
            "awarded_penalties": str(result.awarded_penalties) if result.awarded_penalties else None,
            "awarded_court_fee": str(result.awarded_court_fee) if result.awarded_court_fee else None,
            "awarded_total": str(result.awarded_total) if result.awarded_total else None,
            "denial_reason": result.denial_reason,
            "summary": result.summary,
            "confidence": result.confidence,
            "method": result.method,
            "needs_review": result.needs_review,
            "review_reason": result.review_reason,
        }
