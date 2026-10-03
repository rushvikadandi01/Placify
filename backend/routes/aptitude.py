from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.aptitude import (
    AptitudeAttemptRequest,
    AptitudeEvaluationResponse,
    AptitudeExplainRequest,
    AptitudeExplanationResponse,
    AptitudeQuestionRequest,
    AptitudeQuestionResponse,
    AptitudeSessionAttemptRequest,
    AptitudeSessionAttemptResponse,
    AptitudeSessionQuestionResponse,
    AptitudeSessionStartRequest,
    AptitudeSessionSummaryResponse,
)
from ..services.ai_service import AIConfigurationError, AIProviderError, AIProviderTimeoutError
from ..services.aptitude_agent import (
    AptitudeAgentResponseError,
    AptitudeInvalidAnswerError,
    AptitudeQuestionNotFoundError,
    aptitude_agent,
)
from ..services.aptitude_session_service import (
    AptitudeRepeatedQuestionError,
    AptitudeSessionConflictError,
    AptitudeSessionNotFoundError,
    aptitude_session_service,
)
from ..services.progress_service import ProgressStudentNotFoundError

router = APIRouter(prefix="/aptitude")


def _ai_http_error(error: Exception) -> HTTPException:
    if isinstance(error, AIConfigurationError):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, AIProviderTimeoutError):
        return HTTPException(status_code=504, detail="The AI provider timed out. Please try again.")
    if isinstance(error, AptitudeAgentResponseError):
        return HTTPException(status_code=502, detail=str(error))
    return HTTPException(status_code=502, detail="The AI provider could not complete the aptitude request.")


@router.post("/question", response_model=AptitudeQuestionResponse)
async def generate_question(request: AptitudeQuestionRequest) -> AptitudeQuestionResponse:
    try:
        return await aptitude_agent.generate_question(request)
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, AptitudeAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/attempt", response_model=AptitudeEvaluationResponse)
def submit_attempt(request: AptitudeAttemptRequest) -> AptitudeEvaluationResponse:
    try:
        return aptitude_agent.evaluate_attempt(request)
    except AptitudeQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AptitudeInvalidAnswerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post("/explain", response_model=AptitudeExplanationResponse)
def explain_question(request: AptitudeExplainRequest) -> AptitudeExplanationResponse:
    try:
        return aptitude_agent.explain_question(request.question_id)
    except AptitudeQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None


@router.post("/session/start", response_model=AptitudeSessionQuestionResponse)
async def start_session(
    request: AptitudeSessionStartRequest,
    db: Session = Depends(get_db),
) -> AptitudeSessionQuestionResponse:
    try:
        return await aptitude_session_service.start(request, db)
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, AptitudeAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.post("/session/{session_id}/attempt", response_model=AptitudeSessionAttemptResponse)
async def submit_session_attempt(
    session_id: str,
    request: AptitudeSessionAttemptRequest,
    db: Session = Depends(get_db),
) -> AptitudeSessionAttemptResponse:
    try:
        return await aptitude_session_service.submit_attempt(session_id, request, db)
    except AptitudeSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AptitudeSessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except AptitudeQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AptitudeInvalidAnswerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None


@router.post("/session/{session_id}/next", response_model=AptitudeSessionQuestionResponse)
async def next_session_question(session_id: str) -> AptitudeSessionQuestionResponse:
    try:
        return await aptitude_session_service.next_question(session_id)
    except AptitudeSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AptitudeSessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except AptitudeRepeatedQuestionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except (AIConfigurationError, AIProviderTimeoutError, AIProviderError, AptitudeAgentResponseError) as error:
        raise _ai_http_error(error) from None


@router.get("/session/{session_id}", response_model=AptitudeSessionSummaryResponse)
def get_session_summary(session_id: str) -> AptitudeSessionSummaryResponse:
    try:
        return aptitude_session_service.get_summary(session_id)
    except AptitudeSessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None