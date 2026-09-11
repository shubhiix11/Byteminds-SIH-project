"""
Test Suite for Physical Measurement & Evidence Annotation Service (Prompt 4).
Verifies scale calibration, PIL image annotation generation, color mapping, and schema formatting.
"""

import unittest
import os
from PIL import Image
from measurement_service import MeasurementService
from annotation_service import AnnotationService, COLOR_MAP

class TestMeasurementAndAnnotation(unittest.TestCase):
    def setUp(self):
        self.measurement_service = MeasurementService()
        self.annotation_service = AnnotationService()
        self.test_img_path = os.path.abspath("scratch/test_label_img.jpg")
        os.makedirs("scratch", exist_ok=True)
        img = Image.new("RGB", (800, 600), color=(50, 50, 50))
        img.save(self.test_img_path)

        self.sample_declarations = {
            "net_quantity": {"value": 200, "unit": "g", "raw": "200 g", "confidence": 0.95, "bbox": [100, 200, 150, 30]},
            "max_retail_price": {"value": 85.0, "currency": "INR", "raw": "₹ 85.00", "confidence": 0.96, "bbox": [100, 250, 180, 36]}
        }

    # Test 1: package_dimension measurement math
    def test_01_package_dimension_scale_calculation(self):
        meas_input = {
            "method": "package_dimension",
            "known_physical_mm": 100.0,
            "known_pixel_span": 1000.0  # Scale = 0.1 mm/px
        }
        res = self.measurement_service.measure_declarations(self.sample_declarations, meas_input)
        mrp_m = next(m for m in res if m["declaration"] == "max_retail_price")
        # 36px * 0.1 mm/px = 3.6mm
        self.assertEqual(mrp_m["pixel_height"], 36)
        self.assertEqual(mrp_m["estimated_mm_height"], 3.6)
        self.assertEqual(mrp_m["status"], "MEASURED")

    # Test 2: reference_object measurement math
    def test_02_reference_object_scale_calculation(self):
        meas_input = {
            "method": "reference_object",
            "reference_physical_size_mm": 20.0,
            "reference_pixel_size": 200.0  # Scale = 0.1 mm/px
        }
        res = self.measurement_service.measure_declarations(self.sample_declarations, meas_input)
        qty_m = next(m for m in res if m["declaration"] == "net_quantity")
        # 30px * 0.1 mm/px = 3.0mm
        self.assertEqual(qty_m["pixel_height"], 30)
        self.assertEqual(qty_m["estimated_mm_height"], 3.0)
        self.assertEqual(qty_m["status"], "MEASURED")

    # Test 3: not_available measurement scale yields NOT_VERIFIABLE with null mm
    def test_03_not_available_scale_returns_null_mm(self):
        meas_input = {"method": "not_available"}
        res = self.measurement_service.measure_declarations(self.sample_declarations, meas_input)
        qty_m = next(m for m in res if m["declaration"] == "net_quantity")
        self.assertIsNone(qty_m["estimated_mm_height"])
        self.assertEqual(qty_m["status"], "NOT_VERIFIABLE")
        self.assertIn("No physical scale reference is available", qty_m["reason"])

    # Test 4: Invalid/zero scale input handled safely
    def test_04_invalid_zero_scale(self):
        meas_input = {"method": "package_dimension", "known_physical_mm": 0, "known_pixel_span": 100}
        res = self.measurement_service.measure_declarations(self.sample_declarations, meas_input)
        mrp_m = next(m for m in res if m["declaration"] == "max_retail_price")
        self.assertIsNone(mrp_m["estimated_mm_height"])
        self.assertEqual(mrp_m["status"], "NOT_VERIFIABLE")

    # Test 5: Missing bounding box handling
    def test_05_missing_bbox(self):
        decls = {"commodity_name": "Butter Cookies"}  # No bbox
        res = self.measurement_service.measure_declarations(decls, {"method": "package_dimension", "known_physical_mm": 100, "known_pixel_span": 1000})
        name_m = res[0]
        self.assertIsNone(name_m["bbox"])
        self.assertIsNone(name_m["estimated_mm_height"])
        self.assertEqual(name_m["status"], "NOT_VERIFIABLE")

    # Test 6: Annotation generation & color mapping
    def test_06_annotation_service_generation(self):
        rule_results = [
            {"rule_id": "R6_1_C", "rule_number": "Rule 6(1)(c)", "title": "Net Quantity", "status": "PASS", "bbox": [100, 200, 150, 30], "reason": "Passed"},
            {"rule_id": "R6_1_E", "rule_number": "Rule 6(1)(e)", "title": "MRP", "status": "FAIL", "bbox": [100, 250, 180, 36], "reason": "Failed"}
        ]
        out_path, meta = self.annotation_service.create_annotated_image(self.test_img_path, rule_results, "scratch")
        self.assertTrue(os.path.exists(out_path))
        self.assertEqual(len(meta), 2)
        self.assertEqual(meta[0]["status"], "PASS")
        self.assertEqual(meta[1]["status"], "FAIL")

    # Test 7: Color Map RGBA values
    def test_07_color_map_schema(self):
        self.assertEqual(COLOR_MAP["PASS"], (16, 185, 129, 255))
        self.assertEqual(COLOR_MAP["FAIL"], (244, 63, 94, 255))
        self.assertEqual(COLOR_MAP["WARNING"], (245, 158, 11, 255))

if __name__ == "__main__":
    unittest.main()
