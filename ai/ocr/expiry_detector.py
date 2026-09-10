from __future__ import annotations

import os
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


# ============================================================
# TESSERACT
# ============================================================

def configure_tesseract() -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "pytesseract is not installed. "
            "Run: pip install pytesseract"
        ) from exc

    env_path = os.getenv("TESSERACT_CMD")

    if env_path and Path(env_path).exists():
        pytesseract.pytesseract.tesseract_cmd = env_path
        return env_path

    path_executable = shutil.which("tesseract")

    if path_executable:
        pytesseract.pytesseract.tesseract_cmd = path_executable
        return path_executable

    common_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for executable in common_paths:
        if executable.exists():
            pytesseract.pytesseract.tesseract_cmd = str(executable)
            return str(executable)

    raise RuntimeError(
        "Tesseract executable could not be found."
    )


# ============================================================
# MONTHS
# ============================================================

MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


# ============================================================
# DATE HELPERS
# ============================================================

def normalize_year(year: int) -> int:
    if year < 100:
        return 2000 + year if year <= 69 else 1900 + year

    return year


def build_result(
    parsed_date: date,
    raw_match: str,
) -> dict[str, Any]:

    today = date.today()

    if parsed_date < today:
        status = "EXPIRED"
    elif parsed_date == today:
        status = "EXPIRES_TODAY"
    else:
        status = "VALID"

    return {
        "found": True,
        "expiry_date": parsed_date.isoformat(),
        "raw_match": raw_match,
        "status": status,
        "days_remaining": (
            parsed_date - today
        ).days,
    }


# ============================================================
# OCR DATE PARSER
# ============================================================

def extract_expiry_date(
    text: str,
) -> dict[str, Any]:

    if not text:
        return {
            "found": False,
            "expiry_date": None,
            "raw_match": None,
            "status": "NOT_FOUND",
        }

    text = text.upper()

    # Remove OCR formatting noise.
    cleaned = (
        text
        .replace("\n", " ")
        .replace("\r", " ")
    )

    # --------------------------------------------------------
    # DDMMMYY / DDMMMYYYY
    #
    # Example:
    # 23FEB27
    # --------------------------------------------------------

    compact_pattern = (
        r"\b"
        r"(\d{1,2})"
        r"\s*"
        r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|"
        r"OCT|NOV|DEC)"
        r"\s*"
        r"(\d{2,4})"
        r"\b"
    )

    for match in re.finditer(
        compact_pattern,
        cleaned,
    ):

        day = int(match.group(1))
        month = MONTHS[match.group(2)]
        year = normalize_year(
            int(match.group(3))
        )

        try:
            parsed = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        return build_result(
            parsed,
            match.group(0),
        )

    # --------------------------------------------------------
    # DD/MM/YYYY
    # DD-MM-YYYY
    # --------------------------------------------------------

    numeric_pattern = (
        r"\b"
        r"(\d{1,2})"
        r"[/-]"
        r"(\d{1,2})"
        r"[/-]"
        r"(\d{2,4})"
        r"\b"
    )

    for match in re.finditer(
        numeric_pattern,
        cleaned,
    ):

        day = int(match.group(1))
        month = int(match.group(2))
        year = normalize_year(
            int(match.group(3))
        )

        try:
            parsed = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        return build_result(
            parsed,
            match.group(0),
        )

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    iso_pattern = (
        r"\b"
        r"(\d{4})"
        r"[/-]"
        r"(\d{1,2})"
        r"[/-]"
        r"(\d{1,2})"
        r"\b"
    )

    for match in re.finditer(
        iso_pattern,
        cleaned,
    ):

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:
            parsed = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        return build_result(
            parsed,
            match.group(0),
        )

    return {
        "found": False,
        "expiry_date": None,
        "raw_match": None,
        "status": "NOT_FOUND",
    }


# ============================================================
# OCR TEXT CLEANUP
# ============================================================

def _compact_ocr_text(
    text: str,
    max_chars: int = 1500,
) -> str:

    lines = []

    for line in text.splitlines():

        cleaned = " ".join(
            line.strip().split()
        )

        if not cleaned:
            continue

        lines.append(cleaned)

    result = "\n".join(lines)

    if len(result) > max_chars:
        result = result[:max_chars] + "..."

    return result


# ============================================================
# IMAGE VARIANTS
# ============================================================

def _make_variants(
    image: np.ndarray,
) -> list[np.ndarray]:

    height, width = image.shape[:2]

    variants: list[np.ndarray] = []

    # --------------------------------------------------------
    # Original
    # --------------------------------------------------------

    variants.append(image)

    # --------------------------------------------------------
    # Detect large bright panel
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    _, bright = cv2.threshold(
        gray,
        175,
        255,
        cv2.THRESH_BINARY,
    )

    contours, _ = cv2.findContours(
        bright,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    panel = None
    best_area = 0

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if (
            area > best_area
            and w > width * 0.25
            and h > height * 0.20
        ):
            best_area = area
            panel = image[
                y:y + h,
                x:x + w
            ]

    if panel is not None:
        variants.append(panel)

        ph, pw = panel.shape[:2]

        # Lower-left part of panel where
        # MRP / PKD / BATCH / USE BY are normally printed.
        date_area = panel[
            int(ph * 0.45):ph,
            0:int(pw * 0.85)
        ]

        variants.append(date_area)

        # Focus even more strongly on bottom rows.
        date_area_2 = panel[
            int(ph * 0.60):ph,
            0:int(pw * 0.75)
        ]

        variants.append(date_area_2)

    return variants


# ============================================================
# PREPROCESSING
# ============================================================

def _preprocess(
    image: np.ndarray,
    threshold: int | None = None,
) -> np.ndarray:

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # Enlarge dot-matrix characters.
    gray = cv2.resize(
        gray,
        None,
        fx=5,
        fy=5,
        interpolation=cv2.INTER_CUBIC,
    )

    # Local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(gray)

    # Mild blur to reduce camera noise.
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # Sharpen.
    kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )

    gray = cv2.filter2D(
        gray,
        -1,
        kernel,
    )

    if threshold is not None:

        _, processed = cv2.threshold(
            gray,
            threshold,
            255,
            cv2.THRESH_BINARY,
        )

        return processed

    return gray


# ============================================================
# TARGETED OCR
# ============================================================

def _ocr_candidate(
    image: np.ndarray,
) -> str:

    import pytesseract

    best_text = ""

    configurations = [
        "--psm 6",
        "--psm 11",
        "--psm 13",
    ]

    thresholds = [
        None,
        140,
        160,
        180,
        200,
    ]

    for threshold in thresholds:

        processed = _preprocess(
            image,
            threshold,
        )

        for config in configurations:

            try:

                text = pytesseract.image_to_string(
                    processed,
                    lang="eng",
                    config=(
                        config
                        + " -c "
                        "tessedit_char_whitelist="
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        "abcdefghijklmnopqrstuvwxyz"
                        "0123456789:/-"
                    ),
                )

            except Exception:
                continue

            compact = _compact_ocr_text(
                text,
                max_chars=1500,
            )

            if len(compact) > len(best_text):
                best_text = compact

            # Stop immediately if a date is recognized.
            parsed = extract_expiry_date(
                text
            )

            if parsed["found"]:
                return text

    return best_text


# ============================================================
# IMAGE -> TEXT
# ============================================================

def extract_text_from_image(
    image_path: str | Path,
) -> str:

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    configure_tesseract()

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise RuntimeError(
            "Could not read image."
        )

    variants = _make_variants(
        image
    )

    best_text = ""

    for variant in variants:

        text = _ocr_candidate(
            variant
        )

        if len(text) > len(best_text):
            best_text = text

        parsed = extract_expiry_date(
            text
        )

        if parsed["found"]:
            return text

    return _compact_ocr_text(
        best_text
    )


# ============================================================
# COMPLETE EXPIRY DETECTION
# ============================================================

def detect_expiry(
    image_path: str | Path,
) -> dict[str, Any]:

    # Try targeted OCR.
    ocr_text = extract_text_from_image(
        image_path
    )

    result = extract_expiry_date(
        ocr_text
    )

    if result["found"]:
        result["ocr_text"] = ocr_text
        return result

    return {
        "found": False,
        "expiry_date": None,
        "raw_match": None,
        "status": "NOT_FOUND",
        "ocr_text": ocr_text,
    }


# ============================================================
# PUBLIC SAFE BITE INTERFACE
# ============================================================

def analyze_expiry(
    image_path: str | Path,
) -> dict[str, Any]:

    try:

        result = detect_expiry(
            image_path
        )

        # Keep API responses compact.
        result["ocr_text"] = _compact_ocr_text(
            result.get(
                "ocr_text",
                ""
            ),
            max_chars=1500,
        )

        return result

    except FileNotFoundError as exc:

        return {
            "found": False,
            "expiry_date": None,
            "raw_match": None,
            "status": "IMAGE_NOT_FOUND",
            "ocr_text": "",
            "error": str(exc),
        }

    except Exception as exc:

        return {
            "found": False,
            "expiry_date": None,
            "raw_match": None,
            "status": "OCR_ERROR",
            "ocr_text": "",
            "error": str(exc),
        }


# ============================================================
# TESSERACT PATH
# ============================================================

def get_tesseract_path() -> str | None:

    try:
        return configure_tesseract()

    except Exception:
        return None