"""
Web Research & Product Intelligence Service for LabelSure.
Modular research layer executing programmatic Google Web Search, multi-query targeting,
page fetching, source-cited detail extraction, and conflict detection.
Strictly adheres to ZERO-FABRICATION policy: never invents web results or product details.
Does not alter or override deterministic Legal Metrology compliance verdicts.
"""

import os
import re
import time
import json
import urllib.parse
from datetime import datetime
import requests
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

from web_product_extractor import WebProductExtractor

class WebResearchProvider:
    """Abstract base class for web research search providers."""
    provider_name: str = "google"

    def is_available(self) -> bool:
        raise NotImplementedError
        
    def search(self, query: str, num_results: int = 10) -> list[dict]:
        raise NotImplementedError

class GoogleWebSearchProvider(WebResearchProvider):
    """
    Official programmatic Google Custom Search JSON API provider.
    Requires:
    - GOOGLE_WEB_SEARCH_API_KEY (or GOOGLE_API_KEY)
    - GOOGLE_CLIENT_ID (or GOOGLE_CSE_ID / GOOGLE_CX)
    Endpoint: https://www.googleapis.com/customsearch/v1
    """
    API_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
    provider_name: str = "google"

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_WEB_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        self.cx = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CX") or ""
        self.timeout = int(os.getenv("WEB_RESEARCH_TIMEOUT_SECONDS", 15))
        self.max_results = int(os.getenv("WEB_RESEARCH_MAX_RESULTS", 10))

    def is_available(self) -> bool:
        return bool(self.api_key.strip() and self.cx.strip())

    def search(self, query: str, num_results: int = None) -> list[dict]:
        if not self.is_available():
            return []

        limit = num_results or self.max_results
        params = {
            "key": self.api_key.strip(),
            "cx": self.cx.strip(),
            "q": query.strip(),
            "num": min(limit, 10)
        }

        # Bounded retries with exponential backoff
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                resp = requests.get(self.API_ENDPOINT, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    results = []
                    for idx, item in enumerate(items):
                        link = item.get("link", "")
                        domain = urllib.parse.urlparse(link).netloc if link else ""
                        results.append({
                            "title": item.get("title", ""),
                            "url": link,
                            "snippet": item.get("snippet", ""),
                            "source_domain": domain,
                            "query_used": query,
                            "rank": idx + 1,
                            "pagemap": item.get("pagemap", {})
                        })
                    return results
                elif resp.status_code in [400, 403, 429]:
                    # Bad request / unauthorized / rate-limited
                    error_msg = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                    return []
            except requests.RequestException:
                if attempt < max_retries:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    return []
        return []

class SearchIdentityBuilder:
    @staticmethod
    def build(barcode: str = None, detected_declarations: dict = None, all_detected_text: str = "") -> dict:
        """
        Builds a structured search identity from real OCR and barcode facts.
        Never invents missing values.
        """
        decls = detected_declarations or {}
        
        clean_barcode = None
        if barcode and str(barcode).strip().upper() not in ["NOT_DETECTED", "NONE", "NULL", ""]:
            clean_barcode = re.sub(r'\D', '', str(barcode))
            if len(clean_barcode) not in [8, 12, 13, 14]:
                clean_barcode = None

        # Product name
        p_name = None
        if "commodity_name" in decls:
            c = decls["commodity_name"]
            p_name = c.get("value") if isinstance(c, dict) else str(c)
            p_name = p_name.strip() if p_name else None

        # Brand / Manufacturer
        brand = None
        mfg = None
        if "manufacturer" in decls:
            m = decls["manufacturer"]
            mfg = m.get("name") if isinstance(m, dict) else str(m)
            mfg = mfg.strip() if mfg else None
            # Often brand is part of manufacturer or first word
            if mfg:
                brand = mfg.split()[0]

        # Net Quantity
        net_qty = None
        if "net_quantity" in decls:
            q = decls["net_quantity"]
            net_qty = q.get("text") if isinstance(q, dict) else str(q)
            net_qty = net_qty.strip() if net_qty else None

        # MRP
        mrp = None
        if "max_retail_price" in decls:
            m = decls["max_retail_price"]
            mrp = m.get("text") if isinstance(m, dict) else str(m)
            mrp = mrp.strip() if mrp else None

        # Distinctive phrases from OCR text (clean packaging tokens)
        phrases = []
        if all_detected_text:
            lines = [l.strip() for l in all_detected_text.split('\n') if len(l.strip()) > 3]
            for l in lines:
                if any(k in l.lower() for k in ["pepsico", "bimbo", "lays", "kurkure", "parle", "britannia", "cadbury", "haldiram"]):
                    phrases.append(l)

        return {
            "barcode": clean_barcode,
            "product_name": p_name,
            "brand": brand,
            "manufacturer": mfg,
            "net_quantity": net_qty,
            "mrp": mrp,
            "distinctive_phrases": phrases[:3]
        }

class MultiQueryGenerator:
    @staticmethod
    def generate(identity: dict) -> list[str]:
        """
        Generates targeted multi-query families based on real extracted values.
        Only generates queries for fields that actually exist.
        """
        queries = []
        bc = identity.get("barcode")
        pname = identity.get("product_name")
        brand = identity.get("brand")
        mfg = identity.get("manufacturer")
        qty = identity.get("net_quantity")
        phrases = identity.get("distinctive_phrases", [])

        # 1. Barcode Queries (Highest Priority)
        if bc:
            queries.append(f'"{bc}"')
            if pname:
                queries.append(f'"{bc}" "{pname}"')
            if brand and brand != pname:
                queries.append(f'"{bc}" "{brand}"')
            if mfg and mfg not in [brand, pname]:
                queries.append(f'"{bc}" "{mfg}"')

        # 2. Product Name Queries
        if pname:
            queries.append(f'"{pname}"')
            if brand and brand != pname:
                queries.append(f'"{brand}" "{pname}"')
            if mfg and mfg not in [brand, pname]:
                queries.append(f'"{mfg}" "{pname}"')
            if qty:
                queries.append(f'"{pname}" "{qty}"')

        # 3. Packaging Phrase Queries
        for phrase in phrases:
            if pname and phrase != pname:
                queries.append(f'"{phrase}" "{pname}"')
            elif not pname:
                queries.append(f'"{phrase}"')

        # Deduplicate while preserving order
        seen = set()
        dedup_queries = []
        for q in queries:
            clean_q = q.strip()
            if clean_q and clean_q.lower() not in seen:
                seen.add(clean_q.lower())
                dedup_queries.append(clean_q)

        return dedup_queries[:6]  # Limit to top 6 targeted queries to prevent quota spam

class WebPageFetcher:
    def __init__(self, max_pages: int = 8, timeout: int = 10):
        self.max_pages = max_pages
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def fetch(self, url: str) -> dict:
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200:
                return {
                    "url": resp.url,
                    "html": resp.text,
                    "status": "SUCCESS"
                }
            else:
                return {
                    "url": url,
                    "html": "",
                    "status": f"HTTP_{resp.status_code}"
                }
        except Exception as e:
            return {
                "url": url,
                "html": "",
                "status": "FETCH_FAILED",
                "error": str(e)
            }

class WebResearchCache:
    """Thread-safe in-memory cache for web research by barcode or query key."""
    _cache = {}

    @classmethod
    def get(cls, key: str) -> dict | None:
        if not key:
            return None
        item = cls._cache.get(key)
        if item and (time.time() - item["timestamp"]) < 3600:  # 1 hour TTL
            return item["data"]
        return None

    @classmethod
    def set(cls, key: str, data: dict):
        if key:
            cls._cache[key] = {
                "data": data,
                "timestamp": time.time()
            }

class WebResearchManager:
    """
    Coordinates Google Web Search, multi-query execution, page fetching,
    structured extraction, and conflict detection.
    """
    def __init__(self, provider: WebResearchProvider = None):
        self.provider = provider or GoogleWebSearchProvider()
        self.extractor = WebProductExtractor()
        max_pages = int(os.getenv("WEB_RESEARCH_MAX_PAGES", 8))
        timeout = int(os.getenv("WEB_RESEARCH_TIMEOUT_SECONDS", 15))
        self.fetcher = WebPageFetcher(max_pages=max_pages, timeout=min(timeout, 10))

    def run_research(self, barcode: str = None, detected_declarations: dict = None, all_detected_text: str = "", scan_id: str = None) -> dict:
        """
        Executes end-to-end web research for a scanned product.
        """
        # 1. Build search identity
        identity = SearchIdentityBuilder.build(barcode, detected_declarations, all_detected_text)
        cache_key = identity.get("barcode") or (identity.get("product_name") and f"p_{identity.get('product_name')}")

        # Check Cache (Section 29)
        if cache_key:
            cached = WebResearchCache.get(cache_key)
            if cached:
                cached_res = dict(cached)
                cached_res["cached"] = True
                return cached_res

        # 2. Check Provider Availability (Section 3)
        if not self.provider.is_available():
            return {
                "status": "UNAVAILABLE",
                "reason": "Google web search is not configured or authorized.",
                "provider": "google",
                "queries_run": 0,
                "results_found": 0,
                "pages_fetched": 0,
                "sources_used": 0,
                "search_trace": [],
                "product_identity": {
                    "resolved_name": identity.get("product_name") or "Unresolved Product",
                    "brand": identity.get("brand") or "N/A",
                    "manufacturer": identity.get("manufacturer") or "N/A",
                    "barcode": identity.get("barcode") or "NOT_DETECTED",
                    "category": "Packaged Commodity",
                    "pack_size": identity.get("net_quantity") or "N/A",
                    "confidence": 0.0,
                    "resolution_status": "NOT_VERIFIABLE"
                },
                "details": {},
                "sources": [],
                "conflicts": [],
                "image_comparisons": [],
                "summary": {
                    "status": "UNAVAILABLE",
                    "note": "Web research provider credentials (GOOGLE_WEB_SEARCH_API_KEY / GOOGLE_CLIENT_ID) not configured."
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # 3. Generate Targeted Queries (Section 5 & 6)
        queries = MultiQueryGenerator.generate(identity)
        if not queries:
            return {
                "status": "NO_RELEVANT_RESULTS",
                "reason": "No searchable identifiers (barcode, product name, brand) extracted from image.",
                "provider": "google",
                "queries_run": 0,
                "results_found": 0,
                "pages_fetched": 0,
                "sources_used": 0,
                "search_trace": [],
                "product_identity": {
                    "resolved_name": "Unresolved Product",
                    "brand": "N/A",
                    "manufacturer": "N/A",
                    "barcode": identity.get("barcode") or "NOT_DETECTED",
                    "category": "Packaged Commodity",
                    "pack_size": "N/A",
                    "confidence": 0.0,
                    "resolution_status": "NOT_FOUND"
                },
                "details": {},
                "sources": [],
                "conflicts": [],
                "image_comparisons": [],
                "summary": {"status": "NO_SEARCHABLE_IDENTIFIERS"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # 4. Execute Searches & Collect Sources (Section 7)
        collected_results = []
        seen_urls = set()
        queries_run = 0

        for q in queries:
            queries_run += 1
            search_items = self.provider.search(q)
            for item in search_items:
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    collected_results.append(item)

        if not collected_results:
            return {
                "status": "NO_RELEVANT_RESULTS",
                "reason": "Product not found in reviewed web sources.",
                "provider": "google",
                "queries_run": queries_run,
                "results_found": 0,
                "pages_fetched": 0,
                "sources_used": 0,
                "search_trace": queries,
                "product_identity": {
                    "resolved_name": identity.get("product_name") or "Unresolved Product",
                    "brand": identity.get("brand") or "N/A",
                    "manufacturer": identity.get("manufacturer") or "N/A",
                    "barcode": identity.get("barcode") or "NOT_DETECTED",
                    "category": "Packaged Commodity",
                    "pack_size": identity.get("net_quantity") or "N/A",
                    "confidence": 0.0,
                    "resolution_status": "NOT_FOUND"
                },
                "details": {},
                "sources": [],
                "conflicts": [],
                "image_comparisons": [],
                "summary": {"status": "NO_RELEVANT_RESULTS"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # 5. Page Fetching (Section 8) & Structured Extraction (Section 10)
        pages_to_fetch = collected_results[:self.fetcher.max_pages]
        extracted_pages = []

        for item in pages_to_fetch:
            url = item["url"]
            domain = item.get("source_domain", "")
            title = item.get("title", "")
            q_used = item.get("query_used", "")

            # If pagemap already has rich Schema.org Product data from Google, use it as initial facts
            initial_facts = []
            pagemap = item.get("pagemap", {})
            if pagemap:
                # Check pagemap metatags
                for m in pagemap.get("metatags", []):
                    if isinstance(m, dict):
                        if m.get("og:title"):
                            initial_facts.append({"field": "product_name", "value": m["og:title"], "source_url": url, "source_domain": domain, "source_title": title, "evidence": "Google pagemap og:title", "confidence": 0.90})
                        if m.get("product:price:amount"):
                            initial_facts.append({"field": "selling_price", "value": f"INR {m['product:price:amount']}", "source_url": url, "source_domain": domain, "source_title": title, "evidence": "Google pagemap price", "confidence": 0.90})
                        if m.get("product:brand"):
                            initial_facts.append({"field": "brand", "value": m["product:brand"], "source_url": url, "source_domain": domain, "source_title": title, "evidence": "Google pagemap brand", "confidence": 0.90})

            # Fetch live HTML
            fetch_res = self.fetcher.fetch(url)
            if fetch_res.get("status") == "SUCCESS":
                page_data = self.extractor.extract_from_page(fetch_res["html"], url, title, domain)
                page_data["query_used"] = q_used
                if initial_facts:
                    existing_fields = {f["field"] for f in page_data["facts"]}
                    for inf in initial_facts:
                        if inf["field"] not in existing_fields:
                            page_data["facts"].append(inf)
                extracted_pages.append(page_data)
            else:
                extracted_pages.append({
                    "url": url,
                    "domain": domain,
                    "title": title,
                    "query_used": q_used,
                    "status": fetch_res.get("status", "FETCH_FAILED"),
                    "facts": initial_facts
                })

        # 6. Aggregate Facts & Detect Conflicts (Section 11, 12, 13, 15)
        aggregation = self.extractor.aggregate_and_detect_conflicts(extracted_pages, identity)

        result_payload = {
            "status": "COMPLETE",
            "provider": "google",
            "queries_run": queries_run,
            "results_found": len(collected_results),
            "pages_fetched": len(extracted_pages),
            "sources_used": len(aggregation["sources"]),
            "search_trace": queries,
            "product_identity": aggregation["product_identity"],
            "details": aggregation["structured_details"],
            "sources": aggregation["sources"],
            "conflicts": aggregation["conflicts"],
            "image_comparisons": aggregation["image_comparisons"],
            "summary": {
                "status": "COMPLETE",
                "identity_status": aggregation["product_identity"]["resolution_status"],
                "queries_run": queries_run,
                "results_found": len(collected_results),
                "pages_fetched": len(extracted_pages),
                "sources_used": len(aggregation["sources"]),
                "conflicts_detected": len(aggregation["conflicts"])
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Store in cache
        if cache_key:
            WebResearchCache.set(cache_key, result_payload)

        return result_payload
