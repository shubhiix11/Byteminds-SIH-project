import os
import time
import json
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from database import init_db, save_scan, get_all_scans, get_scan_by_id, get_dashboard_analytics, get_product_history, update_scan_report
from vision_service import VisionService
from compliance_engine import ComplianceEngine
from product_enrichment_service import ProductEnrichmentService
from cross_check_engine import CrossCheckEngine
from measurement_service import MeasurementService
from annotation_service import AnnotationService
from report_generator import ReportGenerator
from barcode_decoder import decode_barcode
from local_ocr_service import LocalOCRService
from web_research_service import WebResearchManager
from openfoodfacts_service import OpenFoodFactsService

UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
ANNOTATED_UPLOADS_DIR = os.path.join(UPLOADS_DIR, 'annotated')
DATA_DIR = os.path.join(BASE_DIR, 'data')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

for folder in [UPLOADS_DIR, ANNOTATED_UPLOADS_DIR, DATA_DIR, REPORTS_DIR]:
    os.makedirs(folder, exist_ok=True)

app = Flask(__name__)
CORS(app)

# Initialize SQLite database schema
init_db()

from tesseract_provider import is_tesseract_available, get_tesseract_path_status, TesseractVisionProvider

# Safe provider configuration check without revealing secrets
app_mode = os.environ.get("LABELSURE_MODE", "production")
vision_provider_name = os.environ.get("VISION_PROVIDER", "tesseract")
enrichment_provider_name = os.environ.get("PRODUCT_ENRICHMENT_PROVIDER", "openai")

raw_openai_key = os.getenv("OPENAI_API_KEY", "").strip()
api_key_configured = bool(raw_openai_key and "YOUR_OPENAI_API_KEY" not in raw_openai_key and len(raw_openai_key) > 10)
api_key_status = "YES" if api_key_configured else "NO"
tess_avail_str = "YES" if is_tesseract_available() else "NO"
tess_path_status = get_tesseract_path_status()

web_research_manager = WebResearchManager()
web_res_avail = "YES" if web_research_manager.provider.is_available() else "NO"

# Safely print runtime status (NEVER print API key, partial key, or secrets)
print(
    f"LabelSure Runtime\n"
    f"Mode: {app_mode}\n"
    f"Primary OCR: Tesseract (local)\n"
    f"Local OCR Available: {tess_avail_str}\n"
    f"Local OCR Path: {tess_path_status}\n"
    f"Barcode Decoder: Ready (zxing / opencv)\n"
    f"OpenAI Vision: Optional (Available: {api_key_status})\n"
    f"Product Enrichment Provider: {enrichment_provider_name}\n"
    f"Web Research Provider: {web_research_manager.provider.provider_name} (Configured: {web_res_avail})\n"
    f"API Key Configured: {api_key_status}"
)

local_ocr_service = LocalOCRService()
vision_service = VisionService()
compliance_engine = ComplianceEngine()
enrichment_service = ProductEnrichmentService()
measurement_service = MeasurementService()
annotation_service = AnnotationService()
report_generator = ReportGenerator(REPORTS_DIR)
openfoodfacts_service = OpenFoodFactsService()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    raw_key = os.getenv("OPENAI_API_KEY", "").strip()
    is_conf = bool(raw_key and "YOUR_OPENAI_API_KEY" not in raw_key and len(raw_key) > 10)
    return jsonify({
        "status": "ok",
        "service": "LabelSure AI Legal Metrology Platform",
        "mode": os.environ.get("LABELSURE_MODE", "production"),
        "primary_ocr": "Tesseract (local)",
        "ocr_provider": "tesseract",
        "vision_provider": os.environ.get("VISION_PROVIDER", "tesseract"),
        "api_key_configured": "YES" if is_conf else "NO",
        "tesseract_available": is_tesseract_available(),
        "tesseract_path_status": get_tesseract_path_status(),
        "barcode_decoder": "Ready (zxing / opencv)",
        "enrichment_provider": os.environ.get("PRODUCT_ENRICHMENT_PROVIDER", "openai"),
        "web_research_provider": web_research_manager.provider.provider_name,
        "web_research_configured": "YES" if web_research_manager.provider.is_available() else "NO",
        "openfoodfacts_provider": "Open Food Facts API v2",
        "version": "7.1.0-OFF-INTEGRATION"
    }), 200

@app.route('/api/diagnostic', methods=['GET'])
def provider_diagnostic():
    raw_key = os.getenv("OPENAI_API_KEY", "").strip()
    is_conf = bool(raw_key and "YOUR_OPENAI_API_KEY" not in raw_key and len(raw_key) > 10)
    if is_conf:
        return jsonify({
            "configured": True,
            "provider": "openai"
        }), 200
    else:
        return jsonify({
            "configured": False,
            "provider": "openai",
            "reason": "API key unavailable"
        }), 200

@app.route('/api/dashboard', methods=['GET'])
def dashboard_metrics():
    analytics = get_dashboard_analytics()
    return jsonify({
        "success": True,
        "dashboard": analytics
    }), 200

@app.route('/api/product-enrichment', methods=['POST'])
def standalone_enrichment():
    payload = request.get_json(silent=True) or request.form
    barcode = payload.get('barcode')
    declarations = payload.get('detected_declarations') or {}

    enrichment = enrichment_service.enrich_product(barcode=barcode, detected_declarations=declarations)
    cross_check = CrossCheckEngine.cross_check(detected_declarations=declarations, enrichment_data=enrichment)

    return jsonify({
        "success": True,
        "enrichment": enrichment,
        "cross_check": cross_check
    }), 200

@app.route('/api/web-research', methods=['POST'])
def standalone_web_research():
    payload = request.get_json(silent=True) or request.form or {}
    barcode = payload.get('barcode')
    declarations = payload.get('detected_declarations') or {}
    all_text = payload.get('all_detected_text') or ""
    scan_id = payload.get('scan_id')

    result = web_research_manager.run_research(
        barcode=barcode,
        detected_declarations=declarations,
        all_detected_text=all_text,
        scan_id=scan_id
    )
    return jsonify({
        "success": True,
        "web_research": result
    }), 200

@app.route('/api/scan', methods=['POST'])
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided under field 'image'"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    inspection_date = request.form.get('inspection_date')
    form_barcode = request.form.get('barcode')
    location = request.form.get('location', 'Inspector Terminal')
    inspector = request.form.get('inspector', 'Inspector Alpha')
    measurement_input = request.form.get('measurement_input')

    if measurement_input:
        try:
            measurement_input = json.loads(measurement_input)
        except Exception:
            measurement_input = None

    original_filename = secure_filename(file.filename)
    timestamp = int(time.time() * 1000)
    scan_id = f"SCAN_{timestamp}"
    saved_filename = f"{timestamp}_{original_filename}"
    file_path = os.path.join(UPLOADS_DIR, saved_filename)
    file.save(file_path)

    # Calculate real image dimensions & size safely
    file_size_bytes = os.path.getsize(file_path)
    try:
        with Image.open(file_path) as img:
            img_w, img_h = img.size
    except Exception:
        img_w, img_h = 0, 0

    app.logger.info(f"[Scan Upload Received] Filename: {saved_filename}, MIME: {file.content_type}, Size: {file_size_bytes} bytes, Dimensions: {img_w}x{img_h}px, Path: {file_path}")

    try:
        # Step 1: Local OCR Service (Tesseract) - Core Primary Extraction
        ocr_t0 = time.time()
        try:
            raw_facts = local_ocr_service.extract_text(file_path)
            local_ocr_status = "SUCCESS" if raw_facts.get("status") in ["SUCCESS", "EMPTY"] else "FAILED"
        except Exception as ocr_err:
            app.logger.error(f"Local OCR extraction error: {ocr_err}")
            raw_facts = {
                "provider": "TESSERACT",
                "available": is_tesseract_available(),
                "status": "FAILED",
                "reason": str(ocr_err),
                "all_detected_text": "",
                "detections": [],
                "declarations": {},
                "confidence_score": 0.0,
                "font_pixel_height": 24.0,
                "product_metadata": {"is_imported": False, "is_photo_inspection": True, "single_surface_only": True}
            }
            local_ocr_status = "FAILED"
        ocr_time_ms = int((time.time() - ocr_t0) * 1000)

        # Step 2: Local Barcode Decoder directly from image pixels
        barcode_decoding_result = decode_barcode(file_path)
        actual_barcode = barcode_decoding_result.get("barcode") or form_barcode or None

        declarations = dict(raw_facts.get("declarations", {}))

        # Step 3: Optional OpenAI Vision (Run only if configured; failure does NOT break scan)
        openai_attempted = False
        openai_available = api_key_configured
        openai_status = "DISABLED" if not api_key_configured else "PENDING"
        openai_error = None
        openai_facts = None

        if api_key_configured:
            openai_attempted = True
            try:
                from vision_service import OpenAIVisionProvider
                o_prov = OpenAIVisionProvider()
                openai_facts = o_prov.extract_facts(file_path)
                if openai_facts.get("status") == "SUCCESS":
                    openai_status = "SUCCESS"
                    # Corroborate declarations
                    for k, v in openai_facts.get("declarations", {}).items():
                        if k not in declarations or not declarations[k]:
                            declarations[k] = v
                else:
                    openai_status = "UNAVAILABLE"
                    openai_error = openai_facts.get("reason", "OpenAI Vision unavailable or quota exhausted")
            except Exception as o_err:
                openai_status = "FAILED"
                openai_error = str(o_err)
                app.logger.warning(f"Optional OpenAI Vision encountered an error: {o_err}")

        # Ensure single_surface_only flag is set on product_metadata for single uploaded photo
        if "product_metadata" not in raw_facts:
            raw_facts["product_metadata"] = {}
        raw_facts["product_metadata"]["single_surface_only"] = True
        raw_facts["declarations"] = declarations

        # Extract product metadata from real OCR declarations
        product_name = str(declarations.get("commodity_name", {}).get("value") if isinstance(declarations.get("commodity_name"), dict) else declarations.get("commodity_name", "Packaged Commodity")).strip() if declarations.get("commodity_name") else "Packaged Commodity"
        mfg_dict = declarations.get("manufacturer") or {}
        mfg_name = mfg_dict.get("name") if isinstance(mfg_dict, dict) else str(mfg_dict) if mfg_dict else None
        brand = mfg_name or "Generic Brand"

        # Step 4: Physical Character Height Measurement
        measurements = measurement_service.measure_declarations(declarations, measurement_input)

        # Step 5: Deterministic Legal Metrology Rule Engine (SOLE & FINAL LEGAL DECISION MAKER)
        compliance_result = compliance_engine.process_scan(
            vision_output=raw_facts,
            inspection_date=inspection_date,
            measurement_input=measurement_input
        )

        # Step 6: Server-Side Image Evidence Annotation
        rule_results = compliance_result["rule_results"]
        annotated_path, annotations_metadata = annotation_service.create_annotated_image(
            original_image_path=file_path,
            rule_results=rule_results,
            output_dir=UPLOADS_DIR
        )

        # Step 7: Product & Barcode Enrichment (OPTIONAL INFORMATIONAL LAYER)
        enrichment_attempted = bool(actual_barcode or declarations)
        enrichment_result = {}
        enrichment_status = "SKIPPED"
        try:
            enrichment_result = enrichment_service.enrich_product(barcode=actual_barcode, detected_declarations=declarations)
            enrichment_status = "SUCCESS" if enrichment_result.get("product_name") else "NOT_FOUND"
        except Exception as enrich_err:
            enrichment_status = "FAILED"
            app.logger.warning(f"Optional Product Enrichment encountered error: {enrich_err}")

        cross_check_result = CrossCheckEngine.cross_check(detected_declarations=declarations, enrichment_data=enrichment_result)

        # Step 8: Web Product Research Layer (INFORMATIONAL & EVIDENCE LAYER)
        web_research_result = web_research_manager.run_research(
            barcode=actual_barcode,
            detected_declarations=declarations,
            all_detected_text=raw_facts.get("all_detected_text", ""),
            scan_id=scan_id
        )

        # Step 9: Open Food Facts Product Lookup (Strictly from real barcode decoder)
        decoded_barcode = barcode_decoding_result.get("barcode") if barcode_decoding_result.get("detected") else None
        off_result = {
            "available": False,
            "status": "NO_BARCODE",
            "barcode": None,
            "source": "OPEN_FOOD_FACTS",
            "message": "Barcode not detected"
        }
        off_cross_check = {"available": False, "reason": "No barcode detected for Open Food Facts lookup."}

        if decoded_barcode:
            try:
                off_result = openfoodfacts_service.get_product_by_barcode(decoded_barcode)
                off_cross_check = openfoodfacts_service.cross_check_with_ocr(declarations, off_result)
            except Exception as off_err:
                app.logger.warning(f"Open Food Facts lookup failed gracefully: {off_err}")
                off_result = {
                    "available": False,
                    "status": "UNAVAILABLE",
                    "barcode": decoded_barcode,
                    "source": "OPEN_FOOD_FACTS",
                    "message": "Open Food Facts service is currently unavailable."
                }
                off_cross_check = {"available": False, "reason": "Open Food Facts service unavailable."}
        off_result["cross_check"] = off_cross_check

        # Dual OCR cross check details
        ocr_cross_check = {"available": False, "reason": "Local Tesseract OCR executed independently"}
        if openai_facts and openai_status == "SUCCESS":
            ocr_cross_check = CrossCheckEngine.cross_check_ocr_providers(openai_facts, raw_facts)
        elif openai_status in ["UNAVAILABLE", "FAILED"]:
            ocr_cross_check = {
                "available": False,
                "reason": f"OpenAI Vision was {openai_status.lower()} ({openai_error or 'quota/network'}). Primary local Tesseract OCR executed independently."
            }

        annotated_filename = os.path.basename(annotated_path)
        orig_url = f"/uploads/{saved_filename}"
        annotated_url = f"/uploads/annotated/{annotated_filename}"

        # Format candidate declarations for developer forensic debugging (Section 12)
        candidate_decls = {
            "manufacturer": declarations.get("manufacturer", {}).get("text") if isinstance(declarations.get("manufacturer"), dict) else declarations.get("manufacturer"),
            "mrp": declarations.get("max_retail_price", {}).get("text") if isinstance(declarations.get("max_retail_price"), dict) else declarations.get("max_retail_price"),
            "net_quantity": declarations.get("net_quantity", {}).get("text") if isinstance(declarations.get("net_quantity"), dict) else declarations.get("net_quantity"),
            "date": declarations.get("date_of_manufacture", {}).get("text") if isinstance(declarations.get("date_of_manufacture"), dict) else declarations.get("date_of_manufacture"),
            "consumer_care": declarations.get("consumer_care", {}).get("text") if isinstance(declarations.get("consumer_care"), dict) else declarations.get("consumer_care"),
            "country": declarations.get("country_of_origin", {}).get("text") if isinstance(declarations.get("country_of_origin"), dict) else declarations.get("country_of_origin")
        }

        # Combine debug metadata for developer forensic inspection
        debug_info = {
            "OCR DEBUG": {
                "image": {
                    "received": True,
                    "filename": saved_filename,
                    "path": file_path,
                    "width": img_w,
                    "height": img_h
                },
                "tesseract": {
                    "available": is_tesseract_available(),
                    "executed": True,
                    "status": local_ocr_status
                },
                "raw_ocr": {
                    "character_count": len(raw_facts.get("raw_ocr_text", "")),
                    "word_count": raw_facts.get("word_count", 0),
                    "text": raw_facts.get("raw_ocr_text", ""),
                    "detections": len(raw_facts.get("detections", []))
                },
                "orientation": {
                    "best_orientation": raw_facts.get("best_orientation", 0),
                    "evaluated_orientations": raw_facts.get("evaluated_orientations", [0, 90, 180, 270])
                },
                "candidate_declarations": candidate_decls
            },
            "IMAGE": {
                "filename": saved_filename,
                "dimensions": f"{img_w}x{img_h}",
                "format": os.path.splitext(saved_filename)[1].replace('.', '').upper(),
                "size_bytes": file_size_bytes
            },
            "LOCAL OCR": {
                "provider": "Tesseract",
                "status": local_ocr_status,
                "executed": True,
                "execution_time_ms": ocr_time_ms,
                "characters_extracted": len(raw_facts.get("raw_ocr_text", "")),
                "detections_count": len(raw_facts.get("detections", [])),
                "declarations_detected": len(declarations),
                "best_orientation": raw_facts.get("best_orientation", 0),
                "raw_ocr_text": raw_facts.get("raw_ocr_text", "")
            },
            "CANDIDATE DECLARATIONS": candidate_decls,
            "OPENAI VISION": {
                "attempted": openai_attempted,
                "available": openai_available,
                "status": openai_status,
                "error": openai_error
            },
            "BARCODE": {
                "attempted": True,
                "detected": barcode_decoding_result.get("detected", False),
                "format": barcode_decoding_result.get("format"),
                "value": actual_barcode,
                "checksum_valid": barcode_decoding_result.get("checksum_valid", False)
            },
            "ENRICHMENT": {
                "attempted": enrichment_attempted,
                "status": enrichment_status,
                "product_identified": bool(enrichment_result and enrichment_result.get("product_name"))
            },
            "WEB RESEARCH": {
                "status": web_research_result.get("status"),
                "provider": web_research_result.get("provider", "google"),
                "queries_executed": web_research_result.get("queries_run", 0),
                "results_found": web_research_result.get("results_found", 0),
                "pages_reviewed": web_research_result.get("pages_fetched", 0),
                "sources_used": web_research_result.get("sources_used", 0)
            },
            "OPEN FOOD FACTS": {
                "status": off_result.get("status"),
                "barcode": decoded_barcode,
                "product_found": bool(off_result.get("status") == "FOUND"),
                "source_url": off_result.get("source_url")
            },
            "RULE ENGINE": {
                "rules_evaluated": len(rule_results),
                "passed": compliance_result["summary"]["passed"],
                "failed": compliance_result["summary"]["failed"],
                "not_verifiable": compliance_result["summary"]["not_verifiable"],
                "not_applicable": compliance_result["summary"]["not_applicable"]
            },
            "MOCK": {
                "mock_used": False,
                "synthetic_data_injected": False
            },
            # Backwards-compatibility fields for legacy dashboard/components
            "backend_url": "http://localhost:5001",
            "scan_endpoint": "/api/scan",
            "image_received": True,
            "image_filename": saved_filename,
            "image_size_bytes": file_size_bytes,
            "image_dimensions": f"{img_w}x{img_h}",
            "labelsure_mode": app_mode,
            "vision_provider": "tesseract",
            "ocr_provider": "Tesseract",
            "tesseract_available": "YES" if is_tesseract_available() else "NO",
            "tesseract_path_status": get_tesseract_path_status(),
            "fallback_used": False,
            "vision_called": True,
            "vision_success": local_ocr_status == "SUCCESS",
            "mock_used": False,
            "mock_vision_used": False,
            "raw_ocr_text": raw_facts.get("raw_ocr_text", ""),
            "all_detected_text_length": len(raw_facts.get("all_detected_text", "")),
            "barcode_decoder": {
                "attempted": True,
                "detected": barcode_decoding_result.get("detected", False),
                "barcode": actual_barcode,
                "format": barcode_decoding_result.get("format"),
                "checksum_valid": barcode_decoding_result.get("checksum_valid", False)
            },
            "enrichment_provider": enrichment_provider_name,
            "mock_enrichment_used": False
        }

        # Combine scan result payload
        scan_payload = {
            "scan_id": scan_id,
            "filename": saved_filename,
            "original_image_url": orig_url,
            "annotated_image_url": annotated_url,
            "overall_status": compliance_result["overall_status"],
            "summary": compliance_result["summary"],
            "rule_results": compliance_result["rule_results"],
            "detected_declarations": compliance_result["detected_declarations"],
            "candidate_declarations": candidate_decls,
            "barcode_decoding": barcode_decoding_result,
            "barcode": actual_barcode or "NOT_DETECTED",
            "product_enrichment": enrichment_result,
            "cross_check": cross_check_result,
            "web_research": web_research_result,
            "openfoodfacts": off_result,
            "openfoodfacts_cross_check": off_cross_check,
            "ocr_cross_check": ocr_cross_check,
            "all_detected_text": raw_facts.get("all_detected_text", ""),
            "raw_ocr_text": raw_facts.get("raw_ocr_text", ""),
            "ocr_detections": raw_facts.get("detections", []),
            "best_orientation": raw_facts.get("best_orientation", 0),
            "measurements": measurements,
            "annotations": annotations_metadata,
            "rule_set_version": compliance_result["rule_set_version"],
            "inspection_date": compliance_result["inspection_date"],
            "disclaimer": compliance_result["disclaimer"],
            "product_name": product_name,
            "brand": brand,
            "inspector": inspector,
            "location": location,
            "debug": debug_info
        }

        # Step 7: Generate PDF Report from computed result
        pdf_path = report_generator.generate_pdf_report(
            scan_result=scan_payload,
            annotated_image_path=annotated_path
        )
        report_url = f"/api/reports/{scan_id}"

        # Step 8: Persist Scan Record into SQLite Database
        db_scan_id = save_scan(
            scan_id=scan_id,
            filename=saved_filename,
            file_path=file_path,
            product_name=product_name,
            brand=brand,
            category="Packaged Food",
            barcode=actual_barcode or "NOT_DETECTED",
            manufacturer=mfg_name or "Unknown Manufacturer",
            location=location,
            inspector=inspector,
            overall_status=compliance_result["overall_status"],
            measurement_method=(measurement_input.get("method") if measurement_input else "not_available"),
            extracted_facts=raw_facts,
            product_enrichment=enrichment_result,
            cross_check=cross_check_result,
            rule_results=compliance_result["rule_results"],
            summary_counts=compliance_result["summary"],
            measurements=measurements,
            annotations=annotations_metadata,
            original_image_url=orig_url,
            annotated_image_url=annotated_url,
            report_path=pdf_path,
            web_research=web_research_result,
            openfoodfacts_status=off_result.get("status"),
            openfoodfacts_product=off_result.get("product"),
            openfoodfacts_source_url=off_result.get("source_url"),
            openfoodfacts_retrieved_at=off_result.get("retrieved_at"),
            status="COMPLETED"
        )

        scan_payload["report_url"] = report_url

        return jsonify({
            "success": True,
            "scan_id": db_scan_id,
            "report_url": report_url,
            **scan_payload
        }), 200

    except Exception as e:
        app.logger.error(f"Error processing scan: {str(e)}")
        return jsonify({
            "error": "Failed to process image scan",
            "details": str(e)
        }), 500

@app.route('/api/openfoodfacts/<barcode>', methods=['GET'])
def get_openfoodfacts_endpoint(barcode):
    """
    Open Food Facts Product-by-Barcode Lookup API.
    Handles: FOUND, NOT_FOUND, UNAVAILABLE, INVALID_BARCODE.
    """
    try:
        bypass_cache = request.args.get('bypass_cache', '').lower() in ['true', '1', 'yes']
        res = openfoodfacts_service.get_product_by_barcode(barcode, bypass_cache=bypass_cache)
        status_code = 200
        if res.get("status") == "INVALID_BARCODE":
            status_code = 400
        elif res.get("status") == "NOT_FOUND":
            status_code = 404
        elif res.get("status") == "UNAVAILABLE":
            status_code = 503
        return jsonify({
            "success": bool(res.get("available", False)),
            "source": "OPEN_FOOD_FACTS",
            "barcode": barcode,
            "status": res.get("status"),
            "product": res.get("product"),
            "source_url": res.get("source_url"),
            "retrieved_at": res.get("retrieved_at"),
            "disclaimer": res.get("disclaimer"),
            "data": res
        }), status_code
    except Exception as e:
        app.logger.error(f"Error in /api/openfoodfacts/{barcode}: {e}")
        return jsonify({
            "success": False,
            "source": "OPEN_FOOD_FACTS",
            "barcode": barcode,
            "status": "UNAVAILABLE",
            "error": str(e)
        }), 500

@app.route('/api/scans', methods=['GET'])
def list_scans():
    search = request.args.get('search')
    status = request.args.get('status')
    category = request.args.get('category')
    scans = get_all_scans(search=search, status=status, category=category)
    return jsonify({
        "success": True,
        "count": len(scans),
        "scans": scans
    }), 200

@app.route('/api/scans/<scan_id>', methods=['GET'])
def get_scan(scan_id):
    scan = get_scan_by_id(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({
        "success": True,
        "scan": scan
    }), 200

@app.route('/api/products/history', methods=['GET'])
def product_history():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    history = get_product_history(query)
    return jsonify({
        "success": True,
        "query": query,
        "count": len(history),
        "history": history
    }), 200

@app.route('/api/reports/<scan_id>', methods=['GET'])
def download_report(scan_id):
    scan = get_scan_by_id(scan_id)
    pdf_filename = f"report_{scan_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    if not os.path.exists(pdf_path) and scan and scan.get("report_path"):
        pdf_path = scan["report_path"]

    if not os.path.exists(pdf_path):
        if scan:
            pdf_path = report_generator.generate_pdf_report(scan)
        else:
            return jsonify({"error": f"Report for scan #{scan_id} not found"}), 404

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"LabelSure_Report_{scan_id}.pdf"
    )

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, filename)

@app.route('/uploads/annotated/<path:filename>', methods=['GET'])
def serve_annotated_upload(filename):
    return send_from_directory(ANNOTATED_UPLOADS_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting LabelSure Flask server on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
