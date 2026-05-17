"""PageSpeed Insights API: Core Web Vitals + diagnostics for mobile and desktop."""

import json
import os
import time
from typing import Dict, List, Optional

import requests

PSI_API_BASE = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
TIMEOUT = 60  # PSI can be slow

# CWV thresholds (Google's official values)
CWV_THRESHOLDS = {
    "lcp":  {"good": 2500,  "needs_improvement": 4000,  "unit": "ms"},
    "inp":  {"good": 200,   "needs_improvement": 500,   "unit": "ms"},
    "cls":  {"good": 0.1,   "needs_improvement": 0.25,  "unit": "score"},
    "fcp":  {"good": 1800,  "needs_improvement": 3000,  "unit": "ms"},
    "ttfb": {"good": 800,   "needs_improvement": 1800,  "unit": "ms"},
}

# Maps Lighthouse audit IDs to metric names
METRIC_IDS = {
    "largest-contentful-paint": "lcp",
    "interaction-to-next-paint": "inp",
    "cumulative-layout-shift": "cls",
    "first-contentful-paint": "fcp",
    "server-response-time": "ttfb",
    "total-blocking-time": "tbt",
    "speed-index": "speed_index",
}


def _rate_metric(name: str, numeric_value: float) -> str:
    thresholds = CWV_THRESHOLDS.get(name)
    if not thresholds:
        return "unknown"
    if numeric_value <= thresholds["good"]:
        return "good"
    if numeric_value <= thresholds["needs_improvement"]:
        return "needs_improvement"
    return "poor"


def _extract_metrics(lighthouse_result: Dict) -> Dict:
    """Pull numeric values for CWV and supporting metrics from Lighthouse JSON."""
    audits = lighthouse_result.get("audits", {})
    metrics = {}

    for audit_id, metric_name in METRIC_IDS.items():
        audit = audits.get(audit_id, {})
        numeric = audit.get("numericValue")
        display = audit.get("displayValue", "")
        if numeric is not None:
            metrics[metric_name] = {
                "value": round(numeric, metric_name == "cls" and 3 or 0),
                "display": display,
                "unit": CWV_THRESHOLDS.get(metric_name, {}).get("unit", ""),
                "rating": _rate_metric(metric_name, numeric),
            }

    return metrics


def _extract_opportunities(lighthouse_result: Dict) -> List[Dict]:
    """Extract actionable opportunities from Lighthouse audits."""
    audits = lighthouse_result.get("audits", {})
    opportunities = []

    for audit_id, audit in audits.items():
        if audit.get("score") is not None and audit["score"] < 0.9:
            details = audit.get("details", {})
            if details.get("type") in ("opportunity", "table"):
                savings_ms = details.get("overallSavingsMs", 0)
                opportunities.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "description": audit.get("description", ""),
                    "score": audit.get("score"),
                    "savings_ms": savings_ms,
                    "display_value": audit.get("displayValue", ""),
                })

    # Sort by potential savings descending
    return sorted(opportunities, key=lambda x: x["savings_ms"], reverse=True)[:10]


def _extract_diagnostics(lighthouse_result: Dict) -> List[Dict]:
    """Extract failed/warning diagnostic audits."""
    audits = lighthouse_result.get("audits", {})
    diagnostics = []

    skip_ids = set(METRIC_IDS.keys())
    for audit_id, audit in audits.items():
        if audit_id in skip_ids:
            continue
        score = audit.get("score")
        if score is not None and score < 1.0:
            diagnostics.append({
                "id": audit_id,
                "title": audit.get("title", ""),
                "score": score,
                "display_value": audit.get("displayValue", ""),
            })

    return sorted(diagnostics, key=lambda x: x["score"] or 0)[:15]


def fetch_psi(url: str, api_key: Optional[str] = None, strategy: str = "mobile") -> Dict:
    """
    Call PageSpeed Insights API for a given strategy.
    api_key is optional; if omitted, the free unauthenticated quota applies.
    Returns a structured result dict including CWV, score, opportunities, diagnostics.
    """
    # Resolve API key: explicit arg > env var > none (unauthenticated)
    resolved_key = api_key or os.environ.get("PAGESPEED_API_KEY")
    params = {"url": url, "strategy": strategy}
    if resolved_key:
        params["key"] = resolved_key

    result = {
        "url": url,
        "strategy": strategy,
        "performance_score": None,
        "metrics": {},
        "opportunities": [],
        "diagnostics": [],
        "field_data_available": False,
        "error": None,
        "evidence": [],
    }

    try:
        resp = requests.get(PSI_API_BASE, params=params, timeout=TIMEOUT)

        if resp.status_code == 429:
            result["error"] = "rate_limited"
            result["evidence"].append(
                "PSI API rate limit reached. "
                "Provide --psi-key to increase quota, or paste PSI results manually."
            )
            return result

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            result["evidence"].append(f"PSI API returned {resp.status_code}: {resp.text[:200]}")
            return result

        data = resp.json()
        lhr = data.get("lighthouseResult", {})
        crux = data.get("loadingExperience", {})

        # Performance score (0–100)
        categories = lhr.get("categories", {})
        perf = categories.get("performance", {})
        score = perf.get("score")
        if score is not None:
            result["performance_score"] = round(score * 100)

        result["metrics"] = _extract_metrics(lhr)
        result["opportunities"] = _extract_opportunities(lhr)
        result["diagnostics"] = _extract_diagnostics(lhr)

        # CrUX field data
        if crux.get("overall_category"):
            result["field_data_available"] = True
            result["field_data_category"] = crux["overall_category"]
            result["evidence"].append(
                f"CrUX field data available: overall = {crux['overall_category']}"
            )

        result["evidence"].append(
            f"PSI {strategy}: score={result['performance_score']}, "
            f"LCP={result['metrics'].get('lcp', {}).get('display', 'N/A')}, "
            f"INP={result['metrics'].get('inp', {}).get('display', 'N/A')}, "
            f"CLS={result['metrics'].get('cls', {}).get('display', 'N/A')}"
        )

    except requests.RequestException as exc:
        result["error"] = str(exc)
        result["evidence"].append(f"PSI API request failed: {exc}")

    return result


def run_psi_both_strategies(url: str, api_key: Optional[str] = None) -> Dict:
    """Run PSI for both mobile and desktop with a short pause between calls."""
    mobile = fetch_psi(url, api_key=api_key, strategy="mobile")
    time.sleep(1)
    desktop = fetch_psi(url, api_key=api_key, strategy="desktop")
    return {"mobile": mobile, "desktop": desktop}


def generate_cwv_findings(psi_results: Dict) -> List[Dict]:
    """Convert PSI results into structured Finding-compatible dicts."""
    findings = []

    for strategy in ("mobile", "desktop"):
        result = psi_results.get(strategy, {})

        if result.get("error") == "rate_limited":
            findings.append({
                "module": "Core Web Vitals",
                "check": f"psi_{strategy}",
                "status": "data_needed",   # not a site problem — data is missing
                "severity": "medium",
                "confidence": "low",
                "evidence": result["evidence"][0] if result["evidence"] else "PSI API unavailable",
                "impact": "Core Web Vitals cannot be assessed without PageSpeed data",
                "fix": "Run with --psi-key=YOUR_KEY or set env var PAGESPEED_API_KEY to increase quota",
            })
            continue

        if result.get("error"):
            findings.append({
                "module": "Core Web Vitals",
                "check": f"psi_{strategy}",
                "status": "unknown",
                "severity": "medium",
                "confidence": "low",
                "evidence": f"PSI {strategy} failed: {result['error']}",
                "impact": "Cannot assess Core Web Vitals",
                "fix": "Ensure URL is publicly accessible and retry",
            })
            continue

        # Overall performance score
        score = result.get("performance_score")
        findings.append({
            "module": "Core Web Vitals",
            "check": f"psi_score_{strategy}",
            "status": "pass" if score and score >= 90 else ("warning" if score and score >= 50 else "fail"),
            "severity": "high" if strategy == "mobile" else "medium",
            "confidence": "high",
            "evidence": f"PSI {strategy} performance score: {score}/100",
            "impact": "Low PSI scores correlate with higher bounce rates and lower rankings",
            "fix": "Review PSI opportunities section for specific fixes" if score and score < 90 else None,
        })

        # Per-metric findings
        metrics = result.get("metrics", {})
        cwv_metrics = [("lcp", "high"), ("inp", "high"), ("cls", "high")]
        supporting = [("fcp", "medium"), ("ttfb", "medium")]

        for metric_name, sev in cwv_metrics + supporting:
            metric = metrics.get(metric_name)
            if not metric:
                continue

            rating = metric["rating"]
            status = {"good": "pass", "needs_improvement": "warning", "poor": "fail"}.get(rating, "unknown")

            thresholds = CWV_THRESHOLDS.get(metric_name, {})
            fix_map = {
                "lcp": "Optimize largest image/text block: use preload, serve next-gen images, reduce server response time",
                "inp": "Reduce JavaScript execution time, break up long tasks, minimize main thread blocking",
                "cls": "Set explicit width/height on images/embeds, avoid inserting content above existing content",
                "fcp": "Eliminate render-blocking resources, inline critical CSS",
                "ttfb": "Use a CDN, optimize server response time, enable caching",
            }

            findings.append({
                "module": "Core Web Vitals",
                "check": f"{metric_name}_{strategy}",
                "status": status,
                "severity": sev if strategy == "mobile" else "low",
                "confidence": "high",
                "evidence": f"{metric_name.upper()} ({strategy}): {metric['display']} → {rating}",
                "impact": f"{metric_name.upper()} is a confirmed Google page experience signal",
                "fix": fix_map.get(metric_name) if status != "pass" else None,
            })

    return findings
