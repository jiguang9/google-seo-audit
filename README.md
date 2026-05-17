# google-seo-audit

A portable Google SEO audit Skill for Claude Code, Codex, OpenClaw, Hermes, and any agent that supports natural language or slash-command invocation.

Audits any public website across nine dimensions, calls the PageSpeed Insights API for Core Web Vitals, optionally parses Google Search Console exports, and outputs a prioritised report with evidence-backed findings and fix recommendations.

---

## What it checks

| Module | Key checks |
|--------|-----------|
| Technical SEO | HTTPS, www redirect, robots.txt, sitemap, canonical, structured data, hreflang, 404 |
| Core Web Vitals | LCP, INP, CLS (mobile + desktop) via PageSpeed Insights API |
| On-page Content | Title, meta description, H1–H6, image alt, E-E-A-T signals, OG tags |
| Internal Links | Link count, anchor text quality, breadcrumbs + BreadcrumbList schema |
| External Links | Referring domain count, source concentration, spam signals (GSC export) |
| Mobile Experience | PSI mobile score, mobile CWV, viewport meta |
| GSC Queries | Top keywords, position distribution, quick-win opportunities (optional) |
| GSC Pages | Top pages, low-CTR pages with high impressions (optional) |
| GSC Coverage | Indexing errors, exclusion reasons (optional) |

Every finding includes: **status · severity · confidence · evidence · impact · fix**.  
Nothing is fabricated — if data is unavailable, status is `unknown`.

---

## Installation

All environments: **`git clone` is the recommended install method** — it gives you one-command updates via `git pull`.

### Claude Code

```bash
# Recommended: clone into Claude Code's skills directory for easy updates
git clone https://github.com/jiguang9/google-seo-audit ~/.claude/skills/google-seo-audit
```

Claude Code auto-loads skills placed in `~/.claude/skills/` or `.claude/skills/` in your project.  
If your Claude Code version supports the `skill add` command:

```bash
claude skill add github:jiguang9/google-seo-audit   # installs without git history
```

See [adapters/claude-code-command.md](adapters/claude-code-command.md) for details.

### Codex

```bash
git clone https://github.com/jiguang9/google-seo-audit ~/.codex/skills/google-seo-audit
```

See [adapters/codex-usage.md](adapters/codex-usage.md).

### OpenClaw

```bash
git clone https://github.com/jiguang9/google-seo-audit ~/.openclaw/skills/google-seo-audit
```

See [adapters/openclaw.md](adapters/openclaw.md).

### Hermes

```bash
git clone https://github.com/jiguang9/google-seo-audit ~/.hermes/skills/google-seo-audit
```

See [adapters/hermes.md](adapters/hermes.md).

---

## Updating

Because the skill is a git repo, updates are a single command regardless of which agent you use:

```bash
cd ~/.claude/skills/google-seo-audit   # or wherever you cloned it
git pull
```

**Automatic update notice**: if you pass `--github-owner=jiguang9` when running the audit,
the skill checks the latest GitHub release and prepends a notice to the report if a newer
version is available. The check is non-blocking — it never delays or fails the audit.

```bash
/google-seo-audit https://example.com --github-owner=jiguang9
```

To get notified of new releases without running an audit, watch this repository:
**GitHub → Watch → Custom → Releases**.

---

## Usage

### Natural language (works in all environments)

```
Audit https://example.com
Run a Google SEO audit on https://example.com
Audit https://example.com with PSI key AIzaSy...
Audit https://example.com with PSI key AIzaSy... and GSC file ./gsc.csv
用 google-seo-audit 诊断 https://example.com
```

### Slash command (Claude Code and compatible environments)

```bash
/google-seo-audit https://example.com
/google-seo-audit https://example.com --psi-key=AIzaSy...
/google-seo-audit https://example.com --psi-key=AIzaSy... --gsc=./gsc-export.csv
```

### Direct Python (standalone)

```bash
pip install -r requirements.txt
cd scripts
python audit_url.py https://example.com
python audit_url.py https://example.com --psi-key=AIzaSy...
python audit_url.py https://example.com --gsc=../examples/gsc-performance-queries.csv
python audit_url.py https://example.com --output=../report.md
# With version check
python audit_url.py https://example.com --github-owner=jiguang9
```

---

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | Yes | Target website URL |
| `--psi-key` | No | [PageSpeed Insights API key](https://developers.google.com/speed/docs/insights/v5/get-started). Free; significantly increases the unauthenticated quota. Try without first — only needed if rate-limited. Can also be set via `PAGESPEED_API_KEY` env var. |
| `--gsc` | No | Path to a GSC CSV export. Supports 6 export types; auto-detected. |
| `--output` | No | Save report to a file instead of stdout |
| `--json` | No | Output raw audit data as JSON |
| `--github-owner` | No | Your GitHub username. Enables version check — audit report will include an update notice if a newer release exists. |

---

## Getting a PageSpeed Insights API key (free, 5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Search for **PageSpeed Insights API** and click **Enable**
5. Go to **APIs & Services → Credentials → Create Credentials → API key**
6. Copy the key — no billing required

---

## Exporting GSC data

See [references/gsc-data-guide.md](references/gsc-data-guide.md) for step-by-step export instructions for all supported report types.

Supported GSC export types (auto-detected by column headers):

| Type | Key columns |
|------|------------|
| performance_queries | Query, Clicks, Impressions, CTR, Position |
| performance_pages | Page, Clicks, Impressions, CTR, Position |
| coverage_pages | URL, Status, Reason |
| links | Source domain, Target page |
| core_web_vitals | URL, Status, Category, Type |
| enhancements | URL, Enhancement type, Status |

---

## Report language

The report language is auto-detected from the target website's `<html lang>` attribute:
- Chinese sites (`zh-*`) → report in Chinese
- All others → report in English

---

## Project structure

```
google-seo-audit/
├── SKILL.md                    # Skill definition (YAML frontmatter + execution instructions)
├── README.md
├── requirements.txt
├── agents/
│   └── openai.yaml             # Codex metadata
├── scripts/
│   ├── audit_url.py            # Main orchestrator (CLI entry point)
│   ├── fetch_page.py           # HTTP fetch, HTTPS/redirect/robots/404 checks
│   ├── parse_html.py           # TKD, headings, schema, images, links, E-E-A-T
│   ├── parse_sitemap.py        # Sitemap discovery, parsing, validation
│   ├── pagespeed.py            # PageSpeed Insights API + CWV findings
│   ├── parse_gsc.py            # GSC CSV auto-detection and parsing
│   └── score_report.py         # Finding scoring + report generation
├── references/
│   ├── audit-checklist.md      # Complete check list with pass/fail criteria
│   ├── gsc-data-guide.md       # GSC export instructions
│   ├── scoring-rubric.md       # Severity/confidence definitions
│   └── google-seo-current-notes.md  # Retired tools, corrected SEO myths
├── templates/
│   └── report-template.md      # Report output format reference
├── adapters/
│   ├── claude-code-command.md
│   ├── codex-usage.md
│   ├── openclaw.md
│   └── hermes.md
├── examples/
│   ├── basic-audit-output.md
│   ├── gsc-performance-queries.csv
│   ├── gsc-performance-pages.csv
│   └── expected-report.md
└── tests/
    └── test_parsers.py
```

---

## Requirements

```
Python 3.9+
requests
beautifulsoup4
lxml
```

Install: `pip install -r requirements.txt`

---

## License

MIT
