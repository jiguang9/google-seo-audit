# Scoring Rubric

Definitions for severity, confidence, status, and module score calculation.

---

## Status values

| Status | Meaning | Emoji |
|--------|---------|-------|
| `pass` | Check met — no action needed | ✅ |
| `warning` | Check partially met or carries display/experience risk | ⚠️ |
| `fail` | Check not met — likely negative SEO impact | ❌ |
| `unknown` | Insufficient data to evaluate — **never fabricate a conclusion** | ❓ |

---

## Severity levels

| Level | Meaning | Emoji |
|-------|---------|-------|
| `high` | Direct confirmed ranking signal or serious crawl/index blocker | 🔴 |
| `medium` | Meaningful SEO impact; affects content quality or user experience | 🟡 |
| `low` | Best practice improvement; indirect or minor impact | 🟢 |

---

## Confidence levels

| Level | Meaning | When to use |
|-------|---------|------------|
| `high` | Based on direct data: HTTP response, PSI API, HTML parse result | Always preferred |
| `medium` | Based on indirect signals: E-E-A-T surface scan, heuristic detection | When direct verification is not possible |
| `low` | Based on very limited data; conclusion is tentative | When check fails due to missing data or access errors |

**Rule**: A finding with `confidence: low` must include a note on what data would increase confidence.

---

## Module score calculation

Each module score is calculated from its findings:

```
score = max(0, round((1 - weighted_penalty_ratio) × 100))

weighted_penalty_ratio =
    Σ (severity_weight × penalty_factor)
    ─────────────────────────────────────
    Σ (severity_weight)
```

Severity weights:
- high → 3
- medium → 2
- low → 1

Penalty factors:
- fail → 1.0
- warning → 0.4
- unknown → 0.2
- pass → 0.0

### Module status labels

| Score | Label | Emoji |
|-------|-------|-------|
| ≥ 80 | pass | ✅ |
| 55–79 | warning | ⚠️ |
| < 55 | fail | ❌ |

---

## Priority list ordering

Findings in the priority fix list are sorted:

1. By severity (high → medium → low)
2. Within same severity, by status (fail → warning → unknown)

`pass` findings are **not** included in the priority list.

---

## Evidence requirements

Every finding must include an `evidence` field containing at least one of:
- Exact HTTP status code and URL tested
- Raw values from PSI API response (e.g. `LCP: 3.2s`)
- HTML element content (e.g. `<title>: "My Page Title" (72 chars)`)
- CSV data summary (e.g. `Query export: 1,240 queries, avg position 18.3`)

Saying "the page seems slow" without data is **not acceptable evidence**.

---

## Corrections to common SEO myths

See [google-seo-current-notes.md](google-seo-current-notes.md) for a full list.
Key corrections applied in scoring:

| Myth | Correction applied |
|------|------------------|
| Title must be exactly 50–60 chars | It's a display guideline; not a ranking factor |
| Meta description controls ranking | It affects CTR; Google often rewrites it |
| Multiple H1 = penalty | It's a structural signal to review; not confirmed penalty |
| URL must be static (no params) | Params need canonical/noindex strategy; not removal |
| Domain age directly improves ranking | It's a historical trust signal; not a direct ranking factor |
| `site:` count = precise index count | It's a rough estimate; not reliable for precise counts |
