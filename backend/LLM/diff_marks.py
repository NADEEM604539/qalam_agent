from typing import Optional

from src.backend.LLM.objects import (
    MarksChangeResponse,
    CourseResultChange,
    AssessmentResultItem,
)


# ---------------------------------------------------------------------------
# Deterministic diff: compares latest vs. previous course result data at
# the individual assessment level and reports every assessment whose
# `obtained_marks` is newly present or has changed value.
#
# This intentionally does NOT use an LLM for detection. Diffing exact
# structured JSON is a precise task with one correct answer — an LLM adds
# unreliability (missed matches, hallucinated changes) with no upside here.
# ---------------------------------------------------------------------------


def _index_by(items: list[dict], key: str) -> dict:
    return {item.get(key): item for item in (items or [])}


def _diff_course(course_id: str, data: dict, previous_data: Optional[dict]) -> CourseResultChange:
    course_name = data.get("course_name")
    new_results: list[AssessmentResultItem] = []

    old_sections = _index_by((previous_data or {}).get("sections", []), "section_name")

    for section in data.get("sections", []) or []:
        section_name = section.get("section_name")
        old_section = old_sections.get(section_name)

        old_types = _index_by(
            (old_section or {}).get("assessment_types", []), "type"
        )

        for a_type in section.get("assessment_types", []) or []:
            type_name = a_type.get("type")
            old_type = old_types.get(type_name)

            old_assessments = _index_by(
                (old_type or {}).get("assessments", []), "name"
            )

            for assessment in a_type.get("assessments", []) or []:
                name = assessment.get("name")
                old_assessment = old_assessments.get(name)

                new_marks = assessment.get("obtained_marks")
                old_marks = (
                    old_assessment.get("obtained_marks")
                    if old_assessment else None
                )

                # Only report when a real obtained_marks value is present
                # now AND it's different from what it was before
                # (covers both: brand-new marks, and a changed value).
                if new_marks is None:
                    continue
                if new_marks == old_marks:
                    continue

                new_results.append(
                    AssessmentResultItem(
                        section_name=section_name,
                        assessment_type=type_name,
                        assessment_name=name,
                        max_marks=assessment.get("max_mark"),
                        obtained_marks=new_marks,
                        percentage=assessment.get("percentage"),
                        class_average=assessment.get("class_average"),
                    )
                )

    return CourseResultChange(
        course_id=course_id,
        course_name=course_name,
        new_results=new_results,
    )


def compute_marks_change(courses_input: list[dict]) -> MarksChangeResponse:
    """
    courses_input: list of dicts, one per course, e.g.

        {
            "course_id": "2235185",
            "data": <latest CourseResult dict>,
            "previous_data": <previous CourseResult dict or None>
        }

    Returns a MarksChangeResponse with `marks_changed=True` and populated
    `courses` only for courses that have at least one assessment whose
    obtained_marks is new or changed.
    """
    changed_courses: list[CourseResultChange] = []

    for entry in courses_input:
        course_change = _diff_course(
            course_id=entry["course_id"],
            data=entry["data"],
            previous_data=entry.get("previous_data"),
        )
        if course_change.new_results:
            changed_courses.append(course_change)

    return MarksChangeResponse(
        marks_changed=bool(changed_courses),
        courses=changed_courses,
    )
