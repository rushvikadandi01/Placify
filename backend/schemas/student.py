from pydantic import BaseModel


class StudentProfile(BaseModel):
    name: str
    target_role: str
    programming_language: str
    experience_level: str
    hours_per_day: float


class StudentCreated(BaseModel):
    message: str
    student_id: int