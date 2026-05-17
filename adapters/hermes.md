# Hermes (爱马仕) — Installation & Usage

## Install

```bash
git clone https://github.com/YOUR_USERNAME/google-seo-audit ~/.hermes/skills/google-seo-audit
```

Or register in your Hermes configuration:

```yaml
skills:
  - name: google-seo-audit
    path: ./google-seo-audit
    entry: SKILL.md
```

## Invocation

Hermes reads the `triggers` block in `SKILL.md` and activates the skill on natural language match:

```
Audit https://example.com
SEO audit https://example.com
Run Google SEO audit on https://example.com with PSI key AIzaSy...
```

## With parameters

```
Audit https://example.com --psi-key AIzaSy... --gsc ./gsc-performance-queries.csv
```

## Execution flow

1. Hermes extracts `url`, `psi-key`, and `gsc` from the invocation
2. If bash/Python available: runs `scripts/audit_url.py` directly
3. If not: follows the 10-step manual execution defined in `SKILL.md`
4. Outputs a formatted markdown report

## Notes

- The `SKILL.md` is the single source of truth — Hermes reads it for both skill discovery and execution instructions.
- No slash command required; pure natural language invocation.
- Report language auto-detected from target site.
