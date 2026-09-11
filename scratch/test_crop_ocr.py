import cv2
import pytesseract
import numpy as np

img = cv2.imread('uploads/exact_pkg_90cw.jpg')
h, w = img.shape[:2]

# Let's crop:
# Crop 1: Top strip where consumer care text is located: y from 0 to h*0.35, x from 0 to w
top_strip = img[0:int(h*0.35), 0:w]

# Crop 2: Middle strip where barcode and text below barcode are: y from h*0.25 to h*0.65, x from 0 to w
mid_strip = img[int(h*0.25):int(h*0.65), 0:w]

# Crop 3: Bottom strip where nutrition info is: y from h*0.65 to h, x from 0 to w
bot_strip = img[int(h*0.65):h, 0:w]

crops = [('top_strip', top_strip), ('mid_strip', mid_strip), ('bot_strip', bot_strip)]

for cname, crop in crops:
    # Try 3x scale
    crop3x = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop3x, cv2.COLOR_BGR2GRAY)
    
    # Also isolate color channels:
    # In blue packaging, Red channel gives max contrast against white
    b, g, r = cv2.split(crop3x)
    r_inv = 255 - r
    
    # Try multiple variants for each crop
    clahe_gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
    clahe_rinv = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(r_inv)
    
    _, otsu_gray = cv2.threshold(clahe_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, otsu_rinv = cv2.threshold(clahe_rinv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    cv2.imwrite(f'uploads/debug_{cname}_clahe_rinv.jpg', clahe_rinv)
    
    for vname, vimg in [('clahe_gray', clahe_gray), ('clahe_rinv', clahe_rinv), ('otsu_rinv', otsu_rinv)]:
        for psm in [6, 11]:
            txt = pytesseract.image_to_string(vimg, config=f'--psm {psm}').strip()
            clean_lines = [l.strip() for l in txt.split('\n') if len(l.strip()) > 3]
            if clean_lines:
                print(f"[{cname}] {vname} (PSM {psm}): {len(txt)} chars")
                print("   " + "\n   ".join(clean_lines[:5]))
                print()
