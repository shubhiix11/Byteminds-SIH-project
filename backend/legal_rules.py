"""
Versioned Legal Metrology (Packaged Commodities) Rules Dataset.
Sourced from the Department of Consumer Affairs, Government of India:
https://consumeraffairs.gov.in/pages/legal-metrology-act
"""

LEGAL_METROLOGY_RULES = [
    {
        "rule_id": "R6_1_A",
        "rule_number": "Rule 6(1)(a)",
        "title": "Name and Address of Manufacturer / Packer / Importer",
        "requirement": "Every package shall bear the name and complete address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer, or for imported packages, the importer.",
        "applicability": "Universal for all packaged commodities",
        "mandatory": True,
        "validation_type": "MANUFACTURER_DECLARATION",
        "expected_format": "Name of Company/Firm + Street/Area/City Address with Pin Code",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(a), DCA Notification GSR 426(E)",
        "notes": "Mandatory declaration on every principal display panel or package."
    },
    {
        "rule_id": "R6_1_B",
        "rule_number": "Rule 6(1)(b)",
        "title": "Common or Generic Name of Commodity",
        "requirement": "Every package shall bear the common or generic name of the commodity contained in the package.",
        "applicability": "Universal for all packaged commodities",
        "mandatory": True,
        "validation_type": "COMMODITY_NAME",
        "expected_format": "Plain language generic or common trade name of product",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(b), DCA Notification GSR 426(E)",
        "notes": "Must clearly identify the generic nature of contents."
    },
    {
        "rule_id": "R6_1_C",
        "rule_number": "Rule 6(1)(c)",
        "title": "Net Quantity Declaration",
        "requirement": "Every package shall bear the net quantity, in terms of standard unit of weight, measure or number.",
        "applicability": "Universal for all packaged commodities",
        "mandatory": True,
        "validation_type": "NET_QUANTITY",
        "expected_format": "Numeric quantity followed by standard unit symbol (g, kg, ml, L, m, N, U)",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(c), DCA Notification GSR 426(E)",
        "notes": "Standard metric unit symbols prescribed under Legal Metrology standards."
    },
    {
        "rule_id": "R6_1_D",
        "rule_number": "Rule 6(1)(d)",
        "title": "Month and Year of Manufacture / Packing / Import",
        "requirement": "Every package shall bear the month and year in which the commodity is manufactured or packed or imported.",
        "applicability": "All packaged commodities except exempted categories (e.g. fresh produce, bidi, LPG)",
        "mandatory": True,
        "validation_type": "DATE_DECLARATION",
        "expected_format": "Month and Year in MM/YYYY, MM-YYYY, or Month Year format",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(d), DCA Notification GSR 426(E)",
        "notes": "Mandatory for tracking manufacturing timeline and shelf validity."
    },
    {
        "rule_id": "R6_1_E",
        "rule_number": "Rule 6(1)(e)",
        "title": "Maximum Retail Price (MRP)",
        "requirement": "Every package shall bear the maximum retail price at which the commodity may be sold to the ultimate consumer inclusive of all taxes.",
        "applicability": "Universal for retail packaged commodities",
        "mandatory": True,
        "validation_type": "MRP_DECLARATION",
        "expected_format": "MRP ₹ xx.xx (Incl. of all taxes) or MRP Rs. xx.xx (inclusive of all taxes)",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(e), DCA Notification GSR 426(E)",
        "notes": "Must explicitly state price with currency symbol and tax inclusive clause."
    },
    {
        "rule_id": "R6_1_F",
        "rule_number": "Rule 6(1)(f)",
        "title": "Consumer Care Details",
        "requirement": "Every package shall bear name, address, telephone number, and e-mail address of the person or office who can be contacted in case of consumer complaints.",
        "applicability": "Universal for retail packaged commodities",
        "mandatory": True,
        "validation_type": "CONSUMER_CARE",
        "expected_format": "Phone / Hotline + Email Address + Contact Officer Address",
        "measurement_requirement": None,
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 6(1)(f), DCA Notification GSR 426(E)",
        "notes": "Mandatory consumer grievance redressal contact point."
    },
    {
        "rule_id": "R6_1_G",
        "rule_number": "Rule 6(1)(g)",
        "title": "Country of Origin for Imported Products",
        "requirement": "When a package contains imported commodities, the package shall clearly declare the country of origin.",
        "applicability": "Conditional: Mandatory ONLY when is_imported is True or item is imported",
        "mandatory": True,  # Conditional mandatory
        "validation_type": "COUNTRY_OF_ORIGIN",
        "expected_format": "Country of Origin: [Country Name] or Made in [Country Name]",
        "measurement_requirement": None,
        "effective_from": "2017-06-23",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Amendment Rules, 2017",
        "source_reference": "Rule 6(1)(g), DCA Notification GSR 629(E)",
        "notes": "Applicable specifically to imported products."
    },
    {
        "rule_id": "R6_1_H",
        "rule_number": "Rule 6(1)(h)",
        "title": "Unit Sale Price Declaration",
        "requirement": "Declaration of Unit Sale Price on packages containing net quantity more than 1 g / 1 ml / 1 metre or multi-unit packages.",
        "applicability": "Conditional: Applicable to packages with net quantity > 1g / 1ml or multi-unit retail packages",
        "mandatory": True,
        "validation_type": "UNIT_SALE_PRICE",
        "expected_format": "₹ xx.xx per g / per kg / per ml / per L / per number",
        "measurement_requirement": None,
        "effective_from": "2022-02-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Amendment Rules, 2021",
        "source_reference": "Rule 6(1)(h), DCA Notification GSR 779(E)",
        "notes": "Unit sale price mandatory for consumer transparency in retail packages."
    },
    {
        "rule_id": "R6_1_I_FONT",
        "rule_number": "Rule 6(1)(i) & Rule 7",
        "title": "Minimum Height of Declarations (Character Height)",
        "requirement": "The height of any numeral and letter in the declaration on the package shall not be less than the minimum height specified in Rule 7 based on net quantity range.",
        "applicability": "Universal for principal display panel declarations",
        "mandatory": True,
        "validation_type": "CHARACTER_HEIGHT",
        "expected_format": "Minimum physical letter height in mm (e.g. >= 1.0mm, >= 2.0mm, >= 4.0mm, >= 6.0mm)",
        "measurement_requirement": "physical_scale",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_reference": "Rule 7, Table 1 - Minimum Height of Numerals",
        "notes": "Requires physical measurement scale. Returns NOT_VERIFIABLE if physical scale is unavailable."
    },
    {
        "rule_id": "R_ECOM_FILTER_2026",
        "rule_number": "Rule 6(10) E-Commerce Amendment",
        "title": "E-Commerce Searchable Country of Origin Filter",
        "requirement": "E-commerce entities shall provide a searchable and sortable country-of-origin filter for imported products listed online.",
        "applicability": "E-Commerce Digital Platforms Only (NOT verifiable from physical package photograph)",
        "mandatory": False,
        "validation_type": "ECOMMERCE_FILTER",
        "expected_format": "Digital search metadata filter",
        "measurement_requirement": None,
        "effective_from": "2026-07-01",
        "effective_to": None,
        "source_title": "Legal Metrology (Packaged Commodities) Amendment Rules, 2026",
        "source_reference": "DCA Notification Feb 13, 2026 Amendment",
        "notes": "E-commerce platform software check. Excluded from package photograph inspection -> NOT_APPLICABLE for photo scans."
    }
]

def get_rules_for_date(inspection_date_str: str) -> list:
    """
    Returns rules effective as of inspection_date_str (YYYY-MM-DD).
    """
    if not inspection_date_str:
        return LEGAL_METROLOGY_RULES

    valid_rules = []
    for rule in LEGAL_METROLOGY_RULES:
        eff_from = rule.get("effective_from")
        eff_to = rule.get("effective_to")

        if eff_from and inspection_date_str < eff_from:
            continue
        if eff_to and inspection_date_str > eff_to:
            continue

        valid_rules.append(rule)

    return valid_rules
