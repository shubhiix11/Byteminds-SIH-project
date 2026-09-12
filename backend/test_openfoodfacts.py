"""
Comprehensive test suite for LabelSure Open Food Facts Barcode Lookup integration.
Validates:
1. Valid barcode request
2. Product found
3. Product not found
4. Invalid barcode
5. API unavailable
6. No barcode
7. Returned data normalization
8. Source attribution
9. OCR / Open Food Facts cross-check mismatch
10. Open Food Facts failure does not break compliance scan
"""

import unittest
from unittest.mock import patch, MagicMock
import requests

from openfoodfacts_service import OpenFoodFactsService
from rules_engine import RulesEngine


class TestOpenFoodFactsIntegration(unittest.TestCase):

    def setUp(self):
        self.service = OpenFoodFactsService(user_agent="LabelSure/1.0 (test-suite)")

    # 1. Valid barcode request
    @patch('openfoodfacts_service.requests.get')
    def test_01_valid_barcode_request(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": 1,
            "product": {
                "code": "8901491001809",
                "product_name": "Lay's Sizzlin Hot",
                "brands": "Lay's"
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertTrue(res["available"])
        self.assertEqual(res["status"], "FOUND")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("8901491001809", args[0])
        self.assertEqual(kwargs["headers"]["User-Agent"], "LabelSure/1.0 (test-suite)")

    # 2. Product found
    @patch('openfoodfacts_service.requests.get')
    def test_02_product_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": 1,
            "product": {
                "code": "8906020461239",
                "product_name": "Crem Treat",
                "brands": "Britannia",
                "categories": "Biscuits",
                "quantity": "60g",
                "nutriscore_grade": "d",
                "nutriments": {
                    "energy-kcal_100g": 480,
                    "fat_100g": 20.0
                }
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8906020461239", bypass_cache=True)
        self.assertEqual(res["status"], "FOUND")
        self.assertTrue(res["available"])
        prod = res["product"]
        self.assertEqual(prod["product_name"], "Crem Treat")
        self.assertEqual(prod["brands"], "Britannia")
        self.assertEqual(prod["quantity"], "60g")
        self.assertEqual(prod["nutriscore_grade"], "D")
        self.assertEqual(prod["nutriments"]["energy-kcal_100g"], 480)

    # 3. Product not found
    @patch('openfoodfacts_service.requests.get')
    def test_03_product_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": 0,
            "status_verbose": "product not found"
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901491100328", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "NOT_FOUND")
        self.assertEqual(res["barcode"], "8901491100328")
        self.assertIn("not found in Open Food Facts", res["message"])

    # 4. Invalid barcode
    def test_04_invalid_barcode(self):
        # SQL/path traversal or invalid characters
        invalid_barcodes = ["../../etc/passwd", "123$#@!", "ab", "   ", ""]
        for b in invalid_barcodes:
            if not b.strip():
                res = self.service.get_product_by_barcode(b, bypass_cache=True)
                self.assertEqual(res["status"], "NO_BARCODE")
            else:
                res = self.service.get_product_by_barcode(b, bypass_cache=True)
                self.assertEqual(res["status"], "INVALID_BARCODE")
                self.assertFalse(res["available"])

    # 5. API unavailable
    @patch('openfoodfacts_service.requests.get')
    def test_05_api_unavailable(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIn("currently unavailable", res["message"])

    # 6. No barcode
    @patch('openfoodfacts_service.requests.get')
    def test_06_no_barcode(self, mock_get):
        res = self.service.get_product_by_barcode(None)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "NO_BARCODE")
        mock_get.assert_not_called()

        res2 = self.service.get_product_by_barcode("")
        self.assertFalse(res2["available"])
        self.assertEqual(res2["status"], "NO_BARCODE")
        mock_get.assert_not_called()

    # 7. Returned data normalization
    @patch('openfoodfacts_service.requests.get')
    def test_07_returned_data_normalization(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Minimal payload with many missing fields
        mock_resp.json.return_value = {
            "status": 1,
            "product": {
                "code": "8901234567890",
                "product_name": "Test Snack"
                # missing brands, allergens, ingredients_text, nutriscore, etc.
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901234567890", bypass_cache=True)
        prod = res["product"]
        self.assertEqual(prod["product_name"], "Test Snack")
        self.assertIsNone(prod["brands"])
        self.assertIsNone(prod["ingredients_text"])
        self.assertIsNone(prod["allergens"])
        self.assertIsNone(prod["nutriscore_grade"])
        self.assertIsNone(prod["nutriments"])
        self.assertIsNone(prod["image_front_url"])

    # 8. Source attribution
    @patch('openfoodfacts_service.requests.get')
    def test_08_source_attribution(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": 1,
            "product": {
                "code": "8901491001809",
                "product_name": "Chips"
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertEqual(res["source"], "OPEN_FOOD_FACTS")
        self.assertEqual(res["source_url"], "https://world.openfoodfacts.org/product/8901491001809")
        self.assertIn("community-maintained", res["disclaimer"].lower())
        self.assertEqual(res["product"]["source"], "OPEN_FOOD_FACTS")
        self.assertEqual(res["product"]["attributed_fields"]["product_name"]["source"], "OPEN_FOOD_FACTS")

    # 9. OCR / Open Food Facts mismatch
    def test_09_ocr_openfoodfacts_mismatch(self):
        off_data = {
            "available": True,
            "status": "FOUND",
            "product": {
                "product_name": "ABC Chips",
                "brands": "SnackCorp",
                "quantity": "50g",
                "countries": "India"
            }
        }

        # Case A: Matching OCR
        matching_ocr = {
            "commodity_name": {"value": "ABC Chips"},
            "manufacturer": {"name": "SnackCorp India Ltd"},
            "net_quantity": {"raw": "50 g"}
        }
        match_result = OpenFoodFactsService.cross_check_with_ocr(matching_ocr, off_data)
        self.assertTrue(match_result["available"])
        self.assertTrue(match_result["details_consistent"])
        self.assertEqual(match_result["mismatches_found"], 0)

        # Case B: Mismatched OCR
        mismatched_ocr = {
            "commodity_name": {"value": "XYZ Cookies"},
            "manufacturer": {"name": "Bakery Ltd"},
            "net_quantity": {"raw": "200 g"}
        }
        mismatch_result = OpenFoodFactsService.cross_check_with_ocr(mismatched_ocr, off_data)
        self.assertTrue(mismatch_result["available"])
        self.assertFalse(mismatch_result["details_consistent"])
        self.assertGreater(mismatch_result["mismatches_found"], 0)
        self.assertIn("NOT alter", mismatch_result["note"])

    # 10. Open Food Facts failure does not break compliance scan
    def test_10_openfoodfacts_failure_does_not_break_compliance_scan(self):
        engine = RulesEngine()
        product_facts = {
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

        # Independent rule engine evaluation
        evaluation = engine.evaluate_package(product_facts)
        mfg_rule = next(r for r in evaluation["rule_results"] if r["rule_id"] == "R6_1_A")
        self.assertEqual(mfg_rule["status"], "PASS")
        qty_rule = next(r for r in evaluation["rule_results"] if r["rule_id"] == "R6_1_C")
        self.assertEqual(qty_rule["status"], "PASS")

        # Even if Open Food Facts lookup completely fails
        failed_off_result = {
            "available": False,
            "status": "UNAVAILABLE",
            "message": "Open Food Facts service is currently unavailable."
        }
        self.assertEqual(failed_off_result["status"], "UNAVAILABLE")

        # The compliance scan remains valid and rule results are unchanged
        self.assertIn("summary", evaluation)
        self.assertEqual(evaluation["summary"]["failed"], 0)


if __name__ == '__main__':
    unittest.main()
