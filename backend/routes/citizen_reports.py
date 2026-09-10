from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.hygiene.hygiene_detector import analyze_hygiene

from ..database import get_db
from ..models import (
    Alert,
    GovernmentOfficer,
    Investigation,
    Restaurant,
)
from ..models_citizen import CitizenReport
from ..security import get_token_payload
from ..services.blockchain_service import (
    create_audit_record,
)


# ============================================================
# ROUTERS
# ============================================================

public_router = APIRouter(
    prefix="/public",
    tags=["Citizen Reports"],
)

government_router = APIRouter(
    prefix="/government/citizen-reports",
    tags=["Citizen Reports - Government"],
)


# ============================================================
# DIRECTORIES
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

CITIZEN_UPLOAD_DIR = (
    PROJECT_ROOT
    / "backend"
    / "uploads"
    / "citizen"
)

CITIZEN_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
}

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024

HYGIENE_VIOLATIONS = {
    "no_apron",
    "no_gloves",
    "no_hairnet",
}

CRITICAL_FINDINGS = {
    "cockroach",
    "lizard",
    "rat",
}


# ============================================================
# GOVERNMENT AUTHENTICATION
# ============================================================

def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(
            payload["sub"]
        )

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
# HASH
# ============================================================

def _sha256(
    content: bytes,
) -> str:

    return hashlib.sha256(
        content
    ).hexdigest()


# ============================================================
# SAVE MEDIA
# ============================================================

def _save_media(
    file: UploadFile,
) -> tuple[Path, bytes]:

    original_name = (
        file.filename
        or "citizen_report"
    )

    extension = (
        Path(original_name)
        .suffix
        .lower()
    )

    allowed_extensions = (
        ALLOWED_IMAGE_EXTENSIONS
        | ALLOWED_VIDEO_EXTENSIONS
    )

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported media type. "
                "Allowed images: jpg, jpeg, png, webp, bmp. "
                "Allowed videos: mp4, mov, avi, webm."
            ),
        )

    content = file.file.read()

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded media is empty",
        )

    if (
        extension
        in ALLOWED_IMAGE_EXTENSIONS
        and len(content) > MAX_IMAGE_BYTES
    ):

        raise HTTPException(
            status_code=413,
            detail="Image exceeds 15 MB limit",
        )

    if (
        extension
        in ALLOWED_VIDEO_EXTENSIONS
        and len(content) > MAX_VIDEO_BYTES
    ):

        raise HTTPException(
            status_code=413,
            detail="Video exceeds 50 MB limit",
        )

    destination = (
        CITIZEN_UPLOAD_DIR
        / f"{uuid.uuid4().hex}{extension}"
    )

    destination.write_bytes(
        content
    )

    return destination, content


# ============================================================
# AI TRIAGE
# ============================================================

def _analyze_citizen_media(
    media_path: Path,
    content_type: str | None,
    extension: str,
) -> dict:

    # --------------------------------------------------------
    # IMAGE ANALYSIS
    # --------------------------------------------------------

    if extension in ALLOWED_IMAGE_EXTENSIONS:

        result = analyze_hygiene(
            media_path
        )

        if not result.get("success"):

            return {
                "ai_status":
                    "AI_ERROR",

                "relevance":
                    0.0,

                "severity":
                    "UNKNOWN",

                "findings": {
                    "message":
                        result.get(
                            "message",
                            "AI analysis failed",
                        ),
                },

                "model":
                    "SafeBite local YOLO",
            }

        detections = result.get(
            "detections",
            [],
        )

        relevant = [
            detection
            for detection
            in detections
            if str(
                detection.get(
                    "label",
                    "",
                )
            ).lower()
            in (
                HYGIENE_VIOLATIONS
                | CRITICAL_FINDINGS
            )
        ]

        max_confidence = 0.0

        if relevant:

            max_confidence = max(
                float(
                    item.get(
                        "confidence",
                        0,
                    )
                )
                for item in relevant
            )

        if not relevant:

            return {
                "ai_status":
                    "SCREENED_NO_RELEVANT_FINDING",

                "relevance":
                    0.0,

                "severity":
                    "LOW",

                "findings": {
                    "detections":
                        detections,

                    "message":
                        "No recognized hygiene violation "
                        "was detected.",
                },

                "model":
                    result.get(
                        "model",
                        "SafeBite local YOLO",
                    ),
            }

        if any(
            str(
                item.get(
                    "label",
                    "",
                )
            ).lower()
            in CRITICAL_FINDINGS
            for item in relevant
        ):

            severity = "CRITICAL"

        else:

            severity = "MODERATE"

        return {
            "ai_status":
                "AI_SCREENED",

            "relevance":
                round(
                    min(
                        1.0,
                        max_confidence,
                    ),
                    4,
                ),

            "severity":
                severity,

            "findings": {
                "detections":
                    detections,

                "relevant_detections":
                    relevant,
            },

            "model":
                result.get(
                    "model",
                    "SafeBite local YOLO",
                ),
        }

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    return {
        "ai_status":
            "VIDEO_ANALYSIS_PENDING",

        "relevance":
            0.0,

        "severity":
            "UNKNOWN",

        "findings": {
            "message":
                "Video received. "
                "Detailed frame-based AI analysis is pending.",
        },

        "model":
            "Pending video analysis",
    }


# ============================================================
# CREATE CITIZEN ALERT
# ============================================================

def _create_citizen_alert(
    db: Session,
    report: CitizenReport,
    restaurant: Restaurant,
) -> Alert:

    severity = (
        str(
            report.ai_severity
            or "UNKNOWN"
        )
        .upper()
    )

    if severity == "CRITICAL":

        alert_severity = "RED"
        risk_score = 90.0

    elif severity == "MODERATE":

        alert_severity = "ORANGE"
        risk_score = 65.0

    elif severity == "LOW":

        alert_severity = "YELLOW"
        risk_score = 30.0

    else:

        alert_severity = "ORANGE"
        risk_score = 50.0

    reason = (
        f"Citizen Report #{report.id}: "
        f"{report.concern_category}. "
        f"AI triage status: {report.ai_status}. "
        f"AI relevance: {report.ai_relevance:.4f}. "
        f"AI severity: {report.ai_severity}."
    )

    alert = Alert(
        alert_type="CITIZEN_REPORT",

        severity=alert_severity,

        risk_score=risk_score,

        reason=reason,

        source="CITIZEN",

        status="OPEN",

        restaurant_id=restaurant.id,

        device_id=None,

        sensor_reading_id=None,
    )

    db.add(
        alert
    )

    db.flush()

    return alert


# ============================================================
# CREATE INVESTIGATION FROM CITIZEN REPORT
# ============================================================

def _create_citizen_investigation(
    db: Session,
    report: CitizenReport,
    alert: Alert,
    officer: GovernmentOfficer,
) -> Investigation:

    existing = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id
            == alert.id
        )
        .first()
    )

    if existing:

        return existing

    findings = (
        f"Investigation automatically created "
        f"from Citizen Report #{report.id}. "
        f"Citizen concern: "
        f"{report.concern_category}. "
        f"AI preliminary status: "
        f"{report.ai_status}. "
        f"AI severity: "
        f"{report.ai_severity}. "
        f"AI relevance: "
        f"{report.ai_relevance:.4f}."
    )

    investigation = Investigation(
        alert_id=alert.id,

        officer_id=officer.id,

        findings=findings,

        action_taken="",

        corrective_action="",

        status="IN_PROGRESS",

        started_at=datetime.utcnow(),

    )

    db.add(
        investigation
    )

    alert.status = (
        "UNDER_INVESTIGATION"
    )

    db.flush()

    return investigation


# ============================================================
# PUBLIC: SUBMIT REPORT
# ============================================================

@public_router.post("/reports")
def submit_citizen_report(
    registration_id: str = Form(...),

    concern_category: str = Form(...),

    description: str = Form(""),

    is_anonymous: bool = Form(True),

    file: UploadFile = File(...),

    db: Session = Depends(get_db),
):

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.registration_id
            == registration_id
        )
        .first()
    )

    if not restaurant:

        raise HTTPException(
            status_code=404,
            detail="Registered outlet not found",
        )

    media_path = None

    try:

        media_path, content = (
            _save_media(file)
        )

        media_hash = _sha256(
            content
        )

        analysis = _analyze_citizen_media(
            media_path=media_path,

            content_type=file.content_type,

            extension=media_path.suffix.lower(),
        )

        report = CitizenReport(
            restaurant_id=restaurant.id,

            concern_category=(
                concern_category.strip()
                [:100]
            ),

            description=(
                description.strip()
            ),

            original_filename=
                file.filename,

            stored_path=
                str(media_path),

            content_type=
                file.content_type,

            media_sha256=
                media_hash,

            is_anonymous=
                is_anonymous,

            status=
                "SUBMITTED",

            ai_status=
                analysis["ai_status"],

            ai_relevance=
                analysis["relevance"],

            ai_severity=
                analysis["severity"],

            ai_findings=
                json.dumps(
                    analysis["findings"],
                    default=str,
                ),

            ai_model=
                analysis["model"],
        )

        db.add(
            report
        )

        db.flush()

        audit = create_audit_record(
            db=db,

            record_type=
                "CITIZEN_REPORT_SUBMITTED",

            entity_type=
                "CITIZEN_REPORT",

            entity_id=
                report.id,

            actor_id=
                None,

            payload={
                "restaurant_id":
                    restaurant.id,

                "registration_id":
                    restaurant.registration_id,

                "concern_category":
                    report.concern_category,

                "media_sha256":
                    media_hash,

                "ai_status":
                    report.ai_status,

                "ai_relevance":
                    report.ai_relevance,

                "ai_severity":
                    report.ai_severity,
            },
        )

        db.commit()

        db.refresh(
            report
        )

        return {
            "success":
                True,

            "report_id":
                report.id,

            "outlet": {
                "name":
                    restaurant.name,

                "registration_id":
                    restaurant.registration_id,
            },

            "status":
                report.status,

            "ai_triage": {
                "status":
                    report.ai_status,

                "relevance":
                    report.ai_relevance,

                "severity":
                    report.ai_severity,
            },

            "media": {
                "sha256":
                    report.media_sha256,
            },

            "audit": {
                "id":
                    audit.id,

                "record_hash":
                    audit.record_hash,

                "blockchain_tx_id":
                    audit.blockchain_tx_id,

                "verification_status":
                    audit.verification_status,
            },
        }

    except Exception:

        if media_path is not None:

            media_path.unlink(
                missing_ok=True
            )

        raise


# ============================================================
# PUBLIC: TRACK REPORT
# ============================================================

@public_router.get(
    "/reports/{report_id}"
)
def get_citizen_report_status(
    report_id: int,

    db: Session = Depends(get_db),
):

    report = (
        db.query(CitizenReport)
        .filter(
            CitizenReport.id
            == report_id
        )
        .first()
    )

    if not report:

        raise HTTPException(
            status_code=404,
            detail="Citizen report not found",
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == report.restaurant_id
        )
        .first()
    )

    return {
        "report_id":
            report.id,

        "outlet":
            restaurant.name
            if restaurant
            else "Unknown",

        "registration_id":
            restaurant.registration_id
            if restaurant
            else None,

        "submitted_at":
            report.submitted_at,

        "status":
            report.status,

        "ai_status":
            report.ai_status,

        "ai_relevance":
            report.ai_relevance,

        "ai_severity":
            report.ai_severity,

        "message": (
            "Your report has been received. "
            "Government officers may review the evidence "
            "and initiate further action."
        ),
    }


# ============================================================
# GOVERNMENT: LIST REPORTS
# ============================================================

@government_router.get("")
def list_citizen_reports(
    status: str | None = None,

    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),

    db: Session = Depends(get_db),
):

    query = (
        db.query(CitizenReport)
        .join(
            Restaurant,
            CitizenReport.restaurant_id
            == Restaurant.id,
        )
    )

    # --------------------------------------------------------
    # Regional restriction
    # --------------------------------------------------------

    if (
        officer.role.upper()
        != "CENTRAL_ADMIN"
    ):

        query = query.filter(
            Restaurant.state
            == officer.state,

            Restaurant.region
            == officer.region,
        )

    if status:

        query = query.filter(
            CitizenReport.status
            == status.upper()
        )

    reports = (
        query
        .order_by(
            CitizenReport.submitted_at.desc()
        )
        .all()
    )

    return {
        "count":
            len(reports),

        "reports": [

            {
                "id":
                    report.id,

                "outlet": {
                    "id":
                        report.restaurant_id,

                    "name":
                        report.restaurant.name,

                    "registration_id":
                        report.restaurant.registration_id,

                    "region":
                        report.restaurant.region,
                },

                "category":
                    report.concern_category,

                "description":
                    report.description,

                "submitted_at":
                    report.submitted_at,

                "status":
                    report.status,

                "ai": {
                    "status":
                        report.ai_status,

                    "relevance":
                        report.ai_relevance,

                    "severity":
                        report.ai_severity,

                    "findings":
                        json.loads(
                            report.ai_findings
                            or "{}"
                        ),
                },

                "media_sha256":
                    report.media_sha256,
            }

            for report in reports

        ],
    }


# ============================================================
# GOVERNMENT: REVIEW REPORT
# ============================================================

class CitizenReportReview(BaseModel):

    status: str

    notes: str = ""


@government_router.post(
    "/{report_id}/review"
)
def review_citizen_report(

    report_id: int,

    payload: CitizenReportReview,

    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),

    db: Session = Depends(get_db),
):

    new_status = (
        payload.status
        .strip()
        .upper()
    )

    allowed_statuses = {
        "VERIFIED",
        "DISMISSED",
        "NEEDS_INVESTIGATION",
    }

    if new_status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be VERIFIED, "
                "DISMISSED, or NEEDS_INVESTIGATION"
            ),
        )

    report = (
        db.query(CitizenReport)
        .filter(
            CitizenReport.id
            == report_id
        )
        .first()
    )

    if not report:

        raise HTTPException(
            status_code=404,
            detail="Citizen report not found",
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == report.restaurant_id
        )
        .first()
    )

    if not restaurant:

        raise HTTPException(
            status_code=404,
            detail="Associated outlet not found",
        )

    # --------------------------------------------------------
    # Regional authorization
    # --------------------------------------------------------

    if (
        officer.role.upper()
        != "CENTRAL_ADMIN"
    ):

        if (
            restaurant.state.lower()
            != officer.state.lower()
            or restaurant.region.lower()
            != officer.region.lower()
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Report is outside your authorized region"
                ),
            )

    # --------------------------------------------------------
    # Prevent accidental re-verification.
    # --------------------------------------------------------

    if (
        report.status == "VERIFIED"
        and new_status == "VERIFIED"
    ):

        raise HTTPException(
            status_code=400,
            detail="Report is already verified",
        )

    # ========================================================
    # UPDATE REPORT STATUS
    # ========================================================

    report.status = new_status

    report.reviewed_by = officer.id

    report.reviewed_at = (
        datetime.utcnow()
    )

    report.review_notes = (
        payload.notes.strip()
    )

    # ========================================================
    # GOVERNMENT AUDIT OF REVIEW
    # ========================================================

    review_audit = create_audit_record(
        db=db,

        record_type=
            "CITIZEN_REPORT_REVIEWED",

        entity_type=
            "CITIZEN_REPORT",

        entity_id=
            report.id,

        actor_id=
            officer.id,

        payload={
            "report_status":
                new_status,

            "review_notes":
                payload.notes,

            "restaurant_id":
                restaurant.id,

            "media_sha256":
                report.media_sha256,

            "ai_status":
                report.ai_status,

            "ai_relevance":
                report.ai_relevance,

            "ai_severity":
                report.ai_severity,
        },
    )

    # ========================================================
    # AUTOMATIC INVESTIGATION
    # ========================================================

    alert = None

    investigation = None

    investigation_audit = None

    if (
        new_status
        == "NEEDS_INVESTIGATION"
    ):

        # ----------------------------------------------------
        # Check whether an investigation was already created
        # for this citizen report.
        #
        # The citizen report itself has no investigation_id,
        # so we identify its generated alert through the
        # unique reason prefix.
        # ----------------------------------------------------

        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.restaurant_id
                == restaurant.id,

                Alert.source
                == "CITIZEN",

                Alert.alert_type
                == "CITIZEN_REPORT",

                Alert.reason.like(
                    f"Citizen Report #{report.id}:%"
                ),
            )
            .order_by(
                Alert.id.desc()
            )
            .first()
        )

        if existing_alert:

            alert = existing_alert

            investigation = (
                db.query(Investigation)
                .filter(
                    Investigation.alert_id
                    == alert.id
                )
                .first()
            )

        else:

            alert = _create_citizen_alert(
                db=db,

                report=report,

                restaurant=restaurant,
            )

            investigation = (
                _create_citizen_investigation(
                    db=db,

                    report=report,

                    alert=alert,

                    officer=officer,
                )
            )

            # ------------------------------------------------
            # Blockchain audit for automatic escalation
            # ------------------------------------------------

            investigation_audit = (
                create_audit_record(
                    db=db,

                    record_type=
                        "CITIZEN_REPORT_ESCALATED",

                    entity_type=
                        "INVESTIGATION",

                    entity_id=
                        investigation.id,

                    actor_id=
                        officer.id,

                    payload={
                        "citizen_report_id":
                            report.id,

                        "alert_id":
                            alert.id,

                        "restaurant_id":
                            restaurant.id,

                        "reason":
                            report.concern_category,

                        "ai_relevance":
                            report.ai_relevance,

                        "ai_severity":
                            report.ai_severity,
                    },
                )
            )

    # ========================================================
    # COMMIT
    # ========================================================

    db.commit()

    db.refresh(
        report
    )

    if alert:

        db.refresh(
            alert
        )

    if investigation:

        db.refresh(
            investigation
        )

    return {
        "success":
            True,

        "report_id":
            report.id,

        "status":
            report.status,

        "reviewed_by":
            officer.name,

        "reviewed_at":
            report.reviewed_at,

        "investigation": (
            {
                "created":
                    investigation_audit
                    is not None,

                "id":
                    investigation.id,

                "alert_id":
                    alert.id,

                "status":
                    investigation.status,

                "priority":
                    alert.severity,

            }
            if investigation and alert
            else None
        ),

        "audit": {
            "record_hash":
                review_audit.record_hash,

            "blockchain_tx_id":
                review_audit.blockchain_tx_id,

            "verification_status":
                review_audit.verification_status,
        },

        "escalation_audit": (
            {
                "record_hash":
                    investigation_audit.record_hash,

                "blockchain_tx_id":
                    investigation_audit.blockchain_tx_id,

                "verification_status":
                    investigation_audit.verification_status,
            }
            if investigation_audit
            else None
        ),
    }


# ============================================================
# GOVERNMENT: SECURE MEDIA VIEWER
# ============================================================

@government_router.get(
    "/{report_id}/media"
)
def view_citizen_report_media(

    report_id: int,

    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),

    db: Session = Depends(get_db),
):

    report = (
        db.query(CitizenReport)
        .filter(
            CitizenReport.id
            == report_id
        )
        .first()
    )

    if not report:

        raise HTTPException(
            status_code=404,
            detail="Citizen report not found",
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == report.restaurant_id
        )
        .first()
    )

    if not restaurant:

        raise HTTPException(
            status_code=404,
            detail="Associated outlet not found",
        )

    # --------------------------------------------------------
    # Regional authorization
    # --------------------------------------------------------

    if (
        officer.role.upper()
        != "CENTRAL_ADMIN"
    ):

        if (
            restaurant.state.lower()
            != officer.state.lower()
            or restaurant.region.lower()
            != officer.region.lower()
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Report is outside your authorized region"
                ),
            )

    # --------------------------------------------------------
    # Secure path validation
    # --------------------------------------------------------

    media_path = Path(
        report.stored_path
    ).resolve()

    upload_root = (
        CITIZEN_UPLOAD_DIR
        .resolve()
    )

    try:

        media_path.relative_to(
            upload_root
        )

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Invalid media path",
        )

    if not media_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Evidence media not found",
        )

    # --------------------------------------------------------
    # Safe content type
    # --------------------------------------------------------

    content_type = (
        report.content_type
        or "application/octet-stream"
    )

    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "video/mp4",
        "video/quicktime",
        "video/webm",
        "video/x-msvideo",
    }

    if content_type not in allowed_content_types:

        content_type = (
            "application/octet-stream"
        )

    return FileResponse(
        path=str(
            media_path
        ),

        media_type=
            content_type,

        headers={
            "Content-Disposition":
                "inline",

            "X-SafeBite-Evidence-Hash":
                report.media_sha256,

            "X-SafeBite-Report-ID":
                str(report.id),
        },
    )