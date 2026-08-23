from pydantic import BaseModel
from typing import Optional


class Assessment(BaseModel):
    name: str
    max_mark: Optional[float] = None
    obtained_marks: Optional[float] = None
    class_average: Optional[float] = None
    percentage: Optional[float] = None


class AssessmentType(BaseModel):
    type: Optional[str] = None
    weight_percent: Optional[float] = None
    obtained_percentage: Optional[float] = None
    assessments: list[Assessment]


class Section(BaseModel):
    section_name: str
    assessment_types: list[AssessmentType]


class CourseResult(BaseModel):
    course_id: str
    sections: list[Section]