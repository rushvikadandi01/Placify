from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from ..database import Base


class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, unique=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    training_type = Column(String(20), nullable=False, index=True)
    category = Column(String(40), nullable=True)
    topic = Column(String(80), nullable=False, index=True)
    difficulty = Column(String(20), nullable=True)
    questions_attempted = Column(Integer, nullable=True)
    questions_correct = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)
    average_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))