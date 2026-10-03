from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.dsa import (
    DSAExplanationRequest,
    DSAExplanationResponse,
    DSAHintRequest,
    DSAHintResponse,
    DSAQuestionRequest,
    DSAQuestionResponse,
    DSASessionAttemptRequest,
    DSASessionAttemptResponse,
    DSASessionQuestionResponse,
    DSASessionStartRequest,
    DSASessionSummaryResponse,
)
from ..services.ai_service import AIConfigurationError, AIProviderError, AIProviderTimeoutError
from ..services.dsa_agent import (
    DSAAgentResponseError,
    DSAQuestionNotFoundError,
    dsa_agent,
)
from ..services.dsa_session_service import (
    DSASessionConflictError,
    DSASessionNotFoundError,
    DSASessionQuestionRepeatError,
    dsa_session_service,
)
from ..services.progress_service import ProgressStudentNotFoundError

router = APIRouter(prefix="/dsa")


@router.post("/question", response_model=DSAQuestionResponse)
async def generate_question(request: DSAQuestionRequest) -> DSAQuestionResponse:
    try:
        return await dsa_agent.generate_question(request)
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except DSAAgentResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except AIProviderError:
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not generate a valid DSA question.",
        ) from None


@router.post("/hint", response_model=DSAHintResponse)
async def get_hint(request: DSAHintRequest) -> DSAHintResponse:
    try:
        return await dsa_session_service.get_hint(request)
    except DSAQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except DSASessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except DSASessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except DSAAgentResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except AIProviderError:
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not generate a valid hint.",
        ) from None


@router.post("/explain", response_model=DSAExplanationResponse)
async def explain_attempt(request: DSAExplanationRequest) -> DSAExplanationResponse:
    try:
        return await dsa_agent.explain_attempt(request)
    except DSAQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except DSAAgentResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except AIProviderError:
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not evaluate this attempt.",
        ) from None


@router.post("/session/start", response_model=DSASessionQuestionResponse)
async def start_session(
    request: DSASessionStartRequest,
    db: Session = Depends(get_db),
) -> DSASessionQuestionResponse:
    try:
        return await dsa_session_service.start(request, db)
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except (AIProviderError, DSAAgentResponseError):
        raise HTTPException(status_code=502, detail="The AI provider could not generate a valid DSA question.") from None


@router.post("/session/{session_id}/attempt", response_model=DSASessionAttemptResponse)
async def submit_session_attempt(
    session_id: str,
    request: DSASessionAttemptRequest,
    db: Session = Depends(get_db),
) -> DSASessionAttemptResponse:
    try:
        return await dsa_session_service.submit_attempt(session_id, request, db)
    except DSASessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except DSASessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except DSAQuestionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except (AIProviderError, DSAAgentResponseError):
        raise HTTPException(status_code=502, detail="The AI provider could not evaluate this attempt.") from None


@router.post("/session/{session_id}/next", response_model=DSASessionQuestionResponse)
async def next_session_question(session_id: str) -> DSASessionQuestionResponse:
    try:
        return await dsa_session_service.next_question(session_id)
    except DSASessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except DSASessionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except DSASessionQuestionRepeatError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except (AIProviderError, DSAAgentResponseError):
        raise HTTPException(status_code=502, detail="The AI provider could not generate a valid DSA question.") from None


@router.get("/session/{session_id}", response_model=DSASessionSummaryResponse)
def get_session_summary(session_id: str) -> DSASessionSummaryResponse:
    try:
        return dsa_session_service.get_summary(session_id)
    except DSASessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None