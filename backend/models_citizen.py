from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .database import Base


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True,
    )

    concern_category = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        Text,
        default="",
        nullable=False,
    )

    original_filename = Column(
        String(255),
    )

    stored_path = Column(
        String(500),
        nullable=False,
    )

    content_type = Column(
        String(100),
    )

    media_sha256 = Column(
        String(64),
        nullable=False,
        index=True,
    )

    is_anonymous = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    status = Column(
        String(40),
        default="SUBMITTED",
        nullable=False,
        index=True,
    )

    submitted_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    ai_status = Column(
        String(50),
        default="NOT_ANALYZED",
        nullable=False,
    )

    ai_relevance = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    ai_severity = Column(
        String(30),
        default="UNKNOWN",
        nullable=False,
    )

    ai_findings = Column(
        Text,
        default="{}",
        nullable=False,
    )

    ai_model = Column(
        String(200),
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("government_officers.id"),
        nullable=True,
    )

    reviewed_at = Column(
        DateTime,
    )

    review_notes = Column(
        Text,
        default="",
        nullable=False,
    )