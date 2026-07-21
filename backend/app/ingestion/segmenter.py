"""
Intelligent document segmentation engine.

Strategy (in order of precedence):

  1. **Structured Dataset Parser** — detects explicit separator blocks
     (===, ---, ###, etc.) that denote ticket boundaries.  When found,
     rule-based and AI segmentation are skipped entirely.

  2. **Rule-based** — regex patterns for ticket IDs, case IDs, email headers, etc.

  3. **AI-assisted** — LLM call to find semantic boundaries.

  4. **Line-break fallback** — split on double newlines.
"""

import re
from dataclasses import dataclass, field

from app.logging import get_logger

logger = get_logger(__name__)

MIN_SEGMENT_CHARS = 20
MAX_SEGMENT_CHARS = 4000

# ── Structured-separator patterns (Stage 1) ───────────────────────────────
#
# These patterns are matched as **blocks** — one or more consecutive lines
# that form the separator.  Everything between two separator blocks is
# treated as ticket content and the separator lines are discarded.

# A single separator block: lines of === or --- optionally wrapping a label.
# Examples:
#   ============================================================
#   TICKET 01
#   ============================================================
#
#   ------------------------------------------------------------
#   TICKET 02
#   ------------------------------------------------------------
#
#   ### TICKET 03 ###
#
#   === Ticket 04 ===
#
#   ===== CASE 05 =====
#
_STRUCTURED_SEPARATOR_RE = re.compile(
    r"""
    (?:                                         # Option A: decorative-block form
        ^ [=\-*]{3,} \s* $                      #   opening ruler
        (?: \n .+ )?                            #   optional label line (e.g. TICKET 01)
        (?: \n [=\-*]{3,} \s* $ )?              #   optional closing ruler
    )
    |
    (?:                                         # Option B: inline label between markers
        ^ \#\#\# \s* (?:TICKET|CASE) \s+ \d+ \s* \#\#\# \s* $
    )
    |
    (?:                                         # Option C: === label ===
        ^ [=\-]++ \s+ (?:TICKET|CASE) \s+ \d+ \s+ [=\-]++ \s* $
    )
    """,
    re.MULTILINE | re.VERBOSE | re.IGNORECASE,
)

# A standalone ruler with no label (pure visual separator).
_STANDALONE_RULER_RE = re.compile(r"^[=\-*_]{3,}\s*$", re.MULTILINE)


def _find_structured_separators(text: str) -> list[tuple[int, int]]:
    """
    Find all structured separator **blocks** as (start, end) spans.
    A block may be 1–3 lines: an optional ruler, an optional label,
    and an optional closing ruler.

    Adjacent separator blocks that are only separated by whitespace are
    merged into a single block so ticket content between them is empty
    and gets discarded.
    """
    matches: list[tuple[int, int]] = []

    for m in _STRUCTURED_SEPARATOR_RE.finditer(text):
        matches.append((m.start(), m.end()))

    # Also detect standalone ruler lines (===, ---, etc. with no label)
    for m in _STANDALONE_RULER_RE.finditer(text):
        start, end = m.start(), m.end()
        # Check whether this ruler is already part of a structured block
        already_covered = any(s <= start and end <= e for s, e in matches)
        if not already_covered:
            matches.append((start, end))

    if not matches:
        return []

    matches.sort(key=lambda x: x[0])

    # Merge adjacent / overlapping blocks and blocks separated only by whitespace
    merged: list[tuple[int, int]] = [matches[0]]
    for start, end in matches[1:]:
        prev_s, prev_e = merged[-1]
        gap = text[prev_e:start]
        # If gap is only whitespace or empty, merge
        if not gap.strip():
            merged[-1] = (prev_s, max(prev_e, end))
        else:
            merged.append((start, end))

    return merged


def _extract_structured_tickets(text: str) -> tuple[list[str], int]:
    """
    Use structured separators to split text into tickets.

    Returns (ticket_texts, separator_count).
    Each ticket text has separator lines removed.
    """
    blocks = _find_structured_separators(text)

    if not blocks:
        return [], 0

    logger.info("Structured separators found: %d", len(blocks))
    for i, (s, e) in enumerate(blocks):
        snippet = text[s:e].replace("\n", "\\n")
        logger.debug("  Separator %d: pos %d-%d -> %r", i + 1, s, e, snippet[:80])

    # Extract text between separators
    tickets: list[str] = []
    prev_end = 0

    for start, end in blocks:
        # Content from prev_end to this separator start
        chunk = text[prev_end:start].strip()
        if chunk:
            tickets.append(chunk)
        prev_end = end

    # Last chunk after the final separator
    tail = text[prev_end:].strip()
    if tail:
        tickets.append(tail)

    # Remove any tickets that are only remnants of separator lines
    cleaned: list[str] = []
    for t in tickets:
        lines = [l for l in t.split("\n") if not _STANDALONE_RULER_RE.match(l)]
        cleaned_text = "\n".join(lines).strip()
        if cleaned_text:
            cleaned.append(cleaned_text)

    empty_removed = len(tickets) - len(cleaned)
    if empty_removed:
        logger.info("Empty tickets removed: %d", empty_removed)

    logger.info("Tickets extracted: %d", len(cleaned))
    return cleaned, len(blocks)


# ── Rule-based patterns (Stage 2) ─────────────────────────────────────────

_TICKET_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(?:Ticket|Tkt|Case|Issue)\s*[#]?\s*\d+\s*[:.]?\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:Case|Incident|Support|Request|Complaint)\s*(?:#|ID)?\s*:?\s*\S+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:Order|Transaction|Refund)\s*(?:#|ID)?\s*:?\s*\S+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:Customer|Account|User)\s*(?:#|ID)?\s*:?\s*\S+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:Chat|Conversation|Session)\s*(?:Start|Begin|Log|#)", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:From|To|Cc|Bcc|Subject|Date)\s*:", re.MULTILINE),
    re.compile(r"^[-=*_]{3,}\s*$", re.MULTILINE),
    re.compile(r"^-+\s*Page\s+\d+\s*-+\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"\[PAGE\s+BREAK\]", re.MULTILINE | re.IGNORECASE),
    re.compile(r"\f"),
    re.compile(r"^\d+[\.\)]\s+(?:Ticket|Case|Issue|Request|Complaint|Order)", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:New|Next)\s+(?:Ticket|Case|Issue|Request|Complaint|Conversation)", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(?:Ticket|Case|Issue|Request|Complaint)\s+#?\d+", re.MULTILINE | re.IGNORECASE),
]


@dataclass
class Segment:
    text: str
    index: int
    word_count: int = 0
    char_count: int = 0
    boundary_type: str = "auto"
    valid: bool = True
    validation_message: str | None = None

    def __post_init__(self):
        self.word_count = len(self.text.split())
        self.char_count = len(self.text)


@dataclass
class SegmentationResult:
    segments: list[Segment]
    method: str  # "structured", "rule", "ai", "line_break", "single"
    warnings: list[str] = field(default_factory=list)


# ── Stage 2: Rule engine ──────────────────────────────────────────────────


def _find_boundaries(text: str) -> list[tuple[int, str]]:
    boundaries: list[tuple[int, str]] = []
    for pattern in _TICKET_PATTERNS:
        for match in pattern.finditer(text):
            pos = match.start()
            btype = _classify_pattern(pattern)
            boundaries.append((pos, btype))

    boundaries.sort(key=lambda x: x[0])
    deduped: list[tuple[int, str]] = []
    for pos, btype in boundaries:
        if deduped and abs(pos - deduped[-1][0]) < 5:
            continue
        deduped.append((pos, btype))
    return deduped


def _classify_pattern(pattern: re.Pattern) -> str:
    source = pattern.pattern[:40].lower()
    if "separator" in source or "[-=*_]" in source:
        return "separator"
    if "page" in source or "\\f" in source:
        return "page_break"
    if "from|to|cc|bcc" in source or "subject|date" in source:
        return "email_header"
    if "chat|conversation" in source:
        return "chat_start"
    return "ticket_id"


def _split_at_boundaries(text: str, boundaries: list[tuple[int, str]]) -> list[tuple[str, str]]:
    if not boundaries:
        return [(text, "single")]

    segments: list[tuple[str, str]] = []
    prev_pos = 0
    prev_type = "start"

    for pos, btype in boundaries:
        if pos <= 0:
            prev_type = btype
            continue
        chunk = text[prev_pos:pos].strip()
        if chunk:
            segments.append((chunk, prev_type))
        prev_pos = pos
        prev_type = btype

    tail = text[prev_pos:].strip()
    if tail:
        segments.append((tail, prev_type))

    return segments


# ── Stage 3: AI-assisted segmentation ─────────────────────────────────────


def _ai_assisted_segmentation(text: str) -> list[tuple[str, str]] | None:
    try:
        from app.config import ACTIVE_MODEL
        from app.extraction import _get_client
        client = _get_client()
    except Exception as exc:
        logger.debug("AI segmentation unavailable: %s", exc)
        return None

    system_prompt = (
        "You are a document segmentation engine. Your job is to split a block of text "
        "containing multiple customer support tickets into individual tickets.\n\n"
        "Rules:\n"
        "- Return a JSON array of strings, each string being one complete ticket.\n"
        "- Detect semantic boundaries: new customer, new greeting, new issue, "
        "new email chain, new chat conversation.\n"
        "- Do NOT split mid-sentence or mid-paragraph.\n"
        "- If the text appears to be a single ticket, return it as a single-element array.\n"
        "- Preserve the original text exactly; do not modify or summarize it.\n"
        "- Minimum segment length is 20 characters."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Split this document into individual tickets:\n\n{text[:8000]}"},
    ]

    try:
        from pydantic import BaseModel

        class AiSegments(BaseModel):
            tickets: list[str]

        result: AiSegments = client.chat.completions.create(
            model=ACTIVE_MODEL,
            response_model=AiSegments,
            messages=messages,
            max_retries=0,
            temperature=0,
        )

        if result.tickets and len(result.tickets) > 1:
            return [(t, "ai") for t in result.tickets]

        return None
    except Exception as exc:
        logger.warning("AI segmentation failed: %s", exc)
        return None


# ── Validation ─────────────────────────────────────────────────────────────


def _validate_segments(segments: list[tuple[str, str]]) -> list[Segment]:
    raw: list[Segment] = []
    for i, (text, btype) in enumerate(segments):
        raw.append(Segment(text=text, index=i, boundary_type=btype))

    merged: list[Segment] = []
    for seg in raw:
        if merged and seg.char_count < MIN_SEGMENT_CHARS and merged[-1].char_count < MAX_SEGMENT_CHARS:
            merged[-1].text += "\n\n" + seg.text
            merged[-1].word_count = len(merged[-1].text.split())
            merged[-1].char_count = len(merged[-1].text)
            merged[-1].boundary_type = f"{merged[-1].boundary_type}+merged"
            merged[-1].validation_message = (
                f"Merged with adjacent segment (was {seg.char_count} chars, "
                f"below min {MIN_SEGMENT_CHARS})"
            )
        else:
            merged.append(seg)

    final: list[Segment] = []
    for seg in merged:
        if seg.char_count > MAX_SEGMENT_CHARS:
            chunks = _split_oversized(seg.text)
            for j, chunk in enumerate(chunks):
                s = Segment(
                    text=chunk,
                    index=len(final),
                    boundary_type=f"{seg.boundary_type}+split",
                    validation_message=(
                        f"Split from oversized segment (was {seg.char_count} chars, "
                        f"max {MAX_SEGMENT_CHARS})"
                    ) if j == 0 else None,
                )
                final.append(s)
        else:
            seg.index = len(final)
            final.append(seg)

    for seg in final:
        if seg.char_count < MIN_SEGMENT_CHARS:
            seg.valid = False
            seg.validation_message = (
                f"Below minimum size ({seg.char_count} < {MIN_SEGMENT_CHARS})"
            )
        if seg.char_count > MAX_SEGMENT_CHARS * 1.5:
            seg.valid = False
            seg.validation_message = (
                f"Exceeds maximum size ({seg.char_count} > {MAX_SEGMENT_CHARS})"
            )

    return final


def _split_oversized(text: str) -> list[str]:
    if not text.strip():
        return [text]
    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > MAX_SEGMENT_CHARS and current:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para) if current else para
    if current.strip():
        chunks.append(current.strip())
    if not chunks:
        chunks = [text[:MAX_SEGMENT_CHARS]]
    return chunks


# ── Fallback ────────────────────────────────────────────────────────────────


def _line_break_fallback(text: str) -> list[Segment]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if not blocks:
        return [Segment(text=text, index=0, boundary_type="single")]

    segments: list[Segment] = []
    for i, block in enumerate(blocks):
        segments.append(Segment(text=block, index=i, boundary_type="line_break"))

    return _validate_segments([(s.text, s.boundary_type) for s in segments])


# ── Main entry point ───────────────────────────────────────────────────────


def segment_document(text: str, use_ai: bool = True) -> SegmentationResult:
    """
    Segment a document into individual tickets.

    Priority:
      1. Structured dataset parser (explicit separators)
         → if found, skip rule-based and AI entirely
      2. Rule-based detection
      3. AI-assisted segmentation (if no rule boundaries found)
      4. Line-break fallback

    Structured separator lines are NEVER included in ticket content.
    """
    text = text.strip()
    if not text:
        return SegmentationResult(segments=[], method="single", warnings=["Empty document"])

    warnings: list[str] = []

    # ── Stage 1: Structured dataset parser ────────────────────────────────
    structured_tickets, sep_count = _extract_structured_tickets(text)

    if structured_tickets and len(structured_tickets) >= 2:
        # Run validation but keep boundary_type as "structured"
        segments = _validate_segments([(t, "structured") for t in structured_tickets])
        logger.info(
            "Structured dataset detected: %d separators -> %d tickets (rule engine skipped: TRUE)",
            sep_count,
            len(segments),
        )
        return SegmentationResult(segments=segments, method="structured", warnings=warnings)

    # ── Stage 2: Rule-based ───────────────────────────────────────────────
    boundaries = _find_boundaries(text)

    if boundaries:
        raw_segments = _split_at_boundaries(text, boundaries)
        segments = _validate_segments(raw_segments)
        logger.info("Rule-based segmentation found %d boundaries -> %d segments", len(boundaries), len(segments))
        return SegmentationResult(segments=segments, method="rule", warnings=warnings)

    # ── Stage 3: AI-assisted ──────────────────────────────────────────────
    if use_ai:
        logger.info("No rule-based boundaries found. Trying AI-assisted segmentation.")
        ai_segments = _ai_assisted_segmentation(text)
        if ai_segments:
            segments = _validate_segments(ai_segments)
            warnings.append("AI-assisted segmentation was used")
            logger.info("AI segmentation produced %d segments", len(segments))
            return SegmentationResult(segments=segments, method="ai", warnings=warnings)

    # ── Stage 4: Fallback ─────────────────────────────────────────────────
    segments = _line_break_fallback(text)
    logger.info("Line-break fallback produced %d segments", len(segments))
    return SegmentationResult(segments=segments, method="line_break", warnings=warnings)
