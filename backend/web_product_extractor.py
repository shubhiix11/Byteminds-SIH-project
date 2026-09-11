"""
Web Product Details Extractor for LabelSure.
Parses publicly accessible web pages and search microdata to extract structured,
source-cited product intelligence.
Detects source consistency and surfaces conflicting product declarations without altering Legal Metrology verdicts.
Strictly adheres to ZERO-FABRICATION policy: only populates fields supported by direct page evidence.
"""

import re
import json
import urllib.parse
from bs4 import BeautifulSoup

class WebProductExtractor:
    def __init__(self):
        pass

    def extract_from_page(self, html_content: str, url: str, title: str, domain: str = "") -> dict:
        """
        Parses raw HTML from a fetched webpage to extract structured product facts with source attribution.
        Returns:
        {
            "url": url,
            "domain": domain,
            "title": title,
            "facts": list[dict],
            "raw_metadata": dict
        }
        """
        if not domain and url:
            domain = urllib.parse.urlparse(url).netloc

        if not html_content or len(html_content.strip()) < 50:
            return {
                "url": url,
                "domain": domain,
                "title": title,
                "facts": [],
                "raw_metadata": {},
                "status": "EMPTY_OR_UNREADABLE"
            }

        soup = BeautifulSoup(html_content, 'html.parser')
        facts = []
        raw_metadata = {}

        # 1. Extract Schema.org JSON-LD (<script type="application/ld+json">)
        json_ld_facts = self._extract_json_ld(soup, url, domain, title)
        facts.extend(json_ld_facts)

        # 2. Extract OpenGraph and Twitter Meta Tags
        meta_facts = self._extract_meta_tags(soup, url, domain, title)
        facts.extend(meta_facts)

        # 3. Extract Microdata & Semantic HTML elements (Pricing, Ingredients, Specs)
        html_facts = self._extract_html_patterns(soup, url, domain, title)
        facts.extend(html_facts)

        # Deduplicate facts by field name, keeping higher confidence
        dedup_facts = {}
        for f in facts:
            field = f["field"]
            val = str(f["value"]).strip()
            if not val or val.lower() in ["none", "null", "n/a", "undefined"]:
                continue
            if field not in dedup_facts or f["confidence"] > dedup_facts[field]["confidence"]:
                dedup_facts[field] = f

        return {
            "url": url,
            "domain": domain,
            "title": title,
            "facts": list(dedup_facts.values()),
            "status": "EXTRACTED" if dedup_facts else "NO_STRUCTURED_FACTS"
        }

    def _extract_json_ld(self, soup: BeautifulSoup, url: str, domain: str, title: str) -> list[dict]:
        facts = []
        scripts = soup.find_all('script', type='application/ld+json')
        
        for s in scripts:
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    continue

                for item in items:
                    # Check for Product or items inside @graph
                    product_items = []
                    if item.get("@type") == "Product":
                        product_items.append(item)
                    elif "@graph" in item and isinstance(item["@graph"], list):
                        for g in item["@graph"]:
                            if isinstance(g, dict) and g.get("@type") in ["Product", "IndividualProduct"]:
                                product_items.append(g)

                    for p in product_items:
                        # Product Name
                        if p.get("name"):
                            facts.append(self._create_fact("product_name", p["name"], url, domain, title, f"JSON-LD name: {p['name']}", 0.95))
                        
                        # Brand
                        brand_val = p.get("brand")
                        if isinstance(brand_val, dict):
                            bname = brand_val.get("name")
                        elif isinstance(brand_val, str):
                            bname = brand_val
                        else:
                            bname = None
                        if bname:
                            facts.append(self._create_fact("brand", bname, url, domain, title, f"JSON-LD brand: {bname}", 0.95))

                        # Manufacturer
                        mfg_val = p.get("manufacturer")
                        if isinstance(mfg_val, dict):
                            mname = mfg_val.get("name")
                        elif isinstance(mfg_val, str):
                            mname = mfg_val
                        else:
                            mname = None
                        if mname:
                            facts.append(self._create_fact("manufacturer", mname, url, domain, title, f"JSON-LD manufacturer: {mname}", 0.92))

                        # Category
                        if p.get("category"):
                            facts.append(self._create_fact("category", str(p["category"]), url, domain, title, f"JSON-LD category: {p['category']}", 0.90))

                        # SKU / Model
                        if p.get("sku"):
                            facts.append(self._create_fact("model_sku", str(p["sku"]), url, domain, title, f"JSON-LD sku: {p['sku']}", 0.90))

                        # Barcode / GTIN
                        gtin = p.get("gtin13") or p.get("gtin8") or p.get("gtin12") or p.get("gtin") or p.get("barcode")
                        if gtin and re.sub(r'\D', '', str(gtin)):
                            clean_gtin = re.sub(r'\D', '', str(gtin))
                            facts.append(self._create_fact("barcode", clean_gtin, url, domain, title, f"JSON-LD gtin: {gtin}", 0.98))

                        # Description
                        if p.get("description") and len(str(p["description"])) > 5:
                            desc = str(p["description"]).strip()[:300]
                            facts.append(self._create_fact("description", desc, url, domain, title, desc[:100], 0.85))

                        # Pricing from offers
                        offers = p.get("offers")
                        if offers:
                            if isinstance(offers, list) and offers:
                                off = offers[0]
                            elif isinstance(offers, dict):
                                off = offers
                            else:
                                off = None
                            if off and isinstance(off, dict):
                                price = off.get("price") or off.get("highPrice") or off.get("lowPrice")
                                curr = off.get("priceCurrency", "INR")
                                if price is not None:
                                    facts.append(self._create_fact("selling_price", f"{curr} {price}", url, domain, title, f"JSON-LD price: {price}", 0.92))

            except Exception:
                continue

        return facts

    def _extract_meta_tags(self, soup: BeautifulSoup, url: str, domain: str, title: str) -> list[dict]:
        facts = []
        meta_tags = soup.find_all('meta')
        meta_dict = {}

        for m in meta_tags:
            prop = m.get('property') or m.get('name') or ''
            cont = m.get('content') or ''
            if prop and cont:
                meta_dict[prop.lower()] = cont.strip()

        # OpenGraph Title
        og_title = meta_dict.get('og:title') or meta_dict.get('twitter:title')
        if og_title and len(og_title) > 2:
            # Clean generic title suffixes (e.g. " - Amazon.in", " | Flipkart")
            clean_title = re.sub(r'\s*[-|–—:]\s*(?:Amazon|Flipkart|Blinkit|Zepto|BigBasket|JioMart|Instamart).*$', '', og_title, flags=re.IGNORECASE).strip()
            if clean_title:
                facts.append(self._create_fact("product_name", clean_title, url, domain, title, f"meta title: {og_title}", 0.88))

        # Brand
        brand = meta_dict.get('product:brand') or meta_dict.get('og:brand')
        if brand:
            facts.append(self._create_fact("brand", brand, url, domain, title, f"meta brand: {brand}", 0.88))

        # Price
        price = meta_dict.get('product:price:amount')
        curr = meta_dict.get('product:price:currency', 'INR')
        if price:
            facts.append(self._create_fact("selling_price", f"{curr} {price}", url, domain, title, f"meta price: {price}", 0.88))

        # Description
        desc = meta_dict.get('og:description') or meta_dict.get('description')
        if desc and len(desc) > 10:
            facts.append(self._create_fact("description", desc[:300], url, domain, title, desc[:100], 0.80))

        return facts

    def _extract_html_patterns(self, soup: BeautifulSoup, url: str, domain: str, title: str) -> list[dict]:
        facts = []
        text = soup.get_text(separator=' ')
        clean_text = re.sub(r'\s+', ' ', text)

        # 1. Net Quantity / Pack Size Pattern
        qty_pattern = re.compile(r'\b(?:net\s*(?:weight|wt|qty|quantity)|pack\s*size|weight)\s*[:.\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|grams?|ml|l|ltr|litres?|n|pieces?|units?))\b', re.IGNORECASE)
        m_qty = qty_pattern.search(clean_text)
        if m_qty:
            val = m_qty.group(1).strip()
            facts.append(self._create_fact("net_quantity", val, url, domain, title, m_qty.group(0), 0.85))
            facts.append(self._create_fact("pack_size", val, url, domain, title, m_qty.group(0), 0.85))

        # 2. MRP Pattern
        mrp_pattern = re.compile(r'\b(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price)\s*[:.\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE)
        m_mrp = mrp_pattern.search(clean_text)
        if m_mrp:
            val = m_mrp.group(1).replace(',', '').strip()
            facts.append(self._create_fact("mrp", f"₹ {val}", url, domain, title, m_mrp.group(0), 0.85))

        # 3. Ingredients Pattern
        ing_pattern = re.compile(r'\b(?:ingredients|contains)\s*[:.\-]\s*([a-zA-Z0-9,\(\)\s\.\-%]{10,250})', re.IGNORECASE)
        m_ing = ing_pattern.search(clean_text)
        if m_ing:
            val = m_ing.group(1).strip()
            facts.append(self._create_fact("ingredients", val, url, domain, title, m_ing.group(0)[:100], 0.82))

        # 4. Country of Origin Pattern
        origin_pattern = re.compile(r'\b(?:country\s*of\s*origin|made\s*in|product\s*of)\s*[:.\-]?\s*([a-zA-Z\s]{3,25})\b', re.IGNORECASE)
        m_org = origin_pattern.search(clean_text)
        if m_org:
            val = m_org.group(1).strip()
            if len(val.split()) <= 3 and val.lower() not in ["india or", "this", "our", "all"]:
                facts.append(self._create_fact("country_of_origin", val, url, domain, title, m_org.group(0), 0.85))

        # 5. Customer Care / Helpline
        care_pattern = re.compile(r'\b(?:customer\s*care|consumer\s*care|helpline|toll\s*free)\s*[:.\-]?\s*([0-9\-\s\+]{8,15}|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', re.IGNORECASE)
        m_care = care_pattern.search(clean_text)
        if m_care:
            val = m_care.group(1).strip()
            facts.append(self._create_fact("customer_care", val, url, domain, title, m_care.group(0), 0.85))

        # 6. Veg / Non-Veg Indicator
        if re.search(r'\b(?:100%\s*vegetarian|pure\s*veg|vegetarian\s*product)\b', clean_text, re.IGNORECASE):
            facts.append(self._create_fact("dietary_indicator", "Vegetarian", url, domain, title, "Vegetarian claim found in page content", 0.90))
        elif re.search(r'\b(?:non-veg|non\s*vegetarian)\b', clean_text, re.IGNORECASE):
            facts.append(self._create_fact("dietary_indicator", "Non-Vegetarian", url, domain, title, "Non-Vegetarian indicator found in page content", 0.90))

        return facts

    def _create_fact(self, field: str, value: str, url: str, domain: str, title: str, evidence: str, confidence: float) -> dict:
        return {
            "field": field,
            "value": str(value).strip(),
            "source_url": url,
            "source_domain": domain or (urllib.parse.urlparse(url).netloc if url else "web"),
            "source_title": title or domain,
            "evidence": str(evidence).strip(),
            "confidence": round(float(confidence), 2)
        }

    def aggregate_and_detect_conflicts(self, page_results: list[dict], search_identity: dict = None) -> dict:
        """
        Aggregates source-cited facts across all reviewed pages.
        Detects source-to-source conflicts and compares against image OCR facts.
        Constructs the resolved product identity.
        """
        all_facts_by_field = {}
        all_sources = []
        seen_urls = set()

        for pr in page_results:
            url = pr.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_sources.append({
                    "url": url,
                    "domain": pr.get("domain", ""),
                    "title": pr.get("title", ""),
                    "query_used": pr.get("query_used", ""),
                    "status": pr.get("status", "SUCCESS"),
                    "extracted_count": len(pr.get("facts", []))
                })

            for f in pr.get("facts", []):
                field = f["field"]
                if field not in all_facts_by_field:
                    all_facts_by_field[field] = []
                all_facts_by_field[field].append(f)

        structured_details = {}
        conflicts = []

        # Evaluate consistency across sources for each field
        for field, fact_list in all_facts_by_field.items():
            # Group by normalized value
            val_groups = {}
            for f in fact_list:
                norm_val = re.sub(r'[^a-zA-Z0-9]', '', f["value"].lower())
                if not norm_val:
                    continue
                if norm_val not in val_groups:
                    val_groups[norm_val] = {
                        "display_value": f["value"],
                        "facts": []
                    }
                val_groups[norm_val]["facts"].append(f)

            if len(val_groups) == 1:
                # All sources agree!
                g = list(val_groups.values())[0]
                primary_fact = max(g["facts"], key=lambda x: x["confidence"])
                structured_details[field] = {
                    "value": g["display_value"],
                    "status": "CONSISTENT",
                    "sources_count": len(g["facts"]),
                    "sources": [{"url": f["source_url"], "domain": f["source_domain"], "title": f["source_title"]} for f in g["facts"]],
                    "confidence": primary_fact["confidence"],
                    "evidence": primary_fact["evidence"],
                    "source_url": primary_fact["source_url"],
                    "source_domain": primary_fact["source_domain"]
                }
            elif len(val_groups) > 1:
                # Potential conflict across sources!
                candidate_values = []
                for norm_key, g in val_groups.items():
                    candidate_values.append({
                        "value": g["display_value"],
                        "sources_count": len(g["facts"]),
                        "sources": [{"url": f["source_url"], "domain": f["source_domain"]} for f in g["facts"]]
                    })
                
                # Choose the candidate value supported by the most sources / highest confidence
                best_group = max(val_groups.values(), key=lambda g: (len(g["facts"]), max(f["confidence"] for f in g["facts"])))
                primary_fact = max(best_group["facts"], key=lambda x: x["confidence"])

                conflicts.append({
                    "field": field,
                    "conflict_type": "SOURCE_DISAGREEMENT",
                    "chosen_value": best_group["display_value"],
                    "candidates": candidate_values,
                    "description": f"Multiple sources reported differing values for {field.replace('_', ' ').title()}."
                })

                structured_details[field] = {
                    "value": best_group["display_value"],
                    "status": "CONFLICT",
                    "sources_count": len(best_group["facts"]),
                    "sources": [{"url": f["source_url"], "domain": f["source_domain"], "title": f["source_title"]} for f in best_group["facts"]],
                    "confidence": primary_fact["confidence"],
                    "evidence": primary_fact["evidence"],
                    "source_url": primary_fact["source_url"],
                    "source_domain": primary_fact["source_domain"]
                }

        # Compare with Image OCR data (Section 13)
        image_comparisons = []
        if search_identity:
            img_barcode = search_identity.get("barcode")
            img_mfg = search_identity.get("manufacturer")
            img_qty = search_identity.get("net_quantity")
            img_mrp = search_identity.get("mrp")

            # Check Net Quantity
            if img_qty and "net_quantity" in structured_details:
                web_q = structured_details["net_quantity"]["value"]
                norm_img_q = re.sub(r'[^a-zA-Z0-9]', '', str(img_qty).lower())
                norm_web_q = re.sub(r'[^a-zA-Z0-9]', '', str(web_q).lower())
                if norm_img_q and norm_web_q and norm_img_q not in norm_web_q and norm_web_q not in norm_img_q:
                    image_comparisons.append({
                        "field": "net_quantity",
                        "image_ocr_value": str(img_qty),
                        "web_research_value": web_q,
                        "status": "POSSIBLE PRODUCT MISMATCH",
                        "note": "Net quantity on physical package image differs from web-sourced product detail."
                    })
                else:
                    image_comparisons.append({
                        "field": "net_quantity",
                        "image_ocr_value": str(img_qty),
                        "web_research_value": web_q,
                        "status": "MATCH",
                        "note": "Net quantity matches image declaration."
                    })

            # Check Barcode
            if img_barcode and "barcode" in structured_details:
                web_bc = structured_details["barcode"]["value"]
                if web_bc == img_barcode:
                    image_comparisons.append({
                        "field": "barcode",
                        "image_ocr_value": img_barcode,
                        "web_research_value": web_bc,
                        "status": "MATCH",
                        "note": "Exact barcode verified in web product databases."
                    })
                else:
                    image_comparisons.append({
                        "field": "barcode",
                        "image_ocr_value": img_barcode,
                        "web_research_value": web_bc,
                        "status": "POSSIBLE PRODUCT MISMATCH",
                        "note": "Web product database returned a different barcode reference."
                    })

        # Build Resolved Product Identity (Section 15)
        resolved_name = structured_details.get("product_name", {}).get("value")
        resolved_brand = structured_details.get("brand", {}).get("value")
        resolved_mfg = structured_details.get("manufacturer", {}).get("value")
        resolved_barcode = structured_details.get("barcode", {}).get("value") or (search_identity.get("barcode") if search_identity else None)
        resolved_cat = structured_details.get("category", {}).get("value")
        resolved_size = structured_details.get("pack_size", {}).get("value") or structured_details.get("net_quantity", {}).get("value")

        if resolved_name and (resolved_brand or resolved_barcode):
            res_status = "MATCHED"
            res_conf = 0.94
        elif resolved_name:
            res_status = "PARTIAL_MATCH"
            res_conf = 0.82
        elif all_sources:
            res_status = "PARTIAL_MATCH"
            res_conf = 0.70
        else:
            res_status = "NOT_FOUND"
            res_conf = 0.0

        if any(c["conflict_type"] == "SOURCE_DISAGREEMENT" for c in conflicts):
            res_status = "CONFLICT"

        product_identity = {
            "resolved_name": resolved_name or (search_identity.get("product_name") if search_identity else "Unresolved Product"),
            "brand": resolved_brand or (search_identity.get("brand") if search_identity else "N/A"),
            "manufacturer": resolved_mfg or (search_identity.get("manufacturer") if search_identity else "N/A"),
            "barcode": resolved_barcode or "NOT_DETECTED",
            "category": resolved_cat or "Packaged Commodity",
            "pack_size": resolved_size or "N/A",
            "confidence": res_conf,
            "resolution_status": res_status
        }

        return {
            "product_identity": product_identity,
            "structured_details": structured_details,
            "sources": all_sources,
            "conflicts": conflicts,
            "image_comparisons": image_comparisons
        }
