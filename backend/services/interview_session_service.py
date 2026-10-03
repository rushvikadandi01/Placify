import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..schemas.interview import (
    InterviewAttemptRequest,
    InterviewDifficulty,
    InterviewEvaluationResponse,
    InterviewFollowUpRequest,
    InterviewMode,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    InterviewSessionAnswerResponse,
    InterviewSessionQuestionResponse,
    InterviewSessionStartRequest,
    InterviewSessionStatus,
    InterviewSessionSummaryResponse,
    InterviewTopic,
)
from ..schemas.progress import TrainingType
from .interview_agent import InterviewAgent, InterviewQuestionNotFoundError, interview_agent
from .progress_service import ProgressService, progress_service


class InterviewSessionNotFoundError(Exception):
    """Raised when an interview session ID is unknown."""


class InterviewSessionConflictError(Exception):
    """Raised when an operation is not valid for the session's current state."""


class InterviewRepeatedQuestionError(Exception):
    """Raised when the AI repeatedly returns a previous session question."""


@dataclass
class InterviewPracticeSession:
    session_id: str
    mode: InterviewMode
    topic: InterviewTopic
    difficulty: InterviewDifficulty
    total_questions: int
    current_question_number: int
    current_question: InterviewQuestionResponse
    student_id: int | None = None
    project_name: str | None = None
    project_description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    questions_attempted: int = 0
    average_score: float = 0.0
    status: InterviewSessionStatus = InterviewSessionStatus.ACTIVE
    questions: list[InterviewQuestionResponse] = field(default_factory=list)
    evaluations: list[InterviewEvaluationResponse] = field(default_factory=list)
    attempted_question_ids: set[str] = field(default_factory=set)
    last_answer: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class InterviewSessionService:
    def __init__(
        self,
        agent: InterviewAgent = interview_agent,
        progress: ProgressService = progress_service,
    ):
        self.agent = agent
        self.progress = progress
        self._sessions: dict[str, InterviewPracticeSession] = {}

    async def start(self, request: InterviewSessionStartRequest, db: Session) -> InterviewSessionQuestionResponse:
        self.progress.validate_student(db, request.student_id)
        question_request = InterviewQuestionRequest(
            mode=request.mode,
            topic=request.topic,
            difficulty=request.difficulty,
            project_name=request.project_name,
            project_description=request.project_description,
        )
        question = await self.agent.generate_question(question_request)
        session = InterviewPracticeSession(
            session_id=str(uuid4()),
            mode=request.mode,
            topic=request.topic,
            difficulty=request.difficulty,
            total_questions=request.total_questions,
            current_question_number=1,
            current_question=question,
            student_id=request.student_id,
            project_name=request.project_name,
            project_description=request.project_description,
            questions=[question],
        )
        self._sessions[session.session_id] = session
        return self._question_response(session)

    async def submit_answer(
        self,
        session_id: str,
        request: InterviewAttemptRequest,
        db: Session,
    ) -> InterviewSessionAnswerResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            self._require_current_question(session, request.question_id)
            if request.question_id in session.attempted_question_ids:
                raise InterviewSessionConflictError("An answer has already been submitted for this question.")
            evaluation = await self.agent.evaluate_answer(request)
            questions_attempted = session.questions_attempted + 1
            evaluations = [*session.evaluations, evaluation]
            average_score = round(sum(item.score for item in evaluations) / len(evaluations), 2)
            completed = questions_attempted >= session.total_questions
            if completed:
                self.progress.record_progress(
                    db,
                    session_id=session.session_id,
                    student_id=session.student_id,
                    training_type=TrainingType.INTERVIEW,
                    category=session.mode.value,
                    topic=session.topic.value,
                    difficulty=session.difficulty.value,
                    questions_attempted=questions_attempted,
                    questions_correct=None,
                    accuracy=None,
                    average_score=average_score,
                )
            session.attempted_question_ids.add(request.question_id)
            session.questions_attempted = questions_attempted
            session.evaluations = evaluations
            session.average_score = average_score
            session.last_answer = request.answer
            if completed:
                session.status = InterviewSessionStatus.COMPLETED
            return InterviewSessionAnswerResponse(
                **evaluation.model_dump(),
                session_id=session.session_id,
                question_number=session.current_question_number,
                questions_attempted=session.questions_attempted,
                average_score=session.average_score,
                status=session.status,
            )

    async def next_question(self, session_id: str) -> InterviewSessionQuestionResponse:
        session = self._get_session(session_id)
        async with session.lock:
            self._require_active(session)
            if session.current_question.question_id not in session.attempted_question_ids:
                raise InterviewSessionConflictError("Submit an answer to the current question before requesting the next one.")
            if not session.last_answer:
                raise InterviewSessionConflictError("The previous answer is required to continue this interview.")

            request = InterviewFollowUpRequest(
                question_id=session.current_question.question_id,
                answer=session.last_answer,
            )
            previous_questions = tuple(question.question for question in session.questions)
            for _ in range(3):
                question = await self.agent.generate_follow_up(request, avoid_questions=previous_questions)
                if self._signature(question) not in {self._signature(item) for item in session.questions}:
                    break
            else:
                raise InterviewRepeatedQuestionError(
                    "The AI returned a repeated interview question. Please request the next question again."
                )

            session.current_question_number += 1
            session.current_question = question
            session.questions.append(question)
            return self._question_response(session)

    def get_summary(self, session_id: str) -> InterviewSessionSummaryResponse:
        session = self._get_session(session_id)
        strengths = self._unique_items(
            [item for evaluation in session.evaluations for item in evaluation.strengths]
        )
        areas_to_improve = self._unique_items(
            [
                item
                for evaluation in session.evaluations
                for item in evaluation.weaknesses + evaluation.missing_points
            ]
        )
        if session.status == InterviewSessionStatus.COMPLETED:
            overall_feedback = (
                f"You completed {session.total_questions} interview questions with an average score of "
                f"{session.average_score}/10. Keep practicing the areas listed below and support your answers "
                "with specific examples. This is practice feedback, not a prediction of interview outcomes."
            )
        else:
            overall_feedback = (
                f"Your interview is in progress: {session.questions_attempted} of {session.total_questions} "
                "questions answered so far."
            )
        return InterviewSessionSummaryResponse(
            session_id=session.session_id,
            mode=session.mode,
            topic=session.topic,
            total_questions=session.total_questions,
            questions_answered=session.questions_attempted,
            average_score=session.average_score,
            status=session.status,
            created_at=session.created_at,
            strengths=strengths[:6],
            areas_to_improve=areas_to_improve[:6],
            overall_feedback=overall_feedback,
        )

    def _get_session(self, session_id: str) -> InterviewPracticeSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise InterviewSessionNotFoundError("Interview session not found. Start a new session and retry.")
        return session

    @staticmethod
    def _require_active(session: InterviewPracticeSession) -> None:
        if session.status != InterviewSessionStatus.ACTIVE:
            raise InterviewSessionConflictError("This interview session is already completed.")

    @staticmethod
    def _require_current_question(session: InterviewPracticeSession, question_id: str) -> None:
        if question_id != session.current_question.question_id:
            raise InterviewSessionConflictError("question_id must match the session's current question.")

    @staticmethod
    def _signature(question: InterviewQuestionResponse) -> str:
        return re.sub(r"\s+", " ", question.question).strip().casefold()

    @staticmethod
    def _unique_items(items: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = item.strip().casefold()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(item.strip())
        return unique

    @staticmethod
    def _question_response(session: InterviewPracticeSession) -> InterviewSessionQuestionResponse:
        return InterviewSessionQuestionResponse(
            session_id=session.session_id,
            question_number=session.current_question_number,
            total_questions=session.total_questions,
            question=session.current_question,
        )


interview_session_service = InterviewSessionService()