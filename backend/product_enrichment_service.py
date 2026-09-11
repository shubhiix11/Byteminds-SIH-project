"""
Product & Barcode Enrichment Service for LabelSure.
Provides provider abstraction (Mock & OpenAI) for AI-assisted barcode interpretation and product context enrichment.
ChatGPT/OpenAI responses are strictly informational and NEVER decide legal compliance.
"""

from abc import ABC, abstractmethod
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class ProductEnrichmentProvider(ABC):
    @abstractmethod
    def enrich(self, barcode: str = None, detected_declarations: dict = None) -> dict:
        """Enrich product information using barcode or detected label declarations."""
        pass

class MockProductEnrichmentProvider(ProductEnrichmentProvider):
    """
    Demo / Mock Product Enrichment Provider for offline testing and development.
    Strictly allowed ONLY when LABELSURE_MODE=demo.
    """
    def enrich(self, barcode: str = None, detected_declarations: dict = None) -> dict:
        if not barcode and not detected_declarations:
            return {
                "available": False,
                "reason": "No barcode or product context provided for enrichment",
                "status": "UNAVAILABLE"
            }

        code = barcode or "8901234567890"
        
        if "biscuit" in str(detected_declarations).lower() or code.endswith("890"):
            product = "Crunchy Butter Cookies"
            brand = "Apex Foods"
            mfg = "Apex Foodworks Pvt Ltd"
            category = "Packaged Biscuits & Confectionery"
            country = "India"
            size = "200 g"
        elif "juice" in str(detected_declarations).lower():
            product = "Organic Mango Nectar"
            brand = "Pure Orchard"
            mfg = "Pure Orchard Beverages Ltd"
            category = "Fruit Beverages"
            country = "India"
            size = "1 L"
        else:
            product = "Premium Packaged Commodity"
            brand = "NutriCraft"
            mfg = "NutriCraft Global Foods Ltd"
            category = "General Packaged Food"
            country = "India"
            size = "250 g"

        return {
            "available": True,
            "status": "SUCCESS",
            "provider": "MockProductEnrichmentProvider",
            "source_type": "DEMO_MOCK_ENRICHMENT",
            "enrichment": {
                "barcode": code,
                "product_name": product,
                "brand": brand,
                "manufacturer": mfg,
                "category": category,
                "country": country,
                "pack_size": size,
                "additional_product_details": "Demo enrichment data from mock provider for testing.",
                "barcode_interpretation": f"EAN-13 GS1 India prefix 890 assigned to {mfg}.",
                "confidence": 0.92
            }
        }

class OpenAIProductEnrichmentProvider(ProductEnrichmentProvider):
    """
    OpenAI ChatGPT API Product & Barcode Enrichment Provider.
    Invokes OpenAI ChatCompletions API with JSON mode.
    Does NOT fabricate product info or barcode numbers.
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("PRODUCT_ENRICHMENT_MODEL", "gpt-4o-mini")

    def enrich(self, barcode: str = None, detected_declarations: dict = None) -> dict:
        if not self.api_key or "YOUR_OPENAI_API_KEY" in self.api_key or len(self.api_key.strip()) < 10:
            return {
                "available": False,
                "reason": "OpenAI API key not configured or invalid in .env",
                "status": "UNAVAILABLE",
                "provider": "OpenAIProductEnrichmentProvider"
            }

        if not barcode and not detected_declarations:
            return {
                "available": False,
                "reason": "Neither barcode nor package declarations were provided for enrichment",
                "status": "UNAVAILABLE",
                "provider": "OpenAIProductEnrichmentProvider"
            }

        prompt_payload = {
            "barcode": barcode or "Not detected",
            "detected_declarations": detected_declarations or {}
        }

        system_prompt = (
            "You are a product information enrichment assistant for packaged consumer goods. "
            "Do not invent product facts or barcode numbers. If information cannot be established from the barcode or context, return null or unknown. "
            "Do not make legal compliance decisions. Return structured JSON only."
        )

        user_prompt = f"Perform product information enrichment for this item context:\n{json.dumps(prompt_payload, indent=2)}"

        req_data = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(req_data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json["choices"][0]["message"]["content"]
                parsed_enrichment = json.loads(content)

                parsed_enrichment["source_type"] = "AI_PRODUCT_ENRICHMENT"
                parsed_enrichment["confidence"] = parsed_enrichment.get("confidence", 0.85)

                return {
                    "available": True,
                    "status": "SUCCESS",
                    "provider": "OpenAIProductEnrichmentProvider",
                    "source_type": "AI_PRODUCT_ENRICHMENT",
                    "enrichment": parsed_enrichment
                }

        except urllib.error.HTTPError as e:
            return {
                "available": False,
                "reason": f"OpenAI API HTTP Error {e.code}: {e.reason}",
                "status": "UNAVAILABLE",
                "provider": "OpenAIProductEnrichmentProvider"
            }
        except Exception as err:
            return {
                "available": False,
                "reason": f"Product enrichment failed: {str(err)}",
                "status": "UNAVAILABLE",
                "provider": "OpenAIProductEnrichmentProvider"
            }

class ProductEnrichmentService:
    def __init__(self, provider: ProductEnrichmentProvider = None):
        app_mode = os.environ.get("LABELSURE_MODE", "production").lower()
        provider_type = os.environ.get("PRODUCT_ENRICHMENT_PROVIDER", "openai").lower()

        if provider:
            if app_mode == "production" and isinstance(provider, MockProductEnrichmentProvider):
                # Never allow MockProductEnrichmentProvider in production mode
                self.provider = OpenAIProductEnrichmentProvider()
            else:
                self.provider = provider
        else:
            if app_mode == "production":
                # In production mode, always use OpenAIProductEnrichmentProvider
                self.provider = OpenAIProductEnrichmentProvider()
            else:
                # In demo mode, select provider based on config
                if provider_type == "openai":
                    self.provider = OpenAIProductEnrichmentProvider()
                else:
                    self.provider = MockProductEnrichmentProvider()

    def enrich_product(self, barcode: str = None, detected_declarations: dict = None) -> dict:
        """
        Enrich product facts using configured provider.
        """
        return self.provider.enrich(barcode=barcode, detected_declarations=detected_declarations)
