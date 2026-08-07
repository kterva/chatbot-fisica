from pydantic import BaseModel, Field, field_validator

from app.config import settings


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=settings.max_question_length,
        description="Pregunta de Física del estudiante.",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("La pregunta no puede estar vacía.")
        return stripped


class ChatResponse(BaseModel):
    answer: str
