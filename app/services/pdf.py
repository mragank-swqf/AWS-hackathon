"""Build and read simple text-layer PDFs. Used by ingest, tests, and demo seed."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

MIN_PAGE_CHARS = 40


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    unreadable: bool


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_text_pdf(pages: list[str]) -> bytes:
    """Write a valid PDF 1.4 file with a Helvetica text layer on each page."""
    if not pages:
        raise ValueError("At least one page is required")

    bodies: list[bytes] = []

    def add(body: bytes) -> int:
        bodies.append(body)
        return len(bodies)

    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    content_ids: list[int] = []
    for text in pages:
        lines = (text or "").split("\n")[:55]
        commands = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
        for line in lines:
            commands.append(f"({_escape_pdf_text(line[:110])}) Tj T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        content_ids.append(
            add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        )

    pages_id = add(b"%placeholder%")
    page_ids: list[int] = []
    for content_id in content_ids:
        page_ids.append(
            add(
                
                    b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] "
                    b"/Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>"
                    % (pages_id, content_id, font_id)
                
            )
        )
    kids = b" ".join(b"%d 0 R" % pid for pid in page_ids)
    bodies[pages_id - 1] = b"<< /Type /Pages /Count %d /Kids [%s] >>" % (len(page_ids), kids)
    catalog_id = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)

    # Assemble with xref. Object numbers are 1-based in bodies order.
    # Put catalog first in the file by emitting in object-number order.
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for number, body in enumerate(bodies, start=1):
        offsets.append(sum(len(part) for part in chunks))
        chunks.append(b"%d 0 obj\n%s\nendobj\n" % (number, body))
    xref_pos = sum(len(part) for part in chunks)
    xref = [b"xref\n0 %d\n" % (len(bodies) + 1), b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(b"%010d 00000 n \n" % offset)
    trailer = (
        b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(bodies) + 1, catalog_id, xref_pos)
    )
    return b"".join(chunks + xref + [trailer])


def extract_pages(data: bytes) -> list[ExtractedPage]:
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise ValueError("The PDF could not be opened") from exc
    if not reader.pages:
        raise ValueError("The PDF has no pages")
    extracted: list[ExtractedPage] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        cleaned = text.strip()
        extracted.append(
            ExtractedPage(
                page_number=index,
                text=cleaned,
                unreadable=len(cleaned) < MIN_PAGE_CHARS,
            )
        )
    return extracted
