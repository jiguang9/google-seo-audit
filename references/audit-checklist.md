# SEO Audit Checklist

Complete check list with pass/fail criteria for all nine modules.

---

## Module 1 — Technical SEO

| Check | Pass criteria | Severity | Confidence source |
|-------|--------------|----------|-------------------|
| HTTPS enforced | `http://` 301-redirects to `https://`; TLS cert valid | High | HTTP response |
| www/non-www consistent | Both variants resolve to the same canonical URL | Medium | HTTP response |
| robots.txt exists | `/robots.txt` returns HTTP 200 with text content | Medium | HTTP response |
| robots.txt not blocking critical paths | No `Disallow: /` or key content dirs for `*`/`googlebot` | High | robots.txt parse |
| sitemap.xml exists | Found at `/sitemap.xml` or referenced in robots.txt | High | HTTP response |
| sitemap.xml valid XML | Parses without error | High | XML parse |
| sitemap has `<lastmod>` dates | At least some entries have `<lastmod>` | Low | XML parse |
| sitemap freshness | Most recent `<lastmod>` is within 180 days | Medium | XML parse |
| 404 returns proper status | Non-existent URL returns HTTP 404 | Medium | HTTP response |
| URL depth ≤ 4 levels | Sample URL has ≤ 4 path segments | Low | URL analysis |
| URL parameters handled | If query params present, canonical/noindex strategy exists | Low | HTML parse |
| Canonical tag present | `<link rel="canonical">` in `<head>` | Medium | HTML parse |
| Structured data present | At least one valid JSON-LD block | Medium | HTML parse |
| hreflang correct (if multilingual) | `x-default` present; all language variants linked | Medium | HTML parse |

---

## Module 2 — Core Web Vitals

| Metric | Good | Needs Improvement | Poor | Severity |
|--------|------|-------------------|------|----------|
| LCP (mobile) | ≤ 2.5s | 2.5–4s | > 4s | High |
| INP (mobile) | ≤ 200ms | 200–500ms | > 500ms | High |
| CLS (mobile) | ≤ 0.1 | 0.1–0.25 | > 0.25 | High |
| LCP (desktop) | ≤ 2.5s | 2.5–4s | > 4s | Medium |
| INP (desktop) | ≤ 200ms | 200–500ms | > 500ms | Medium |
| CLS (desktop) | ≤ 0.1 | 0.1–0.25 | > 0.25 | Medium |
| FCP | ≤ 1.8s | reference | — | Reference |
| TTFB | ≤ 800ms | reference | — | Reference |
| PSI performance score | ≥ 90 = good; 50–89 = warning; < 50 = fail | High (mobile) | PSI API |

---

## Module 3 — On-page Content

| Check | Pass criteria | Severity | Notes |
|-------|--------------|----------|-------|
| `<title>` present | Title tag exists and is non-empty | High | |
| Title length | 50–60 chars | Low | Display guideline, not a ranking rule |
| Meta description present | Non-empty `<meta name="description">` | Medium | |
| Meta description length | 150–160 chars | Low | Display guideline |
| H1 present | At least one H1 tag | High | |
| H1 unique | One H1 per page | Low | Multiple H1 is a structural signal, not a confirmed penalty |
| Heading hierarchy | No level skips (H1→H2→H3) | Low | |
| Image alt attributes | All informational images have non-empty alt | Medium | |
| Image formats | ≥ 50% of images use WebP/AVIF | Low | |
| Open Graph tags | og:title, og:description, og:image present | Low | |
| E-E-A-T signals | Author, date, About/Contact/Privacy links present | Medium | Confidence: medium (indirect) |
| Content length | ≥ 300 visible words for key pages | Medium | |

---

## Module 4 — Internal Links

| Check | Pass criteria | Severity |
|-------|--------------|----------|
| Internal link count | ≥ 5 internal links on key pages | Medium |
| Anchor text quality | No more than 3 instances of generic anchors | Low |
| Breadcrumb navigation | HTML breadcrumb present | Low |
| BreadcrumbList schema | JSON-LD BreadcrumbList markup present | Low |

---

## Module 5 — External Links / Backlinks (GSC required)

| Check | Pass criteria | Severity | Notes |
|-------|--------------|----------|-------|
| Referring domain count | More domains = better (context-dependent) | Medium | |
| Source concentration | Top referring domain < 50% of total links | Medium | |
| Spam domain signals | No obvious spam patterns in top sources | Medium | |
| DA/DR scores | **Not available from GSC** — requires Ahrefs/Moz/Semrush | — | Do not infer |

---

## Module 6 — Mobile Experience

| Check | Pass criteria | Severity | Data source |
|-------|--------------|----------|------------|
| Viewport meta tag | `<meta name="viewport" content="width=device-width">` | High | HTML parse |
| PSI mobile score | ≥ 90 | High | PSI API |
| Mobile LCP | ≤ 2.5s | High | PSI API |
| Mobile INP | ≤ 200ms | High | PSI API |
| Mobile CLS | ≤ 0.1 | High | PSI API |

> **Note**: Google Mobile-Friendly Test and GSC Mobile Usability report are retired (2024).
> Mobile experience is assessed via PageSpeed Insights and Core Web Vitals only.

---

## Module 7–9 — GSC Modules (optional)

### Performance (queries)
| Check | Flag condition |
|-------|---------------|
| Quick-win queries | Position 11–20 with impressions > 100 |
| Low CTR queries | CTR < 2% with impressions > 500 |

### Performance (pages)
| Check | Flag condition |
|-------|---------------|
| Low-CTR pages | CTR < 2% with impressions > 500 |

### Coverage
| Check | Flag condition |
|-------|---------------|
| Indexing errors | Any URLs with "Error" status |
| High exclusion count | > 20% of submitted URLs excluded |

---

## Confidence Levels

| Level | Meaning |
|-------|---------|
| High | Based on direct HTTP response, API data, or HTML parse |
| Medium | Based on indirect signals or heuristic detection |
| Low | Based on limited data; conclusion is tentative |
| N/A | No data available — status is `unknown` |

**Rule**: If confidence is Low or N/A, the finding must state what data is needed.
**Never fabricate a conclusion.**
