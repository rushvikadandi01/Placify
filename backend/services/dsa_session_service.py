import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..schemas.dsa import (
    DSAExplanationRequest,
    DSAHintRequest,
    DSAQuestionRequest,
    DSAQuestionResponse,
    DSADifficulty,
    DSASessionAttemptRequest,
    DSASessionAttemptResponse,
    DSASessionQuestionResponse,
    DSASessionStartRequest,
    DSASessionStatus,
    DSASessionSummaryResponse,
    DSATopic,
)
from ..schemas.progress import TrainingType
from .dsa_agent import DSAAgent, DSAQuestionNotFoundError, dsa_agent
from .progress_service import ProgressService, progress_service


class DSASessionNotFoundError(Exception):
    """Raised when a practice session ID is unknown."""


class DSASessionConflictError(Exception):
    """Raised when an operation does not match the current session state."""


class DSASessionQuestionRepeatError(Exception):
    """Raised when the AI repeatedly returns an earlier question."""


@dataclass
class DSAPracticeSession:
    session_id: str
    topic: DSATopic
    difficulty: DSADifficulty
    current_question_number: int
    total_questions: int
    current_question: DSAQuestionResponse
    student_id: int | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    questions_attempted: int = 0
    questions_correct: int = 0
    hints_used: int = 0
    status: DSASessionStatus = DSASessionStatus.ACTIVE
    questions: list[DSAQuestionResponse] = field(default_factory=list)
    attempted_question_ids: set[str] = field(default_factory=set)
    question_signatures: set[str] = field(default_factory=set)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class DSASessionService:
    def __init__(
        self,
        agent: DSAAgent = dsa_agent,
        progress: ProgressService = progress_service,
    ):
        self.agent = agent
        self.progress = progress
        self._sessions: dict[str, DSAPracticeSession] = {}

    async def start(self, request: DSASessionStartRequest, db: Session) -> DSASessionQuestionResponse:
        self.progress.validate_student(db, request.student_id)
        question_request = DSAQuestionRequest(topic=request.topic, difficulty=request.difficulty)
        question = await self.agent.generate_question(question_request)
        session_id = str(uuid4())
        session = DSAPracticeSession(
            session_id=session_id,
            topic=request.topic,
            difficulty=request.difficulty,
            current_question_number=1,
            total_questions=request.total_questions,
            current_question=question,
            student_id=request.student_id,
            questions=[question],
            question_signatures={self._question_signature(question)},
        )
        self._sessions[session_id] = session
        return self._question_response(session)

    async def get_hint(self, request: DSAHintRequest):
        if request.session_id is None:
            return await self.agent.get_hint(request)

        session = self._get_session(request.session_id)
        async with session.lock:
            self._require_active(session)
            if request.question_id != session.current_question.question_id:
                raise DSASessionConflictError("Hint question_id must match the session's current question.")
            hint = await self.agent.get_hint(request)
            session.hints_used += 1
            return hint

    async def submit_attempt(
        self,
        session_id: str,
        request: DSASessionAttemptRequest,
        db: Session,
    ) -> DSASessionAttemptResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            if request.question_id != session.current_question.question_id:
                raise DSASessionConflictError("question_id must match the session's current question.")
            if request.question_id in session.attempted_question_ids:
                raise DSASessionConflictError("An attempt has already been submitted for this question.")

            explanation = await self.agent.explain_attempt(
                DSAExplanationRequest(
                    question_id=request.question_id,
                    attempt=request.attempt,
                    include_solution=request.include_solution,
                )
            )
            questions_attempted = session.questions_attempted + 1
            questions_correct = session.questions_correct + int(explanation.is_correct)
            completed = questions_attempted >= session.total_questions
            if completed:
                self.progress.record_progress(
                    db,
                    session_id=session.session_id,
                    student_id=session.student_id,
                    training_type=TrainingType.DSA,
                    category=None,
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
                session.status = DSASessionStatus.COMPLETED

            return DSASessionAttemptResponse(
                session_id=session.session_id,
                question_number=session.current_question_number,
                is_correct=explanation.is_correct,
                feedback=explanation.assessment,
                mistakes=explanation.logical_mistakes,
                edge_cases=explanation.edge_cases,
                time_complexity=explanation.time_complexity,
                space_complexity=explanation.space_complexity,
                questions_attempted=session.questions_attempted,
                questions_correct=session.questions_correct,
                hints_used=session.hints_used,
                status=session.status,
                reference_solution=explanation.reference_solution,
            )

    async def next_question(self, session_id: str) -> DSASessionQuestionResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            if session.current_question.question_id not in session.attempted_question_ids:
                raise DSASessionConflictError("Submit an attempt for the current question before requesting the next one.")

            question_request = DSAQuestionRequest(topic=session.topic, difficulty=session.difficulty)
            question = await self._generate_distinct_question(session, question_request)
            session.current_question_number += 1
            session.current_question = question
            session.questions.append(question)
            session.question_signatures.add(self._question_signature(question))
            return self._question_response(session)

    def get_summary(self, session_id: str) -> DSASessionSummaryResponse:
        session = self._get_session(session_id)
        accuracy = (
            round(session.questions_correct / session.questions_attempted * 100, 2)
            if session.questions_attempted
            else 0.0
        )
        return DSASessionSummaryResponse(
            session_id=session.session_id,
            status=session.status,
            topic=session.topic,
            difficulty=session.difficulty,
            total_questions=session.total_questions,
            questions_attempted=session.questions_attempted,
            questions_correct=session.questions_correct,
            accuracy=accuracy,
            hints_used=session.hints_used,
            current_question_number=session.current_question_number,
            created_at=session.created_at,
        )

    async def _generate_distinct_question(
        self,
        session: DSAPracticeSession,
        request: DSAQuestionRequest,
    ) -> DSAQuestionResponse:
        prior_titles = tuple(question.title for question in session.questions)
        for _ in range(3):
            question = await self.agent.generate_question(request, avoid_titles=prior_titles)
            signature = self._question_signature(question)
            if signature not in session.question_signatures:
                return question
        raise DSASessionQuestionRepeatError(
            "The AI returned a repeated question. Please request the next question again."
        )

    def _get_session(self, session_id: str) -> DSAPracticeSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise DSASessionNotFoundError("Practice session not found. Start a new session and retry.")
        return session

    @staticmethod
    def _require_active(session: DSAPracticeSession) -> None:
        if session.status != DSASessionStatus.ACTIVE:
            raise DSASessionConflictError("This practice session is already completed.")

    @staticmethod
    def _question_signature(question: DSAQuestionResponse) -> str:
        return re.sub(r"\s+", " ", question.problem).strip().casefold()

    @staticmethod
    def _question_response(session: DSAPracticeSession) -> DSASessionQuestionResponse:
        return DSASessionQuestionResponse(
            session_id=session.session_id,
            question_number=session.current_question_number,
            total_questions=session.total_questions,
            question=session.current_question,
        )


dsa_session_service = DSASessionService()