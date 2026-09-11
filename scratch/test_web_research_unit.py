import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("backend"))

from web_research_service import GoogleWebSearchProvider, SearchIdentityBuilder, MultiQueryGenerator, WebResearchManager
from web_product_extractor import WebProductExtractor

print("=== 1. Testing Google Provider Availability ===")
provider = GoogleWebSearchProvider()
print(f"Provider available: {provider.is_available()}")

print("\n=== 2. Testing Search Identity Builder ===")
identity = SearchIdentityBuilder.build(
    barcode="8901491001809",
    detected_declarations={
        "manufacturer": {"name": "PepsiCo India Holdings Pvt Ltd"},
        "commodity_name": {"value": "Potato Chips"},
        "net_quantity": {"text": "50 g"},
        "max_retail_price": {"text": "₹ 20.00"}
    },
    all_detected_text="PepsiCo India Holdings Pvt Ltd\nPotato Chips\nNet Qty 50g"
)
print("Built Identity:", identity)
assert identity["barcode"] == "8901491001809"
assert identity["product_name"] == "Potato Chips"
assert identity["manufacturer"] == "PepsiCo India Holdings Pvt Ltd"

print("\n=== 3. Testing Multi-Query Generator ===")
queries = MultiQueryGenerator.generate(identity)
print(f"Generated {len(queries)} queries:")
for q in queries:
    print(f"  - {q}")
assert any("8901491001809" in q for q in queries)
assert any("Potato Chips" in q for q in queries)

print("\n=== 4. Testing Web Product Extractor on Mock HTML ===")
extractor = WebProductExtractor()
mock_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Lay's Classic Salted Potato Chips 50g - Buy Online</title>
    <meta property="og:title" content="Lay's Classic Salted Potato Chips 50g" />
    <meta property="product:price:amount" content="20.00" />
    <meta property="product:brand" content="Lay's" />
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Lay's Classic Salted Potato Chips",
        "image": "https://example.com/lays.jpg",
        "description": "Crispy and delicious salted potato chips",
        "brand": {
            "@type": "Brand",
            "name": "Lay's"
        },
        "manufacturer": {
            "@type": "Organization",
            "name": "PepsiCo India"
        },
        "sku": "LAY-50G-SALT",
        "gtin13": "8901491001809",
        "category": "Snacks",
        "offers": {
            "@type": "Offer",
            "price": "20.00",
            "priceCurrency": "INR"
        }
    }
    </script>
</head>
<body>
    <div class="product-info">
        <p>Net Quantity: 50 g</p>
        <p>MRP: Rs 20.00</p>
        <p>Country of Origin: India</p>
        <p>Ingredients: Potatoes, Edible Vegetable Oil, Salt.</p>
        <p>Customer Care: 1800-22-4020 or care@pepsico.com</p>
        <p>100% Vegetarian Product</p>
    </div>
</body>
</html>
"""
extracted = extractor.extract_from_page(mock_html, "https://example.com/lays-50g", "Lay's Classic Salted Potato Chips 50g", "example.com")
print(f"Extracted {len(extracted['facts'])} facts from page:")
for f in extracted['facts']:
    print(f"  [{f['field']}] = '{f['value']}' (conf: {f['confidence']}, source: {f['source_domain']})")

fields = {f['field']: f['value'] for f in extracted['facts']}
assert fields.get("product_name") == "Lay's Classic Salted Potato Chips"
assert fields.get("brand") == "Lay's"
assert fields.get("barcode") == "8901491001809"
assert fields.get("net_quantity") == "50 g"
assert fields.get("dietary_indicator") == "Vegetarian"

print("\n=== 5. Testing Aggregation & Conflict Detection ===")
# Add a second page with a conflicting net quantity
page2 = {
    "url": "https://retailer.com/lays",
    "domain": "retailer.com",
    "title": "Lay's Chips Retailer",
    "facts": [
        {"field": "product_name", "value": "Lay's Classic Salted Potato Chips", "source_url": "https://retailer.com/lays", "source_domain": "retailer.com", "source_title": "Retailer", "evidence": "text", "confidence": 0.90},
        {"field": "net_quantity", "value": "52 g", "source_url": "https://retailer.com/lays", "source_domain": "retailer.com", "source_title": "Retailer", "evidence": "text", "confidence": 0.85}
    ]
}
agg = extractor.aggregate_and_detect_conflicts([extracted, page2], identity)
print(f"Product Identity: {agg['product_identity']}")
print(f"Conflicts Detected: {len(agg['conflicts'])}")
for c in agg['conflicts']:
    print(f"  Conflict in {c['field']}: {c['description']}")
    print(f"  Candidates: {c['candidates']}")

assert len(agg['conflicts']) == 1
assert agg['conflicts'][0]['field'] == "net_quantity"

print("\n=== 6. Testing Web Research Manager (Unconfigured/Safe Mode) ===")
manager = WebResearchManager()
result = manager.run_research(barcode="8901491001809", detected_declarations=identity)
print(f"Manager Status without API Key: {result['status']}")
print(f"Manager Reason: {result.get('reason')}")
assert result['status'] in ["UNAVAILABLE", "COMPLETE"]

print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")
