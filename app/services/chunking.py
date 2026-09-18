"""Cut extracted pages into clause-sized chunks (spec 10)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.enums import ExtractionMethod
from app.services.pdf import ExtractedPage

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - tokenizer missing should not block ingest
    _ENCODING = None

TARGET_TOKENS = 800
MAX_TOKENS = 1200
MIN_TOKENS = 100
OVERLAP_TOKENS = 100

CLAUSE_START = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+){0,5}(?:\s+|$)"
    r"|\([a-zivx]+\)\s+"
    r"|(?:Para|Paragraph|Clause|Section|Annexure|Schedule)\b"
    r")",
    re.IGNORECASE,
)
ALL_CAPS = re.compile(r"^[A-Z][A-Z0-9 ,.'()\-]{8,}$")
TABLE_LINE = re.compile(r"\t| \s*\|\s* ")


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    text: str
    page_start: int
    page_end: int
    section_title: str | None
    clause_number: str | None
    extraction_method: str


def count_tokens(text: str) -> int:
    if _ENCODING is None:
        return max(1, len(text.split()))
    return len(_ENCODING.encode(text))


def _clause_number(line: str) -> str | None:
    match = re.match(r"^(\d+(?:\.\d+){0,5})", line.strip())
    if match:
        return match.group(1)
    return None


def _is_section_break(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(CLAUSE_START.match(stripped) or ALL_CAPS.match(stripped))


def _split_oversized(text: str, page_start: int, page_end: int, section: str | None, clause: str | None) -> list[dict]:
    tokens = text.split()
    if count_tokens(text) <= MAX_TOKENS:
        return [
            {
                "text": text,
                "page_start": page_start,
                "page_end": page_end,
                "section_title": section,
                "clause_number": clause,
                "extraction_method": ExtractionMethod.TEXT.value,
            }
        ]
    pieces: list[dict] = []
    # Word-level packing with overlap. Never drop page range to hit a size target.
    words = tokens
    start = 0
    while start < len(words):
        end = start
        packed: list[str] = []
        while end < len(words) and count_tokens(" ".join(packed + [words[end]])) <= TARGET_TOKENS:
            packed.append(words[end])
            end += 1
        if not packed:
            packed = [words[end]]
            end += 1
        pieces.append(
            {
                "text": " ".join(packed),
                "page_start": page_start,
                "page_end": page_end,
                "section_title": section,
                "clause_number": clause,
                "extraction_method": ExtractionMethod.TEXT.value,
            }
        )
        if end >= len(words):
            break
        overlap = packed[-OVERLAP_TOKENS:] if len(packed) > OVERLAP_TOKENS else packed
        start = end - len(overlap)
    return pieces


def chunk_pages(pages: list[ExtractedPage]) -> list[ChunkDraft]:
    drafts: list[dict] = []
    current_lines: list[str] = []
    current_start: int | None = None
    current_end: int | None = None
    section_title: str | None = None
    clause_number: str | None = None

    def flush() -> None:
        nonlocal current_lines, current_start, current_end, clause_number
        if not current_lines or current_start is None or current_end is None:
            current_lines = []
            return
        text = "\n".join(current_lines).strip()
        if not text:
            current_lines = []
            return
        if drafts and count_tokens(text) < MIN_TOKENS:
            drafts[-1]["text"] = drafts[-1]["text"] + "\n" + text
            drafts[-1]["page_end"] = max(drafts[-1]["page_end"], current_end)
        else:
            drafts.extend(_split_oversized(text, current_start, current_end, section_title, clause_number))
        current_lines = []

    for page in pages:
        if page.unreadable:
            flush()
            drafts.append(
                {
                    "text": f"[Page {page.page_number} could not be read. No text layer.]",
                    "page_start": page.page_number,
                    "page_end": page.page_number,
                    "section_title": None,
                    "clause_number": None,
                    "extraction_method": ExtractionMethod.UNREADABLE.value,
                }
            )
            continue
        for line in page.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if ALL_CAPS.match(stripped) and not TABLE_LINE.search(stripped):
                section_title = stripped.title()
            if current_lines and _is_section_break(stripped) and not TABLE_LINE.search(stripped):
                flush()
                current_start = page.page_number
                current_end = page.page_number
                clause_number = _clause_number(stripped) or clause_number
                current_lines = [stripped]
                continue
            if current_start is None:
                current_start = page.page_number
            current_end = page.page_number
            if _clause_number(stripped):
                clause_number = _clause_number(stripped)
            current_lines.append(stripped)
        # Keep a clause that crosses a page break in the same chunk.
    flush()

    return [
        ChunkDraft(
            chunk_index=index,
            text=item["text"],
            page_start=item["page_start"],
            page_end=item["page_end"],
            section_title=item["section_title"],
            clause_number=item["clause_number"],
            extraction_method=item["extraction_method"],
        )
        for index, item in enumerate(drafts)
    ]
