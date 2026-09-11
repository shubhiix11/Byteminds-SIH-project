"""
Productization Test Suite for LabelSure (Prompt 5).
Verifies PDF report generation, database persistence, search/filter queries, product history, and dashboard analytics.
"""

import unittest
import os
import json
from database import init_db, save_scan, get_all_scans, get_scan_by_id, get_dashboard_analytics, get_product_history
from report_generator import ReportGenerator

class TestProductization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.reports_dir = os.path.abspath("scratch/test_reports")
        cls.report_gen = ReportGenerator(cls.reports_dir)

    def test_01_pdf_report_generation(self):
        sample_scan = {
            "scan_id": "TEST_SCAN_101",
            "product_name": "Test Product",
            "brand": "Test Brand",
            "overall_status": "NON_COMPLIANT",
            "summary": {"rules_checked": 10, "passed": 7, "failed": 1, "warnings": 0, "not_verifiable": 1, "not_applicable": 1},
            "detected_declarations": {"commodity_name": "Test Product", "net_quantity": {"value": 500, "unit": "g"}},
            "rule_results": [
                {"rule_number": "Rule 6(1)(a)", "title": "Manufacturer", "status": "FAIL", "reason": "Missing declaration", "source_reference": "Rule 6(1)(a)"}
            ],
            "inspection_date": "2026-09-11",
            "disclaimer": "AI-assisted compliance screening tool — Not an official government certification"
        }
        pdf_path = self.report_gen.generate_pdf_report(sample_scan)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith("report_TEST_SCAN_101.pdf"))

    def test_02_database_save_and_retrieve(self):
        scan_id = f"SCAN_TEST_{int(os.times().user * 1000)}"
        db_scan_id = save_scan(
            scan_id=scan_id,
            filename="test_img.jpg",
            file_path="/tmp/test_img.jpg",
            product_name="Database Test Product",
            brand="DB Brand",
            category="Packaged Food",
            barcode="8901112223334",
            manufacturer="DB Mfg Ltd",
            overall_status="COMPLIANT",
            extracted_facts={"declarations": {}},
            rule_results=[{"rule_number": "Rule 6(1)(c)", "status": "PASS"}],
            summary_counts={"rules_checked": 10, "passed": 10, "failed": 0, "warnings": 0, "not_verifiable": 0, "not_applicable": 0},
            status="COMPLETED"
        )
        self.assertEqual(db_scan_id, scan_id)

        retrieved = get_scan_by_id(scan_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["product_name"], "Database Test Product")
        self.assertEqual(retrieved["overall_status"], "COMPLIANT")

    def test_03_database_search_and_filter(self):
        # Search by product name
        scans_search = get_all_scans(search="Database Test Product")
        self.assertGreater(len(scans_search), 0)
        self.assertEqual(scans_search[0]["product_name"], "Database Test Product")

        # Filter by status
        scans_compliant = get_all_scans(status="COMPLIANT")
        self.assertGreater(len(scans_compliant), 0)
        for s in scans_compliant:
            self.assertEqual(s["overall_status"], "COMPLIANT")

    def test_04_product_inspection_history(self):
        # Save multiple inspections for same product
        prod_name = "Multi Inspection Commodity"
        save_scan(scan_id="INSP_1", filename="1.jpg", file_path="/tmp/1.jpg", product_name=prod_name, overall_status="FAIL", extracted_facts={})
        save_scan(scan_id="INSP_2", filename="2.jpg", file_path="/tmp/2.jpg", product_name=prod_name, overall_status="COMPLIANT", extracted_facts={})

        history = get_product_history(prod_name)
        self.assertGreaterEqual(len(history), 2)
        # Newest inspection comes first
        self.assertEqual(history[0]["scan_id"], "INSP_2")
        self.assertEqual(history[1]["scan_id"], "INSP_1")

    def test_05_dashboard_analytics_aggregation(self):
        analytics = get_dashboard_analytics()
        self.assertIn("total_inspections", analytics)
        self.assertIn("compliant_count", analytics)
        self.assertIn("non_compliant_count", analytics)
        self.assertIn("needs_review_count", analytics)
        self.assertIn("common_violations", analytics)
        self.assertIn("recent_scans", analytics)
        self.assertGreaterEqual(analytics["total_inspections"], 1)

if __name__ == "__main__":
    unittest.main()
