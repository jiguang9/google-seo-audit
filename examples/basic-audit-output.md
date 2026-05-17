# Google SEO Audit Report

**Target**: https://www.example.com
**Date**: 2026-05-17
**Detected Language**: English (en)
**PSI API**: Keyless request (quota: ~400/day)
**GSC Data**: Not provided

---

## Summary

| Module | Status | Score |
|--------|--------|-------|
| Technical SEO | ⚠️ | 68/100 |
| Core Web Vitals | ⚠️ | 62/100 |
| Content | ✅ | 82/100 |
| Internal Links | ⚠️ | 70/100 |
| External Links (GSC) | ❓ | N/A — no GSC data |
| Mobile Experience | ⚠️ | 65/100 |

---

## Priority Fix List

### 🔴 High Severity — Fix immediately

**1. [Technical SEO] robots_txt** 🔴
- **Status**: ❌ FAIL
- **Severity / Confidence**: high / high
- **Evidence**: Disallow rule `/products/` found in robots.txt for User-agent: * — this blocks the entire products directory from Googlebot
- **Impact**: Product pages cannot be crawled or indexed; direct revenue impact
- **Fix**: Remove `Disallow: /products/` from robots.txt; use noindex meta tags on specific pages you want excluded instead

---

**2. [Core Web Vitals] lcp_mobile** 🔴
- **Status**: ❌ FAIL
- **Severity / Confidence**: high / high
- **Evidence**: LCP (mobile): 5.2s → poor (threshold: ≤ 2.5s good, 2.5–4s needs improvement, > 4s poor)
- **Impact**: LCP is a confirmed Google page experience signal; poor LCP correlates with higher bounce rates
- **Fix**: Optimize largest image/text block: use preload for hero image, serve next-gen image formats (WebP/AVIF), reduce server response time (current TTFB: 1.4s)

---

### 🟡 Medium Severity — Fix this month

**3. [Content] meta_description** 🟡
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: medium / high
- **Evidence**: Meta description absent on homepage
- **Impact**: Google may auto-generate a snippet from page content; a crafted description improves CTR in SERP
- **Fix**: Add `<meta name="description" content="...">` (150–160 chars) summarising the page's value proposition

**4. [Core Web Vitals] cls_mobile** 🟡
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: high / high
- **Evidence**: CLS (mobile): 0.18 → needs improvement (threshold: ≤ 0.1 good, 0.1–0.25 needs improvement)
- **Impact**: High CLS causes visual instability; users see content jumping during page load
- **Fix**: Set explicit width/height attributes on all images and video embeds; avoid inserting ads/banners above existing content

**5. [Technical SEO] structured_data** 🟡
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: medium / high
- **Evidence**: No JSON-LD structured data found on homepage
- **Impact**: Missing structured data reduces eligibility for rich results in Google SERP (breadcrumbs, FAQs, etc.)
- **Fix**: Add Organization and BreadcrumbList JSON-LD to homepage; add Article schema to blog posts

---

### 🟢 Low Severity — Continuous improvement

**6. [Content] image_alt_attributes** 🟢
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: medium / high
- **Evidence**: 4 images missing alt text: /img/hero-bg.jpg, /img/partner-logo-1.png, /img/partner-logo-2.png, /img/team-photo.jpg
- **Impact**: Impacts image search visibility and web accessibility (WCAG)
- **Fix**: Add descriptive alt text to all informational images; use empty alt="" for purely decorative images

**7. [Internal Links] breadcrumb_schema** 🟢
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: low / high
- **Evidence**: Breadcrumb: HTML=yes, BreadcrumbList schema=no
- **Impact**: HTML breadcrumb exists but BreadcrumbList schema is absent; breadcrumb display in SERP not enabled
- **Fix**: Add JSON-LD `BreadcrumbList` markup to enable breadcrumb display in Google search results

**8. [Content] image_formats** 🟢
- **Status**: ⚠️ WARNING
- **Severity / Confidence**: low / high
- **Evidence**: 12 images: 3 missing alt, 1 empty alt, 2/12 modern format (WebP/AVIF) — 16.7%
- **Impact**: Legacy image formats increase page weight and contribute to slow LCP
- **Fix**: Convert images to WebP or AVIF; use `<picture>` element for browser compatibility fallback

---

## Detailed Module Reports

### Technical SEO

| Check | Status | Evidence |
|-------|--------|---------|
| HTTPS enforced | ✅ | http://example.com → https://www.example.com (301); TLS cert valid |
| www redirect | ✅ | example.com → www.example.com (301 consistent) |
| robots.txt | ❌ | `Disallow: /products/` blocks critical content directory |
| sitemap.xml | ✅ | Found at /sitemap.xml; 847 URLs; most recent lastmod 12 days ago |
| 404 page | ✅ | /seo-audit-nonexistent-page-xk9q2.html → HTTP 404 (custom page: yes) |
| URL depth | ✅ | Sample URL depth: 2 levels |
| Canonical tag | ✅ | `<link rel="canonical" href="https://www.example.com/">` present |
| Structured data | ⚠️ | No JSON-LD found on homepage |
| hreflang | ✅ | No hreflang tags (single-language site — expected) |

---

### Core Web Vitals

| Metric | Mobile | Desktop |
|--------|--------|---------|
| LCP | ❌ 5.2s (poor) | ⚠️ 3.1s (needs improvement) |
| INP | ✅ 180ms (good) | ✅ 95ms (good) |
| CLS | ⚠️ 0.18 (needs improvement) | ✅ 0.04 (good) |
| FCP | 2.8s | 1.4s |
| TTFB | 1.4s | 820ms |
| PSI Score | ⚠️ 62/100 | ⚠️ 74/100 |

---

### Content

| Check | Status | Evidence |
|-------|--------|---------|
| Title | ✅ | "Enterprise ERP Software — Example Inc" (42 chars, within display range) |
| Meta description | ❌ | Absent on homepage |
| H1 | ✅ | 1 H1: "Enterprise Resource Planning for Growing Businesses" |
| Heading hierarchy | ✅ | H1→H2→H3, no level skips |
| Image alt | ⚠️ | 4 images missing alt text |
| Image formats | ⚠️ | 16.7% modern format (WebP/AVIF) |
| Open Graph | ✅ | og:title, og:description, og:image present |
| E-E-A-T signals | ⚠️ | Found: about_page_link, contact_page_link; Missing: author_byline, publication_date, privacy_policy_link |

---

### Internal Links

| Check | Status | Evidence |
|-------|--------|---------|
| Internal link count | ✅ | 34 internal links |
| External link count | ✅ | 6 external links |
| Anchor text quality | ⚠️ | 4 weak anchor text instances: "click here" (×2), "read more" (×2) |
| Breadcrumb HTML | ✅ | Breadcrumb nav detected via class="breadcrumb" |
| BreadcrumbList schema | ⚠️ | HTML breadcrumb present; JSON-LD BreadcrumbList absent |

---

### External Links (GSC)

GSC Links export not provided.

To enable backlink analysis:
1. Open [Google Search Console](https://search.google.com/search-console)
2. Navigate to **Links** → **Export external links** → **Download CSV**
3. Re-run audit with `--gsc=./gsc-links.csv`

---

### Mobile Experience

| Check | Status | Value |
|-------|--------|-------|
| Viewport meta | ✅ | `width=device-width, initial-scale=1` |
| PSI mobile score | ⚠️ | 62/100 |
| Mobile LCP | ❌ | 5.2s (poor) |
| Mobile INP | ✅ | 180ms (good) |
| Mobile CLS | ⚠️ | 0.18 (needs improvement) |

---

## Disclaimer

- `site:` query results are rough estimates; use GSC Coverage report for precise index counts.
- Domain age is historical trust context, not a direct ranking signal.
- E-E-A-T findings are surface-level with medium confidence.
- DA/DR scores not available from GSC; use Ahrefs/Moz/Semrush.

---

*Generated by [google-seo-audit](https://github.com/YOUR_USERNAME/google-seo-audit)*
