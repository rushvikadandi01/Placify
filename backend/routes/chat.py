from fastapi import APIRouter, HTTPException

from ..schemas.chat import ChatRequest, ChatResponse
from ..services.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIProviderTimeoutError,
)
from ..services.placement_agent import placement_agent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await placement_agent.respond(request)
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="The AI provider timed out. Please try again.",
        ) from None
    except AIProviderError:
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not complete the request.",
        ) from None