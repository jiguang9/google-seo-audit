# Codex — Installation, Update & Usage

## Install (recommended: git clone)

```bash
git clone https://github.com/YOUR_USERNAME/google-seo-audit ~/.codex/skills/google-seo-audit
```

Or reference via URL in your Codex configuration:

```yaml
skills:
  - url: https://github.com/YOUR_USERNAME/google-seo-audit
```

## Update

```bash
cd ~/.codex/skills/google-seo-audit
git pull
```

## Invocation

Codex triggers the skill via natural language matching against the `triggers` in `SKILL.md`:

```
Audit https://example.com
Run a Google SEO audit on https://example.com
SEO audit https://example.com with PSI key AIzaSy...
Audit https://example.com, github owner is YOUR_USERNAME   # enables version check
```

## With all parameters

```
Audit https://example.com using PSI key AIzaSy..., GSC file ./gsc-export.csv,
and check for updates (github owner YOUR_USERNAME)
```

## Get notified of updates

Watch the GitHub repo for new releases:
**GitHub → Watch → Custom → Releases**

## Notes

- Codex reads `agents/openai.yaml` and `SKILL.md` for skill metadata and execution instructions.
- Codex will attempt to run `scripts/audit_url.py` if the environment has Python available.
- If no Python runtime: Codex follows the manual execution steps in `SKILL.md` (Steps 1–10).
