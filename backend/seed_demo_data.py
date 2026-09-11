"""
Demo Data Seeder Script for LabelSure.
Explicitly populates SQLite database with sample Legal Metrology packaged commodity inspection scans.
Run with: python backend/seed_demo_data.py
"""

import os
import time
from database import init_db, save_scan
from report_generator import ReportGenerator

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

for folder in [REPORTS_DIR, UPLOADS_DIR]:
    os.makedirs(folder, exist_ok=True)

report_gen = ReportGenerator(REPORTS_DIR)

DEMO_SCANS = [
    {
        "product_name": "Crunchy Butter Cookies",
        "brand": "Apex Foods",
        "category": "Packaged Biscuits",
        "barcode": "8901234567890",
        "manufacturer": "Apex Foodworks Pvt Ltd",
        "overall_status": "COMPLIANT",
        "summary": {"rules_checked": 10, "passed": 8, "failed": 0, "warnings": 0, "not_verifiable": 0, "not_applicable": 2},
        "rule_results": [
            {"rule_id": "R6_1_A", "rule_number": "Rule 6(1)(a)", "title": "Name & Address of Manufacturer", "status": "PASS", "detected_text": "Apex Foodworks Pvt Ltd", "reason": "Manufacturer details valid.", "source_reference": "Rule 6(1)(a)"},
            {"rule_id": "R6_1_C", "rule_number": "Rule 6(1)(c)", "title": "Net Quantity", "status": "PASS", "detected_text": "200 g", "reason": "Valid metric quantity.", "source_reference": "Rule 6(1)(c)"},
            {"rule_id": "R6_1_E", "rule_number": "Rule 6(1)(e)", "title": "Maximum Retail Price (MRP)", "status": "PASS", "detected_text": "₹ 85.00 (Incl. of all taxes)", "reason": "MRP format valid.", "source_reference": "Rule 6(1)(e)"}
        ]
    },
    {
        "product_name": "Organic Mango Nectar",
        "brand": "Pure Orchard",
        "category": "Fruit Beverages",
        "barcode": "8909876543210",
        "manufacturer": "Pure Orchard Beverages Ltd",
        "overall_status": "NON_COMPLIANT",
        "summary": {"rules_checked": 10, "passed": 6, "failed": 2, "warnings": 0, "not_verifiable": 0, "not_applicable": 2},
        "rule_results": [
            {"rule_id": "R6_1_A", "rule_number": "Rule 6(1)(a)", "title": "Name & Address of Manufacturer", "status": "FAIL", "detected_text": None, "reason": "Mandatory manufacturer declaration missing.", "source_reference": "Rule 6(1)(a)"},
            {"rule_id": "R6_1_C", "rule_number": "Rule 6(1)(c)", "title": "Net Quantity", "status": "PASS", "detected_text": "1 L", "reason": "Valid metric quantity.", "source_reference": "Rule 6(1)(c)"},
            {"rule_id": "R6_1_E", "rule_number": "Rule 6(1)(e)", "title": "Maximum Retail Price (MRP)", "status": "FAIL", "detected_text": "Rs 140", "reason": "MRP missing mandatory tax inclusion clause.", "source_reference": "Rule 6(1)(e)"}
        ]
    },
    {
        "product_name": "Imported Swiss Chocolate Almonds",
        "brand": "Swiss Gourmet",
        "category": "Imported Confectionery",
        "barcode": "7610123456789",
        "manufacturer": "Swiss Gourmet AG",
        "overall_status": "NEEDS_REVIEW",
        "summary": {"rules_checked": 10, "passed": 7, "failed": 0, "warnings": 0, "not_verifiable": 1, "not_applicable": 2},
        "rule_results": [
            {"rule_id": "R6_1_A", "rule_number": "Rule 6(1)(a)", "title": "Name & Address of Importer", "status": "PASS", "detected_text": "Swiss Gourmet AG", "reason": "Importer details valid.", "source_reference": "Rule 6(1)(a)"},
            {"rule_id": "R6_1_G", "rule_number": "Rule 6(1)(g)", "title": "Country of Origin", "status": "NOT_VERIFIABLE", "detected_text": None, "reason": "Cannot verify country of origin from OCR evidence.", "source_reference": "Rule 6(1)(g)"}
        ]
    }
]

def seed_data():
    init_db()
    print("Seeding LabelSure demo scan records into SQLite database...")
    for idx, item in enumerate(DEMO_SCANS):
        timestamp = int(time.time() * 1000) + (idx * 1000)
        scan_id = f"DEMO_SCAN_{timestamp}"
        filename = f"demo_package_{idx+1}.jpg"
        file_path = os.path.join(UPLOADS_DIR, filename)

        # Create dummy image file if missing
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(b"DEMO IMAGE CONTENT")

        scan_payload = {
            "scan_id": scan_id,
            "filename": filename,
            "product_name": item["product_name"],
            "brand": item["brand"],
            "category": item["category"],
            "barcode": item["barcode"],
            "manufacturer": item["manufacturer"],
            "overall_status": item["overall_status"],
            "summary": item["summary"],
            "rule_results": item["rule_results"],
            "inspection_date": "2026-09-11",
            "disclaimer": "AI-assisted compliance screening tool — Not an official government certification"
        }

        # Generate report
        pdf_path = report_gen.generate_pdf_report(scan_payload)

        db_id = save_scan(
            scan_id=scan_id,
            filename=filename,
            file_path=file_path,
            product_name=item["product_name"],
            brand=item["brand"],
            category=item["category"],
            barcode=item["barcode"],
            manufacturer=item["manufacturer"],
            overall_status=item["overall_status"],
            extracted_facts={"declarations": {"commodity_name": item["product_name"]}},
            rule_results=item["rule_results"],
            summary_counts=item["summary"],
            report_path=pdf_path,
            status="COMPLETED"
        )
        print(f"Seeded scan #{scan_id} -> Product: {item['product_name']} [{item['overall_status']}]")

    print("\nDemo data seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
