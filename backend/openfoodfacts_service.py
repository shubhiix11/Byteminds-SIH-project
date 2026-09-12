"""
Open Food Facts Product-by-Barcode Service for LabelSure.
Queries the official Open Food Facts public API v3:
GET https://world.openfoodfacts.org/api/v3/product/{barcode}
to enrich packaging scans with community product data without altering
deterministic Legal Metrology compliance verdicts.
"""

import os
import re
import time
import requests
from datetime import datetime, timezone

OFF_API_V3_BASE_URL = "https://world.openfoodfacts.org/api/v3/product"
DEFAULT_USER_AGENT = "LabelSure/1.0 (https://labelsure.gov.in; legal-metrology@labelsure.gov.in)"

# Explicit requested fields for LabelSure (Section 4)
REQUESTED_FIELDS = (
    "product_name,"
    "product_name_en,"
    "generic_name,"
    "brands,"
    "categories,"
    "quantity,"
    "product_quantity,"
    "product_quantity_unit,"
    "packaging,"
    "ingredients_text,"
    "allergens,"
    "countries,"
    "labels,"
    "origins,"
    "manufacturing_places,"
    "nutriscore_grade,"
    "nutriscore_data,"
    "nutriments,"
    "image_front_url,"
    "image_ingredients_url,"
    "image_nutrition_url,"
    "stores,"
    "code"
)

# In-memory TTL cache: { barcode: { "timestamp": float, "status": str, "data": dict } }
_OFF_CACHE = {}
CACHE_TTL_FOUND_SEC = 3600      # 1 hour for found products
CACHE_TTL_NOT_FOUND_SEC = 300   # 5 minutes for not-found items


def _is_valid_barcode(barcode: str) -> bool:
    """Validates barcode format (alphanumeric, 3 to 48 characters, no URL injection characters)."""
    if not barcode or not isinstance(barcode, str):
        return False
    cleaned = barcode.strip()
    return bool(re.fullmatch(r'^[A-Za-z0-9\-_]{3,48}$', cleaned))


def _clean_str(val):
    """Returns stripped string or None if empty."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


class OpenFoodFactsService:
    def __init__(self, user_agent: str = None, timeout: int = 10):
        self.user_agent = user_agent or os.getenv("OPENFOODFACTS_USER_AGENT", DEFAULT_USER_AGENT)
        self.timeout = timeout

    def get_product_by_barcode(
        self,
        barcode: str,
        bypass_cache: bool = False,
        product_type: str = "food",
        cc: str = "IN",
        lc: str = "en"
    ) -> dict:
        """
        Looks up a product in Open Food Facts API v3 by barcode.
        Never fabricates data. Returns status:
        - NO_BARCODE: Barcode was null or empty
        - INVALID_BARCODE: Barcode format was invalid
        - FOUND: Product found in Open Food Facts with non-empty product object
        - NOT_FOUND: Barcode detected, but not in Open Food Facts (HTTP 404 or product not found)
        - UNAVAILABLE: Open Food Facts API unreachable, timed out, rate limited (429), or 5xx
        """
        if not barcode or not str(barcode).strip():
            return {
                "available": False,
                "status": "NO_BARCODE",
                "barcode": None,
                "source": "OPEN_FOOD_FACTS",
                "message": "Barcode not detected"
            }

        barcode_str = str(barcode).strip()
        if not _is_valid_barcode(barcode_str):
            return {
                "available": False,
                "status": "INVALID_BARCODE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "message": f"Invalid barcode format: {barcode_str}"
            }

        now = time.time()
        # In-memory cache check
        if not bypass_cache and barcode_str in _OFF_CACHE:
            entry = _OFF_CACHE[barcode_str]
            ttl = CACHE_TTL_FOUND_SEC if entry.get("status") == "FOUND" else CACHE_TTL_NOT_FOUND_SEC
            if now - entry["timestamp"] < ttl:
                cached_data = dict(entry["data"])
                cached_data["cached"] = True
                return cached_data

        source_url = f"https://world.openfoodfacts.org/product/{barcode_str}"
        endpoint_url = f"{OFF_API_V3_BASE_URL}/{barcode_str}"

        params = {
            "fields": REQUESTED_FIELDS,
            "cc": cc or "IN",
            "lc": lc or "en"
        }
        if product_type:
            params["product_type"] = product_type

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }

        try:
            response = requests.get(
                endpoint_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as timeout_err:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Open Food Facts service timed out.",
                "error": str(timeout_err)
            }
        except (requests.exceptions.ConnectionError, requests.RequestException, Exception) as net_err:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Open Food Facts service is currently unavailable.",
                "error": str(net_err)
            }

        # Handle rate limiting (429) and server errors (5xx)
        if response.status_code == 429:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Open Food Facts rate limit exceeded (HTTP 429).",
                "http_status": 429
            }

        if response.status_code >= 500:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": f"Open Food Facts server error (HTTP {response.status_code}).",
                "http_status": response.status_code
            }

        # Documented HTTP 404 is NOT_FOUND
        if response.status_code == 404:
            result = {
                "available": False,
                "status": "NOT_FOUND",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Barcode detected, but this product was not found in Open Food Facts."
            }
            _OFF_CACHE[barcode_str] = {"timestamp": now, "status": "NOT_FOUND", "data": result}
            return result

        # Any non-200, non-404 code
        if response.status_code != 200:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": f"Open Food Facts returned unexpected HTTP status {response.status_code}.",
                "http_status": response.status_code
            }

        # Parse JSON
        try:
            payload = response.json()
        except Exception as json_err:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Failed to parse Open Food Facts JSON response.",
                "error": str(json_err)
            }

        # Response Detection Rule:
        # FOUND requires HTTP success and a usable non-empty "product" dictionary.
        # NOT_FOUND if payload indicates not found or product is missing/empty.
        product_raw = payload.get("product")
        has_usable_product = isinstance(product_raw, dict) and bool(product_raw)

        api_result_id = payload.get("result", {}).get("id") if isinstance(payload.get("result"), dict) else None
        api_status = payload.get("status")

        if not has_usable_product or api_result_id == "product_not_found" or api_status in [0, "failure", "product_not_found"]:
            result = {
                "available": False,
                "status": "NOT_FOUND",
                "barcode": barcode_str,
                "source": "OPEN_FOOD_FACTS",
                "source_url": source_url,
                "message": "Barcode detected, but this product was not found in Open Food Facts."
            }
            _OFF_CACHE[barcode_str] = {"timestamp": now, "status": "NOT_FOUND", "data": result}
            return result

        # Normalize product according to Section 4 & Section 3
        normalized_product = self._normalize_product(barcode_str, product_raw, source_url)

        result = {
            "available": True,
            "status": "FOUND",
            "source": "OPEN_FOOD_FACTS",
            "source_url": source_url,
            "barcode": barcode_str,
            "retrieved_at": datetime.now(timezone.utc).isoformat() + "Z",
            "disclaimer": "Product information retrieved from Open Food Facts. Open Food Facts is a community-maintained database.",
            "product": normalized_product,
            "raw": product_raw
        }

        # Cache found product
        _OFF_CACHE[barcode_str] = {"timestamp": now, "status": "FOUND", "data": result}
        return result

    def _normalize_product(self, barcode: str, p: dict, source_url: str) -> dict:
        """
        Parses all requested fields into clean application-level object.
        Uses null for unavailable fields. Never invents values.
        """
        nutriments_raw = p.get("nutriments") if isinstance(p.get("nutriments"), dict) else {}
        nutriments_clean = {}
        key_nutrients = [
            "energy-kcal_100g", "energy_100g", "fat_100g", "saturated-fat_100g",
            "carbohydrates_100g", "sugars_100g", "proteins_100g", "salt_100g", "sodium_100g", "fiber_100g"
        ]
        for k in key_nutrients:
            if k in nutriments_raw and nutriments_raw[k] is not None:
                nutriments_clean[k] = nutriments_raw[k]

        nutriscore_grade = _clean_str(p.get("nutriscore_grade"))
        if nutriscore_grade:
            nutriscore_grade = nutriscore_grade.upper()

        product_name = _clean_str(p.get("product_name")) or _clean_str(p.get("product_name_en"))
        product_name_en = _clean_str(p.get("product_name_en"))
        generic_name = _clean_str(p.get("generic_name"))
        brands = _clean_str(p.get("brands"))
        categories = _clean_str(p.get("categories"))
        quantity = _clean_str(p.get("quantity"))
        product_quantity = p.get("product_quantity")
        product_quantity_unit = _clean_str(p.get("product_quantity_unit"))
        packaging = _clean_str(p.get("packaging"))
        ingredients = _clean_str(p.get("ingredients_text"))
        allergens = _clean_str(p.get("allergens"))
        countries = _clean_str(p.get("countries"))
        labels = _clean_str(p.get("labels"))
        origins = _clean_str(p.get("origins"))
        manufacturing_places = _clean_str(p.get("manufacturing_places"))
        nutriscore_data = p.get("nutriscore_data") if isinstance(p.get("nutriscore_data"), dict) else None
        image_front_url = _clean_str(p.get("image_front_url"))
        image_front_small_url = _clean_str(p.get("image_front_small_url"))
        image_ingredients_url = _clean_str(p.get("image_ingredients_url"))
        image_nutrition_url = _clean_str(p.get("image_nutrition_url"))
        stores = _clean_str(p.get("stores"))
        code = _clean_str(p.get("code")) or barcode

        # Application-level normalized fields
        fields = {
            # Exact Section 4 field names:
            "name": product_name,
            "brand": brands,
            "category": categories,
            "quantity": quantity,
            "packaging": packaging,
            "ingredients": ingredients,
            "allergens": allergens,
            "countries": countries,
            "labels": labels,
            "nutriments": nutriments_clean if nutriments_clean else None,
            "nutriscore": nutriscore_grade,
            "image_url": image_front_url,

            # Section 3 & component compatibility aliases:
            "code": code,
            "product_name": product_name,
            "product_name_en": product_name_en,
            "generic_name": generic_name,
            "brands": brands,
            "categories": categories,
            "product_quantity": product_quantity,
            "product_quantity_unit": product_quantity_unit,
            "ingredients_text": ingredients,
            "nutriscore_grade": nutriscore_grade,
            "nutriscore_data": nutriscore_data,
            "origins": origins,
            "manufacturing_places": manufacturing_places,
            "stores": stores,
            "image_front_url": image_front_url,
            "image_front_small_url": image_front_small_url,
            "image_ingredients_url": image_ingredients_url,
            "image_nutrition_url": image_nutrition_url,
            "source": "OPEN_FOOD_FACTS",
            "source_url": source_url
        }

        # Field-level source attribution
        attributed_fields = {}
        for k, v in fields.items():
            if k not in ["source", "source_url"]:
                attributed_fields[k] = {
                    "value": v,
                    "source": "OPEN_FOOD_FACTS",
                    "available": v is not None
                }
        fields["attributed_fields"] = attributed_fields

        return fields

    @staticmethod
    def cross_check_with_ocr(detected_declarations: dict, off_data: dict) -> dict:
        """
        Compares Open Food Facts data with image OCR declarations.
        Does NOT overwrite image evidence.
        Does NOT alter Legal Metrology compliance verdicts.
        """
        if not off_data or not off_data.get("available") or off_data.get("status") != "FOUND":
            return {
                "available": False,
                "reason": "Open Food Facts product data not found or unavailable for cross-checking.",
                "details_consistent": None,
                "field_checks": []
            }

        product = off_data.get("product", {})
        ocr = detected_declarations or {}

        def get_ocr_val(key):
            v = ocr.get(key)
            if isinstance(v, dict):
                return str(v.get("value", "") or v.get("name", "") or v.get("raw", "")).strip()
            return str(v or "").strip()

        field_checks = []
        matches_count = 0
        mismatches_count = 0

        # 1. Product Name Comparison
        ocr_prod = get_ocr_val("commodity_name")
        off_prod = product.get("name") or product.get("product_name") or product.get("generic_name")
        if ocr_prod and off_prod:
            match = (ocr_prod.lower() in off_prod.lower() or off_prod.lower() in ocr_prod.lower())
            status = "MATCH" if match else "POSSIBLE MISMATCH"
            if match:
                matches_count += 1
            else:
                mismatches_count += 1
            field_checks.append({
                "field": "Product Name",
                "status": status,
                "ocr_value": ocr_prod,
                "off_value": off_prod,
                "explanation": f"Image OCR detected '{ocr_prod}', Open Food Facts lists '{off_prod}'."
            })
        elif off_prod and not ocr_prod:
            field_checks.append({
                "field": "Product Name",
                "status": "NOT IN OCR",
                "ocr_value": "Not detected",
                "off_value": off_prod,
                "explanation": f"Open Food Facts lists '{off_prod}', but commodity name was not visible in image OCR."
            })

        # 2. Brand / Manufacturer Comparison
        ocr_mfg = get_ocr_val("manufacturer")
        off_brand = product.get("brand") or product.get("brands") or product.get("manufacturing_places")
        if ocr_mfg and off_brand:
            ocr_words = set(re.findall(r'\w+', ocr_mfg.lower()))
            off_words = set(re.findall(r'\w+', off_brand.lower()))
            overlap = ocr_words.intersection(off_words)
            match = (len(overlap) > 0 or ocr_mfg.lower() in off_brand.lower() or off_brand.lower() in ocr_mfg.lower())
            status = "MATCH" if match else "POSSIBLE MISMATCH"
            if match:
                matches_count += 1
            else:
                mismatches_count += 1
            field_checks.append({
                "field": "Brand / Manufacturer",
                "status": status,
                "ocr_value": ocr_mfg,
                "off_value": off_brand,
                "explanation": f"Image OCR manufacturer '{ocr_mfg}' {'matches' if match else 'differs from'} Open Food Facts brand '{off_brand}'."
            })
        elif off_brand and not ocr_mfg:
            field_checks.append({
                "field": "Brand / Manufacturer",
                "status": "NOT IN OCR",
                "ocr_value": "Not detected",
                "off_value": off_brand,
                "explanation": f"Open Food Facts lists brand '{off_brand}', but manufacturer declaration was not detected in image."
            })

        # 3. Net Quantity / Pack Size Comparison
        ocr_qty = get_ocr_val("net_quantity")
        off_qty = product.get("quantity")
        if ocr_qty and off_qty:
            clean_ocr = re.sub(r'[\s\.\,]', '', ocr_qty.lower())
            clean_off = re.sub(r'[\s\.\,]', '', off_qty.lower())
            match = (clean_ocr in clean_off or clean_off in clean_ocr)
            status = "MATCH" if match else "POSSIBLE MISMATCH"
            if match:
                matches_count += 1
            else:
                mismatches_count += 1
            field_checks.append({
                "field": "Net Quantity",
                "status": status,
                "ocr_value": ocr_qty,
                "off_value": off_qty,
                "explanation": f"Image OCR Net Quantity '{ocr_qty}' {'matches' if match else 'differs from'} Open Food Facts size '{off_qty}'."
            })
        elif off_qty and not ocr_qty:
            field_checks.append({
                "field": "Net Quantity",
                "status": "NOT IN OCR",
                "ocr_value": "Not detected",
                "off_value": off_qty,
                "explanation": f"Open Food Facts lists quantity '{off_qty}', not detected in uploaded image surface."
            })

        # 4. Country of Origin Comparison
        ocr_country = get_ocr_val("country_of_origin")
        off_countries = product.get("countries")
        if ocr_country and off_countries:
            match = (ocr_country.lower() in off_countries.lower() or off_countries.lower() in ocr_country.lower())
            status = "MATCH" if match else "POSSIBLE MISMATCH"
            if match:
                matches_count += 1
            else:
                mismatches_count += 1
            field_checks.append({
                "field": "Country of Origin",
                "status": status,
                "ocr_value": ocr_country,
                "off_value": off_countries,
                "explanation": f"Image OCR country '{ocr_country}' {'matches' if match else 'differs from'} Open Food Facts countries '{off_countries}'."
            })

        details_consistent = (mismatches_count == 0) if field_checks else None

        return {
            "available": True,
            "details_consistent": details_consistent,
            "matches_found": matches_count,
            "mismatches_found": mismatches_count,
            "field_checks": field_checks,
            "note": "Cross-check results provide informational consistency analysis and do NOT alter the deterministic Legal Metrology compliance verdict."
        }


# Module-level convenience function as specified in Section 1
def get_product_by_barcode(
    barcode: str,
    bypass_cache: bool = False,
    product_type: str = "food",
    cc: str = "IN",
    lc: str = "en"
) -> dict:
    """
    Direct function interface for Open Food Facts v3 product lookup.
    """
    service = OpenFoodFactsService()
    return service.get_product_by_barcode(
        barcode=barcode,
        bypass_cache=bypass_cache,
        product_type=product_type,
        cc=cc,
        lc=lc
    )
