"""
Google Search Console CSV parser with automatic export-type detection.

Supported export types:
  - performance_queries : Query, Clicks, Impressions, CTR, Position
  - performance_pages   : Page, Clicks, Impressions, CTR, Position
  - coverage_pages      : URL, Status, Reason (indexing coverage)
  - links               : Source domain, Target page (backlinks)
  - core_web_vitals     : URL, Status, Category, Type
  - enhancements        : URL, Enhancement type, Status
"""

import csv
import io
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Type detection
# ---------------------------------------------------------------------------

def detect_gsc_export_type(filepath: str) -> Tuple[str, List[str]]:
    """
    Auto-detect GSC export type by inspecting header columns.
    Returns (type_string, header_columns).
    """
    path = Path(filepath)
    if not path.exists():
        return "not_found", []

    try:
        with open(filepath, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            headers = [h.strip().lower() for h in next(reader)]
    except (StopIteration, UnicodeDecodeError):
        return "unreadable", []

    header_set = set(headers)

    if "query" in header_set and "clicks" in header_set and "impressions" in header_set:
        return "performance_queries", headers
    if "page" in header_set and "clicks" in header_set and "impressions" in header_set:
        return "performance_pages", headers
    if "url" in header_set and "status" in header_set and "reason" in header_set:
        return "coverage_pages", headers
    if any("source" in h for h in headers) and any("target" in h for h in headers):
        return "links", headers
    if "url" in header_set and "category" in header_set and "type" in header_set:
        return "core_web_vitals", headers
    if "url" in header_set and any("enhancement" in h for h in headers):
        return "enhancements", headers

    return "unknown", headers


def _read_csv_rows(filepath: str) -> List[Dict]:
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {k.strip(): v.strip() for k, v in row.items()}
            for row in reader
        ]


# ---------------------------------------------------------------------------
# Per-type parsers
# ---------------------------------------------------------------------------

def _safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val.replace("%", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return default


def parse_performance_queries(filepath: str) -> Dict:
    """Analyse query-level performance: top queries, CTR, ranking distribution."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file", "rows": []}

    # Normalise column names (GSC may localise headers)
    col_map = {}
    for key in rows[0]:
        lk = key.lower()
        if "query" in lk:
            col_map["query"] = key
        elif "click" in lk:
            col_map["clicks"] = key
        elif "impression" in lk:
            col_map["impressions"] = key
        elif "ctr" in lk:
            col_map["ctr"] = key
        elif "position" in lk:
            col_map["position"] = key

    parsed = []
    for row in rows:
        parsed.append({
            "query": row.get(col_map.get("query", ""), ""),
            "clicks": int(_safe_float(row.get(col_map.get("clicks", ""), "0"))),
            "impressions": int(_safe_float(row.get(col_map.get("impressions", ""), "0"))),
            "ctr": _safe_float(row.get(col_map.get("ctr", ""), "0")),
            "position": _safe_float(row.get(col_map.get("position", ""), "0")),
        })

    parsed.sort(key=lambda x: x["clicks"], reverse=True)

    total_clicks = sum(r["clicks"] for r in parsed)
    total_impressions = sum(r["impressions"] for r in parsed)
    avg_position = (
        sum(r["position"] * r["impressions"] for r in parsed) / total_impressions
        if total_impressions else 0
    )

    # Ranking distribution buckets
    pos_buckets = {"top3": 0, "4_10": 0, "11_20": 0, "21_plus": 0}
    for r in parsed:
        p = r["position"]
        if p <= 3:
            pos_buckets["top3"] += 1
        elif p <= 10:
            pos_buckets["4_10"] += 1
        elif p <= 20:
            pos_buckets["11_20"] += 1
        else:
            pos_buckets["21_plus"] += 1

    # Low-hanging fruit: good impressions but low position (quick-win opportunities)
    quick_wins = [
        r for r in parsed
        if 10 < r["position"] <= 20 and r["impressions"] > 100
    ]

    return {
        "type": "performance_queries",
        "total_queries": len(parsed),
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_position": round(avg_position, 1),
        "position_distribution": pos_buckets,
        "top_queries_by_clicks": parsed[:10],
        "quick_win_queries": sorted(quick_wins, key=lambda x: x["impressions"], reverse=True)[:10],
        "evidence": (
            f"{len(parsed)} queries, {total_clicks} total clicks, "
            f"{total_impressions} impressions, avg position {round(avg_position, 1)}"
        ),
    }


def parse_performance_pages(filepath: str) -> Dict:
    """Analyse page-level performance: best/worst pages, CTR distribution."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file"}

    col_map = {}
    for key in (rows[0] if rows else {}):
        lk = key.lower()
        if "page" in lk or "url" in lk:
            col_map.setdefault("page", key)
        elif "click" in lk:
            col_map["clicks"] = key
        elif "impression" in lk:
            col_map["impressions"] = key
        elif "ctr" in lk:
            col_map["ctr"] = key
        elif "position" in lk:
            col_map["position"] = key

    parsed = []
    for row in rows:
        parsed.append({
            "page": row.get(col_map.get("page", ""), ""),
            "clicks": int(_safe_float(row.get(col_map.get("clicks", ""), "0"))),
            "impressions": int(_safe_float(row.get(col_map.get("impressions", ""), "0"))),
            "ctr": _safe_float(row.get(col_map.get("ctr", ""), "0")),
            "position": _safe_float(row.get(col_map.get("position", ""), "0")),
        })

    parsed.sort(key=lambda x: x["clicks"], reverse=True)

    # Low-CTR pages with high impressions
    low_ctr_pages = [
        r for r in parsed
        if r["impressions"] > 500 and r["ctr"] < 2.0
    ]

    return {
        "type": "performance_pages",
        "total_pages": len(parsed),
        "top_pages_by_clicks": parsed[:10],
        "low_ctr_high_impression_pages": sorted(
            low_ctr_pages, key=lambda x: x["impressions"], reverse=True
        )[:10],
        "evidence": f"{len(parsed)} pages analysed from GSC performance export",
    }


def parse_coverage_pages(filepath: str) -> Dict:
    """Analyse indexing coverage: excluded/error/valid pages."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file"}

    status_counts = Counter()
    reason_counts = Counter()
    error_urls = []
    excluded_urls = []

    for row in rows:
        # GSC coverage columns vary by language; try common variants
        url = row.get("URL") or row.get("url") or ""
        status = row.get("Status") or row.get("status") or row.get("Coverage") or ""
        reason = row.get("Reason") or row.get("reason") or row.get("Reason for exclusion") or ""

        status_counts[status] += 1
        if reason:
            reason_counts[reason] += 1

        status_lower = status.lower()
        if "error" in status_lower:
            error_urls.append({"url": url, "status": status, "reason": reason})
        elif "excluded" in status_lower or "not indexed" in status_lower:
            excluded_urls.append({"url": url, "status": status, "reason": reason})

    total = len(rows)
    indexed = status_counts.get("Valid", 0) + status_counts.get("Submitted and indexed", 0)

    return {
        "type": "coverage_pages",
        "total_urls": total,
        "status_breakdown": dict(status_counts),
        "top_exclusion_reasons": reason_counts.most_common(10),
        "error_count": len(error_urls),
        "error_url_samples": error_urls[:5],
        "excluded_count": len(excluded_urls),
        "excluded_url_samples": excluded_urls[:5],
        "evidence": (
            f"{total} URLs: {len(error_urls)} errors, "
            f"{len(excluded_urls)} excluded. "
            f"Top reason: {reason_counts.most_common(1)[0] if reason_counts else 'n/a'}"
        ),
    }


def parse_links(filepath: str) -> Dict:
    """Analyse backlink data from GSC Links export."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file"}

    # Column names vary; detect source/target
    source_col, target_col = None, None
    for key in (rows[0] if rows else {}):
        lk = key.lower()
        if "source" in lk or "referring" in lk or "external" in lk:
            source_col = key
        if "target" in lk or "your" in lk:
            target_col = key

    if not source_col:
        return {"error": "Could not detect source domain column", "columns": list(rows[0].keys()) if rows else []}

    source_domains = Counter()
    target_pages = Counter()

    for row in rows:
        src = row.get(source_col, "").strip()
        tgt = row.get(target_col, "").strip() if target_col else ""
        if src:
            source_domains[src] += 1
        if tgt:
            target_pages[tgt] += 1

    total_links = len(rows)
    unique_domains = len(source_domains)
    top_sources = source_domains.most_common(20)
    concentration = top_sources[0][1] / total_links if total_links and top_sources else 0

    # Basic spam signal: very long TLD list or numeric-heavy domains
    spam_signals = [
        d for d, _ in top_sources
        if len(d) > 60 or sum(c.isdigit() for c in d) > len(d) * 0.4
    ]

    return {
        "type": "links",
        "total_link_rows": total_links,
        "unique_referring_domains": unique_domains,
        "top_referring_domains": top_sources[:20],
        "top_linked_pages": target_pages.most_common(10),
        "top_source_concentration_pct": round(concentration * 100, 1),
        "potential_spam_domain_signals": spam_signals[:5],
        "note": (
            "GSC links export does not include DA/DR. "
            "Authority scores require Ahrefs/Moz/Semrush."
        ),
        "evidence": (
            f"{total_links} link rows, {unique_domains} unique referring domains. "
            f"Top source: {top_sources[0] if top_sources else 'n/a'}"
        ),
    }


def parse_cwv_report(filepath: str) -> Dict:
    """Parse GSC Core Web Vitals report export."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file"}

    status_counts = Counter()
    category_counts = Counter()

    for row in rows:
        status = row.get("Status", row.get("status", ""))
        category = row.get("Category", row.get("category", ""))
        status_counts[status] += 1
        if category:
            category_counts[category] += 1

    return {
        "type": "core_web_vitals",
        "total_urls": len(rows),
        "status_breakdown": dict(status_counts),
        "category_breakdown": dict(category_counts),
        "evidence": (
            f"GSC CWV report: {len(rows)} URLs. "
            f"Status breakdown: {dict(status_counts)}"
        ),
    }


def parse_enhancements(filepath: str) -> Dict:
    """Parse GSC rich results / enhancements report."""
    rows = _read_csv_rows(filepath)
    if not rows:
        return {"error": "Empty file"}

    status_counts = Counter()
    enhancement_types = Counter()

    for row in rows:
        status = row.get("Status", row.get("status", ""))
        etype = None
        for k in row:
            if "enhancement" in k.lower() or "type" in k.lower():
                etype = row[k]
                break
        status_counts[status] += 1
        if etype:
            enhancement_types[etype] += 1

    return {
        "type": "enhancements",
        "total_urls": len(rows),
        "status_breakdown": dict(status_counts),
        "enhancement_types": dict(enhancement_types),
        "evidence": (
            f"GSC enhancements: {len(rows)} URLs. "
            f"Types: {dict(enhancement_types)}"
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_gsc_file(filepath: str) -> Dict:
    """
    Auto-detect GSC export type and dispatch to the appropriate parser.
    Returns parsed data or an error dict if type is unrecognized.
    """
    export_type, headers = detect_gsc_export_type(filepath)

    dispatchers = {
        "performance_queries": parse_performance_queries,
        "performance_pages": parse_performance_pages,
        "coverage_pages": parse_coverage_pages,
        "links": parse_links,
        "core_web_vitals": parse_cwv_report,
        "enhancements": parse_enhancements,
    }

    if export_type == "not_found":
        return {"error": f"File not found: {filepath}"}

    if export_type == "unreadable":
        return {"error": f"File could not be read (encoding issue?): {filepath}"}

    if export_type == "unknown":
        return {
            "error": "Unrecognized GSC export format",
            "detected_headers": headers,
            "hint": (
                "Expected columns for supported types:\n"
                "  performance_queries: Query, Clicks, Impressions, CTR, Position\n"
                "  performance_pages  : Page, Clicks, Impressions, CTR, Position\n"
                "  coverage_pages     : URL, Status, Reason\n"
                "  links              : Source domain, Target page\n"
                "  core_web_vitals    : URL, Status, Category, Type\n"
                "  enhancements       : URL, Enhancement type, Status"
            ),
        }

    result = dispatchers[export_type](filepath)
    result["detected_type"] = export_type
    return result
