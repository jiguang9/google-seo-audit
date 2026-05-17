"""Sitemap discovery, fetching, parsing and validation."""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoogleSEOAudit/1.0)",
    "Accept": "application/xml,text/xml,*/*;q=0.8",
}
TIMEOUT = 15

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
    "video": "http://www.google.com/schemas/sitemap-video/1.1",
}


def find_sitemap_url(base_url: str, robots_sitemap_refs: Optional[List[str]] = None) -> Dict:
    """
    Locate sitemap URL by:
    1. Sitemap directives from robots.txt
    2. Standard /sitemap.xml path
    3. /sitemap_index.xml fallback
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    candidates = list(robots_sitemap_refs or [])
    candidates += [f"{origin}/sitemap.xml", f"{origin}/sitemap_index.xml"]

    result = {
        "found": False,
        "url": None,
        "source": None,
        "candidates_tried": [],
        "evidence": [],
    }

    for candidate in candidates:
        if candidate in result["candidates_tried"]:
            continue
        result["candidates_tried"].append(candidate)
        try:
            r = requests.head(candidate, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                result["found"] = True
                result["url"] = candidate
                result["source"] = "robots_txt" if candidate in (robots_sitemap_refs or []) else "default_path"
                result["evidence"].append(f"Sitemap found at {candidate} (HTTP 200)")
                return result
            else:
                result["evidence"].append(f"{candidate} → HTTP {r.status_code}")
        except requests.RequestException as exc:
            result["evidence"].append(f"{candidate} → error: {exc}")

    return result


def fetch_sitemap(sitemap_url: str) -> Dict:
    """Fetch sitemap XML content."""
    result = {
        "url": sitemap_url,
        "status_code": None,
        "content": None,
        "is_index": False,
        "error": None,
    }

    try:
        r = requests.get(sitemap_url, headers=HEADERS, timeout=TIMEOUT)
        result["status_code"] = r.status_code
        if r.status_code == 200:
            result["content"] = r.text
            result["is_index"] = "<sitemapindex" in r.text[:500]
    except requests.RequestException as exc:
        result["error"] = str(exc)

    return result


def _parse_url_entries(root: ET.Element) -> List[Dict]:
    """Parse <url> entries from a standard sitemap."""
    entries = []
    for url_el in root.findall(".//sm:url", NS):
        loc = url_el.findtext("sm:loc", default="", namespaces=NS)
        lastmod = url_el.findtext("sm:lastmod", namespaces=NS)
        changefreq = url_el.findtext("sm:changefreq", namespaces=NS)
        priority = url_el.findtext("sm:priority", namespaces=NS)
        entries.append({
            "loc": loc.strip() if loc else "",
            "lastmod": lastmod.strip() if lastmod else None,
            "changefreq": changefreq.strip() if changefreq else None,
            "priority": float(priority) if priority else None,
        })
    return entries


def _parse_sitemap_refs(root: ET.Element) -> List[str]:
    """Extract child sitemap URLs from a sitemap index."""
    return [
        el.findtext("sm:loc", default="", namespaces=NS).strip()
        for el in root.findall(".//sm:sitemap", NS)
    ]


def parse_sitemap_xml(content: str, max_child_fetch: int = 3) -> Dict:
    """
    Parse sitemap XML, handling both sitemap index and standard sitemaps.
    Fetches up to max_child_fetch child sitemaps to count total URLs.
    """
    result = {
        "is_index": False,
        "child_sitemaps": [],
        "total_url_count": 0,
        "sampled_urls": [],
        "lastmod_dates": [],
        "has_lastmod": False,
        "parse_error": None,
        "evidence": [],
    }

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        result["parse_error"] = str(exc)
        result["evidence"].append(f"XML parse error: {exc}")
        return result

    tag = root.tag.lower()
    if "sitemapindex" in tag:
        result["is_index"] = True
        result["child_sitemaps"] = _parse_sitemap_refs(root)
        result["evidence"].append(
            f"Sitemap index with {len(result['child_sitemaps'])} child sitemap(s)"
        )

        # Sample first few child sitemaps for URL counts
        sampled_count = 0
        for child_url in result["child_sitemaps"][:max_child_fetch]:
            child_fetch = fetch_sitemap(child_url)
            if child_fetch["content"]:
                try:
                    child_root = ET.fromstring(child_fetch["content"])
                    entries = _parse_url_entries(child_root)
                    sampled_count += len(entries)
                    result["sampled_urls"].extend(e["loc"] for e in entries[:3])
                    result["lastmod_dates"].extend(
                        e["lastmod"] for e in entries if e["lastmod"]
                    )
                except ET.ParseError:
                    pass

        result["total_url_count"] = sampled_count
        result["evidence"].append(
            f"Sampled {min(max_child_fetch, len(result['child_sitemaps']))} child sitemaps: "
            f"~{sampled_count} URLs counted"
        )
    else:
        entries = _parse_url_entries(root)
        result["total_url_count"] = len(entries)
        result["sampled_urls"] = [e["loc"] for e in entries[:5]]
        result["lastmod_dates"] = [e["lastmod"] for e in entries if e["lastmod"]]
        result["evidence"].append(f"Standard sitemap with {len(entries)} URL entries")

    result["has_lastmod"] = bool(result["lastmod_dates"])

    # Freshness check: warn if most recent lastmod is very old
    if result["lastmod_dates"]:
        valid_dates = []
        for d in result["lastmod_dates"]:
            try:
                parsed_dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
                # Strip timezone for naive UTC comparison
                if parsed_dt.tzinfo is not None:
                    parsed_dt = parsed_dt.replace(tzinfo=None)
                valid_dates.append(parsed_dt)
            except ValueError:
                pass
        if valid_dates:
            most_recent = max(valid_dates)
            now = datetime.utcnow()
            days_old = (now - most_recent).days
            result["most_recent_lastmod"] = most_recent.date().isoformat()
            result["most_recent_days_old"] = days_old
            result["evidence"].append(
                f"Most recent lastmod: {most_recent.date()} ({days_old} days ago)"
            )

    return result


def validate_sitemap(sitemap_data: Dict) -> Dict:
    """Produce pass/warning/fail findings for the sitemap module."""
    findings = []

    if not sitemap_data.get("found"):
        findings.append({
            "check": "sitemap_exists",
            "status": "fail",
            "severity": "high",
            "confidence": "high",
            "evidence": "No sitemap.xml found at /sitemap.xml or in robots.txt",
            "impact": "Search engines cannot easily discover all pages",
            "fix": "Create and submit an XML sitemap via Google Search Console",
        })
        return {"findings": findings, "sitemap_data": sitemap_data}

    findings.append({
        "check": "sitemap_exists",
        "status": "pass",
        "severity": "high",
        "confidence": "high",
        "evidence": f"Sitemap found at {sitemap_data.get('url')}",
        "impact": "Sitemap present; helps Google discover pages",
        "fix": None,
    })

    parsed = sitemap_data.get("parsed", {})

    if parsed.get("parse_error"):
        findings.append({
            "check": "sitemap_valid_xml",
            "status": "fail",
            "severity": "high",
            "confidence": "high",
            "evidence": f"XML parse error: {parsed['parse_error']}",
            "impact": "Invalid sitemap cannot be processed by search engines",
            "fix": "Validate sitemap XML syntax and regenerate",
        })

    if not parsed.get("has_lastmod"):
        findings.append({
            "check": "sitemap_has_lastmod",
            "status": "warning",
            "severity": "low",
            "confidence": "medium",
            "evidence": "No <lastmod> dates found in sitemap entries",
            "impact": "Google may rely on crawl data for freshness instead",
            "fix": "Add <lastmod> dates to help Google prioritize recrawling",
        })

    days_old = parsed.get("most_recent_days_old")
    if days_old and days_old > 180:
        findings.append({
            "check": "sitemap_freshness",
            "status": "warning",
            "severity": "medium",
            "confidence": "medium",
            "evidence": f"Most recent lastmod is {days_old} days old",
            "impact": "Stale lastmod dates may signal inactive content",
            "fix": "Update lastmod when pages are modified; automate sitemap regeneration",
        })

    return {"findings": findings, "sitemap_data": sitemap_data}
