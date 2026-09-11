import unittest
import os
import json
import tempfile
from PIL import Image, ImageDraw

# Ensure LABELSURE_MODE=production for tests
os.environ["LABELSURE_MODE"] = "production"
os.environ["VISION_PROVIDER"] = "openai"
os.environ["PRODUCT_ENRICHMENT_PROVIDER"] = "openai"

from vision_service import VisionService, MockVisionProvider, OpenAIVisionProvider
from product_enrichment_service import ProductEnrichmentService, MockProductEnrichmentProvider, OpenAIProductEnrichmentProvider
from barcode_decoder import decode_barcode
from compliance_engine import ComplianceEngine

class TestProductionModeEnforcement(unittest.TestCase):
    def setUp(self):
        os.environ["LABELSURE_MODE"] = "production"

    def test_production_mode_never_uses_mock_vision(self):
        """1. Production mode must select OpenAIVisionProvider even if MockVisionProvider is requested."""
        service = VisionService(provider=MockVisionProvider())
        self.assertIsInstance(service.provider, OpenAIVisionProvider)
        self.assertNotIsInstance(service.provider, MockVisionProvider)

    def test_production_mode_never_uses_mock_enrichment(self):
        """2. Production mode must select OpenAIProductEnrichmentProvider even if MockProductEnrichmentProvider is requested."""
        service = ProductEnrichmentService(provider=MockProductEnrichmentProvider())
        self.assertIsInstance(service.provider, OpenAIProductEnrichmentProvider)
        self.assertNotIsInstance(service.provider, MockProductEnrichmentProvider)

    def test_missing_api_key_returns_unavailable_without_mock_data(self):
        """3. Missing OPENAI_API_KEY must return UNAVAILABLE status and never fake product data."""
        provider = OpenAIProductEnrichmentProvider(api_key="YOUR_OPENAI_API_KEY_HERE")
        result = provider.enrich(barcode="8901234567890", detected_declarations={"commodity": "Chips"})
        self.assertFalse(result.get("available"))
        self.assertEqual(result.get("status"), "UNAVAILABLE")
        self.assertNotIn("Crunchy Butter Cookies", json.dumps(result))
        self.assertNotIn("Apex Foods", json.dumps(result))

    def test_barcode_decoder_does_not_fabricate(self):
        """4. Barcode decoder on a blank image must return barcode=None and status=NOT_DETECTED."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (200, 200), color="white")
            img.save(f.name)
            temp_path = f.name

        try:
            res = decode_barcode(temp_path)
            self.assertFalse(res["detected"])
            self.assertIsNone(res["barcode"])
            self.assertEqual(res["status"], "NOT_DETECTED")
            self.assertNotEqual(res["barcode"], "8901234567890")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_demo_mode_allows_mock_provider(self):
        """5. Demo mode explicitly allows MockVisionProvider when LABELSURE_MODE=demo."""
        os.environ["LABELSURE_MODE"] = "demo"
        service = VisionService(provider=MockVisionProvider())
        self.assertIsInstance(service.provider, MockVisionProvider)
        os.environ["LABELSURE_MODE"] = "production"

    def test_unavailability_does_not_break_compliance(self):
        """6. Missing vision/enrichment facts must not crash Legal Metrology Engine."""
        engine = ComplianceEngine()
        empty_vision = {
            "declarations": {},
            "product_metadata": {"is_imported": False}
        }
        res = engine.process_scan(empty_vision)
        self.assertIn(res["overall_status"], ["NON_COMPLIANT", "NEEDS_REVIEW"])
        self.assertIn("summary", res)

if __name__ == "__main__":
    unittest.main()
