"""OCR and document text extraction service."""
from pypdf import PdfReader
import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Tuple, Optional


class OCRService:
    """Extract text from PDFs and images using pypdf and Tesseract."""

    def extract_text(self, file_path: str, file_type: str) -> Tuple[str, Optional[float]]:
        """Extract text and return (text, confidence)."""
        if file_type == "pdf":
            return self._extract_pdf(file_path)
        elif file_type == "image":
            return self._extract_image(file_path)
        elif file_type == "text":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), 1.0
        return "", None

    def _extract_pdf(self, file_path: str) -> Tuple[str, Optional[float]]:
        """Extract text from PDF using pypdf. Falls back to OCR if no native text found."""
        try:
            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text)

            full_text = "\n".join(text_parts)

            # If we got meaningful text, return with high confidence
            if full_text.strip():
                return full_text, 0.95

            # If no text extracted, PDF may be scanned/image-based
            # We attempt OCR on rendered pages if pdf2image is available
            return self._ocr_scanned_pdf(file_path)

        except Exception as e:
            return "", None

    def _ocr_scanned_pdf(self, file_path: str) -> Tuple[str, Optional[float]]:
        """Fallback OCR for scanned PDFs using pdf2image if available."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=300)
            text_parts = []
            confidences = []

            for img in images:
                text, conf = self._ocr_image_pil(img)
                if text:
                    text_parts.append(text)
                if conf is not None:
                    confidences.append(conf)

            full_text = "\n".join(text_parts)
            avg_conf = sum(confidences) / len(confidences) if confidences else None
            return full_text, avg_conf

        except ImportError:
            # pdf2image not installed or poppler missing
            return (
                "[This PDF appears to be image-based (scanned). "
                "Native text extraction found no content. "
                "Install pdf2image and poppler for OCR fallback, "
                "or convert pages to images and upload them directly.]",
                None
            )
        except Exception:
            return "", None

    def _extract_image(self, file_path: str) -> Tuple[str, Optional[float]]:
        """Extract text from image using Tesseract OCR."""
        try:
            # Handle Windows paths with spaces or non-ASCII characters
            img_array = np.fromfile(file_path, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None:
                img = cv2.imread(file_path)
        except Exception:
            img = cv2.imread(file_path)

        if img is None:
            return "[Error: Could not load image file]", None

        # Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Convert to PIL for Tesseract
        pil_img = Image.fromarray(denoised)
        return self._ocr_image_pil(pil_img)

    def _ocr_image_pil(self, pil_img: Image.Image) -> Tuple[str, Optional[float]]:
        """Run Tesseract OCR on a PIL Image."""
        # Tesseract with Hindi + English
        custom_config = r"--oem 3 --psm 6 -l eng+hin"
        try:
            text = pytesseract.image_to_string(pil_img, config=custom_config)

            # Get confidence data
            data = pytesseract.image_to_data(pil_img, config=custom_config, output_type=pytesseract.Output.DICT)
            confidences = []
            for confidence in data.get("conf", []):
                try:
                    value = float(confidence)
                except (TypeError, ValueError):
                    continue
                if value >= 0:
                    confidences.append(value)
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else None

            return text.strip(), avg_conf
        except Exception as e:
            # Fallback if Tesseract binary is missing or language pack unavailable
            return (
                f"[Tesseract OCR unavailable or encountered error: {str(e)}. "
                "Please verify Tesseract installation and PATH configuration.]",
                None
            )
