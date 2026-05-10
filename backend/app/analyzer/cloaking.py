from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path

from backend.app.analyzer.rules import score_signals
from backend.app.crawler.browser import DESKTOP_UA, scan_page
from backend.app.models import PageSignals


IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)

SCAN_ENVIRONMENTS = [
    {
        "name": "desktop_chrome",
        "viewport": {"width": 1365, "height": 900},
        "user_agent": DESKTOP_UA,
        "extra_http_headers": {},
    },
    {
        "name": "mobile_iphone",
        "viewport": {"width": 390, "height": 844},
        "user_agent": IPHONE_UA,
        "extra_http_headers": {},
    },
    {
        "name": "ad_click_referer",
        "viewport": {"width": 1365, "height": 900},
        "user_agent": DESKTOP_UA,
        "extra_http_headers": {"Referer": "https://www.facebook.com/"},
    },
]

GEO_CONFIG_PATH = Path(__file__).resolve().parents[3] / "storage" / "geo_environments.json"


def _text_similarity(left: str, right: str) -> float:
    left_sample = left[:5000]
    right_sample = right[:5000]
    if not left_sample and not right_sample:
        return 1.0
    return SequenceMatcher(None, left_sample, right_sample).ratio()


def _summary(signals: PageSignals) -> dict:
    risk = score_signals(signals)
    return {
        "final_url": signals.final_url,
        "title": signals.title,
        "risk_score": risk.score,
        "risk_level": risk.level,
        "policy_labels": risk.policy_labels,
        "has_download_button": signals.has_download_button,
        "has_form": signals.has_form,
        "has_password_field": signals.has_password_field,
        "has_phone_field": signals.has_phone_field,
        "redirect_count": len(signals.redirect_chain),
        "screenshot_path": signals.screenshot_path,
    }


def analyze_environment_differences(environment_results: dict[str, PageSignals]) -> dict:
    names = list(environment_results)
    summaries = {name: _summary(signals) for name, signals in environment_results.items()}
    score = 0
    reasons: list[str] = []
    notes: list[str] = []
    comparisons: list[dict] = []
    low_similarity_pairs: list[str] = []

    for index, left_name in enumerate(names):
        for right_name in names[index + 1 :]:
            left = environment_results[left_name]
            right = environment_results[right_name]
            left_risk = summaries[left_name]["risk_score"]
            right_risk = summaries[right_name]["risk_score"]
            similarity = _text_similarity(left.visible_text, right.visible_text)
            risk_delta = abs(left_risk - right_risk)
            comparison = {
                "left": left_name,
                "right": right_name,
                "text_similarity": round(similarity, 2),
                "risk_delta": risk_delta,
                "final_url_changed": left.final_url != right.final_url,
                "download_mismatch": left.has_download_button != right.has_download_button,
                "form_mismatch": left.has_form != right.has_form,
                "password_mismatch": left.has_password_field != right.has_password_field,
            }
            comparisons.append(comparison)

            if comparison["final_url_changed"]:
                score += 30
                reasons.append(f"{left_name} and {right_name} resolved to different final URLs")
            if risk_delta >= 50:
                score += 25
                reasons.append(f"Risk score differed by {risk_delta} between {left_name} and {right_name}")
            elif risk_delta >= 30:
                score += 8
                notes.append(f"Moderate risk score difference of {risk_delta} between {left_name} and {right_name}")
            if comparison["download_mismatch"]:
                score += 20
                reasons.append(f"Download CTA appeared in only one of {left_name}/{right_name}")
            if comparison["password_mismatch"]:
                score += 15
                reasons.append(f"Password field appeared in only one of {left_name}/{right_name}")
            if similarity < 0.5:
                low_similarity_pairs.append(f"{left_name}/{right_name}")

    if low_similarity_pairs:
        score += 5
        reasons.append(f"Page text similarity was low across {len(low_similarity_pairs)} environment pair(s)")
        notes.append(
            "Low text similarity is a weak cloaking signal by itself; responsive layout, age gates, consent prompts, or mobile-specific UI can cause benign differences."
        )

    capped_score = min(score, 100)
    if capped_score >= 70:
        level = "High"
    elif capped_score >= 40:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("No major environment mismatch detected")

    return {
        "score": capped_score,
        "level": level,
        "reasons": reasons,
        "notes": notes,
        "environment_summaries": summaries,
        "comparisons": comparisons,
    }


async def run_cloaking_check(url: str) -> dict:
    results: dict[str, PageSignals] = {}
    for env in SCAN_ENVIRONMENTS:
        results[env["name"]] = await scan_page(
            url,
            take_screenshot=True,
            environment_name=env["name"],
            viewport=env["viewport"],
            user_agent=env["user_agent"],
            extra_http_headers=env["extra_http_headers"],
        )
    analysis = analyze_environment_differences(results)
    analysis["device_referer_status"] = "completed"
    analysis["geo_analysis"] = await run_geo_cloaking_check(url)
    return analysis


def load_geo_environments(path: Path = GEO_CONFIG_PATH) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    environments = data.get("environments", data if isinstance(data, list) else [])
    return [env for env in environments if env.get("name") and env.get("proxy")]


async def run_geo_cloaking_check(url: str) -> dict:
    geo_envs = load_geo_environments()
    if not geo_envs:
        return {
            "status": "skipped",
            "reason": "No geo proxy environments configured. Add storage/geo_environments.json with real regional proxies to enable geo cloaking checks.",
            "score": 0,
            "level": "Not Run",
            "environment_summaries": {},
            "comparisons": [],
        }

    results: dict[str, PageSignals] = {}
    for env in geo_envs:
        proxy = env["proxy"]
        if isinstance(proxy, str):
            proxy = {"server": proxy}
        results[env["name"]] = await scan_page(
            url,
            take_screenshot=True,
            environment_name=env["name"],
            viewport=env.get("viewport") or {"width": 1365, "height": 900},
            user_agent=env.get("user_agent") or DESKTOP_UA,
            extra_http_headers=env.get("extra_http_headers") or {},
            proxy=proxy,
            locale=env.get("locale"),
            timezone_id=env.get("timezone_id"),
        )
    analysis = analyze_environment_differences(results)
    analysis["status"] = "completed"
    return analysis
