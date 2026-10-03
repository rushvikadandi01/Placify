from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.progress import ProgressRecordResponse, ProgressSummaryResponse, TopicProgressResponse
from ..services.progress_service import ProgressStudentNotFoundError, progress_service

router = APIRouter(prefix="/progress")


def _student_not_found(error: ProgressStudentNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.get("/{student_id}", response_model=list[ProgressRecordResponse])
def get_progress(student_id: int, db: Session = Depends(get_db)) -> list[ProgressRecordResponse]:
    try:
        return progress_service.get_progress(db, student_id)
    except ProgressStudentNotFoundError as error:
        raise _student_not_found(error) from None


@router.get("/{student_id}/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(student_id: int, db: Session = Depends(get_db)) -> ProgressSummaryResponse:
    try:
        return progress_service.get_summary(db, student_id)
    except ProgressStudentNotFoundError as error:
        raise _student_not_found(error) from None


@router.get("/{student_id}/topics", response_model=list[TopicProgressResponse])
def get_topic_progress(student_id: int, db: Session = Depends(get_db)) -> list[TopicProgressResponse]:
    try:
        return progress_service.get_topic_progress(db, student_id)
    except ProgressStudentNotFoundError as error:
        raise _student_not_found(error) from None