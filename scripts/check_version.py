"""
Version check utility.
Compares the locally installed skill version against the latest GitHub release.
Called optionally at the start of each audit run.
"""

import json
import re
from pathlib import Path
from typing import Optional

import requests

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
SKILL_FILE = Path(__file__).parent.parent / "SKILL.md"
TIMEOUT = 5  # Fast check; never blocks the audit on failure


def _read_local_version() -> Optional[str]:
    """Parse version from SKILL.md YAML frontmatter."""
    try:
        text = SKILL_FILE.read_text(encoding="utf-8")
        match = re.search(r"^version:\s*([^\s#]+)", text, re.MULTILINE)
        return match.group(1).strip() if match else None
    except (OSError, AttributeError):
        return None


def _parse_semver(version_str: str):
    """Return (major, minor, patch) tuple, or None if unparseable."""
    clean = version_str.lstrip("v")
    parts = clean.split(".")
    try:
        return tuple(int(p) for p in parts[:3])
    except ValueError:
        return None


def check_for_update(owner: str, repo: str = "google-seo-audit") -> dict:
    """
    Check GitHub releases API for a newer version.
    Always returns a dict; never raises — update check must not block the audit.

    Returns:
        {
          "local_version": "1.0.0",
          "latest_version": "1.1.0",   # or None if check failed
          "update_available": True,
          "release_url": "https://github.com/...",
          "notice": "human-readable update message or None",
          "error": None or "reason check failed"
        }
    """
    # Empty string owner = user explicitly disabled the check
    if not owner or not owner.strip():
        return {"update_available": False, "error": "version check disabled", "notice": None}

    local = _read_local_version()
    result = {
        "local_version": local,
        "latest_version": None,
        "update_available": False,
        "release_url": None,
        "notice": None,
        "error": None,
    }

    if not local:
        result["error"] = "Could not read local version from SKILL.md"
        return result

    try:
        resp = requests.get(
            GITHUB_API.format(owner=owner, repo=repo),
            timeout=TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 404:
            result["error"] = "No releases found on GitHub yet"
            return result
        if resp.status_code != 200:
            result["error"] = f"GitHub API returned HTTP {resp.status_code}"
            return result

        data = resp.json()
        latest_tag = data.get("tag_name", "")
        release_url = data.get("html_url", "")
        result["latest_version"] = latest_tag.lstrip("v")
        result["release_url"] = release_url

        local_sv = _parse_semver(local)
        latest_sv = _parse_semver(latest_tag)

        if local_sv and latest_sv and latest_sv > local_sv:
            result["update_available"] = True
            result["notice"] = (
                f"⬆️  Update available: v{local} → v{result['latest_version']}\n"
                f"   Run: cd <skill-dir> && git pull\n"
                f"   Release notes: {release_url}"
            )

    except requests.RequestException as exc:
        result["error"] = f"Version check failed (network): {exc}"

    return result


def format_update_banner(check_result: dict) -> str:
    """Return a notice string for the top of the report, or empty string."""
    if check_result.get("update_available"):
        return (
            f"\n> {check_result['notice']}\n"
        )
    return ""


if __name__ == "__main__":
    import sys
    owner = sys.argv[1] if len(sys.argv) > 1 else "jiguang9"
    result = check_for_update(owner)
    if result["update_available"]:
        print(result["notice"])
    elif result["error"]:
        print(f"Version check skipped: {result['error']}")
    else:
        print(f"Up to date (v{result['local_version']})")
