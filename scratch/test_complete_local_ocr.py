import os
import cv2
import pytesseract
import numpy as np
import re

def detect_best_orientation(cv_img):
    """
    Evaluates 0, 90, 180, 270 deg rotations quickly using lightweight sample OCR.
    Returns (best_angle, rotated_img)
    """
    angles = [0, 90, 180, 270]
    scores = {}
    
    # Resize down to max 600px for speed
    h, w = cv_img.shape[:2]
    scale = 600.0 / max(h, w)
    small = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else cv_img

    # Packaging keyword hints
    kw_pattern = re.compile(r'\b(lic|no|mrp|rs|inr|net|qty|g|gm|kg|ml|mfg|mfd|date|exp|use|best|care|call|email|com|phone|toll|free|contact|address|consumer|marketed|manufactured|packed|product|batch|lot|fssai|india)\b', re.IGNORECASE)

    for angle in angles:
        if angle == 0:
            rot_small = small
        elif angle == 90:
            rot_small = cv2.rotate(small, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            rot_small = cv2.rotate(small, cv2.ROTATE_180)
        elif angle == 270:
            rot_small = cv2.rotate(small, cv2.ROTATE_90_COUNTERCLOCKWISE)

        gray = cv2.cvtColor(rot_small, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
        
        # Fast OCR pass with PSM 11
        try:
            txt = pytesseract.image_to_string(clahe, config='--psm 11').strip()
            # Words with 3+ alphabetic characters
            alpha_words = re.findall(r'[a-zA-Z]{3,}', txt)
            kw_matches = kw_pattern.findall(txt)
            
            # Score: 1 pt per alpha word, 15 pts per packaging keyword
            score = len(alpha_words) + (len(kw_matches) * 15)
            scores[angle] = score
        except Exception:
            scores[angle] = 0

    best_angle = max(scores, key=scores.get)
    # If 0 is close or all 0, default to 0
    if scores[best_angle] == 0:
        best_angle = 0

    # Rotate original image to best angle
    if best_angle == 0:
        best_img = cv_img
    elif best_angle == 90:
        best_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
    elif best_angle == 180:
        best_img = cv2.rotate(cv_img, cv2.ROTATE_180)
    elif best_angle == 270:
        best_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return best_angle, best_img, scores

print("Testing orientation detection on both images...")
img1 = cv2.imread('uploads/1789137133823_WhatsApp_Image_2026-09-10_at_11.53.06_AM.jpeg')
b1, _, s1 = detect_best_orientation(img1)
print(f"Image 1 (Bimbo): Best={b1} deg, Scores={s1}")

img2 = cv2.imread('uploads/1789069208079_WhatsApp_Image_2026-09-10_at_2.06.31_PM.jpeg')
b2, _, s2 = detect_best_orientation(img2)
print(f"Image 2 (PepsiCo): Best={b2} deg, Scores={s2}")
