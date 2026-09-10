from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from ai.hygiene.hygiene_detector import analyze_hygiene
from ai.ocr.expiry_detector import analyze_expiry

from ..database import get_db
from ..models import (
    AIDetection,
    GovernmentOfficer,
    Investigation,
)
from ..security import get_token_payload
from ..services.blockchain_service import (
    blockchain_status,
    create_audit_record,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# ============================================================
# DIRECTORIES
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

AI_UPLOAD_DIR = (
    PROJECT_ROOT
    / "backend"
    / "uploads"
    / "ai"
)

AI_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(payload["sub"])

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
        )

    officer = (
        db.query(GovernmentOfficer)
        .filter(
            GovernmentOfficer.id
            == officer_id
        )
        .first()
    )

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Officer not found",
        )

    if officer.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=401,
            detail="Officer account is inactive",
        )

    return officer


# ============================================================
# SAVE TEMPORARY IMAGE
# ============================================================

def _save_upload(
    file: UploadFile,
) -> Path:

    original_name = (
        file.filename
        or "inspection_image"
    )

    extension = (
        Path(original_name)
        .suffix
        .lower()
    )

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image type. "
                "Allowed: jpg, jpeg, png, webp, bmp"
            ),
        )

    destination = (
        AI_UPLOAD_DIR
        / f"{uuid.uuid4().hex}{extension}"
    )

    try:
        content = file.file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty",
            )

        destination.write_bytes(
            content
        )

    except HTTPException:
        raise

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not store image: {exc}"
            ),
        )

    return destination


# ============================================================
# INVESTIGATION LOOKUP
# ============================================================

def _get_investigation(
    db: Session,
    investigation_id: int | None,
):
    if investigation_id is None:
        return None

    return (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )


# ============================================================
# AI STATUS
# ============================================================

@router.get("/status")
def ai_status(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
):
    return {
        "enabled": True,

        "services": {
            "expiry_ocr": True,
            "hygiene_detection": True,
        },

        "blockchain":
            blockchain_status(),

        "message": (
            "AI API available. "
            "Expiry OCR requires OCR engine support. "
            "Hygiene detection requires trained model weights."
        ),
    }


# ============================================================
# EXPIRY OCR
# ============================================================

@router.post("/expiry")
def expiry_analysis(
    file: UploadFile = File(...),
    investigation_id: int | None = None,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    image_path = _save_upload(file)

    try:
        result = analyze_expiry(
            image_path
        )

        investigation = _get_investigation(
            db,
            investigation_id,
        )

        restaurant_id = None

        if investigation:
            restaurant_id = (
                investigation.alert.restaurant_id
            )

        # Store expiry analysis for the outlet.
        if (
            result.get("success") is True
            and restaurant_id is not None
        ):
            expiry_detection = AIDetection(
                detection_type="expiry_analysis",
                confidence=float(
                    result.get(
                        "confidence",
                        0,
                    )
                ),
                description=str(result),
                image_path=None,
                restaurant_id=restaurant_id,
                device_id=None,
            )

            db.add(
                expiry_detection
            )

            db.flush()

        # Create audit only for successful AI analysis.
        audit = None

        if (
            investigation_id is not None
            and result.get("success") is True
        ):
            audit = create_audit_record(
                db=db,
                record_type="AI_EXPIRY_ANALYSIS",
                entity_type="INVESTIGATION",
                entity_id=investigation_id,
                actor_id=officer.id,
                payload={
                    "filename":
                        file.filename,
                    "result":
                        result,
                },
            )

            db.commit()
            db.refresh(audit)

        return {
            "service":
                "expiry_ocr",

            "investigation_id":
                investigation_id,

            "result":
                result,

            "audit": (
                {
                    "id":
                        audit.id,

                    "record_hash":
                        audit.record_hash,

                    "blockchain_tx_id":
                        audit.blockchain_tx_id,

                    "verification_status":
                        audit.verification_status,
                }
                if audit
                else None
            ),
        }

    finally:
        image_path.unlink(
            missing_ok=True
        )


# ============================================================
# HYGIENE AI
# ============================================================

@router.post("/hygiene")
def hygiene_analysis(
    file: UploadFile = File(...),
    investigation_id: int | None = None,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    image_path = _save_upload(file)

    try:
        result = analyze_hygiene(
            image_path
        )

        investigation = _get_investigation(
            db,
            investigation_id,
        )

        restaurant_id = None

        if investigation:
            restaurant_id = (
                investigation.alert.restaurant_id
            )

        stored_findings = []

        # ----------------------------------------------------
        # Persist YOLO findings
        # ----------------------------------------------------

        if (
            result.get("success") is True
            and restaurant_id is not None
        ):

            for detection in result.get(
                "detections",
                [],
            ):

                label = str(
                    detection.get(
                        "label",
                        "unknown",
                    )
                )

                confidence = float(
                    detection.get(
                        "confidence",
                        0,
                    )
                )

                class_id = detection.get(
                    "class_id"
                )

                bbox = detection.get(
                    "bbox"
                )

                description = (
                    "SafeBite local YOLO "
                    "hygiene detection."
                )

                if class_id is not None:
                    description += (
                        f" Class ID: {class_id}."
                    )

                if bbox is not None:
                    description += (
                        f" Bounding box: {bbox}."
                    )

                ai_detection = AIDetection(
                    detection_type=label,
                    confidence=confidence,
                    description=description,
                    image_path=None,
                    restaurant_id=restaurant_id,
                    device_id=None,
                )

                db.add(
                    ai_detection
                )

                stored_findings.append(
                    {
                        "label":
                            label,
                        "confidence":
                            confidence,
                    }
                )

            db.flush()

        # ----------------------------------------------------
        # Blockchain-backed audit
        # ----------------------------------------------------

        audit = None

        if (
            investigation_id is not None
            and result.get("success") is True
        ):

            audit = create_audit_record(
                db=db,
                record_type="AI_HYGIENE_ANALYSIS",
                entity_type="INVESTIGATION",
                entity_id=investigation_id,
                actor_id=officer.id,
                payload={
                    "filename":
                        file.filename,

                    "result":
                        result,

                    "stored_findings":
                        stored_findings,
                },
            )

            db.commit()
            db.refresh(audit)

        return {
            "service":
                "hygiene_detection",

            "investigation_id":
                investigation_id,

            "result":
                result,

            "stored_findings":
                len(stored_findings),

            "audit": (
                {
                    "id":
                        audit.id,

                    "record_hash":
                        audit.record_hash,

                    "blockchain_tx_id":
                        audit.blockchain_tx_id,

                    "verification_status":
                        audit.verification_status,
                }
                if audit
                else None
            ),
        }

    finally:
        image_path.unlink(
            missing_ok=True
        )