# Claude Code — Installation & Usage

## Install

```bash
# From GitHub
claude skill add github:YOUR_USERNAME/google-seo-audit

# Or from a local clone
git clone https://github.com/YOUR_USERNAME/google-seo-audit
claude skill add ./google-seo-audit
```

## Slash command

```bash
/google-seo-audit https://example.com
/google-seo-audit https://example.com --psi-key=AIzaSy...
/google-seo-audit https://example.com --psi-key=AIzaSy... --gsc=./gsc.csv
```

## Natural language

```
Audit https://example.com
Run a Google SEO audit on https://example.com with PSI key AIzaSy...
用 google-seo-audit 诊断 https://example.com
```

## Save report to file

```bash
/google-seo-audit https://example.com --output=./report.md
```

## Notes

- Claude Code will invoke `scripts/audit_url.py` via bash if Python 3.9+ is available.
- If bash is not permitted, the agent will execute each audit step manually using web_fetch and web_search.
- The `--psi-key` is optional. The skill will attempt a keyless PSI request first.
