import pytest

import backend.app.services.pdf_text_extraction_service as pdf_module
from backend.app.services.pdf_text_extraction_service import (
    PDFTextExtractionService,
)


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


def install_fake_reader(monkeypatch, pages, encrypted=False):
    class FakeReader:
        def __init__(self, stream):
            self.pages = pages
            self.is_encrypted = encrypted

    monkeypatch.setattr(pdf_module, "PdfReader", FakeReader)


def test_extract_text_from_multiple_pages(monkeypatch):
    install_fake_reader(
        monkeypatch,
        [
            FakePage("Statement period: March 2026"),
            FakePage("Closing balance: INR 120000"),
        ],
    )

    service = PDFTextExtractionService()
    result = service.extract_text(b"%PDF-1.7\nmock PDF content")

    assert "Statement period: March 2026" in result
    assert "Closing balance: INR 120000" in result


def test_reject_non_pdf():
    service = PDFTextExtractionService()

    with pytest.raises(ValueError, match="DOCUMENT_PDF_INVALID"):
        service.extract_text(b"This is not a PDF document")


def test_reject_encrypted_pdf(monkeypatch):
    install_fake_reader(monkeypatch, [], encrypted=True)

    service = PDFTextExtractionService()

    with pytest.raises(ValueError, match="DOCUMENT_PDF_ENCRYPTED"):
        service.extract_text(b"%PDF-1.7\nmock PDF content")


def test_reject_pdf_without_text_layer(monkeypatch):
    install_fake_reader(
        monkeypatch,
        [FakePage(None), FakePage("   ")],
    )

    service = PDFTextExtractionService()

    with pytest.raises(ValueError, match="DOCUMENT_PDF_NO_TEXT_LAYER"):
        service.extract_text(b"%PDF-1.7\nmock PDF content")


def test_reject_too_many_pages(monkeypatch):
    service = PDFTextExtractionService()

    install_fake_reader(
        monkeypatch,
        [FakePage("Some text") for _ in range(service.MAX_PAGES + 1)],
    )

    with pytest.raises(ValueError, match="DOCUMENT_PDF_TOO_MANY_PAGES"):
        service.extract_text(b"%PDF-1.7\nmock PDF content")


def test_reject_pdf_larger_than_limit():
    service = PDFTextExtractionService()
    oversized_pdf = b"%PDF-" + (
        b"x" * service.MAX_PDF_BYTES
    )

    with pytest.raises(ValueError, match="DOCUMENT_PDF_TOO_LARGE"):
        service.extract_text(oversized_pdf)


def test_reject_extracted_text_larger_than_limit(monkeypatch):
    service = PDFTextExtractionService()

    install_fake_reader(
        monkeypatch,
        [FakePage("A" * (service.MAX_TEXT_CHARS + 1))],
    )

    with pytest.raises(ValueError, match="DOCUMENT_PDF_TEXT_TOO_LONG"):
        service.extract_text(b"%PDF-1.7\nmock PDF content")