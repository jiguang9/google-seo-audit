"""
Unit tests for CSV parsers, HTML parsers, and sitemap parser.
Run: python -m pytest tests/test_parsers.py -v
     or: cd tests && python test_parsers.py
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest

# Add scripts/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_page import check_robots_txt
from parse_gsc import detect_gsc_export_type, parse_gsc_file
from parse_html import (
    check_ai_seo_readiness,
    detect_language,
    detect_site_type,
    parse_breadcrumbs,
    parse_canonical,
    parse_headings,
    parse_hreflang,
    parse_images,
    parse_links,
    parse_schema,
    parse_tkd,
    parse_viewport,
)
from parse_sitemap import parse_sitemap_xml
from score_report import (
    Finding,
    _score_from_findings,
    build_ai_seo_findings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp_csv(rows: list, fieldnames: list) -> str:
    """Write rows to a temp CSV file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    f.close()
    return f.name


def _cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# GSC CSV detection tests
# ---------------------------------------------------------------------------

class TestGSCDetection(unittest.TestCase):

    def test_detects_performance_queries(self):
        path = _write_temp_csv(
            [{"Query": "erp software", "Clicks": "100", "Impressions": "5000", "CTR": "2%", "Position": "4.2"}],
            ["Query", "Clicks", "Impressions", "CTR", "Position"],
        )
        detected, _ = detect_gsc_export_type(path)
        self.assertEqual(detected, "performance_queries")
        _cleanup(path)

    def test_detects_performance_pages(self):
        path = _write_temp_csv(
            [{"Page": "https://example.com/", "Clicks": "200", "Impressions": "8000", "CTR": "2.5%", "Position": "3.1"}],
            ["Page", "Clicks", "Impressions", "CTR", "Position"],
        )
        detected, _ = detect_gsc_export_type(path)
        self.assertEqual(detected, "performance_pages")
        _cleanup(path)

    def test_detects_coverage_pages(self):
        path = _write_temp_csv(
            [{"URL": "https://example.com/page", "Status": "Submitted and indexed", "Reason": ""}],
            ["URL", "Status", "Reason"],
        )
        detected, _ = detect_gsc_export_type(path)
        self.assertEqual(detected, "coverage_pages")
        _cleanup(path)

    def test_detects_links(self):
        path = _write_temp_csv(
            [{"Source domain": "ahrefs.com", "Target page": "https://example.com/"}],
            ["Source domain", "Target page"],
        )
        detected, _ = detect_gsc_export_type(path)
        self.assertEqual(detected, "links")
        _cleanup(path)

    def test_returns_unknown_for_unrecognised_format(self):
        path = _write_temp_csv(
            [{"foo": "bar", "baz": "qux"}],
            ["foo", "baz"],
        )
        detected, _ = detect_gsc_export_type(path)
        self.assertEqual(detected, "unknown")
        _cleanup(path)

    def test_returns_not_found_for_missing_file(self):
        detected, _ = detect_gsc_export_type("/tmp/this-file-does-not-exist-ever.csv")
        self.assertEqual(detected, "not_found")


# ---------------------------------------------------------------------------
# GSC CSV parsing tests
# ---------------------------------------------------------------------------

class TestGSCParsing(unittest.TestCase):

    def test_parse_performance_queries_basic(self):
        path = _write_temp_csv(
            [
                {"Query": "erp software", "Clicks": "100", "Impressions": "5000", "CTR": "2%", "Position": "4.2"},
                {"Query": "cloud erp", "Clicks": "80", "Impressions": "4000", "CTR": "2%", "Position": "15.3"},
            ],
            ["Query", "Clicks", "Impressions", "CTR", "Position"],
        )
        result = parse_gsc_file(path)
        self.assertEqual(result["type"], "performance_queries")
        self.assertEqual(result["total_queries"], 2)
        self.assertEqual(result["total_clicks"], 180)
        # position 15.3 should be a quick-win candidate
        self.assertTrue(any(q["query"] == "cloud erp" for q in result["quick_win_queries"]))
        _cleanup(path)

    def test_parse_coverage_pages_counts_errors(self):
        path = _write_temp_csv(
            [
                {"URL": "https://example.com/a", "Status": "Submitted and indexed", "Reason": ""},
                {"URL": "https://example.com/b", "Status": "Error", "Reason": "Server error (5xx)"},
                {"URL": "https://example.com/c", "Status": "Excluded", "Reason": "Duplicate page"},
            ],
            ["URL", "Status", "Reason"],
        )
        result = parse_gsc_file(path)
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["excluded_count"], 1)
        _cleanup(path)

    def test_parse_links_counts_domains(self):
        path = _write_temp_csv(
            [
                {"Source domain": "ahrefs.com", "Target page": "https://example.com/"},
                {"Source domain": "ahrefs.com", "Target page": "https://example.com/blog/"},
                {"Source domain": "moz.com", "Target page": "https://example.com/"},
            ],
            ["Source domain", "Target page"],
        )
        result = parse_gsc_file(path)
        self.assertEqual(result["unique_referring_domains"], 2)
        self.assertEqual(result["total_link_rows"], 3)
        _cleanup(path)

    def test_parse_links_has_no_da_dr(self):
        path = _write_temp_csv(
            [{"Source domain": "example.org", "Target page": "https://example.com/"}],
            ["Source domain", "Target page"],
        )
        result = parse_gsc_file(path)
        # Verify note about DA/DR absence is present
        self.assertIn("DA/DR", result.get("note", ""))
        _cleanup(path)


# ---------------------------------------------------------------------------
# HTML parsing tests
# ---------------------------------------------------------------------------

class TestHTMLParsing(unittest.TestCase):

    def _page(self, head="", body="", lang="en"):
        return f'<html lang="{lang}"><head>{head}</head><body>{body}</body></html>'

    def test_parse_tkd_extracts_title(self):
        html = self._page(head="<title>My Page Title</title>")
        result = parse_tkd(html)
        self.assertEqual(result["title"]["text"], "My Page Title")
        self.assertTrue(result["title"]["present"])

    def test_parse_tkd_missing_title(self):
        html = self._page()
        result = parse_tkd(html)
        self.assertFalse(result["title"]["present"])

    def test_parse_tkd_title_truncation_risk(self):
        long_title = "A" * 75
        html = self._page(head=f"<title>{long_title}</title>")
        result = parse_tkd(html)
        self.assertEqual(result["title"]["display_risk"], "truncation_likely")

    def test_parse_tkd_meta_keywords_note(self):
        html = self._page(head='<meta name="keywords" content="erp, software">')
        result = parse_tkd(html)
        self.assertIn("Google ignores", result["meta_keywords"]["note"])

    def test_parse_headings_h1_count(self):
        html = self._page(body="<h1>Main Title</h1><h2>Sub</h2><h3>Sub-sub</h3>")
        result = parse_headings(html)
        self.assertEqual(result["h1_count"], 1)
        self.assertFalse(result["multiple_h1_risk"])
        self.assertFalse(result["no_h1"])

    def test_parse_headings_level_skip_detected(self):
        html = self._page(body="<h1>Title</h1><h3>Skipped H2</h3>")
        result = parse_headings(html)
        self.assertTrue(len(result["level_skips"]) > 0)

    def test_parse_headings_multiple_h1(self):
        html = self._page(body="<h1>First</h1><h1>Second</h1>")
        result = parse_headings(html)
        self.assertEqual(result["h1_count"], 2)
        self.assertTrue(result["multiple_h1_risk"])

    def test_parse_headings_empty_h1_counted_separately(self):
        html = self._page(body="<h1></h1><h1></h1><h1>Real Title</h1>")
        result = parse_headings(html)
        self.assertEqual(result["h1_count"], 3)
        self.assertEqual(result["h1_empty_count"], 2)
        self.assertEqual(result["h1_with_text_count"], 1)
        self.assertIn("empty/hidden", result["evidence"])

    def test_parse_canonical_present(self):
        html = self._page(head='<link rel="canonical" href="https://example.com/page/">')
        result = parse_canonical(html, "https://example.com/page/")
        self.assertTrue(result["present"])
        self.assertEqual(result["href"], "https://example.com/page/")

    def test_parse_canonical_absent(self):
        html = self._page()
        result = parse_canonical(html)
        self.assertFalse(result["present"])
        self.assertIsNone(result["href"])

    def test_parse_images_alt_audit(self):
        html = self._page(body='''
            <img src="a.jpg" alt="Good alt">
            <img src="b.webp">
            <img src="c.png" alt="">
        ''')
        result = parse_images(html)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["missing_alt_count"], 1)
        self.assertEqual(result["empty_alt_count"], 1)
        self.assertEqual(result["modern_format_count"], 1)

    def test_parse_links_internal_external(self):
        html = self._page(body='''
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
            <a href="https://external.com/page">External</a>
            <a href="https://www.example.com/blog">Blog</a>
        ''')
        result = parse_links(html, "https://example.com")
        self.assertEqual(result["internal_count"], 3)
        self.assertEqual(result["external_count"], 1)

    def test_parse_links_weak_anchors_detected(self):
        html = self._page(body='''
            <a href="/page1">Click here</a>
            <a href="/page2">Read more</a>
            <a href="/page3">Enterprise ERP Software</a>
        ''')
        result = parse_links(html, "https://example.com")
        self.assertEqual(result["weak_anchor_count"], 2)

    def test_parse_viewport_present(self):
        html = self._page(head='<meta name="viewport" content="width=device-width, initial-scale=1">')
        result = parse_viewport(html)
        self.assertTrue(result["present"])
        self.assertTrue(result["has_width_device"])

    def test_parse_viewport_absent(self):
        html = self._page()
        result = parse_viewport(html)
        self.assertFalse(result["present"])

    def test_parse_schema_detects_jsonld(self):
        schema_data = json.dumps({"@context": "https://schema.org", "@type": "Organization", "name": "Example"})
        html = self._page(head=f'<script type="application/ld+json">{schema_data}</script>')
        result = parse_schema(html)
        self.assertTrue(result["present"])
        self.assertIn("Organization", result["types"])
        self.assertIn("Organization", result["eligible_for_rich_results"])

    def test_parse_schema_invalid_json(self):
        html = self._page(head='<script type="application/ld+json">{invalid json}</script>')
        result = parse_schema(html)
        self.assertFalse(result["present"])
        self.assertTrue(len(result["parse_errors"]) > 0)

    def test_detect_language_html_attr(self):
        html = '<html lang="zh-CN"><head></head><body></body></html>'
        result = detect_language(html)
        self.assertEqual(result["lang_code"], "zh")
        self.assertEqual(result["report_language"], "zh")

    def test_detect_language_defaults_to_en(self):
        html = "<html><head></head><body></body></html>"
        result = detect_language(html)
        self.assertEqual(result["report_language"], "en")

    def test_detect_language_cn_mapped_to_zh(self):
        # Common mistake on Chinese sites: lang="cn" instead of lang="zh-CN"
        html = '<html lang="cn"><head></head><body></body></html>'
        result = detect_language(html)
        self.assertEqual(result["lang_code"], "zh")
        self.assertEqual(result["report_language"], "zh")

    def test_detect_language_zh_underscore_locale(self):
        # og:locale often uses underscore: zh_CN
        html = '<html><head><meta property="og:locale" content="zh_CN"></head><body></body></html>'
        result = detect_language(html)
        self.assertEqual(result["lang_code"], "zh")
        self.assertEqual(result["report_language"], "zh")

    def test_detect_language_tw_mapped_to_zh(self):
        html = '<html lang="tw"><head></head><body></body></html>'
        result = detect_language(html)
        self.assertEqual(result["lang_code"], "zh")
        self.assertEqual(result["report_language"], "zh")

    def test_parse_breadcrumbs_schema_detected(self):
        schema_data = json.dumps({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        })
        html = self._page(head=f'<script type="application/ld+json">{schema_data}</script>')
        result = parse_breadcrumbs(html)
        self.assertTrue(result["schema_breadcrumb"])

    def test_parse_breadcrumbs_html_class(self):
        html = self._page(body='<nav class="breadcrumb"><a href="/">Home</a> › Page</nav>')
        result = parse_breadcrumbs(html)
        self.assertTrue(result["html_breadcrumb"])


# ---------------------------------------------------------------------------
# Sitemap parsing tests
# ---------------------------------------------------------------------------

class TestSitemapParsing(unittest.TestCase):

    def test_standard_sitemap(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2025-01-01</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/about/</loc>
    <lastmod>2025-01-15</lastmod>
  </url>
</urlset>"""
        result = parse_sitemap_xml(xml)
        self.assertFalse(result["is_index"])
        self.assertEqual(result["total_url_count"], 2)
        self.assertTrue(result["has_lastmod"])
        self.assertIn("https://example.com/", result["sampled_urls"])

    def test_sitemap_index(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-posts.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-pages.xml</loc>
  </sitemap>
</sitemapindex>"""
        result = parse_sitemap_xml(xml)
        self.assertTrue(result["is_index"])
        self.assertEqual(len(result["child_sitemaps"]), 2)

    def test_sitemap_invalid_xml(self):
        result = parse_sitemap_xml("<not valid xml <<<")
        self.assertIsNotNone(result["parse_error"])

    def test_sitemap_no_lastmod(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
</urlset>"""
        result = parse_sitemap_xml(xml)
        self.assertFalse(result["has_lastmod"])


# ---------------------------------------------------------------------------
# robots.txt parsing tests (unit-tests the parser logic directly)
# ---------------------------------------------------------------------------

class TestRobotsTxtParsing(unittest.TestCase):
    """
    Tests for the Sitemap-inside-UA-block bug fix.
    We patch requests.get to return controlled robots.txt content.
    """

    def _run_check(self, robots_content: str) -> dict:
        """Monkey-patch requests.get and call check_robots_txt."""
        import unittest.mock as mock
        import fetch_page

        fake_response = mock.MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"Content-Type": "text/plain"}
        fake_response.text = robots_content

        with mock.patch.object(fetch_page.requests, "get", return_value=fake_response):
            return check_robots_txt("https://example.com")

    def test_sitemap_outside_ua_block_captured(self):
        robots = (
            "User-agent: *\n"
            "Disallow: /private/\n"
            "\n"
            "Sitemap: https://example.com/sitemap.xml\n"
        )
        result = self._run_check(robots)
        self.assertIn("https://example.com/sitemap.xml", result["sitemap_refs"])

    def test_sitemap_inside_ua_block_still_captured(self):
        # Bug: previously Sitemap inside a matching UA block was silently dropped
        robots = (
            "User-agent: *\n"
            "Disallow: /private/\n"
            "Sitemap: https://example.com/sitemap-inside.xml\n"
        )
        result = self._run_check(robots)
        self.assertIn("https://example.com/sitemap-inside.xml", result["sitemap_refs"])

    def test_sitemap_deduplication(self):
        robots = (
            "Sitemap: https://example.com/sitemap.xml\n"
            "User-agent: *\n"
            "Sitemap: https://example.com/sitemap.xml\n"  # duplicate
        )
        result = self._run_check(robots)
        self.assertEqual(result["sitemap_refs"].count("https://example.com/sitemap.xml"), 1)

    def test_disallow_all_blocks_critical_paths(self):
        robots = "User-agent: *\nDisallow: /\n"
        result = self._run_check(robots)
        self.assertTrue(result["blocks_critical_paths"])

    def test_disallow_partial_not_flagged(self):
        robots = "User-agent: *\nDisallow: /admin/\n"
        result = self._run_check(robots)
        self.assertFalse(result["blocks_critical_paths"])


# ---------------------------------------------------------------------------
# New feature tests (CWV N/A score, schema limitation, hreflang validation,
# site type detection, AI SEO readiness, canonical-hreflang mismatch)
# ---------------------------------------------------------------------------

class TestCWVScoring(unittest.TestCase):
    """_score_from_findings returns None when all findings are data_needed."""

    def _dn(self, check):
        return Finding(
            module="Core Web Vitals", check=check, status="data_needed",
            severity="high", confidence="low", evidence="PSI rate limited",
            impact="", fix="use --psi-key",
        )

    def test_all_data_needed_returns_none(self):
        findings = [self._dn("psi_mobile"), self._dn("psi_desktop")]
        self.assertIsNone(_score_from_findings(findings))

    def test_mixed_findings_scores_normally(self):
        findings = [
            self._dn("psi_mobile"),
            Finding(module="Core Web Vitals", check="lcp_mobile", status="fail",
                    severity="high", confidence="high", evidence="LCP 5s", impact="slow"),
        ]
        score = _score_from_findings(findings)
        self.assertIsNotNone(score)
        self.assertLess(score, 100)

    def test_empty_findings_returns_100(self):
        self.assertEqual(_score_from_findings([]), 100)


class TestSchemaDetectionLimitation(unittest.TestCase):

    def test_no_schema_evidence_includes_limitation(self):
        html = "<html><head><title>Test</title></head><body>Hello</body></html>"
        result = parse_schema(html)
        self.assertFalse(result["present"])
        self.assertIn("Static HTML scan", result["evidence"])
        self.assertIn("detection_limitation", result)

    def test_no_schema_confidence_is_medium_in_findings(self):
        from score_report import build_technical_findings
        audit = {
            "https": {"original_uses_https": True, "http_redirects_to_https": True, "evidence": []},
            "www_redirect": {"consistent": True, "evidence": []},
            "robots": {"exists": True, "blocks_critical_paths": False, "disallow_rules": []},
            "page_404": {"returns_proper_404": True, "has_custom_404_page": True},
            "url_info": {"depth": 1, "is_static": True, "query_string": None},
            "canonical": {"present": True, "href": "https://example.com/", "evidence": "canonical: https://example.com/"},
            "schema": {"present": False, "evidence": "No JSON-LD found in static HTML. Static HTML scan only."},
            "hreflang": {"present": False, "count": 0, "entries": [], "issues": []},
        }
        findings = build_technical_findings(audit)
        schema_f = next((f for f in findings if f.check == "structured_data"), None)
        self.assertIsNotNone(schema_f)
        self.assertEqual(schema_f.confidence, "medium")
        self.assertEqual(schema_f.status, "warning")


class TestHreflangValidation(unittest.TestCase):

    def test_missing_self_reference(self):
        html = """<html><head>
        <link rel="alternate" hreflang="en" href="https://example.com/">
        <link rel="alternate" hreflang="zh" href="https://example.com/zh/">
        <link rel="alternate" hreflang="x-default" href="https://example.com/">
        </head><body></body></html>"""
        result = parse_hreflang(html, "https://example.com/zh/page/")
        self.assertIn("missing_self_reference", result["issues"])
        self.assertFalse(result["self_referencing"])

    def test_self_referencing_pass(self):
        html = """<html><head>
        <link rel="alternate" hreflang="en" href="https://example.com/">
        <link rel="alternate" hreflang="x-default" href="https://example.com/">
        </head><body></body></html>"""
        result = parse_hreflang(html, "https://example.com/")
        self.assertTrue(result["self_referencing"])
        self.assertNotIn("missing_self_reference", result["issues"])

    def test_missing_x_default(self):
        html = """<html><head>
        <link rel="alternate" hreflang="en" href="https://example.com/">
        <link rel="alternate" hreflang="zh" href="https://example.com/zh/">
        </head><body></body></html>"""
        result = parse_hreflang(html, "https://example.com/")
        self.assertIn("missing_x_default", result["issues"])
        self.assertFalse(result["has_x_default"])

    def test_invalid_lang_code_en_uk(self):
        html = """<html><head>
        <link rel="alternate" hreflang="en-UK" href="https://example.com/en/">
        <link rel="alternate" hreflang="x-default" href="https://example.com/">
        </head><body></body></html>"""
        result = parse_hreflang(html)
        self.assertIn("invalid_lang_codes", result["issues"])
        codes = [c["code"] for c in result["invalid_codes"]]
        self.assertIn("en-UK", codes)

    def test_relative_hrefs_detected(self):
        html = """<html><head>
        <link rel="alternate" hreflang="en" href="/en/">
        <link rel="alternate" hreflang="x-default" href="/">
        </head><body></body></html>"""
        result = parse_hreflang(html)
        self.assertIn("relative_hrefs", result["issues"])

    def test_no_hreflang_no_issues(self):
        html = "<html><head></head><body></body></html>"
        result = parse_hreflang(html)
        self.assertFalse(result["present"])
        self.assertEqual(result["issues"], [])


class TestSiteTypeDetection(unittest.TestCase):

    def test_ecommerce_from_text(self):
        html = "<html><body><button>Add to Cart</button><span>Buy Now</span></body></html>"
        result = detect_site_type(html, "https://shop.example.com/product")
        self.assertEqual(result["type"], "ecommerce")

    def test_ecommerce_from_schema(self):
        html = "<html><body></body></html>"
        result = detect_site_type(html, "https://example.com/", schema_types=["Product", "Offer"])
        self.assertEqual(result["type"], "ecommerce")

    def test_blog_from_url(self):
        html = "<html><body></body></html>"
        result = detect_site_type(html, "https://example.com/blog/my-post")
        self.assertEqual(result["type"], "blog")

    def test_saas_from_pricing_text(self):
        html = "<html><body><p>Free trial available. $29 per month per user.</p></body></html>"
        result = detect_site_type(html, "https://app.example.com/pricing")
        self.assertEqual(result["type"], "saas")

    def test_general_fallback(self):
        html = "<html><body><p>Hello world.</p></body></html>"
        result = detect_site_type(html, "https://example.com/")
        self.assertEqual(result["type"], "general")


class TestAISEOReadiness(unittest.TestCase):

    def test_faq_schema_detected(self):
        html = """<html><head>
        <script type="application/ld+json">{"@type": "FAQPage"}</script>
        </head><body></body></html>"""
        result = check_ai_seo_readiness(html, "https://example.com/")
        self.assertTrue(result["has_faq_schema"])
        self.assertIn("faq_or_howto_schema", result["present"])

    def test_entity_schema_detected(self):
        html = """<html><head>
        <script type="application/ld+json">{"@type": "Organization", "name": "Acme"}</script>
        </head><body></body></html>"""
        result = check_ai_seo_readiness(html, "https://example.com/")
        self.assertTrue(result["has_entity_schema"])
        self.assertIn("entity_schema", result["present"])

    def test_missing_signals_listed(self):
        html = "<html><body><p>Hello world.</p></body></html>"
        result = check_ai_seo_readiness(html, "https://example.com/")
        self.assertIn("faq_or_howto_schema", result["missing"])
        self.assertIn("entity_schema", result["missing"])

    def test_llms_txt_url_generated(self):
        result = check_ai_seo_readiness("<html><body></body></html>", "https://example.com/page")
        self.assertEqual(result["llms_txt_url"], "https://example.com/llms.txt")


class TestAISEOFindings(unittest.TestCase):

    def test_missing_faq_and_entity_generate_warnings(self):
        audit = {
            "ai_seo": {
                "has_faq_schema": False, "has_entity_schema": False,
                "has_qa_content": False, "has_author": False,
            },
            "llms_txt": {"exists": False, "checked_url": "https://example.com/llms.txt"},
        }
        findings = build_ai_seo_findings(audit)
        statuses = {f.check: f.status for f in findings}
        self.assertEqual(statuses.get("faq_schema"), "warning")
        self.assertEqual(statuses.get("entity_clarity"), "warning")
        self.assertEqual(statuses.get("llms_txt"), "warning")

    def test_present_signals_generate_passes(self):
        audit = {
            "ai_seo": {
                "has_faq_schema": True, "has_entity_schema": True,
                "has_qa_content": True, "has_author": True,
            },
            "llms_txt": {"exists": True, "checked_url": "https://example.com/llms.txt"},
        }
        findings = build_ai_seo_findings(audit)
        statuses = {f.check: f.status for f in findings}
        self.assertEqual(statuses.get("faq_schema"), "pass")
        self.assertEqual(statuses.get("entity_clarity"), "pass")
        self.assertEqual(statuses.get("llms_txt"), "pass")

    def test_empty_ai_seo_returns_no_findings(self):
        self.assertEqual(build_ai_seo_findings({}), [])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
