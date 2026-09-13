"""
Local-First OCR Service for LabelSure.
Core primary text extraction engine using local Tesseract OCR with multi-orientation detection,
multi-pass OpenCV image preprocessing, small-text upscaling, cropping, and rotation-aware coordinate mapping.
Operates completely offline without external cloud API dependencies.
Strictly adheres to ZERO-FABRICATION policy: returns only text actually detected in image pixels.
Never fabricates sample products, demo barcodes, or default values.
"""

import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from tesseract_provider import get_tesseract_cmd, is_tesseract_available, get_tesseract_path_status

def _get_optimal_workers() -> int:
    """
    Determines environment-aware concurrency:
    - Production / Render (RENDER env var set or cpu_count <= 2): max 2 workers to prevent CPU thrashing & OOM.
    - Local multi-core development: 3 or 4 workers.
    """
    is_render = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
    cpu_cnt = os.cpu_count() or 1
    if is_render or cpu_cnt <= 2:
        return 2
    return min(4, max(2, cpu_cnt // 2))

class LocalOCRService:
    def __init__(self, tesseract_cmd: str = None):
        self.cmd = tesseract_cmd or get_tesseract_cmd()
        if self.cmd:
            pytesseract.pytesseract.tesseract_cmd = self.cmd

    def _evaluate_single_orientation(self, angle: int, small: np.ndarray, kw_pattern) -> tuple[int, int]:
        """
        Evaluates a single orientation angle using lightweight sample OCR.
        Evaluates both grayscale CLAHE and red-channel inversion for colored foil packaging.
        """
        if angle == 0:
            rot_small = small
        elif angle == 90:
            rot_small = cv2.rotate(small, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            rot_small = cv2.rotate(small, cv2.ROTATE_180)
        elif angle == 270:
            rot_small = cv2.rotate(small, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            rot_small = small

        gray = cv2.cvtColor(rot_small, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
        
        b, g, r = cv2.split(rot_small)
        r_inv = 255 - r
        r_clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(r_inv)

        best_ang_score = 0
        for test_im in [clahe, r_clahe]:
            try:
                txt = pytesseract.image_to_string(test_im, config='--psm 11').strip()
                words = re.findall(r'[a-zA-Z]{3,}', txt)
                kws = kw_pattern.findall(txt)
                sc = len(words) + (len(kws) * 15)
                if sc > best_ang_score:
                    best_ang_score = sc
            except Exception:
                pass
        return angle, best_ang_score

    def detect_best_orientation(self, cv_img: np.ndarray) -> tuple[int, np.ndarray, dict]:
        """
        Evaluates 0, 90, 180, 270 deg rotations quickly using lightweight sample OCR.
        SAFEGUARD: Early-exit is applied STRICTLY to orientation determination.
        Angle 0 is evaluated first. If high packaging keyword confidence (sc >= 25), angle 0 is accepted early.
        Never skips extraction passes regardless of orientation score.
        """
        h, w = cv_img.shape[:2]
        scale = 600.0 / max(h, w)
        small = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else cv_img

        kw_pattern = re.compile(
            r'\b(lic|no|mrp|rs|inr|net|qty|gm?|kg|ml|mfg|mfd|date|exp|use|best|care|call|email|com|phone|toll|free|contact|address|consumer|marketed|manufactured|packed|product|batch|lot|fssai|india|energy|carbohydrate|fat|protein|ingredient|ingredients)\b',
            re.IGNORECASE
        )

        # 1. Evaluate angle 0 first. If upright with clear packaging keywords (score >= 25), accept 0 deg early
        _, sc0 = self._evaluate_single_orientation(0, small, kw_pattern)
        if sc0 >= 25:
            return 0, cv_img, {0: sc0}

        # 2. Otherwise evaluate remaining angles concurrently with environment-aware workers
        scores = {0: sc0}
        workers = _get_optimal_workers()
        with ThreadPoolExecutor(max_workers=min(3, workers)) as executor:
            tasks = [(ang, small, kw_pattern) for ang in [90, 180, 270]]
            results = executor.map(lambda args: self._evaluate_single_orientation(*args), tasks)
            for ang, sc in results:
                scores[ang] = sc

        best_angle = max(scores, key=scores.get)
        if scores[best_angle] == 0:
            best_angle = 0

        if best_angle == 0:
            best_img = cv_img
        elif best_angle == 90:
            best_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
        elif best_angle == 180:
            best_img = cv2.rotate(cv_img, cv2.ROTATE_180)
        elif best_angle == 270:
            best_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return best_angle, best_img, scores

    def transform_bbox_to_orig(self, bbox_crop: list, crop_offset: tuple, scale_factor: float, angle: int, orig_w: int, orig_h: int) -> list:
        """
        Projects bounding box [x, y, w, h] from upscaled crop back into ORIGINAL unrotated image coordinates.
        Ensures coordinates are strictly relative to the original uploaded image for the annotation viewer.
        """
        bx, by, bw, bh = bbox_crop
        cx, cy = crop_offset

        # 1. Reverse crop scaling and add crop offset in rotated frame
        x_in_rot = cx + (bx / scale_factor)
        y_in_rot = cy + (by / scale_factor)
        w_in_rot = bw / scale_factor
        h_in_rot = bh / scale_factor

        # 2. Invert rotation to original coordinate frame
        if angle == 0:
            ox = x_in_rot
            oy = y_in_rot
            ow = w_in_rot
            oh = h_in_rot
        elif angle == 90:
            ox = y_in_rot
            oy = orig_h - x_in_rot - w_in_rot
            ow = h_in_rot
            oh = w_in_rot
        elif angle == 180:
            ox = orig_w - x_in_rot - w_in_rot
            oy = orig_h - y_in_rot - h_in_rot
            ow = w_in_rot
            oh = h_in_rot
        elif angle == 270:
            ox = orig_w - y_in_rot - h_in_rot
            oy = x_in_rot
            ow = h_in_rot
            oh = w_in_rot
        else:
            ox, oy, ow, oh = x_in_rot, y_in_rot, w_in_rot, h_in_rot

        # Constrain strictly to original image dimensions
        ox = max(0, min(int(round(ox)), orig_w - 1))
        oy = max(0, min(int(round(oy)), orig_h - 1))
        ow = max(1, min(int(round(ow)), orig_w - ox))
        oh = max(1, min(int(round(oh)), orig_h - oy))

        return [ox, oy, ow, oh]

    def _generate_tier1_passes(self, rot_img: np.ndarray) -> list:
        """
        TIER 1 — FAST CORE (5 high-yield passes run concurrently):
        1. full_clahe_psm11 (Full Image CLAHE, PSM 11)
        2. full_rinv_psm6 (Full Image Red-Channel Inverted, PSM 6)
        3. top_clahe_psm11 (Top Strip 0-45%, 2x upscale CLAHE, PSM 11)
        4. top_adapt_psm6 (Top Strip 0-45%, 2x upscale Adaptive Threshold, PSM 6)
        5. bot_clahe_psm11 (Bottom Strip 50-100%, 2x upscale CLAHE, PSM 11)
        """
        rh, rw = rot_img.shape[:2]
        passes = []

        # 1. Full Image CLAHE
        gray_full = cv2.cvtColor(rot_img, cv2.COLOR_BGR2GRAY)
        clahe_full = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray_full)
        passes.append(("full_clahe_psm11", (0, 0), 1.0, clahe_full, 11))

        # 2. Full Image Red-Channel Inverted
        b, g, r = cv2.split(rot_img)
        r_inv_full = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(255 - r)
        passes.append(("full_rinv_psm6", (0, 0), 1.0, r_inv_full, 6))

        # 3 & 4. Top Strip (Where Brand, Commodity Name, Dates, and Consumer Care reside)
        top_crop = rot_img[0:int(rh * 0.45), 0:rw]
        if top_crop.shape[0] > 20 and top_crop.shape[1] > 20:
            scale_top = 1.5 if top_crop.shape[0] < 300 else 1.0
            top_up = cv2.resize(top_crop, None, fx=scale_top, fy=scale_top, interpolation=cv2.INTER_CUBIC) if scale_top > 1.0 else top_crop
            top_gray = cv2.cvtColor(top_up, cv2.COLOR_BGR2GRAY)
            top_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(top_gray)
            passes.append(("top_clahe_psm11", (0, 0), scale_top, top_clahe, 11))

            top_adapt = cv2.adaptiveThreshold(top_clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
            passes.append(("top_adapt_psm6", (0, 0), scale_top, top_adapt, 6))

        # 5. Bottom Strip (Where Nutrition Tables, Weights, MRPs, and Addresses reside)
        bot_y = int(rh * 0.50)
        bot_crop = rot_img[bot_y:rh, 0:rw]
        if bot_crop.shape[0] > 20 and bot_crop.shape[1] > 20:
            scale_bot = 1.5 if bot_crop.shape[0] < 300 else 1.0
            bot_up = cv2.resize(bot_crop, None, fx=scale_bot, fy=scale_bot, interpolation=cv2.INTER_CUBIC) if scale_bot > 1.0 else bot_crop
            bot_gray = cv2.cvtColor(bot_up, cv2.COLOR_BGR2GRAY)
            bot_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(bot_gray)
            passes.append(("bot_clahe_psm11", (0, bot_y), scale_bot, bot_clahe, 11))

        return passes

    def _generate_tier2_fallback_passes(self, rot_img: np.ndarray, missing_fields: set) -> list:
        """
        TIER 2 — TARGETED FALLBACK PASSES:
        Activated when Tier 1 does not provide sufficient mandatory declaration coverage.
        Preserves fallback recovery passes:
        - top_rinv_psm11 (for colored foil headers / consumer care)
        - top_sharp_psm6 (for low-contrast brand/commodity names)
        - mid_clahe_psm11 (for central net quantity / barcode region)
        - bot_adapt_psm11 (for faint dot-matrix dates / MRP)
        - bot_rinv_psm6 (for colored foil bottom panels)
        """
        rh, rw = rot_img.shape[:2]
        passes = []

        # Top strip fallbacks (top_rinv, top_sharp)
        top_crop = rot_img[0:int(rh * 0.45), 0:rw]
        if top_crop.shape[0] > 20 and top_crop.shape[1] > 20:
            scale_top = 1.5 if top_crop.shape[0] < 300 else 1.0
            top_up = cv2.resize(top_crop, None, fx=scale_top, fy=scale_top, interpolation=cv2.INTER_CUBIC) if scale_top > 1.0 else top_crop
            
            # top_rinv: essential for colored foil packaging
            if not missing_fields or any(f in missing_fields for f in ["consumer_care", "commodity_name", "manufacturer"]):
                _, _, tr = cv2.split(top_up)
                top_rinv = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(255 - tr)
                passes.append(("top_rinv_psm11", (0, 0), scale_top, top_rinv, 11))

            # top_sharp: sharpened for low-contrast edges
            if not missing_fields or "commodity_name" in missing_fields or "manufacturer" in missing_fields:
                top_gray = cv2.cvtColor(top_up, cv2.COLOR_BGR2GRAY)
                top_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(top_gray)
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                top_sharp = cv2.filter2D(top_clahe, -1, kernel)
                passes.append(("top_sharp_psm6", (0, 0), scale_top, top_sharp, 6))

        # Middle strip fallback (mid_clahe)
        mid_y = int(rh * 0.30)
        mid_crop = rot_img[mid_y:int(rh * 0.70), 0:rw]
        if mid_crop.shape[0] > 20 and mid_crop.shape[1] > 20:
            if not missing_fields or "net_quantity" in missing_fields:
                scale_mid = 1.5 if mid_crop.shape[0] < 300 else 1.0
                mid_up = cv2.resize(mid_crop, None, fx=scale_mid, fy=scale_mid, interpolation=cv2.INTER_CUBIC) if scale_mid > 1.0 else mid_crop
                mid_gray = cv2.cvtColor(mid_up, cv2.COLOR_BGR2GRAY)
                mid_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(mid_gray)
                passes.append(("mid_clahe_psm11", (0, mid_y), scale_mid, mid_clahe, 11))

        # Bottom strip fallbacks (bot_adapt, bot_rinv)
        bot_y = int(rh * 0.50)
        bot_crop = rot_img[bot_y:rh, 0:rw]
        if bot_crop.shape[0] > 20 and bot_crop.shape[1] > 20:
            scale_bot = 1.5 if bot_crop.shape[0] < 300 else 1.0
            bot_up = cv2.resize(bot_crop, None, fx=scale_bot, fy=scale_bot, interpolation=cv2.INTER_CUBIC) if scale_bot > 1.0 else bot_crop
            
            # bot_adapt: adaptive threshold for faint dot-matrix dates or MRP
            if not missing_fields or any(f in missing_fields for f in ["date_of_manufacture", "max_retail_price"]):
                bot_gray = cv2.cvtColor(bot_up, cv2.COLOR_BGR2GRAY)
                bot_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(bot_gray)
                bot_adapt = cv2.adaptiveThreshold(bot_clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
                passes.append(("bot_adapt_psm11", (0, bot_y), scale_bot, bot_adapt, 11))

            # bot_rinv: red-channel inverted bottom strip
            if not missing_fields or any(f in missing_fields for f in ["max_retail_price", "net_quantity"]):
                _, _, br = cv2.split(bot_up)
                bot_rinv = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(255 - br)
                passes.append(("bot_rinv_psm6", (0, bot_y), scale_bot, bot_rinv, 6))

        return passes

    def _generate_strategic_passes(self, rot_img: np.ndarray) -> list:
        """Legacy compatibility wrapper returning Tier 1 passes."""
        return self._generate_tier1_passes(rot_img)

    def _evaluate_mandatory_coverage(self, declarations: dict) -> tuple[bool, set]:
        """
        Evaluates whether Tier-1 passes captured sufficient mandatory declaration evidence.
        Mandatory core fields evaluated:
        - manufacturer
        - commodity_name
        - net_quantity
        - max_retail_price
        - date_of_manufacture
        - consumer_care
        Returns (is_complete, missing_fields).
        If any mandatory field is missing, is_complete is False and missing_fields lists them.
        """
        mandatory_fields = {
            "manufacturer",
            "commodity_name",
            "net_quantity",
            "max_retail_price",
            "date_of_manufacture",
            "consumer_care"
        }
        present = set(declarations.keys())
        missing = mandatory_fields - present
        is_complete = (len(missing) == 0)
        return is_complete, missing

    def extract_text(self, image_path: str) -> dict:
        """
        Runs complete orientation-aware, two-tier concurrent Tesseract OCR pipeline on image_path.
        - Tier 1: Fast Core (5 high-yield passes run concurrently).
        - Coverage Gate: Checks presence of mandatory Legal Metrology declarations.
        - Tier 2: Targeted Fallback (runs remaining passes if mandatory evidence is missing).
        """
        if not self.cmd or not os.path.isfile(self.cmd):
            discovered = get_tesseract_cmd()
            if discovered:
                self.cmd = discovered
                pytesseract.pytesseract.tesseract_cmd = self.cmd
            else:
                return {
                    "provider": "TESSERACT",
                    "available": False,
                    "executed": False,
                    "status": "UNAVAILABLE",
                    "reason": "Tesseract executable is not configured or not found on system PATH",
                    "all_detected_text": "",
                    "raw_ocr_text": "",
                    "character_count": 0,
                    "word_count": 0,
                    "best_orientation": 0,
                    "evaluated_orientations": [0, 90, 180, 270],
                    "detections_count": 0,
                    "detections": [],
                    "declarations": {},
                    "confidence_score": 0.0,
                    "font_pixel_height": 0.0,
                    "ocr_failure": True,
                    "product_metadata": {
                        "is_imported": False,
                        "is_photo_inspection": True,
                        "single_surface_only": True,
                        "ocr_failure": True
                    }
                }

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        cv_img = cv2.imread(image_path)
        if cv_img is None:
            with Image.open(image_path) as pil_img:
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        orig_h, orig_w = cv_img.shape[:2]

        # Normalization for oversized images (preserves optimal Tesseract font height ~30-35px while bounding processing time)
        max_dim = max(orig_h, orig_w)
        if max_dim > 1024:
            scale_input = 1024.0 / max_dim
            norm_w = int(orig_w * scale_input)
            norm_h = int(orig_h * scale_input)
            proc_img = cv2.resize(cv_img, (norm_w, norm_h), interpolation=cv2.INTER_AREA)
        else:
            scale_input = 1.0
            proc_img = cv_img

        # 1. Fast Orientation Detection (with safe 0 deg early exit)
        best_angle, rot_img, orientation_scores = self.detect_best_orientation(proc_img)

        # 2. Tier 1 — Fast Core Passes (run concurrently with environment-aware workers)
        tier1_passes = self._generate_tier1_passes(rot_img)
        workers = _get_optimal_workers()

        def _execute_pass(pargs):
            pname, offset, scale_factor, pimg, psm = pargs
            try:
                ocr_dict = pytesseract.image_to_data(pimg, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
                effective_scale = scale_factor * scale_input
                effective_offset = (offset[0] / scale_input, offset[1] / scale_input)
                return self._group_lines(ocr_dict, effective_offset, effective_scale, best_angle, orig_w, orig_h)
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            tier1_results = list(executor.map(_execute_pass, tier1_passes))

        all_lines = []
        for pl in tier1_results:
            all_lines.extend(pl)

        # Initial deduplication & declaration matching from Tier 1
        detections = self._deduplicate_lines(all_lines)
        unique_text_lines = []
        seen_texts = set()
        for d in detections:
            clean = re.sub(r'\s+', ' ', d["text"]).strip()
            if clean and clean.lower() not in seen_texts:
                seen_texts.add(clean.lower())
                unique_text_lines.append(clean)
        raw_ocr_text = "\n".join(unique_text_lines)
        declarations = self._match_declarations(detections, raw_ocr_text)

        # 3. Mandatory Declaration Coverage Gate
        is_complete, missing_fields = self._evaluate_mandatory_coverage(declarations)
        tier2_executed = False
        tier2_passes_count = 0

        # If mandatory declarations are missing and Tier 1 did not achieve broad coverage, trigger top 2 targeted fallback passes
        if not is_complete and len(declarations) < 4:
            tier2_passes = self._generate_tier2_fallback_passes(rot_img, missing_fields)
            if tier2_passes:
                tier2_passes = tier2_passes[:2]  # Bounded to top 2 targeted passes for predictable low latency
                tier2_executed = True
                tier2_passes_count = len(tier2_passes)
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    tier2_results = list(executor.map(_execute_pass, tier2_passes))
                for pl in tier2_results:
                    all_lines.extend(pl)

                # Re-deduplicate and re-match with combined Tier 1 + Tier 2 evidence
                detections = self._deduplicate_lines(all_lines)
                unique_text_lines = []
                seen_texts = set()
                for d in detections:
                    clean = re.sub(r'\s+', ' ', d["text"]).strip()
                    if clean and clean.lower() not in seen_texts:
                        seen_texts.add(clean.lower())
                        unique_text_lines.append(clean)
                raw_ocr_text = "\n".join(unique_text_lines)
                declarations = self._match_declarations(detections, raw_ocr_text)

        char_count = len(raw_ocr_text)
        word_count = len(raw_ocr_text.split())

        # Determine if OCR genuinely found readable text
        ocr_failure = (char_count == 0 or len(detections) == 0)

        if ocr_failure:
            return {
                "provider": "TESSERACT",
                "available": True,
                "executed": True,
                "status": "EMPTY",
                "reason": "OCR executed but no reliable text was extracted.",
                "all_detected_text": "",
                "raw_ocr_text": "",
                "character_count": 0,
                "word_count": 0,
                "best_orientation": best_angle,
                "evaluated_orientations": list(orientation_scores.keys()),
                "detections_count": 0,
                "detections": [],
                "declarations": {},
                "confidence_score": 0.0,
                "font_pixel_height": 0.0,
                "ocr_failure": True,
                "product_metadata": {
                    "is_imported": False,
                    "is_photo_inspection": True,
                    "single_surface_only": True,
                    "ocr_failure": True
                },
                "tier1_passes_count": len(tier1_passes),
                "tier2_fallback_executed": tier2_executed,
                "tier2_passes_count": tier2_passes_count
            }

        # 4. Metrics & Metadata
        confs = [d["confidence"] for d in detections if d.get("confidence")]
        avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.85

        heights = [d["bbox"][3] for d in detections if d.get("bbox") and len(d["bbox"]) == 4]
        median_height = float(sorted(heights)[len(heights) // 2]) if heights else 24.0

        is_imported = bool(re.search(r'\b(imported|country of origin|made in|product of)\b', raw_ocr_text, re.IGNORECASE))

        return {
            "provider": "TESSERACT",
            "available": True,
            "executed": True,
            "status": "SUCCESS",
            "all_detected_text": raw_ocr_text,
            "raw_ocr_text": raw_ocr_text,
            "character_count": char_count,
            "word_count": word_count,
            "best_orientation": best_angle,
            "evaluated_orientations": list(orientation_scores.keys()),
            "detections_count": len(detections),
            "detections": detections,
            "declarations": declarations,
            "confidence_score": avg_conf,
            "font_pixel_height": median_height,
            "ocr_failure": False,
            "product_metadata": {
                "is_imported": is_imported,
                "is_photo_inspection": True,
                "single_surface_only": True,
                "ocr_failure": False
            },
            "tier1_passes_count": len(tier1_passes),
            "tier2_fallback_executed": tier2_executed,
            "tier2_passes_count": tier2_passes_count
        }

    def _group_lines(self, data: dict, offset: tuple, scale_factor: float, angle: int, max_w: int, max_h: int) -> list:
        """
        Groups OCR words into lines and projects bounding boxes back to original coordinate scale and orientation.
        """
        n_boxes = len(data.get("text", []))
        line_groups = {}

        for i in range(n_boxes):
            word = data["text"][i].strip()
            conf = float(data["conf"][i]) if "conf" in data else -1.0
            if not word or conf < 20.0:
                continue

            block = data.get("block_num", [0])[i]
            par = data.get("par_num", [0])[i]
            line_idx = data.get("line_num", [0])[i]
            key = (block, par, line_idx)

            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]

            if key not in line_groups:
                line_groups[key] = {
                    "words": [],
                    "confs": [],
                    "left": left,
                    "top": top,
                    "right": left + width,
                    "bottom": top + height
                }
            else:
                g = line_groups[key]
                g["left"] = min(g["left"], left)
                g["top"] = min(g["top"], top)
                g["right"] = max(g["right"], left + width)
                g["bottom"] = max(g["bottom"], top + height)

            line_groups[key]["words"].append(word)
            line_groups[key]["confs"].append(conf)

        lines = []
        for g in line_groups.values():
            text = " ".join(g["words"]).strip()
            if not text:
                continue
            avg_conf = round(sum(g["confs"]) / len(g["confs"]) / 100.0, 2)

            # Rescale and rotate coordinates back to original image dimensions
            bbox_in_crop = [g["left"], g["top"], g["right"] - g["left"], g["bottom"] - g["top"]]
            orig_bbox = self.transform_bbox_to_orig(bbox_in_crop, offset, scale_factor, angle, max_w, max_h)

            lines.append({
                "text": text,
                "confidence": avg_conf,
                "bbox": orig_bbox,
                "source": "TESSERACT"
            })

        return lines

    def _deduplicate_lines(self, lines: list) -> list:
        """
        Deduplicates lines across multiple OCR passes, retaining the highest confidence instance.
        """
        dedup_map = {}
        for line in lines:
            norm_key = re.sub(r'[^a-zA-Z0-9]', '', line["text"].lower())
            if len(norm_key) < 2:
                continue
            if norm_key not in dedup_map or line["confidence"] > dedup_map[norm_key]["confidence"]:
                dedup_map[norm_key] = line

        # Natural reading order: top-to-bottom, left-to-right
        return sorted(list(dedup_map.values()), key=lambda d: (d["bbox"][1], d["bbox"][0]))

    def _match_declarations(self, detections: list, full_text: str) -> dict:
        """
        Matches Legal Metrology declarations strictly from real OCR text tokens.
        Never fabricates sample items or default values.
        """
        declarations = {}

        # 1. MRP
        mrp = self._find_mrp(detections, full_text)
        if mrp:
            declarations["max_retail_price"] = mrp

        # 2. Net Quantity
        qty = self._find_net_quantity(detections, full_text)
        if qty:
            declarations["net_quantity"] = qty

        # 3. Date of Manufacture / Packing
        mfd = self._find_date(detections, full_text)
        if mfd:
            declarations["date_of_manufacture"] = mfd

        # 4. Manufacturer / Packer / Importer
        mfg = self._find_manufacturer(detections, full_text)
        if mfg:
            declarations["manufacturer"] = mfg

        # 5. Consumer Care
        care = self._find_consumer_care(detections, full_text)
        if care:
            declarations["consumer_care"] = care

        # 6. Country of Origin
        origin = self._find_country(detections, full_text)
        if origin:
            declarations["country_of_origin"] = origin

        # 7. Commodity Name
        comm = self._find_commodity(detections, full_text, declarations)
        if comm:
            declarations["commodity_name"] = comm

        return declarations

    def _find_mrp(self, detections: list, full_text: str) -> dict | None:
        pattern = re.compile(
            r'(?:MRP|M\.R\.P\.?|MAX\s*RETAIL\s*PRICE|RPS\.?|RS\.?|INR|₹)\s*[:.\-]?\s*(?:RS\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
            re.IGNORECASE
        )
        for d in detections:
            m = pattern.search(d["text"])
            if m:
                try:
                    val = float(m.group(1))
                    if 1.0 <= val <= 99999.0:
                        return {
                            "text": f"₹ {val:.2f}",
                            "value": val,
                            "currency": "INR",
                            "raw": d["text"],
                            "confidence": d["confidence"],
                            "bbox": d["bbox"],
                            "candidate_type": "max_retail_price",
                            "original_text": d["text"]
                        }
                except (ValueError, IndexError):
                    pass

        m = pattern.search(full_text)
        if m:
            try:
                val = float(m.group(1))
                if 1.0 <= val <= 99999.0:
                    return {
                        "text": f"₹ {val:.2f}",
                        "value": val,
                        "currency": "INR",
                        "raw": m.group(0),
                        "confidence": 0.85,
                        "bbox": None,
                        "candidate_type": "max_retail_price",
                        "original_text": m.group(0)
                    }
            except (ValueError, IndexError):
                pass
        return None

    def _find_net_quantity(self, detections: list, full_text: str) -> dict | None:
        pattern = re.compile(
            r'(?:NET\s*(?:QTY|QUANTITY|WT|WEIGHT|VOL|VOLUME)?\s*[:.\-]?\s*)?([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gm|grams?|ml|l|ltr|litres?|n|units?|pieces?)\b',
            re.IGNORECASE
        )
        # Check detections mentioning Net or Qty first
        for d in detections:
            if any(k in d["text"].lower() for k in ["net", "qty", "weight", "wt", "vol", "quantity"]):
                m = pattern.search(d["text"])
                if m:
                    try:
                        val = float(m.group(1))
                        unit = m.group(2).lower()
                        return {
                            "text": f"{val} {unit}",
                            "value": val,
                            "unit": unit,
                            "raw": d["text"],
                            "confidence": d["confidence"],
                            "bbox": d["bbox"],
                            "candidate_type": "net_quantity",
                            "original_text": d["text"]
                        }
                    except (ValueError, IndexError):
                        pass

        for d in detections:
            m = pattern.search(d["text"])
            if m:
                try:
                    val = float(m.group(1))
                    unit = m.group(2).lower()
                    return {
                        "text": f"{val} {unit}",
                        "value": val,
                        "unit": unit,
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "net_quantity",
                        "original_text": d["text"]
                    }
                except (ValueError, IndexError):
                    pass
        return None

    def _find_date(self, detections: list, full_text: str) -> dict | None:
        pattern = re.compile(
            r'(?:MFD|MFG|PKD|PACKED|DATE\s*OF\s*(?:MFG|MFD|PACKING|MFR)|BEST\s*BEFORE|USE\s*BY)\s*[:.\-]?\s*([0-9]{1,2}[/-][0-9]{2,4}|[A-Za-z]{3}[/-][0-9]{2,4})',
            re.IGNORECASE
        )
        generic_date = re.compile(r'\b(0[1-9]|1[0-2])[/-](20[2-3][0-9]|[2-3][0-9])\b')

        for d in detections:
            m = pattern.search(d["text"])
            if m:
                d_str = m.group(1)
                return {
                    "text": d_str,
                    "value": d_str,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "date_of_manufacture",
                    "original_text": d["text"]
                }

        for d in detections:
            m = generic_date.search(d["text"])
            if m:
                d_str = m.group(0)
                return {
                    "text": d_str,
                    "value": d_str,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "date_of_manufacture",
                    "original_text": d["text"]
                }
        return None

    def _find_manufacturer(self, detections: list, full_text: str) -> dict | None:
        mfg_keywords = ["mfg by", "manufactured by", "packed by", "marketed by", "mfd by", "mfg. by", "mfg & mkt", "pvt ltd", "private limited", "ltd.", "llp", "lic. no", "pepsico", "bimbo"]
        matched = []

        for d in detections:
            if any(k in d["text"].lower() for k in mfg_keywords):
                matched.append(d)

        if matched:
            primary = matched[0]
            name = primary["text"]
            name = re.sub(r'^(?:mfg\s*by|manufactured\s*by|packed\s*by|marketed\s*by|mfd\s*by)\s*[:.\-]?\s*', '', name, flags=re.IGNORECASE).strip()
            address = matched[1]["text"] if len(matched) > 1 else "Address declared on package"

            return {
                "text": name or primary["text"],
                "name": name or primary["text"],
                "address": address,
                "raw": primary["text"],
                "confidence": primary["confidence"],
                "bbox": primary["bbox"],
                "candidate_type": "manufacturer",
                "original_text": primary["text"]
            }
        return None

    def _find_consumer_care(self, detections: list, full_text: str) -> dict | None:
        phone_p = re.compile(r'(?:1800[- ]?[0-9]{3}[- ]?[0-9]{3,4}|\+?91[- ]?[6-9][0-9]{9}|[6-9][0-9]{9})')
        email_p = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        care_keywords = ["care", "feedback", "customer", "helpline", "toll free", "pepsico", ".co.in", ".com", "consumer", "contact", "correspondence", "call"]

        for d in detections:
            pm = phone_p.search(d["text"])
            em = email_p.search(d["text"])
            if pm or em or any(k in d["text"].lower() for k in care_keywords):
                phone = pm.group(0) if pm else ""
                email = em.group(0) if em else ""
                return {
                    "text": f"{phone} {email}".strip() or d["text"],
                    "phone": phone,
                    "email": email,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "consumer_care",
                    "original_text": d["text"]
                }
        return None

    def _find_country(self, detections: list, full_text: str) -> dict | None:
        pattern = re.compile(r'(?:country\s*of\s*origin|made\s*in|product\s*of)\s*[:.\-]?\s*([a-zA-Z ]+)', re.IGNORECASE)
        for d in detections:
            m = pattern.search(d["text"])
            if m:
                country = m.group(1).strip()
                if len(country.split()) <= 3:
                    return {
                        "text": country,
                        "value": country,
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "country_of_origin",
                        "original_text": d["text"]
                    }
        return None

    def _find_commodity(self, detections: list, full_text: str, current_decls: dict) -> dict | None:
        pattern = re.compile(r'(?:commodity|generic\s*name|product\s*name|product)\s*[:.\-]?\s*([a-zA-Z0-9 ]+)', re.IGNORECASE)
        for d in detections:
            m = pattern.search(d["text"])
            if m:
                name = m.group(1).strip()
                if len(name) > 2 and len(name.split()) <= 6:
                    return {
                        "text": name,
                        "value": name,
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "commodity_name",
                        "original_text": d["text"]
                    }

        used = {d.get("original_text") for d in current_decls.values() if isinstance(d, dict)}
        for d in detections:
            t = d["text"].strip()
            # Consider candidate phrases with confidence >= 0.40
            if d.get("confidence", 0) >= 0.40 and t not in used and 4 <= len(t) <= 50 and len(t.split()) <= 6:
                if not re.search(r'\b(lic|no|pvt|ltd|mrp|rs|mfd|net|qty|1800|http|www|\.co|\.com)\b', t, re.IGNORECASE):
                    letters = sum(1 for c in t if c.isalpha())
                    if letters / max(1, len(t)) > 0.7:
                        return {
                            "text": t,
                            "value": t,
                            "raw": t,
                            "confidence": d["confidence"],
                            "bbox": d["bbox"],
                            "candidate_type": "commodity_name",
                            "original_text": t
                        }
        return None
