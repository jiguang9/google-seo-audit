"""
HTML report generator for google-seo-audit.
Produces a self-contained, single-file HTML report with inline CSS.
No external dependencies — works offline.
"""

from __future__ import annotations

from typing import Dict, List
from score_report import (
    Finding,
    STATUS_EMOJI,
    SEVERITY_EMOJI,
    assemble_findings,
    _score_from_findings,
    _status_label,
)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

_COLOR = {
    "pass":        {"bg": "#dcfce7", "text": "#15803d", "border": "#86efac"},
    "warning":     {"bg": "#fef9c3", "text": "#a16207", "border": "#fde047"},
    "fail":        {"bg": "#fee2e2", "text": "#b91c1c", "border": "#fca5a5"},
    "unknown":     {"bg": "#f3f4f6", "text": "#4b5563", "border": "#d1d5db"},
    "data_needed": {"bg": "#eff6ff", "text": "#1d4ed8", "border": "#93c5fd"},
    "high":        "#ef4444",
    "medium":      "#f59e0b",
    "low":         "#22c55e",
}

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  line-height: 1.6;
  font-size: 15px;
}

.container { max-width: 960px; margin: 0 auto; padding: 24px 16px 60px; }

/* ── Header ─────────────────────────────────────────────── */
.report-header {
  background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%);
  color: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  margin-bottom: 28px;
}
.report-header h1 { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
.report-header .meta { font-size: 13px; opacity: 0.85; display: flex; gap: 20px; flex-wrap: wrap; }
.report-header .meta span::before { content: "• "; opacity: 0.6; }
.report-header .meta span:first-child::before { content: ""; }

.update-banner {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #92400e;
}

/* ── Summary cards ───────────────────────────────────────── */
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 28px 0 14px;
  padding-bottom: 6px;
  border-bottom: 2px solid #e2e8f0;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 8px;
}

.score-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}

.score-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}
.score-circle.pass    { background: #dcfce7; color: #15803d; }
.score-circle.warning { background: #fef9c3; color: #a16207; }
.score-circle.fail    { background: #fee2e2; color: #b91c1c; }
.score-circle.na      { background: #f1f5f9; color: #64748b; }

.score-info { min-width: 0; }
.score-info .mod-name { font-weight: 600; font-size: 13px; color: #475569; line-height: 1.3; }
.score-info .score-label { font-size: 20px; font-weight: 700; color: #1e293b; }

/* ── Priority list ───────────────────────────────────────── */
.severity-group { margin-bottom: 24px; }

.severity-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
  cursor: pointer;
  user-select: none;
}
.severity-header .badge-count {
  background: #e2e8f0;
  color: #475569;
  border-radius: 999px;
  padding: 1px 9px;
  font-size: 12px;
  font-weight: 600;
}
.severity-header .toggle-icon { margin-left: auto; color: #94a3b8; font-size: 12px; }

.finding-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px 18px;
  margin-bottom: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.finding-card.high    { border-left-color: #ef4444; }
.finding-card.medium  { border-left-color: #f59e0b; }
.finding-card.low     { border-left-color: #22c55e; }
.finding-card.data_needed { border-left-color: #3b82f6; }

.finding-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.finding-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.finding-module { font-size: 11px; color: #64748b; font-weight: 500; margin-top: 2px; }

.badges { display: flex; gap: 6px; flex-wrap: wrap; flex-shrink: 0; }
.badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}
.badge.status-pass    { background: #dcfce7; color: #15803d; }
.badge.status-warning { background: #fef9c3; color: #a16207; }
.badge.status-fail    { background: #fee2e2; color: #b91c1c; }
.badge.status-unknown { background: #f1f5f9; color: #64748b; }
.badge.status-data_needed { background: #dbeafe; color: #1d4ed8; }
.badge.conf-high   { background: #f0fdf4; color: #166534; }
.badge.conf-medium { background: #fffbeb; color: #92400e; }
.badge.conf-low    { background: #fef2f2; color: #991b1b; }

.finding-body { font-size: 13px; }
.finding-body .row { display: flex; gap: 8px; margin-bottom: 5px; align-items: baseline; }
.finding-body .label { color: #64748b; font-weight: 600; min-width: 72px; flex-shrink: 0; }
.finding-body .value { color: #334155; }
.finding-body .fix-value { color: #15803d; font-weight: 500; }

/* ── Detail table ────────────────────────────────────────── */
details { margin-bottom: 12px; }
details summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  color: #475569;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
details summary::-webkit-details-marker { display: none; }
details[open] summary { border-radius: 8px 8px 0 0; border-bottom-color: transparent; }
details summary .arrow { margin-left: auto; color: #94a3b8; transition: transform .2s; }
details[open] summary .arrow { transform: rotate(90deg); }

.detail-table {
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}
.detail-row {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}
.detail-row:last-child { border-bottom: none; }
.detail-row:nth-child(even) { background: #f8fafc; }
.detail-row .dc-status { width: 44px; padding: 10px 12px; text-align: center; flex-shrink: 0; }
.detail-row .dc-check { width: 200px; padding: 10px 12px; font-weight: 600; color: #334155; flex-shrink: 0; }
.detail-row .dc-evidence { flex: 1; padding: 10px 12px; color: #475569; }

/* ── Data needed section ─────────────────────────────────── */
.data-needed-card {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 10px;
  font-size: 13px;
}
.data-needed-card .dn-title { font-weight: 600; color: #1d4ed8; margin-bottom: 6px; }
.data-needed-card .dn-row { color: #334155; margin-bottom: 4px; }
.data-needed-card .dn-fix { color: #1d4ed8; }

/* ── Disclaimer ──────────────────────────────────────────── */
.disclaimer {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 12px;
  color: #64748b;
  margin-top: 32px;
}
.disclaimer ul { padding-left: 18px; }
.disclaimer li { margin-bottom: 3px; }
.footer { text-align: center; font-size: 12px; color: #94a3b8; margin-top: 20px; }
.footer a { color: #3b82f6; text-decoration: none; }

@media print {
  body { background: #fff; }
  .container { max-width: 100%; padding: 0; }
  .report-header { border-radius: 0; }
  details { display: block; }
  details summary { display: none; }
  .detail-table { border: 1px solid #e2e8f0; border-radius: 4px; }
}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _status_badge(status: str) -> str:
    labels = {
        "pass": "PASS", "warning": "WARNING", "fail": "FAIL",
        "unknown": "UNKNOWN", "data_needed": "DATA NEEDED",
    }
    label = labels.get(status, status.upper())
    return f'<span class="badge status-{status}">{label}</span>'


def _conf_badge(confidence: str, lang: str) -> str:
    conf_labels_zh = {"high": "可信度：高", "medium": "可信度：中", "low": "可信度：低"}
    conf_labels_en = {"high": "Confidence: high", "medium": "Confidence: med", "low": "Confidence: low"}
    labels = conf_labels_zh if lang == "zh" else conf_labels_en
    label = labels.get(confidence, confidence)
    return f'<span class="badge conf-{confidence}">{_esc(label)}</span>'


def _score_card(module: str, score: int, lang: str) -> str:
    label = _status_label(score)
    score_display = str(score) if score >= 0 else "—"
    return f"""
    <div class="score-card">
      <div class="score-circle {label}">{score_display}</div>
      <div class="score-info">
        <div class="mod-name">{_esc(module)}</div>
        <div class="score-label">{score_display}/100</div>
      </div>
    </div>"""


def _finding_card(f: Finding, idx: int, lang: str) -> str:
    labels = {
        "en": {"evidence": "Evidence", "impact": "Impact", "fix": "Fix"},
        "zh": {"evidence": "证据", "impact": "影响", "fix": "修复建议"},
    }
    L = labels.get(lang, labels["en"])

    fix_html = ""
    if f.fix:
        fix_html = f"""
        <div class="row">
          <span class="label">✅ {L['fix']}:</span>
          <span class="fix-value">{_esc(f.fix)}</span>
        </div>"""

    return f"""
    <div class="finding-card {_esc(f.severity)}">
      <div class="finding-top">
        <div>
          <div class="finding-title">{idx}. {_esc(f.check.replace('_', ' ').title())}</div>
          <div class="finding-module">{_esc(f.module)}</div>
        </div>
        <div class="badges">
          {_status_badge(f.status)}
          {_conf_badge(f.confidence, lang)}
        </div>
      </div>
      <div class="finding-body">
        <div class="row">
          <span class="label">{L['evidence']}:</span>
          <span class="value">{_esc(f.evidence)}</span>
        </div>
        <div class="row">
          <span class="label">{L['impact']}:</span>
          <span class="value">{_esc(f.impact)}</span>
        </div>
        {fix_html}
      </div>
    </div>"""


def _detail_section(module: str, findings: List[Finding], lang: str) -> str:
    rows = ""
    for f in findings:
        rows += f"""
        <div class="detail-row">
          <div class="dc-status">{STATUS_EMOJI.get(f.status, '')}</div>
          <div class="dc-check">{_esc(f.check)}</div>
          <div class="dc-evidence">{_esc(f.evidence)}</div>
        </div>"""

    return f"""
    <details>
      <summary>
        {_esc(module)}
        <span class="arrow">▶</span>
      </summary>
      <div class="detail-table">{rows}</div>
    </details>"""


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_html_report(audit_data: Dict, language: str = "en") -> str:
    url = audit_data.get("url", "")
    date = audit_data.get("date", "")
    lang_detected = audit_data.get("detected_language", "en")
    update_banner_text = audit_data.get("_update_notice", "")

    all_module_findings = assemble_findings(audit_data)
    scores = {mod: _score_from_findings(findings) for mod, findings in all_module_findings.items()}

    # Sort priority findings
    severity_order = {"high": 0, "medium": 1, "low": 2}
    status_order   = {"fail": 0, "warning": 1, "unknown": 2, "pass": 3}
    priority_findings = [
        f for findings in all_module_findings.values()
        for f in findings if f.status in ("fail", "warning", "unknown")
    ]
    priority_findings.sort(key=lambda f: (severity_order.get(f.severity, 9), status_order.get(f.status, 9)))

    data_needed_findings = [
        f for findings in all_module_findings.values()
        for f in findings if f.status == "data_needed"
    ]

    lang = language

    # ── Localisation strings ──────────────────────────────────
    if lang == "zh":
        title_str       = f"Google SEO 诊断报告 — {_esc(url)}"
        heading_str     = "Google SEO 诊断报告"
        meta_url        = f"目标：{_esc(url)}"
        meta_date       = f"日期：{date}"
        meta_lang       = f"语言：{lang_detected}"
        summary_title   = "📊 总览"
        priority_title  = "🔧 优先修复清单"
        detail_title    = "📋 各模块详细诊断"
        dn_title        = "📊 数据待补充"
        dn_subtitle     = "以下检测项因数据缺失未能运行，不代表网站存在问题。"
        dn_how          = "解决方式："
        sev_labels      = {"high": "🔴 高优先级（立即修复）", "medium": "🟡 中优先级（本月内处理）", "low": "🟢 低优先级（持续改进）"}
        disc_title      = "免责说明"
        disc_items      = [
            "site: 指令结果仅为估算，非精确收录量；请使用 GSC 覆盖率报告获取准确数据。",
            "域名年龄为历史信任参考，非直接排名因子。",
            "E-E-A-T 信号为页面表层扫描，可信度为中。",
            "DA/DR 权威评分无法从 GSC 获取；请使用 Ahrefs/Moz/Semrush 导出数据。",
        ]
        footer_str      = f'由 <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a> 生成'
    else:
        title_str       = f"Google SEO Audit Report — {_esc(url)}"
        heading_str     = "Google SEO Audit Report"
        meta_url        = f"Target: {_esc(url)}"
        meta_date       = f"Date: {date}"
        meta_lang       = f"Language: {lang_detected}"
        summary_title   = "📊 Summary"
        priority_title  = "🔧 Priority Fix List"
        detail_title    = "📋 Detailed Module Reports"
        dn_title        = "📊 Data Needed"
        dn_subtitle     = "These checks could not run because data was unavailable. They are not site errors."
        dn_how          = "How to fix:"
        sev_labels      = {"high": "🔴 High Severity — Fix immediately", "medium": "🟡 Medium Severity — Fix this month", "low": "🟢 Low Severity — Continuous improvement"}
        disc_title      = "Disclaimer"
        disc_items      = [
            "site: operator results are rough estimates; use GSC Coverage for precise index counts.",
            "Domain age is a historical trust indicator, not a direct ranking factor.",
            "E-E-A-T findings are surface-level with medium confidence.",
            "DA/DR scores are unavailable from GSC; use Ahrefs/Moz/Semrush for authority data.",
        ]
        footer_str      = f'Generated by <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a>'

    # ── Update banner ────────────────────────────────────────
    update_html = ""
    if update_banner_text:
        update_html = f'<div class="update-banner">⬆️ {_esc(update_banner_text.strip())}</div>'

    # ── Score cards ──────────────────────────────────────────
    score_cards = "".join(_score_card(mod, s, lang) for mod, s in scores.items())

    # ── Priority list ────────────────────────────────────────
    groups: Dict[str, List] = {"high": [], "medium": [], "low": []}
    for f in priority_findings:
        groups.setdefault(f.severity, []).append(f)

    priority_html = ""
    counter = 1
    for sev in ("high", "medium", "low"):
        items = groups.get(sev, [])
        if not items:
            continue
        cards_html = ""
        for f in items:
            cards_html += _finding_card(f, counter, lang)
            counter += 1
        priority_html += f"""
        <div class="severity-group">
          <div class="severity-header">
            <span>{sev_labels[sev]}</span>
            <span class="badge-count">{len(items)}</span>
          </div>
          {cards_html}
        </div>"""

    # ── Data needed ──────────────────────────────────────────
    dn_html = ""
    if data_needed_findings:
        dn_cards = ""
        for i, f in enumerate(data_needed_findings, 1):
            dn_cards += f"""
            <div class="data-needed-card">
              <div class="dn-title">{i}. [{_esc(f.module)}] {_esc(f.check)}</div>
              <div class="dn-row">{_esc(f.evidence)}</div>
              <div class="dn-row dn-fix">{_esc(dn_how)} {_esc(f.fix or '')}</div>
            </div>"""
        dn_html = f"""
        <div class="section-title">{dn_title}</div>
        <p style="font-size:13px;color:#475569;margin-bottom:12px;">{dn_subtitle}</p>
        {dn_cards}"""

    # ── Detail sections ──────────────────────────────────────
    details_html = "".join(
        _detail_section(mod, findings, lang)
        for mod, findings in all_module_findings.items()
    )

    # ── Disclaimer ───────────────────────────────────────────
    disc_items_html = "".join(f"<li>{_esc(item)}</li>" for item in disc_items)
    disclaimer_html = f"""
    <div class="disclaimer">
      <strong>{disc_title}</strong>
      <ul style="margin-top:6px;">{disc_items_html}</ul>
    </div>"""

    # ── Assemble ─────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_str}</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="container">

  {update_html}

  <div class="report-header">
    <h1>{heading_str}</h1>
    <div class="meta">
      <span>{meta_url}</span>
      <span>{meta_date}</span>
      <span>{meta_lang}</span>
    </div>
  </div>

  <div class="section-title">{summary_title}</div>
  <div class="score-grid">{score_cards}</div>

  <div class="section-title">{priority_title}</div>
  {priority_html if priority_html else '<p style="color:#64748b;font-size:13px;">No issues found.</p>'}

  {dn_html}

  <div class="section-title">{detail_title}</div>
  {details_html}

  {disclaimer_html}
  <div class="footer">{footer_str}</div>

</div>
</body>
</html>"""
