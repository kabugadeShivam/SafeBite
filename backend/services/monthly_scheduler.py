from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from ..database import SessionLocal
from ..models import Restaurant
from ..models_monthly import MonthlyAIAnalysis
from .monthly_notice_service import generate_monthly_notices


_scheduler_started = False
_scheduler_lock = threading.Lock()


def _previous_month(value: datetime) -> str:
    if value.month == 1:
        return f"{value.year - 1:04d}-12"

    return f"{value.year:04d}-{value.month - 1:02d}"


def _should_run(target_month: str) -> bool:
    db = SessionLocal()
    try:
        outlet_count = (
            db.query(Restaurant)
            .filter(Restaurant.status == "ACTIVE")
            .count()
        )

        analyzed_count = (
            db.query(MonthlyAIAnalysis)
            .filter(
                MonthlyAIAnalysis.audit_month == target_month
            )
            .join(
                Restaurant,
                MonthlyAIAnalysis.restaurant_id
                == Restaurant.id,
            )
            .count()
        )

        return (
            outlet_count == 0
            or analyzed_count < outlet_count
        )
    finally:
        db.close()


def _run_for_month(target_month: str) -> None:
    db = SessionLocal()
    try:
        generate_monthly_notices(
            db=db,
            audit_month=target_month,
            state=None,
            region=None,
            actor_id=None,
        )
    except Exception:
        # A failed monthly run must never stop the API process.
        db.rollback()
    finally:
        db.close()


def _scheduler_loop() -> None:
    run_day = max(
        1,
        min(
            28,
            int(
                os.getenv(
                    "SAFE_BITE_MONTHLY_RUN_DAY",
                    "1",
                )
            ),
        ),
    )

    run_hour = max(
        0,
        min(
            23,
            int(
                os.getenv(
                    "SAFE_BITE_MONTHLY_RUN_HOUR_UTC",
                    "2",
                )
            ),
        ),
    )

    catch_up_days = max(
        1,
        min(
            7,
            int(
                os.getenv(
                    "SAFE_BITE_MONTHLY_CATCH_UP_DAYS",
                    "7",
                )
            ),
        ),
    )

    last_attempted_month = None

    while True:
        now = datetime.utcnow()
        target_month = _previous_month(now)

        run_window = (
            now.day >= run_day
            and now.day <= min(
                28,
                run_day + catch_up_days - 1,
            )
            and now.hour >= run_hour
        )

        if (
            run_window
            and target_month != last_attempted_month
            and _should_run(target_month)
        ):
            _run_for_month(target_month)
            last_attempted_month = target_month

        time.sleep(60)


def start_monthly_scheduler() -> None:
    global _scheduler_started

    if os.getenv(
        "SAFE_BITE_MONTHLY_AUTO_RUN",
        "true",
    ).strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        return

    with _scheduler_lock:
        if _scheduler_started:
            return

        thread = threading.Thread(
            target=_scheduler_loop,
            name="SafeBiteMonthlyAuditScheduler",
            daemon=True,
        )

        thread.start()
        _scheduler_started = True
