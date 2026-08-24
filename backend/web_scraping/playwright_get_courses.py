import re
from playwright.async_api import async_playwright, Page
from backend.web_scraping.playwright_login import login_to_qalam
import asyncio


COURSE_HREF_RE = re.compile(r"/student/course/info/(\d+)")


async def fetch_courses(page: Page, courses_url: str):
    """Go to the courses page and return all course IDs + basic info.

    Assumes `page` is already logged in (see get_enrolled_courses).
    """
    await page.goto(courses_url)
    await page.wait_for_load_state("networkidle")

    cards = await page.query_selector_all("a[href*='/student/course/info/']")

    courses = []
    for card in cards:
        href = await card.get_attribute("href") or ""
        match = COURSE_HREF_RE.search(href)
        if not match:
            continue
        course_id = match.group(1)

        async def text_or_none(selector):
            el = await card.query_selector(selector)
            return (await el.inner_text()).strip() if el else None

        course_name = await text_or_none(".card-header span")
        teacher = await text_or_none(".card-title")
        code = await text_or_none(".sub-heading")
        courses.append({
            "course_id": course_id,
            "href": href,
            "course_name": course_name,
            "teacher": teacher,
            "code": code,
        })

    return courses


async def get_enrolled_courses(email:str, password:str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        logged_in = await login_to_qalam(
            page,
            email=email,
            password=password,
        )

        if not logged_in:
            await browser.close()
            raise RuntimeError("Login to Qalam failed; see login_debug.png/html")

        courses = await fetch_courses(page, "https://qalam.nust.edu.pk/student/dashboard")
        await browser.close()
        return courses


if __name__=="__main__":
    
    asyncio.run(get_enrolled_courses())

