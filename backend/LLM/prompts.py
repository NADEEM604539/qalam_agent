from langchain_core.prompts import PromptTemplate
from backend.LLM.parsers import marks_change_parser

marks_change_prompt = PromptTemplate(
    template="""
You are a university marks-change detection agent.

You will receive a LIST of course objects:

{{
    "course_id": "...",
    "data": <latest course result>,
    "previous_data": <previous course result, may be null>
}}

Compare `data.sections` with `previous_data.sections` for each course.

RULES:

1. A section is NEW only if its `section_name` exists in `data`
   but not in `previous_data`. If `previous_data` is null, treat
   every section in `data` as new.

2. ONLY process newly added sections. Ignore:
   - deleted sections
   - existing/unchanged sections
   - changes inside existing sections

3. For each new section, inspect its assessment types and assessments.

4. Consider it a real result only when actual marks/results are present.
   Ignore:
   - null/None marks
   - empty assessments
   - missing results
   - `class_average = 0` when it is only a placeholder

5. For every valid result, extract:
   section_name, assessment_type, assessment_name (the assessment's `name`),
   max_marks, obtained_marks, percentage, and class_average.

6. Never invent data. Leave a field null if it is not present in the source.

7. If no new section (across any course) contains actual results, set
   `marks_changed` to false and return an empty `courses` list. Do not
   set `email_subject` or `email_body` in this case.

8. If real new results are found, set `marks_changed` to true and, for
   each affected course, populate a `CourseResultChange` with its
   `course_id` and the list of `new_results` (AssessmentResultItem items).
   Only include courses that actually have new results.

9. Do NOT generate `email_subject` or `email_body` yourself — leave them
   null. A separate deterministic step will render the email from the
   structured data you return.

10. Do not mention deleted or unchanged sections anywhere in your output.

Return the result strictly according to the provided output format,
and output nothing except the structured object.

{format_instructions}

COURSE DATA:
{courses}
""",
    input_variables=["courses"],
    partial_variables={
        "format_instructions": marks_change_parser.get_format_instructions()
    },
)
