import os
from io import BytesIO
import pymupdf
import pytesseract
from PIL import Image
from pypdf import PdfReader


class PDFTextExtractionService:
    MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_PAGES = 50
    MAX_TEXT_CHARS = 10_000
    MIN_TEXT_CHARS = 20

    OCR_ENABLED_ENV = "PDF_OCR_ENABLED"
    TESSERACT_CMD_ENV = "TESSERACT_CMD"

    DEFAULT_TESSERACT_CMD = r"D:\AI_Tools\Tesseract\tesseract.exe"

    OCR_TIMEOUT_SECONDS = 15
    OCR_MAX_RENDER_DIMENSION = 2500
    OCR_MAX_RENDER_SCALE = 2.0
    OCR_MIN_RENDER_SCALE = 0.5

    @staticmethod
    def _ocr_enabled() -> bool:
        return os.getenv("PDF_OCR_ENABLED", "false").strip().lower() in {
            "1", "true", "yes", "on"
        }

    def _ocr_page(self, pdf_bytes: bytes, page_index: int) -> str:
        """Render and OCR one page, with bounded rendering and execution."""
        tesseract_cmd = os.getenv(
            self.TESSERACT_CMD_ENV,
            self.DEFAULT_TESSERACT_CMD,
        )

        if not os.path.isfile(tesseract_cmd):
            raise ValueError("DOCUMENT_PDF_OCR_ENGINE_UNAVAILABLE")

        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        try:
            with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
                page = pdf.load_page(page_index)
                rect = page.rect

                largest_dimension = max(rect.width, rect.height)
                if largest_dimension <= 0:
                    raise ValueError("DOCUMENT_PDF_OCR_RENDER_FAILED")

                scale = min(
                    self.OCR_MAX_RENDER_SCALE,
                    self.OCR_MAX_RENDER_DIMENSION / largest_dimension,
                )

                if scale < self.OCR_MIN_RENDER_SCALE:
                    raise ValueError("DOCUMENT_PDF_OCR_PAGE_DIMENSIONS_TOO_LARGE")

                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(scale, scale),
                    colorspace=pymupdf.csRGB,
                    alpha=False,
                )

                image = Image.frombytes(
                    "RGB",
                    (pixmap.width, pixmap.height),
                    pixmap.samples,
                )

                try:
                    return pytesseract.image_to_string(
                        image,
                        lang="eng",
                        timeout=self.OCR_TIMEOUT_SECONDS,
                    ).strip()
                except pytesseract.TesseractNotFoundError as exc:
                    raise ValueError(
                        "DOCUMENT_PDF_OCR_ENGINE_UNAVAILABLE"
                    ) from exc
                except RuntimeError as exc:
                    raise ValueError("DOCUMENT_PDF_OCR_TIMEOUT") from exc
                except Exception as exc:
                    raise ValueError("DOCUMENT_PDF_OCR_FAILED") from exc

        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("DOCUMENT_PDF_OCR_RENDER_FAILED") from exc

    def extract_text(self, pdf_bytes: bytes) -> str:
        if not isinstance(pdf_bytes, bytes) or not pdf_bytes:
            raise ValueError("DOCUMENT_PDF_EMPTY")

        if len(pdf_bytes) > self.MAX_PDF_BYTES:
            raise ValueError("DOCUMENT_PDF_TOO_LARGE")

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

        page_texts = []
        missing_page_indexes = []

        try:
            for page_index, page in enumerate(pages):
                text = page.extract_text()

                if text and text.strip():
                    page_texts.append(text.strip())
                else:
                    page_texts.append(None)
                    missing_page_indexes.append(page_index)

        except Exception as exc:
            raise ValueError(
                "DOCUMENT_PDF_TEXT_EXTRACTION_FAILED"
            ) from exc

        if missing_page_indexes:
            if not self._ocr_enabled():
                if all(text is None for text in page_texts):
                    raise ValueError("DOCUMENT_PDF_NO_TEXT_LAYER")
                raise ValueError("DOCUMENT_PDF_OCR_DISABLED")

            for page_index in missing_page_indexes:
                text = self._ocr_page(pdf_bytes, page_index)

                if not text or not text.strip():
                    raise ValueError("DOCUMENT_PDF_OCR_NO_TEXT")

                page_texts[page_index] = text.strip()

        source_text = "\n\n".join(
            text for text in page_texts if text is not None
        ).strip()

        if not source_text:
            raise ValueError("DOCUMENT_PDF_NO_TEXT_LAYER")

        if len(source_text) < self.MIN_TEXT_CHARS:
            raise ValueError("DOCUMENT_PDF_TEXT_TOO_SHORT")

        if len(source_text) > self.MAX_TEXT_CHARS:
            raise ValueError("DOCUMENT_PDF_TEXT_TOO_LONG")

        return source_text

pdf_text_extraction_service = PDFTextExtractionService()