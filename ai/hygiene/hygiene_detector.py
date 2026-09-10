from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parent
    / "weights"
    / "hygiene.pt"
)


# Classes that represent actual hygiene/contamination problems.
RISK_WEIGHTS = {
    "no_apron": 35,
    "no_gloves": 35,
    "no_hairnet": 35,
    "cockroach": 60,
    "lizard": 60,
    "rat": 60,
}


def _calculate_hygiene_risk(
    detections: list[dict[str, Any]],
) -> int:
    score = 0

    for detection in detections:
        label = (
            str(detection.get("label", ""))
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        confidence = float(
            detection.get("confidence", 0)
        )

        weight = RISK_WEIGHTS.get(label, 0)

        score += int(weight * confidence)

    return min(100, score)


def _risk_status(score: int) -> str:
    if score >= 70:
        return "HIGH_RISK"

    if score >= 40:
        return "MODERATE_RISK"

    return "LOW_RISK"


def analyze_hygiene(
    image_path: str | Path,
    model_path: str | Path | None = None,
) -> dict[str, Any]:

    image_path = Path(image_path)

    if not image_path.exists():
        return {
            "success": False,
            "status": "IMAGE_NOT_FOUND",
            "detections": [],
            "risk_score": 0,
            "risk_status": "LOW_RISK",
            "message": str(image_path),
        }

    selected_model = (
        Path(model_path)
        if model_path
        else DEFAULT_MODEL_PATH
    )

    if not selected_model.exists():
        return {
            "success": False,
            "status": "MODEL_NOT_CONFIGURED",
            "detections": [],
            "risk_score": 0,
            "risk_status": "LOW_RISK",
            "message": (
                "Hygiene model weights not found. "
                f"Expected: {selected_model}"
            ),
        }

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        return {
            "success": False,
            "status": "DEPENDENCY_MISSING",
            "detections": [],
            "risk_score": 0,
            "risk_status": "LOW_RISK",
            "message": "ultralytics is not installed.",
            "error": str(exc),
        }

    try:
        model = YOLO(str(selected_model))

        results = model.predict(
            source=str(image_path),
            verbose=False,
            conf=0.25,
        )

        detections: list[dict[str, Any]] = []

        for result in results:
            names = result.names

            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())

                label = names[class_id]

                xyxy = [
                    round(float(value), 2)
                    for value in box.xyxy[0].tolist()
                ]

                detections.append(
                    {
                        "label": label,
                        "confidence": round(
                            confidence,
                            4,
                        ),
                        "class_id": class_id,
                        "bbox": xyxy,
                    }
                )

        risk_score = _calculate_hygiene_risk(
            detections
        )

        return {
            "success": True,
            "status": _risk_status(risk_score),
            "risk_status": _risk_status(risk_score),
            "detections": detections,
            "risk_score": risk_score,
            "model": str(selected_model),
            "prediction_count": len(detections),
        }

    except Exception as exc:
        return {
            "success": False,
            "status": "MODEL_ERROR",
            "detections": [],
            "risk_score": 0,
            "risk_status": "LOW_RISK",
            "message": str(exc),
        }