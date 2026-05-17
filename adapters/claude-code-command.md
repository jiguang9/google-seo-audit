# Claude Code — Installation, Update & Usage

## Install (recommended: git clone)

```bash
git clone https://github.com/jiguang9/google-seo-audit ~/.claude/skills/google-seo-audit
claude skill add ~/.claude/skills/google-seo-audit
```

## Update

```bash
cd ~/.claude/skills/google-seo-audit
git pull
```

That's it — one command, always in sync with the latest release.

## Install (alternative: directly from GitHub)

```bash
claude skill add github:jiguang9/google-seo-audit
```

> This copies files locally with no git history. To update, re-run the command above.

## Slash command

```bash
/google-seo-audit https://example.com
/google-seo-audit https://example.com --psi-key=AIzaSy...
/google-seo-audit https://example.com --psi-key=AIzaSy... --gsc=./gsc.csv
/google-seo-audit https://example.com --github-owner=jiguang9   # version check
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

## Get notified of updates

Watch the GitHub repo for new releases:
**GitHub → Watch → Custom → Releases**

## Notes

- Claude Code will invoke `scripts/audit_url.py` via bash if Python 3.9+ is available.
- If bash is not permitted, the agent executes each audit step manually using web_fetch and web_search.
- The `--psi-key` is optional — the skill tries a keyless request first.
- `--github-owner` enables version check; prepends an update notice to the report if a newer release exists.
