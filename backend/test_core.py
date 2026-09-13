from __future__ import annotations

import os
import unittest

from backend.main import app
from backend.services.item_safety_service import assess_item
from backend.services.monthly_ai_analyzer import analyze_monthly_performance


class ItemSafetyTests(unittest.TestCase):
    def test_expired_item_is_unsafe(self):
        result = assess_item({"status": "EXPIRED"})
        self.assertEqual(result["status"], "UNSAFE")
        self.assertFalse(result["safe"])

    def test_valid_item_without_other_risk_is_safe(self):
        result = assess_item({"status": "VALID"})
        self.assertEqual(result["status"], "SAFE")
        self.assertTrue(result["safe"])

    def test_valid_item_with_high_storage_temperature_needs_action(self):
        result = assess_item(
            {"status": "VALID"},
            temperature=10,
        )
        self.assertEqual(result["status"], "CHECK")
        self.assertIn("Storage temperature is elevated", result["reasons"])

    def test_high_visual_risk_makes_item_unsafe(self):
        result = assess_item(
            {"status": "VALID"},
            vision={
                "success": True,
                "risk_score": 75,
            },
        )
        self.assertEqual(result["status"], "UNSAFE")


class MonthlyAITests(unittest.TestCase):
    def test_fallback_uses_official_base_score(self):
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            result = analyze_monthly_performance(
                current={
                    "compliance_score": 82,
                    "concerns": [],
                    "risk_trend": "STABLE",
                },
                history=[],
                audit_month="2026-09",
            )
            self.assertEqual(result["score"], 82.0)
            self.assertEqual(result["status"], "GOOD")
            self.assertEqual(result["ai_model"], "RULE_BASED_FALLBACK")
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key

    def test_persistent_failure_is_detected_deterministically(self):
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            result = analyze_monthly_performance(
                current={
                    "compliance_score": 55,
                    "concerns": [],
                    "risk_trend": "STABLE",
                },
                history=[
                    {"audit_month": "2026-08", "score": 54},
                    {"audit_month": "2026-07", "score": 56},
                ],
                audit_month="2026-09",
            )
            self.assertTrue(result["persistent_failure"])
            self.assertTrue(result["licence_review_recommended"])
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key


class RouteRegistrationTests(unittest.TestCase):
    def test_required_routes_are_registered(self):
        paths = {route.path for route in app.routes}
        required = {
            "/health",
            "/sensors/readings",
            "/ai/expiry",
            "/ai/hygiene",
            "/ai/item-safety",
            "/government/monthly-notices",
            "/government/monthly-notices/generate",
            "/government/action-queue",
            "/public/outlets/{registration_id}",
        }
        self.assertTrue(required.issubset(paths))


if __name__ == "__main__":
    unittest.main(verbosity=2)
