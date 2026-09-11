"""
Cross-Check Engine for LabelSure.
Compares OCR Image-derived facts against AI Product Enrichment information.
Generates informational consistency reports without altering legal compliance verdicts.
"""

import re

class CrossCheckEngine:
    @staticmethod
    def cross_check(detected_declarations: dict, enrichment_data: dict) -> dict:
        """
        Cross-checks OCR extracted facts against AI/Barcode enriched product facts.
        """
        if not enrichment_data or not enrichment_data.get("available"):
            return {
                "available": False,
                "reason": "Enrichment data not available for cross-checking",
                "details_consistent": None,
                "field_checks": []
            }

        enrichment = enrichment_data.get("enrichment", {})
        ocr_facts = detected_declarations or {}

        field_checks = []
        mismatches_count = 0
        matches_count = 0

        # Helper to extract value safely
        def get_ocr_val(key):
            v = ocr_facts.get(key)
            if isinstance(v, dict):
                return str(v.get("value", "") or v.get("name", "") or v.get("raw", "")).strip()
            return str(v or "").strip()

        # 1. Product Name Check
        ocr_product = get_ocr_val("commodity_name")
        enr_product = str(enrichment.get("product_name", "") or "").strip()
        if ocr_product and enr_product:
            match = ocr_product.lower() in enr_product.lower() or enr_product.lower() in ocr_product.lower()
            status = "CONSISTENT" if match else "MISMATCH"
            if not match: mismatches_count += 1
            else: matches_count += 1
            field_checks.append({
                "field": "Product Name",
                "status": status,
                "ocr_value": ocr_product,
                "enrichment_value": enr_product,
                "explanation": f"OCR product '{ocr_product}' is {'consistent with' if match else 'differs from'} AI enrichment '{enr_product}'."
            })

        # 2. Manufacturer Check
        ocr_mfg = get_ocr_val("manufacturer")
        enr_mfg = str(enrichment.get("manufacturer", "") or "").strip()
        if ocr_mfg and enr_mfg:
            # Check overlap in company name words
            ocr_words = set(ocr_mfg.lower().split())
            enr_words = set(enr_mfg.lower().split())
            overlap = ocr_words.intersection(enr_words)
            match = len(overlap) > 0 or ocr_mfg.lower() in enr_mfg.lower() or enr_mfg.lower() in ocr_mfg.lower()
            status = "CONSISTENT" if match else "MISMATCH"
            if not match: mismatches_count += 1
            else: matches_count += 1
            field_checks.append({
                "field": "Manufacturer Name",
                "status": status,
                "ocr_value": ocr_mfg,
                "enrichment_value": enr_mfg,
                "explanation": f"OCR manufacturer '{ocr_mfg}' is {'consistent with' if match else 'differs from'} AI enrichment '{enr_mfg}'."
            })

        # 3. Net Quantity / Pack Size Check
        ocr_qty = get_ocr_val("net_quantity")
        enr_size = str(enrichment.get("pack_size", "") or "").strip()
        if ocr_qty and enr_size:
            # Check numeric and unit overlap
            match = (ocr_qty.lower().replace(" ", "") in enr_size.lower().replace(" ", "") or
                     enr_size.lower().replace(" ", "") in ocr_qty.lower().replace(" ", ""))
            status = "CONSISTENT" if match else "MISMATCH"
            if not match: mismatches_count += 1
            else: matches_count += 1
            field_checks.append({
                "field": "Net Quantity / Pack Size",
                "status": status,
                "ocr_value": ocr_qty,
                "enrichment_value": enr_size,
                "explanation": f"OCR Net Quantity '{ocr_qty}' is {'consistent with' if match else 'differs from'} AI enrichment size '{enr_size}'."
            })

        details_consistent = mismatches_count == 0

        return {
            "available": True,
            "details_consistent": details_consistent,
            "mismatches_found": mismatches_count,
            "matches_found": matches_count,
            "field_checks": field_checks,
            "note": "Cross-check results provide informational consistency analysis and do NOT alter the deterministic Legal Metrology compliance verdict."
        }

    @staticmethod
    def cross_check_ocr_providers(openai_facts: dict, tesseract_facts: dict) -> dict:
        """
        Compares declarations extracted by OpenAI Vision vs Tesseract Local OCR.
        If both agree on values (e.g. MRP ₹20), confidence is strengthened.
        If they disagree, records an explicit UNCERTAINTY state without concealing the conflict.
        """
        if not openai_facts or not tesseract_facts:
            return {
                "available": False,
                "reason": "Both OCR providers must be available to perform dual OCR verification.",
                "has_disagreement": False,
                "comparisons": []
            }

        openai_decls = openai_facts.get("declarations", {}) if isinstance(openai_facts, dict) else {}
        tess_decls = tesseract_facts.get("declarations", {}) if isinstance(tesseract_facts, dict) else {}

        comparisons = []
        agreed_count = 0
        disagree_count = 0

        # Helper to extract clean text/val
        def get_val(decl):
            if not decl: return None
            if isinstance(decl, dict):
                return decl.get("value") or decl.get("text") or decl.get("name") or decl.get("raw")
            return decl

        # 1. Maximum Retail Price (MRP)
        o_mrp = openai_decls.get("max_retail_price")
        t_mrp = tess_decls.get("max_retail_price")
        if o_mrp or t_mrp:
            o_val = o_mrp.get("value") if isinstance(o_mrp, dict) else None
            t_val = t_mrp.get("value") if isinstance(t_mrp, dict) else None
            o_raw = (o_mrp.get("raw") if isinstance(o_mrp, dict) else str(o_mrp)) if o_mrp else "Not detected"
            t_raw = (t_mrp.get("raw") if isinstance(t_mrp, dict) else str(t_mrp)) if t_mrp else "Not detected"

            if o_val is not None and t_val is not None:
                if abs(float(o_val) - float(t_val)) < 0.01:
                    status = "AGREED"
                    agreed_count += 1
                    explanation = f"Both OpenAI Vision and Tesseract detected matching MRP (₹{float(o_val):.2f}). Evidence strengthened."
                else:
                    status = "DISAGREEMENT"
                    disagree_count += 1
                    explanation = f"Uncertainty: Disagreement detected. OpenAI reported '₹{o_val}' while Tesseract reported '₹{t_val}'. Requires manual inspection."
            else:
                status = "SINGLE_PROVIDER"
                explanation = f"Detected by {'OpenAI' if o_mrp else 'Tesseract'} only. Second provider did not detect MRP."

            comparisons.append({
                "field": "Maximum Retail Price (MRP)",
                "status": status,
                "confidence_strengthened": status == "AGREED",
                "openai_value": o_raw,
                "tesseract_value": t_raw,
                "explanation": explanation
            })

        # 2. Net Quantity
        o_qty = openai_decls.get("net_quantity")
        t_qty = tess_decls.get("net_quantity")
        if o_qty or t_qty:
            o_val = o_qty.get("value") if isinstance(o_qty, dict) else None
            t_val = t_qty.get("value") if isinstance(t_qty, dict) else None
            o_unit = str(o_qty.get("unit", "")).lower() if isinstance(o_qty, dict) else ""
            t_unit = str(t_qty.get("unit", "")).lower() if isinstance(t_qty, dict) else ""
            o_raw = (o_qty.get("raw") if isinstance(o_qty, dict) else str(o_qty)) if o_qty else "Not detected"
            t_raw = (t_qty.get("raw") if isinstance(t_qty, dict) else str(t_qty)) if t_qty else "Not detected"

            if o_val is not None and t_val is not None:
                val_match = abs(float(o_val) - float(t_val)) < 0.01
                unit_match = o_unit == t_unit or (not o_unit) or (not t_unit)
                if val_match and unit_match:
                    status = "AGREED"
                    agreed_count += 1
                    explanation = f"Both OpenAI Vision and Tesseract detected matching Net Quantity ({o_val} {o_unit}). Evidence strengthened."
                else:
                    status = "DISAGREEMENT"
                    disagree_count += 1
                    explanation = f"Uncertainty: Disagreement detected. OpenAI reported '{o_raw}' while Tesseract reported '{t_raw}'."
            else:
                status = "SINGLE_PROVIDER"
                explanation = f"Detected by {'OpenAI' if o_qty else 'Tesseract'} only."

            comparisons.append({
                "field": "Net Quantity",
                "status": status,
                "confidence_strengthened": status == "AGREED",
                "openai_value": o_raw,
                "tesseract_value": t_raw,
                "explanation": explanation
            })

        # 3. Date of Manufacture
        o_date = openai_decls.get("date_of_manufacture")
        t_date = tess_decls.get("date_of_manufacture")
        if o_date or t_date:
            o_val = str(get_val(o_date) or "")
            t_val = str(get_val(t_date) or "")

            if o_val and t_val:
                match = o_val.replace(" ", "").lower() == t_val.replace(" ", "").lower() or (o_val in t_val) or (t_val in o_val)
                if match:
                    status = "AGREED"
                    agreed_count += 1
                    explanation = f"Both OpenAI Vision and Tesseract detected consistent manufacturing date ({o_val})."
                else:
                    status = "DISAGREEMENT"
                    disagree_count += 1
                    explanation = f"Uncertainty: Date mismatch between OpenAI ('{o_val}') and Tesseract ('{t_val}')."
            else:
                status = "SINGLE_PROVIDER"
                explanation = f"Detected by {'OpenAI' if o_val else 'Tesseract'} only."

            comparisons.append({
                "field": "Date of Manufacture",
                "status": status,
                "confidence_strengthened": status == "AGREED",
                "openai_value": o_val or "Not detected",
                "tesseract_value": t_val or "Not detected",
                "explanation": explanation
            })

        # 4. Manufacturer Name
        o_mfg = openai_decls.get("manufacturer")
        t_mfg = tess_decls.get("manufacturer")
        if o_mfg or t_mfg:
            o_name = str((o_mfg.get("name") if isinstance(o_mfg, dict) else o_mfg) or "").strip()
            t_name = str((t_mfg.get("name") if isinstance(t_mfg, dict) else t_mfg) or "").strip()

            if o_name and t_name:
                o_words = set(re.findall(r'\w+', o_name.lower()))
                t_words = set(re.findall(r'\w+', t_name.lower()))
                overlap = o_words.intersection(t_words)
                match = len(overlap) >= 1 or o_name.lower() in t_name.lower() or t_name.lower() in o_name.lower()
                if match:
                    status = "AGREED"
                    agreed_count += 1
                    explanation = f"Both providers identified consistent manufacturer '{o_name}'."
                else:
                    status = "DISAGREEMENT"
                    disagree_count += 1
                    explanation = f"Uncertainty: Manufacturer name differs between OpenAI ('{o_name}') and Tesseract ('{t_name}')."
            else:
                status = "SINGLE_PROVIDER"
                explanation = f"Detected by {'OpenAI' if o_name else 'Tesseract'} only."

            comparisons.append({
                "field": "Manufacturer Name",
                "status": status,
                "confidence_strengthened": status == "AGREED",
                "openai_value": o_name or "Not detected",
                "tesseract_value": t_name or "Not detected",
                "explanation": explanation
            })

        has_disagreement = disagree_count > 0
        overall = "AGREED" if (agreed_count > 0 and not has_disagreement) else ("DISAGREEMENT" if has_disagreement else "SINGLE_PROVIDER")

        return {
            "available": True,
            "providers_compared": ["OpenAI Vision", "Tesseract Local OCR"],
            "overall_status": overall,
            "has_disagreement": has_disagreement,
            "agreed_count": agreed_count,
            "disagreement_count": disagree_count,
            "comparisons": comparisons,
            "note": "Dual-OCR cross check provides transparent consistency auditing. Disagreements highlight uncertainty without discarding evidence."
        }

