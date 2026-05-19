"""
Scoring engine and report generator.
Converts raw audit data into structured findings, module scores, and a
formatted markdown report in English or Chinese.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Finding dataclass
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    module: str
    check: str
    status: str          # pass | warning | fail | unknown | data_needed
    severity: str        # high | medium | low
    confidence: str      # high | medium | low
    evidence: str
    impact: str
    fix: Optional[str] = None
    detail: Optional[Any] = None


STATUS_EMOJI = {"pass": "✅", "warning": "⚠️", "fail": "❌", "unknown": "❓", "data_needed": "📊"}
SEVERITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


# ---------------------------------------------------------------------------
# Module scorers
# ---------------------------------------------------------------------------

def _score_from_findings(findings: List[Finding]) -> Optional[int]:
    """Compute a 0–100 module score. Returns None when all findings are data_needed (no real data)."""
    if not findings:
        return 100

    # All findings are data_needed → no actual data to score; show N/A rather than a misleading 100
    if all(f.status == "data_needed" for f in findings):
        return None

    weights = {"high": 3, "medium": 2, "low": 1}
    penalties = {"fail": 1.0, "warning": 0.4, "unknown": 0.2, "data_needed": 0.0, "pass": 0.0}

    total_weight = sum(weights.get(f.severity, 1) for f in findings)
    lost = sum(
        weights.get(f.severity, 1) * penalties.get(f.status, 0)
        for f in findings
    )
    ratio = lost / total_weight if total_weight else 0
    return max(0, round((1 - ratio) * 100))


def _status_label(score: Optional[int]) -> str:
    if score is None:
        return "unknown"
    if score >= 80:
        return "pass"
    if score >= 55:
        return "warning"
    return "fail"


# ---------------------------------------------------------------------------
# Build findings from raw audit data
# ---------------------------------------------------------------------------

def build_technical_findings(audit: Dict) -> List[Finding]:
    findings = []

    # HTTPS
    https = audit.get("https", {})
    if https.get("error"):
        findings.append(Finding(
            module="Technical SEO", check="https",
            status="unknown", severity="high", confidence="low",
            evidence=f"HTTPS check could not complete: {https['error']}",
            impact="HTTPS is a confirmed Google ranking signal",
            fix="Ensure the site is accessible and retry",
        ))
    elif not https.get("original_uses_https") or not https.get("http_redirects_to_https"):
        findings.append(Finding(
            module="Technical SEO", check="https",
            status="fail", severity="high", confidence="high",
            evidence="; ".join(https.get("evidence", [])),
            impact="HTTPS is a confirmed Google ranking signal; non-HTTPS pages may rank lower",
            fix="Configure 301 redirect HTTP → HTTPS; obtain a valid TLS certificate",
        ))
    else:
        findings.append(Finding(
            module="Technical SEO", check="https",
            status="pass", severity="high", confidence="high",
            evidence="; ".join(https.get("evidence", [])),
            impact="HTTPS correctly enforced",
        ))

    # www / non-www consistency
    www = audit.get("www_redirect", {})
    if www.get("redirect_type") == "inconsistent":
        findings.append(Finding(
            module="Technical SEO", check="www_redirect",
            status="warning", severity="medium", confidence="high",
            evidence="; ".join(www.get("evidence", [])),
            impact="Inconsistent www/non-www may split PageRank across two versions",
            fix="Pick one canonical version and redirect the other with a 301",
        ))
    elif www.get("consistent"):
        findings.append(Finding(
            module="Technical SEO", check="www_redirect",
            status="pass", severity="medium", confidence="high",
            evidence="; ".join(www.get("evidence", [])),
            impact="www/non-www consistently redirected",
        ))

    # robots.txt
    robots = audit.get("robots", {})
    if not robots.get("exists"):
        findings.append(Finding(
            module="Technical SEO", check="robots_txt",
            status="warning", severity="medium", confidence="high",
            evidence="robots.txt not found",
            impact="Without robots.txt, crawlers use default behavior; sitemap location cannot be declared",
            fix="Create /robots.txt and reference your sitemap URL",
        ))
    elif robots.get("blocks_critical_paths"):
        findings.append(Finding(
            module="Technical SEO", check="robots_txt",
            status="fail", severity="high", confidence="high",
            evidence=f"Disallow rules may block important content: {robots.get('disallow_rules', [])}",
            impact="Critical pages may not be indexed",
            fix="Review Disallow rules and remove or narrow any that block key content",
        ))
    else:
        findings.append(Finding(
            module="Technical SEO", check="robots_txt",
            status="pass", severity="medium", confidence="high",
            evidence=f"robots.txt present with {len(robots.get('disallow_rules', []))} Disallow rules",
            impact="robots.txt correctly configured",
        ))

    # 404 page
    page_404 = audit.get("page_404", {})
    if not page_404.get("returns_proper_404"):
        code = page_404.get("actual_status_code", "unknown")
        findings.append(Finding(
            module="Technical SEO", check="404_page",
            status="fail", severity="medium", confidence="high",
            evidence=f"Non-existent URL returned HTTP {code} instead of 404",
            impact="Soft 404s waste crawl budget and confuse search engines",
            fix="Configure server to return HTTP 404 status for non-existent pages",
        ))
    else:
        custom = page_404.get("has_custom_404_page")
        findings.append(Finding(
            module="Technical SEO", check="404_page",
            status="pass", severity="medium", confidence="high",
            evidence=f"404 page returns HTTP 404; custom page: {'yes' if custom else 'no'}",
            impact="Correct 404 handling prevents crawl budget waste",
        ))

    # URL depth
    url_info = audit.get("url_info", {})
    depth = url_info.get("depth", 0)
    if depth > 4:
        findings.append(Finding(
            module="Technical SEO", check="url_depth",
            status="warning", severity="low", confidence="medium",
            evidence=f"Sample URL depth: {depth} level(s)",
            impact="Deeply nested URLs may reduce crawl efficiency; not a confirmed ranking penalty",
            fix="Consider flattening URL structure for key content pages",
        ))

    # URL parameters
    if not url_info.get("is_static") and url_info.get("query_string"):
        findings.append(Finding(
            module="Technical SEO", check="url_parameters",
            status="warning", severity="low", confidence="medium",
            evidence=f"Query string present: ?{url_info['query_string']}",
            impact="Parameter URLs need canonical or noindex strategy to avoid duplicate indexing",
            fix="Add canonical tags or configure URL parameter handling in Google Search Console",
        ))

    # Canonical tag
    canonical = audit.get("canonical", {})
    if not canonical.get("present"):
        findings.append(Finding(
            module="Technical SEO", check="canonical",
            status="warning", severity="medium", confidence="medium",
            evidence="No canonical tag found on this page",
            impact="Without canonical, Google may index duplicate or near-duplicate versions",
            fix="Add <link rel='canonical'> to indexable pages; verify context for pagination/param pages",
        ))
    else:
        findings.append(Finding(
            module="Technical SEO", check="canonical",
            status="pass", severity="medium", confidence="high",
            evidence=canonical.get("evidence", "canonical present"),
            impact="Canonical tag present; helps consolidate link signals",
        ))

    # Structured data — confidence is medium when not found because JS-injected schema is invisible
    schema = audit.get("schema", {})
    if not schema.get("present"):
        findings.append(Finding(
            module="Technical SEO", check="structured_data",
            status="warning", severity="medium", confidence="medium",
            evidence=schema.get("evidence", "No JSON-LD structured data found in static HTML"),
            impact="Missing structured data reduces eligibility for rich results in Google SERP",
            fix="Add Schema.org markup (Organization, BreadcrumbList, Article). Verify JS-injected schema with Google Rich Results Test.",
        ))
    else:
        eligible = schema.get("eligible_for_rich_results", [])
        findings.append(Finding(
            module="Technical SEO", check="structured_data",
            status="pass", severity="medium", confidence="high",
            evidence=schema.get("evidence", ""),
            impact=f"Eligible for rich results: {eligible}" if eligible else "Structured data present",
        ))

    # Hreflang validation (only when tags are present)
    hreflang = audit.get("hreflang", {})
    if hreflang.get("present"):
        issues = hreflang.get("issues", [])

        if "missing_self_reference" in issues:
            findings.append(Finding(
                module="Technical SEO", check="hreflang_self_reference",
                status="fail", severity="high", confidence="high",
                evidence=f"Page URL not found in its own hreflang set ({hreflang.get('count')} tags present)",
                impact="Google ignores the entire hreflang cluster when self-referencing entry is missing",
                fix="Add a <link rel='alternate' hreflang='xx' href='{this-page-url}'> entry for the current page's own locale",
            ))

        if "missing_x_default" in issues:
            findings.append(Finding(
                module="Technical SEO", check="hreflang_x_default",
                status="warning", severity="medium", confidence="high",
                evidence=f"{hreflang.get('count')} hreflang tags present but no x-default fallback declared",
                impact="Without x-default, Google has no fallback for users whose locale isn't explicitly targeted",
                fix="Add <link rel='alternate' hreflang='x-default' href='{fallback-url}'> (typically points to the default-language homepage or a language-selector page)",
            ))

        if "invalid_lang_codes" in issues:
            bad = hreflang.get("invalid_codes", [])
            bad_str = "; ".join(f"{b['code']} → {b['suggestion']}" for b in bad)
            findings.append(Finding(
                module="Technical SEO", check="hreflang_lang_codes",
                status="fail", severity="high", confidence="high",
                evidence=f"Invalid hreflang codes detected: {bad_str}",
                impact="Invalid lang codes cause Google to silently drop the hreflang pair",
                fix="Use BCP-47 format: ISO 639-1 language + optional ISO 3166-1 region (e.g. en-GB not en-UK)",
            ))

        if "relative_hrefs" in issues:
            findings.append(Finding(
                module="Technical SEO", check="hreflang_absolute_urls",
                status="fail", severity="high", confidence="high",
                evidence=f"Relative URLs in hreflang: {hreflang.get('relative_hrefs', [])[:3]}",
                impact="Hreflang href values must be absolute URLs; relative URLs are ignored",
                fix="Replace all hreflang href values with full absolute URLs including protocol and domain",
            ))

        if not issues:
            findings.append(Finding(
                module="Technical SEO", check="hreflang",
                status="pass", severity="medium", confidence="high",
                evidence=hreflang.get("evidence", ""),
                impact="Hreflang configuration looks well-formed on this page",
            ))

        # Canonical-hreflang consistency (single-page check only)
        canonical = audit.get("canonical", {})
        if canonical.get("present") and hreflang.get("entries"):
            canon_href = (canonical.get("href") or "").rstrip("/")
            hreflang_hrefs = {e["href"].rstrip("/") for e in hreflang.get("entries", [])}
            if canon_href and hreflang_hrefs and canon_href not in hreflang_hrefs:
                findings.append(Finding(
                    module="Technical SEO", check="hreflang_canonical_mismatch",
                    status="fail", severity="high", confidence="medium",
                    evidence=f"Canonical URL ({canon_href}) not found in hreflang set",
                    impact="When canonical is absent from the hreflang set, Google silently drops the entire cluster",
                    fix="Ensure the canonical URL appears as one of the hreflang href values, or align canonical and hreflang to the same URL variant",
                ))

    return findings


def build_content_findings(audit: Dict) -> List[Finding]:
    findings = []

    tkd = audit.get("tkd", {})

    # Title
    title = tkd.get("title", {})
    if not title.get("present"):
        findings.append(Finding(
            module="Content", check="title_present",
            status="fail", severity="high", confidence="high",
            evidence="<title> tag absent",
            impact="Title is a primary on-page ranking signal and SERP display element",
            fix="Add a unique, descriptive <title> tag to every page",
        ))
    elif title.get("display_risk") == "truncation_likely":
        findings.append(Finding(
            module="Content", check="title_length",
            status="warning", severity="low", confidence="medium",
            evidence=title.get("evidence", ""),
            impact="Title may be truncated in Google SERP (display guideline: 50-60 chars)",
            fix="Trim title to ~55 chars to reduce truncation risk",
        ))
    elif title.get("display_risk") == "too_short":
        findings.append(Finding(
            module="Content", check="title_length",
            status="warning", severity="low", confidence="medium",
            evidence=title.get("evidence", ""),
            impact="Very short titles provide less keyword context",
            fix="Expand title to clearly describe the page topic",
        ))
    else:
        findings.append(Finding(
            module="Content", check="title_present",
            status="pass", severity="high", confidence="high",
            evidence=title.get("evidence", ""),
            impact="Title present and within display guidelines",
        ))

    # Meta description
    desc = tkd.get("meta_description", {})
    if not desc.get("present"):
        findings.append(Finding(
            module="Content", check="meta_description",
            status="warning", severity="medium", confidence="high",
            evidence="Meta description absent",
            impact="Google may auto-generate a snippet; a crafted description improves CTR",
            fix="Add a unique meta description (150-160 chars) summarising the page value",
        ))
    elif desc.get("display_risk") == "truncation_likely":
        findings.append(Finding(
            module="Content", check="meta_description_length",
            status="warning", severity="low", confidence="medium",
            evidence=desc.get("evidence", ""),
            impact="Description may be truncated in SERP (display guideline: 150-160 chars)",
            fix="Trim meta description to ~155 chars",
        ))
    else:
        findings.append(Finding(
            module="Content", check="meta_description",
            status="pass", severity="medium", confidence="high",
            evidence=desc.get("evidence", ""),
            impact="Meta description present",
        ))

    # Headings
    headings = audit.get("headings", {})
    if headings.get("no_h1"):
        findings.append(Finding(
            module="Content", check="h1_present",
            status="fail", severity="high", confidence="high",
            evidence="No H1 tag found",
            impact="H1 is a primary on-page signal for page topic",
            fix="Add one descriptive H1 tag per page",
        ))
    elif headings.get("multiple_h1_risk"):
        findings.append(Finding(
            module="Content", check="h1_unique",
            status="warning", severity="low", confidence="medium",
            evidence=f"{headings.get('h1_count')} H1 tags found: {headings.get('h1_texts', [])[:3]}",
            impact="Multiple H1 is a structural signal worth reviewing; not a confirmed ranking penalty",
            fix="Review if multiple H1 tags reflect intentional document structure",
        ))

    if headings.get("level_skips"):
        findings.append(Finding(
            module="Content", check="heading_hierarchy",
            status="warning", severity="low", confidence="medium",
            evidence=f"Heading level skips detected: {headings.get('level_skips')}",
            impact="Irregular heading hierarchy may reduce content clarity for crawlers and screen readers",
            fix="Use sequential heading levels (H1→H2→H3) without skipping",
        ))

    # Images
    images = audit.get("images", {})
    missing_alt = images.get("missing_alt_count", 0)
    if missing_alt > 0:
        findings.append(Finding(
            module="Content", check="image_alt_attributes",
            status="warning" if missing_alt < 5 else "fail",
            severity="medium", confidence="high",
            evidence=images.get("evidence", ""),
            impact=f"{missing_alt} images without alt text; impacts image search visibility and accessibility",
            fix="Add descriptive alt attributes to all informational images",
        ))

    if images.get("modern_format_pct", 0) < 50 and images.get("total", 0) > 3:
        findings.append(Finding(
            module="Content", check="image_formats",
            status="warning", severity="low", confidence="high",
            evidence=images.get("evidence", ""),
            impact="Legacy image formats (JPEG/PNG) increase page weight and slow LCP",
            fix="Convert images to WebP or AVIF; use <picture> for browser compatibility",
        ))

    # E-E-A-T
    eeat = audit.get("eeat", {})
    missing_eeat = eeat.get("missing_signals", [])
    if len(missing_eeat) >= 3:
        findings.append(Finding(
            module="Content", check="eeat_signals",
            status="warning", severity="medium", confidence="medium",
            evidence=eeat.get("evidence", ""),
            impact="Weak E-E-A-T signals may affect trust assessment, especially for YMYL content",
            fix=f"Address missing signals: {missing_eeat}",
            detail=eeat,
        ))

    return findings


def build_link_findings(audit: Dict) -> List[Finding]:
    findings = []

    links = audit.get("links", {})
    breadcrumbs = audit.get("breadcrumbs", {})

    if links.get("internal_count", 0) < 5:
        findings.append(Finding(
            module="Internal Links", check="internal_link_count",
            status="warning", severity="medium", confidence="medium",
            evidence=links.get("evidence", ""),
            impact="Too few internal links limits PageRank distribution across the site",
            fix="Link to related pages using descriptive anchor text",
        ))

    if links.get("weak_anchor_count", 0) > 3:
        findings.append(Finding(
            module="Internal Links", check="anchor_text_quality",
            status="warning", severity="low", confidence="high",
            evidence=f"{links.get('weak_anchor_count')} weak anchor text instances found",
            impact="Generic anchors ('click here', 'read more') provide no keyword context to crawlers",
            fix="Replace generic anchors with descriptive, keyword-relevant text",
        ))

    if not breadcrumbs.get("html_breadcrumb"):
        findings.append(Finding(
            module="Internal Links", check="breadcrumbs",
            status="warning", severity="low", confidence="medium",
            evidence="No breadcrumb navigation detected",
            impact="Breadcrumbs improve site structure clarity and enable breadcrumb rich results",
            fix="Add breadcrumb navigation with BreadcrumbList Schema markup",
        ))
    elif breadcrumbs.get("html_breadcrumb") and not breadcrumbs.get("schema_breadcrumb"):
        findings.append(Finding(
            module="Internal Links", check="breadcrumb_schema",
            status="warning", severity="low", confidence="high",
            evidence=breadcrumbs.get("evidence", ""),
            impact="HTML breadcrumb exists but lacks BreadcrumbList schema for rich results",
            fix="Add JSON-LD BreadcrumbList markup to enable breadcrumb display in SERP",
        ))
    else:
        findings.append(Finding(
            module="Internal Links", check="breadcrumbs",
            status="pass", severity="low", confidence="high",
            evidence=breadcrumbs.get("evidence", ""),
            impact="Breadcrumb navigation with schema markup present",
        ))

    return findings


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def build_ai_seo_findings(audit: Dict) -> List[Finding]:
    """Lightweight AI search readiness checks (AEO, GEO, AI Overviews)."""
    findings = []
    ai_seo = audit.get("ai_seo", {})
    if not ai_seo:
        return findings

    # FAQ / HowTo schema — structured answers AI can extract
    if not ai_seo.get("has_faq_schema"):
        findings.append(Finding(
            module="AI SEO", check="faq_schema",
            status="warning", severity="low", confidence="medium",
            evidence="No FAQPage or HowTo schema found in static HTML",
            impact="FAQ and HowTo schema improve eligibility for AI Overviews, featured snippets, and voice answers",
            fix="Add FAQPage JSON-LD for Q&A content; HowTo schema for step-by-step guides",
        ))
    else:
        findings.append(Finding(
            module="AI SEO", check="faq_schema",
            status="pass", severity="low", confidence="medium",
            evidence="FAQPage or HowTo schema present",
            impact="Eligible for structured answer extraction by AI search engines",
        ))

    # Entity schema — helps AI build knowledge graph
    if not ai_seo.get("has_entity_schema"):
        findings.append(Finding(
            module="AI SEO", check="entity_clarity",
            status="warning", severity="low", confidence="medium",
            evidence="No Organization or Person entity schema found",
            impact="AI systems use entity graphs for brand recognition; missing entity markup reduces association accuracy",
            fix="Add Organization schema with name, url, description, and sameAs (social profiles)",
        ))
    else:
        findings.append(Finding(
            module="AI SEO", check="entity_clarity",
            status="pass", severity="low", confidence="medium",
            evidence="Organization or Person entity schema present",
            impact="Entity markup supports AI knowledge graph association",
        ))

    # llms.txt — AI bot access declaration
    llms_txt = audit.get("llms_txt", {})
    if not llms_txt.get("exists"):
        findings.append(Finding(
            module="AI SEO", check="llms_txt",
            status="warning", severity="low", confidence="high",
            evidence=f"llms.txt not found at {llms_txt.get('checked_url', 'domain root')}",
            impact="llms.txt declares to AI crawlers (GPTBot, ClaudeBot) which content may be used; absence means no explicit AI access policy",
            fix="Create /llms.txt following the llmstxt.org spec; at minimum list key pages and their purpose",
        ))
    else:
        findings.append(Finding(
            module="AI SEO", check="llms_txt",
            status="pass", severity="low", confidence="high",
            evidence=f"llms.txt found at {llms_txt.get('checked_url')}",
            impact="AI access policy declared",
        ))

    return findings


def assemble_findings(audit_data: Dict) -> Dict[str, List[Finding]]:
    """Build all findings grouped by module."""
    module_findings: Dict[str, List[Finding]] = {}

    tech = build_technical_findings(audit_data)
    module_findings["Technical SEO"] = tech

    content = build_content_findings(audit_data)
    module_findings["Content"] = content

    link_f = build_link_findings(audit_data)
    module_findings["Internal Links"] = link_f

    # CWV findings are pre-built by pagespeed.py
    cwv = audit_data.get("cwv_findings", [])
    if cwv:
        module_findings["Core Web Vitals"] = [
            Finding(**{k: v for k, v in f.items() if k in Finding.__dataclass_fields__})
            for f in cwv
        ]

    # AI SEO readiness
    ai_seo_f = build_ai_seo_findings(audit_data)
    if ai_seo_f:
        module_findings["AI SEO"] = ai_seo_f

    return module_findings


def _render_finding_en(f: Finding, idx: int) -> str:
    emoji = SEVERITY_EMOJI.get(f.severity, "")
    lines = [
        f"**{idx}. [{f.module}] {f.check.replace('_', ' ').title()}** {emoji}",
        f"- **Status**: {STATUS_EMOJI.get(f.status, '')} {f.status.upper()}",
        f"- **Severity / Confidence**: {f.severity} / {f.confidence}",
        f"- **Evidence**: {f.evidence}",
        f"- **Impact**: {f.impact}",
    ]
    if f.fix:
        lines.append(f"- **Fix**: {f.fix}")
    return "\n".join(lines)


def _render_finding_zh(f: Finding, idx: int) -> str:
    status_zh = {"pass": "通过", "warning": "警告", "fail": "失败", "unknown": "未知"}
    sev_zh = {"high": "高", "medium": "中", "low": "低"}
    conf_zh = {"high": "高", "medium": "中", "low": "低"}
    emoji = SEVERITY_EMOJI.get(f.severity, "")
    lines = [
        f"**{idx}. [{f.module}] {f.check}** {emoji}",
        f"- **状态**: {STATUS_EMOJI.get(f.status, '')} {status_zh.get(f.status, f.status)}",
        f"- **严重度 / 可信度**: {sev_zh.get(f.severity, f.severity)} / {conf_zh.get(f.confidence, f.confidence)}",
        f"- **证据**: {f.evidence}",
        f"- **影响**: {f.impact}",
    ]
    if f.fix:
        lines.append(f"- **修复建议**: {f.fix}")
    return "\n".join(lines)


def generate_report(audit_data: Dict, language: str = "en") -> str:
    """Generate a full markdown SEO audit report."""
    url = audit_data.get("url", "")
    date = audit_data.get("date", "")
    lang_detected = audit_data.get("detected_language", "en")
    site_type_info = audit_data.get("site_type", {})
    site_type_str = site_type_info.get("type", "general")
    site_type_conf = site_type_info.get("confidence", "low")

    all_module_findings = assemble_findings(audit_data)

    # Module scores
    scores = {
        mod: _score_from_findings(findings)
        for mod, findings in all_module_findings.items()
    }

    # Priority list: actionable findings only (excludes pass and data_needed)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    status_order = {"fail": 0, "warning": 1, "unknown": 2, "pass": 3}
    priority_findings = [
        f for findings in all_module_findings.values()
        for f in findings
        if f.status in ("fail", "warning", "unknown")
    ]
    priority_findings.sort(key=lambda f: (severity_order.get(f.severity, 9), status_order.get(f.status, 9)))

    # Data-needed findings: missing data, not site problems — shown in their own section
    data_needed_findings = [
        f for findings in all_module_findings.values()
        for f in findings
        if f.status == "data_needed"
    ]

    render_fn = _render_finding_zh if language == "zh" else _render_finding_en

    if language == "zh":
        return _build_report_zh(url, date, lang_detected, scores, all_module_findings, priority_findings, data_needed_findings, render_fn, site_type_str, site_type_conf)
    return _build_report_en(url, date, lang_detected, scores, all_module_findings, priority_findings, data_needed_findings, render_fn, site_type_str, site_type_conf)


def _build_report_en(url, date, lang_detected, scores, module_findings, priority_findings, data_needed_findings, render_fn, site_type="general", site_type_conf="low") -> str:
    status_label = {mod: _status_label(s) for mod, s in scores.items()}
    summary_rows = "\n".join(
        f"| {mod} | {STATUS_EMOJI.get(status_label[mod], '')} | {'N/A (no data)' if scores[mod] is None else f'{scores[mod]}/100'} |"
        for mod in scores
    )

    priority_sections = {"🔴 High Severity": [], "🟡 Medium Severity": [], "🟢 Low Severity / Suggestions": []}
    for i, f in enumerate(priority_findings, 1):
        rendered = render_fn(f, i)
        if f.severity == "high":
            priority_sections["🔴 High Severity"].append(rendered)
        elif f.severity == "medium":
            priority_sections["🟡 Medium Severity"].append(rendered)
        else:
            priority_sections["🟢 Low Severity / Suggestions"].append(rendered)

    priority_md = ""
    for section, items in priority_sections.items():
        if items:
            priority_md += f"\n### {section}\n\n" + "\n\n---\n\n".join(items) + "\n"

    if data_needed_findings:
        priority_md += "\n### 📊 Data Needed\n\n"
        priority_md += "_These checks could not run because data was unavailable. They are not site errors._\n\n"
        for i, f in enumerate(data_needed_findings, 1):
            priority_md += f"**{i}. [{f.module}] {f.check}**\n- {f.evidence}\n- **How to fix**: {f.fix}\n\n"

    detail_md = ""
    for mod, findings in module_findings.items():
        detail_md += f"\n### {mod}\n\n"
        for f in findings:
            detail_md += f"{STATUS_EMOJI.get(f.status, '')} **{f.check}** — {f.evidence}\n\n"

    return f"""# Google SEO Audit Report

**Target**: {url}
**Date**: {date}
**Detected Language**: {lang_detected}
**Detected Site Type**: {site_type} (confidence: {site_type_conf})

---

## Summary

| Module | Status | Score |
|--------|--------|-------|
{summary_rows}

---

## Priority Fix List

{priority_md}

---

## Detailed Module Reports

{detail_md}

---

*Generated by [google-seo-audit](https://github.com/jiguang9/google-seo-audit)*
*Note: site: operator gives a rough estimate; not a precise index count.*
*Domain age is a historical trust indicator, not a direct ranking factor.*
"""


def _build_report_zh(url, date, lang_detected, scores, module_findings, priority_findings, data_needed_findings, render_fn, site_type="general", site_type_conf="low") -> str:
    status_label = {mod: _status_label(s) for mod, s in scores.items()}
    summary_rows = "\n".join(
        f"| {mod} | {STATUS_EMOJI.get(status_label[mod], '')} | {'N/A（无数据）' if scores[mod] is None else f'{scores[mod]}/100'} |"
        for mod in scores
    )

    priority_sections = {"🔴 高优先级（立即修复）": [], "🟡 中优先级（本月内处理）": [], "🟢 低优先级（持续改进）": []}
    for i, f in enumerate(priority_findings, 1):
        rendered = render_fn(f, i)
        if f.severity == "high":
            priority_sections["🔴 高优先级（立即修复）"].append(rendered)
        elif f.severity == "medium":
            priority_sections["🟡 中优先级（本月内处理）"].append(rendered)
        else:
            priority_sections["🟢 低优先级（持续改进）"].append(rendered)

    priority_md = ""
    for section, items in priority_sections.items():
        if items:
            priority_md += f"\n### {section}\n\n" + "\n\n---\n\n".join(items) + "\n"

    if data_needed_findings:
        priority_md += "\n### 📊 数据待补充\n\n"
        priority_md += "_以下检测项因数据缺失未能运行，不代表网站存在问题。_\n\n"
        for i, f in enumerate(data_needed_findings, 1):
            priority_md += f"**{i}. [{f.module}] {f.check}**\n- {f.evidence}\n- **解决方式**: {f.fix}\n\n"

    detail_md = ""
    for mod, findings in module_findings.items():
        detail_md += f"\n### {mod}\n\n"
        for f in findings:
            detail_md += f"{STATUS_EMOJI.get(f.status, '')} **{f.check}** — {f.evidence}\n\n"

    return f"""# Google SEO 诊断报告

**目标网站**: {url}
**诊断日期**: {date}
**检测语言**: {lang_detected}
**推断站点类型**: {site_type}（置信度：{site_type_conf}）

---

## 总览

| 模块 | 状态 | 得分 |
|------|------|------|
{summary_rows}

---

## 优先修复清单

{priority_md}

---

## 各模块详细诊断

{detail_md}

---

*由 [google-seo-audit](https://github.com/jiguang9/google-seo-audit) 生成*
*注：site: 指令仅为估算，非精确收录量；域名年龄为历史信任参考，非直接排名因子。*
"""
