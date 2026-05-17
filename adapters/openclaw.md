# OpenClaw (龙虾) — Installation, Update & Usage

## Install (recommended: git clone)

```bash
git clone https://github.com/YOUR_USERNAME/google-seo-audit ~/.openclaw/skills/google-seo-audit
```

Or add to your OpenClaw skill registry:

```yaml
skills:
  - name: google-seo-audit
    source: https://github.com/YOUR_USERNAME/google-seo-audit
    skill_file: SKILL.md
```

## Update

```bash
cd ~/.openclaw/skills/google-seo-audit
git pull
```

## Invocation

OpenClaw matches natural language triggers defined in `SKILL.md`:

```
Audit https://example.com
用 google-seo-audit 诊断 https://example.com
检查 https://example.com 的 SEO
Run SEO audit on https://example.com with key AIzaSy...
```

## With version check

```
对 https://example.com 进行 SEO 诊断，github owner 是 YOUR_USERNAME
```

## With all parameters

```
对 https://example.com 进行 SEO 诊断，PSI key 是 AIzaSy...，GSC 文件在 ./gsc.csv，github owner 是 YOUR_USERNAME
```

## Get notified of updates

Watch the GitHub repo for new releases:
**GitHub → Watch → Custom → Releases**

## Notes

- Report language auto-detected from target site's `<html lang>` attribute.
- If bash tools are available, `scripts/audit_url.py` will be run directly.
- Version check is non-blocking — a failed check never stops the audit.
