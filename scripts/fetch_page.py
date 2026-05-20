"""HTTP fetching utilities: page fetch, HTTPS check, redirect chain, robots.txt, 404."""

import requests
from urllib.parse import urlparse
from typing import Dict, List, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoogleSEOAudit/1.0; +https://github.com/google-seo-audit)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 15


def fetch_url(url: str) -> Dict:
    """Fetch a URL, return status, headers, HTML and redirect chain."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return {
            "url": url,
            "final_url": resp.url,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "html": resp.text,
            "redirect_chain": [r.url for r in resp.history],
            "redirect_count": len(resp.history),
            "content_type": resp.headers.get("Content-Type", ""),
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "final_url": None,
            "status_code": None,
            "headers": {},
            "html": None,
            "redirect_chain": [],
            "redirect_count": 0,
            "content_type": "",
            "error": str(exc),
        }


def check_https(base_url: str) -> Dict:
    """
    Verify HTTPS enforcement:
    - original URL uses HTTPS
    - http:// variant redirects to https://
    - TLS certificate is valid
    """
    parsed = urlparse(base_url)
    netloc = parsed.netloc
    path = parsed.path or "/"

    result = {
        "original_uses_https": parsed.scheme == "https",
        "http_redirects_to_https": False,
        "https_cert_valid": False,
        "confidence": "high",
        "evidence": [],
    }

    # Test http → https redirect
    http_url = f"http://{netloc}{path}"
    try:
        r = requests.get(http_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        result["http_redirects_to_https"] = r.url.startswith("https://")
        result["evidence"].append(f"GET {http_url} → {r.url} (status {r.status_code})")
    except requests.RequestException as exc:
        result["confidence"] = "medium"
        result["evidence"].append(f"HTTP redirect check failed: {exc}")

    # Test TLS cert validity + HSTS header
    https_url = f"https://{netloc}"
    try:
        r_https = requests.get(https_url, headers=HEADERS, timeout=TIMEOUT, verify=True)
        result["https_cert_valid"] = True
        result["evidence"].append(f"TLS certificate valid for {netloc}")
        hsts = r_https.headers.get("Strict-Transport-Security", "")
        result["hsts_present"] = bool(hsts)
        result["hsts_value"] = hsts or None
        if hsts:
            result["evidence"].append(f"HSTS header present: {hsts}")
        else:
            result["evidence"].append("HSTS header absent")
    except requests.exceptions.SSLError as exc:
        result["https_cert_valid"] = False
        result["hsts_present"] = False
        result["hsts_value"] = None
        result["evidence"].append(f"TLS certificate error: {exc}")
    except requests.RequestException as exc:
        result["confidence"] = "medium"
        result["hsts_present"] = False
        result["hsts_value"] = None
        result["evidence"].append(f"HTTPS cert check failed: {exc}")

    return result


def check_www_redirect(base_url: str) -> Dict:
    """Check www vs non-www redirect consistency."""
    parsed = urlparse(base_url)
    netloc = parsed.netloc

    if netloc.startswith("www."):
        bare = netloc[4:]
        www = netloc
    else:
        bare = netloc
        www = f"www.{netloc}"

    scheme = parsed.scheme or "https"
    www_url = f"{scheme}://{www}/"
    bare_url = f"{scheme}://{bare}/"

    result = {
        "www_url": www_url,
        "non_www_url": bare_url,
        "canonical_version": None,
        "consistent": False,
        "redirect_type": None,
        "confidence": "high",
        "evidence": [],
    }

    try:
        r_www = requests.get(www_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        r_bare = requests.get(bare_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)

        final_www = r_www.url.rstrip("/")
        final_bare = r_bare.url.rstrip("/")

        if final_www == final_bare:
            result["consistent"] = True
            result["canonical_version"] = r_www.url
            codes = [r.status_code for r in r_www.history + r_bare.history]
            result["redirect_type"] = "301" if 301 in codes else "302" if 302 in codes else "other"
        else:
            result["canonical_version"] = None
            result["redirect_type"] = "inconsistent"

        result["evidence"].append(f"{www_url} → {r_www.url}")
        result["evidence"].append(f"{bare_url} → {r_bare.url}")
    except requests.RequestException as exc:
        result["confidence"] = "low"
        result["evidence"].append(f"www redirect check failed: {exc}")

    return result


def check_robots_txt(base_url: str) -> Dict:
    """Fetch robots.txt, parse disallow rules and sitemap references."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Paths that, if disallowed, signal a likely misconfiguration
    sensitive_patterns = ["/", "/products", "/services", "/blog", "/articles", "/news"]

    result = {
        "exists": False,
        "url": robots_url,
        "content": None,
        "disallow_rules": [],
        "allow_rules": [],
        "sitemap_refs": [],
        "blocks_critical_paths": False,
        "confidence": "high",
        "evidence": [],
    }

    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and "text" in r.headers.get("Content-Type", ""):
            result["exists"] = True
            result["content"] = r.text

            current_ua_applies = False
            for raw_line in r.text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition(":")
                key, val = key.strip().lower(), val.strip()
                if key == "user-agent":
                    current_ua_applies = val in ("*", "googlebot")
                elif key == "sitemap" and val:
                    # Sitemap is a global directive; capture regardless of UA block position
                    if val not in result["sitemap_refs"]:
                        result["sitemap_refs"].append(val)
                elif current_ua_applies:
                    if key == "disallow" and val:
                        result["disallow_rules"].append(val)
                        if val == "/" or any(val.startswith(p) for p in sensitive_patterns[1:]):
                            result["blocks_critical_paths"] = True
                    elif key == "allow" and val:
                        result["allow_rules"].append(val)

            result["evidence"].append(
                f"robots.txt found at {robots_url}; "
                f"{len(result['disallow_rules'])} Disallow rules, "
                f"{len(result['sitemap_refs'])} Sitemap refs"
            )
        else:
            result["evidence"].append(f"robots.txt returned status {r.status_code}")
    except requests.RequestException as exc:
        result["confidence"] = "low"
        result["evidence"].append(f"robots.txt fetch failed: {exc}")

    return result


def check_404_page(base_url: str) -> Dict:
    """Verify the site returns a true 404 status for non-existent URLs."""
    parsed = urlparse(base_url)
    test_path = "/seo-audit-nonexistent-page-xk9q2.html"
    test_url = f"{parsed.scheme}://{parsed.netloc}{test_path}"

    result = {
        "test_url": test_url,
        "returns_proper_404": False,
        "actual_status_code": None,
        "has_custom_404_page": False,
        "confidence": "high",
        "evidence": [],
    }

    try:
        r = requests.get(test_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        size_bytes = len(r.content)
        result["actual_status_code"] = r.status_code
        result["returns_proper_404"] = r.status_code == 404
        result["has_custom_404_page"] = r.status_code == 404 and len(r.text) > 500
        result["response_size_bytes"] = size_bytes
        result["large_404_page"] = size_bytes > 100_000  # > 100 KB
        result["evidence"].append(
            f"GET {test_url} → HTTP {r.status_code} "
            f"({size_bytes // 1024} KB)"
        )
    except requests.RequestException as exc:
        result["confidence"] = "low"
        result["evidence"].append(f"404 check failed: {exc}")

    return result


def get_url_metrics(url: str) -> Dict:
    """Return URL depth and whether it appears static."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    depth = len([seg for seg in path.split("/") if seg]) if path else 0
    is_static = not bool(parsed.query)
    has_extension = "." in (path.split("/")[-1] if "/" in path else path)

    return {
        "depth": depth,
        "is_static": is_static,
        "has_extension": has_extension,
        "query_string": parsed.query or None,
        "evidence": [
            f"URL depth: {depth} level(s)",
            f"Query string: {'present' if parsed.query else 'absent'}",
        ],
    }


def check_llms_txt(base_url: str) -> Dict:
    """Check whether /llms.txt exists at the domain root (AI bot access declarations)."""
    parsed = urlparse(base_url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
    result = {
        "checked_url": llms_url,
        "exists": False,
        "content_preview": None,
        "error": None,
    }
    try:
        r = requests.get(llms_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
        if r.status_code == 200 and r.text.strip():
            result["exists"] = True
            result["content_preview"] = r.text.strip()[:300]
        else:
            result["error"] = f"HTTP {r.status_code}"
    except requests.RequestException as exc:
        result["error"] = str(exc)
    return result
