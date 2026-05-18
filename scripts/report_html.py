"""
HTML report generator for google-seo-audit.
Design: clean technical-documentation aesthetic — monospace accents,
purposeful color, no decoration for decoration's sake.
Self-contained single file, no external dependencies.
"""

from __future__ import annotations

from typing import Dict, List
from score_report import (
    Finding,
    STATUS_EMOJI,
    assemble_findings,
    _score_from_findings,
    _status_label,
)

# ---------------------------------------------------------------------------
# CSS — full inline stylesheet
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --bg:            #F7F6F2;
  --surface:       #FFFFFF;
  --border:        #E2E0D8;
  --border-light:  #EDECE7;

  --ink:           #18181A;
  --ink-2:         #4A4845;
  --ink-3:         #908C88;

  --accent:        #1F6FEB;

  --pass:          #16A34A;
  --pass-bg:       #F0FDF4;
  --pass-border:   #BBF7D0;
  --warn:          #CA8A04;
  --warn-bg:       #FEFCE8;
  --warn-border:   #FDE047;
  --fail:          #DC2626;
  --fail-bg:       #FEF2F2;
  --fail-border:   #FECACA;
  --need:          #2563EB;
  --need-bg:       #EFF6FF;
  --need-border:   #BFDBFE;

  --r:             5px;
  --mono: "SF Mono","Cascadia Code","Fira Code","Consolas","Courier New",monospace;
  --sans: -apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",Arial,
          "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
}

*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.65;
  color: var(--ink);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Header ─────────────────────────────────────────────────────── */

.hdr {
  background: #111115;
  color: #fff;
  border-bottom: 1px solid #2A2A2F;
}

.hdr-inner {
  max-width: 880px;
  margin: 0 auto;
  padding: 28px 28px 26px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.hdr-left { min-width: 0; }

.hdr-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.hdr-wordmark {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #4B6FEF;
  background: rgba(75,111,239,.12);
  padding: 2px 8px;
  border-radius: 3px;
}

.hdr-dot {
  width: 4px;
  height: 4px;
  background: #3A3A40;
  border-radius: 50%;
}

.hdr-date {
  font-family: var(--mono);
  font-size: 11px;
  color: #5A5A62;
  letter-spacing: .04em;
}

.hdr-url {
  font-family: var(--mono);
  font-size: 17px;
  font-weight: 500;
  color: #F0EEE8;
  word-break: break-all;
  line-height: 1.45;
  letter-spacing: -.01em;
}

.hdr-right {
  text-align: right;
  flex-shrink: 0;
}

.hdr-lang {
  font-size: 11px;
  color: #5A5A62;
  font-family: var(--mono);
}

/* ── Update banner ───────────────────────────────────────────────── */

.update-banner {
  max-width: 880px;
  margin: 20px auto 0;
  padding: 0 28px;
}

.update-inner {
  background: var(--warn-bg);
  border: 1px solid var(--warn-border);
  border-radius: var(--r);
  padding: 10px 14px;
  font-size: 13px;
  color: #713F12;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

/* ── Main layout ─────────────────────────────────────────────────── */

.wrap {
  max-width: 880px;
  margin: 0 auto;
  padding: 36px 28px 80px;
}

/* ── Section headings ────────────────────────────────────────────── */

.sec {
  margin-bottom: 48px;
}

.sec-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

.sec-n {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-3);
  letter-spacing: .06em;
  flex-shrink: 0;
}

.sec-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -.01em;
}

/* ── Score grid ──────────────────────────────────────────────────── */

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(152px, 1fr));
  gap: 10px;
}

.sc-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 16px 16px 14px;
  position: relative;
  overflow: hidden;
}

/* thin top accent bar */
.sc-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}
.sc-card.pass::before   { background: var(--pass); }
.sc-card.warning::before{ background: var(--warn); }
.sc-card.fail::before   { background: var(--fail); }
.sc-card.na::before     { background: var(--border); }

.sc-num {
  font-family: var(--mono);
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -.03em;
  margin-bottom: 10px;
}
.sc-num.pass    { color: var(--pass); }
.sc-num.warning { color: var(--warn); }
.sc-num.fail    { color: var(--fail); }
.sc-num.na      { color: var(--ink-3); }

.sc-track {
  height: 3px;
  background: var(--border-light);
  border-radius: 99px;
  margin-bottom: 9px;
  overflow: hidden;
}

.sc-fill {
  height: 100%;
  border-radius: 99px;
}
.sc-fill.pass    { background: var(--pass); }
.sc-fill.warning { background: var(--warn); }
.sc-fill.fail    { background: var(--fail); }
.sc-fill.na      { background: var(--border); }

.sc-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-3);
  line-height: 1.3;
  letter-spacing: .01em;
}

/* ── Severity groups ─────────────────────────────────────────────── */

.sev-group { margin-bottom: 20px; }

.sev-label {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 8px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.sev-label.high   { color: var(--fail); }
.sev-label.medium { color: var(--warn); }
.sev-label.low    { color: var(--pass); }

.sev-pill {
  background: currentColor;
  opacity: .15;
  width: 20px;
  height: 2px;
  border-radius: 99px;
}

.sev-count {
  margin-left: auto;
  font-family: var(--mono);
  font-size: 10px;
  opacity: .6;
}

/* ── Finding cards ───────────────────────────────────────────────── */

.fc {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid transparent;
  border-radius: var(--r);
  padding: 14px 16px;
  margin-bottom: 7px;
}
.fc.high   { border-left-color: var(--fail); }
.fc.medium { border-left-color: var(--warn); }
.fc.low    { border-left-color: var(--pass); }
.fc.data_needed { border-left-color: var(--need); }

.fc-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.fc-meta {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 4px;
}

.fc-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.4;
}

.fc-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  flex-shrink: 0;
  align-items: flex-start;
  justify-content: flex-end;
  padding-top: 2px;
}

.bdg {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid transparent;
  white-space: nowrap;
}

.bdg.s-pass     { background: var(--pass-bg);   color: var(--pass);  border-color: var(--pass-border); }
.bdg.s-warning  { background: var(--warn-bg);   color: var(--warn);  border-color: var(--warn-border); }
.bdg.s-fail     { background: var(--fail-bg);   color: var(--fail);  border-color: var(--fail-border); }
.bdg.s-unknown  { background: #F4F4F5; color: #71717A; border-color: #E4E4E7; }
.bdg.s-data_needed { background: var(--need-bg); color: var(--need); border-color: var(--need-border); }

.bdg.c-high   { background: #FFF7F7; color: #7F1D1D; border-color: #FECACA; }
.bdg.c-medium { background: #FEFCE8; color: #713F12; border-color: #FDE68A; }
.bdg.c-low    { background: #F0FDF4; color: #14532D; border-color: #BBF7D0; }

/* Finding rows: evidence / impact / fix */
.fc-body { font-size: 12.5px; color: var(--ink-2); }

.fc-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 8px;
  margin-bottom: 5px;
  align-items: baseline;
}
.fc-row:last-child { margin-bottom: 0; }

.fc-lbl {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink-3);
  padding-top: 1px;
}

.fc-val { line-height: 1.55; }

.fc-val.evidence {
  font-family: var(--mono);
  font-size: 11px;
  background: var(--bg);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-light);
  word-break: break-all;
  color: var(--ink-2);
}

.fc-val.fix { color: #15803D; font-weight: 500; }

/* ── Data-needed section ─────────────────────────────────────────── */

.dn-note {
  font-size: 12px;
  color: var(--ink-3);
  margin-bottom: 10px;
}

.dn-card {
  background: var(--need-bg);
  border: 1px solid var(--need-border);
  border-left: 3px solid var(--need);
  border-radius: var(--r);
  padding: 12px 14px;
  margin-bottom: 7px;
  font-size: 12.5px;
}

.dn-title { font-weight: 700; color: var(--need); margin-bottom: 4px; }
.dn-ev   { color: var(--ink-2); margin-bottom: 3px; }
.dn-fix  { color: #1D4ED8; font-size: 11.5px; }

/* ── Detail collapsibles ─────────────────────────────────────────── */

details {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  margin-bottom: 6px;
  overflow: hidden;
}

details summary {
  padding: 11px 14px;
  cursor: pointer;
  user-select: none;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--ink-2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  list-style: none;
  gap: 8px;
}
details summary::-webkit-details-marker { display: none; }
details[open] summary {
  border-bottom: 1px solid var(--border-light);
  color: var(--ink);
}

.arr {
  width: 14px;
  height: 14px;
  color: var(--ink-3);
  flex-shrink: 0;
  transition: transform .15s ease;
}
details[open] .arr { transform: rotate(90deg); }

.dt-row {
  display: grid;
  grid-template-columns: 36px 200px 1fr;
  border-bottom: 1px solid var(--border-light);
  font-size: 12px;
  align-items: baseline;
}
.dt-row:last-child { border-bottom: none; }
.dt-row:nth-child(even) { background: var(--bg); }

.dt-s  { padding: 8px 0 8px 14px; text-align: center; }
.dt-c  { padding: 8px 10px; font-weight: 600; color: var(--ink-2); }
.dt-e  {
  padding: 8px 14px 8px 0;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-3);
  word-break: break-word;
}

/* ── Disclaimer ──────────────────────────────────────────────────── */

.disc {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 14px 16px;
  margin-top: 40px;
}

.disc-title {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 8px;
}

.disc ul {
  padding-left: 16px;
  font-size: 11.5px;
  color: var(--ink-3);
  line-height: 1.75;
}

.foot {
  text-align: center;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-3);
  padding: 20px 0 0;
  letter-spacing: .02em;
}
.foot a { color: var(--accent); text-decoration: none; }

/* ── Print ───────────────────────────────────────────────────────── */

@media print {
  body { background: #fff; font-size: 12px; }
  .hdr { background: #111115 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .sc-card::before { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .sc-fill   { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .fc        { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .wrap { padding: 20px; }
  details { display: block !important; }
  details summary { display: none; }
  .sev-label, .fc-badges { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""

# SVG chevron (inline, no external dependency)
_CHEVRON = '<svg class="arr" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="5,3 11,8 5,13"/></svg>'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _status_bdg(status: str) -> str:
    labels = {
        "pass": "PASS",
        "warning": "WARN",
        "fail": "FAIL",
        "unknown": "N/A",
        "data_needed": "DATA",
    }
    return f'<span class="bdg s-{status}">{labels.get(status, status.upper())}</span>'


def _conf_bdg(conf: str, lang: str) -> str:
    if lang == "zh":
        labels = {"high": "高置信", "medium": "中置信", "low": "低置信"}
    else:
        labels = {"high": "CONF·H", "medium": "CONF·M", "low": "CONF·L"}
    return f'<span class="bdg c-{conf}">{labels.get(conf, conf.upper())}</span>'


def _score_card(module: str, score: int) -> str:
    lbl = _status_label(score)
    num = str(score) if score >= 0 else "—"
    pct = f"{min(score, 100)}%" if score >= 0 else "0%"
    return f"""
<div class="sc-card {lbl}">
  <div class="sc-num {lbl}">{num}</div>
  <div class="sc-track"><div class="sc-fill {lbl}" style="width:{pct}"></div></div>
  <div class="sc-label">{_esc(module)}</div>
</div>"""


def _finding_card(f: Finding, idx: int, lang: str) -> str:
    L = {
        "en": {"ev": "Evidence", "impact": "Impact", "fix": "Fix"},
        "zh": {"ev": "证据", "impact": "影响", "fix": "修复"},
    }.get(lang, {"ev": "Evidence", "impact": "Impact", "fix": "Fix"})

    fix_row = ""
    if f.fix:
        fix_row = f"""
      <div class="fc-row">
        <span class="fc-lbl">{L['fix']}</span>
        <span class="fc-val fix">{_esc(f.fix)}</span>
      </div>"""

    return f"""
<div class="fc {f.severity}">
  <div class="fc-head">
    <div>
      <div class="fc-meta">{_esc(f.module)}</div>
      <div class="fc-title">{idx}. {_esc(f.check.replace('_', ' ').title())}</div>
    </div>
    <div class="fc-badges">
      {_status_bdg(f.status)}
      {_conf_bdg(f.confidence, lang)}
    </div>
  </div>
  <div class="fc-body">
    <div class="fc-row">
      <span class="fc-lbl">{L['ev']}</span>
      <span class="fc-val evidence">{_esc(f.evidence)}</span>
    </div>
    <div class="fc-row">
      <span class="fc-lbl">{L['impact']}</span>
      <span class="fc-val">{_esc(f.impact)}</span>
    </div>{fix_row}
  </div>
</div>"""


def _detail_block(module: str, findings: List[Finding]) -> str:
    rows = "".join(f"""
    <div class="dt-row">
      <div class="dt-s">{STATUS_EMOJI.get(f.status, '')}</div>
      <div class="dt-c">{_esc(f.check)}</div>
      <div class="dt-e">{_esc(f.evidence)}</div>
    </div>""" for f in findings)
    return f"""
<details>
  <summary>{_esc(module)}{_CHEVRON}</summary>
  {rows}
</details>"""


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_html_report(audit_data: Dict, language: str = "en") -> str:
    url          = audit_data.get("url", "")
    date         = audit_data.get("date", "")
    lang_tag     = audit_data.get("detected_language", language)
    update_text  = audit_data.get("_update_notice", "").strip()

    all_module_findings = assemble_findings(audit_data)
    scores = {mod: _score_from_findings(f) for mod, f in all_module_findings.items()}

    # Sort priority findings
    _sev = {"high": 0, "medium": 1, "low": 2}
    _sta = {"fail": 0, "warning": 1, "unknown": 2, "pass": 3}
    prio = sorted(
        [f for flist in all_module_findings.values() for f in flist
         if f.status in ("fail", "warning", "unknown")],
        key=lambda f: (_sev.get(f.severity, 9), _sta.get(f.status, 9)),
    )
    dn = [f for flist in all_module_findings.values() for f in flist
          if f.status == "data_needed"]

    lang = language

    # ── i18n strings ──────────────────────────────────────────────
    if lang == "zh":
        brand       = "SEO 诊断"
        lbl_target  = "目标"
        lbl_date    = "日期"
        lbl_lang    = f"语言：{lang_tag}"
        s_summary   = "总览"
        s_priority  = "优先修复"
        s_detail    = "模块详情"
        s_dn        = "数据待补充"
        dn_note     = "以下检测因数据缺失未能运行，不代表网站存在问题。"
        dn_how      = "解决："
        sev_lbl     = {"high": "高优先级 — 立即修复", "medium": "中优先级 — 本月处理", "low": "低优先级 — 持续改进"}
        disc_head   = "免责说明"
        disc_items  = [
            "site: 查询结果为估算值；精确收录量请查阅 GSC 覆盖率报告。",
            "域名年龄仅为历史信任参考，非直接排名因子。",
            "E-E-A-T 信号为表层扫描，置信度为中等。",
            "DA/DR 权威评分无法从 GSC 获取，请使用 Ahrefs/Moz/Semrush。",
        ]
        footer_link = f'由 <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a> 生成'
        no_issues   = "未发现问题。"
    else:
        brand       = "SEO Audit"
        lbl_target  = "Target"
        lbl_date    = "Date"
        lbl_lang    = f"lang: {lang_tag}"
        s_summary   = "Summary"
        s_priority  = "Priority Fixes"
        s_detail    = "Module Detail"
        s_dn        = "Data Needed"
        dn_note     = "These checks couldn't run due to missing data — not site errors."
        dn_how      = "How to fix:"
        sev_lbl     = {"high": "High — Fix immediately", "medium": "Medium — Fix this month", "low": "Low — Continuous improvement"}
        disc_head   = "Disclaimer"
        disc_items  = [
            "site: results are estimates; use GSC Coverage for precise index counts.",
            "Domain age is a historical trust signal, not a direct ranking factor.",
            "E-E-A-T findings are surface-level; confidence is medium.",
            "DA/DR scores require Ahrefs/Moz/Semrush — unavailable from GSC.",
        ]
        footer_link = f'Generated by <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a>'
        no_issues   = "No issues found."

    # ── Sub-components ─────────────────────────────────────────────

    update_html = ""
    if update_text:
        update_html = f"""
<div class="update-banner">
  <div class="update-inner">⬆ {_esc(update_text)}</div>
</div>"""

    score_cards = "".join(_score_card(mod, s) for mod, s in scores.items())

    # Priority list grouped by severity
    groups: dict = {"high": [], "medium": [], "low": []}
    for f in prio:
        groups.setdefault(f.severity, []).append(f)

    prio_html = ""
    counter = 1
    for sev in ("high", "medium", "low"):
        items = groups.get(sev, [])
        if not items:
            continue
        cards = "".join(_finding_card(f, counter + i, lang) for i, f in enumerate(items))
        counter += len(items)
        prio_html += f"""
<div class="sev-group">
  <div class="sev-label {sev}">
    <span class="sev-pill"></span>
    {sev_lbl[sev]}
    <span class="sev-count">{len(items)}</span>
  </div>
  {cards}
</div>"""

    if not prio_html:
        prio_html = f'<p style="font-size:13px;color:var(--ink-3)">{no_issues}</p>'

    # Data-needed
    dn_html = ""
    if dn:
        dn_cards = "".join(f"""
<div class="dn-card">
  <div class="dn-title">{i+1}. [{_esc(f.module)}] {_esc(f.check)}</div>
  <div class="dn-ev">{_esc(f.evidence)}</div>
  <div class="dn-fix">{_esc(dn_how)} {_esc(f.fix or '')}</div>
</div>""" for i, f in enumerate(dn))
        dn_html = f"""
<div class="sec">
  <div class="sec-head">
    <span class="sec-n">04</span>
    <span class="sec-title">📊 {s_dn}</span>
  </div>
  <p class="dn-note">{dn_note}</p>
  {dn_cards}
</div>"""

    detail_blocks = "".join(
        _detail_block(mod, findings)
        for mod, findings in all_module_findings.items()
    )

    disc_items_html = "".join(f"<li>{_esc(it)}</li>" for it in disc_items)

    # ── Final assembly ─────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{brand} — {_esc(url)}</title>
<style>{_CSS}</style>
</head>
<body>

<header class="hdr">
  <div class="hdr-inner">
    <div class="hdr-left">
      <div class="hdr-eyebrow">
        <span class="hdr-wordmark">{brand}</span>
        <span class="hdr-dot"></span>
        <span class="hdr-date">{_esc(date)}</span>
      </div>
      <div class="hdr-url">{_esc(url)}</div>
    </div>
    <div class="hdr-right">
      <div class="hdr-lang">{_esc(lbl_lang)}</div>
    </div>
  </div>
</header>

{update_html}

<div class="wrap">

  <div class="sec">
    <div class="sec-head">
      <span class="sec-n">01</span>
      <span class="sec-title">{s_summary}</span>
    </div>
    <div class="score-grid">{score_cards}</div>
  </div>

  <div class="sec">
    <div class="sec-head">
      <span class="sec-n">02</span>
      <span class="sec-title">{s_priority}</span>
    </div>
    {prio_html}
  </div>

  {dn_html}

  <div class="sec">
    <div class="sec-head">
      <span class="sec-n">{"05" if dn else "03"}</span>
      <span class="sec-title">{s_detail}</span>
    </div>
    {detail_blocks}
  </div>

  <div class="disc">
    <div class="disc-title">{disc_head}</div>
    <ul>{disc_items_html}</ul>
  </div>

  <div class="foot">{footer_link}</div>

</div>
</body>
</html>"""
