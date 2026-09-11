import cv2
import pytesseract
import numpy as np

img = cv2.imread('uploads/1789137133823_WhatsApp_Image_2026-09-10_at_11.53.06_AM.jpeg')
rot90 = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

gray = cv2.cvtColor(rot90, cv2.COLOR_BGR2GRAY)
up2 = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8)).apply(up2)
inv_clahe = 255 - clahe

kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
sharp = cv2.filter2D(inv_clahe, -1, kernel)
_, otsu = cv2.threshold(inv_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adapt = cv2.adaptiveThreshold(inv_clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 10)

variants = [
    ('up2_gray', up2),
    ('clahe', clahe),
    ('inv_clahe', inv_clahe),
    ('sharp', sharp),
    ('otsu', otsu),
    ('adapt', adapt)
]

for name, p_img in variants:
    for psm in [11, 6]:
        data = pytesseract.image_to_data(p_img, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
        words = [data['text'][i].strip() for i in range(len(data['text'])) if data['text'][i].strip() and int(data['conf'][i]) > 25]
        text_str = ' '.join(words)
        if len(text_str) > 10:
            confs = [int(data['conf'][i]) for i in range(len(data['text'])) if data['text'][i].strip() and int(data['conf'][i]) > 25]
            avg_c = np.mean(confs) if confs else 0
            print(f"{name} (PSM {psm}): {len(words)} words, conf_avg={avg_c:.1f}")
            print(f"   Words: {text_str[:200]}")
            print()
