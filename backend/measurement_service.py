"""
Measurement Service for LabelSure.
Calculates physical character height (in mm) from pixel bounding boxes using explicit scale inputs:
- package_dimension
- reference_object
- not_available

Never invents or estimates millimetre values without physical scale calibration.
"""

class MeasurementService:
    @staticmethod
    def calculate_scale(measurement_input: dict) -> dict:
        """
        Derives mm_per_px scale factor from physical scale calibration inputs.
        """
        if not measurement_input:
            measurement_input = {"method": "not_available"}

        method = measurement_input.get("method", "not_available")

        if method == "not_available":
            return {
                "method": "not_available",
                "scale_available": False,
                "mm_per_px": None,
                "reason": "No physical scale reference is available."
            }

        known_mm = measurement_input.get("known_physical_mm") or measurement_input.get("reference_physical_size_mm")
        known_px = measurement_input.get("known_pixel_span") or measurement_input.get("reference_pixel_size")

        if not known_mm or not known_px or float(known_px) <= 0 or float(known_mm) <= 0:
            return {
                "method": method,
                "scale_available": False,
                "mm_per_px": None,
                "reason": "Invalid or incomplete physical scale dimensions provided."
            }

        mm_per_px = float(known_mm) / float(known_px)
        px_per_mm = float(known_px) / float(known_mm)

        return {
            "method": method,
            "scale_available": True,
            "mm_per_px": mm_per_px,
            "px_per_mm": px_per_mm,
            "known_physical_mm": float(known_mm),
            "known_pixel_span": float(known_px),
            "confidence": measurement_input.get("confidence", 0.92)
        }

    def measure_declarations(self, declarations: dict, measurement_input: dict) -> list:
        """
        Measures text height in pixels and physical mm for detected declarations with bounding boxes.
        """
        scale_info = self.calculate_scale(measurement_input)
        measurements = []

        if not declarations:
            return measurements

        for decl_key, decl_val in declarations.items():
            if not decl_val:
                continue

            bbox = None
            conf = 0.90
            px_height = None

            if isinstance(decl_val, dict):
                bbox = decl_val.get("bbox")
                conf = decl_val.get("confidence", 0.90)
                if bbox and len(bbox) == 4:
                    px_height = bbox[3]  # height in pixels
            
            # Default pixel height estimate if bbox exists
            if px_height is None and bbox and len(bbox) == 4:
                px_height = bbox[3]

            if not bbox or not px_height:
                measurements.append({
                    "declaration": decl_key,
                    "bbox": None,
                    "pixel_height": None,
                    "estimated_mm_height": None,
                    "measurement_method": scale_info["method"],
                    "measurement_confidence": 0.0,
                    "status": "NOT_VERIFIABLE",
                    "reason": "Bounding box coordinates not detected for this declaration."
                })
                continue

            if scale_info["scale_available"]:
                estimated_mm = round(px_height * scale_info["mm_per_px"], 2)
                measurements.append({
                    "declaration": decl_key,
                    "bbox": bbox,
                    "pixel_height": px_height,
                    "estimated_mm_height": estimated_mm,
                    "measurement_method": scale_info["method"],
                    "reference_value": f"{scale_info['known_physical_mm']}mm = {scale_info['known_pixel_span']}px",
                    "measurement_confidence": conf,
                    "status": "MEASURED",
                    "reason": f"Measured text height of {px_height}px corresponds to estimated physical height of {estimated_mm}mm."
                })
            else:
                measurements.append({
                    "declaration": decl_key,
                    "bbox": bbox,
                    "pixel_height": px_height,
                    "estimated_mm_height": None,
                    "measurement_method": "not_available",
                    "measurement_confidence": conf,
                    "status": "NOT_VERIFIABLE",
                    "reason": "No physical scale reference is available. Physical height in mm cannot be derived."
                })

        return measurements
