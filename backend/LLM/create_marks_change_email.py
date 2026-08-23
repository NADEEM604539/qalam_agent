from backend.LLM.objects import MarksChangeResponse
from backend.LLM.diff_marks import compute_marks_change
import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Detection of what changed is done deterministically in Python
# (see diff_marks.compute_marks_change) — comparing exact obtained_marks
# values at the individual-assessment level is a precise task with one
# correct answer, and an LLM only adds a chance of missed/hallucinated
# matches. No LLM call is involved in this pipeline anymore.
# ---------------------------------------------------------------------------


def _fmt(value, suffix: str = "") -> str:
    """Format a numeric field for table display, or '-' if missing."""
    if value is None:
        return "-"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}{suffix}"


def _col_widths(rows: list[list[str]], headers: list[str]) -> list[int]:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    return widths


def _describe_assessment(r) -> str:
    """One clause describing a single assessment result, in prose."""
    name = r.assessment_name
    a_type = r.assessment_type

    marks_part = None
    if r.obtained_marks is not None and r.max_marks is not None:
        marks_part = f"scored {_fmt(r.obtained_marks)} out of {_fmt(r.max_marks)}"
    elif r.obtained_marks is not None:
        marks_part = f"scored {_fmt(r.obtained_marks)}"

    extras = []
    if r.percentage is not None:
        extras.append(f"{_fmt(r.percentage, '%')}")
    if r.class_average is not None:
        extras.append(f"class average was {_fmt(r.class_average)}")

    sentence = f'"{name}" ({a_type})'
    if marks_part:
        sentence += f" — {marks_part}"
    if extras:
        sentence += f" ({', '.join(extras)})"

    return sentence


def _render_section_paragraph(section_name: str, results: list) -> str:
    """
    One paragraph for a section: a lead-in sentence naming the section,
    followed by prose covering every new assessment result in it.
    """
    descriptions = [_describe_assessment(r) for r in results]

    if len(descriptions) == 1:
        body = f"A new result was posted: {descriptions[0]}."
    else:
        joined = "; ".join(descriptions)
        body = f"New results were posted: {joined}."

    return f"{section_name}: {body}"


def build_email_text(response: MarksChangeResponse) -> str:
    """
    Deterministically render a plain-text email: for each course, a
    heading with the course id, followed by one prose paragraph per
    section covering all of that section's new assessment results.
    """
    if not response.marks_changed or not response.courses:
        return ""

    course_blocks = []

    for course in response.courses:
        if not course.new_results:
            continue

        # Group this course's new results by section, preserving the
        # order sections first appear in.
        sections: dict[str, list] = {}
        for r in course.new_results:
            sections.setdefault(r.section_name, []).append(r)

        title = course.course_id
        if course.course_name:
            title += f" - {course.course_name}"

        paragraphs = [
            _render_section_paragraph(section_name, results)
            for section_name, results in sections.items()
        ]

        course_blocks.append(
            f"{title}\n{'=' * len(title)}\n\n" + "\n\n".join(paragraphs)
        )

    if not course_blocks:
        return ""

    body = (
        "Hi,\n\n"
        "New results have been posted on Qalam for the following "
        "course(s):\n\n"
        + "\n\n".join(course_blocks)
        + "\n\nLog in to Qalam for full details.\n\n"
        "---\n"
        "This is an automated notification."
    )

    return body


def build_email_subject(response: MarksChangeResponse) -> str:
    course_ids = ", ".join(c.course_id for c in response.courses if c.new_results)
    return f"New Results Posted: {course_ids}"


async def llm_generate_email(courses_input: list[dict]) -> MarksChangeResponse:
    """
    courses_input: list of dicts, one per course that changed, e.g.

        {
            "course_id": "2235185",
            "data": <latest CourseResult dict>,
            "previous_data": <previous CourseResult dict or None>
        }

    Returns a MarksChangeResponse. If any assessment's obtained_marks is
    newly present or has changed, `marks_changed=True` and
    `email_subject`/`email_body` are populated with a ready-to-send
    plain-text email. Otherwise `marks_changed=False` and no email
    fields are set (caller should not send anything).

    Kept as `async def` for backwards compatibility with existing
    callers (e.g. workflow.py), even though the diff itself is
    synchronous.
    """
    if not courses_input:
        return MarksChangeResponse(marks_changed=False, courses=[])

    response = compute_marks_change(courses_input)

    if response.marks_changed:
        response.email_subject = build_email_subject(response)
        response.email_body = build_email_text(response)
    else:
        response.email_subject = None
        response.email_body = None

    return response
