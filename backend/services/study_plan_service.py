import json
import re
from collections import defaultdict

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..schemas.progress import ProgressRecordResponse, TrainingType
from ..schemas.study_plan import StudyPlanRequest, StudyPlanResponse
from .ai_service import AIConfigurationError, AIService, ai_service
from .progress_service import ProgressService, ProgressStudentNotFoundError, progress_service

STUDY_PLAN_SYSTEM_PROMPT = """You are a practical placement-preparation study planner. Create a realistic daily plan using only the supplied progress data and user request. Never invent historical scores, sessions, strengths, or weaknesses. Mark unmeasured areas as unmeasured and balance DSA, aptitude, technical interview, and HR/project preparation over the requested duration without forcing every area into every day. Spend more time on evidenced weak areas and prioritize requested focus areas. Respect the exact daily time budget: the sum of task duration_minutes must equal total_minutes, and total_minutes must not exceed max_minutes_per_day. Use whole-number minutes. Include useful activity and a short reason for each task. Return only JSON with keys daily_plan and recommendations. Each daily_plan item must contain day, total_minutes, and tasks; each task must contain area, topic, activity, duration_minutes, and reason."""


class StudyPlanResponseError(Exception):
    """Raised when an AI-generated plan is malformed or violates the request constraints."""


class StudyPlanService:
    def __init__(
        self,
        progress: ProgressService = progress_service,
        language_model: AIService = ai_service,
    ):
        self.progress = progress
        self.language_model = language_model

    async def generate_plan(self, db: Session, request: StudyPlanRequest) -> StudyPlanResponse:
        records = self.progress.get_progress(db, request.student_id)
        topic_performance = self._analyze_progress(records)
        detected_strengths, detected_weaknesses = self._classify_performance(topic_performance)
        total_questions = sum(record.questions_attempted or 0 for record in records)
        limited_data = len(records) < 5 or total_questions < 10
        progress_note = (
            "Limited progress data is available. The plan will become more personalized after additional practice."
            if limited_data
            else None
        )

        context = {
            "student_progress": {
                "topic_performance": topic_performance,
                "recent_sessions": [self._record_context(record) for record in records[:10]],
                "total_sessions": len(records),
                "total_questions": total_questions,
                "detected_strengths": detected_strengths,
                "detected_weaknesses": detected_weaknesses,
                "limited_progress_data": limited_data,
                "unmeasured_areas": self._unmeasured_areas(topic_performance),
            },
            "request": {
                "days": request.days,
                "hours_per_day": request.hours_per_day,
                "max_minutes_per_day": int(request.hours_per_day * 60),
                "goal": request.goal or "placement preparation",
                "focus_areas": request.focus_areas,
            },
        }
        content = await self.language_model.generate_response(
            STUDY_PLAN_SYSTEM_PROMPT,
            json.dumps(context, ensure_ascii=True, default=str),
        )
        if content is None:
            raise AIConfigurationError("Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to generate a study plan.")

        generated = self._parse_json(content)
        response_data = {
            "student_id": request.student_id,
            "duration_days": request.days,
            "hours_per_day": request.hours_per_day,
            "overall_goal": request.goal or "placement preparation",
            "detected_strengths": detected_strengths,
            "detected_weaknesses": detected_weaknesses,
            "progress_note": progress_note,
            "daily_plan": generated.get("daily_plan"),
            "recommendations": generated.get("recommendations"),
        }
        plan = self._validate_plan(response_data)
        self._validate_time_budget(plan, int(request.hours_per_day * 60))
        self._validate_focus_areas(plan, request.focus_areas)
        return plan

    @staticmethod
    def _analyze_progress(records: list[ProgressRecordResponse]) -> list[dict]:
        grouped: dict[tuple[str, str | None, str], list[ProgressRecordResponse]] = defaultdict(list)
        for record in records:
            grouped[(record.training_type.value, record.category, record.topic)].append(record)

        results: list[dict] = []
        for (training_type, category, topic), topic_records in sorted(grouped.items()):
            attempted = sum(record.questions_attempted or 0 for record in topic_records)
            item = {
                "training_type": training_type,
                "category": category,
                "topic": topic,
                "sessions": len(topic_records),
                "questions_attempted": attempted,
            }
            if training_type == TrainingType.INTERVIEW.value:
                scored_records = [record for record in topic_records if record.average_score is not None]
                scored_questions = sum(record.questions_attempted or 0 for record in scored_records)
                item["average_score"] = (
                    round(
                        sum((record.average_score or 0) * (record.questions_attempted or 0) for record in scored_records)
                        / scored_questions,
                        2,
                    )
                    if scored_questions
                    else None
                )
            else:
                correct = sum(record.questions_correct or 0 for record in topic_records)
                item["questions_correct"] = correct
                item["accuracy"] = round(correct / attempted * 100, 2) if attempted else None
            results.append(item)
        return results

    @staticmethod
    def _classify_performance(topic_performance: list[dict]) -> tuple[list[str], list[str]]:
        strengths: list[str] = []
        weaknesses: list[str] = []
        for item in topic_performance:
            if item["training_type"] == TrainingType.INTERVIEW.value:
                score = item.get("average_score")
                if score is None or item["questions_attempted"] < 3:
                    continue
                label = f"{item['topic']} (Interview): {score}/10 average"
                if score >= 8:
                    strengths.append(label)
                elif score < 6:
                    weaknesses.append(label)
                continue

            accuracy = item.get("accuracy")
            if accuracy is None or item["questions_attempted"] < 5:
                continue
            label = f"{item['topic']} ({item['training_type']}): {accuracy}% accuracy"
            if accuracy >= 80:
                strengths.append(label)
            elif accuracy < 60:
                weaknesses.append(label)
        return strengths, weaknesses

    @staticmethod
    def _unmeasured_areas(topic_performance: list[dict]) -> list[str]:
        measured_types = {item["training_type"] for item in topic_performance}
        areas = {
            TrainingType.DSA.value: "DSA",
            TrainingType.APTITUDE.value: "Aptitude",
            TrainingType.INTERVIEW.value: "Interview preparation",
        }
        return [label for key, label in areas.items() if key not in measured_types]

    @staticmethod
    def _record_context(record: ProgressRecordResponse) -> dict:
        return {
            "training_type": record.training_type.value,
            "category": record.category,
            "topic": record.topic,
            "difficulty": record.difficulty,
            "questions_attempted": record.questions_attempted,
            "questions_correct": record.questions_correct,
            "accuracy": record.accuracy,
            "average_score": record.average_score,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
        }

    @staticmethod
    def _parse_json(content: str) -> dict:
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start < 0 or end <= start:
                raise StudyPlanResponseError("The AI returned malformed study-plan content.") from None
            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                raise StudyPlanResponseError("The AI returned malformed study-plan content.") from None
        if not isinstance(parsed, dict):
            raise StudyPlanResponseError("The AI study plan must be a JSON object.")
        return parsed

    @staticmethod
    def _validate_plan(data: dict) -> StudyPlanResponse:
        try:
            return StudyPlanResponse.model_validate(data)
        except ValidationError as error:
            fields = sorted({str(issue["loc"][0]) for issue in error.errors() if issue.get("loc")})
            invalid_fields = ", ".join(fields) or "unknown fields"
            raise StudyPlanResponseError(
                f"The AI study plan did not match the required format. Check fields: {invalid_fields}."
            ) from None

    @staticmethod
    def _validate_time_budget(plan: StudyPlanResponse, max_minutes: int) -> None:
        for daily_plan in plan.daily_plan:
            if daily_plan.total_minutes > max_minutes:
                raise StudyPlanResponseError(
                    f"Day {daily_plan.day} exceeds the requested {max_minutes}-minute daily time limit."
                )

    @staticmethod
    def _validate_focus_areas(plan: StudyPlanResponse, focus_areas: list[str]) -> None:
        if not focus_areas:
            return
        plan_text = " ".join(
            f"{task.area} {task.topic} {task.activity} {task.reason}"
            for day in plan.daily_plan
            for task in day.tasks
        ).casefold()
        missing = [area for area in focus_areas if area.casefold() not in plan_text]
        if missing:
            raise StudyPlanResponseError(
                "The AI study plan did not include the requested focus areas: " + ", ".join(missing) + "."
            )


study_plan_service = StudyPlanService()