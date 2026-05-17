# Codex — Installation & Usage

## Install

Codex reads `agents/openai.yaml` and `SKILL.md` for skill metadata and execution instructions.

```bash
git clone https://github.com/YOUR_USERNAME/google-seo-audit
# Point Codex to the skill directory in your project or global skills path
```

Or reference via URL in your Codex configuration:

```yaml
skills:
  - url: https://github.com/YOUR_USERNAME/google-seo-audit
```

## Invocation

Codex triggers the skill via natural language matching against the `triggers` in `SKILL.md`:

```
Audit https://example.com
Run a Google SEO audit on https://example.com
SEO audit https://example.com with PSI key AIzaSy...
```

## With parameters

```
Audit https://example.com using PSI key AIzaSy... and GSC file ./gsc-export.csv
```

Codex will extract `url`, `psi_key`, and `gsc_file` from the natural language input and pass them to the skill execution steps defined in `SKILL.md`.

## Notes

- Codex will attempt to run `scripts/audit_url.py` if the environment has Python available.
- If no Python runtime: Codex follows the manual execution steps in `SKILL.md` (Steps 1–10).
- The `agents/openai.yaml` file defines the skill metadata for Codex discovery.
