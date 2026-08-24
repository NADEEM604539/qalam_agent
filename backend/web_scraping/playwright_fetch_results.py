import re

from playwright.async_api import async_playwright

from backend.web_scraping.playwright_login import login_to_qalam


RESULT_URL_TEMPLATE = (
    "https://qalam.nust.edu.pk/student/course/gradebook/{course_id}"
)


async def fetch_course_result(course_id: str, email:str, password:str) -> dict:

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:

            # ---------------------------------------------
            # Login
            # ---------------------------------------------

            await login_to_qalam(
                page=page,
                email=email,
                password=password,
            )

            # ---------------------------------------------
            # Open result page
            # ---------------------------------------------

            url = RESULT_URL_TEMPLATE.format(
                course_id=course_id
            )

            await page.goto(url)

            await page.wait_for_load_state("networkidle")

            # ---------------------------------------------
            # Get section names
            # ---------------------------------------------

            tab_items = page.locator(
                "ul.uk-tab > li:not(.uk-tab-responsive)"
            )

            section_names = []

            for i in range(await tab_items.count()):

                tab = tab_items.nth(i)

                link = tab.locator("a")

                if await link.count() > 0:

                    raw = (await link.inner_text()).strip()

                    clean = re.sub(
                        r"\s+",
                        " ",
                        raw
                    )

                    section_names.append(clean)

            # ---------------------------------------------
            # Get sections
            # ---------------------------------------------

            switcher_items = page.locator(
                "ul.uk-switcher > li"
            )

            sections = []

            for idx in range(await switcher_items.count()):

                li = switcher_items.nth(idx)

                if idx < len(section_names):

                    section_name = section_names[idx]

                else:

                    section_name = f"Section {idx + 1}"

                # -----------------------------------------
                # Assessment type parent rows
                # -----------------------------------------

                parent_rows = li.locator(
                    "tr.table-parent-row"
                )

                assessment_types = []

                for parent_index in range(
                    await parent_rows.count()
                ):

                    parent = parent_rows.nth(
                        parent_index
                    )

                    # -------------------------------------
                    # Assessment type
                    # -------------------------------------

                    type_link = parent.locator(
                        "a.js-toggle-children-row"
                    )

                    type_name = None
                    weight_percent = None

                    if await type_link.count() > 0:

                        badge = type_link.locator(
                            ".uk-badge"
                        )

                        if await badge.count() > 0:

                            badge_text = (
                                await badge.inner_text()
                            ).strip()

                        else:

                            badge_text = ""

                        full_text = re.sub(
                            r"\s+",
                            " ",
                            (
                                await type_link.inner_text()
                            ).strip()
                        )

                        type_name = (
                            full_text
                            .replace(
                                badge_text,
                                ""
                            )
                            .strip()
                        )

                        weight_match = re.search(
                            r"[\d.]+",
                            badge_text
                        )

                        if weight_match:

                            weight_percent = float(
                                weight_match.group()
                            )

                    # -------------------------------------
                    # Overall obtained percentage
                    # -------------------------------------

                    tds = parent.locator("td")

                    obtained_percentage = None

                    if await tds.count() >= 2:

                        obtained_text = (
                            await tds.nth(1).inner_text()
                        ).strip()

                        try:

                            obtained_percentage = float(
                                obtained_text
                            )

                        except ValueError:

                            obtained_percentage = None

                    # -------------------------------------
                    # Individual assessments
                    # -------------------------------------

                    assessments = []

                    # Find the next rows after this parent
                    # until another parent row is reached.

                    current_row = parent

                    while True:

                        next_row = current_row.locator(
                            "xpath=following-sibling::tr[1]"
                        )

                        # No next row
                        if await next_row.count() == 0:
                            break

                        # ---------------------------------
                        # Is this another assessment type?
                        # ---------------------------------

                        if await next_row.locator(
                            "tr.table-parent-row"
                        ).count() > 0:

                            break

                        is_parent = await next_row.evaluate(
                            """
                            el =>
                                el.classList.contains(
                                    'table-parent-row'
                                )
                            """
                        )

                        if is_parent:
                            break

                        # ---------------------------------
                        # Is this the header row?
                        # ---------------------------------

                        is_header = await next_row.evaluate(
                            """
                            el =>
                                el.classList.contains(
                                    'md-bg-blue-grey-800'
                                )
                            """
                        )

                        if not is_header:

                            cells = next_row.locator("td")

                            if await cells.count() >= 5:

                                def to_float(value):

                                    try:
                                        return float(value)

                                    except (
                                        ValueError,
                                        TypeError
                                    ):
                                        return None

                                name = (
                                    await cells.nth(0).inner_text()
                                ).strip()

                                max_mark = (
                                    await cells.nth(1).inner_text()
                                ).strip()

                                obtained_marks = (
                                    await cells.nth(2).inner_text()
                                ).strip()

                                class_average = (
                                    await cells.nth(3).inner_text()
                                ).strip()

                                percentage = (
                                    await cells.nth(4).inner_text()
                                ).strip()

                                assessments.append(
                                    {
                                        "name": name,
                                        "max_mark": to_float(
                                            max_mark
                                        ),
                                        "obtained_marks": to_float(
                                            obtained_marks
                                        ),
                                        "class_average": to_float(
                                            class_average
                                        ),
                                        "percentage": to_float(
                                            percentage
                                        ),
                                    }
                                )

                        # Move to next row
                        current_row = next_row

                    # -------------------------------------
                    # Store assessment type
                    # -------------------------------------

                    assessment_types.append(
                        {
                            "type": type_name,
                            "weight_percent": weight_percent,
                            "obtained_percentage": (
                                obtained_percentage
                            ),
                            "assessments": assessments,
                        }
                    )

                # -----------------------------------------
                # Store section
                # -----------------------------------------

                sections.append(
                    {
                        "section_name": section_name,
                        "assessment_types": (
                            assessment_types
                        ),
                    }
                )

            # ---------------------------------------------
            # Return final structured result
            # ---------------------------------------------
            print(course_id, "_______")
            print(sections)
            return {
                "course_id": course_id,
                "sections": sections,
            }

        finally:

            await browser.close()