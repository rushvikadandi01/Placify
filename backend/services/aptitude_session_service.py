import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..schemas.aptitude import (
    AptitudeAttemptRequest,
    AptitudeCategory,
    AptitudeDifficulty,
    AptitudeEvaluationResponse,
    AptitudeQuestionRequest,
    AptitudeQuestionResponse,
    AptitudeSessionAttemptRequest,
    AptitudeSessionAttemptResponse,
    AptitudeSessionQuestionResponse,
    AptitudeSessionStartRequest,
    AptitudeSessionStatus,
    AptitudeSessionSummaryResponse,
    AptitudeTopic,
)
from ..schemas.progress import TrainingType
from .aptitude_agent import (
    AptitudeAgent,
    AptitudeQuestionNotFoundError,
    aptitude_agent,
)
from .progress_service import ProgressService, progress_service


class AptitudeSessionNotFoundError(Exception):
    """Raised when an aptitude session ID is unknown."""


class AptitudeSessionConflictError(Exception):
    """Raised when an operation does not match the current session state."""


class AptitudeRepeatedQuestionError(Exception):
    """Raised when the AI repeatedly generates an earlier session question."""


@dataclass
class AptitudePracticeSession:
    session_id: str
    category: AptitudeCategory
    topic: AptitudeTopic
    difficulty: AptitudeDifficulty
    current_question_number: int
    total_questions: int
    current_question: AptitudeQuestionResponse
    student_id: int | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    questions_attempted: int = 0
    questions_correct: int = 0
    status: AptitudeSessionStatus = AptitudeSessionStatus.ACTIVE
    questions: list[AptitudeQuestionResponse] = field(default_factory=list)
    attempted_question_ids: set[str] = field(default_factory=set)
    question_signatures: set[str] = field(default_factory=set)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class AptitudeSessionService:
    def __init__(
        self,
        agent: AptitudeAgent = aptitude_agent,
        progress: ProgressService = progress_service,
    ):
        self.agent = agent
        self.progress = progress
        self._sessions: dict[str, AptitudePracticeSession] = {}

    async def start(self, request: AptitudeSessionStartRequest, db: Session) -> AptitudeSessionQuestionResponse:
        self.progress.validate_student(db, request.student_id)
        question_request = AptitudeQuestionRequest(
            category=request.category,
            topic=request.topic,
            difficulty=request.difficulty,
        )
        question = await self.agent.generate_question(question_request)
        session = AptitudePracticeSession(
            session_id=str(uuid4()),
            category=request.category,
            topic=request.topic,
            difficulty=request.difficulty,
            current_question_number=1,
            total_questions=request.total_questions,
            current_question=question,
            student_id=request.student_id,
            questions=[question],
            question_signatures={self._signature(question)},
        )
        self._sessions[session.session_id] = session
        return self._question_response(session)

    async def submit_attempt(
        self,
        session_id: str,
        request: AptitudeSessionAttemptRequest,
        db: Session,
    ) -> AptitudeSessionAttemptResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            self._require_current_question(session, request.question_id)
            if request.question_id in session.attempted_question_ids:
                raise AptitudeSessionConflictError("An attempt has already been submitted for this question.")
            evaluation = self.agent.evaluate_attempt(
                AptitudeAttemptRequest(
                    question_id=request.question_id,
                    selected_answer=request.selected_answer,
                )
            )
            questions_attempted = session.questions_attempted + 1
            questions_correct = session.questions_correct + int(evaluation.is_correct)
            completed = questions_attempted >= session.total_questions
            if completed:
                self.progress.record_progress(
                    db,
                    session_id=session.session_id,
                    student_id=session.student_id,
                    training_type=TrainingType.APTITUDE,
                    category=session.category.value,
                    topic=session.topic.value,
                    difficulty=session.difficulty.value,
                    questions_attempted=questions_attempted,
                    questions_correct=questions_correct,
                    accuracy=round(questions_correct / questions_attempted * 100, 2),
                    average_score=None,
                )
            session.attempted_question_ids.add(request.question_id)
            session.questions_attempted = questions_attempted
            session.questions_correct = questions_correct
            if completed:
                session.status = AptitudeSessionStatus.COMPLETED
            return self._attempt_response(session, evaluation)

    async def next_question(self, session_id: str) -> AptitudeSessionQuestionResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            if session.current_question.question_id not in session.attempted_question_ids:
                raise AptitudeSessionConflictError("Submit an attempt for the current question before requesting the next one.")
            question_request = AptitudeQuestionRequest(
                category=session.category,
                topic=session.topic,
                difficulty=session.difficulty,
            )
            question = await self._generate_distinct_question(session, question_request)
            session.current_question_number += 1
            session.current_question = question
            session.questions.append(question)
            session.question_signatures.add(self._signature(question))
            return self._question_response(session)

    def get_summary(self, session_id: str) -> AptitudeSessionSummaryResponse:
        session = self._get_session(session_id)
        accuracy = (
            round(session.questions_correct / session.questions_attempted * 100, 2)
            if session.questions_attempted
            else 0.0
        )
        return AptitudeSessionSummaryResponse(
            session_id=session.session_id,
            category=session.category,
            topic=session.topic,
            difficulty=session.difficulty,
            current_question_number=session.current_question_number,
            total_questions=session.total_questions,
            questions_attempted=session.questions_attempted,
            questions_correct=session.questions_correct,
            accuracy=accuracy,
            status=session.status,
            created_at=session.created_at,
        )

    async def _generate_distinct_question(
        self,
        session: AptitudePracticeSession,
        request: AptitudeQuestionRequest,
    ) -> AptitudeQuestionResponse:
        prior_questions = tuple(question.question for question in session.questions)
        for _ in range(3):
            question = await self.agent.generate_question(request, avoid_questions=prior_questions)
            if self._signature(question) not in session.question_signatures:
                return question
        raise AptitudeRepeatedQuestionError(
            "The AI returned a repeated aptitude question. Please request the next question again."
        )

    def _get_session(self, session_id: str) -> AptitudePracticeSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AptitudeSessionNotFoundError("Aptitude session not found. Start a new session and retry.")
        return session

    @staticmethod
    def _require_active(session: AptitudePracticeSession) -> None:
        if session.status != AptitudeSessionStatus.ACTIVE:
            raise AptitudeSessionConflictError("This aptitude session is already completed.")

    @staticmethod
    def _require_current_question(session: AptitudePracticeSession, question_id: str) -> None:
        if question_id != session.current_question.question_id:
            raise AptitudeSessionConflictError("question_id must match the session's current question.")

    @staticmethod
    def _signature(question: AptitudeQuestionResponse) -> str:
        return re.sub(r"\s+", " ", question.question).strip().casefold()

    @staticmethod
    def _question_response(session: AptitudePracticeSession) -> AptitudeSessionQuestionResponse:
        return AptitudeSessionQuestionResponse(
            session_id=session.session_id,
            question_number=session.current_question_number,
            total_questions=session.total_questions,
            question=session.current_question,
        )

    @staticmethod
    def _attempt_response(
        session: AptitudePracticeSession,
        evaluation: AptitudeEvaluationResponse,
    ) -> AptitudeSessionAttemptResponse:
        return AptitudeSessionAttemptResponse(
            **evaluation.model_dump(),
            session_id=session.session_id,
            question_number=session.current_question_number,
            questions_attempted=session.questions_attempted,
            questions_correct=session.questions_correct,
            status=session.status,
        )


aptitude_session_service = AptitudeSessionService()