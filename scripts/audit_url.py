"""
Main orchestrator for the Google SEO audit.

Usage:
    python audit_url.py https://example.com
    python audit_url.py https://example.com --psi-key=AIza...
    python audit_url.py https://example.com --psi-key=AIza... --gsc=./gsc.csv
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from datetime import date
from typing import Optional
from urllib.parse import urlparse

from fetch_page import (
    check_404_page,
    check_https,
    check_robots_txt,
    check_www_redirect,
    fetch_url,
    get_url_metrics,
)
from pagespeed import generate_cwv_findings, run_psi_both_strategies
from parse_gsc import parse_gsc_file
from parse_html import (
    check_eeat_signals,
    detect_language,
    parse_breadcrumbs,
    parse_canonical,
    parse_headings,
    parse_hreflang,
    parse_images,
    parse_links,
    parse_og_tags,
    parse_schema,
    parse_tkd,
    parse_viewport,
)
from parse_sitemap import find_sitemap_url, fetch_sitemap, parse_sitemap_xml, validate_sitemap
from score_report import generate_report
from report_html import generate_html_report
from check_version import check_for_update, format_update_banner


_BLOCKED_HOSTS = re.compile(
    r"^(localhost|.*\.local|.*\.internal|.*\.localhost)$", re.I
)
_PRIVATE_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _check_safe_url(url: str) -> None:
    """Refuse localhost, loopback, and private-range targets."""
    host = urlparse(url).hostname or ""
    if _BLOCKED_HOSTS.match(host):
        raise ValueError(f"Refusing to audit private/local host: {host}")
    try:
        addr = ipaddress.ip_address(host)
        if any(addr in net for net in _PRIVATE_RANGES):
            raise ValueError(f"Refusing to audit private IP address: {host}")
    except ValueError as exc:
        if "Refusing" in str(exc):
            raise


def _normalise_url(raw: str) -> str:
    """Ensure URL has a scheme."""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw.rstrip("/")


def _extract_domain(url: str) -> str:
    return urlparse(url).netloc


def run_audit(
    url: str,
    psi_key: Optional[str] = None,
    gsc_file: Optional[str] = None,
    output_json: bool = False,
    github_owner: Optional[str] = "jiguang9",
    output_format: str = "html",
) -> str:
    """
    Full Google SEO audit pipeline.
    Returns a formatted markdown report string.
    """
    url = _normalise_url(url)
    _check_safe_url(url)   # blocks localhost / private IPs
    print(f"[audit] Starting audit for: {url}", flush=True)

    # ------------------------------------------------------------------
    # 0. Version check (non-blocking; never fails the audit)
    # ------------------------------------------------------------------
    update_banner = ""
    if github_owner:
        version_info = check_for_update(github_owner)
        update_banner = format_update_banner(version_info)
        if version_info.get("update_available"):
            print(f"[audit] {version_info['notice']}", flush=True)

    audit_data: dict = {
        "url": url,
        "date": date.today().isoformat(),
    }

    # ------------------------------------------------------------------
    # 1. Fetch page
    # ------------------------------------------------------------------
    print("[audit] Fetching page HTML ...", flush=True)
    page = fetch_url(url)
    html = page.get("html") or ""

    if not html:
        print(f"[audit] ERROR: Could not fetch {url} — {page.get('error')}", file=sys.stderr)
        return f"# Audit Failed\n\nCould not fetch `{url}`.\n\nError: {page.get('error')}"

    # ------------------------------------------------------------------
    # 2. Language detection
    # ------------------------------------------------------------------
    lang_info = detect_language(html, url)
    audit_data["detected_language"] = lang_info["detected"]
    report_language = lang_info["report_language"]
    print(f"[audit] Detected language: {lang_info['detected']} → report in: {report_language}", flush=True)

    # ------------------------------------------------------------------
    # 3. HTTPS & redirects
    # ------------------------------------------------------------------
    print("[audit] Checking HTTPS and redirects ...", flush=True)
    audit_data["https"] = check_https(url)
    audit_data["www_redirect"] = check_www_redirect(url)

    # ------------------------------------------------------------------
    # 4. robots.txt
    # ------------------------------------------------------------------
    print("[audit] Fetching robots.txt ...", flush=True)
    robots = check_robots_txt(url)
    audit_data["robots"] = robots

    # ------------------------------------------------------------------
    # 5. sitemap.xml
    # ------------------------------------------------------------------
    print("[audit] Locating and parsing sitemap ...", flush=True)
    sitemap_location = find_sitemap_url(url, robots.get("sitemap_refs", []))
    if sitemap_location["found"]:
        sitemap_fetch = fetch_sitemap(sitemap_location["url"])
        if sitemap_fetch["content"]:
            sitemap_location["parsed"] = parse_sitemap_xml(sitemap_fetch["content"])
        else:
            sitemap_location["parsed"] = {"error": sitemap_fetch.get("error")}
    audit_data["sitemap"] = sitemap_location
    sitemap_validation = validate_sitemap(sitemap_location)
    audit_data["sitemap_findings"] = sitemap_validation["findings"]

    # ------------------------------------------------------------------
    # 6. 404 page
    # ------------------------------------------------------------------
    print("[audit] Testing 404 handling ...", flush=True)
    audit_data["page_404"] = check_404_page(url)

    # ------------------------------------------------------------------
    # 7. URL metrics
    # ------------------------------------------------------------------
    audit_data["url_info"] = get_url_metrics(url)

    # ------------------------------------------------------------------
    # 8. HTML analysis
    # ------------------------------------------------------------------
    print("[audit] Analysing HTML (TKD, headings, schema, images, links) ...", flush=True)
    audit_data["tkd"] = parse_tkd(html)
    audit_data["headings"] = parse_headings(html)
    audit_data["canonical"] = parse_canonical(html, url)
    audit_data["hreflang"] = parse_hreflang(html)
    audit_data["schema"] = parse_schema(html)
    audit_data["images"] = parse_images(html, url)
    audit_data["links"] = parse_links(html, url)
    audit_data["viewport"] = parse_viewport(html)
    audit_data["og_tags"] = parse_og_tags(html)
    audit_data["eeat"] = check_eeat_signals(html, url)
    audit_data["breadcrumbs"] = parse_breadcrumbs(html)

    # ------------------------------------------------------------------
    # 9. PageSpeed Insights
    # ------------------------------------------------------------------
    print("[audit] Running PageSpeed Insights (mobile + desktop) ...", flush=True)
    psi_results = run_psi_both_strategies(url, api_key=psi_key)
    audit_data["psi"] = psi_results
    audit_data["cwv_findings"] = generate_cwv_findings(psi_results)

    # ------------------------------------------------------------------
    # 10. GSC data (optional)
    # ------------------------------------------------------------------
    if gsc_file:
        print(f"[audit] Parsing GSC export: {gsc_file} ...", flush=True)
        gsc_data = parse_gsc_file(gsc_file)
        audit_data["gsc"] = gsc_data
        if gsc_data.get("error"):
            print(f"[audit] GSC warning: {gsc_data['error']}", file=sys.stderr)
    else:
        audit_data["gsc"] = None

    # ------------------------------------------------------------------
    # 11. Generate report
    # ------------------------------------------------------------------
    print("[audit] Generating report ...", flush=True)
    if output_json:
        def _serial(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return obj.__dict__
            return str(obj)
        return json.dumps(audit_data, default=_serial, ensure_ascii=False, indent=2)

    if output_format == "html":
        # Pass update notice into audit_data so HTML generator can render it
        audit_data["_update_notice"] = update_banner.strip().lstrip(">").strip()
        return generate_html_report(audit_data, language=report_language)

    report = generate_report(audit_data, language=report_language)
    return update_banner + report


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Google SEO Audit — generates a prioritised SEO diagnostic report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audit_url.py https://example.com
  python audit_url.py https://example.com --psi-key=AIzaSy...
  python audit_url.py https://example.com --gsc=./gsc-export.csv
  python audit_url.py https://example.com --format=html --output=report.html
  python audit_url.py https://example.com --output=report.md
        """,
    )
    parser.add_argument("url", help="Target website URL")
    parser.add_argument("--psi-key", dest="psi_key", default=None,
                        help="Google PageSpeed Insights API key (optional; increases rate limit)")
    parser.add_argument("--gsc", dest="gsc_file", default=None,
                        help="Path to Google Search Console CSV export (optional)")
    parser.add_argument("--output", dest="output_file", default=None,
                        help="Save report to file instead of stdout")
    parser.add_argument("--json", dest="output_json", action="store_true",
                        help="Output raw audit data as JSON instead of markdown")
    parser.add_argument("--github-owner", dest="github_owner", default="jiguang9",
                        help="GitHub username for version check (default: jiguang9). Pass empty string to disable.")
    parser.add_argument("--format", dest="output_format", default="html",
                        choices=["md", "html"],
                        help="Output format: html (default) or md")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    report = run_audit(
        url=args.url,
        psi_key=args.psi_key,
        gsc_file=args.gsc_file,
        output_json=args.output_json,
        github_owner=args.github_owner,
        output_format=args.output_format,
    )

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[audit] Report saved to {args.output_file}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
