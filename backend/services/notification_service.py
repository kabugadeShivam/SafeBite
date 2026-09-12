from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any

import requests
from sqlalchemy.orm import Session

from ..models import MonthlyAuditNotice
from ..models_monthly import NotificationDelivery, OutletContact


class NotificationResult:
    def __init__(
        self,
        channel: str,
        status: str,
        destination: str | None = None,
        provider_message_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.channel = channel
        self.status = status
        self.destination = destination
        self.provider_message_id = provider_message_id
        self.error_message = error_message


def _send_email(
    contact: OutletContact,
    notice: MonthlyAuditNotice,
) -> NotificationResult:
    destination = (contact.email or "").strip()

    if not destination:
        return NotificationResult(
            "EMAIL",
            "MISSING_DESTINATION",
        )

    host = os.getenv("SAFEBITE_SMTP_HOST", "").strip()
    username = os.getenv("SAFEBITE_SMTP_USERNAME", "").strip()
    password = os.getenv("SAFEBITE_SMTP_PASSWORD", "")
    from_email = os.getenv("SAFEBITE_FROM_EMAIL", "").strip()
    port = int(os.getenv("SAFEBITE_SMTP_PORT", "587"))
    use_tls = os.getenv(
        "SAFEBITE_SMTP_USE_TLS",
        "true",
    ).strip().lower() in {"1", "true", "yes"}

    if not host or not from_email:
        return NotificationResult(
            "EMAIL",
            "NOT_CONFIGURED",
            destination=destination,
        )

    message = EmailMessage()
    message["Subject"] = notice.title
    message["From"] = from_email
    message["To"] = destination
    message.set_content(notice.message)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()

            if username:
                smtp.login(username, password)

            smtp.send_message(message)

        return NotificationResult(
            "EMAIL",
            "SENT",
            destination=destination,
        )

    except (OSError, smtplib.SMTPException) as exc:
        return NotificationResult(
            "EMAIL",
            "FAILED",
            destination=destination,
            error_message=str(exc),
        )


def _send_sms(
    contact: OutletContact,
    notice: MonthlyAuditNotice,
) -> NotificationResult:
    destination = (contact.phone or "").strip()

    if not destination:
        return NotificationResult(
            "SMS",
            "MISSING_DESTINATION",
        )

    account_sid = os.getenv(
        "TWILIO_ACCOUNT_SID",
        "",
    ).strip()

    auth_token = os.getenv(
        "TWILIO_AUTH_TOKEN",
        "",
    ).strip()

    from_number = os.getenv(
        "TWILIO_FROM_NUMBER",
        "",
    ).strip()

    if not account_sid or not auth_token or not from_number:
        return NotificationResult(
            "SMS",
            "NOT_CONFIGURED",
            destination=destination,
        )

    body = (
        f"SafeBite: {notice.title}. "
        f"Score {notice.compliance_score:.0f}/100, "
        f"status {notice.compliance_status}. "
        f"{notice.message.splitlines()[2] if len(notice.message.splitlines()) > 2 else notice.message}"
    )

    body = body[:1400]

    url = (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{account_sid}/Messages.json"
    )

    try:
        response = requests.post(
            url,
            data={
                "From": from_number,
                "To": destination,
                "Body": body,
            },
            auth=(account_sid, auth_token),
            timeout=20,
        )
    except requests.RequestException as exc:
        return NotificationResult(
            "SMS",
            "FAILED",
            destination=destination,
            error_message=str(exc),
        )

    if not response.ok:
        return NotificationResult(
            "SMS",
            "FAILED",
            destination=destination,
            error_message=f"Provider HTTP {response.status_code}",
        )

    try:
        provider_data = response.json()
    except ValueError:
        provider_data = {}

    return NotificationResult(
        "SMS",
        "SENT",
        destination=destination,
        provider_message_id=provider_data.get("sid"),
    )


def deliver_monthly_notice(
    db: Session,
    notice: MonthlyAuditNotice,
) -> dict[str, Any]:
    contact = (
        db.query(OutletContact)
        .filter(
            OutletContact.restaurant_id
            == notice.restaurant_id,
            OutletContact.active.is_(True),
        )
        .first()
    )

    if not contact:
        notice.delivery_status = "PENDING_CONTACT"
        return {
            "delivery_status": "PENDING_CONTACT",
            "results": [],
        }

    results = [
        _send_email(contact, notice),
        _send_sms(contact, notice),
    ]

    for result in results:
        db.add(
            NotificationDelivery(
                notice_id=notice.id,
                channel=result.channel,
                destination=result.destination,
                status=result.status,
                provider_message_id=result.provider_message_id,
                error_message=result.error_message,
                sent_at=(
                    datetime.utcnow()
                    if result.status == "SENT"
                    else None
                ),
            )
        )

    statuses = {item.status for item in results}

    if "SENT" in statuses and statuses <= {"SENT"}:
        notice.delivery_status = "SENT"
    elif "SENT" in statuses:
        notice.delivery_status = "PARTIAL"
    elif "FAILED" in statuses:
        notice.delivery_status = "FAILED"
    else:
        notice.delivery_status = "NOT_CONFIGURED"

    return {
        "delivery_status": notice.delivery_status,
        "results": [
            {
                "channel": item.channel,
                "status": item.status,
                "destination": item.destination,
                "provider_message_id": item.provider_message_id,
                "error_message": item.error_message,
            }
            for item in results
        ],
    }
