import cv2
import pytesseract
import numpy as np

img = cv2.imread('uploads/exact_pkg_90cw.jpg')
h, w = img.shape[:2]
# Top strip where consumer care text is located
top_strip = img[0:int(h*0.35), 0:int(w*0.8)]

# Let's test a specialized packaging text enhancement:
# 1. Red channel inversion (since packaging is cyan, white text on cyan has highest contrast in Red channel)
b, g, r = cv2.split(top_strip)
r_inv = 255 - r

# 2. Resize 3x with cubic interpolation
scaled = cv2.resize(r_inv, None, fx=3.5, fy=3.5, interpolation=cv2.INTER_CUBIC)

# 3. Denoise slightly (Gaussian blur with small kernel)
blurred = cv2.GaussianBlur(scaled, (3, 3), 0)

# 4. CLAHE contrast boost
clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8)).apply(blurred)

# 5. Thresholding variants:
# A: Otsu
_, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# B: Adaptive Gaussian
adapt_g = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15)
# C: Adaptive Mean
adapt_m = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 15)

variants = [
    ('clahe_3.5x', clahe),
    ('otsu_3.5x', otsu),
    ('adapt_g_3.5x', adapt_g),
    ('adapt_m_3.5x', adapt_m)
]

for vname, vimg in variants:
    cv2.imwrite(f'uploads/test_{vname}.jpg', vimg)
    for psm in [6, 11, 4]:
        txt = pytesseract.image_to_string(vimg, config=f'--psm {psm}').strip()
        print(f"=== {vname} (PSM {psm}) ===")
        print(txt)
        print('-'*40)
