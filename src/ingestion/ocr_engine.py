"""
OCR Engine Module (Owner: Member P1)
Extracts text from scanned ephemera, simulated historical records, and degraded PDFs using OCR.
Includes image preprocessing (binarization, contrast enhancement, noise reduction) and auto-detection.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Common Tesseract binary locations on Windows and Unix systems
COMMON_TESSERACT_PATHS = [
    os.getenv("TESSERACT_CMD", ""),
    os.getenv("TESSERACT_PATH", ""),
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]

_TESSERACT_CHECKED = False
_TESSERACT_AVAILABLE = False


def find_tesseract_binary() -> Optional[str]:
    """
    Locates the Tesseract OCR executable on the system PATH or standard locations.
    """
    which_cmd = shutil.which("tesseract")
    if which_cmd and os.path.isfile(which_cmd):
        return which_cmd

    for candidate in COMMON_TESSERACT_PATHS:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


def init_tesseract() -> bool:
    """
    Initializes pytesseract with the discovered binary path.
    Returns True if Tesseract is available, False otherwise.
    """
    global _TESSERACT_CHECKED, _TESSERACT_AVAILABLE
    if _TESSERACT_CHECKED:
        return _TESSERACT_AVAILABLE

    cmd = find_tesseract_binary()
    if cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = cmd
            _TESSERACT_AVAILABLE = True
        except ImportError:
            _TESSERACT_AVAILABLE = False
    else:
        _TESSERACT_AVAILABLE = False

    _TESSERACT_CHECKED = True
    if not _TESSERACT_AVAILABLE:
        logger.debug("Tesseract OCR executable not detected; falling back to embedded text extraction.")
    return _TESSERACT_AVAILABLE


def preprocess_image_for_ocr(
    image_input: Union[Path, str, Image.Image],
    contrast_factor: float = 1.8,
    upscale_min_width: int = 1000,
    binarize_threshold: int = 140
) -> Image.Image:
    """
    Applies image preprocessing pipeline tailored for degraded simulated historical scans:
    1. RGB/RGBA to Grayscale conversion
    2. Optional resolution upscaling for low-DPI scans
    3. Contrast stretching/enhancement
    4. Unsharp masking / sharpening
    5. Adaptive/fixed binarization (thresholding) to eliminate background noise/parchment tint
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(str(image_input))
    else:
        img = image_input.copy()

    # 1. Grayscale
    if img.mode != "L":
        img = img.convert("L")

    # 2. Upscale if too small
    width, height = img.size
    if width < upscale_min_width:
        scale = upscale_min_width / max(width, 1)
        new_size = (int(width * scale), int(height * scale))
        img = img.resize(new_size, resample=Image.Resampling.BILINEAR)

    # 3. Contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast_factor)

    # 4. Sharpening filter
    img = img.filter(ImageFilter.SHARPEN)

    # 5. Thresholding / Binarization
    table = [0 if i < binarize_threshold else 255 for i in range(256)]
    img = img.point(table, "1")

    return img


def run_ocr_on_image(
    image_input: Union[Path, str, Image.Image],
    preprocess: bool = True,
    psm: int = 3
) -> str:
    """
    Executes Tesseract OCR on a preprocessed image with robust fallback.
    """
    is_avail = init_tesseract()
    if not is_avail:
        return ""

    try:
        import pytesseract

        if preprocess:
            processed_img = preprocess_image_for_ocr(image_input)
        else:
            if isinstance(image_input, (str, Path)):
                processed_img = Image.open(str(image_input))
            else:
                processed_img = image_input

        custom_config = f"--oem 3 --psm {psm}"
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        return text.strip()
    except Exception as e:
        logger.warning(f"Error during OCR execution: {e}")
        return ""


def is_scanned_page(page, min_char_count: int = 40) -> bool:
    """
    Heuristic to determine whether a PDF page is a scanned document / image with no native text layer.
    """
    try:
        text = page.get_text("text").strip()
        if len(text) >= min_char_count:
            return False
        images = page.get_images()
        return len(images) > 0 or len(text) == 0
    except Exception:
        return False


def process_scanned_pdf(pdf_path: Path, dpi: int = 150) -> List[Dict[str, Any]]:
    """
    Renders scanned PDF pages to raster images and executes OCR extraction per page.
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            logger.error("PyMuPDF is required for process_scanned_pdf.")
            return []

    results = []
    try:
        doc = fitz.open(str(pdf_path))
        is_avail = init_tesseract()

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1

            if is_avail:
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = run_ocr_on_image(img, preprocess=True)
                if not ocr_text.strip():
                    ocr_text = page.get_text("text").strip()
                is_ocr = True
            else:
                ocr_text = page.get_text("text").strip()
                is_ocr = False

            results.append({
                "page_number": page_num,
                "text": ocr_text,
                "is_ocr": is_ocr
            })
        doc.close()
    except Exception as e:
        logger.error(f"Failed to process scanned PDF {pdf_path}: {e}")

    return results
