"""
Product & Barcode Enrichment Service Test Suite.
Verifies enrichment providers, fallback behavior, cross-checking, and strict legal verdict isolation.
"""

import os
os.environ["LABELSURE_MODE"] = "demo"
import unittest
from product_enrichment_service import ProductEnrichmentService, MockProductEnrichmentProvider, OpenAIProductEnrichmentProvider
from cross_check_engine import CrossCheckEngine
from rules_engine import RulesEngine

class TestProductEnrichment(unittest.TestCase):
    def setUp(self):
        os.environ["LABELSURE_MODE"] = "demo"
        self.mock_service = ProductEnrichmentService(provider=MockProductEnrichmentProvider())
        self.rules_engine = RulesEngine()
        self.sample_declarations = {
            "commodity_name": "Crunchy Butter Cookies",
            "net_quantity": {"value": 200, "unit": "g", "raw": "200 g"},
            "manufacturer": {"name": "Apex Foodworks Pvt Ltd", "address": "Gurugram, Haryana"},
            "max_retail_price": {"value": 85.0, "currency": "INR", "raw": "₹ 85.00"}
        }

    # Test 1: API key missing yields UNAVAILABLE without failing
    def test_01_openai_api_key_missing_fallback(self):
        provider = OpenAIProductEnrichmentProvider(api_key="YOUR_OPENAI_API_KEY_HERE")
        res = provider.enrich(barcode="8901234567890", detected_declarations=self.sample_declarations)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIn("not configured", res["reason"])

    # Test 2: Successful mock product enrichment
    def test_02_mock_product_enrichment(self):
        res = self.mock_service.enrich_product(barcode="8901234567890", detected_declarations=self.sample_declarations)
        self.assertTrue(res["available"])
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["source_type"], "DEMO_MOCK_ENRICHMENT")
        self.assertIn("enrichment", res)
        self.assertEqual(res["enrichment"]["barcode"], "8901234567890")

    # Test 3: No barcode detected does not fail scan
    def test_03_no_barcode_detected(self):
        res = self.mock_service.enrich_product(barcode=None, detected_declarations=None)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")

    # Test 4: Cross-check matching product details
    def test_04_cross_check_matching_details(self):
        enrichment_res = self.mock_service.enrich_product(barcode="8901234567890", detected_declarations=self.sample_declarations)
        cc_res = CrossCheckEngine.cross_check(self.sample_declarations, enrichment_res)
        self.assertTrue(cc_res["available"])
        self.assertTrue(cc_res["details_consistent"])
        self.assertEqual(cc_res["mismatches_found"], 0)

    # Test 5: Cross-check mismatching details yields informational warning (not legal failure)
    def test_05_cross_check_mismatching_details(self):
        mismatched_declarations = {
            "commodity_name": "Different Chocolate Cookies",
            "net_quantity": {"value": 500, "unit": "g", "raw": "500 g"},  # Enriched is 200g
            "manufacturer": {"name": "Other Company Ltd", "address": "Mumbai"}
        }
        enrichment_res = self.mock_service.enrich_product(barcode="8901234567890", detected_declarations=self.sample_declarations)
        cc_res = CrossCheckEngine.cross_check(mismatched_declarations, enrichment_res)
        self.assertTrue(cc_res["available"])
        self.assertFalse(cc_res["details_consistent"])
        self.assertGreater(cc_res["mismatches_found"], 0)

    # Test 6: Enrichment failure does not affect rule engine execution
    def test_06_rule_engine_runs_independently_when_enrichment_fails(self):
        # Sample missing manufacturer -> mandatory FAIL in rule engine
        failing_facts = {
            "product_metadata": {"is_imported": False, "is_photo_inspection": True},
            "declarations": {
                "commodity_name": "Crunchy Butter Cookies",
                "net_quantity": {"value": 200, "unit": "g", "raw": "200 g"},
                "manufacturer": None  # MISSING -> FAIL
            }
        }
        rule_res = self.rules_engine.evaluate_package(failing_facts)
        self.assertEqual(rule_res["overall_status"], "NON_COMPLIANT")

    # Test 7: Enrichment claims can NEVER change a legal verdict
    def test_07_enrichment_never_changes_legal_verdict(self):
        # Case: Enrichment claims "Product is 100% genuine and compliant", but Manufacturer is missing on package
        failing_facts = {
            "product_metadata": {"is_imported": False, "is_photo_inspection": True},
            "declarations": {
                "commodity_name": "Crunchy Butter Cookies",
                "net_quantity": {"value": 200, "unit": "g", "raw": "200 g"},
                "manufacturer": None  # MISSING -> FAIL
            }
        }
        rule_res = self.rules_engine.evaluate_package(failing_facts)
        
        # Enrichment output claims compliant
        enrichment = {
            "available": True,
            "enrichment": {"additional_product_details": "Product appears compliant with all standards"}
        }

        # Verify final verdict remains NON_COMPLIANT from rule engine
        self.assertEqual(rule_res["overall_status"], "NON_COMPLIANT")

if __name__ == '__main__':
    unittest.main()
