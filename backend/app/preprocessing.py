"""
Preprocessing Worker (per architecture diagram).
Normalizes text, detects language, and strips PII before the text ever reaches Groq.

PII stripping is a security requirement (PRD Section 11) — not optional, since the
raw dataset contains real-shaped names/emails and we don't want those hitting a
third-party LLM provider unnecessarily.
"""

import re
from dataclasses import dataclass

try:
    from langdetect import LangDetectException, detect
except ImportError:  # pragma: no cover - optional dependency guard
    detect = None
    LangDetectException = Exception

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
ZIP_RE = re.compile(r"\b\d{5}(-\d{4})?\b")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class PreprocessResult:
    clean_text: str
    language: str
    pii_redacted_count: int


def strip_pii(text: str) -> tuple[str, int]:
    """Redact emails, phone-like numbers, and zip codes. Returns (clean_text, redaction_count)."""
    count = 0

    def _sub(pattern: re.Pattern, replacement: str, s: str) -> str:
        nonlocal count
        new_s, n = pattern.subn(replacement, s)
        count += n
        return new_s

    text = _sub(EMAIL_RE, "[REDACTED_EMAIL]", text)
    text = _sub(PHONE_RE, "[REDACTED_PHONE]", text)
    text = _sub(ZIP_RE, "[REDACTED_ZIP]", text)
    return text, count


def normalize_text(text: str) -> str:
    text = text.strip()
    text = WHITESPACE_RE.sub(" ", text)
    return text


def detect_language(text: str) -> str:
    if detect is None:
        return "unknown"
    try:
        return str(detect(text))
    except LangDetectException:
        return "unknown"


def preprocess(raw_text: str) -> PreprocessResult:
    normalized = normalize_text(raw_text)
    redacted, pii_count = strip_pii(normalized)
    lang = detect_language(redacted)
    return PreprocessResult(clean_text=redacted, language=lang, pii_redacted_count=pii_count)
