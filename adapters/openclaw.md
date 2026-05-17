# OpenClaw (龙虾) — Installation & Usage

## Install

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

## Invocation

OpenClaw matches natural language triggers defined in `SKILL.md`:

```
Audit https://example.com
用 google-seo-audit 诊断 https://example.com
检查 https://example.com 的 SEO
Run SEO audit on https://example.com with key AIzaSy...
```

## With GSC data

```
对 https://example.com 进行 SEO 诊断，GSC 文件在 ./gsc.csv，PSI key 是 AIzaSy...
```

## Notes

- OpenClaw will extract parameters from natural language and invoke the skill execution steps in `SKILL.md`.
- If bash tools are available, `scripts/audit_url.py` will be run directly.
- Report language is auto-detected from the target site's `<html lang>` attribute.
