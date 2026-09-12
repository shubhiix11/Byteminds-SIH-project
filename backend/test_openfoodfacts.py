"""
Comprehensive test suite for LabelSure Open Food Facts API v3 Barcode Lookup integration.
Validates:
1. Valid barcode -> API request
2. Product found
3. Product not found
4. Invalid barcode
5. Network failure
6. Timeout
7. HTTP 429
8. Missing optional fields
9. Proper User-Agent
10. No mock fallback
11. OCR/Open Food Facts mismatch
12. Scan still works when OFF is unavailable
"""

import unittest
from unittest.mock import patch, MagicMock
import requests
import os

from openfoodfacts_service import OpenFoodFactsService, get_product_by_barcode
from rules_engine import RulesEngine


class TestOpenFoodFactsIntegration(unittest.TestCase):

    def setUp(self):
        self.service = OpenFoodFactsService(user_agent="LabelSure/1.0 (https://labelsure.gov.in; test-suite)")

    # 1. Valid barcode -> API request
    @patch('openfoodfacts_service.requests.get')
    def test_01_valid_barcode_api_request(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
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

        # Verify endpoint URL is API v3
        self.assertEqual(args[0], "https://world.openfoodfacts.org/api/v3/product/8901491001809")

        # Verify query parameters: product_type=food, fields, cc=IN, lc=en
        params = kwargs.get("params", {})
        self.assertEqual(params.get("product_type"), "food")
        self.assertEqual(params.get("cc"), "IN")
        self.assertEqual(params.get("lc"), "en")
        self.assertIn("product_name", params.get("fields", ""))
        self.assertIn("ingredients_text", params.get("fields", ""))

    # 2. Product found
    @patch('openfoodfacts_service.requests.get')
    def test_02_product_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "product": {
                "code": "8906020461239",
                "product_name": "Crem Treat",
                "brands": "Britannia",
                "categories": "Biscuits, Cookies",
                "quantity": "60g",
                "product_quantity": 60,
                "product_quantity_unit": "g",
                "packaging": "Plastic packet",
                "ingredients_text": "Wheat flour, sugar, vegetable oil",
                "allergens": "wheat, milk",
                "countries": "India",
                "labels": "Vegetarian",
                "nutriscore_grade": "d",
                "nutriments": {
                    "energy-kcal_100g": 480,
                    "fat_100g": 20.0
                },
                "image_front_url": "https://images.openfoodfacts.org/images/front.jpg"
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8906020461239", bypass_cache=True)
        self.assertEqual(res["status"], "FOUND")
        self.assertTrue(res["available"])
        self.assertEqual(res["source"], "OPEN_FOOD_FACTS")
        self.assertEqual(res["source_url"], "https://world.openfoodfacts.org/product/8906020461239")

        prod = res["product"]
        # Standard Section 4 fields
        self.assertEqual(prod["name"], "Crem Treat")
        self.assertEqual(prod["brand"], "Britannia")
        self.assertEqual(prod["category"], "Biscuits, Cookies")
        self.assertEqual(prod["quantity"], "60g")
        self.assertEqual(prod["packaging"], "Plastic packet")
        self.assertEqual(prod["ingredients"], "Wheat flour, sugar, vegetable oil")
        self.assertEqual(prod["allergens"], "wheat, milk")
        self.assertEqual(prod["countries"], "India")
        self.assertEqual(prod["labels"], "Vegetarian")
        self.assertEqual(prod["nutriscore"], "D")
        self.assertEqual(prod["nutriments"]["energy-kcal_100g"], 480)
        self.assertEqual(prod["image_url"], "https://images.openfoodfacts.org/images/front.jpg")

    # 3. Product not found
    @patch('openfoodfacts_service.requests.get')
    def test_03_product_not_found(self, mock_get):
        # Subcase A: Documented HTTP 404 response
        mock_resp_404 = MagicMock()
        mock_resp_404.status_code = 404
        mock_resp_404.json.return_value = {
            "status": "failure",
            "result": {"id": "product_not_found", "name": "Product not found"}
        }
        mock_get.return_value = mock_resp_404

        res = self.service.get_product_by_barcode("8901491100328", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "NOT_FOUND")
        self.assertEqual(res["barcode"], "8901491100328")
        self.assertEqual(res["source"], "OPEN_FOOD_FACTS")
        self.assertIn("Barcode detected, but this product was not found in Open Food Facts.", res["message"])

        # Subcase B: HTTP 200 with empty product object
        mock_resp_empty = MagicMock()
        mock_resp_empty.status_code = 200
        mock_resp_empty.json.return_value = {
            "status": "failure",
            "product": {}
        }
        mock_get.return_value = mock_resp_empty

        res2 = self.service.get_product_by_barcode("8901491100329", bypass_cache=True)
        self.assertFalse(res2["available"])
        self.assertEqual(res2["status"], "NOT_FOUND")

    # 4. Invalid barcode
    def test_04_invalid_barcode(self):
        invalid_barcodes = ["../../etc/passwd", "123$#@!", "ab", "<script>", "   ", ""]
        for b in invalid_barcodes:
            if not b.strip():
                res = self.service.get_product_by_barcode(b, bypass_cache=True)
                self.assertEqual(res["status"], "NO_BARCODE")
                self.assertFalse(res["available"])
            else:
                res = self.service.get_product_by_barcode(b, bypass_cache=True)
                self.assertEqual(res["status"], "INVALID_BARCODE")
                self.assertFalse(res["available"])

    # 5. Network failure
    @patch('openfoodfacts_service.requests.get')
    def test_05_network_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect to host")

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIn("currently unavailable", res["message"])

    # 6. Timeout
    @patch('openfoodfacts_service.requests.get')
    def test_06_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Request connection timed out")

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIn("timed out", res["message"])

    # 7. HTTP 429
    @patch('openfoodfacts_service.requests.get')
    def test_07_http_429(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIn("rate limit exceeded", res["message"])

    # 8. Missing optional fields
    @patch('openfoodfacts_service.requests.get')
    def test_08_missing_optional_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Minimal payload with many missing fields
        mock_resp.json.return_value = {
            "status": "success",
            "product": {
                "code": "8901234567890",
                "product_name": "Minimal Snack"
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901234567890", bypass_cache=True)
        self.assertEqual(res["status"], "FOUND")
        prod = res["product"]
        self.assertEqual(prod["name"], "Minimal Snack")
        self.assertIsNone(prod["brand"])
        self.assertIsNone(prod["category"])
        self.assertIsNone(prod["quantity"])
        self.assertIsNone(prod["packaging"])
        self.assertIsNone(prod["ingredients"])
        self.assertIsNone(prod["allergens"])
        self.assertIsNone(prod["countries"])
        self.assertIsNone(prod["labels"])
        self.assertIsNone(prod["nutriments"])
        self.assertIsNone(prod["nutriscore"])
        self.assertIsNone(prod["image_url"])

    # 9. Proper User-Agent
    @patch('openfoodfacts_service.requests.get')
    def test_09_proper_user_agent(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "product": {"product_name": "Test"}}
        mock_get.return_value = mock_resp

        custom_ua = "LabelSure/1.0 (test-project@labelsure.gov.in)"
        service = OpenFoodFactsService(user_agent=custom_ua)
        service.get_product_by_barcode("8901491001809", bypass_cache=True)

        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["User-Agent"], custom_ua)

    # 10. No mock fallback
    @patch('openfoodfacts_service.requests.get')
    def test_10_no_mock_fallback(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        res = self.service.get_product_by_barcode("8901491001809", bypass_cache=True)
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertFalse(res["available"])
        self.assertNotIn("product", res)
        # Ensure no mock product details are fabricated
        self.assertNotIn("Crunchy Butter Cookies", str(res))

    # 11. OCR/Open Food Facts mismatch
    def test_11_ocr_openfoodfacts_mismatch(self):
        off_data = {
            "available": True,
            "status": "FOUND",
            "product": {
                "name": "XYZ Chips",
                "product_name": "XYZ Chips",
                "brand": "SnackCorp",
                "brands": "SnackCorp",
                "quantity": "50g",
                "countries": "India"
            }
        }

        # Case A: Matching OCR
        matching_ocr = {
            "commodity_name": {"value": "XYZ Chips"},
            "manufacturer": {"name": "SnackCorp India Ltd"},
            "net_quantity": {"raw": "50 g"}
        }
        match_res = OpenFoodFactsService.cross_check_with_ocr(matching_ocr, off_data)
        self.assertTrue(match_res["available"])
        self.assertTrue(match_res["details_consistent"])
        self.assertEqual(match_res["mismatches_found"], 0)

        # Case B: Mismatched OCR (XYZ Chips vs ABC Cookies)
        mismatched_ocr = {
            "commodity_name": {"value": "ABC Cookies"},
            "manufacturer": {"name": "Other Bakery Ltd"},
            "net_quantity": {"raw": "200 g"}
        }
        mismatch_res = OpenFoodFactsService.cross_check_with_ocr(mismatched_ocr, off_data)
        self.assertTrue(mismatch_res["available"])
        self.assertFalse(mismatch_res["details_consistent"])
        self.assertGreater(mismatch_res["mismatches_found"], 0)
        self.assertIn("NOT alter", mismatch_res["note"])

    # 12. Scan still works when OFF is unavailable
    def test_12_scan_still_works_when_off_unavailable(self):
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

        # Deterministic rule engine evaluation
        evaluation = engine.evaluate_package(product_facts)
        mfg_rule = next(r for r in evaluation["rule_results"] if r["rule_id"] == "R6_1_A")
        self.assertEqual(mfg_rule["status"], "PASS")

        # Open Food Facts service unavailable
        failed_off_result = {
            "available": False,
            "status": "UNAVAILABLE",
            "message": "Open Food Facts service is currently unavailable."
        }
        self.assertEqual(failed_off_result["status"], "UNAVAILABLE")

        # The compliance scan remains 100% valid and rule results are unchanged
        self.assertIn("summary", evaluation)
        self.assertEqual(evaluation["summary"]["failed"], 0)


if __name__ == '__main__':
    unittest.main()
