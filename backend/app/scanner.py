from __future__ import annotations

from urllib.parse import urlparse

from backend.app.analyzer.cloaking import run_cloaking_check
from backend.app.analyzer.rules import score_signals
from backend.app.automation.flow_runner import run_dynamic_flow
from backend.app.crawler.browser import scan_page
from backend.app.db.database import save_scan
from backend.app.llm.policy_reasoner import merge_rule_and_llm, reason_about_policy
from backend.app.models import ScanResult


def normalize_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("URL is required")
    if not urlparse(cleaned).scheme:
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid http or https URL")
    return cleaned


async def run_scan(url: str, dynamic: bool = False, use_llm: bool = False, cloaking: bool = False) -> ScanResult:
    url = normalize_url(url)
    signals = await scan_page(url)
    if dynamic:
        signals.automation_steps = await run_dynamic_flow(url)
        signals.automation_signals = sorted(
            {
                signal
                for step in signals.automation_steps
                for signal in step.get("detected_signals", [])
            }
        )
    if cloaking:
        signals.cloaking_analysis = await run_cloaking_check(url)
    risk = score_signals(signals)
    if use_llm:
        llm = reason_about_policy(signals, risk)
        risk = merge_rule_and_llm(risk, llm)
    return save_scan(ScanResult(signals=signals, risk=risk))
