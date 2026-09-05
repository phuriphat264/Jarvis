"""
ConfidenceEngine — Deterministic preference confidence calculator.

Formula:
    confidence = min(1.0, 0.15 * log2(evidence_count + 1))

Evidence → Confidence (approx):
    1  →  0.15
    5  →  0.35
   15  →  0.59
   30  →  0.74
  100  →  1.00 (capped)

USER_EXPLICIT always → 1.0
"""
import math
from typing import Literal


SOURCE = Literal["USER_EXPLICIT", "BEHAVIOR"]


class ConfidenceEngine:
    BASE_FACTOR = 0.15

    @classmethod
    def calculate(cls, evidence_count: int, source: SOURCE) -> float:
        if source == "USER_EXPLICIT":
            return 1.0
        if evidence_count <= 0:
            return 0.0
        raw = cls.BASE_FACTOR * math.log2(evidence_count + 1)
        return round(min(1.0, raw), 4)

    @classmethod
    def meets_threshold(cls, confidence: float, threshold: float = 0.75) -> bool:
        return confidence >= threshold

    @classmethod
    def decay(cls, current_confidence: float, days_inactive: int, decay_days: int = 90) -> float:
        """Linear decay over decay_days. Floors at 0.0."""
        if days_inactive <= 0:
            return current_confidence
        factor = max(0.0, 1.0 - (days_inactive / decay_days))
        return round(current_confidence * factor, 4)
