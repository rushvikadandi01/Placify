from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AptitudeCategory(str, Enum):
    QUANTITATIVE = "QUANTITATIVE"
    LOGICAL_REASONING = "LOGICAL_REASONING"
    VERBAL = "VERBAL"


class AptitudeTopic(str, Enum):
    PERCENTAGES = "Percentages"
    PROFIT_AND_LOSS = "Profit and Loss"
    RATIO_AND_PROPORTION = "Ratio and Proportion"
    AVERAGES = "Averages"
    TIME_AND_WORK = "Time and Work"
    TIME_SPEED_DISTANCE = "Time Speed Distance"
    SIMPLE_INTEREST = "Simple Interest"
    COMPOUND_INTEREST = "Compound Interest"
    NUMBER_SYSTEM = "Number System"
    NUMBER_SERIES = "Number Series"
    CODING_DECODING = "Coding Decoding"
    BLOOD_RELATIONS = "Blood Relations"
    DIRECTIONS = "Directions"
    SYLLOGISMS = "Syllogisms"
    SEATING_ARRANGEMENT = "Seating Arrangement"
    GRAMMAR = "Grammar"
    VOCABULARY = "Vocabulary"
    SENTENCE_CORRECTION = "Sentence Correction"
    READING_COMPREHENSION = "Reading Comprehension"


class AptitudeDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class AptitudeSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


TOPIC_CATEGORIES = {
    AptitudeTopic.PERCENTAGES: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.PROFIT_AND_LOSS: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.RATIO_AND_PROPORTION: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.AVERAGES: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.TIME_AND_WORK: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.TIME_SPEED_DISTANCE: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.SIMPLE_INTEREST: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.COMPOUND_INTEREST: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.NUMBER_SYSTEM: AptitudeCategory.QUANTITATIVE,
    AptitudeTopic.NUMBER_SERIES: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.CODING_DECODING: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.BLOOD_RELATIONS: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.DIRECTIONS: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.SYLLOGISMS: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.SEATING_ARRANGEMENT: AptitudeCategory.LOGICAL_REASONING,
    AptitudeTopic.GRAMMAR: AptitudeCategory.VERBAL,
    AptitudeTopic.VOCABULARY: AptitudeCategory.VERBAL,
    AptitudeTopic.SENTENCE_CORRECTION: AptitudeCategory.VERBAL,
    AptitudeTopic.READING_COMPREHENSION: AptitudeCategory.VERBAL,
}


class AptitudeQuestionRequest(BaseModel):
    category: AptitudeCategory
    topic: AptitudeTopic
    difficulty: AptitudeDifficulty = AptitudeDifficulty.EASY

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().replace("-", "_").replace(" ", "_").upper()
            for category in AptitudeCategory:
                if normalized == category.value:
                    return category
        return value

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = " ".join(value.strip().replace("-", " ").replace("_", " ").lower().split())
            for topic in AptitudeTopic:
                if normalized == topic.value.lower():
                    return topic
        return value

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, value: object) -> object:
        if isinstance(value, str):
            for difficulty in AptitudeDifficulty:
                if value.strip().lower() == difficulty.value.lower():
                    return difficulty
        return value

    @model_validator(mode="after")
    def topic_must_match_category(self):
        if TOPIC_CATEGORIES[self.topic] != self.category:
            raise ValueError(f"Topic '{self.topic.value}' does not belong to category '{self.category.value}'.")
        return self


class AptitudeQuestionResponse(BaseModel):
    question_id: str
    question: str = Field(min_length=10)
    options: list[str] = Field(min_length=4, max_length=4)
    category: AptitudeCategory
    topic: AptitudeTopic
    difficulty: AptitudeDifficulty


class AptitudeAttemptRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    selected_answer: str = Field(min_length=1, max_length=500)

    @field_validator("selected_answer")
    @classmethod
    def selected_answer_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Selected answer must not be empty.")
        return value


class AptitudeExplainRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)


class AptitudeEvaluationResponse(BaseModel):
    question_id: str
    is_correct: bool
    selected_answer: str
    correct_answer: str
    explanation: str
    learning_feedback: str
    improvement_tip: str | None = None


class AptitudeExplanationResponse(BaseModel):
    question_id: str
    correct_answer: str
    explanation: str
    learning_feedback: str
    improvement_tip: str | None = None


class AptitudeSessionStartRequest(AptitudeQuestionRequest):
    total_questions: int = Field(default=5, ge=1, le=20)
    student_id: int | None = Field(default=None, gt=0)


class AptitudeSessionQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: AptitudeQuestionResponse


class AptitudeSessionAttemptRequest(AptitudeAttemptRequest):
    pass


class AptitudeSessionAttemptResponse(AptitudeEvaluationResponse):
    session_id: str
    question_number: int
    questions_attempted: int
    questions_correct: int
    status: AptitudeSessionStatus


class AptitudeSessionSummaryResponse(BaseModel):
    session_id: str
    category: AptitudeCategory
    topic: AptitudeTopic
    difficulty: AptitudeDifficulty
    current_question_number: int
    total_questions: int
    questions_attempted: int
    questions_correct: int
    accuracy: float
    status: AptitudeSessionStatus
    created_at: datetime