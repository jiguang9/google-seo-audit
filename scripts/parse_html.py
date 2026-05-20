"""HTML analysis: TKD, headings, canonical, hreflang, schema, images, links, E-E-A-T."""

import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4 lxml")


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_language(html: str, url: str = "") -> Dict:
    """Detect content language from HTML lang attribute and meta tags."""
    soup = BeautifulSoup(html, "lxml")
    sources = {}

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        sources["html_lang_attr"] = html_tag["lang"].strip()

    og_locale = soup.find("meta", property="og:locale")
    if og_locale and og_locale.get("content"):
        sources["og_locale"] = og_locale["content"]

    meta_lang = soup.find("meta", attrs={"http-equiv": re.compile("content-language", re.I)})
    if meta_lang and meta_lang.get("content"):
        sources["meta_content_language"] = meta_lang["content"]

    detected = (
        sources.get("html_lang_attr")
        or sources.get("og_locale")
        or sources.get("meta_content_language")
        or "en"
    )

    # Split by both '-' and '_' to handle zh-CN, zh_CN, zh_Hans, etc.
    lang_code = re.split(r"[-_]", detected)[0].lower()

    # Map country-code-as-language mistakes common on Chinese sites:
    # <html lang="cn"> or <html lang="tw"> or <html lang="hk">
    _COUNTRY_TO_LANG = {"cn": "zh", "tw": "zh", "hk": "zh"}
    lang_code = _COUNTRY_TO_LANG.get(lang_code, lang_code)

    is_cjk = lang_code in ("zh", "ja", "ko")

    return {
        "detected": detected,
        "lang_code": lang_code,
        "is_cjk": is_cjk,
        "sources": sources,
        "report_language": "zh" if lang_code == "zh" else "en",
    }


# ---------------------------------------------------------------------------
# TKD (Title, Keywords, Description)
# ---------------------------------------------------------------------------

def parse_tkd(html: str) -> Dict:
    """Extract and evaluate title, meta description, meta keywords."""
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else None
    title_len = len(title_text) if title_text else 0

    meta_desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta_desc = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else None
    desc_len = len(meta_desc) if meta_desc else 0

    meta_kw_tag = soup.find("meta", attrs={"name": re.compile("^keywords$", re.I)})
    meta_kw = meta_kw_tag["content"].strip() if meta_kw_tag and meta_kw_tag.get("content") else None

    return {
        "title": {
            "text": title_text,
            "length": title_len,
            "present": bool(title_text),
            # 50-60 chars is a display guideline, not a ranking factor
            "display_risk": "truncation_likely" if title_len > 60 else ("too_short" if title_len < 20 else "ok"),
            "evidence": f"Title: \"{title_text}\" ({title_len} chars)",
        },
        "meta_description": {
            "text": meta_desc,
            "length": desc_len,
            "present": bool(meta_desc),
            "display_risk": "truncation_likely" if desc_len > 160 else ("too_short" if 0 < desc_len < 70 else ("missing" if desc_len == 0 else "ok")),
            "evidence": f"Meta description: {desc_len} chars" if meta_desc else "Meta description: absent",
        },
        "meta_keywords": {
            "text": meta_kw,
            "present": bool(meta_kw),
            "note": "Google ignores meta keywords; no SEO value, no maintenance needed.",
            "evidence": "Meta keywords tag present (no Google SEO impact)" if meta_kw else "Meta keywords tag absent (expected)",
        },
    }


# ---------------------------------------------------------------------------
# Heading structure
# ---------------------------------------------------------------------------

def parse_headings(html: str) -> Dict:
    """Extract H1–H6 hierarchy and check for structural issues."""
    soup = BeautifulSoup(html, "lxml")
    headings: List[Dict] = []

    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            headings.append({"level": level, "text": tag.get_text(strip=True)})

    h1_tags = [h for h in headings if h["level"] == 1]
    h1_with_text = [h for h in h1_tags if h["text"]]
    h1_empty = len(h1_tags) - len(h1_with_text)
    levels_present = sorted({h["level"] for h in headings})

    # Detect level skips (e.g. H1 → H3 with no H2)
    skips = []
    for i in range(len(levels_present) - 1):
        if levels_present[i + 1] - levels_present[i] > 1:
            skips.append(f"H{levels_present[i]} → H{levels_present[i+1]}")

    # Evidence: distinguish empty H1s from content-bearing ones
    h1_summary = f"{len(h1_tags)} H1 tag(s)"
    if h1_empty:
        h1_summary += f" ({h1_empty} empty/hidden)"
    sample_texts = [h["text"] for h in h1_with_text[:3]]

    return {
        "headings": headings,
        "h1_count": len(h1_tags),
        "h1_with_text_count": len(h1_with_text),
        "h1_empty_count": h1_empty,
        "h1_texts": sample_texts,
        "levels_present": levels_present,
        "level_skips": skips,
        # Multiple H1 is a structural signal, not a confirmed penalty
        "multiple_h1_risk": len(h1_tags) > 1,
        "no_h1": len(h1_tags) == 0,
        "evidence": (
            f"{h1_summary}; "
            f"heading levels present: {levels_present}; "
            f"level skips: {skips or 'none'}"
        ),
    }


# ---------------------------------------------------------------------------
# Canonical & Hreflang
# ---------------------------------------------------------------------------

def parse_canonical(html: str, page_url: str = "") -> Dict:
    """Extract canonical tag and assess its configuration."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("link", rel="canonical")
    canonical_href = tag["href"].strip() if tag and tag.get("href") else None

    is_self_referencing = bool(canonical_href and page_url and canonical_href.rstrip("/") == page_url.rstrip("/"))

    return {
        "present": bool(canonical_href),
        "href": canonical_href,
        "is_self_referencing": is_self_referencing,
        # Context-dependent: pagination/hreflang/param pages require case-by-case judgment
        "note": "Canonical recommended for indexable pages; verify context for pagination, param URLs, hreflang pages.",
        "evidence": f"canonical: {canonical_href}" if canonical_href else "canonical tag: absent",
    }


# Common invalid lang code mistakes (lowercase key → correct value)
_INVALID_LANG_CODES: Dict[str, str] = {
    "en-uk": "en-GB",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hk": "zh-HK",
    "pt-br": "pt-BR",
    "es-mx": "es-MX",
    "fr-fr": "fr-FR",
}


def parse_hreflang(html: str, page_url: str = "") -> Dict:
    """Extract hreflang tags and validate for common configuration errors."""
    soup = BeautifulSoup(html, "lxml")
    tags = soup.find_all("link", rel="alternate", hreflang=True)

    entries = [
        {"hreflang": t.get("hreflang", ""), "href": t.get("href", "")}
        for t in tags
    ]
    has_x_default = any(e["hreflang"] == "x-default" for e in entries)

    # Self-referencing check: page must include itself in its own hreflang set
    page_url_clean = page_url.rstrip("/")
    self_referencing = None
    if page_url_clean and entries:
        self_referencing = any(e["href"].rstrip("/") == page_url_clean for e in entries)

    # Invalid lang code detection (e.g. "en-UK" should be "en-GB")
    invalid_codes = [
        {"code": e["hreflang"], "suggestion": _INVALID_LANG_CODES[e["hreflang"].lower()]}
        for e in entries
        if e["hreflang"].lower() in _INVALID_LANG_CODES
    ]

    # Relative href check (hreflang hrefs must be absolute URLs)
    relative_hrefs = [e["href"] for e in entries if e["href"] and not e["href"].startswith("http")]

    issues = []
    if entries and self_referencing is False:
        issues.append("missing_self_reference")
    if entries and not has_x_default and len(entries) > 1:
        issues.append("missing_x_default")
    if invalid_codes:
        issues.append("invalid_lang_codes")
    if relative_hrefs:
        issues.append("relative_hrefs")

    return {
        "present": bool(entries),
        "count": len(entries),
        "entries": entries,
        "has_x_default": has_x_default,
        "self_referencing": self_referencing,
        "invalid_codes": invalid_codes,
        "relative_hrefs": relative_hrefs,
        "issues": issues,
        "evidence": (
            f"{len(entries)} hreflang tag(s); issues: {issues or 'none'}"
            if entries
            else "No hreflang tags (only relevant for multilingual sites)"
        ),
    }


# ---------------------------------------------------------------------------
# Structured data (Schema.org JSON-LD)
# ---------------------------------------------------------------------------

_SCHEMA_DETECTION_LIMITATION = (
    "Static HTML scan only — CMS plugins (Yoast, RankMath, AIOSEO) often inject "
    "JSON-LD via JavaScript which is not visible here. "
    "Verify with Google Rich Results Test or browser DevTools if result is unexpected."
)


def parse_schema(html: str) -> Dict:
    """Extract JSON-LD structured data blocks and identify types."""
    soup = BeautifulSoup(html, "lxml")
    blocks = soup.find_all("script", type="application/ld+json")

    schemas = []
    parse_errors = []
    for block in blocks:
        try:
            data = json.loads(block.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                schema_type = item.get("@type", "Unknown")
                schemas.append({"type": schema_type, "data": item})
        except (json.JSONDecodeError, AttributeError) as exc:
            parse_errors.append(str(exc))

    types_found = list({s["type"] for s in schemas})
    rich_result_types = {
        "Article", "NewsArticle", "BlogPosting", "Product", "FAQPage",
        "HowTo", "Recipe", "Event", "BreadcrumbList", "Organization",
        "LocalBusiness", "Review", "AggregateRating", "JobPosting",
        "VideoObject", "Course", "SoftwareApplication",
    }
    eligible_for_rich_results = [t for t in types_found if t in rich_result_types]

    return {
        "present": bool(schemas),
        "count": len(schemas),
        "types": types_found,
        "eligible_for_rich_results": eligible_for_rich_results,
        "parse_errors": parse_errors,
        "detection_limitation": _SCHEMA_DETECTION_LIMITATION,
        "evidence": (
            f"{len(schemas)} JSON-LD block(s); types: {types_found}"
            if schemas
            else f"No JSON-LD found in static HTML. {_SCHEMA_DETECTION_LIMITATION}"
        ),
    }


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

def parse_images(html: str, base_url: str = "") -> Dict:
    """Audit image alt attributes and format usage."""
    soup = BeautifulSoup(html, "lxml")
    images = soup.find_all("img")

    total = len(images)
    missing_alt = []
    empty_alt = []
    modern_format_count = 0
    modern_extensions = {".webp", ".avif", ".svg"}

    for img in images:
        src = img.get("src", "")
        alt = img.get("alt")
        if alt is None:
            missing_alt.append(src)
        elif alt.strip() == "":
            empty_alt.append(src)

        ext = "." + src.rsplit(".", 1)[-1].lower() if "." in src else ""
        if ext in modern_extensions:
            modern_format_count += 1

    return {
        "total": total,
        "missing_alt_count": len(missing_alt),
        "missing_alt_samples": missing_alt[:5],
        "empty_alt_count": len(empty_alt),
        "modern_format_count": modern_format_count,
        "modern_format_pct": round(modern_format_count / total * 100, 1) if total else 0,
        "evidence": (
            f"{total} images: {len(missing_alt)} missing alt, "
            f"{len(empty_alt)} empty alt, "
            f"{modern_format_count}/{total} modern format (WebP/AVIF)"
        ),
    }


# ---------------------------------------------------------------------------
# Links (internal / external)
# ---------------------------------------------------------------------------

def parse_links(html: str, base_url: str) -> Dict:
    """Categorize links as internal or external, check anchor text quality."""
    soup = BeautifulSoup(html, "lxml")
    base_netloc = urlparse(base_url).netloc.replace("www.", "")

    internal, external = [], []
    weak_anchor_patterns = re.compile(
        r"^(click here|here|read more|more|learn more|点击这里|了解更多|查看更多|more info|details)$",
        re.I,
    )
    weak_anchors = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, href)
        anchor_text = a.get_text(strip=True)

        parsed = urlparse(full_url)
        link_netloc = parsed.netloc.replace("www.", "")

        entry = {"url": full_url, "anchor": anchor_text}
        if link_netloc == base_netloc or not link_netloc:
            internal.append(entry)
        else:
            external.append(entry)

        if anchor_text and weak_anchor_patterns.match(anchor_text):
            weak_anchors.append({"url": full_url, "anchor": anchor_text})

    # PDF link detection — PDFs without HTML landing pages hurt crawl efficiency
    pdf_links = [
        {"url": full_url, "anchor": anchor_text}
        for a in soup.find_all("a", href=True)
        for full_url, anchor_text in [(urljoin(base_url, a["href"].strip()), a.get_text(strip=True))]
        if full_url.lower().endswith(".pdf") or ".pdf?" in full_url.lower()
    ]

    return {
        "internal_count": len(internal),
        "external_count": len(external),
        "internal_links": internal[:20],
        "external_links": external[:10],
        "weak_anchor_count": len(weak_anchors),
        "weak_anchor_samples": weak_anchors[:5],
        "pdf_link_count": len(pdf_links),
        "pdf_link_samples": pdf_links[:5],
        "evidence": (
            f"{len(internal)} internal links, {len(external)} external links; "
            f"{len(weak_anchors)} weak anchor text; {len(pdf_links)} PDF link(s)"
        ),
    }


# ---------------------------------------------------------------------------
# Viewport & Open Graph
# ---------------------------------------------------------------------------

def parse_viewport(html: str) -> Dict:
    """Check viewport meta tag for mobile rendering."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("meta", attrs={"name": re.compile("viewport", re.I)})
    content = tag["content"].strip() if tag and tag.get("content") else None
    has_width_device = bool(content and "width=device-width" in content)

    return {
        "present": bool(tag),
        "content": content,
        "has_width_device": has_width_device,
        "evidence": f"viewport: {content}" if content else "viewport meta tag: absent",
    }


def parse_og_tags(html: str) -> Dict:
    """Extract Open Graph and Twitter Card tags."""
    soup = BeautifulSoup(html, "lxml")

    og = {}
    for tag in soup.find_all("meta", property=re.compile("^og:", re.I)):
        prop = tag.get("property", "").lower()
        og[prop] = tag.get("content", "")

    twitter = {}
    for tag in soup.find_all("meta", attrs={"name": re.compile("^twitter:", re.I)}):
        name = tag.get("name", "").lower()
        twitter[name] = tag.get("content", "")

    return {
        "og_present": bool(og),
        "og_tags": og,
        "twitter_present": bool(twitter),
        "twitter_tags": twitter,
        "has_og_image": bool(og.get("og:image")),
        "evidence": (
            f"OG tags: {len(og)} found; Twitter Card tags: {len(twitter)} found"
        ),
    }


# ---------------------------------------------------------------------------
# E-E-A-T signals (indirect, medium confidence)
# ---------------------------------------------------------------------------

def check_eeat_signals(html: str, base_url: str) -> Dict:
    """
    Check for surface-level E-E-A-T signals.
    These are indirect indicators; confidence is medium.
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    found_signals = []
    missing_signals = []

    # Author byline
    author_patterns = ["author", "written by", "by ", "撰文", "作者"]
    has_author = any(p in text for p in author_patterns)
    (found_signals if has_author else missing_signals).append("author_byline")

    # Publication date
    date_tags = soup.find_all(["time", "meta"], attrs={
        "datetime": True,
        "itemprop": re.compile("datePublished|dateModified", re.I),
    })
    pub_meta = soup.find("meta", attrs={"name": re.compile("publish.*date|article.*date", re.I)})
    has_date = bool(date_tags or pub_meta or re.search(r"\d{4}-\d{2}-\d{2}", text[:2000]))
    (found_signals if has_date else missing_signals).append("publication_date")

    # About / Contact pages (internal link check)
    links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    has_about = any("about" in l.lower() or "关于" in l for l in links)
    has_contact = any("contact" in l.lower() or "联系" in l for l in links)
    (found_signals if has_about else missing_signals).append("about_page_link")
    (found_signals if has_contact else missing_signals).append("contact_page_link")

    # Privacy policy
    has_privacy = any("privacy" in l.lower() or "隐私" in l for l in links)
    (found_signals if has_privacy else missing_signals).append("privacy_policy_link")

    return {
        "found_signals": found_signals,
        "missing_signals": missing_signals,
        "score": f"{len(found_signals)}/{len(found_signals) + len(missing_signals)}",
        "confidence": "medium",
        "note": "E-E-A-T signals are indirect; this is a surface-level scan only.",
        "evidence": f"E-E-A-T signals detected: {found_signals}; absent: {missing_signals}",
    }


# ---------------------------------------------------------------------------
# Breadcrumbs
# ---------------------------------------------------------------------------

def parse_breadcrumbs(html: str) -> Dict:
    """Detect breadcrumb navigation and BreadcrumbList schema."""
    soup = BeautifulSoup(html, "lxml")

    # BreadcrumbList in JSON-LD
    schema_breadcrumb = False
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            if any(i.get("@type") == "BreadcrumbList" for i in items):
                schema_breadcrumb = True
                break
        except (json.JSONDecodeError, AttributeError):
            pass

    # HTML breadcrumb via aria-label or common class names
    html_breadcrumb = bool(
        soup.find(attrs={"aria-label": re.compile("breadcrumb", re.I)})
        or soup.find(class_=re.compile("breadcrumb", re.I))
        or soup.find(id=re.compile("breadcrumb", re.I))
    )

    return {
        "html_breadcrumb": html_breadcrumb,
        "schema_breadcrumb": schema_breadcrumb,
        "evidence": (
            f"Breadcrumb: HTML={'yes' if html_breadcrumb else 'no'}, "
            f"BreadcrumbList schema={'yes' if schema_breadcrumb else 'no'}"
        ),
    }


# ---------------------------------------------------------------------------
# Keyword density (informational, no target threshold enforced)
# ---------------------------------------------------------------------------

def detect_site_type(html: str, url: str, schema_types: List[str] = None) -> Dict:
    """Infer site type from HTML signals, URL patterns, and schema types."""
    soup = BeautifulSoup(html, "lxml")
    text_lower = soup.get_text(" ", strip=True).lower()
    url_lower = url.lower()
    schema_types = schema_types or []

    signals: Dict[str, List[str]] = {
        "ecommerce": [],
        "local": [],
        "blog": [],
        "saas": [],
        "multilingual": [],
    }

    # Ecommerce
    if any(t in schema_types for t in ("Product", "Offer", "ItemList")):
        signals["ecommerce"].append("Product/Offer schema")
    if any(p in url_lower for p in ("/shop", "/store", "/products", "/cart", "/checkout")):
        signals["ecommerce"].append("ecommerce URL pattern")
    if any(p in text_lower for p in ("add to cart", "buy now", "加入购物车", "立即购买", "checkout")):
        signals["ecommerce"].append("ecommerce UI text")

    # Local business
    if any(t in schema_types for t in ("LocalBusiness", "Restaurant", "Hotel", "Store")):
        signals["local"].append("LocalBusiness schema")
    if re.search(r'\b(opening hours?|business hours?|directions|get directions)\b', text_lower):
        signals["local"].append("local business text")

    # Blog / content
    if any(t in schema_types for t in ("Article", "BlogPosting", "NewsArticle")):
        signals["blog"].append("Article/Blog schema")
    if any(p in url_lower for p in ("/blog", "/article", "/post", "/news")):
        signals["blog"].append("blog URL pattern")

    # SaaS / software
    if "SoftwareApplication" in schema_types:
        signals["saas"].append("SoftwareApplication schema")
    if any(p in text_lower for p in ("free trial", "per month", "per user", "/月", "免费试用", "sign up free")):
        signals["saas"].append("SaaS pricing text")
    if any(p in url_lower for p in ("/pricing", "/signup", "/register", "/dashboard", "/app/")):
        signals["saas"].append("SaaS URL pattern")

    # Multilingual: detected by hreflang count — left to caller with hreflang data
    # (annotated externally in audit_url.py)

    scored = sorted(signals.items(), key=lambda x: len(x[1]), reverse=True)
    best_type, best_signals = scored[0]

    if not best_signals:
        return {
            "type": "general",
            "signals": [],
            "confidence": "low",
            "evidence": "No strong site type signals detected; treating as general site",
        }

    return {
        "type": best_type,
        "signals": best_signals,
        "all_signals": {k: v for k, v in signals.items() if v},
        "confidence": "medium" if len(best_signals) >= 2 else "low",
        "evidence": f"Inferred site type: {best_type} ({'; '.join(best_signals)})",
    }


def check_ai_seo_readiness(html: str, url: str) -> Dict:
    """
    Check signals relevant for AI search visibility: AEO, GEO, AI Overviews.
    Looks for FAQ/HowTo schema, entity markup, author attribution, Q&A content.
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    ld_blocks = [s.string or "" for s in soup.find_all("script", type="application/ld+json")]
    ld_combined = " ".join(ld_blocks)

    present: List[str] = []
    missing: List[str] = []

    # FAQ or HowTo schema → structured answers AI can extract
    has_faq = '"FAQPage"' in ld_combined or '"HowTo"' in ld_combined
    (present if has_faq else missing).append("faq_or_howto_schema")

    # Organization or Person entity → helps AI build knowledge graph
    has_entity = '"Organization"' in ld_combined or '"Person"' in ld_combined
    (present if has_entity else missing).append("entity_schema")

    # Author attribution (schema, itemprop, or class-based)
    has_author = bool(
        soup.find(attrs={"itemprop": re.compile("author", re.I)})
        or soup.find(class_=re.compile(r"\bauthor\b", re.I))
        or re.search(r'\b(by |written by |author:)\s*\w', text.lower())
    )
    (present if has_author else missing).append("author_attribution")

    # Answer-structured Q&A content patterns
    has_qa = bool(re.search(
        r'\b(what is|how to|why does|how does|what are|什么是|如何|为什么|怎么)\b.{10,200}\?',
        text, re.I
    ))
    (present if has_qa else missing).append("answer_structured_content")

    parsed = urlparse(url)
    llms_txt_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"

    return {
        "present": present,
        "missing": missing,
        "has_faq_schema": has_faq,
        "has_entity_schema": has_entity,
        "has_author": has_author,
        "has_qa_content": has_qa,
        "llms_txt_url": llms_txt_url,
        "evidence": f"AI SEO signals present: {present}; missing: {missing}",
        "confidence": "medium",
    }


def estimate_keyword_density(html: str, keyword: str) -> Dict:
    """Estimate how often a keyword appears relative to total word count."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True).lower()
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    kw_lower = keyword.lower()
    occurrences = len(re.findall(re.escape(kw_lower), text))
    density = round(occurrences / word_count * 100, 2) if word_count else 0

    return {
        "keyword": keyword,
        "occurrences": occurrences,
        "word_count": word_count,
        "density_pct": density,
        "stuffing_risk": density > 5,
        "evidence": f'"{keyword}" appears {occurrences} times in ~{word_count} words ({density}%)',
    }
