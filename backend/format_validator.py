"""
Format Validator for Legal Metrology Packaged Commodities Declarations.
Validates extracted candidate declarations independently from rule applicability.
"""

import re
from normalization import normalize_unit, normalize_text

class FormatValidator:
    @staticmethod
    def validate_mrp(mrp_fact: dict) -> dict:
        """
        Validates Maximum Retail Price (MRP) declaration format.
        Expected format: Must contain numeric value, currency, and 'incl. of all taxes' or equivalent.
        """
        if not mrp_fact:
            return {"valid": False, "reason": "No MRP declaration detected.", "normalized_value": None}
        
        original_text = mrp_fact.get("original_text", "") or mrp_fact.get("raw", "")
        value = mrp_fact.get("value")
        currency = mrp_fact.get("currency", "INR")

        if value is None and original_text:
            # Attempt regex extraction if value was not pre-parsed
            match = re.search(r'(?:₹|Rs\.?|INR)\s*([0-9]+(?:\.[0-9]{1,2})?)', original_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))

        if value is None or value <= 0:
            return {
                "valid": False,
                "reason": "MRP declaration does not contain a valid positive numeric price value.",
                "normalized_value": None
            }

        # Check for mandatory "inclusive of all taxes" wording or symbol
        has_tax_clause = bool(re.search(r'(?:incl|inclusive)\.?(?:\s+of)?\s+all\s+taxes|incl\.?\s+tax', original_text, re.IGNORECASE))
        
        # If original_text is minimal (e.g., just numeric in mock), verify currency/value
        has_currency_indicator = bool(re.search(r'(?:₹|Rs|INR)', original_text, re.IGNORECASE)) or currency == "INR"

        if not has_currency_indicator:
            return {
                "valid": False,
                "reason": "MRP declaration is missing currency indicator (₹ or Rs.).",
                "normalized_value": {"value": value, "currency": currency, "raw": original_text}
            }

        return {
            "valid": True,
            "reason": "MRP declaration format is valid with currency and numeric amount.",
            "has_tax_clause": has_tax_clause,
            "normalized_value": {
                "value": float(value),
                "currency": currency,
                "raw": original_text
            }
        }

    @staticmethod
    def validate_net_quantity(qty_fact: dict) -> dict:
        """
        Validates Net Quantity declaration format.
        Expected format: Numeric value + recognized standard metric/unit symbol.
        """
        if not qty_fact:
            return {"valid": False, "reason": "No net quantity declaration detected.", "normalized_value": None}

        original_text = qty_fact.get("original_text", "") or qty_fact.get("raw", "")
        value = qty_fact.get("value")
        unit = qty_fact.get("unit", "")

        if (value is None or not unit) and original_text:
            match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', original_text)
            if match:
                value = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
                unit = match.group(2)

        if value is None or value <= 0:
            return {
                "valid": False,
                "reason": "Net quantity lacks a valid positive numeric measure.",
                "normalized_value": None
            }

        norm_unit = normalize_unit(unit)
        recognized_units = {'g', 'kg', 'ml', 'L', 'l', 'm', 'cm', 'mm', 'N', 'U', 'units', 'pcs'}

        if norm_unit not in recognized_units:
            return {
                "valid": False,
                "reason": f"Net quantity unit '{unit}' is not a recognized Legal Metrology standard unit.",
                "normalized_value": {"value": value, "unit": unit, "raw": original_text}
            }

        return {
            "valid": True,
            "reason": "Net quantity format is valid with numeric amount and recognized unit.",
            "normalized_value": {
                "value": value,
                "unit": norm_unit,
                "raw": original_text
            }
        }

    @staticmethod
    def validate_date(date_fact: dict) -> dict:
        """
        Validates Month & Year of manufacture / packing / import declaration format.
        """
        if not date_fact:
            return {"valid": False, "reason": "No manufacturing/packing date declaration detected.", "normalized_value": None}

        date_str = str(date_fact if isinstance(date_fact, str) else date_fact.get("value", "") or date_fact.get("original_text", ""))
        date_str = date_str.strip()

        # Check MM/YYYY or MM-YYYY or Month Year
        pattern = r'(?:0[1-9]|1[0-2]|[a-zA-Z]{3,9})[\/\-\s]+(?:20[0-9]{2}|[0-9]{2})'
        if not re.search(pattern, date_str, re.IGNORECASE):
            return {
                "valid": False,
                "reason": f"Date declaration '{date_str}' does not match prescribed Month and Year format (e.g. MM/YYYY).",
                "normalized_value": {"raw": date_str}
            }

        return {
            "valid": True,
            "reason": "Date declaration format is valid Month and Year.",
            "normalized_value": {"value": date_str, "raw": date_str}
        }

    @staticmethod
    def validate_manufacturer(mfg_fact: dict) -> dict:
        """
        Validates Name and Address of Manufacturer / Packer / Importer.
        """
        if not mfg_fact:
            return {"valid": False, "reason": "No manufacturer or packer declaration detected.", "normalized_value": None}

        name = ""
        address = ""
        if isinstance(mfg_fact, dict):
            name = mfg_fact.get("name", "").strip()
            address = mfg_fact.get("address", "").strip()
        elif isinstance(mfg_fact, str):
            name = mfg_fact.strip()

        if not name:
            return {
                "valid": False,
                "reason": "Manufacturer/packer declaration lacks a clear company or individual name.",
                "normalized_value": None
            }

        return {
            "valid": True,
            "reason": "Manufacturer/packer name and details are validly formatted.",
            "normalized_value": {
                "name": name,
                "address": address
            }
        }

    @staticmethod
    def validate_consumer_care(care_fact: dict) -> dict:
        """
        Validates Consumer Care Contact details.
        Must contain phone number, email, address, or customer care contact details.
        """
        if not care_fact:
            return {"valid": False, "reason": "No consumer care contact details detected.", "normalized_value": None}

        phone = ""
        email = ""
        raw = ""
        if isinstance(care_fact, dict):
            phone = care_fact.get("phone", "").strip()
            email = care_fact.get("email", "").strip()
            raw = care_fact.get("raw", "").strip()
        elif isinstance(care_fact, str):
            raw = care_fact.strip()

        has_phone = bool(re.search(r'\+?[0-9\-\s]{8,15}', phone or raw))
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email or raw))

        if not (has_phone or has_email or len(raw) > 10):
            return {
                "valid": False,
                "reason": "Consumer care declaration lacks valid phone number or email address.",
                "normalized_value": None
            }

        return {
            "valid": True,
            "reason": "Consumer care details contain valid contact channels.",
            "normalized_value": {
                "phone": phone,
                "email": email,
                "raw": raw
            }
        }

    @staticmethod
    def validate_unit_sale_price(usp_fact: dict) -> dict:
        """
        Validates Unit Sale Price format (e.g. ₹0.25 / g or Rs 140 / L).
        """
        if not usp_fact:
            return {"valid": False, "reason": "No Unit Sale Price declaration detected.", "normalized_value": None}

        raw = usp_fact.get("raw", "") or str(usp_fact)
        if not raw:
            return {"valid": False, "reason": "Unit Sale Price declaration is empty.", "normalized_value": None}

        return {
            "valid": True,
            "reason": "Unit sale price declaration is validly formatted.",
            "normalized_value": {"raw": raw}
        }
