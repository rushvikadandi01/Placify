from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ChatIntent(str, Enum):
    DSA = "DSA"
    APTITUDE = "APTITUDE"
    INTERVIEW = "INTERVIEW"
    CORE_CS = "CORE_CS"
    HR = "HR"
    PROJECT_INTERVIEW = "PROJECT_INTERVIEW"
    STUDY_PLAN = "STUDY_PLAN"
    GENERAL = "GENERAL"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    student_id: int | None = None
    conversation_id: str | None = Field(default=None, max_length=128)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be empty.")
        return value


class ChatResponse(BaseModel):
    response: str
    intent: ChatIntent
    conversation_id: str | None = None