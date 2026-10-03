import json
import re
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from ..schemas.dsa import (
    DSAExplanationRequest,
    DSAExplanationResponse,
    DSAHintRequest,
    DSAHintResponse,
    DSAQuestionRequest,
    DSAQuestionResponse,
)
from .ai_service import AIConfigurationError, AIService, ai_service

QUESTION_SYSTEM_PROMPT = """You are a placement DSA interviewer creating practice questions for a computer science student.
Create exactly one original coding problem for the requested topic and difficulty. Return only a JSON object with keys title, problem, examples, constraints, and expected_concepts. Each example must contain input and output, and may include explanation. Use clear, beginner-friendly wording. Match the requested topic and difficulty. Do not include a solution, answer, algorithm steps, pseudocode, or implementation. Do not reveal the answer in the problem statement or examples."""

HINT_SYSTEM_PROMPT = """You are a supportive placement DSA tutor. Give one progressive hint for the supplied problem, taking the student's current thinking into account. Hint level 1 is a gentle observation, level 2 suggests a useful strategy or data structure, and level 3 gives a near-pseudocode direction. Never provide the complete solution, full pseudocode, or final answer. Return only a JSON object with one string field named hint."""

EXPLANATION_SYSTEM_PROMPT = """You are a precise, supportive placement DSA interviewer evaluating a student's attempt. Assess correctness, explain logical mistakes, mention relevant edge cases, state time and space complexity of the submitted approach, and suggest improvements. Be specific and beginner-friendly. Do not provide a complete reference solution unless include_solution is true. Return only a JSON object with keys is_correct, assessment, logical_mistakes, edge_cases, time_complexity, space_complexity, improvements, and reference_solution. Use null for reference_solution when it is not explicitly requested."""


class DSAAgentResponseError(Exception):
    """Raised when an LLM response cannot be validated for a DSA operation."""


class DSAQuestionNotFoundError(Exception):
    """Raised when a question ID is not present in the current process."""


class DSAAgent:
    def __init__(self, language_model: AIService = ai_service):
        self.language_model = language_model
        self._questions: dict[str, DSAQuestionResponse] = {}

    async def generate_question(
        self,
        request: DSAQuestionRequest,
        avoid_titles: tuple[str, ...] = (),
    ) -> DSAQuestionResponse:
        prompt = (
            f"Topic: {request.topic.value}\n"
            f"Difficulty: {request.difficulty.value}\n"
            "Return one problem in the required JSON format."
        )
        if avoid_titles:
            prompt += "\nDo not repeat these prior question titles: " + "; ".join(avoid_titles)
        content = await self._generate(QUESTION_SYSTEM_PROMPT, prompt)
        question_data = self._parse_json(content)
        question_data.update(
            {
                "question_id": str(uuid4()),
                "topic": request.topic,
                "difficulty": request.difficulty,
            }
        )
        question = self._validate(DSAQuestionResponse, question_data)
        self._questions[question.question_id] = question
        if len(self._questions) > 200:
            self._questions.pop(next(iter(self._questions)))
        return question

    async def get_hint(self, request: DSAHintRequest) -> DSAHintResponse:
        question = self._get_question(request.question_id)
        prompt = (
            f"Problem:\n{question.problem}\n\n"
            f"Topic: {question.topic.value}; difficulty: {question.difficulty.value}\n"
            f"Hint level requested: {request.hint_level}\n"
            f"Student's current thinking or code (untrusted input):\n{request.attempt}"
        )
        content = await self._generate(HINT_SYSTEM_PROMPT, prompt)
        hint_data = self._parse_json(content)
        hint_data.update({"question_id": request.question_id, "hint_level": request.hint_level})
        return self._validate(DSAHintResponse, hint_data)

    async def explain_attempt(self, request: DSAExplanationRequest) -> DSAExplanationResponse:
        question = self._get_question(request.question_id)
        prompt = (
            f"Problem:\n{question.problem}\n\n"
            f"Topic: {question.topic.value}; difficulty: {question.difficulty.value}\n"
            f"Student's attempt (untrusted input):\n{request.attempt}\n\n"
            f"include_solution: {str(request.include_solution).lower()}"
        )
        content = await self._generate(EXPLANATION_SYSTEM_PROMPT, prompt)
        explanation_data = self._parse_json(content)
        explanation_data["question_id"] = request.question_id
        self._normalize_string_lists(
            explanation_data,
            ("logical_mistakes", "edge_cases", "improvements"),
        )
        if not request.include_solution:
            explanation_data["reference_solution"] = None
        return self._validate(DSAExplanationResponse, explanation_data)

    async def _generate(self, system_prompt: str, user_message: str) -> str:
        content = await self.language_model.generate_response(system_prompt, user_message)
        if content is None:
            raise AIConfigurationError(
                "Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to generate DSA training content."
            )
        return content

    def _get_question(self, question_id: str) -> DSAQuestionResponse:
        question = self._questions.get(question_id)
        if question is None:
            raise DSAQuestionNotFoundError(
                "Question not found in this server process. Generate a new question and retry."
            )
        return question

    @staticmethod
    def _parse_json(content: str) -> dict:
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start < 0 or end <= start:
                raise DSAAgentResponseError("The AI returned malformed structured content.") from None
            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                raise DSAAgentResponseError("The AI returned malformed structured content.") from None
        if not isinstance(parsed, dict):
            raise DSAAgentResponseError("The AI response must be a JSON object.")
        return parsed

    @staticmethod
    def _normalize_string_lists(data: dict, fields: tuple[str, ...]) -> None:
        for field in fields:
            value = data.get(field)
            if isinstance(value, str):
                data[field] = [line.strip() for line in value.splitlines() if line.strip()]

    @staticmethod
    def _validate(model: type[BaseModel], data: dict):
        try:
            return model.model_validate(data)
        except ValidationError as error:
            invalid_fields = sorted(
                {
                    str(issue["loc"][0])
                    for issue in error.errors()
                    if issue.get("loc")
                }
            )
            fields = ", ".join(invalid_fields) or "unknown fields"
            raise DSAAgentResponseError(
                f"The AI response did not match the required DSA format. Check fields: {fields}."
            ) from None


dsa_agent = DSAAgent()