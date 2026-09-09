"""Interface placeholder for the future YOLO hygiene model."""


def normalize_detection(label: str, confidence: float):
    label = label.strip().upper()
    return {
        "label": label,
        "confidence": round(float(confidence), 4),
        "is_actionable": label in {"UNCOVERED_FOOD", "GARBAGE_OVERFLOW", "PPE_NON_COMPLIANCE"},
    }
