"""
Annotation Service for LabelSure.
Creates annotated package images with color-coded bounding boxes and text badges:
- PASS = GREEN (#10b981)
- FAIL = RED (#f43f5e)
- WARNING = AMBER (#f59e0b)
- NOT_VERIFIABLE = BLUE (#60a5fa)
- NOT_APPLICABLE = GRAY (#6b7280)
Never overwrites original uploaded images.
"""

import os
from PIL import Image, ImageDraw, ImageFont

COLOR_MAP = {
    "PASS": (16, 185, 129, 255),        # Emerald Green
    "FAIL": (244, 63, 94, 255),         # Rose Red
    "WARNING": (245, 158, 11, 255),     # Amber Yellow
    "NOT_VERIFIABLE": (96, 165, 250, 255), # Blue
    "NOT_APPLICABLE": (107, 114, 128, 255) # Gray
}

class AnnotationService:
    def create_annotated_image(self, original_image_path: str, rule_results: list, output_dir: str) -> tuple:
        """
        Draws bounding box annotations on image copy and saves to output_dir/annotated/.
        Returns (annotated_file_path, annotations_metadata_list).
        """
        if not os.path.exists(original_image_path):
            raise FileNotFoundError(f"Original image not found: {original_image_path}")

        annotated_dir = os.path.join(output_dir, "annotated")
        os.makedirs(annotated_dir, exist_ok=True)

        filename = os.path.basename(original_image_path)
        annotated_file_path = os.path.join(annotated_dir, f"annotated_{filename}")

        img = Image.open(original_image_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        annotations_metadata = []

        # Try loading font or fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        for rule in rule_results or []:
            bbox = rule.get("bbox")
            status = rule.get("status", "NOT_VERIFIABLE")
            rule_title = rule.get("title", rule.get("rule_number", "Declaration"))

            if not bbox or len(bbox) != 4:
                continue

            x, y, w, h = bbox
            color = COLOR_MAP.get(status, COLOR_MAP["NOT_VERIFIABLE"])

            # 1. Draw bounding box border (width 3px)
            draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

            # 2. Draw semi-transparent background fill inside box
            fill_color = (color[0], color[1], color[2], 30)
            draw.rectangle([x, y, x + w, y + h], fill=fill_color)

            # 3. Draw status badge header above bbox
            badge_text = f"[{status}] {rule_title}"
            badge_bg = (color[0], color[1], color[2], 220)
            
            # Badge text bounding box
            text_bbox = draw.textbbox((x, max(0, y - 24)), badge_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            badge_y = max(0, y - text_height - 6)
            draw.rectangle([x, badge_y, x + text_width + 12, badge_y + text_height + 6], fill=badge_bg)
            draw.text((x + 6, badge_y + 3), badge_text, fill=(255, 255, 255, 255), font=font)

            annotations_metadata.append({
                "rule_id": rule.get("rule_id"),
                "rule_number": rule.get("rule_number"),
                "title": rule_title,
                "status": status,
                "bbox": [x, y, w, h],
                "label": badge_text,
                "reason": rule.get("reason")
            })

        # Composite overlay with original image
        composed = Image.alpha_composite(img, overlay).convert("RGB")
        composed.save(annotated_file_path, "JPEG", quality=92)

        return annotated_file_path, annotations_metadata
