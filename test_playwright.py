import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content("<html><title>ok</title><body>Hello Playwright</body></html>")
        print(await page.title())
        print(await page.locator("body").inner_text())
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
