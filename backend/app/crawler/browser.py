from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from backend.app.crawler.extractor import (
    clean_text,
    extract_forms,
    extract_hidden_text,
    extract_links,
    field_flags,
    has_download_cta,
    matched_risk_term_evidence,
    matched_risk_term_categories,
    matched_risk_terms,
)
from backend.app.models import PageSignals


STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage"
SCREENSHOT_DIR = STORAGE_DIR / "screenshots"
DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _redirect_chain_from_response(response) -> list[str]:
    chain: list[str] = []
    request = response.request if response else None
    while request:
        chain.append(request.url)
        request = request.redirected_from
    return list(reversed(chain))


async def scan_page(
    url: str,
    take_screenshot: bool = True,
    environment_name: str | None = None,
    viewport: dict | None = None,
    user_agent: str | None = None,
    extra_http_headers: dict | None = None,
    proxy: dict | None = None,
    locale: str | None = None,
    timezone_id: str | None = None,
) -> PageSignals:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=False,
            viewport=viewport or {"width": 1365, "height": 900},
            user_agent=user_agent or DESKTOP_UA,
            extra_http_headers=extra_http_headers,
            proxy=proxy,
            locale=locale,
            timezone_id=timezone_id,
        )
        page = await context.new_page()
        download_seen = False

        async def mark_download(_download) -> None:
            nonlocal download_seen
            download_seen = True

        page.on("download", mark_download)
        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        title = clean_text(await page.title())
        final_url = page.url
        html = await page.content()
        visible_text = clean_text(await page.locator("body").inner_text(timeout=5000))
        headers = response.headers if response else {}
        redirect_chain = _redirect_chain_from_response(response)

        screenshot_path = None
        if take_screenshot:
            suffix = f"_{environment_name}" if environment_name else ""
            screenshot_path = str(SCREENSHOT_DIR / f"{uuid4().hex}{suffix}.png")
            await page.screenshot(path=screenshot_path, full_page=False)

        await context.close()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    forms = extract_forms(soup, final_url)
    has_password, has_phone = field_flags(forms)
    content_disposition = headers.get("content-disposition", "").lower()

    risk_text = " ".join([title, visible_text])

    return PageSignals(
        requested_url=url,
        final_url=final_url,
        title=title,
        visible_text=visible_text[:20000],
        hidden_text=extract_hidden_text(soup),
        links=extract_links(soup, final_url),
        redirect_chain=redirect_chain,
        has_download_button=has_download_cta(soup, final_url),
        has_form=bool(forms),
        has_password_field=has_password,
        has_phone_field=has_phone,
        has_forced_download="attachment" in content_disposition,
        matched_risk_terms=matched_risk_terms(risk_text),
        risk_term_categories=matched_risk_term_categories(risk_text),
        risk_term_evidence=matched_risk_term_evidence(risk_text),
        forms=forms,
        screenshot_path=screenshot_path,
    )
