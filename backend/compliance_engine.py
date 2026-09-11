"""
Compliance Engine Orchestrator.
Connects Vision candidate facts, normalization, font scale measurement, and the deterministic Legal Metrology rule engine.
"""

from normalization import normalize_unit, normalize_text
from rules_engine import RulesEngine, RULE_SET_VERSION

LEGAL_SAFETY_DISCLAIMER = (
    "AI-assisted compliance screening based on implemented Legal Metrology packaged-commodity requirements. "
    "This system is designed for screening and compliance support; it is not an official government certification or legal judgment."
)

class ComplianceEngine:
    def __init__(self):
        self.rules_engine = RulesEngine()

    def process_scan(self, vision_output: dict, inspection_date: str = None, measurement_input: dict = None) -> dict:
        """
        Processes extracted vision facts and returns structured Legal Metrology compliance evaluation.
        """
        extracted_facts = vision_output.get("declarations", {})
        
        # Apply normalization to candidate facts
        if "net_quantity" in extracted_facts and isinstance(extracted_facts["net_quantity"], dict):
            unit = extracted_facts["net_quantity"].get("unit")
            if unit:
                extracted_facts["net_quantity"]["unit"] = normalize_unit(unit)

        if "commodity_name" in extracted_facts and isinstance(extracted_facts["commodity_name"], str):
            extracted_facts["commodity_name"] = normalize_text(extracted_facts["commodity_name"])

        # Run deterministic rule engine
        evaluation = self.rules_engine.evaluate_package(
            product_facts=vision_output,
            inspection_date=inspection_date,
            measurement_input=measurement_input
        )

        return {
            "overall_status": evaluation["overall_status"],  # COMPLIANT | NON_COMPLIANT | NEEDS_REVIEW
            "summary": evaluation["summary"],
            "detected_declarations": extracted_facts,
            "rule_results": evaluation["rule_results"],
            "measurement": measurement_input or {"method": "not_available"},
            "rule_set_version": evaluation["rule_set_version"],
            "inspection_date": evaluation["inspection_date"],
            "disclaimer": LEGAL_SAFETY_DISCLAIMER
        }
