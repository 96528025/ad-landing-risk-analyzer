from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from playwright.async_api import Page, async_playwright


STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage"
SCREENSHOT_DIR = STORAGE_DIR / "screenshots"

ACTION_POLICY = [
    ("download", 95, "download_or_install"),
    ("install", 95, "download_or_install"),
    ("apk", 95, "download_or_install"),
    ("claim", 85, "reward_claim"),
    ("bonus", 85, "reward_claim"),
    ("start now", 75, "start_flow"),
    ("get started", 75, "start_flow"),
    ("continue", 70, "continue_flow"),
    ("sign up", 65, "account_creation"),
    ("register", 65, "account_creation"),
    ("join", 60, "account_creation"),
    ("subscribe", 60, "payment_or_subscription"),
    ("payment", 60, "payment_or_subscription"),
    ("checkout", 60, "payment_or_subscription"),
    ("login", 45, "login"),
    ("log in", 45, "login"),
    ("learn more", 25, "information_link"),
    ("watch", 20, "content_navigation"),
    ("accept", 10, "consent_prompt"),
    ("agree", 10, "consent_prompt"),
    ("allow all", 10, "consent_prompt"),
    ("got it", 10, "consent_prompt"),
    ("not now", 10, "consent_prompt"),
    ("close", 10, "dismiss_prompt"),
    ("dismiss", 10, "dismiss_prompt"),
]

CONSENT_ACTIONS = [
    "accept",
    "agree",
    "allow all",
    "ok",
    "got it",
    "close",
    "dismiss",
    "not now",
]

UNSAFE_ACTIONS = [
    "18 or older",
    "i am 18",
    "enter",
]

FAKE_VALUES = {
    "email": "reviewer@example.com",
    "password": "Password123!",
    "tel": "4155550100",
    "text": "Alex Reviewer",
    "search": "product",
    "url": "https://example.com",
    "number": "100",
}


async def _detect_interstitials(page: Page) -> list[str]:
    try:
        text = (await page.locator("body").inner_text(timeout=2500)).lower()
    except Exception:
        return []

    detections: list[str] = []
    age_markers = [
        "18 or older",
        "under 18",
        "age-restricted",
        "age restricted",
        "age of majority",
        "notice to users",
        "sexual activity",
    ]
    cookie_markers = [
        "accept cookies",
        "cookie consent",
        "manage cookies",
        "privacy preferences",
    ]
    login_markers = [
        "log in to continue",
        "sign in to continue",
        "login to continue",
        "create an account",
    ]

    if sum(marker in text for marker in age_markers) >= 2:
        detections.append("age_gate")
    if any(marker in text for marker in cookie_markers):
        detections.append("cookie_consent")
    if any(marker in text for marker in login_markers):
        detections.append("login_wall")
    return detections


async def _screenshot(page: Page, label: str) -> dict:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = str(SCREENSHOT_DIR / f"{uuid4().hex}_{label}.png")
    await page.screenshot(path=path, full_page=False)
    return {"label": label, "url": page.url, "screenshot_path": path}


def _action_score(text: str, href: str | None = None) -> tuple[int, str]:
    target = f"{text} {href or ''}".lower()
    for token, score, reason in ACTION_POLICY:
        if token in target:
            return score, reason
    if href and re.search(r"\.(apk|exe|dmg|pkg|zip|msi)(\?|$)", href.lower()):
        return 100, "download_file_link"
    return 0, "low_priority"


async def _visible_action_candidates(page: Page, limit: int = 20) -> list[dict]:
    elements = page.locator("a, button, input[type=submit], input[type=button], [role=button]")
    count = min(await elements.count(), 80)
    candidates: list[dict] = []
    for index in range(count):
        element = elements.nth(index)
        try:
            if not await element.is_visible(timeout=500):
                continue
            raw_text = await element.inner_text(timeout=500)
        except Exception:
            raw_text = ""
        try:
            value = await element.get_attribute("value") or ""
            aria = await element.get_attribute("aria-label") or ""
            href = await element.get_attribute("href")
        except Exception:
            value = ""
            aria = ""
            href = None
        text = " ".join(part.strip() for part in [raw_text, value, aria] if part and part.strip())
        text = re.sub(r"\s+", " ", text).strip()
        if not text and not href:
            continue
        score, reason = _action_score(text, href)
        if score <= 0:
            continue
        lowered = text.lower()
        unsafe = any(token in lowered for token in UNSAFE_ACTIONS)
        candidates.append(
            {
                "index": index,
                "text": text[:120] or "(link)",
                "href": href,
                "priority": score,
                "reason": reason,
                "unsafe": unsafe,
                "action_key": f"{index}:{text[:80]}:{href or ''}",
            }
        )
    return sorted(candidates, key=lambda item: item["priority"], reverse=True)[:limit]


async def _handle_lightweight_prompt(page: Page) -> dict | None:
    candidates = await _visible_action_candidates(page, limit=30)
    for candidate in candidates:
        text = candidate["text"].lower()
        if any(token in text for token in UNSAFE_ACTIONS):
            continue
        if not any(token in text for token in CONSENT_ACTIONS):
            continue
        try:
            await page.locator("a, button, input[type=submit], input[type=button], [role=button]").nth(candidate["index"]).click(
                timeout=2000
            )
            await page.wait_for_timeout(500)
            return {
                "clicked": candidate["text"],
                "reason": "lightweight_prompt",
                "priority": candidate["priority"],
            }
        except Exception:
            continue
    return None


async def _page_state(page: Page) -> str:
    try:
        text = await page.locator("body").inner_text(timeout=2500)
    except Exception:
        text = ""
    try:
        scroll_y = await page.evaluate("() => Math.round(window.scrollY)")
    except Exception:
        scroll_y = 0
    signature = f"{page.url}|{scroll_y}|{text[:2500]}"
    return hashlib.sha256(signature.encode("utf-8", errors="ignore")).hexdigest()


async def _fill_visible_form_fields(page: Page) -> list[str]:
    filled: list[str] = []
    inputs = page.locator("input:not([type=hidden]), textarea")
    count = min(await inputs.count(), 8)
    for index in range(count):
        field = inputs.nth(index)
        if not await field.is_visible():
            continue
        field_type = (await field.get_attribute("type") or "text").lower()
        value = FAKE_VALUES.get(field_type, FAKE_VALUES["text"])
        try:
            current_value = await field.input_value(timeout=1000)
            if current_value:
                continue
            await field.fill(value, timeout=1500)
            name = await field.get_attribute("name")
            filled.append(name or field_type)
        except Exception:
            continue
    return filled


async def run_dynamic_flow(url: str, max_steps: int = 5) -> list[dict]:
    steps: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=False,
            viewport={"width": 1365, "height": 900},
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        initial_step = await _screenshot(page, "initial")
        initial_step["detected_signals"] = await _detect_interstitials(page)
        initial_step["candidate_actions"] = await _visible_action_candidates(page, limit=5)
        steps.append(initial_step)
        last_state = await _page_state(page)
        seen_states = {last_state}
        clicked_actions: set[str] = set()

        if "age_gate" in initial_step["detected_signals"]:
            blocked_step = await _screenshot(page, "blocked_age_gate")
            blocked_step["detected_signals"] = initial_step["detected_signals"]
            blocked_step["blocked_reason"] = "Age gate detected; automation stopped before entering restricted content."
            steps.append(blocked_step)
            await context.close()
            await browser.close()
            return steps

        for step_index in range(max_steps):
            prompt_action = await _handle_lightweight_prompt(page)
            if prompt_action:
                prompt_step = await _screenshot(page, f"step_{step_index + 1}_prompt")
                prompt_step["clicked"] = prompt_action["clicked"]
                prompt_step["action_reason"] = prompt_action["reason"]
                prompt_step["detected_signals"] = await _detect_interstitials(page)
                prompt_step["candidate_actions"] = await _visible_action_candidates(page, limit=5)
                steps.append(prompt_step)
                last_state = await _page_state(page)
                seen_states.add(last_state)
                continue

            await page.mouse.wheel(0, 900)
            await page.wait_for_timeout(500)
            detected = await _detect_interstitials(page)
            filled = await _fill_visible_form_fields(page)

            clicked = None
            action_reason = None
            candidate_actions = await _visible_action_candidates(page, limit=10)
            actionable_candidates = [
                candidate
                for candidate in candidate_actions
                if not candidate["unsafe"] and candidate["action_key"] not in clicked_actions
            ]
            if actionable_candidates:
                chosen = actionable_candidates[0]
                try:
                    await page.locator("a, button, input[type=submit], input[type=button], [role=button]").nth(
                        chosen["index"]
                    ).click(timeout=3000)
                    clicked = chosen["text"]
                    action_reason = chosen["reason"]
                    clicked_actions.add(chosen["action_key"])
                except Exception as exc:
                    action_reason = f"click_failed: {exc}"

            if clicked is None and not filled:
                steps.append(await _screenshot(page, f"step_{step_index + 1}_no_action"))
                steps[-1]["detected_signals"] = detected
                steps[-1]["candidate_actions"] = candidate_actions
                if candidate_actions and all(candidate["unsafe"] for candidate in candidate_actions):
                    steps[-1]["blocked_reason"] = "Only unsafe or policy-blocked actions were available."
                break

            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            current_state = await _page_state(page)
            if current_state == last_state or current_state in seen_states:
                steps.append(
                    {
                        "label": f"step_{step_index + 1}_no_state_change",
                        "url": page.url,
                        "clicked": clicked,
                        "action_reason": action_reason,
                        "filled_fields": filled,
                        "detected_signals": detected,
                        "candidate_actions": candidate_actions,
                        "blocked_reason": "No meaningful page state change detected; stopped to avoid duplicate screenshots.",
                    }
                )
                break
            last_state = current_state
            seen_states.add(current_state)
            step = await _screenshot(page, f"step_{step_index + 1}")
            step["clicked"] = clicked
            step["action_reason"] = action_reason
            step["filled_fields"] = filled
            step["detected_signals"] = sorted(set(detected + await _detect_interstitials(page)))
            step["candidate_actions"] = candidate_actions[:5]
            steps.append(step)

        await context.close()
        await browser.close()
    return steps
