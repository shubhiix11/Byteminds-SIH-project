import sqlite3
import os
import json
from datetime import datetime, timezone

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
DB_PATH = os.path.join(DATA_DIR, 'labelsure.db')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def get_db_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    ensure_data_dir()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create base table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            extracted_facts TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()

    # 2. Check existing columns and alter table to add missing schema fields
    cursor.execute("PRAGMA table_info(scans)")
    rows = cursor.fetchall()
    existing_cols = set()
    for col in rows:
        if isinstance(col, dict) or hasattr(col, 'keys'):
            existing_cols.add(col['name'])
        else:
            existing_cols.add(col[1])

    new_columns = [
        ("scan_id", "TEXT"),
        ("product_name", "TEXT"),
        ("brand", "TEXT"),
        ("category", "TEXT"),
        ("barcode", "TEXT"),
        ("manufacturer", "TEXT"),
        ("location", "TEXT DEFAULT 'Inspector Terminal'"),
        ("inspector", "TEXT DEFAULT 'Inspector Alpha'"),
        ("overall_status", "TEXT DEFAULT 'NEEDS_REVIEW'"),
        ("measurement_method", "TEXT DEFAULT 'not_available'"),
        ("product_enrichment", "TEXT"),
        ("cross_check", "TEXT"),
        ("rule_results", "TEXT"),
        ("summary_counts", "TEXT"),
        ("measurements", "TEXT"),
        ("annotations", "TEXT"),
        ("original_image_url", "TEXT"),
        ("annotated_image_url", "TEXT"),
        ("report_path", "TEXT"),
        ("web_research", "TEXT"),
        ("openfoodfacts_status", "TEXT"),
        ("openfoodfacts_product", "TEXT"),
        ("openfoodfacts_source_url", "TEXT"),
        ("openfoodfacts_retrieved_at", "TEXT")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE scans ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                pass

    conn.commit()
    conn.close()

def save_scan(filename, file_path, extracted_facts, status="COMPLETED", scan_id=None,
              product_name=None, brand=None, category=None, barcode=None, manufacturer=None,
              location="Inspector Terminal", inspector="Inspector Alpha",
              overall_status="NEEDS_REVIEW", measurement_method="not_available",
              product_enrichment=None, cross_check=None, rule_results=None,
              summary_counts=None, measurements=None, annotations=None,
              original_image_url=None, annotated_image_url=None, report_path=None,
              web_research=None, openfoodfacts_status=None, openfoodfacts_product=None,
              openfoodfacts_source_url=None, openfoodfacts_retrieved_at=None):
    
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not scan_id:
        scan_id = f"SCAN_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    created_at = datetime.now(timezone.utc).isoformat() + 'Z'

    cursor.execute('''
        INSERT OR REPLACE INTO scans (
            scan_id, filename, file_path, product_name, brand, category, barcode, manufacturer,
            location, inspector, overall_status, measurement_method, extracted_facts,
            product_enrichment, cross_check, rule_results, summary_counts, measurements,
            annotations, original_image_url, annotated_image_url, report_path, web_research,
            openfoodfacts_status, openfoodfacts_product, openfoodfacts_source_url, openfoodfacts_retrieved_at,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        scan_id, filename, file_path,
        product_name or "Unknown Commodity",
        brand or "Generic Brand",
        category or "Packaged Commodity",
        barcode or "N/A",
        manufacturer or "Unknown Manufacturer",
        location, inspector, overall_status, measurement_method,
        json.dumps(extracted_facts) if isinstance(extracted_facts, (dict, list)) else extracted_facts,
        json.dumps(product_enrichment) if isinstance(product_enrichment, (dict, list)) else product_enrichment,
        json.dumps(cross_check) if isinstance(cross_check, (dict, list)) else cross_check,
        json.dumps(rule_results) if isinstance(rule_results, (dict, list)) else rule_results,
        json.dumps(summary_counts) if isinstance(summary_counts, (dict, list)) else summary_counts,
        json.dumps(measurements) if isinstance(measurements, (dict, list)) else measurements,
        json.dumps(annotations) if isinstance(annotations, (dict, list)) else annotations,
        original_image_url, annotated_image_url, report_path,
        json.dumps(web_research) if isinstance(web_research, (dict, list)) else web_research,
        openfoodfacts_status,
        json.dumps(openfoodfacts_product) if isinstance(openfoodfacts_product, (dict, list)) else openfoodfacts_product,
        openfoodfacts_source_url,
        openfoodfacts_retrieved_at,
        status, created_at
    ))

    conn.commit()
    conn.close()
    return scan_id

def update_scan_report(scan_id, report_path):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE scans SET report_path = ? WHERE scan_id = ? OR id = ?', (report_path, str(scan_id), str(scan_id)))
    conn.commit()
    conn.close()

def get_all_scans(search=None, status=None, category=None):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM scans WHERE 1=1'
    params = []

    if search:
        query += ' AND (product_name LIKE ? OR brand LIKE ? OR barcode LIKE ? OR manufacturer LIKE ? OR scan_id LIKE ?)'
        pattern = f'%{search}%'
        params.extend([pattern, pattern, pattern, pattern, pattern])

    if status and status != 'ALL':
        query += ' AND overall_status = ?'
        params.append(status)

    if category and category != 'ALL':
        query += ' AND category = ?'
        params.append(category)

    query += ' ORDER BY created_at DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [_parse_scan_row(r) for r in rows]

def get_scan_by_id(scan_id):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scans WHERE scan_id = ? OR id = ?', (str(scan_id), str(scan_id)))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return _parse_scan_row(r)

def get_product_history(product_name_or_barcode):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    pattern = f'%{product_name_or_barcode}%'
    cursor.execute('''
        SELECT * FROM scans 
        WHERE product_name LIKE ? OR barcode LIKE ? OR brand LIKE ?
        ORDER BY created_at DESC
    ''', (pattern, pattern, pattern))
    rows = cursor.fetchall()
    conn.close()
    return [_parse_scan_row(r) for r in rows]

def get_dashboard_analytics():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM scans')
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as count FROM scans WHERE overall_status = 'COMPLIANT'")
    compliant = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM scans WHERE overall_status = 'NON_COMPLIANT'")
    non_compliant = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM scans WHERE overall_status = 'NEEDS_REVIEW'")
    needs_review = cursor.fetchone()['count']

    # Aggregating common violations from saved rule_results
    cursor.execute("SELECT rule_results FROM scans WHERE overall_status = 'NON_COMPLIANT' OR overall_status = 'NEEDS_REVIEW'")
    rows = cursor.fetchall()
    
    violation_counts = {}
    for r in rows:
        r_json = r['rule_results']
        if r_json:
            try:
                r_list = json.loads(r_json) if isinstance(r_json, str) else r_json
                for item in r_list:
                    if item.get("status") == "FAIL":
                        title = item.get("title") or item.get("rule_number") or "Violation"
                        violation_counts[title] = violation_counts.get(title, 0) + 1
            except Exception:
                pass

    common_violations = [
        {"violation": k, "count": v} for k, v in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    cursor.execute('SELECT * FROM scans ORDER BY created_at DESC LIMIT 10')
    recent_rows = cursor.fetchall()
    recent_scans = [_parse_scan_row(r) for r in recent_rows]

    cursor.execute("SELECT * FROM scans WHERE overall_status IN ('NON_COMPLIANT', 'NEEDS_REVIEW') ORDER BY created_at DESC LIMIT 10")
    attention_rows = cursor.fetchall()
    attention_products = [_parse_scan_row(r) for r in attention_rows]

    conn.close()

    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "non_compliant_count": non_compliant,
        "needs_review_count": needs_review,
        "common_violations": common_violations,
        "recent_scans": recent_scans,
        "attention_products": attention_products
    }

def _parse_scan_row(r):
    def safe_json(val):
        if not val: return {}
        if isinstance(val, (dict, list)): return val
        try: return json.loads(val)
        except Exception: return {}

    keys = r.keys()

    return {
        'id': r['id'],
        'scan_id': r['scan_id'] if 'scan_id' in keys and r['scan_id'] else str(r['id']),
        'filename': r['filename'],
        'file_path': r['file_path'],
        'product_name': r['product_name'] if 'product_name' in keys and r['product_name'] else "Unknown Commodity",
        'brand': r['brand'] if 'brand' in keys and r['brand'] else "Generic Brand",
        'category': r['category'] if 'category' in keys and r['category'] else "Packaged Commodity",
        'barcode': r['barcode'] if 'barcode' in keys and r['barcode'] else "N/A",
        'manufacturer': r['manufacturer'] if 'manufacturer' in keys and r['manufacturer'] else "Unknown Manufacturer",
        'location': r['location'] if 'location' in keys and r['location'] else "Inspector Terminal",
        'inspector': r['inspector'] if 'inspector' in keys and r['inspector'] else "Inspector Alpha",
        'overall_status': r['overall_status'] if 'overall_status' in keys and r['overall_status'] else "NEEDS_REVIEW",
        'measurement_method': r['measurement_method'] if 'measurement_method' in keys and r['measurement_method'] else "not_available",
        'extracted_facts': safe_json(r['extracted_facts']),
        'product_enrichment': safe_json(r['product_enrichment'] if 'product_enrichment' in keys else None),
        'cross_check': safe_json(r['cross_check'] if 'cross_check' in keys else None),
        'rule_results': safe_json(r['rule_results'] if 'rule_results' in keys else None),
        'summary_counts': safe_json(r['summary_counts'] if 'summary_counts' in keys else None),
        'measurements': safe_json(r['measurements'] if 'measurements' in keys else None),
        'annotations': safe_json(r['annotations'] if 'annotations' in keys else None),
        'original_image_url': r['original_image_url'] if 'original_image_url' in keys and r['original_image_url'] else f"/uploads/{r['filename']}",
        'annotated_image_url': r['annotated_image_url'] if 'annotated_image_url' in keys else None,
        'report_path': r['report_path'] if 'report_path' in keys else None,
        'web_research': safe_json(r['web_research'] if 'web_research' in keys else None),
        'openfoodfacts_status': r['openfoodfacts_status'] if 'openfoodfacts_status' in keys else None,
        'openfoodfacts_product': safe_json(r['openfoodfacts_product'] if 'openfoodfacts_product' in keys else None),
        'openfoodfacts_source_url': r['openfoodfacts_source_url'] if 'openfoodfacts_source_url' in keys else None,
        'openfoodfacts_retrieved_at': r['openfoodfacts_retrieved_at'] if 'openfoodfacts_retrieved_at' in keys else None,
        'status': r['status'],
        'created_at': r['created_at']
    }
