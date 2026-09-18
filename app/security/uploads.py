from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, get_settings

PDF_MAGIC = b"%PDF"
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


class UploadRejected(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    content_type: str
    data: bytes


def validate_pdf_upload(
    filename: str | None,
    content_type: str | None,
    data: bytes,
    settings: Settings | None = None,
) -> ValidatedUpload:
    """Reject anything that is not a PDF, empty, or over the size cap (spec 07 SEC-004)."""
    settings = settings or get_settings()
    name = (filename or "").strip()
    if not name:
        raise UploadRejected("INVALID_FILENAME", "A filename is required")
    if not name.lower().endswith(".pdf"):
        raise UploadRejected("UNSUPPORTED_FILE_TYPE", "Only PDF files are accepted", status_code=415)
    if not data:
        raise UploadRejected("EMPTY_FILE", "The uploaded file is empty")
    if len(data) > settings.max_upload_bytes:
        raise UploadRejected(
            "FILE_TOO_LARGE",
            f"File exceeds the {settings.max_upload_bytes} byte limit",
            status_code=413,
        )
    if not data.startswith(PDF_MAGIC):
        raise UploadRejected("UNSUPPORTED_FILE_TYPE", "Only PDF files are accepted", status_code=415)
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared and declared not in ALLOWED_CONTENT_TYPES and declared != "application/octet-stream":
        raise UploadRejected("UNSUPPORTED_FILE_TYPE", "Only PDF files are accepted", status_code=415)
    return ValidatedUpload(filename=name, content_type="application/pdf", data=data)
