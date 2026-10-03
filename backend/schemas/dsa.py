from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DSATopic(str, Enum):
    ARRAYS = "Arrays"
    STRINGS = "Strings"
    HASH_MAP = "HashMap"
    HASH_SET = "HashSet"
    LINKED_LIST = "Linked List"
    STACK = "Stack"
    QUEUE = "Queue"
    BINARY_TREE = "Binary Tree"
    BST = "BST"
    HEAP = "Heap"
    GRAPH = "Graph"
    RECURSION = "Recursion"
    SORTING = "Sorting"
    SEARCHING = "Searching"
    DYNAMIC_PROGRAMMING = "Dynamic Programming"


class DSADifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class DSASessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class DSAQuestionRequest(BaseModel):
    topic: DSATopic = DSATopic.ARRAYS
    difficulty: DSADifficulty = DSADifficulty.EASY

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())
        aliases = {
            "array": "Arrays",
            "hash map": "HashMap",
            "hash set": "HashSet",
            "linkedlist": "Linked List",
            "tree": "Binary Tree",
            "binary trees": "Binary Tree",
            "binary search tree": "BST",
            "heaps": "Heap",
            "graphs": "Graph",
            "dp": "Dynamic Programming",
        }
        for topic in DSATopic:
            if normalized == topic.value.lower():
                return topic
        return aliases.get(normalized, value)

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            for difficulty in DSADifficulty:
                if normalized == difficulty.value.lower():
                    return difficulty
        return value


class DSASessionStartRequest(DSAQuestionRequest):
    total_questions: int = Field(default=5, ge=1, le=20)
    student_id: int | None = Field(default=None, gt=0)


class DSAExample(BaseModel):
    input: str = Field(min_length=1)
    output: str = Field(min_length=1)
    explanation: str | None = None


class DSAQuestionResponse(BaseModel):
    question_id: str
    topic: DSATopic
    difficulty: DSADifficulty
    title: str = Field(min_length=3, max_length=160)
    problem: str = Field(min_length=20)
    examples: list[DSAExample] = Field(min_length=1, max_length=5)
    constraints: list[str] = Field(min_length=1)
    expected_concepts: list[str] = Field(min_length=1)


class DSAHintRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    attempt: str = Field(max_length=12000)
    hint_level: int = Field(default=1, ge=1, le=3)
    session_id: str | None = Field(default=None, max_length=64)


class DSAHintResponse(BaseModel):
    question_id: str
    hint: str = Field(min_length=1)
    hint_level: int = Field(ge=1, le=3)


class DSAExplanationRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    attempt: str = Field(min_length=1, max_length=12000)
    include_solution: bool = False

    @field_validator("attempt")
    @classmethod
    def attempt_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Attempt must not be empty.")
        return value


class DSAExplanationResponse(BaseModel):
    question_id: str
    is_correct: bool
    assessment: str = Field(min_length=1)
    logical_mistakes: list[str]
    edge_cases: list[str]
    time_complexity: str = Field(min_length=1)
    space_complexity: str = Field(min_length=1)
    improvements: list[str]
    reference_solution: str | None = None


class DSASessionQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: DSAQuestionResponse


class DSASessionAttemptRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    attempt: str = Field(min_length=1, max_length=12000)
    include_solution: bool = False

    @field_validator("attempt")
    @classmethod
    def attempt_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Attempt must not be empty.")
        return value


class DSASessionAttemptResponse(BaseModel):
    session_id: str
    question_number: int
    is_correct: bool
    feedback: str
    mistakes: list[str]
    edge_cases: list[str]
    time_complexity: str
    space_complexity: str
    questions_attempted: int
    questions_correct: int
    hints_used: int
    status: DSASessionStatus
    reference_solution: str | None = None


class DSASessionSummaryResponse(BaseModel):
    session_id: str
    status: DSASessionStatus
    topic: DSATopic
    difficulty: DSADifficulty
    total_questions: int
    questions_attempted: int
    questions_correct: int
    accuracy: float
    hints_used: int
    current_question_number: int
    created_at: datetime