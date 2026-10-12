from io import BytesIO

from pypdf import PdfReader


class PDFTextExtractionService:
    MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_PAGES = 50
    MAX_TEXT_CHARS = 10_000
    MIN_TEXT_CHARS = 20

    def extract_text(self, pdf_bytes: bytes) -> str:
        if not isinstance(pdf_bytes, bytes) or not pdf_bytes:
            raise ValueError("DOCUMENT_PDF_EMPTY")

        if len(pdf_bytes) > self.MAX_PDF_BYTES:
            raise ValueError("DOCUMENT_PDF_TOO_LARGE")

        # Permit minor leading bytes, but require the PDF signature near
        # the start of the uploaded file.
        if b"%PDF-" not in pdf_bytes[:1024]:
            raise ValueError("DOCUMENT_PDF_INVALID")

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
        except Exception as exc:
            raise ValueError("DOCUMENT_PDF_INVALID") from exc

        try:
            if reader.is_encrypted:
                raise ValueError("DOCUMENT_PDF_ENCRYPTED")

            pages = reader.pages
            page_count = len(pages)

        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("DOCUMENT_PDF_INVALID") from exc

        if page_count == 0:
            raise ValueError("DOCUMENT_PDF_NO_PAGES")

        if page_count > self.MAX_PAGES:
            raise ValueError("DOCUMENT_PDF_TOO_MANY_PAGES")

        extracted_pages = []

        try:
            for page in pages:
                page_text = page.extract_text()

                if page_text and page_text.strip():
                    extracted_pages.append(page_text.strip())

        except Exception as exc:
            raise ValueError(
                "DOCUMENT_PDF_TEXT_EXTRACTION_FAILED"
            ) from exc

        source_text = "\n\n".join(extracted_pages).strip()

        if not source_text:
            raise ValueError("DOCUMENT_PDF_NO_TEXT_LAYER")

        if len(source_text) < self.MIN_TEXT_CHARS:
            raise ValueError("DOCUMENT_PDF_TEXT_TOO_SHORT")

        # Do not silently truncate a document: doing so could omit evidence.
        if len(source_text) > self.MAX_TEXT_CHARS:
            raise ValueError("DOCUMENT_PDF_TEXT_TOO_LONG")

        return source_text


pdf_text_extraction_service = PDFTextExtractionService()