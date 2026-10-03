import json
import re
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from ..schemas.aptitude import (
    AptitudeAttemptRequest,
    AptitudeCategory,
    AptitudeDifficulty,
    AptitudeEvaluationResponse,
    AptitudeExplanationResponse,
    AptitudeQuestionRequest,
    AptitudeQuestionResponse,
    AptitudeTopic,
)
from .ai_service import AIConfigurationError, AIService, ai_service

QUESTION_SYSTEM_PROMPT = """You are an experienced placement aptitude coach. Create exactly one multiple-choice question for the requested category, topic, and difficulty. Return only a JSON object with keys question, options, correct_answer, explanation, learning_feedback, improvement_tip, and answer_check. Provide exactly four distinct option strings with no A/B/C/D prefixes. There must be exactly one correct option, and correct_answer must exactly match that option. Independently solve and verify the answer before responding. For numerical questions, show the relevant calculation clearly in explanation and confirm the result matches only one option. For logical reasoning, ensure the premises determine the answer. For verbal questions, ensure one option is clearly correct. Keep the initial question free of clues that reveal the answer. Use beginner-friendly language."""


class AptitudeAgentResponseError(Exception):
    """Raised when generated aptitude content fails structural or answer validation."""


class AptitudeQuestionNotFoundError(Exception):
    """Raised when a generated aptitude question is not available in memory."""


class AptitudeInvalidAnswerError(Exception):
    """Raised when a submitted answer is not one of the question options."""


class _AptitudeQuestionRecord(AptitudeQuestionResponse):
    correct_answer: str
    explanation: str = Field(min_length=1)
    learning_feedback: str = Field(min_length=1)
    improvement_tip: str | None = None
    answer_check: str | None = None


class AptitudeAgent:
    def __init__(self, language_model: AIService = ai_service):
        self.language_model = language_model
        self._questions: dict[str, _AptitudeQuestionRecord] = {}

    async def generate_question(
        self,
        request: AptitudeQuestionRequest,
        avoid_questions: tuple[str, ...] = (),
    ) -> AptitudeQuestionResponse:
        prompt = (
            f"Category: {request.category.value}\n"
            f"Topic: {request.topic.value}\n"
            f"Difficulty: {request.difficulty.value}\n"
            "Return one checked question in the required JSON format."
        )
        if avoid_questions:
            prompt += "\nDo not repeat these previous problem statements:\n" + "\n---\n".join(avoid_questions)

        content = await self._generate(prompt)
        data = self._parse_json(content)
        data["question_id"] = str(uuid4())
        data["category"] = request.category
        data["topic"] = request.topic
        data["difficulty"] = request.difficulty
        data["options"] = self._normalize_options(data.get("options"))
        data["correct_answer"] = self._normalize_correct_answer(data.get("correct_answer"), data["options"])
        record = self._validate_record(data)
        self._questions[record.question_id] = record
        if len(self._questions) > 200:
            self._questions.pop(next(iter(self._questions)))
        return self._public_question(record)

    def evaluate_attempt(self, request: AptitudeAttemptRequest) -> AptitudeEvaluationResponse:
        record = self._get_question(request.question_id)
        selected_answer = self._resolve_answer(request.selected_answer, record.options)
        return AptitudeEvaluationResponse(
            question_id=record.question_id,
            is_correct=selected_answer.casefold() == record.correct_answer.casefold(),
            selected_answer=selected_answer,
            correct_answer=record.correct_answer,
            explanation=record.explanation,
            learning_feedback=record.learning_feedback,
            improvement_tip=record.improvement_tip,
        )

    def explain_question(self, question_id: str) -> AptitudeExplanationResponse:
        record = self._get_question(question_id)
        return AptitudeExplanationResponse(
            question_id=record.question_id,
            correct_answer=record.correct_answer,
            explanation=record.explanation,
            learning_feedback=record.learning_feedback,
            improvement_tip=record.improvement_tip,
        )

    async def _generate(self, user_message: str) -> str:
        system_prompt = "You create verified placement aptitude MCQs. Never reveal the answer in the question text."
        content = await self.language_model.generate_response(QUESTION_SYSTEM_PROMPT + "\n" + system_prompt, user_message)
        if content is None:
            raise AIConfigurationError(
                "Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to generate aptitude questions."
            )
        return content

    def _get_question(self, question_id: str) -> _AptitudeQuestionRecord:
        record = self._questions.get(question_id)
        if record is None:
            raise AptitudeQuestionNotFoundError(
                "Aptitude question not found in this server process. Generate a new question and retry."
            )
        return record

    @staticmethod
    def _parse_json(content: str) -> dict:
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start < 0 or end <= start:
                raise AptitudeAgentResponseError("The AI returned malformed aptitude content.") from None
            try:
                data = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                raise AptitudeAgentResponseError("The AI returned malformed aptitude content.") from None
        if not isinstance(data, dict):
            raise AptitudeAgentResponseError("The AI response must be a JSON object.")
        return data

    @staticmethod
    def _normalize_options(options: object) -> list[str]:
        if not isinstance(options, list) or len(options) != 4:
            raise AptitudeAgentResponseError("The AI response must contain exactly four options.")
        normalized: list[str] = []
        for option in options:
            if not isinstance(option, str) or not option.strip():
                raise AptitudeAgentResponseError("Each aptitude option must be non-empty text.")
            cleaned = re.sub(r"^\s*\(?[A-D]\)?[.)\]:-]\s*", "", option.strip(), flags=re.IGNORECASE)
            normalized.append(cleaned)
        if len({option.casefold() for option in normalized}) != 4:
            raise AptitudeAgentResponseError("The four aptitude options must be distinct.")
        return normalized

    @classmethod
    def _normalize_correct_answer(cls, answer: object, options: list[str]) -> str:
        if not isinstance(answer, str) or not answer.strip():
            raise AptitudeAgentResponseError("The AI response did not provide one correct answer.")
        cleaned_answer = answer.strip()
        label_match = re.fullmatch(r"(?:option\s*)?\(?([A-D])\)?[.)]??", cleaned_answer, flags=re.IGNORECASE)
        if label_match:
            return options[ord(label_match.group(1).upper()) - ord("A")]
        cleaned_answer = re.sub(r"^\s*\(?[A-D]\)?[.)\]:-]\s*", "", cleaned_answer, flags=re.IGNORECASE)
        matches = [option for option in options if option.casefold() == cleaned_answer.casefold()]
        if len(matches) != 1:
            raise AptitudeAgentResponseError("The correct answer must match exactly one provided option.")
        return matches[0]

    @staticmethod
    def _resolve_answer(answer: str, options: list[str]) -> str:
        cleaned_answer = answer.strip()
        label_match = re.fullmatch(r"(?:option\s*)?\(?([A-D])\)?[.)]??", cleaned_answer, flags=re.IGNORECASE)
        if label_match:
            return options[ord(label_match.group(1).upper()) - ord("A")]
        cleaned_answer = re.sub(r"^\s*\(?[A-D]\)?[.)\]:-]\s*", "", cleaned_answer, flags=re.IGNORECASE)
        for option in options:
            if option.casefold() == cleaned_answer.casefold():
                return option
        raise AptitudeInvalidAnswerError("Selected answer must match one of the four provided options.")

    @staticmethod
    def _validate_record(data: dict) -> _AptitudeQuestionRecord:
        try:
            return _AptitudeQuestionRecord.model_validate(data)
        except ValidationError as error:
            invalid_fields = sorted(
                {str(issue["loc"][0]) for issue in error.errors() if issue.get("loc")}
            )
            fields = ", ".join(invalid_fields) or "unknown fields"
            raise AptitudeAgentResponseError(
                f"The AI response did not match the aptitude question format. Check fields: {fields}."
            ) from None

    @staticmethod
    def _public_question(record: _AptitudeQuestionRecord) -> AptitudeQuestionResponse:
        return AptitudeQuestionResponse(
            question_id=record.question_id,
            question=record.question,
            options=record.options,
            category=record.category,
            topic=record.topic,
            difficulty=record.difficulty,
        )


aptitude_agent = AptitudeAgent()