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
    UniqueConstraint,
)

from .database import Base


class MonthlyAIAnalysis(Base):
    __tablename__ = "monthly_ai_analyses"

    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "audit_month",
            name="uq_monthly_ai_restaurant_month",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True,
    )
    audit_month = Column(String(7), nullable=False, index=True)
    score = Column(Float, nullable=False)
    public_status = Column(String(20), nullable=False)
    ai_comment = Column(Text, nullable=False)
    base_audit_score = Column(Float, nullable=False)
    licence_review_recommended = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    ai_model = Column(String(120), nullable=False)
    input_snapshot = Column(Text, default="{}", nullable=False)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    generated_by = Column(
        Integer,
        ForeignKey("government_officers.id"),
        nullable=True,
    )


class OutletContact(Base):
    __tablename__ = "outlet_contacts"

    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            name="uq_outlet_contact_restaurant",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True,
    )
    official_name = Column(String(200), nullable=False)
    email = Column(String(255))
    phone = Column(String(40))
    active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(
        Integer,
        ForeignKey("monthly_audit_notices.id"),
        nullable=False,
        index=True,
    )
    channel = Column(String(20), nullable=False)
    destination = Column(String(255))
    status = Column(String(30), nullable=False)
    provider_message_id = Column(String(200))
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
