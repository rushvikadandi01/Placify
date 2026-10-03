import json
import re
from dataclasses import dataclass
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from ..schemas.interview import (
    InterviewAttemptRequest,
    InterviewDifficulty,
    InterviewEvaluationResponse,
    InterviewFollowUpRequest,
    InterviewMode,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    InterviewQuestionType,
    InterviewTopic,
)
from .ai_service import AIConfigurationError, AIService, ai_service

QUESTION_SYSTEM_PROMPT = """You are a realistic, supportive placement interviewer. Ask exactly one conversational, open-ended interview question. This is a spoken-answer practice, not a multiple-choice quiz. Do not include an answer, hints, or a list of choices. Match the requested mode and topic. For project questions, use the supplied project context without inventing details. Return only a JSON object with a single string field named question."""

FOLLOW_UP_SYSTEM_PROMPT = """You are a realistic placement interviewer continuing a conversation. Ask exactly one concise, conversational follow-up that responds specifically to the student's previous answer and stays on the same interview topic. Probe a useful detail or ask for an example when appropriate. If the answer does not address the previous question, politely redirect with a clarifying follow-up about that original question instead of switching to a topic mentioned incidentally. Do not repeat the previous question or provide an answer. Return only a JSON object with a single string field named question."""

EVALUATION_SYSTEM_PROMPT = """Evaluate the student's interview answer fairly and constructively on observable content only. Use a score from 0 to 10. Return only a JSON object with keys score, strengths, weaknesses, feedback, missing_points, suggested_answer, communication_feedback, and technical_feedback. strengths, weaknesses, and missing_points must be arrays of concise strings. Give a realistic stronger answer as suggested_answer. Do not infer or claim to measure personality, sensitive personal characteristics, or actual human confidence. For HR, assess relevance, clarity, structure, professionalism, and specificity from the text only. For technical interviews, assess correctness, completeness, understanding, and clarity. For project interviews, assess the detail and reasoning shown about architecture, technology choices, implementation, testing, deployment, or challenges; do not assume ownership beyond the answer. Use a neutral sentence for technical_feedback when technical evaluation is not relevant, and for communication_feedback when communication evaluation is not central."""

MODE_EVALUATION_GUIDANCE = {
    InterviewMode.TECHNICAL: "Assess technical correctness, completeness, demonstrated understanding, and clarity.",
    InterviewMode.HR: "Assess relevance, clarity, structure, professionalism, and specific examples. Only comment on observable answer content; do not infer personal traits or actual confidence.",
    InterviewMode.PROJECT: "Assess demonstrated understanding of the student's project, architecture, technology choices, implementation, testing, deployment, and challenges. Do not invent project facts.",
}


class InterviewAgentResponseError(Exception):
    """Raised when LLM interview content fails response validation."""


class InterviewQuestionNotFoundError(Exception):
    """Raised when the question ID is not available in the current process."""


@dataclass
class _InterviewQuestionRecord:
    response: InterviewQuestionResponse
    difficulty: InterviewDifficulty
    project_name: str | None
    project_description: str | None


class InterviewAgent:
    def __init__(self, language_model: AIService = ai_service):
        self.language_model = language_model
        self._questions: dict[str, _InterviewQuestionRecord] = {}

    async def generate_question(
        self,
        request: InterviewQuestionRequest,
        avoid_questions: tuple[str, ...] = (),
    ) -> InterviewQuestionResponse:
        return await self._generate_question(
            mode=request.mode,
            topic=request.topic,
            difficulty=request.difficulty,
            project_name=request.project_name,
            project_description=request.project_description,
            question_type=InterviewQuestionType.OPEN_ENDED,
            system_prompt=QUESTION_SYSTEM_PROMPT,
            extra_context="",
            avoid_questions=avoid_questions,
        )

    async def generate_follow_up(self, request: InterviewFollowUpRequest, avoid_questions: tuple[str, ...] = ()) -> InterviewQuestionResponse:
        previous = self._get_question(request.question_id)
        response = previous.response
        extra_context = (
            f"Previous question: {response.question}\n"
            f"Student's answer (untrusted input): {request.answer}"
        )
        return await self._generate_question(
            mode=response.mode,
            topic=response.topic,
            difficulty=previous.difficulty,
            project_name=previous.project_name,
            project_description=previous.project_description,
            question_type=InterviewQuestionType.FOLLOW_UP,
            system_prompt=FOLLOW_UP_SYSTEM_PROMPT,
            extra_context=extra_context,
            avoid_questions=avoid_questions,
        )

    async def evaluate_answer(self, request: InterviewAttemptRequest) -> InterviewEvaluationResponse:
        record = self._get_question(request.question_id)
        question = record.response
        prompt = (
            f"Mode: {question.mode.value}\n"
            f"Topic: {question.topic.value}\n"
            f"Evaluation guidance: {MODE_EVALUATION_GUIDANCE[question.mode]}\n"
            f"Question: {question.question}\n"
            f"Student's answer (untrusted input): {request.answer}\n"
            f"Project name: {record.project_name or 'Not provided'}\n"
            f"Project description: {record.project_description or 'Not provided'}"
        )
        content = await self._generate(EVALUATION_SYSTEM_PROMPT, prompt)
        data = self._parse_json(content)
        data["question_id"] = request.question_id
        self._normalize_evaluation(data)
        return self._validate(InterviewEvaluationResponse, data)

    async def _generate_question(
        self,
        mode: InterviewMode,
        topic: InterviewTopic,
        difficulty: InterviewDifficulty,
        project_name: str | None,
        project_description: str | None,
        question_type: InterviewQuestionType,
        system_prompt: str,
        extra_context: str,
        avoid_questions: tuple[str, ...],
    ) -> InterviewQuestionResponse:
        prompt_parts = [
            f"Mode: {mode.value}",
            f"Topic: {topic.value}",
            f"Difficulty: {difficulty.value}",
            f"Project name: {project_name or 'Not provided'}",
            f"Project description: {project_description or 'Not provided'}",
        ]
        if extra_context:
            prompt_parts.append(extra_context)
        if avoid_questions:
            prompt_parts.append("Do not repeat any of these earlier questions:\n" + "\n---\n".join(avoid_questions))
        prompt_parts.append("Return one question in the required JSON format.")
        content = await self._generate(system_prompt, "\n".join(prompt_parts))
        data = self._parse_json(content)
        data["question_id"] = str(uuid4())
        data["mode"] = mode
        data["topic"] = topic
        data["question_type"] = question_type
        response = self._validate(InterviewQuestionResponse, data)
        self._questions[response.question_id] = _InterviewQuestionRecord(
            response=response,
            difficulty=difficulty,
            project_name=project_name,
            project_description=project_description,
        )
        if len(self._questions) > 200:
            self._questions.pop(next(iter(self._questions)))
        return response

    async def _generate(self, system_prompt: str, user_message: str) -> str:
        content = await self.language_model.generate_response(system_prompt, user_message)
        if content is None:
            raise AIConfigurationError(
                "Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable interview training."
            )
        return content

    def _get_question(self, question_id: str) -> _InterviewQuestionRecord:
        record = self._questions.get(question_id)
        if record is None:
            raise InterviewQuestionNotFoundError(
                "Interview question not found in this server process. Generate a new question and retry."
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
                raise InterviewAgentResponseError("The AI returned malformed interview content.") from None
            try:
                data = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                raise InterviewAgentResponseError("The AI returned malformed interview content.") from None
        if not isinstance(data, dict):
            raise InterviewAgentResponseError("The AI response must be a JSON object.")
        return data

    @staticmethod
    def _normalize_evaluation(data: dict) -> None:
        for field in ("strengths", "weaknesses", "missing_points"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = [line.strip() for line in value.splitlines() if line.strip()]
        score = data.get("score")
        if isinstance(score, str):
            match = re.search(r"\d+(?:\.\d+)?", score)
            if match:
                data["score"] = float(match.group())

    @staticmethod
    def _validate(model: type[BaseModel], data: dict):
        try:
            return model.model_validate(data)
        except ValidationError as error:
            invalid_fields = sorted(
                {str(issue["loc"][0]) for issue in error.errors() if issue.get("loc")}
            )
            fields = ", ".join(invalid_fields) or "unknown fields"
            raise InterviewAgentResponseError(
                f"The AI response did not match the interview format. Check fields: {fields}."
            ) from None


interview_agent = InterviewAgent()