from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student
from ..schemas.student import StudentCreated, StudentProfile

router = APIRouter()


@router.post("/student", response_model=StudentCreated)
def create_student(student: StudentProfile, db: Session = Depends(get_db)):
    new_student = Student(
        name=student.name,
        target_role=student.target_role,
        programming_language=student.programming_language,
        experience_level=student.experience_level,
        hours_per_day=student.hours_per_day,
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {
        "message": "Student profile created successfully!",
        "student_id": new_student.id,
    }