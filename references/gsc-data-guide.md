# GSC Data Export Guide

Step-by-step instructions for exporting each supported report type from Google Search Console.

---

## How to access Google Search Console

1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Select your property (domain or URL-prefix)
3. Follow the section below for the specific export you need

---

## Export type 1: Performance — Queries

**What it provides**: keyword rankings, clicks, impressions, CTR, average position.

**Steps**:
1. Click **Performance** → **Search results** in the left menu
2. Set date range (last 3 months recommended)
3. Make sure **Queries** tab is selected (default)
4. Click **Export** (top right) → **Download CSV**

**Columns**: `Query, Clicks, Impressions, CTR, Position`

**Use in audit**: Top keywords, ranking distribution, quick-win opportunities (pos 11–20).

---

## Export type 2: Performance — Pages

**What it provides**: page-level traffic, CTR, and average ranking position.

**Steps**:
1. Click **Performance** → **Search results**
2. Click the **Pages** tab
3. Click **Export** → **Download CSV**

**Columns**: `Page, Clicks, Impressions, CTR, Position`

**Use in audit**: Best/worst performing pages, low-CTR high-impression pages.

---

## Export type 3: Indexing Coverage (Pages)

**What it provides**: which pages are indexed, excluded, or have errors.

**Steps**:
1. Click **Indexing** → **Pages** in the left menu
2. Select status filter if needed (or leave as "All")
3. Click **Export** → **Download CSV**

**Columns**: `URL, Status, Reason` (column names may vary by GSC language)

**Use in audit**: Indexing errors, exclusion reasons, crawl waste.

---

## Export type 4: Links — External links

**What it provides**: referring domains and target pages.

**Steps**:
1. Click **Links** in the left menu
2. Under **External links**, click **Export external links**
3. Choose **More sample links** or **Latest links** → **Download CSV**

**Columns**: `Source domain, Target page` (or similar)

**Use in audit**: Referring domain count, source concentration, spam signals.

> **Important**: GSC links export does NOT include Domain Authority or DR scores.
> For authority metrics, use Ahrefs, Moz, or Semrush.

---

## Export type 5: Core Web Vitals

**What it provides**: URL-level CWV status (Good / Needs improvement / Poor).

**Steps**:
1. Click **Experience** → **Core Web Vitals** in the left menu
2. Select **Mobile** or **Desktop** tab
3. Click **Export** → **Download CSV**

**Columns**: `URL, Status, Category, Type`

**Use in audit**: Confirms which specific URLs have CWV issues.

---

## Export type 6: Enhancements / Rich results

**What it provides**: structured data errors and rich result eligibility.

**Steps**:
1. Click **Experience** → the specific enhancement (e.g., **Breadcrumbs**, **FAQ**, **Product**)
2. Click **Export** → **Download CSV**

**Columns**: `URL, Enhancement type, Status` (varies by enhancement type)

**Use in audit**: Structured data errors, rich result coverage.

---

## Passing GSC files to the audit

```bash
# Single file
/google-seo-audit https://example.com --gsc=./gsc-queries.csv

# The skill auto-detects the export type — no need to specify
```

If the file type cannot be detected, the skill will output:
- The detected column headers
- A table of expected column names for each supported type
- A request to confirm which export type the file is

---

## Notes

- GSC data is sampled; exact numbers may differ from Analytics
- Performance data typically has a 2–3 day delay
- Links data may lag by weeks — it reflects Google's most recent crawl snapshot
- `site:` operator in Google Search is a rough estimate; do not use for precise index counts
