# Hermes (爱马仕) — Installation, Update & Usage

## Install (recommended: git clone)

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

## Update

```bash
cd ~/.hermes/skills/google-seo-audit
git pull
```

## Invocation

Hermes reads the `triggers` block in `SKILL.md` and activates the skill on natural language match:

```
Audit https://example.com
SEO audit https://example.com
Run Google SEO audit on https://example.com with PSI key AIzaSy...
```

## With version check

```
Audit https://example.com --github-owner YOUR_USERNAME
```

## With all parameters

```
Audit https://example.com --psi-key AIzaSy... --gsc ./gsc-performance-queries.csv --github-owner YOUR_USERNAME
```

## Execution flow

1. Hermes extracts `url`, `psi-key`, `gsc`, and `github-owner` from the invocation
2. If bash/Python available: runs `scripts/audit_url.py` directly
3. If not: follows the 10-step manual execution defined in `SKILL.md`
4. Outputs formatted markdown report (+ update notice if newer version exists)

## Get notified of updates

Watch the GitHub repo for new releases:
**GitHub → Watch → Custom → Releases**

## Notes

- `SKILL.md` is the single source of truth for skill discovery and execution.
- No slash command required; pure natural language invocation.
- Report language auto-detected from target site.
