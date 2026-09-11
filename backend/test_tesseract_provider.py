"""
Comprehensive Test Suite for Tesseract Local OCR Provider in LabelSure.
Tests binary path discovery, strict zero-fabrication on blank/unreadable images,
schema compliance, provider mode enforcement, barcode independence,
and dual-OCR cross-check comparisons with uncertainty states.
"""

import os
import tempfile
import unittest
from PIL import Image, ImageDraw, ImageFont

from tesseract_provider import (
    get_tesseract_cmd,
    is_tesseract_available,
    get_tesseract_path_status,
    get_tesseract_version,
    TesseractVisionProvider
)
from vision_service import VisionService, OpenAIVisionProvider, MockVisionProvider
from cross_check_engine import CrossCheckEngine
from compliance_engine import ComplianceEngine
from measurement_service import MeasurementService
from annotation_service import AnnotationService
from barcode_decoder import decode_barcode

class TestTesseractProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tesseract_available = is_tesseract_available()

    def test_01_tesseract_discovery_and_path_safety(self):
        """1. Verify Tesseract detection via PATH or TESSERACT_CMD without leaking secrets."""
        status = get_tesseract_path_status()
        self.assertIn(status, ["configured", "not configured"])

        # Path status must NEVER expose Windows drive path or tokens
        self.assertNotIn("C:\\", status)
        self.assertNotIn("/", status)

        if self.tesseract_available:
            cmd = get_tesseract_cmd()
            self.assertIsNotNone(cmd)
            self.assertTrue(os.path.isfile(cmd))
            version = get_tesseract_version()
            self.assertIsNotNone(version)
            self.assertIn("tesseract", version.lower())

    def test_02_custom_tesseract_cmd_env_variable(self):
        """2. Verify TESSERACT_CMD environment variable is respected."""
        current_cmd = get_tesseract_cmd()
        if current_cmd:
            original_env = os.environ.get("TESSERACT_CMD")
            try:
                os.environ["TESSERACT_CMD"] = current_cmd
                self.assertEqual(get_tesseract_cmd(), current_cmd)
                self.assertEqual(get_tesseract_path_status(), "configured")
            finally:
                if original_env is not None:
                    os.environ["TESSERACT_CMD"] = original_env
                else:
                    os.environ.pop("TESSERACT_CMD", None)

    def test_03_no_fabrication_on_blank_image(self):
        """3. Strict Zero Fabrication: Blank image must return empty declarations without demo products or barcodes."""
        if not self.tesseract_available:
            self.skipTest("Tesseract not available on system")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            blank_img = Image.new("RGB", (400, 300), color="white")
            blank_img.save(f.name)
            temp_path = f.name

        try:
            provider = TesseractVisionProvider()
            facts = provider.extract_facts(temp_path)

            self.assertEqual(facts["provider"], "TesseractVisionProvider")
            self.assertEqual(facts["source_type"], "LOCAL_OCR")
            # Declarations must be completely empty
            self.assertEqual(facts["declarations"], {})
            self.assertEqual(facts["confidence_score"], 0.0)
            self.assertEqual(facts["all_detected_text"], "")
            self.assertEqual(facts["ocr_items"], [])

            # NEVER fabricate sample data
            raw_str = str(facts).lower()
            self.assertNotIn("butter cookies", raw_str)
            self.assertNotIn("apex foodworks", raw_str)
            self.assertNotIn("8901234567890", raw_str)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_04_barcode_independence(self):
        """4. Barcode Guarantee: Tesseract does not guess barcode digits; barcode decoder is sole source."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create image with no barcode
            img = Image.new("RGB", (300, 200), color="white")
            d = ImageDraw.Draw(img)
            d.text((20, 20), "Sample Label Text Only", fill="black")
            img.save(f.name)
            temp_path = f.name

        try:
            barcode_res = decode_barcode(temp_path)
            self.assertFalse(barcode_res["detected"])
            self.assertIsNone(barcode_res["barcode"])
            self.assertEqual(barcode_res["status"], "NOT_DETECTED")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_05_real_ocr_extraction_and_schema_compliance(self):
        """5. Real OCR extraction: extracts visible text declarations matching required schema."""
        if not self.tesseract_available:
            self.skipTest("Tesseract not available on system")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a crisp synthetic test label with Legal Metrology declarations
            img = Image.new("RGB", (900, 500), color="white")
            d = ImageDraw.Draw(img)
            # Use larger, clear text
            d.text((40, 30), "COMMODITY: CRISPY POTATO CHIPS", fill="black")
            d.text((40, 80), "NET QUANTITY: 200 g", fill="black")
            d.text((40, 130), "MRP Rs 50.00 (INCL OF ALL TAXES)", fill="black")
            d.text((40, 180), "MFD: 06/2026", fill="black")
            d.text((40, 230), "Mfg by: Apex Foods Pvt Ltd, Delhi 110001", fill="black")
            d.text((40, 280), "Consumer Care: 1800-111-222, care@apexfoods.com", fill="black")
            d.text((40, 330), "Country of Origin: India", fill="black")
            img.save(f.name)
            temp_path = f.name

        try:
            provider = TesseractVisionProvider()
            facts = provider.extract_facts(temp_path)

            self.assertEqual(facts["status"], "SUCCESS")
            self.assertIn("all_detected_text", facts)
            self.assertTrue(len(facts["all_detected_text"]) > 0)

            decls = facts["declarations"]
            self.assertTrue(len(decls) > 0)

            # Check schema on any detected declarations:
            # { "text": "...", "confidence": 0.0, "bbox": [x,y,w,h], "candidate_type": "...", "original_text": "..." }
            for decl_key, decl in decls.items():
                self.assertIn("text", decl)
                self.assertIn("confidence", decl)
                self.assertIn("candidate_type", decl)
                self.assertIn("original_text", decl)
                self.assertTrue("bbox" in decl)
                if decl["bbox"] is not None:
                    self.assertEqual(len(decl["bbox"]), 4)

            # Check all detected items schema
            for item in facts["ocr_items"]:
                self.assertIn("text", item)
                self.assertIn("confidence", item)
                self.assertIn("bbox", item)
                self.assertIn("candidate_type", item)
                self.assertIn("original_text", item)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_06_provider_mode_enforcement(self):
        """6. Provider selection and production mode enforcement: Mock forbidden in production."""
        os.environ["LABELSURE_MODE"] = "production"

        # Production with VISION_PROVIDER=tesseract
        os.environ["VISION_PROVIDER"] = "tesseract"
        service = VisionService()
        self.assertIsInstance(service.provider, TesseractVisionProvider)

        # Production with VISION_PROVIDER=mock must NEVER select MockVisionProvider
        os.environ["VISION_PROVIDER"] = "mock"
        service_mock = VisionService()
        self.assertNotIsInstance(service_mock.provider, MockVisionProvider)

        # Passing MockVisionProvider explicitly in production mode must be rejected
        service_explicit_mock = VisionService(provider=MockVisionProvider())
        self.assertNotIsInstance(service_explicit_mock.provider, MockVisionProvider)

        # In demo mode, mock is allowed
        os.environ["LABELSURE_MODE"] = "demo"
        os.environ["VISION_PROVIDER"] = "mock"
        service_demo = VisionService()
        self.assertIsInstance(service_demo.provider, MockVisionProvider)

    def test_07_ocr_cross_check_matching_strengthens_evidence(self):
        """7. OCR Cross-Check: Matching values between OpenAI and Tesseract strengthen evidence."""
        openai_facts = {
            "declarations": {
                "max_retail_price": {"value": 20.0, "raw": "MRP ₹ 20.00"},
                "net_quantity": {"value": 100.0, "unit": "g", "raw": "100 g"},
                "date_of_manufacture": {"value": "05/2026", "raw": "MFD 05/2026"},
                "manufacturer": {"name": "Apex Foodworks Pvt Ltd"}
            }
        }
        tesseract_facts = {
            "declarations": {
                "max_retail_price": {"value": 20.0, "text": "₹ 20.00", "raw": "MRP ₹ 20.00"},
                "net_quantity": {"value": 100.0, "unit": "g", "text": "100 g", "raw": "100 g"},
                "date_of_manufacture": {"value": "05/2026", "text": "05/2026"},
                "manufacturer": {"name": "Apex Foodworks Pvt Ltd"}
            }
        }

        cross_res = CrossCheckEngine.cross_check_ocr_providers(openai_facts, tesseract_facts)
        self.assertTrue(cross_res["available"])
        self.assertEqual(cross_res["overall_status"], "AGREED")
        self.assertFalse(cross_res["has_disagreement"])
        self.assertGreaterEqual(cross_res["agreed_count"], 3)
        self.assertEqual(cross_res["disagreement_count"], 0)

        # Check that MRP has confidence_strengthened = True
        mrp_comp = next(c for c in cross_res["comparisons"] if c["field"] == "Maximum Retail Price (MRP)")
        self.assertEqual(mrp_comp["status"], "AGREED")
        self.assertTrue(mrp_comp["confidence_strengthened"])

    def test_08_ocr_cross_check_disagreement_shows_uncertainty_state(self):
        """8. OCR Cross-Check: Disagreement shows uncertainty state without hiding conflicting values."""
        openai_facts = {
            "declarations": {
                "max_retail_price": {"value": 20.0, "raw": "MRP ₹ 20.00"},
                "net_quantity": {"value": 100.0, "unit": "g", "raw": "100 g"}
            }
        }
        tesseract_facts = {
            "declarations": {
                "max_retail_price": {"value": 25.0, "raw": "MRP ₹ 25.00"},  # Disagrees!
                "net_quantity": {"value": 100.0, "unit": "g", "raw": "100 g"}
            }
        }

        cross_res = CrossCheckEngine.cross_check_ocr_providers(openai_facts, tesseract_facts)
        self.assertTrue(cross_res["available"])
        self.assertTrue(cross_res["has_disagreement"])
        self.assertEqual(cross_res["overall_status"], "DISAGREEMENT")

        mrp_comp = next(c for c in cross_res["comparisons"] if c["field"] == "Maximum Retail Price (MRP)")
        self.assertEqual(mrp_comp["status"], "DISAGREEMENT")
        self.assertFalse(mrp_comp["confidence_strengthened"])
        # Both values are preserved and exposed
        self.assertIn("20", mrp_comp["openai_value"])
        self.assertIn("25", mrp_comp["tesseract_value"])

    def test_09_end_to_end_pipeline_with_tesseract(self):
        """9. Pipeline integration: Tesseract facts flow through normalization, rules, measurement, annotation."""
        tess_facts = {
            "provider": "TesseractVisionProvider",
            "source_type": "LOCAL_OCR",
            "status": "SUCCESS",
            "confidence_score": 0.92,
            "font_pixel_height": 28.0,
            "product_metadata": {"is_imported": False, "is_photo_inspection": True},
            "all_detected_text": "MRP Rs 20.00 Net Qty 100g MFD 05/2026",
            "declarations": {
                "commodity_name": {"text": "Potato Chips", "value": "Potato Chips", "raw": "Potato Chips", "confidence": 0.95, "bbox": [10, 10, 100, 25], "candidate_type": "commodity_name", "original_text": "Potato Chips"},
                "net_quantity": {"text": "100 g", "value": 100, "unit": "g", "raw": "100 g", "confidence": 0.95, "bbox": [10, 50, 100, 25], "candidate_type": "net_quantity", "original_text": "100 g"},
                "max_retail_price": {"text": "₹ 20.00", "value": 20.0, "currency": "INR", "raw": "MRP Rs 20.00", "confidence": 0.96, "bbox": [10, 90, 120, 25], "candidate_type": "max_retail_price", "original_text": "MRP Rs 20.00"},
                "date_of_manufacture": {"text": "05/2026", "value": "05/2026", "raw": "MFD 05/2026", "confidence": 0.94, "bbox": [10, 130, 80, 25], "candidate_type": "date_of_manufacture", "original_text": "MFD 05/2026"},
                "manufacturer": {"text": "Apex Foods Pvt Ltd", "name": "Apex Foods Pvt Ltd", "address": "Delhi", "raw": "Apex Foods Pvt Ltd, Delhi", "confidence": 0.93, "bbox": [10, 170, 200, 25], "candidate_type": "manufacturer", "original_text": "Apex Foods Pvt Ltd"},
                "consumer_care": {"text": "1800-111-222", "phone": "1800-111-222", "email": "care@apex.com", "raw": "1800-111-222", "confidence": 0.92, "bbox": [10, 210, 150, 25], "candidate_type": "consumer_care", "original_text": "1800-111-222"}
            }
        }

        compliance_engine = ComplianceEngine()
        comp_res = compliance_engine.process_scan(tess_facts)
        self.assertIn(comp_res["overall_status"], ["COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW"])
        self.assertTrue(len(comp_res["rule_results"]) > 0)
        self.assertIn("summary", comp_res)

        # Measurement
        meas_service = MeasurementService()
        measurements = meas_service.measure_declarations(tess_facts["declarations"], {"method": "package_dimension", "known_physical_mm": 100.0, "known_pixel_span": 1000.0})
        self.assertTrue(len(measurements) > 0)

        # Annotation
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (400, 300), color="white")
            img.save(f.name)
            temp_img = f.name

        try:
            with tempfile.TemporaryDirectory() as out_dir:
                annot_service = AnnotationService()
                annot_path, metadata = annot_service.create_annotated_image(temp_img, comp_res["rule_results"], out_dir)
                self.assertTrue(os.path.exists(annot_path))
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

if __name__ == '__main__':
    unittest.main()
