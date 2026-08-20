from playwright.async_api import async_playwright


LOGIN_URL = "https://qalam.nust.edu.pk/web/login"
DASHBOARD_URL = "https://qalam.nust.edu.pk/student/dashboard"


async def login_to_qalam(email: str, password: str) -> bool:
    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        try:
            # 1. Open login page
            await page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded"
            )

            # 2. Fill email
            await page.locator("#login").fill(email)

            # 3. Fill password
            await page.locator('input[type="password"]').fill(password)

            # 4. Click Login button
            await page.locator(
                'button[type="submit"]'
            ).click()

            # 5. Wait for navigation / page to settle
            await page.wait_for_load_state(
                "domcontentloaded"
            )

            # 6. Check final URL
            current_url = page.url

            if current_url.rstrip("/") == DASHBOARD_URL.rstrip("/"):
                return True

            return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

        finally:
            await browser.close()