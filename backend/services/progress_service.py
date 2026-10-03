from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import ProgressRecord, Student
from ..schemas.progress import (
    ProgressRecordResponse,
    ProgressSummaryResponse,
    TopicProgressResponse,
    TrainingType,
)


class ProgressStudentNotFoundError(Exception):
    """Raised when progress is requested for an unknown student."""


class ProgressService:
    def validate_student(self, db: Session, student_id: int | None) -> None:
        if student_id is not None and db.get(Student, student_id) is None:
            raise ProgressStudentNotFoundError("Student not found.")

    def record_progress(
        self,
        db: Session,
        *,
        session_id: str,
        student_id: int | None,
        training_type: TrainingType,
        category: str | None,
        topic: str,
        difficulty: str | None,
        questions_attempted: int | None,
        questions_correct: int | None,
        accuracy: float | None,
        average_score: float | None,
        status: str = "completed",
    ) -> ProgressRecord:
        self.validate_student(db, student_id)
        existing = db.scalar(select(ProgressRecord).where(ProgressRecord.session_id == session_id))
        if existing is not None:
            return existing

        record = ProgressRecord(
            session_id=session_id,
            student_id=student_id,
            training_type=training_type.value,
            category=category,
            topic=topic,
            difficulty=difficulty,
            questions_attempted=questions_attempted,
            questions_correct=questions_correct,
            accuracy=accuracy,
            average_score=average_score,
            status=status,
        )
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(ProgressRecord).where(ProgressRecord.session_id == session_id))
            if existing is not None:
                return existing
            raise
        db.refresh(record)
        return record

    def get_progress(self, db: Session, student_id: int) -> list[ProgressRecordResponse]:
        records = self._records_for_student(db, student_id)
        return [ProgressRecordResponse.model_validate(record) for record in records]

    def get_summary(self, db: Session, student_id: int) -> ProgressSummaryResponse:
        records = self._records_for_student(db, student_id)
        question_records = [record for record in records if record.questions_attempted is not None]
        total_questions = sum(record.questions_attempted or 0 for record in question_records)
        total_correct = sum(record.questions_correct or 0 for record in question_records)
        interview_scores = [
            record.average_score
            for record in records
            if record.training_type == TrainingType.INTERVIEW.value and record.average_score is not None
        ]
        return ProgressSummaryResponse(
            student_id=student_id,
            total_sessions=len(records),
            total_questions=total_questions,
            total_correct=total_correct,
            overall_accuracy=round(total_correct / total_questions * 100, 2) if total_questions else 0.0,
            average_interview_score=(
                round(sum(interview_scores) / len(interview_scores), 2) if interview_scores else None
            ),
            dsa_sessions=sum(record.training_type == TrainingType.DSA.value for record in records),
            aptitude_sessions=sum(record.training_type == TrainingType.APTITUDE.value for record in records),
            interview_sessions=sum(record.training_type == TrainingType.INTERVIEW.value for record in records),
        )

    def get_topic_progress(self, db: Session, student_id: int) -> list[TopicProgressResponse]:
        records = self._records_for_student(db, student_id)
        grouped: dict[tuple[str, str | None, str], list[ProgressRecord]] = defaultdict(list)
        for record in records:
            grouped[(record.training_type, record.category, record.topic)].append(record)

        result: list[TopicProgressResponse] = []
        for (training_type, category, topic), topic_records in sorted(grouped.items()):
            attempted = sum(record.questions_attempted or 0 for record in topic_records)
            if training_type == TrainingType.INTERVIEW.value:
                scores = [record.average_score for record in topic_records if record.average_score is not None]
                result.append(
                    TopicProgressResponse(
                        training_type=TrainingType(training_type),
                        category=category,
                        topic=topic,
                        attempted=attempted,
                        correct=None,
                        accuracy=None,
                        average_score=round(sum(scores) / len(scores), 2) if scores else None,
                    )
                )
                continue

            correct = sum(record.questions_correct or 0 for record in topic_records)
            result.append(
                TopicProgressResponse(
                    training_type=TrainingType(training_type),
                    category=category,
                    topic=topic,
                    attempted=attempted,
                    correct=correct,
                    accuracy=round(correct / attempted * 100, 2) if attempted else 0.0,
                    average_score=None,
                )
            )
        return result

    def _records_for_student(self, db: Session, student_id: int) -> list[ProgressRecord]:
        self.validate_student(db, student_id)
        statement = (
            select(ProgressRecord)
            .where(ProgressRecord.student_id == student_id)
            .order_by(ProgressRecord.created_at.desc(), ProgressRecord.id.desc())
        )
        return list(db.scalars(statement).all())


progress_service = ProgressService()