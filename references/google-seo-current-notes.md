# Google SEO Current Notes

Corrections to outdated SEO practices, retired tools, and common myths.
Updated: 2025. Cross-reference with [Google Search Central](https://developers.google.com/search/docs).

---

## Retired tools and reports — do not reference

| Tool / Report | Status | Replacement |
|---------------|--------|-------------|
| Google Mobile-Friendly Test | **Retired 2024** | PageSpeed Insights mobile score + Core Web Vitals |
| GSC Mobile Usability report | **Retired / changed 2024** | PSI mobile diagnostics, Core Web Vitals |
| FID (First Input Delay) | **Replaced by INP (March 2024)** | INP (Interaction to Next Paint) is the CWV metric |
| AMP requirement for Top Stories | **Removed** | Any mobile-fast page is eligible |

---

## Core Web Vitals — current metrics (2024+)

| Metric | Status | Thresholds |
|--------|--------|-----------|
| LCP — Largest Contentful Paint | **Active CWV** | Good ≤ 2.5s / NI 2.5–4s / Poor > 4s |
| INP — Interaction to Next Paint | **Active CWV** (replaced FID Mar 2024) | Good ≤ 200ms / NI 200–500ms / Poor > 500ms |
| CLS — Cumulative Layout Shift | **Active CWV** | Good ≤ 0.1 / NI 0.1–0.25 / Poor > 0.25 |
| FID — First Input Delay | **Retired Mar 2024** | Replaced by INP |

---

## Softened / corrected SEO rules

### Title tag length
- **Old claim**: Must be 50–60 characters; exceeding causes ranking penalty.
- **Correction**: 50–60 chars is a *display guideline* to reduce SERP truncation. Google dynamically rewrites titles. Length has no direct correlation with ranking.
- **Audit behaviour**: Flag as display risk warning, not a ranking failure.

### Meta description length
- **Old claim**: Must be 150–160 characters.
- **Correction**: Display guideline only. Google frequently rewrites meta descriptions. No direct ranking impact.
- **Audit behaviour**: Flag truncation risk; note CTR may be affected by auto-generated snippets.

### Meta keywords tag
- **Old claim**: Add relevant keywords to `<meta name="keywords">`.
- **Correction**: Google officially ignores the meta keywords tag (confirmed since 2009). No SEO value.
- **Audit behaviour**: Note "no maintenance needed"; neither flag presence nor absence as an issue.

### H1 uniqueness
- **Old claim**: Multiple H1 tags = SEO error.
- **Correction**: Multiple H1 tags are a *structural signal worth reviewing* but are not a confirmed ranking penalty. Modern HTML5 allows multiple H1 tags in sectioned documents.
- **Audit behaviour**: Warn as structural review item; do not mark as fail.

### URL static vs dynamic
- **Old claim**: Dynamic URLs with `?key=value` should be avoided entirely.
- **Correction**: URL parameters are fine *with proper canonical / noindex strategy*. Google handles parameter URLs well when configured correctly.
- **Audit behaviour**: Flag parameter URLs as needing a canonical strategy, not removal.

### URL depth (≤ 3 levels)
- **Old claim**: URLs must be ≤ 3 levels deep; deeper URLs rank worse.
- **Correction**: URL depth is a *crawl efficiency consideration*, not a confirmed ranking factor. Deep URLs for infrequently updated content may receive less crawl budget.
- **Audit behaviour**: Flag as crawl efficiency suggestion, not a ranking rule.

### Canonical on every page
- **Old claim**: Every page must have a self-referencing canonical.
- **Correction**: Canonical tags are *recommended for indexable pages* but context-dependent:
  - Pagination, parameter pages, hreflang alternates, and aggregation pages require case-by-case judgment.
  - Missing canonical on a well-structured page is a warning, not a definite error.
- **Audit behaviour**: Warn; note context dependency.

### Domain age
- **Old claim**: Older domains rank better.
- **Correction**: Domain age is a *historical trust signal* (established brand, accumulated backlinks over time). It is not a direct algorithmic ranking factor. Google's John Mueller has confirmed domain age itself is not used as a ranking signal.
- **Audit behaviour**: Include as informational context; do not score it.

### site: operator for index count
- **Old claim**: `site:domain.com` shows the exact number of indexed pages.
- **Correction**: `site:` results are a *rough estimate only*. They exclude personalisation filtering, deduplication, and are not a reliable measure. Use Google Search Console Coverage report for accurate data.
- **Audit behaviour**: Always label as "estimated" and recommend GSC Coverage report for precision.

### Keyword density (2%–8%)
- **Old claim**: Keyword density must be between 2% and 8%.
- **Correction**: Google does not use keyword density as a ranking metric. Natural language use of relevant terms matters; mechanical density targets lead to keyword stuffing.
- **Audit behaviour**: Only flag obvious stuffing (> 5% density for a single keyword); do not require a minimum.

---

## E-E-A-T — important nuances

E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) is a quality framework used by Google's human quality raters. It is **not directly a ranking algorithm signal** — it influences how quality raters assess content, which in turn shapes algorithm training.

Practical implications:
- E-E-A-T matters most for **YMYL (Your Money or Your Life)** content (health, finance, legal, news)
- For general commercial or informational content, its impact is less direct
- Surface-level signals (author byline, About page, contact info) are indicators, not guarantees
- Confidence for E-E-A-T findings: always **medium**

---

## Backlinks — what GSC can and cannot tell you

GSC Links export provides:
- ✅ Referring domain names
- ✅ Target pages
- ✅ Link counts per source

GSC Links export does **not** provide:
- ❌ Domain Authority (DA) — Moz metric
- ❌ Domain Rating (DR) — Ahrefs metric  
- ❌ Spam scores
- ❌ Link quality assessment

To get authority scores, use Ahrefs, Moz, or Semrush exports separately.
