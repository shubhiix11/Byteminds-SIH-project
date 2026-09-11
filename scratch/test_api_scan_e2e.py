import requests
import json
import time

url = "http://localhost:5001/api/scan"

def test_upload(image_path, label):
    print(f"\n==========================================")
    print(f"TESTING {label}: {image_path}")
    print(f"==========================================")
    t0 = time.time()
    with open(image_path, "rb") as f:
        files = {"image": f}
        data = {"inspector": "Inspector Alpha", "location": "Test Facility"}
        resp = requests.post(url, files=files, data=data)
    elapsed = time.time() - t0
    print(f"Status Code: {resp.status_code} in {elapsed:.2f}s")
    if resp.status_code != 200:
        print("ERROR:", resp.text[:500])
        return None
    res = resp.json()
    scan_id = res.get("scan_id")
    overall_status = res.get("overall_status")
    summary = res.get("summary")
    barcode = res.get("barcode")
    decls = res.get("detected_declarations", {})
    raw_ocr = res.get("raw_ocr_text", "")
    best_orientation = res.get("best_orientation")
    ocr_detections = res.get("ocr_detections", [])
    candidate_decls = res.get("candidate_declarations", {})

    print(f"Scan ID: {scan_id}")
    print(f"Overall Status: {overall_status}")
    print(f"Summary: {summary}")
    print(f"Barcode: {barcode}")
    print(f"Best Orientation: {best_orientation} deg")
    print(f"Raw OCR Text Length: {len(raw_ocr)} characters")
    print(f"OCR Detections Count: {len(ocr_detections)}")
    print(f"Candidate Declarations: {candidate_decls}")
    print(f"Detected Declarations: {list(decls.keys())}")
    for k, v in decls.items():
        val = v.get("text") if isinstance(v, dict) else v
        bbox = v.get("bbox") if isinstance(v, dict) else None
        print(f"  - {k}: {val} (bbox: {bbox})")

    rule_results = res.get("rule_results", [])
    print(f"\nRule Results ({len(rule_results)} rules):")
    for r in rule_results:
        print(f"  [{r['status']}] {r['rule_number']} - {r['title']}: {r.get('reason')}")

    print("\nOCR Debug:")
    print(json.dumps(res.get("debug", {}).get("OCR DEBUG", {}), indent=2))
    return res

# 1. Bimbo package image
r1 = test_upload("uploads/1789137133823_WhatsApp_Image_2026-09-10_at_11.53.06_AM.jpeg", "1. BIMBO PACKAGE IMAGE")

# 2. PepsiCo package image
r2 = test_upload("uploads/1789069208079_WhatsApp_Image_2026-09-10_at_2.06.31_PM.jpeg", "2. PEPSICO PACKAGE IMAGE")

# 3. Blank image
r3 = test_upload("uploads/test_blank.jpg", "3. BLANK IMAGE")
