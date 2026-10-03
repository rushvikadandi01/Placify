from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class StudyPlanRequest(BaseModel):
    student_id: int = Field(gt=0)
    days: int = Field(ge=1, le=30)
    hours_per_day: float = Field(ge=0.5, le=12)
    focus_areas: list[str] = Field(default_factory=list, max_length=10)
    goal: str | None = Field(default=None, max_length=300)

    @field_validator("focus_areas")
    @classmethod
    def normalize_focus_areas(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Focus areas must not be empty.")
        return list(dict.fromkeys(cleaned))

    @field_validator("goal")
    @classmethod
    def normalize_goal(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class StudyPlanTask(BaseModel):
    area: str = Field(min_length=1, max_length=80)
    topic: str = Field(min_length=1, max_length=120)
    activity: str = Field(min_length=3, max_length=500)
    duration_minutes: int = Field(ge=1, le=720)
    reason: str = Field(min_length=3, max_length=500)


class DailyStudyPlan(BaseModel):
    day: int = Field(ge=1, le=30)
    total_minutes: int = Field(ge=1, le=720)
    tasks: list[StudyPlanTask] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def task_minutes_must_match_total(self) -> Self:
        task_total = sum(task.duration_minutes for task in self.tasks)
        if task_total != self.total_minutes:
            raise ValueError("total_minutes must equal the sum of task durations.")
        return self


class StudyPlanResponse(BaseModel):
    student_id: int
    duration_days: int = Field(ge=1, le=30)
    hours_per_day: float = Field(ge=0.5, le=12)
    overall_goal: str
    detected_strengths: list[str]
    detected_weaknesses: list[str]
    progress_note: str | None = None
    daily_plan: list[DailyStudyPlan] = Field(min_length=1, max_length=30)
    recommendations: list[str]

    @model_validator(mode="after")
    def days_must_be_sequential(self) -> Self:
        expected_days = list(range(1, self.duration_days + 1))
        actual_days = [day.day for day in self.daily_plan]
        if actual_days != expected_days:
            raise ValueError("daily_plan must contain one sequential entry for each requested day.")
        return self