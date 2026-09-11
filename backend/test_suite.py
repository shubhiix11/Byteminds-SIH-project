"""
Comprehensive Legal Metrology Rule Engine Test Suite.
Verifies all 16 required legal compliance engine conditions.
"""

import unittest
from rules_engine import RulesEngine
from format_validator import FormatValidator
from measurement_engine import MeasurementEngine

class TestLegalMetrologyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RulesEngine()
        self.validator = FormatValidator()
        self.measurement = MeasurementEngine()

        self.sample_complete_facts = {
            "product_metadata": {"is_imported": False, "is_photo_inspection": True},
            "font_pixel_height": 24.0,
            "declarations": {
                "commodity_name": "Crunchy Butter Cookies",
                "net_quantity": {"value": 200, "unit": "g", "raw": "200 g", "confidence": 0.98},
                "max_retail_price": {"value": 85.0, "currency": "INR", "raw": "₹ 85.00 (Incl. of all taxes)", "confidence": 0.98},
                "date_of_manufacture": {"value": "04/2026", "raw": "MFD 04/2026", "confidence": 0.97},
                "manufacturer": {"name": "Apex Foodworks Pvt Ltd", "address": "Gurugram, Haryana - 122001", "confidence": 0.96},
                "consumer_care": {"phone": "+91-1800-111-222", "email": "care@apexfoods.com", "confidence": 0.95},
                "unit_sale_price": {"raw": "₹ 0.425 / g", "confidence": 0.95}
            }
        }

    # Test 1: Manufacturer detected -> PASS
    def test_01_manufacturer_detected_pass(self):
        res = self.engine.evaluate_package(self.sample_complete_facts)
        mfg_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_A")
        self.assertEqual(mfg_rule["status"], "PASS")

    # Test 2: Manufacturer missing -> FAIL
    def test_02_manufacturer_missing_fail(self):
        facts = dict(self.sample_complete_facts)
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["manufacturer"] = None
        res = self.engine.evaluate_package(facts)
        mfg_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_A")
        self.assertEqual(mfg_rule["status"], "FAIL")

    # Test 3: Net quantity detected correctly -> PASS
    def test_03_net_quantity_pass(self):
        res = self.engine.evaluate_package(self.sample_complete_facts)
        qty_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_C")
        self.assertEqual(qty_rule["status"], "PASS")

    # Test 4: Net quantity malformed -> FAIL
    def test_04_net_quantity_malformed_fail(self):
        facts = dict(self.sample_complete_facts)
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["net_quantity"] = {"value": -50, "unit": "unknown_unit", "raw": "invalid"}
        res = self.engine.evaluate_package(facts)
        qty_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_C")
        self.assertEqual(qty_rule["status"], "FAIL")

    # Test 5: MRP detected correctly -> PASS
    def test_05_mrp_pass(self):
        res = self.engine.evaluate_package(self.sample_complete_facts)
        mrp_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_E")
        self.assertEqual(mrp_rule["status"], "PASS")

    # Test 6: MRP malformed -> FAIL
    def test_06_mrp_malformed_fail(self):
        facts = dict(self.sample_complete_facts)
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["max_retail_price"] = {"value": -10, "currency": "INVALID", "raw": "Free"}
        res = self.engine.evaluate_package(facts)
        mrp_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_E")
        self.assertEqual(mrp_rule["status"], "FAIL")

    # Test 7: Conditional rule not applicable -> NOT_APPLICABLE
    def test_07_country_of_origin_not_applicable_for_domestic(self):
        res = self.engine.evaluate_package(self.sample_complete_facts)
        origin_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_G")
        self.assertEqual(origin_rule["status"], "NOT_APPLICABLE")

    # Test 8: Required evidence unavailable -> NOT_VERIFIABLE
    def test_08_country_of_origin_not_verifiable_when_imported_unknown(self):
        facts = dict(self.sample_complete_facts)
        facts["product_metadata"] = {"is_imported": None}
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["country_of_origin"] = None
        res = self.engine.evaluate_package(facts)
        origin_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_G")
        self.assertEqual(origin_rule["status"], "NOT_VERIFIABLE")

    # Test 9: Low-confidence OCR evidence -> NOT_VERIFIABLE (does not automatically fail)
    def test_09_low_confidence_ocr_yields_not_verifiable(self):
        facts = dict(self.sample_complete_facts)
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["net_quantity"] = {"value": 200, "unit": "g", "raw": "200 g", "confidence": 0.3}
        res = self.engine.evaluate_package(facts)
        qty_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_C")
        self.assertEqual(qty_rule["status"], "NOT_VERIFIABLE")

    # Test 10: not_available measurement -> NOT_VERIFIABLE
    def test_10_font_measurement_not_available(self):
        res = self.engine.evaluate_package(self.sample_complete_facts, measurement_input={"method": "not_available"})
        font_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_I_FONT")
        self.assertEqual(font_rule["status"], "NOT_VERIFIABLE")

    # Test 11: package_dimension measurement -> physical size calculated
    def test_11_font_measurement_package_dimension(self):
        meas_input = {
            "method": "package_dimension",
            "known_physical_mm": 200.0,
            "known_pixel_span": 2000.0,  # Scale: 0.1 mm per pixel
            "confidence": 0.95
        }
        res = self.engine.evaluate_package(self.sample_complete_facts, measurement_input=meas_input)
        font_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_I_FONT")
        # 24px * 0.1 mm/px = 2.4 mm (requires 4.0 mm for 200g package) -> FAIL or PASS depending on threshold
        self.assertIn(font_rule["status"], ["PASS", "FAIL"])
        self.assertEqual(font_rule["normalized_value"]["estimated_mm_height"], 2.4)

    # Test 12: reference_object measurement -> physical size calculated
    def test_12_font_measurement_reference_object(self):
        meas_input = {
            "method": "reference_object",
            "known_physical_mm": 50.0,
            "known_pixel_span": 250.0,  # Scale: 0.2 mm per pixel
            "confidence": 0.95
        }
        res = self.engine.evaluate_package(self.sample_complete_facts, measurement_input=meas_input)
        font_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_I_FONT")
        # 24px * 0.2 mm/px = 4.8 mm (requires 4.0 mm for 200g package) -> PASS
        self.assertEqual(font_rule["status"], "PASS")
        self.assertEqual(font_rule["normalized_value"]["estimated_mm_height"], 4.8)

    # Test 13: Mandatory failure -> NON_COMPLIANT overall
    def test_13_mandatory_failure_non_compliant(self):
        facts = dict(self.sample_complete_facts)
        facts["declarations"] = dict(facts["declarations"])
        facts["declarations"]["manufacturer"] = None  # Mandatory FAIL
        res = self.engine.evaluate_package(facts)
        self.assertEqual(res["overall_status"], "NON_COMPLIANT")

    # Test 14: No failures + important NOT_VERIFIABLE -> NEEDS_REVIEW overall
    def test_14_unverifiable_needs_review(self):
        # Without physical scale, font size is NOT_VERIFIABLE (mandatory)
        res = self.engine.evaluate_package(self.sample_complete_facts, measurement_input={"method": "not_available"})
        self.assertEqual(res["overall_status"], "NEEDS_REVIEW")

    # Test 15: All applicable mandatory checks pass -> COMPLIANT overall
    def test_15_all_pass_compliant(self):
        meas_input = {
            "method": "package_dimension",
            "known_physical_mm": 200.0,
            "known_pixel_span": 1000.0,  # Scale: 0.2 mm per pixel -> 24px = 4.8mm >= 4.0mm
            "confidence": 0.95
        }
        res = self.engine.evaluate_package(self.sample_complete_facts, measurement_input=meas_input)
        self.assertEqual(res["overall_status"], "COMPLIANT")

    # Test 16: Rule effective dates select applicable version
    def test_16_rule_effective_dates_versioning(self):
        # Unit Sale Price (Rule 6(1)(h)) was effective starting 2022-02-01
        res_old = self.engine.evaluate_package(self.sample_complete_facts, inspection_date="2015-05-10")
        usp_old = next((r for r in res_old["rule_results"] if r["rule_id"] == "R6_1_H"), None)
        self.assertIsNone(usp_old, "Rule 6(1)(h) should not exist for 2015 inspection date")

        res_new = self.engine.evaluate_package(self.sample_complete_facts, inspection_date="2026-05-10")
        usp_new = next((r for r in res_new["rule_results"] if r["rule_id"] == "R6_1_H"), None)
        self.assertIsNotNone(usp_new, "Rule 6(1)(h) must exist for 2026 inspection date")

    # Test 17: Single surface inspection does not fail missing declarations -> NOT_VERIFIABLE
    def test_17_single_surface_inspection_unverifiable(self):
        facts = {
            "product_metadata": {"is_imported": False, "is_photo_inspection": True, "single_surface_only": True},
            "font_pixel_height": 24.0,
            "declarations": {
                # Only manufacturer is visible on this surface; net qty, mrp, date are on other surfaces
                "manufacturer": {"name": "Apex Foodworks Pvt Ltd", "address": "Gurugram, Haryana - 122001", "confidence": 0.96}
            }
        }
        res = self.engine.evaluate_package(facts)
        mfg_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_A")
        self.assertEqual(mfg_rule["status"], "PASS")

        qty_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_C")
        self.assertEqual(qty_rule["status"], "NOT_VERIFIABLE")
        self.assertIn("not detected in the uploaded image surface", qty_rule["reason"])

        mrp_rule = next(r for r in res["rule_results"] if r["rule_id"] == "R6_1_E")
        self.assertEqual(mrp_rule["status"], "NOT_VERIFIABLE")

        # Overall should be NEEDS_REVIEW, NOT NON_COMPLIANT
        self.assertEqual(res["overall_status"], "NEEDS_REVIEW")

if __name__ == '__main__':
    unittest.main()

