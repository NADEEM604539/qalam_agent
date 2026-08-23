from pydantic import BaseModel, Field
from typing import Optional


class AssessmentResultItem(BaseModel):
    section_name: str
    assessment_type: str
    assessment_name: str
    max_marks: Optional[float] = None
    obtained_marks: Optional[float] = None
    percentage: Optional[float] = None
    class_average: Optional[float] = None


class CourseResultChange(BaseModel):
    course_id: str
    course_name: Optional[str] = None
    new_results: list[AssessmentResultItem] = Field(default_factory=list)


class MarksChangeResponse(BaseModel):
    marks_changed: bool
    courses: list[CourseResultChange] = Field(default_factory=list)
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
