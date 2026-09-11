from abc import ABC, abstractmethod
import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class VisionProvider(ABC):
    @abstractmethod
    def extract_facts(self, image_path: str) -> dict:
        """Extract structured label facts from image at image_path."""
        pass

class MockVisionProvider(VisionProvider):
    """
    Mock vision provider returning structured candidate OCR facts for testing/demo.
    Strictly allowed ONLY when LABELSURE_MODE=demo.
    """
    def extract_facts(self, image_path: str) -> dict:
        filename = os.path.basename(image_path).lower()

        if 'missing_mfg' in filename:
            commodity = "Butter Cookies"
            net_qty = {"value": 200, "unit": "g", "raw": "200 g", "confidence": 0.95, "bbox": [10, 20, 100, 30]}
            mrp = {"value": 85.00, "currency": "INR", "raw": "₹ 85.00 (Incl. of all taxes)", "confidence": 0.96, "bbox": [10, 50, 100, 30]}
            mfd = {"value": "04/2026", "raw": "MFD 04/2026", "confidence": 0.94, "bbox": [10, 80, 100, 30]}
            manufacturer = None
            care = {"phone": "+91-1800-111-222", "email": "care@apexfoods.com", "confidence": 0.92, "bbox": [10, 110, 100, 30]}
            origin = "India"
            is_imported = False
        elif 'imported' in filename:
            commodity = "Imported Chocolate Almonds"
            net_qty = {"value": 150, "unit": "g", "raw": "150g", "confidence": 0.95, "bbox": [10, 20, 100, 30]}
            mrp = {"value": 299.00, "currency": "INR", "raw": "MRP ₹ 299.00 (Incl. of all taxes)", "confidence": 0.96, "bbox": [10, 50, 100, 30]}
            mfd = {"value": "01/2026", "raw": "Packed 01/2026", "confidence": 0.93, "bbox": [10, 80, 100, 30]}
            manufacturer = {"name": "Swiss Gourmet Confectionery AG", "address": "Zurich, Switzerland", "confidence": 0.94, "bbox": [10, 110, 100, 30]}
            care = {"phone": "+91-1800-999-000", "email": "help@swissgourmet.in", "confidence": 0.91, "bbox": [10, 140, 100, 30]}
            origin = {"value": "Switzerland", "confidence": 0.95, "bbox": [10, 170, 100, 30]}
            is_imported = True
        else:
            commodity = "Crunchy Butter Cookies"
            net_qty = {"value": 200, "unit": "g", "raw": "200 g (0.44 lbs)", "confidence": 0.97, "bbox": [120, 340, 180, 48]}
            mrp = {"value": 85.00, "currency": "INR", "raw": "₹ 85.00 (Incl. of all taxes)", "confidence": 0.98, "bbox": [120, 400, 200, 48]}
            mfd = {"value": "04/2026", "raw": "MFD: 04/2026", "confidence": 0.96, "bbox": [120, 460, 150, 40]}
            manufacturer = {
                "name": "Apex Foodworks Pvt Ltd",
                "address": "Plot 42, Industrial Area, Sector 5, Gurugram, Haryana - 122001",
                "confidence": 0.96,
                "bbox": [120, 100, 400, 80]
            }
            care = {
                "phone": "+91-1800-111-222",
                "email": "care@apexfoods.com",
                "raw": "+91-1800-111-222, care@apexfoods.com",
                "confidence": 0.95,
                "bbox": [120, 520, 350, 50]
            }
            origin = None
            is_imported = False

        return {
            "provider": "MockVisionProvider",
            "source_type": "DEMO_MOCK_ENRICHMENT",
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
            "confidence_score": 0.96,
            "product_metadata": {
                "is_imported": is_imported,
                "is_photo_inspection": True
            },
            "font_pixel_height": 24.0,
            "declarations": {
                "commodity_name": commodity,
                "net_quantity": net_qty,
                "max_retail_price": mrp,
                "date_of_manufacture": mfd,
                "manufacturer": manufacturer,
                "consumer_care": care,
                "country_of_origin": origin
            }
        }

class OpenAIVisionProvider(VisionProvider):
    """
    Production OpenAI GPT-4o Vision OCR provider.
    Extracts visible packaged commodity text declarations directly from real image pixels.
    Does NOT fabricate declarations if text is unreadable or absent.
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("VISION_MODEL", "gpt-4o-mini")

    def extract_facts(self, image_path: str) -> dict:
        if not self.api_key or "YOUR_OPENAI_API_KEY" in self.api_key or len(self.api_key.strip()) < 10:
            return {
                "provider": "OpenAIVisionProvider",
                "status": "UNAVAILABLE",
                "reason": "OpenAI API key is missing or unconfigured in .env",
                "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                "confidence_score": 0.0,
                "font_pixel_height": 0.0,
                "product_metadata": {"is_imported": False, "is_photo_inspection": True},
                "declarations": {}
            }

        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

            ext = os.path.splitext(image_path)[1].lower().replace('.', '')
            mime_type = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg', 'webp'] else "image/jpeg"
            image_url = f"data:{mime_type};base64,{encoded_image}"

            system_prompt = (
                "You are an expert Legal Metrology OCR vision system for packaged commodities in India. "
                "Examine the image carefully and extract visible label declarations. "
                "Do NOT invent details. If a declaration is not visible or unreadable, return null or empty object. "
                "Return JSON matching schema: "
                "{"
                "  \"declarations\": {"
                "    \"commodity_name\": \"...\", "
                "    \"net_quantity\": {\"value\": 100, \"unit\": \"g\", \"raw\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}, "
                "    \"max_retail_price\": {\"value\": 50.0, \"currency\": \"INR\", \"raw\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}, "
                "    \"date_of_manufacture\": {\"value\": \"04/2026\", \"raw\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}, "
                "    \"manufacturer\": {\"name\": \"...\", \"address\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}, "
                "    \"consumer_care\": {\"phone\": \"...\", \"email\": \"...\", \"raw\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}, "
                "    \"country_of_origin\": {\"value\": \"...\", \"confidence\": 0.95, \"bbox\": [x,y,w,h]}"
                "  }, "
                "  \"product_metadata\": {\"is_imported\": false, \"is_photo_inspection\": true}, "
                "  \"font_pixel_height\": 24.0, "
                "  \"confidence_score\": 0.92"
                "}"
            )

            req_data = {
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all visible packaged commodity declarations from this label image for Legal Metrology inspection."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                "temperature": 0.1
            }

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(req_data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                return {
                    "provider": "OpenAIVisionProvider",
                    "source_type": "IMAGE_OCR",
                    "status": "SUCCESS",
                    "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                    "confidence_score": parsed.get("confidence_score", 0.90),
                    "font_pixel_height": float(parsed.get("font_pixel_height", 20.0)),
                    "product_metadata": parsed.get("product_metadata", {"is_imported": False, "is_photo_inspection": True}),
                    "declarations": parsed.get("declarations", {})
                }

        except urllib.error.HTTPError as e:
            err_detail = ""
            try:
                err_body = e.read().decode('utf-8')
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message")
                err_code = err_json.get("error", {}).get("code")
                if err_msg:
                    err_detail = f" - {err_code}: {err_msg}" if err_code else f" - {err_msg}"
            except Exception:
                pass

            return {
                "provider": "OpenAIVisionProvider",
                "status": "UNAVAILABLE",
                "reason": f"OpenAI HTTP Error {e.code}: {e.reason}{err_detail}",
                "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                "confidence_score": 0.0,
                "font_pixel_height": 0.0,
                "product_metadata": {"is_imported": False, "is_photo_inspection": True},
                "declarations": {}
            }
        except Exception as err:
            return {
                "provider": "OpenAIVisionProvider",
                "status": "UNAVAILABLE",
                "reason": f"Vision extraction failed: {str(err)}",
                "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                "confidence_score": 0.0,
                "font_pixel_height": 0.0,
                "product_metadata": {"is_imported": False, "is_photo_inspection": True},
                "declarations": {}
            }

class VisionService:
    def __init__(self, provider: VisionProvider = None):
        app_mode = os.environ.get("LABELSURE_MODE", "production").lower()
        provider_name = os.environ.get("VISION_PROVIDER", "openai").lower()

        from tesseract_provider import TesseractVisionProvider

        if provider:
            if app_mode == "production" and isinstance(provider, MockVisionProvider):
                # Never allow MockVisionProvider in production mode
                if provider_name == "tesseract":
                    self.provider = TesseractVisionProvider()
                else:
                    self.provider = OpenAIVisionProvider()
            else:
                self.provider = provider
        else:
            if app_mode == "production":
                # In production mode: mock is strictly disallowed
                if provider_name == "tesseract":
                    self.provider = TesseractVisionProvider()
                else:
                    self.provider = OpenAIVisionProvider()
            else:
                # In demo mode, select provider based on config
                if provider_name == "openai":
                    self.provider = OpenAIVisionProvider()
                elif provider_name == "tesseract":
                    self.provider = TesseractVisionProvider()
                else:
                    self.provider = MockVisionProvider()

    def process_image(self, image_path: str) -> dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        result = self.provider.extract_facts(image_path)
        result["fallback_used"] = False
        result["active_provider"] = self.provider.__class__.__name__
        return result


