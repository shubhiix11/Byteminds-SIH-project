"""
Measurement Engine for Character Height / Declaration Font Size.
Evaluates physical font sizes in mm using known scale references (package dimension or reference object).
Never converts pixels to mm without explicit physical scale information.
"""

class MeasurementEngine:
    @staticmethod
    def get_required_font_size_mm(net_qty_value: float, net_qty_unit: str) -> float:
        """
        Rule 7 Table 1 font size standards:
        - Up to 50g/ml: 1.0 mm
        - 50g/ml to 200g/ml: 2.0 mm
        - 200g/ml to 1kg/L: 4.0 mm
        - Above 1kg/L: 6.0 mm
        """
        if not net_qty_value or net_qty_value <= 0:
            return 1.0  # Default minimum threshold

        unit = (net_qty_unit or '').lower()
        # Convert kg/L to g/ml for threshold lookup
        qty_g_ml = net_qty_value
        if unit in ['kg', 'l']:
            qty_g_ml = net_qty_value * 1000

        if qty_g_ml <= 50:
            return 1.0
        elif qty_g_ml <= 200:
            return 2.0
        elif qty_g_ml <= 1000:
            return 4.0
        else:
            return 6.0

    @staticmethod
    def evaluate_character_height(pixel_height: float, measurement_input: dict, required_mm: float) -> dict:
        """
        Evaluates font height in mm against required_mm threshold.
        measurement_input schema:
        {
            "method": "package_dimension" | "reference_object" | "not_available",
            "known_physical_mm": 150.0,
            "known_pixel_span": 1500.0,
            "confidence": 0.95
        }
        """
        if not measurement_input:
            measurement_input = {"method": "not_available"}

        method = measurement_input.get("method", "not_available")
        confidence = measurement_input.get("confidence", 0.9)

        if method == "not_available" or not pixel_height or pixel_height <= 0:
            return {
                "status": "NOT_VERIFIABLE",
                "pixel_height": pixel_height,
                "estimated_mm_height": None,
                "measurement_method": "not_available",
                "reference_value": None,
                "measurement_confidence": 0.0,
                "reason": "Physical scale information (package dimensions or reference object) is not available. Pixel height cannot be converted to physical mm without physical scale calibration."
            }

        known_mm = measurement_input.get("known_physical_mm")
        known_px = measurement_input.get("known_pixel_span")

        if not known_mm or not known_px or known_px <= 0:
            return {
                "status": "NOT_VERIFIABLE",
                "pixel_height": pixel_height,
                "estimated_mm_height": None,
                "measurement_method": method,
                "reference_value": None,
                "measurement_confidence": 0.0,
                "reason": "Invalid or incomplete physical scale calibration data provided."
            }

        mm_per_px = float(known_mm) / float(known_px)
        estimated_mm = round(pixel_height * mm_per_px, 2)
        passed = estimated_mm >= required_mm

        return {
            "status": "PASS" if passed else "FAIL",
            "pixel_height": pixel_height,
            "estimated_mm_height": estimated_mm,
            "required_mm_height": required_mm,
            "measurement_method": method,
            "reference_value": f"{known_mm}mm = {known_px}px ({mm_per_px:.4f} mm/px)",
            "measurement_confidence": confidence,
            "reason": f"Estimated character height ({estimated_mm} mm) {'satisfies' if passed else 'fails'} the minimum required height of {required_mm} mm for this package size."
        }
