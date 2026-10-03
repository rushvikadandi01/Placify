from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.study_plan import StudyPlanRequest, StudyPlanResponse
from ..services.ai_service import AIConfigurationError, AIProviderError, AIProviderTimeoutError
from ..services.progress_service import ProgressStudentNotFoundError
from ..services.study_plan_service import StudyPlanResponseError, study_plan_service

router = APIRouter(prefix="/study-plan")


@router.post("", response_model=StudyPlanResponse)
async def generate_study_plan(
    request: StudyPlanRequest,
    db: Session = Depends(get_db),
) -> StudyPlanResponse:
    try:
        return await study_plan_service.generate_plan(db, request)
    except ProgressStudentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except AIProviderTimeoutError:
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from None
    except StudyPlanResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except AIProviderError:
        raise HTTPException(status_code=502, detail="The AI provider could not generate the study plan.") from None