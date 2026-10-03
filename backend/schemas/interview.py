from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class InterviewMode(str, Enum):
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    PROJECT = "PROJECT"


class InterviewTopic(str, Enum):
    DSA = "DSA"
    DBMS = "DBMS"
    OPERATING_SYSTEMS = "Operating Systems"
    COMPUTER_NETWORKS = "Computer Networks"
    OOP = "OOP"
    JAVA = "Java"
    PYTHON = "Python"
    AI_ML = "AI/ML"
    TELL_ME_ABOUT_YOURSELF = "Tell Me About Yourself"
    STRENGTHS_AND_WEAKNESSES = "Strengths and Weaknesses"
    MOTIVATION = "Motivation"
    BEHAVIORAL = "Behavioral"
    TEAMWORK = "Teamwork"
    LEADERSHIP = "Leadership"
    CAREER_GOALS = "Career Goals"
    CONFLICT_RESOLUTION = "Conflict Resolution"
    PROJECT_INTRODUCTION = "Project Introduction"
    ARCHITECTURE = "Architecture"
    TECHNOLOGY_CHOICES = "Technology Choices"
    IMPLEMENTATION = "Implementation"
    CHALLENGES = "Challenges"
    TESTING = "Testing"
    DEPLOYMENT = "Deployment"
    FUTURE_IMPROVEMENTS = "Future Improvements"


class InterviewDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class InterviewQuestionType(str, Enum):
    OPEN_ENDED = "OPEN_ENDED"
    FOLLOW_UP = "FOLLOW_UP"


class InterviewSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


TOPIC_MODES = {
    InterviewTopic.DSA: InterviewMode.TECHNICAL,
    InterviewTopic.DBMS: InterviewMode.TECHNICAL,
    InterviewTopic.OPERATING_SYSTEMS: InterviewMode.TECHNICAL,
    InterviewTopic.COMPUTER_NETWORKS: InterviewMode.TECHNICAL,
    InterviewTopic.OOP: InterviewMode.TECHNICAL,
    InterviewTopic.JAVA: InterviewMode.TECHNICAL,
    InterviewTopic.PYTHON: InterviewMode.TECHNICAL,
    InterviewTopic.AI_ML: InterviewMode.TECHNICAL,
    InterviewTopic.TELL_ME_ABOUT_YOURSELF: InterviewMode.HR,
    InterviewTopic.STRENGTHS_AND_WEAKNESSES: InterviewMode.HR,
    InterviewTopic.MOTIVATION: InterviewMode.HR,
    InterviewTopic.BEHAVIORAL: InterviewMode.HR,
    InterviewTopic.TEAMWORK: InterviewMode.HR,
    InterviewTopic.LEADERSHIP: InterviewMode.HR,
    InterviewTopic.CAREER_GOALS: InterviewMode.HR,
    InterviewTopic.CONFLICT_RESOLUTION: InterviewMode.HR,
    InterviewTopic.PROJECT_INTRODUCTION: InterviewMode.PROJECT,
    InterviewTopic.ARCHITECTURE: InterviewMode.PROJECT,
    InterviewTopic.TECHNOLOGY_CHOICES: InterviewMode.PROJECT,
    InterviewTopic.IMPLEMENTATION: InterviewMode.PROJECT,
    InterviewTopic.CHALLENGES: InterviewMode.PROJECT,
    InterviewTopic.TESTING: InterviewMode.PROJECT,
    InterviewTopic.DEPLOYMENT: InterviewMode.PROJECT,
    InterviewTopic.FUTURE_IMPROVEMENTS: InterviewMode.PROJECT,
}


class InterviewQuestionRequest(BaseModel):
    mode: InterviewMode
    topic: InterviewTopic
    difficulty: InterviewDifficulty = InterviewDifficulty.MEDIUM
    project_name: str | None = Field(default=None, max_length=200)
    project_description: str | None = Field(default=None, max_length=8000)

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().replace("-", "_").replace(" ", "_").upper()
            for mode in InterviewMode:
                if normalized == mode.value:
                    return mode
        return value

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = " ".join(value.strip().replace("_", " ").replace("-", " ").lower().split())
            for topic in InterviewTopic:
                if normalized == topic.value.lower():
                    return topic
        return value

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, value: object) -> object:
        if isinstance(value, str):
            for difficulty in InterviewDifficulty:
                if value.strip().lower() == difficulty.value.lower():
                    return difficulty
        return value

    @model_validator(mode="after")
    def topic_must_match_mode(self) -> InterviewQuestionRequest:
        if TOPIC_MODES[self.topic] != self.mode:
            raise ValueError(f"Topic '{self.topic.value}' does not belong to mode '{self.mode.value}'.")
        return self


class InterviewQuestionResponse(BaseModel):
    question_id: str
    question: str = Field(min_length=10)
    mode: InterviewMode
    topic: InterviewTopic
    question_type: InterviewQuestionType


class InterviewAttemptRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(min_length=1, max_length=12000)

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Answer must not be empty.")
        return value


class InterviewFollowUpRequest(InterviewAttemptRequest):
    pass


class InterviewEvaluationResponse(BaseModel):
    question_id: str
    score: float = Field(ge=0, le=10)
    strengths: list[str]
    weaknesses: list[str]
    feedback: str = Field(min_length=1)
    missing_points: list[str]
    suggested_answer: str = Field(min_length=1)
    communication_feedback: str = Field(min_length=1)
    technical_feedback: str = Field(min_length=1)


class InterviewSessionStartRequest(InterviewQuestionRequest):
    total_questions: int = Field(default=5, ge=1, le=20)
    student_id: int | None = Field(default=None, gt=0)


class InterviewSessionQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: InterviewQuestionResponse


class InterviewSessionAnswerResponse(InterviewEvaluationResponse):
    session_id: str
    question_number: int
    questions_attempted: int
    average_score: float
    status: InterviewSessionStatus


class InterviewSessionSummaryResponse(BaseModel):
    session_id: str
    mode: InterviewMode
    topic: InterviewTopic
    total_questions: int
    questions_answered: int
    average_score: float
    status: InterviewSessionStatus
    created_at: datetime
    strengths: list[str]
    areas_to_improve: list[str]
    overall_feedback: str