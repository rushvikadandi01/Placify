from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.interview import (
    InterviewAttemptRequest,
    InterviewEvaluationResponse,
    InterviewFollowUpRequest,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    InterviewSessionAnswerResponse,
    InterviewSessionQuestionResponse,
    InterviewSessionStartRequest,
    InterviewSessionSummaryResponse,
)
from ..services.ai_service import AIConfigurationError, AIProviderError, AIProviderTimeoutError
from ..services.interview_agent import (
    InterviewAgentResponseError,
    InterviewQuestionNotFoundError,
    interview_agent,
)
from ..services.interview_session_service import (
    InterviewRepeatedQuestionError,
    InterviewSessionConflictError,
    InterviewSessionNotFoundError,
    interview_session_service,
)
from ..services.progress_service import ProgressStudentNotFoundError

router = APIRouter(prefix="/interview")


def _ai_http_error(error: Exception) -> HTTPException:
    if isinstance(error, AIConfigurationError):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, AIProviderTimeoutError):
        return HTTPException(status_code=504, detail="The AI provider timed out. Please try again.")
    if isinstance(error, InterviewAgentResponseError):
        return HTTPException(status_code=502, detail=str(error))
    return HTTPException(status_code=502, detail="The AI provider could not complete the interview request.")


@router.post("/question", response_model=InterviewQuestionResponse)
async def generate_question(request: InterviewQuestionRequest) -> InterviewQuestionResponse:
    try:
        return await interview_agent.generate_question(request)
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/evaluate", response_model=InterviewEvaluationResponse)
async def evaluate_answer(request: InterviewAttemptRequest) -> InterviewEvaluationResponse:
    try:
        return await interview_agent.evaluate_answer(request)
    except InterviewQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/follow-up", response_model=InterviewQuestionResponse)
async def generate_follow_up(request: InterviewFollowUpRequest) -> InterviewQuestionResponse:
    try:
        return await interview_agent.generate_follow_up(request)
    except InterviewQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/session/start", response_model=InterviewSessionQuestionResponse)
async def start_session(
    request: InterviewSessionStartRequest,
    db: Session = Depends(get_db),
) -> InterviewSessionQuestionResponse:
    try:
        return await interview_session_service.start(request, db)
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/session/{session_id}/answer", response_model=InterviewSessionAnswerResponse)
async def answer_session_question(
    session_id: str,
    request: InterviewAttemptRequest,
    db: Session = Depends(get_db),
) -> InterviewSessionAnswerResponse:
    try:
        return await interview_session_service.submit_answer(session_id, request, db)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except InterviewSessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except InterviewQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/session/{session_id}/next", response_model=InterviewSessionQuestionResponse)
async def next_session_question(session_id: str) -> InterviewSessionQuestionResponse:
    try:
        return await interview_session_service.next_question(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except InterviewSessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except InterviewRepeatedQuestionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except InterviewQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, InterviewAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.get("/session/{session_id}", response_model=InterviewSessionSummaryResponse)
def get_session_summary(session_id: str) -> InterviewSessionSummaryResponse:
    try:
        return interview_session_service.get_summary(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None