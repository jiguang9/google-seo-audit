"""
HTML report generator — consulting-report aesthetic.
Cover-first document layout, generous whitespace, strong visual hierarchy.
Self-contained single file, no external dependencies, bilingual EN/ZH.
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
# CSS  (plain string — single braces are fine here, NOT an f-string)
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --navy:      #142030;
  --navy-2:    #1D3148;
  --accent:    #C94B1F;
  --page:      #F6F5F1;
  --white:     #FFFFFF;
  --card-br:   #E5E0D6;
  --row-br:    #EDEAE3;

  --ink:       #1A1917;
  --ink-2:     #4A4640;
  --ink-3:     #9A9590;
  --ink-4:     #C8C2BA;

  --fail:      #B91C1C;
  --fail-lt:   #FEF2F2;
  --fail-ring: #FCA5A5;
  --warn:      #A16207;
  --warn-lt:   #FEFCE8;
  --warn-ring: #FDE047;
  --pass:      #15803D;
  --pass-lt:   #F0FDF4;
  --pass-ring: #6EE7B7;
  --need:      #1D4ED8;
  --need-lt:   #EFF6FF;
  --need-ring: #93C5FD;

  --serif: Georgia,"Palatino Linotype","Times New Roman",
           "Songti SC","STSong","FangSong","SimSun", serif;
  --sans:  -apple-system,BlinkMacSystemFont,"Segoe UI",
           "PingFang SC","Hiragino Sans GB","Microsoft YaHei",
           "Noto Sans CJK SC","WenQuanYi Micro Hei", sans-serif;
  --mono:  "SF Mono","Fira Code","Cascadia Code","Consolas",
           "Courier New", monospace;

  --sh-card: 0 2px 12px rgba(0,0,0,.07), 0 1px 3px rgba(0,0,0,.05);
  --sh-sm:   0 1px 4px rgba(0,0,0,.06);
}

*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 16px; }

body {
  font-family: var(--sans);
  font-size: .875rem;
  line-height: 1.7;
  color: var(--ink);
  background: var(--page);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── COVER ───────────────────────────────────────────────────── */

.cover {
  background: var(--navy);
  position: relative;
}

.cover-accent {
  height: 4px;
  background: var(--accent);
}

.cover-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 64px 56px 56px;
}

.cover-kicker {
  font-family: var(--mono);
  font-size: .5625rem;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: rgba(255,255,255,.28);
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.cover-kicker::after {
  content: "";
  flex: 1;
  height: 1px;
  background: rgba(255,255,255,.1);
}

.cover-title {
  font-family: var(--serif);
  font-size: 2.5rem;
  font-weight: 700;
  color: #FFFFFF;
  line-height: 1.15;
  letter-spacing: -.02em;
  margin-bottom: 6px;
}

.cover-subtitle {
  font-family: var(--serif);
  font-size: 1rem;
  font-style: italic;
  color: rgba(255,255,255,.42);
  margin-bottom: 40px;
}

.cover-url-block {
  background: rgba(255,255,255,.055);
  border: 1px solid rgba(255,255,255,.1);
  border-left: 3px solid var(--accent);
  border-radius: 5px;
  padding: 14px 18px;
  margin-bottom: 48px;
}

.cover-url-label {
  font-family: var(--mono);
  font-size: .5rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: rgba(255,255,255,.3);
  margin-bottom: 5px;
}

.cover-url-value {
  font-family: var(--mono);
  font-size: .9375rem;
  color: rgba(255,255,255,.9);
  word-break: break-all;
  line-height: 1.55;
}

.cover-meta-row {
  display: flex;
  gap: 48px;
  flex-wrap: wrap;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,.1);
}

.cover-meta-item {}

.cover-meta-label {
  font-family: var(--mono);
  font-size: .5rem;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: rgba(255,255,255,.28);
  margin-bottom: 4px;
}

.cover-meta-value {
  font-family: var(--mono);
  font-size: .8125rem;
  color: rgba(255,255,255,.7);
}

/* ── UPDATE BANNER ───────────────────────────────────────────── */

.banner-wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 56px 0;
}

.banner {
  background: var(--warn-lt);
  border: 1px solid var(--warn-ring);
  border-radius: 5px;
  padding: 10px 14px;
  font-size: .8125rem;
  color: #713F12;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

/* ── CONTENT ─────────────────────────────────────────────────── */

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 64px 56px 96px;
}

/* ── SECTION BLOCKS ──────────────────────────────────────────── */

.section {
  margin-bottom: 72px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  gap: 0;
  margin-bottom: 32px;
  padding-bottom: 18px;
  border-bottom: 2px solid var(--card-br);
  position: relative;
}

/* decorative large section number behind title */
.section-num {
  font-family: var(--serif);
  font-size: 4.5rem;
  font-weight: 700;
  color: var(--row-br);
  line-height: 1;
  letter-spacing: -.04em;
  margin-right: 18px;
  margin-top: -8px;
  flex-shrink: 0;
  user-select: none;
}

.section-text {}

.section-eyebrow {
  font-family: var(--mono);
  font-size: .5625rem;
  font-weight: 700;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 5px;
}

.section-title {
  font-family: var(--serif);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -.02em;
  line-height: 1.2;
}

/* ── SCORE GRID ──────────────────────────────────────────────── */

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
  gap: 18px;
}

.score-card {
  background: var(--white);
  border: 1px solid var(--card-br);
  border-radius: 10px;
  padding: 28px 18px 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  box-shadow: var(--sh-card);
  text-align: center;
}

/* conic-gradient ring: --score (0-100 number), --clr (hex color) */
.score-ring {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: conic-gradient(
    var(--clr) calc(var(--score) * 1%),
    var(--row-br) calc(var(--score) * 1%)
  );
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-donut {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-number {
  font-family: var(--serif);
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -.03em;
}
.score-number.pass    { color: var(--pass); }
.score-number.warning { color: var(--warn); }
.score-number.fail    { color: var(--fail); }
.score-number.na      { color: var(--ink-3); }

.score-module {
  font-size: .75rem;
  font-weight: 600;
  color: var(--ink-3);
  line-height: 1.35;
}

/* ── SEVERITY GROUP HEADERS ──────────────────────────────────── */

.sev-group {
  margin-bottom: 32px;
}

.sev-group-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 6px;
  margin-bottom: 14px;
}
.sev-group-head.high   { background: var(--fail-lt); border-left: 4px solid var(--fail); }
.sev-group-head.medium { background: var(--warn-lt); border-left: 4px solid var(--warn); }
.sev-group-head.low    { background: var(--pass-lt); border-left: 4px solid var(--pass); }

.sev-group-icon {
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
}

.sev-group-label {
  font-size: .6875rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
  flex: 1;
}
.sev-group-head.high   .sev-group-label { color: var(--fail); }
.sev-group-head.medium .sev-group-label { color: var(--warn); }
.sev-group-head.low    .sev-group-label { color: var(--pass); }

.sev-group-count {
  font-family: var(--mono);
  font-size: .6875rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 99px;
  letter-spacing: .02em;
}
.sev-group-head.high   .sev-group-count { background: var(--fail-ring); color: #7F1D1D; }
.sev-group-head.medium .sev-group-count { background: var(--warn-ring); color: #713F12; }
.sev-group-head.low    .sev-group-count { background: var(--pass-ring); color: #14532D; }

/* ── FINDING CARDS ───────────────────────────────────────────── */

.fc {
  background: var(--white);
  border: 1px solid var(--card-br);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: var(--sh-sm);
}

/* colored left stripe + top header bar */
.fc-head {
  display: flex;
  border-bottom: 1px solid var(--row-br);
}

.fc-stripe {
  width: 5px;
  flex-shrink: 0;
  border-radius: 0;
}
.fc.high        .fc-stripe { background: var(--fail); }
.fc.medium      .fc-stripe { background: var(--warn); }
.fc.low         .fc-stripe { background: var(--pass); }
.fc.data_needed .fc-stripe { background: var(--need); }

.fc-head-content {
  flex: 1;
  padding: 16px 18px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.fc-index-module {
  font-family: var(--mono);
  font-size: .5625rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: 5px;
}
.fc.high   .fc-index-module { color: var(--fail); }
.fc.medium .fc-index-module { color: var(--warn); }
.fc.low    .fc-index-module { color: var(--pass); }
.fc.data_needed .fc-index-module { color: var(--need); }

.fc-check-name {
  font-family: var(--serif);
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.3;
  letter-spacing: -.01em;
}

.fc-badges {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  flex-shrink: 0;
  align-items: flex-start;
  justify-content: flex-end;
  padding-top: 2px;
}

.badge {
  font-family: var(--mono);
  font-size: .5rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 3px;
  border: 1px solid transparent;
  white-space: nowrap;
}
.badge.s-pass    { background: var(--pass-lt);  color: var(--pass);  border-color: var(--pass-ring); }
.badge.s-warning { background: var(--warn-lt);  color: var(--warn);  border-color: var(--warn-ring); }
.badge.s-fail    { background: var(--fail-lt);  color: var(--fail);  border-color: var(--fail-ring); }
.badge.s-unknown { background: #F4F4F5; color: #52525B; border-color: #E4E4E7; }
.badge.s-data_needed { background: var(--need-lt); color: var(--need); border-color: var(--need-ring); }
.badge.c-high    { background: #FFF7ED; color: #9A3412; border-color: #FED7AA; }
.badge.c-medium  { background: var(--warn-lt); color: #78350F; border-color: var(--warn-ring); }
.badge.c-low     { background: var(--fail-lt); color: #9F1239; border-color: var(--fail-ring); }

/* Finding body rows */
.fc-body {
  padding: 18px 18px 0 23px;  /* 23 = 5px stripe + 18px padding */
}

.fc-field {
  margin-bottom: 14px;
}

.fc-field-label {
  font-family: var(--mono);
  font-size: .5rem;
  font-weight: 800;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 5px;
}

.fc-field-value {
  font-size: .8125rem;
  color: var(--ink-2);
  line-height: 1.6;
}

.fc-field-value.evidence {
  font-family: var(--mono);
  font-size: .75rem;
  color: var(--ink-2);
  background: var(--page);
  border: 1px solid var(--card-br);
  border-radius: 4px;
  padding: 9px 13px;
  word-break: break-all;
  white-space: pre-wrap;
  line-height: 1.55;
}

/* Fix block — distinct green callout at bottom */
.fc-fix-block {
  margin: 0;
  padding: 14px 18px 16px 23px;
  background: var(--pass-lt);
  border-top: 1px solid var(--pass-ring);
}

.fc-fix-label {
  font-family: var(--mono);
  font-size: .5rem;
  font-weight: 800;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: var(--pass);
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.fc-fix-label::before {
  content: "→";
  font-style: normal;
}

.fc-fix-value {
  font-size: .8125rem;
  color: #14532D;
  font-weight: 500;
  line-height: 1.6;
}

/* ── DATA NEEDED ─────────────────────────────────────────────── */

.dn-intro {
  background: var(--need-lt);
  border: 1px solid var(--need-ring);
  border-radius: 5px;
  padding: 11px 16px;
  font-size: .8125rem;
  color: #1E3A8A;
  margin-bottom: 14px;
}

.dn-card {
  background: var(--white);
  border: 1px solid var(--card-br);
  border-left: 5px solid var(--need);
  border-radius: 7px;
  padding: 16px 18px;
  margin-bottom: 10px;
  box-shadow: var(--sh-sm);
}

.dn-card-title  { font-weight: 700; font-size: .9rem; color: var(--need); margin-bottom: 7px; }
.dn-card-ev     { font-size: .8125rem; color: var(--ink-2); margin-bottom: 5px; }
.dn-card-fix    { font-size: .75rem; color: #1E40AF; font-weight: 500; }

/* ── DETAIL SECTIONS (collapsible) ───────────────────────────── */

.details-wrap { margin-top: 4px; }

details {
  background: var(--white);
  border: 1px solid var(--card-br);
  border-radius: 7px;
  margin-bottom: 8px;
  overflow: hidden;
}

details summary {
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: .875rem;
  font-weight: 700;
  color: var(--ink-2);
}
details summary::-webkit-details-marker { display: none; }
details[open] summary {
  color: var(--ink);
  border-bottom: 1px solid var(--row-br);
  background: #FAFAF7;
}

.chev {
  width: 15px;
  height: 15px;
  color: var(--ink-3);
  flex-shrink: 0;
  transition: transform .15s ease;
}
details[open] .chev { transform: rotate(90deg); }

.dt-row {
  display: grid;
  grid-template-columns: 40px 220px 1fr;
  border-bottom: 1px solid var(--row-br);
  font-size: .75rem;
  align-items: baseline;
}
.dt-row:last-child   { border-bottom: none; }
.dt-row:nth-child(even) { background: var(--page); }

.dt-s { padding: 9px 0 9px 14px; text-align: center; }
.dt-c { padding: 9px 10px; font-weight: 600; color: var(--ink-2); }
.dt-e {
  padding: 8px 16px 8px 0;
  font-family: var(--mono);
  font-size: .6875rem;
  color: var(--ink-3);
  word-break: break-word;
  line-height: 1.5;
}

/* ── DISCLAIMER ──────────────────────────────────────────────── */

.disc {
  margin-top: 56px;
  background: var(--white);
  border: 1px solid var(--card-br);
  border-radius: 7px;
  padding: 20px 24px;
}

.disc-label {
  font-family: var(--mono);
  font-size: .5rem;
  font-weight: 700;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 10px;
}

.disc ul {
  padding-left: 18px;
  font-size: .75rem;
  color: var(--ink-3);
  line-height: 1.85;
}

.foot {
  margin-top: 28px;
  padding-bottom: 8px;
  text-align: center;
  font-family: var(--mono);
  font-size: .625rem;
  letter-spacing: .05em;
  color: var(--ink-4);
}
.foot a { color: #2563EB; text-decoration: none; }

/* ── EMPTY STATE ─────────────────────────────────────────────── */

.no-issues {
  text-align: center;
  padding: 40px;
  color: var(--ink-3);
  font-size: .875rem;
  background: var(--white);
  border: 1px solid var(--card-br);
  border-radius: 8px;
}

/* ── PRINT ───────────────────────────────────────────────────── */

@media print {
  body  { background: #fff; font-size: 12px; }

  .cover,
  .cover-accent,
  .sev-group-head,
  .fc-stripe,
  .fc-fix-block,
  .score-ring { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

  .content { padding: 24px 32px; }

  details            { display: block !important; }
  details summary    { display: none; }
  .chev              { display: none; }
  .section           { page-break-inside: avoid; }
  .fc                { page-break-inside: avoid; }
}
"""

# Inline SVG chevron — no external icon dependency
_CHEV = (
    '<svg class="chev" viewBox="0 0 16 16" fill="none" '
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="5,3 11,8 5,13"/></svg>'
)

# Severity icons
_SEV_ICON = {"high": "⛔", "medium": "⚠️", "low": "ℹ️"}

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


def _score_color(score: int) -> str:
    label = _status_label(score)
    return {
        "pass":    "#15803D",
        "warning": "#A16207",
        "fail":    "#B91C1C",
    }.get(label, "#C8C2BA")


def _status_bdg(status: str, lang: str) -> str:
    if lang == "zh":
        labels = {"pass": "通过", "warning": "警告", "fail": "失败",
                  "unknown": "未知", "data_needed": "待补充"}
    else:
        labels = {"pass": "PASS", "warning": "WARN", "fail": "FAIL",
                  "unknown": "N/A", "data_needed": "DATA"}
    return f'<span class="badge s-{status}">{labels.get(status, status.upper())}</span>'


def _conf_bdg(conf: str, lang: str) -> str:
    if lang == "zh":
        labels = {"high": "高置信", "medium": "中置信", "low": "低置信"}
    else:
        labels = {"high": "CONF·H", "medium": "CONF·M", "low": "CONF·L"}
    return f'<span class="badge c-{conf}">{labels.get(conf, conf.upper())}</span>'


def _score_card(module: str, score: int) -> str:
    label = _status_label(score)
    color = _score_color(score)
    num   = str(score) if score >= 0 else "—"
    return (
        f'<div class="score-card">'
        f'<div class="score-ring" style="--score:{score};--clr:{color}">'
        f'<div class="score-donut">'
        f'<span class="score-number {label}">{num}</span>'
        f'</div></div>'
        f'<div class="score-module">{_esc(module)}</div>'
        f'</div>'
    )


def _finding_card(f: Finding, idx: int, lang: str) -> str:
    L = {
        "en": {"ev": "Evidence", "impact": "Impact", "fix": "Recommended Fix"},
        "zh": {"ev": "证据", "impact": "影响", "fix": "修复建议"},
    }.get(lang, {"ev": "Evidence", "impact": "Impact", "fix": "Recommended Fix"})

    fix_html = ""
    if f.fix:
        fix_html = (
            f'<div class="fc-fix-block">'
            f'<div class="fc-fix-label">{L["fix"]}</div>'
            f'<div class="fc-fix-value">{_esc(f.fix)}</div>'
            f'</div>'
        )

    return (
        f'<div class="fc {f.severity}">'

        # ── header strip ──
        f'<div class="fc-head">'
        f'<div class="fc-stripe"></div>'
        f'<div class="fc-head-content">'
        f'<div>'
        f'<div class="fc-index-module">{idx}. {_esc(f.module)}</div>'
        f'<div class="fc-check-name">{_esc(f.check.replace("_", " ").title())}</div>'
        f'</div>'
        f'<div class="fc-badges">{_status_bdg(f.status, lang)}{_conf_bdg(f.confidence, lang)}</div>'
        f'</div>'
        f'</div>'

        # ── body fields ──
        f'<div class="fc-body">'
        f'<div class="fc-field">'
        f'<div class="fc-field-label">{L["ev"]}</div>'
        f'<div class="fc-field-value evidence">{_esc(f.evidence)}</div>'
        f'</div>'
        f'<div class="fc-field">'
        f'<div class="fc-field-label">{L["impact"]}</div>'
        f'<div class="fc-field-value">{_esc(f.impact)}</div>'
        f'</div>'
        f'</div>'

        # ── fix callout (green footer) ──
        + fix_html +
        f'</div>'
    )


def _detail_block(module: str, findings: List[Finding]) -> str:
    rows = "".join(
        f'<div class="dt-row">'
        f'<div class="dt-s">{STATUS_EMOJI.get(f.status, "")}</div>'
        f'<div class="dt-c">{_esc(f.check)}</div>'
        f'<div class="dt-e">{_esc(f.evidence)}</div>'
        f'</div>'
        for f in findings
    )
    return (
        f'<details>'
        f'<summary>{_esc(module)}{_CHEV}</summary>'
        f'{rows}'
        f'</details>'
    )


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

def generate_html_report(audit_data: Dict, language: str = "en") -> str:
    url         = audit_data.get("url", "")
    date        = audit_data.get("date", "")
    lang_tag    = audit_data.get("detected_language", language)
    update_text = audit_data.get("_update_notice", "").strip()

    all_module_findings = assemble_findings(audit_data)
    scores = {mod: _score_from_findings(flist) for mod, flist in all_module_findings.items()}

    _sev = {"high": 0, "medium": 1, "low": 2}
    _sta = {"fail": 0, "warning": 1, "unknown": 2, "pass": 3}

    prio = sorted(
        [f for flist in all_module_findings.values()
           for f in flist if f.status in ("fail", "warning", "unknown")],
        key=lambda f: (_sev.get(f.severity, 9), _sta.get(f.status, 9)),
    )
    dn = [f for flist in all_module_findings.values()
            for f in flist if f.status == "data_needed"]

    lang = language

    # ── i18n ─────────────────────────────────────────────────────
    if lang == "zh":
        report_label   = "网站 SEO 诊断报告"
        report_sub     = "Google Search 优化诊断"
        url_label      = "诊断目标"
        meta_date      = ("诊断日期", date)
        meta_lang      = ("检测语言", lang_tag)
        meta_engine    = ("搜索引擎", "Google Search")
        kicker         = "SEO AUDIT REPORT · CONFIDENTIAL"
        ey_01          = "第 01 节 — 综合评分"
        ti_01          = "综合评分"
        ey_02          = "第 02 节 — 优先修复"
        ti_02          = "优先修复清单"
        ey_dn          = "第 03 节 — 数据待补充"
        ti_dn          = "数据待补充"
        dn_intro_txt   = "以下检测因数据缺失无法运行，不代表网站存在问题。"
        dn_how         = "解决方式："
        ey_detail      = "第 04 节 — 模块详情"
        ti_detail      = "各模块详细诊断"
        sev_labels     = {
            "high":   "高优先级 — 立即修复",
            "medium": "中优先级 — 本月处理",
            "low":    "低优先级 — 持续改进",
        }
        disc_head      = "免责说明"
        disc_items     = [
            "site: 查询结果为粗略估算，精确收录量请参阅 GSC 覆盖率报告。",
            "域名年龄为历史信任参考，非直接排名因子。",
            "E-E-A-T 信号检测为页面表层扫描，置信度为中等。",
            "DA/DR 权威评分无法从 GSC 获取，请使用 Ahrefs/Moz/Semrush 导出。",
        ]
        footer_html    = '由 <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a> 生成'
        no_issues_txt  = "未发现需要修复的问题。"
    else:
        report_label   = "SEO Audit Report"
        report_sub     = "Google Search Optimisation Diagnostic"
        url_label      = "Target URL"
        meta_date      = ("Date", date)
        meta_lang      = ("Language", lang_tag)
        meta_engine    = ("Engine", "Google Search")
        kicker         = "SEO AUDIT REPORT · CONFIDENTIAL"
        ey_01          = "SECTION 01 — AUDIT OVERVIEW"
        ti_01          = "Performance Overview"
        ey_02          = "SECTION 02 — PRIORITY FINDINGS"
        ti_02          = "Priority Findings"
        ey_dn          = "SECTION 03 — DATA NEEDED"
        ti_dn          = "Data Needed"
        dn_intro_txt   = "These checks could not run due to missing data — they are not site errors."
        dn_how         = "How to fix:"
        ey_detail      = "SECTION 04 — MODULE DETAIL"
        ti_detail      = "Module Detail"
        sev_labels     = {
            "high":   "High Priority — Fix Immediately",
            "medium": "Medium Priority — Fix This Month",
            "low":    "Low Priority — Continuous Improvement",
        }
        disc_head      = "Disclaimer"
        disc_items     = [
            "site: results are estimates; use GSC Coverage for precise index counts.",
            "Domain age is a historical trust signal, not a direct ranking factor.",
            "E-E-A-T findings are surface-level scans; confidence is medium.",
            "DA/DR scores require Ahrefs/Moz/Semrush — unavailable from GSC.",
        ]
        footer_html    = 'Generated by <a href="https://github.com/jiguang9/google-seo-audit">google-seo-audit</a>'
        no_issues_txt  = "No issues found requiring attention."

    # Adjust section numbers when Data Needed section is present
    dn_num     = "03" if dn else None
    detail_num = "04" if dn else "03"
    ey_detail  = (f"SECTION {detail_num} — MODULE DETAIL"
                  if lang != "zh" else f"第 {detail_num} 节 — 模块详情")

    # ── Sub-components ────────────────────────────────────────────

    update_html = ""
    if update_text:
        update_html = (
            f'<div class="banner-wrap">'
            f'<div class="banner">⬆ {_esc(update_text)}</div>'
            f'</div>'
        )

    score_cards = "".join(_score_card(mod, s) for mod, s in scores.items())

    # Priority findings grouped by severity
    groups: Dict[str, List] = {"high": [], "medium": [], "low": []}
    for f in prio:
        groups.setdefault(f.severity, []).append(f)

    prio_html = ""
    counter   = 1
    for sev in ("high", "medium", "low"):
        items = groups.get(sev, [])
        if not items:
            continue
        cards = "".join(_finding_card(f, counter + i, lang) for i, f in enumerate(items))
        counter += len(items)
        prio_html += (
            f'<div class="sev-group">'
            f'<div class="sev-group-head {sev}">'
            f'<span class="sev-group-icon">{_SEV_ICON[sev]}</span>'
            f'<span class="sev-group-label">{sev_labels[sev]}</span>'
            f'<span class="sev-group-count">{len(items)}</span>'
            f'</div>'
            f'{cards}'
            f'</div>'
        )

    if not prio_html:
        prio_html = f'<div class="no-issues">{no_issues_txt}</div>'

    # Data Needed section
    dn_section_html = ""
    if dn:
        dn_cards = "".join(
            f'<div class="dn-card">'
            f'<div class="dn-card-title">{i+1}. [{_esc(f.module)}] {_esc(f.check)}</div>'
            f'<div class="dn-card-ev">{_esc(f.evidence)}</div>'
            f'<div class="dn-card-fix">{_esc(dn_how)} {_esc(f.fix or "")}</div>'
            f'</div>'
            for i, f in enumerate(dn)
        )
        dn_section_html = (
            f'<div class="section">'
            f'<div class="section-head">'
            f'<span class="section-num">{dn_num}</span>'
            f'<div class="section-text">'
            f'<div class="section-eyebrow">{_esc(ey_dn)}</div>'
            f'<div class="section-title">{_esc(ti_dn)}</div>'
            f'</div>'
            f'</div>'
            f'<div class="dn-intro">{dn_intro_txt}</div>'
            f'{dn_cards}'
            f'</div>'
        )

    detail_blocks = "".join(
        _detail_block(mod, findings)
        for mod, findings in all_module_findings.items()
    )

    disc_li = "".join(f"<li>{_esc(it)}</li>" for it in disc_items)

    # Cover metadata items
    def _meta_item(label: str, value: str) -> str:
        return (
            f'<div class="cover-meta-item">'
            f'<div class="cover-meta-label">{_esc(label)}</div>'
            f'<div class="cover-meta-value">{_esc(value)}</div>'
            f'</div>'
        )

    meta_html = (
        _meta_item(*meta_date)
        + _meta_item(*meta_lang)
        + _meta_item(*meta_engine)
    )

    # ── Final HTML assembly ───────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(report_label)} — {_esc(url)}</title>
<style>{_CSS}</style>
</head>
<body>

<div class="cover">
  <div class="cover-accent"></div>
  <div class="cover-inner">
    <div class="cover-kicker">{_esc(kicker)}</div>
    <div class="cover-title">{_esc(report_label)}</div>
    <div class="cover-subtitle">{_esc(report_sub)}</div>
    <div class="cover-url-block">
      <div class="cover-url-label">{_esc(url_label)}</div>
      <div class="cover-url-value">{_esc(url)}</div>
    </div>
    <div class="cover-meta-row">{meta_html}</div>
  </div>
</div>

{update_html}

<div class="content">

  <div class="section">
    <div class="section-head">
      <span class="section-num">01</span>
      <div class="section-text">
        <div class="section-eyebrow">{_esc(ey_01)}</div>
        <div class="section-title">{_esc(ti_01)}</div>
      </div>
    </div>
    <div class="score-grid">{score_cards}</div>
  </div>

  <div class="section">
    <div class="section-head">
      <span class="section-num">02</span>
      <div class="section-text">
        <div class="section-eyebrow">{_esc(ey_02)}</div>
        <div class="section-title">{_esc(ti_02)}</div>
      </div>
    </div>
    {prio_html}
  </div>

  {dn_section_html}

  <div class="section">
    <div class="section-head">
      <span class="section-num">{detail_num}</span>
      <div class="section-text">
        <div class="section-eyebrow">{_esc(ey_detail)}</div>
        <div class="section-title">{_esc(ti_detail)}</div>
      </div>
    </div>
    <div class="details-wrap">{detail_blocks}</div>
  </div>

  <div class="disc">
    <div class="disc-label">{_esc(disc_head)}</div>
    <ul>{disc_li}</ul>
  </div>

  <div class="foot">{footer_html}</div>

</div>
</body>
</html>"""
