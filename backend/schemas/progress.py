from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class TrainingType(str, Enum):
    DSA = "DSA"
    APTITUDE = "APTITUDE"
    INTERVIEW = "INTERVIEW"


class ProgressRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    student_id: int | None
    training_type: TrainingType
    category: str | None
    topic: str
    difficulty: str | None
    questions_attempted: int | None
    questions_correct: int | None
    accuracy: float | None
    average_score: float | None
    status: str
    created_at: datetime


class ProgressSummaryResponse(BaseModel):
    student_id: int
    total_sessions: int
    total_questions: int
    total_correct: int
    overall_accuracy: float
    average_interview_score: float | None
    dsa_sessions: int
    aptitude_sessions: int
    interview_sessions: int


class TopicProgressResponse(BaseModel):
    training_type: TrainingType
    category: str | None
    topic: str
    attempted: int
    correct: int | None
    accuracy: float | None
    average_score: float | None