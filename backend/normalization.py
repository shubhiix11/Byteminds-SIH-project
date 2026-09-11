"""
Unit and text normalization module for Legal Metrology compliance data.
"""

UNIT_MAP = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "l": "L",
    "liter": "L",
    "litre": "L",
    "liters": "L",
    "litres": "L",
}

def normalize_unit(unit_str: str) -> str:
    """Normalize unit string to standardized Legal Metrology unit code."""
    if not unit_str:
        return ""
    cleaned = unit_str.strip().lower()
    return UNIT_MAP.get(cleaned, unit_str.strip())

def normalize_text(text: str) -> str:
    """Normalize whitespace and capitalization."""
    if not text:
        return ""
    return " ".join(text.strip().split())
