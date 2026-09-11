"""
Deterministic Legal Metrology (Packaged Commodities) Rule Engine.
Evaluates normalized candidate declarations against versioned rules.
"""

from datetime import datetime
from legal_rules import LEGAL_METROLOGY_RULES, get_rules_for_date
from format_validator import FormatValidator
from measurement_engine import MeasurementEngine

RULE_SET_VERSION = "2026.1-PC-RULES"

class RulesEngine:
    def __init__(self):
        self.validator = FormatValidator()
        self.measurement_engine = MeasurementEngine()

    def evaluate_package(self, product_facts: dict, inspection_date: str = None, measurement_input: dict = None) -> dict:
        """
        Main entry point for evaluating package declarations against Legal Metrology rules.
        """
        if not inspection_date:
            inspection_date = datetime.utcnow().strftime("%Y-%m-%d")

        # 1. Filter rules effective as of inspection_date
        effective_rules = get_rules_for_date(inspection_date)

        declarations = product_facts.get("declarations", {})
        product_meta = product_facts.get("product_metadata", {})
        
        is_imported = product_meta.get("is_imported")
        is_photo_inspection = product_meta.get("is_photo_inspection", True)
        single_surface_only = product_meta.get("single_surface_only", False)
        ocr_failure = product_meta.get("ocr_failure", False)

        rule_results = []
        passed_count = 0
        failed_count = 0
        warning_count = 0
        not_verifiable_count = 0
        not_applicable_count = 0

        # Extract candidates
        mfg_fact = declarations.get("manufacturer")
        commodity_fact = declarations.get("commodity_name")
        qty_fact = declarations.get("net_quantity")
        date_fact = declarations.get("date_of_manufacture")
        mrp_fact = declarations.get("max_retail_price")
        care_fact = declarations.get("consumer_care")
        origin_fact = declarations.get("country_of_origin")
        usp_fact = declarations.get("unit_sale_price")

        for rule in effective_rules:
            rule_id = rule["rule_id"]
            val_type = rule["validation_type"]
            mandatory = rule["mandatory"]

            status = "NOT_VERIFIABLE"
            reason = ""
            detected_text = None
            normalized_value = None
            confidence = None
            bbox = None

            # --- APPLICABILITY CHECKS ---
            
            # E-Commerce filter check (Rule 6(10))
            if val_type == "ECOMMERCE_FILTER":
                if is_photo_inspection:
                    status = "NOT_APPLICABLE"
                    reason = "E-Commerce digital search filter rules are platform software requirements, not verifiable from physical package photograph."
                    not_applicable_count += 1
                    rule_results.append(self._build_result(rule, status, detected_text, normalized_value, confidence, bbox, reason))
                    continue

            # Country of origin check (Rule 6(1)(g))
            if val_type == "COUNTRY_OF_ORIGIN":
                if is_imported is False:
                    status = "NOT_APPLICABLE"
                    reason = "Country of origin declaration is mandatory only for imported products under Rule 6(1)(g)."
                    not_applicable_count += 1
                    rule_results.append(self._build_result(rule, status, detected_text, normalized_value, confidence, bbox, reason))
                    continue
                elif is_imported is None and not origin_fact:
                    # Missing indicator on whether product is imported
                    status = "NOT_VERIFIABLE"
                    reason = "Cannot establish whether commodity is imported to evaluate Rule 6(1)(g) applicability."
                    not_verifiable_count += 1
                    rule_results.append(self._build_result(rule, status, detected_text, normalized_value, confidence, bbox, reason))
                    continue

            # Unit Sale Price check (Rule 6(1)(h))
            if val_type == "UNIT_SALE_PRICE":
                net_val = qty_fact.get("value") if isinstance(qty_fact, dict) else None
                net_unit = qty_fact.get("unit") if isinstance(qty_fact, dict) else None
                # Check if USP applies (> 1g/1ml or multi-unit)
                if net_val and net_val <= 1 and net_unit in ['g', 'ml']:
                    status = "NOT_APPLICABLE"
                    reason = "Unit Sale Price declaration is not applicable for packages of 1g or 1ml or smaller under Rule 6(1)(h)."
                    not_applicable_count += 1
                    rule_results.append(self._build_result(rule, status, detected_text, normalized_value, confidence, bbox, reason))
                    continue

            # --- EVALUATION LOGIC BY VALIDATION TYPE ---

            if val_type == "MANUFACTURER_DECLARATION":
                if not mfg_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory declaration of Manufacturer / Packer / Importer name and address is missing."
                else:
                    conf = mfg_fact.get("confidence", 0.95) if isinstance(mfg_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Manufacturer declaration detected with low OCR confidence ({conf:.2f}). Needs manual review."
                    else:
                        v_res = self.validator.validate_manufacturer(mfg_fact)
                        status = "PASS" if v_res["valid"] else "FAIL"
                        reason = v_res["reason"]
                        normalized_value = v_res["normalized_value"]
                        detected_text = str(mfg_fact)
                        confidence = conf

            elif val_type == "COMMODITY_NAME":
                if not commodity_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory generic or common commodity name is missing."
                else:
                    conf = 0.95
                    if isinstance(commodity_fact, dict):
                        conf = commodity_fact.get("confidence", 0.95)
                        detected_text = commodity_fact.get("original_text", "") or commodity_fact.get("raw", "")
                    else:
                        detected_text = str(commodity_fact)

                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Commodity name detected with low OCR confidence ({conf:.2f})."
                    elif len(detected_text.strip()) > 1:
                        status = "PASS"
                        reason = "Common or generic commodity name declaration is present."
                        normalized_value = {"name": detected_text.strip()}
                        confidence = conf
                    else:
                        status = "FAIL"
                        reason = "Commodity name declaration is blank or invalid."

            elif val_type == "NET_QUANTITY":
                if not qty_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Net Quantity declaration is missing."
                else:
                    conf = qty_fact.get("confidence", 0.95) if isinstance(qty_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Net Quantity detected with low OCR confidence ({conf:.2f})."
                    else:
                        v_res = self.validator.validate_net_quantity(qty_fact if isinstance(qty_fact, dict) else {"raw": str(qty_fact)})
                        status = "PASS" if v_res["valid"] else "FAIL"
                        reason = v_res["reason"]
                        normalized_value = v_res["normalized_value"]
                        detected_text = qty_fact.get("raw") if isinstance(qty_fact, dict) else str(qty_fact)
                        confidence = conf

            elif val_type == "DATE_DECLARATION":
                if not date_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Month & Year of manufacture / packing / import is missing."
                else:
                    conf = date_fact.get("confidence", 0.95) if isinstance(date_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Manufacturing date detected with low OCR confidence ({conf:.2f})."
                    else:
                        v_res = self.validator.validate_date(date_fact)
                        status = "PASS" if v_res["valid"] else "FAIL"
                        reason = v_res["reason"]
                        normalized_value = v_res["normalized_value"]
                        detected_text = str(date_fact)
                        confidence = conf

            elif val_type == "MRP_DECLARATION":
                if not mrp_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Maximum Retail Price (MRP) declaration is missing."
                else:
                    conf = mrp_fact.get("confidence", 0.95) if isinstance(mrp_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"MRP declaration detected with low OCR confidence ({conf:.2f})."
                    else:
                        v_res = self.validator.validate_mrp(mrp_fact if isinstance(mrp_fact, dict) else {"raw": str(mrp_fact)})
                        status = "PASS" if v_res["valid"] else "FAIL"
                        reason = v_res["reason"]
                        normalized_value = v_res["normalized_value"]
                        detected_text = mrp_fact.get("raw") if isinstance(mrp_fact, dict) else str(mrp_fact)
                        confidence = conf

            elif val_type == "CONSUMER_CARE":
                if not care_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Consumer Care contact details (phone / email / address) are missing."
                else:
                    conf = care_fact.get("confidence", 0.95) if isinstance(care_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Consumer care details detected with low OCR confidence ({conf:.2f})."
                    else:
                        v_res = self.validator.validate_consumer_care(care_fact)
                        status = "PASS" if v_res["valid"] else "FAIL"
                        reason = v_res["reason"]
                        normalized_value = v_res["normalized_value"]
                        detected_text = str(care_fact)
                        confidence = conf

            elif val_type == "COUNTRY_OF_ORIGIN":
                if not origin_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Country of Origin declaration for imported product is missing."
                else:
                    conf = origin_fact.get("confidence", 0.95) if isinstance(origin_fact, dict) else 0.95
                    if conf < 0.5:
                        status = "NOT_VERIFIABLE"
                        reason = f"Country of origin detected with low OCR confidence ({conf:.2f})."
                    else:
                        status = "PASS"
                        reason = f"Country of origin declared as '{origin_fact if isinstance(origin_fact, str) else origin_fact.get('value')}'."
                        normalized_value = {"country": origin_fact if isinstance(origin_fact, str) else origin_fact.get("value")}
                        detected_text = str(origin_fact)
                        confidence = conf

            elif val_type == "UNIT_SALE_PRICE":
                if not usp_fact:
                    if ocr_failure:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VERIFIABLE_OCR_FAILURE: OCR could not extract reliable text from uploaded image."
                    elif single_surface_only:
                        status = "NOT_VERIFIABLE"
                        reason = "NOT_VISIBLE_IN_UPLOADED_SURFACE: The declaration was not detected in the uploaded image."
                    else:
                        status = "FAIL"
                        reason = "Mandatory Unit Sale Price declaration is missing for package."
                else:
                    v_res = self.validator.validate_unit_sale_price(usp_fact if isinstance(usp_fact, dict) else {"raw": str(usp_fact)})
                    status = "PASS" if v_res["valid"] else "FAIL"
                    reason = v_res["reason"]
                    normalized_value = v_res["normalized_value"]
                    detected_text = str(usp_fact)
                    confidence = 0.95

            elif val_type == "CHARACTER_HEIGHT":
                net_val = qty_fact.get("value") if isinstance(qty_fact, dict) else 100
                net_unit = qty_fact.get("unit") if isinstance(qty_fact, dict) else "g"
                req_mm = self.measurement_engine.get_required_font_size_mm(net_val, net_unit)
                
                px_height = product_facts.get("font_pixel_height", 24.0)
                m_res = self.measurement_engine.evaluate_character_height(px_height, measurement_input, req_mm)
                
                status = m_res["status"]
                reason = m_res["reason"]
                normalized_value = {
                    "pixel_height": m_res.get("pixel_height", px_height),
                    "estimated_mm_height": m_res.get("estimated_mm_height"),
                    "required_mm_height": m_res.get("required_mm_height", req_mm),
                    "method": m_res.get("measurement_method", "not_available")
                }
                confidence = m_res.get("measurement_confidence", 0.0)

            # Tally counts
            if status == "PASS":
                passed_count += 1
            elif status == "FAIL":
                failed_count += 1
            elif status == "WARNING":
                warning_count += 1
            elif status == "NOT_VERIFIABLE":
                not_verifiable_count += 1
            elif status == "NOT_APPLICABLE":
                not_applicable_count += 1

            rule_results.append(self._build_result(rule, status, detected_text, normalized_value, confidence, bbox, reason))

        # --- OVERALL PRODUCT STATUS DETERMINATION ---
        # NON_COMPLIANT: At least one applicable mandatory check = FAIL
        # NEEDS_REVIEW: No mandatory check fails, but at least one applicable mandatory check is NOT_VERIFIABLE
        # COMPLIANT: All applicable mandatory checks = PASS
        
        mandatory_fails = [r for r in rule_results if r["mandatory"] and r["status"] == "FAIL"]
        mandatory_unverifiable = [r for r in rule_results if r["mandatory"] and r["status"] == "NOT_VERIFIABLE"]

        if len(mandatory_fails) > 0:
            overall_status = "NON_COMPLIANT"
        elif len(mandatory_unverifiable) > 0:
            overall_status = "NEEDS_REVIEW"
        else:
            overall_status = "COMPLIANT"

        return {
            "overall_status": overall_status,
            "summary": {
                "rules_checked": len(rule_results),
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
                "not_verifiable": not_verifiable_count,
                "not_applicable": not_applicable_count
            },
            "rule_results": rule_results,
            "rule_set_version": RULE_SET_VERSION,
            "inspection_date": inspection_date
        }

    def _build_result(self, rule: dict, status: str, text: str, norm_val: dict, conf: float, bbox: list, reason: str) -> dict:
        return {
            "rule_id": rule["rule_id"],
            "rule_number": rule["rule_number"],
            "title": rule["title"],
            "mandatory": rule["mandatory"],
            "status": status,  # PASS | FAIL | WARNING | NOT_VERIFIABLE | NOT_APPLICABLE
            "detected_text": text,
            "normalized_value": norm_val,
            "confidence": conf,
            "bbox": bbox,
            "reason": reason,
            "source_title": rule["source_title"],
            "source_reference": rule["source_reference"]
        }
