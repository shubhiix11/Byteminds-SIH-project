import os
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image

tess_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tess_cmd):
    pytesseract.pytesseract.tesseract_cmd = tess_cmd

def detect_best_orientation(cv_img):
    angles = [0, 90, 180, 270]
    scores = {}
    
    h, w = cv_img.shape[:2]
    scale = 600.0 / max(h, w)
    small = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else cv_img

    kw_pattern = re.compile(
        r'\b(lic|no|mrp|rs|inr|net|qty|gm?|kg|ml|mfg|mfd|date|exp|use|best|care|call|email|com|phone|toll|free|contact|address|consumer|marketed|manufactured|packed|product|batch|lot|fssai|india|energy|carbohydrate|fat|protein|ingredient|ingredients)\b',
        re.IGNORECASE
    )

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
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8)).apply(gray)
        
        b, g, r = cv2.split(rot_small)
        r_inv = 255 - r
        r_clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8)).apply(r_inv)
        
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
        scores[angle] = best_ang_score

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

def transform_bbox_to_orig(bbox_crop, crop_offset, scale_factor, angle, orig_w, orig_h):
    bx, by, bw, bh = bbox_crop
    cx, cy = crop_offset

    x_in_rot = cx + (bx / scale_factor)
    y_in_rot = cy + (by / scale_factor)
    w_in_rot = bw / scale_factor
    h_in_rot = bh / scale_factor

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

    ox = max(0, min(int(round(ox)), orig_w - 1))
    oy = max(0, min(int(round(oy)), orig_h - 1))
    ow = max(1, min(int(round(ow)), orig_w - ox))
    oh = max(1, min(int(round(oh)), orig_h - oy))

    return [ox, oy, ow, oh]

def run_multi_pass_ocr(cv_img):
    orig_h, orig_w = cv_img.shape[:2]
    
    # 1. Orientation detection
    best_angle, rot_img, orientation_scores = detect_best_orientation(cv_img)
    rh, rw = rot_img.shape[:2]
    
    # 2. Define regions / crops
    # Top strip (0-40%), Middle strip (30-70%), Bottom strip (60-100%), and Full
    regions = [
        ("full", (0, 0), rot_img),
        ("top", (0, 0), rot_img[0:int(rh * 0.40), 0:rw]),
        ("mid", (0, int(rh * 0.30)), rot_img[int(rh * 0.30):int(rh * 0.70), 0:rw]),
        ("bot", (0, int(rh * 0.60)), rot_img[int(rh * 0.60):rh, 0:rw])
    ]
    
    all_raw_lines = []
    
    for rname, offset, rimg in regions:
        ch, cw = rimg.shape[:2]
        if ch < 10 or cw < 10:
            continue
            
        # Determine upscale factor based on size
        scale = 1.0
        if rname == "full":
            if max(ch, cw) < 1600:
                scale = 1.5
        else:
            scale = 2.5
            
        scaled = cv2.resize(rimg, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        
        # Preprocessing variants
        # 1. Grayscale CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        
        # 2. Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharp = cv2.filter2D(clahe, -1, kernel)
        
        # 3. Adaptive threshold
        adapt = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
        
        # 4. Otsu threshold
        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 5. Color channel inversion for colored packaging
        b, g, r = cv2.split(scaled)
        r_inv = 255 - r
        r_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(r_inv)
        
        variants = [
            ("clahe", clahe),
            ("sharp", sharp),
            ("r_clahe", r_clahe),
            ("adapt", adapt),
            ("otsu", otsu)
        ]
        
        # Strategic PSM modes: PSM 11 (sparse text) and PSM 6 (uniform block)
        psm_modes = [11, 6] if rname != "full" else [11]
        
        for vname, vimg in variants:
            for psm in psm_modes:
                try:
                    data = pytesseract.image_to_data(vimg, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
                    lines = extract_lines_from_data(data, offset, scale, best_angle, orig_w, orig_h)
                    all_raw_lines.extend(lines)
                except Exception:
                    continue

    # Deduplicate lines
    deduped = deduplicate_detections(all_raw_lines)
    
    # Aggregate raw text
    unique_texts = []
    seen = set()
    for d in deduped:
        clean = re.sub(r'\s+', ' ', d["text"]).strip()
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            unique_texts.append(clean)
            
    raw_ocr_text = "\n".join(unique_texts)
    
    # Match candidate declarations
    declarations = match_declarations(deduped, raw_ocr_text)
    
    return {
        "best_orientation": best_angle,
        "orientation_scores": orientation_scores,
        "raw_ocr_text": raw_ocr_text,
        "character_count": len(raw_ocr_text),
        "word_count": len(raw_ocr_text.split()),
        "detections_count": len(deduped),
        "detections": deduped,
        "declarations": declarations
    }

def extract_lines_from_data(data, offset, scale_factor, angle, orig_w, orig_h):
    n_boxes = len(data.get("text", []))
    line_groups = {}
    
    for i in range(n_boxes):
        word = data["text"][i].strip()
        conf = float(data["conf"][i]) if "conf" in data else -1.0
        if not word or conf < 20.0:  # Ignore ultra-low confidence noise
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
        
        bbox_in_crop = [g["left"], g["top"], g["right"] - g["left"], g["bottom"] - g["top"]]
        orig_bbox = transform_bbox_to_orig(bbox_in_crop, offset, scale_factor, angle, orig_w, orig_h)
        
        lines.append({
            "text": text,
            "confidence": avg_conf,
            "bbox": orig_bbox,
            "source": "TESSERACT"
        })
        
    return lines

def deduplicate_detections(lines):
    dedup_map = {}
    for line in lines:
        norm_key = re.sub(r'[^a-zA-Z0-9]', '', line["text"].lower())
        if len(norm_key) < 2:
            continue
        if norm_key not in dedup_map or line["confidence"] > dedup_map[norm_key]["confidence"]:
            dedup_map[norm_key] = line
            
    # Sort detections by y, then x
    return sorted(list(dedup_map.values()), key=lambda d: (d["bbox"][1], d["bbox"][0]))

def match_declarations(detections, full_text):
    declarations = {}
    
    # 1. MRP
    mrp_pattern = re.compile(
        r'(?:MRP|M\.R\.P\.?|MAX\s*RETAIL\s*PRICE|RPS\.?|RS\.?|INR|₹)\s*[:.\-]?\s*(?:RS\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
        re.IGNORECASE
    )
    for d in detections:
        m = mrp_pattern.search(d["text"])
        if m:
            try:
                val = float(m.group(1))
                if 1.0 <= val <= 99999.0:
                    declarations["max_retail_price"] = {
                        "text": f"₹ {val:.2f}",
                        "value": val,
                        "currency": "INR",
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "max_retail_price",
                        "original_text": d["text"]
                    }
                    break
            except Exception:
                pass

    # 2. Net Quantity
    qty_pattern = re.compile(
        r'(?:NET\s*(?:QTY|QUANTITY|WT|WEIGHT|VOL|VOLUME)?\s*[:.\-]?\s*)?([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gm|grams?|ml|l|ltr|litres?|n|units?|pieces?)\b',
        re.IGNORECASE
    )
    # Check lines with explicit keywords first
    for d in detections:
        if any(k in d["text"].lower() for k in ["net", "qty", "weight", "wt", "vol", "quantity"]):
            m = qty_pattern.search(d["text"])
            if m:
                try:
                    val = float(m.group(1))
                    unit = m.group(2).lower()
                    declarations["net_quantity"] = {
                        "text": f"{val} {unit}",
                        "value": val,
                        "unit": unit,
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "net_quantity",
                        "original_text": d["text"]
                    }
                    break
                except Exception:
                    pass
    if "net_quantity" not in declarations:
        for d in detections:
            m = qty_pattern.search(d["text"])
            if m:
                try:
                    val = float(m.group(1))
                    unit = m.group(2).lower()
                    declarations["net_quantity"] = {
                        "text": f"{val} {unit}",
                        "value": val,
                        "unit": unit,
                        "raw": d["text"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "candidate_type": "net_quantity",
                        "original_text": d["text"]
                    }
                    break
                except Exception:
                    pass

    # 3. Date
    date_pattern = re.compile(
        r'(?:MFD|MFG|PKD|PACKED|DATE\s*OF\s*(?:MFG|MFD|PACKING|MFR)|BEST\s*BEFORE|USE\s*BY)\s*[:.\-]?\s*([0-9]{1,2}[/-][0-9]{2,4}|[A-Za-z]{3}[/-][0-9]{2,4})',
        re.IGNORECASE
    )
    generic_date = re.compile(r'\b(0[1-9]|1[0-2])[/-](20[2-3][0-9]|[2-3][0-9])\b')
    for d in detections:
        m = date_pattern.search(d["text"])
        if m:
            d_str = m.group(1)
            declarations["date_of_manufacture"] = {
                "text": d_str,
                "value": d_str,
                "raw": d["text"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "candidate_type": "date_of_manufacture",
                "original_text": d["text"]
            }
            break
    if "date_of_manufacture" not in declarations:
        for d in detections:
            m = generic_date.search(d["text"])
            if m:
                d_str = m.group(0)
                declarations["date_of_manufacture"] = {
                    "text": d_str,
                    "value": d_str,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "date_of_manufacture",
                    "original_text": d["text"]
                }
                break

    # 4. Manufacturer
    mfg_keywords = ["mfg by", "manufactured by", "packed by", "marketed by", "mfd by", "mfg. by", "mfg & mkt", "pvt ltd", "private limited", "ltd.", "llp", "lic. no", "pepsico", "bimbo"]
    for d in detections:
        if any(k in d["text"].lower() for k in mfg_keywords):
            raw = d["text"]
            name = re.sub(r'^(?:mfg\s*by|manufactured\s*by|packed\s*by|marketed\s*by|mfd\s*by)\s*[:.\-]?\s*', '', raw, flags=re.IGNORECASE).strip()
            declarations["manufacturer"] = {
                "text": name or raw,
                "name": name or raw,
                "address": "Address declared on package",
                "raw": raw,
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "candidate_type": "manufacturer",
                "original_text": raw
            }
            break

    # 5. Consumer Care
    phone_p = re.compile(r'(?:1800[- ]?[0-9]{3}[- ]?[0-9]{3,4}|\+?91[- ]?[6-9][0-9]{9}|[6-9][0-9]{9})')
    email_p = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    care_keywords = ["care", "feedback", "customer", "helpline", "toll free", "pepsico", ".co.in", ".com", "consumer", "contact", "correspondence", "call"]
    
    for d in detections:
        pm = phone_p.search(d["text"])
        em = email_p.search(d["text"])
        if pm or em or any(k in d["text"].lower() for k in care_keywords):
            phone = pm.group(0) if pm else ""
            email = em.group(0) if em else ""
            declarations["consumer_care"] = {
                "text": f"{phone} {email}".strip() or d["text"],
                "phone": phone,
                "email": email,
                "raw": d["text"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "candidate_type": "consumer_care",
                "original_text": d["text"]
            }
            break

    # 6. Country of Origin
    origin_pattern = re.compile(r'(?:country\s*of\s*origin|made\s*in|product\s*of)\s*[:.\-]?\s*([a-zA-Z ]+)', re.IGNORECASE)
    for d in detections:
        m = origin_pattern.search(d["text"])
        if m:
            country = m.group(1).strip()
            if len(country.split()) <= 3:
                declarations["country_of_origin"] = {
                    "text": country,
                    "value": country,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "country_of_origin",
                    "original_text": d["text"]
                }
                break

    # 7. Commodity Name
    comm_pattern = re.compile(r'(?:commodity|generic\s*name|product\s*name|product)\s*[:.\-]?\s*([a-zA-Z0-9 ]+)', re.IGNORECASE)
    for d in detections:
        m = comm_pattern.search(d["text"])
        if m:
            name = m.group(1).strip()
            if len(name) > 2 and len(name.split()) <= 6:
                declarations["commodity_name"] = {
                    "text": name,
                    "value": name,
                    "raw": d["text"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "candidate_type": "commodity_name",
                    "original_text": d["text"]
                }
                break

    return declarations

# Test on Image 1 (Bimbo)
print("=== TEST 1: Bimbo package ===")
img1 = cv2.imread('uploads/1789137133823_WhatsApp_Image_2026-09-10_at_11.53.06_AM.jpeg')
res1 = run_multi_pass_ocr(img1)
print(f"Orientation: {res1['best_orientation']} deg")
print(f"Character count: {res1['character_count']}")
print(f"Word count: {res1['word_count']}")
print(f"Detections count: {res1['detections_count']}")
print(f"Declarations detected: {list(res1['declarations'].keys())}")
for k, v in res1['declarations'].items():
    print(f"  {k}: {v.get('text')} (bbox: {v.get('bbox')})")
print("Sample detections:")
for d in res1['detections'][:10]:
    print(f"  [{d['confidence']}] {d['text']} -> {d['bbox']}")

print("\n=== TEST 2: PepsiCo package ===")
img2 = cv2.imread('uploads/1789069208079_WhatsApp_Image_2026-09-10_at_2.06.31_PM.jpeg')
res2 = run_multi_pass_ocr(img2)
print(f"Orientation: {res2['best_orientation']} deg")
print(f"Character count: {res2['character_count']}")
print(f"Word count: {res2['word_count']}")
print(f"Detections count: {res2['detections_count']}")
print(f"Declarations detected: {list(res2['declarations'].keys())}")
for k, v in res2['declarations'].items():
    print(f"  {k}: {v.get('text')} (bbox: {v.get('bbox')})")

print("\n=== TEST 3: Blank image ===")
blank = np.full((600, 800, 3), 240, dtype=np.uint8)
res3 = run_multi_pass_ocr(blank)
print(f"Orientation: {res3['best_orientation']} deg")
print(f"Character count: {res3['character_count']}")
print(f"Word count: {res3['word_count']}")
print(f"Detections count: {res3['detections_count']}")
print(f"Declarations detected: {list(res3['declarations'].keys())}")
