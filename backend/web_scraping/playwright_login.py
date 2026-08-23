from playwright.async_api import async_playwright, Page


LOGIN_URL = "https://qalam.nust.edu.pk/web/login"
DASHBOARD_URL = "https://qalam.nust.edu.pk/student/dashboard"


async def login_to_qalam(page: Page, email: str, password: str) -> bool:
    """
    Logs into Qalam using the given page (so the caller keeps control of the
    browser/context and the session cookies stay on that same page).
    Does NOT launch or close a browser itself.
    """
    try:
        # 1. Open login page (domcontentloaded is enough here; the explicit
        #    wait_for_selector below handles waiting for the form to render)
        await page.goto(
            LOGIN_URL,
            wait_until="domcontentloaded"
        )

        # 2. Explicitly wait for the login field to actually appear
        #    (domcontentloaded can fire before JS renders the form)
        await page.wait_for_selector("#login", state="visible", timeout=30000)

        # 3. Fill email
        await page.locator("#login").fill(email)

        # 4. Fill password
        await page.locator('input[type="password"]').fill(password)

        # 5. Cloudflare Rocket Loader defers script init; the form's submit
        #    handler no-ops until window.__cfRLUnblockHandlers is set
        await page.wait_for_function(
            "window.__cfRLUnblockHandlers === true", timeout=30000
        )

        # 6. Click Login button and wait for the resulting navigation together,
        #    so we don't race the redirect after submit
        async with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            await page.locator('button[type="submit"]').click()

        # 7. Check final URL
        current_url = page.url

        if current_url.rstrip("/") == DASHBOARD_URL.rstrip("/"):
            return True

        return False

    except Exception as e:
        # Dump a screenshot + HTML snapshot so failures are diagnosable
        try:
            await page.screenshot(path="login_debug.png")
            html = await page.content()
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as dump_err:
            print(f"Failed to capture debug info: {dump_err}")

        print(f"Login error: {e}")
        return False