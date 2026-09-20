import pytest
from app.config import get_settings
from app.security.uploads import UploadRejected, validate_pdf_upload

PDF = b"%PDF-1.4 minimal"


def test_non_pdf_extension_is_rejected():
    with pytest.raises(UploadRejected) as exc:
        validate_pdf_upload("notes.txt", "text/plain", b"hello")
    assert exc.value.status_code == 415


def test_non_pdf_magic_is_rejected():
    with pytest.raises(UploadRejected) as exc:
        validate_pdf_upload("file.pdf", "application/pdf", b"not-a-pdf")
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"


def test_empty_file_is_rejected():
    with pytest.raises(UploadRejected):
        validate_pdf_upload("file.pdf", "application/pdf", b"")


def test_oversized_file_is_rejected(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "8")
    get_settings.cache_clear()
    with pytest.raises(UploadRejected) as exc:
        validate_pdf_upload("file.pdf", "application/pdf", b"%PDF-12345")
    assert exc.value.status_code == 413
    get_settings.cache_clear()


def test_pdf_is_accepted():
    result = validate_pdf_upload("circular.pdf", "application/pdf", PDF)
    assert result.filename == "circular.pdf"
