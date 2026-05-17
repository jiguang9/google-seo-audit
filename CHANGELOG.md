# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.0.0] — 2026-05-17

### Added
- `SKILL.md` — portable skill definition with YAML frontmatter and dual-trigger support
  (slash command + natural language) for Claude Code, Codex, OpenClaw, Hermes
- `scripts/fetch_page.py` — HTTPS enforcement, www/non-www redirect, robots.txt, 404 checks
- `scripts/parse_html.py` — TKD, H1–H6 hierarchy, canonical, hreflang, JSON-LD schema,
  image alt audit, internal/external links, E-E-A-T surface scan, breadcrumbs
- `scripts/parse_sitemap.py` — sitemap discovery, XML parsing, lastmod freshness check
- `scripts/pagespeed.py` — PageSpeed Insights API (mobile + desktop); LCP/INP/CLS/FCP/TTFB
- `scripts/parse_gsc.py` — auto-detects 6 GSC export types by column headers; parses
  performance queries/pages, coverage, links, CWV, enhancements
- `scripts/score_report.py` — weighted scoring engine; bilingual report generation (EN/ZH)
- `scripts/audit_url.py` — main orchestrator and CLI entry point
- `scripts/check_version.py` — non-blocking GitHub release version check
- `adapters/` — installation and invocation guides for Claude Code, Codex, OpenClaw, Hermes
- `references/` — audit checklist, GSC export guide, scoring rubric, Google SEO current notes
- `examples/` — sample GSC CSVs and expected report output
- `tests/test_parsers.py` — 34 unit tests covering all parsers (100% passing)

### Design decisions
- PSI API key is optional; skill tries keyless request first
- Report language auto-detected from `<html lang>` attribute
- All findings include: status · severity · confidence · evidence · impact · fix
- No finding is fabricated: unavailable data → `status: unknown`
- Softened absolute SEO rules (title length, H1 uniqueness, URL depth, etc.) per
  current Google documentation; see `references/google-seo-current-notes.md`
- Backlink DA/DR not inferred from GSC; noted as requiring Ahrefs/Moz/Semrush

---

## How to upgrade

```bash
cd <skill-install-directory>
git pull
```

If installed via `claude skill add github:...` (not git clone), re-run the install command:

```bash
claude skill add github:jiguang9/google-seo-audit
```
