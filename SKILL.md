---
name: google-seo-audit
description: >
  Performs a comprehensive Google SEO audit for any website URL.
  Analyses technical SEO, Core Web Vitals (LCP/INP/CLS), on-page content,
  internal links, backlinks (via optional GSC export), and mobile experience.
  Generates a prioritised diagnostic report with evidence-backed findings,
  severity ratings, confidence levels, and actionable fix recommendations.
  Report language auto-detected from the target site.
version: 1.0.0
author: google-seo-audit
license: MIT
triggers:
  natural_language:
    - "audit {url}"
    - "seo audit {url}"
    - "run google seo audit on {url}"
    - "check seo for {url}"
    - "diagnose {url}"
    - "用 google-seo-audit 诊断 {url}"
    - "对 {url} 进行 SEO 诊断"
    - "检查 {url} 的 SEO"
  slash_command: /google-seo-audit
args:
  - name: url
    required: true
    description: "Target website URL (e.g. https://example.com)"
  - name: psi-key
    required: false
    description: "Google PageSpeed Insights API key. Optional; increases daily quota from ~400 to 25,000 requests."
  - name: gsc
    required: false
    description: "Path to a Google Search Console CSV export. Auto-detects export type. Optional module."
tools_required:
  - web_fetch
  - web_search
  - bash
---

# Google SEO Audit Skill

## Overview

This skill audits any publicly accessible website for Google SEO health across
nine dimensions. It combines live page fetching, PageSpeed Insights API data,
optional GSC exports, and HTML analysis to produce a prioritised report.

Every finding includes:
- **Status**: pass / warning / fail / unknown
- **Severity**: high / medium / low
- **Confidence**: high / medium / low (no finding is fabricated without evidence)
- **Evidence**: the raw data that supports the conclusion
- **Impact**: the SEO consequence
- **Fix**: a concrete remediation step (omitted for passing checks)

If data is unavailable for a check, the status is `unknown` and the finding
explains what data is needed — **no conclusions are invented**.

---

## Invocation

### Slash command (Claude Code, environments that support it)

```
/google-seo-audit https://example.com
/google-seo-audit https://example.com --psi-key=AIzaSy...
/google-seo-audit https://example.com --psi-key=AIzaSy... --gsc=./gsc-export.csv
```

### Natural language (Codex, OpenClaw, Hermes, and all environments)

```
Audit https://example.com
Run a Google SEO audit on https://example.com
用 google-seo-audit 诊断 https://example.com
对 https://example.com 进行 SEO 诊断，PSI key 是 AIzaSy...，GSC 文件在 ./gsc.csv
```

The agent must extract `url`, optional `psi-key`, and optional `gsc` path
from the invocation, then follow the execution steps below.

---

## Execution Steps

When this skill is triggered, the agent **must** execute the following steps
in order. Use `scripts/audit_url.py` if bash is available. Otherwise, execute
each step manually using the available tools.

### Step 0 — Check bash availability and version

```bash
python scripts/audit_url.py {url} [--psi-key={key}] [--gsc={file}] [--github-owner={owner}] --output=report.md
```

If bash / Python is available: run the command above and output the report.  
If **not** available: execute Steps 1–10 manually using web_fetch and web_search.

**Version check** (optional, non-blocking): if `--github-owner` is provided, the script
calls `scripts/check_version.py` to compare the local `version` in SKILL.md against the
latest GitHub release. If a newer version is found, a notice is prepended to the report.
If the check fails for any reason (network, no releases yet), the audit continues silently.

When running manually (no bash): call `web_fetch` on
`https://api.github.com/repos/{owner}/google-seo-audit/releases/latest`, compare
`tag_name` against the `version` in this file's YAML frontmatter, and prepend a notice
if an update is available.

---

### Step 1 — Fetch the page

Use `web_fetch` to retrieve the target URL. Record:
- Final URL after redirects
- HTTP status code
- Response headers (Content-Type, X-Robots-Tag, etc.)
- Full HTML body

---

### Step 2 — Detect language

Read the `<html lang="...">` attribute or `<meta http-equiv="content-language">`.
Set `report_language`:
- `zh` if lang code starts with `zh`
- `en` otherwise (default)

---

### Step 3 — Technical SEO checks

Perform each check; record evidence, status, severity, confidence:

| Check | How to verify |
|-------|--------------|
| HTTPS enforced | Fetch `http://domain` — does it 301 to `https://`? |
| www/non-www consistent | Fetch both; do they resolve to the same final URL? |
| robots.txt | Fetch `{origin}/robots.txt`; parse Disallow/Allow/Sitemap rules |
| Robots blocks critical paths | Check if `/` or major content dirs are Disallowed for `*` or `googlebot` |
| sitemap.xml | Fetch `{origin}/sitemap.xml` or URL from robots.txt; check existence and XML validity |
| sitemap lastmod | Check if `<lastmod>` dates are present and recent |
| 404 handling | Fetch a deliberately wrong URL; verify HTTP 404 status is returned |
| URL depth | Count `/` segments in the sample URL |
| URL parameters | Check for `?key=value` in URL; note canonical strategy needed |
| Canonical tag | Parse `<link rel="canonical">` from HTML head |
| Structured data | Parse `<script type="application/ld+json">` blocks; identify @type values |
| Hreflang | Parse `<link rel="alternate" hreflang="...">` tags |

---

### Step 4 — PageSpeed Insights (Core Web Vitals)

Call PSI API for **mobile** strategy first, then **desktop**:

```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile[&key={psi_key}]
```

Extract and rate:

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2.5s | 2.5–4s | > 4s |
| INP | ≤ 200ms | 200–500ms | > 500ms |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| FCP | ≤ 1.8s | reference only | — |
| TTFB | ≤ 800ms | reference only | — |

If API returns 429 (rate limited): set status=unknown, note user should provide `--psi-key`.  
If no key provided: try without key first; only prompt for key on failure.

---

### Step 5 — On-page content analysis

Parse the fetched HTML:

| Check | What to look for |
|-------|-----------------|
| `<title>` | Present? Length (display guideline: 50–60 chars, not a hard limit) |
| `<meta name="description">` | Present? Length (guideline: 150–160 chars) |
| `<meta name="keywords">` | Note: Google ignores this tag |
| H1–H6 hierarchy | Count H1 tags; detect heading level skips |
| Image `alt` attributes | Count images without alt or with empty alt |
| Image formats | Check for WebP/AVIF usage |
| Open Graph / Twitter Card | Check og:title, og:image, twitter:card |
| E-E-A-T signals | Author byline, pub date, About/Contact/Privacy links |
| Content word count | Count visible words; flag if < 300 for important pages |

---

### Step 6 — Internal link analysis

From the fetched HTML:

| Check | Logic |
|-------|-------|
| Internal link count | Count `<a href>` pointing to same domain |
| External link count | Count `<a href>` pointing to other domains |
| Weak anchor text | Flag "click here", "read more", "more", "了解更多" etc. |
| Breadcrumb nav | Detect via aria-label/class; check for BreadcrumbList JSON-LD |

---

### Step 7 — GSC module (if `--gsc` provided)

1. Read the CSV file
2. Auto-detect type by column headers:
   - `Query, Clicks, Impressions, CTR, Position` → performance_queries
   - `Page, Clicks, Impressions, CTR, Position` → performance_pages
   - `URL, Status, Reason` → coverage_pages
   - Columns containing "source" and "target" → links
   - `URL, Status, Category, Type` → core_web_vitals
   - `URL` + column with "enhancement" → enhancements
3. If type is unrecognized: output "Unrecognized GSC export format" + detected column names + expected formats hint
4. Parse and include relevant metrics in the report

---

### Step 8 — Backlinks (GSC links export)

If GSC links data is available:
- Report: unique referring domains, top sources, source concentration
- Flag: heavy reliance on very few domains (top 1 source > 50% of links)
- Flag: potential spam domain patterns (very long domains, numeric-heavy domains)
- **Do NOT infer DA/DR from GSC data** — note that authority scores require Ahrefs/Moz/Semrush

If GSC links data is **not** available:
- Output: "External link analysis requires GSC Links export. Export from Search Console → Links → Export."

---

### Step 9 — Mobile experience

Based on PSI mobile results (Step 4):
- Mobile performance score
- Mobile Core Web Vitals ratings
- PSI mobile-specific diagnostics (font sizes, tap target sizes, etc.)
- Viewport meta tag presence (from Step 5 HTML)

> Note: Google Mobile-Friendly Test and GSC Mobile Usability report are retired.
> Mobile experience is now assessed via PageSpeed Insights and Core Web Vitals only.

---

### Step 10 — Assemble and output report

Structure the report as:

```
# Google SEO Audit Report / Google SEO 诊断报告

Target / 目标网站: {url}
Date / 诊断日期: {today}
Detected Language / 检测语言: {lang}

## Summary / 总览
[Module score table]

## Priority Fix List / 优先修复清单
### 🔴 High Severity (fix immediately)
### 🟡 Medium Severity (fix this month)
### 🟢 Low Severity (continuous improvement)

## Detailed Module Reports / 各模块详细诊断
[Per-module findings]
```

Each finding **must include**: status emoji, severity, confidence, evidence, impact, fix (if applicable).

---

## Quality Rules

1. **Never fabricate a finding** — if data is missing, status = `unknown`.
2. **Confidence must reflect data quality** — PSI data → high; HTML scan → high; E-E-A-T surface scan → medium.
3. **Soften absolute SEO claims**:
   - Title/description lengths are display guidelines, not ranking rules.
   - Multiple H1 is a structural signal, not a confirmed penalty.
   - URL parameters need canonical strategy, not removal.
   - URL depth is a crawl efficiency suggestion, not a ranking rule.
   - Domain age is a historical trust indicator, not a direct ranking factor.
   - `site:` count is an estimate, not a precise index count.
4. **Do not cite retired tools**: Google Mobile-Friendly Test and GSC Mobile Usability report are retired.
5. **Do not infer DA/DR from GSC data** — GSC links export does not contain authority scores.

---

## Environment Adapters

See [adapters/](adapters/) for environment-specific installation and invocation instructions:

- [Claude Code](adapters/claude-code-command.md)
- [Codex](adapters/codex-usage.md)
- [OpenClaw](adapters/openclaw.md)
- [Hermes](adapters/hermes.md)

---

## References

- [audit-checklist.md](references/audit-checklist.md) — Complete check list with pass/fail criteria
- [gsc-data-guide.md](references/gsc-data-guide.md) — How to export each GSC report type
- [scoring-rubric.md](references/scoring-rubric.md) — Scoring weights and severity definitions
- [google-seo-current-notes.md](references/google-seo-current-notes.md) — Retired tools and corrected SEO myths
