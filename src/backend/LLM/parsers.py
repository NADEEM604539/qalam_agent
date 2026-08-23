from langchain_core.output_parsers import PydanticOutputParser
from src.backend.LLM.objects import MarksChangeResponse


marks_change_parser = PydanticOutputParser(pydantic_object=MarksChangeResponse)
