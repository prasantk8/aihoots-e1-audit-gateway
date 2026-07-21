"""Pre-flight policy checks. Every decision is auditable (ADR-001 guideline 2).

Deliberately simple rules: the *pattern* (audited, explainable decisions) is the
product, not the sophistication of the rules. Precision/recall of these checks is
measured honestly against a labelled corpus — see tests/corpus and the Evaluation
section of the article.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"


@dataclass
class PolicyResult:
    decision: Decision
    text: str                 # possibly redacted prompt
    reasons: list[str]


# Illustrative PII patterns. Intentionally conservative and documented; a real
# deployment would tune these and measure them (that measurement is the point).
_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "credit_card_like": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

_BLOCKLIST = [
    # Matches "ignore instructions", "ignore all instructions",
    # "ignore previous instructions", "ignore all previous instructions", etc.
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous\s+|prior\s+|above\s+)?instructions\b",
               re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:previous\s+|prior\s+)?instructions\b",
               re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
]

_MAX_PROMPT_CHARS = 8000


def evaluate(prompt: str) -> PolicyResult:
    reasons: list[str] = []

    if len(prompt) > _MAX_PROMPT_CHARS:
        return PolicyResult(Decision.BLOCK, prompt, [f"prompt exceeds {_MAX_PROMPT_CHARS} chars"])

    for pattern in _BLOCKLIST:
        if pattern.search(prompt):
            return PolicyResult(Decision.BLOCK, prompt, [f"blocklist match: {pattern.pattern}"])

    redacted = prompt
    for label, pattern in _PII_PATTERNS.items():
        if pattern.search(redacted):
            redacted = pattern.sub(f"[REDACTED:{label}]", redacted)
            reasons.append(f"redacted {label}")

    if reasons:
        return PolicyResult(Decision.REDACT, redacted, reasons)
    return PolicyResult(Decision.ALLOW, prompt, ["no policy triggers"])
