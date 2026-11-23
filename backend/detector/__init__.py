"""Highlight Detector & Scoring Subsystem."""

from backend.detector.highlight_detector import detect_highlights
from backend.detector.highlight_scorer import ScoreBreakdown, ScoreFactor, SmartHighlightScorer
from backend.detector.models import DetectorSettings, HighlightCandidate, HighlightType

__all__ = [
    "detect_highlights",
    "DetectorSettings",
    "HighlightCandidate",
    "HighlightType",
    "ScoreBreakdown",
    "ScoreFactor",
    "SmartHighlightScorer",
]
