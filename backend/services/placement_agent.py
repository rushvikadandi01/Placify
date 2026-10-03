from ..schemas.chat import ChatIntent, ChatRequest, ChatResponse
from .ai_service import AIService, ai_service
from .intent_router import classify_intent

SYSTEM_PROMPT = """You are a practical, supportive placement preparation mentor for a CSE/AIML student.
Explain concepts clearly in beginner-friendly language and keep answers concise. Adapt to the student's stated experience level; if it is unknown and matters, ask. For DSA problems, offer a hint before a full solution unless the student asks directly for the solution. Distinguish technical subjects, aptitude, interviews, HR, projects, and study planning. In interview practice, ask one question at a time and wait for the student's answer. Never claim or imply that placement is guaranteed. Do not invent facts about the student's background or project."""

OFFLINE_RESPONSES = {
    ChatIntent.DSA: "I classified this as DSA. An AI provider is not configured, so I cannot generate a tailored explanation yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.APTITUDE: "I classified this as aptitude. An AI provider is not configured, so I cannot generate a tailored practice question yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.INTERVIEW: "I classified this as interview practice. An AI provider is not configured, so I cannot conduct a tailored mock interview yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.CORE_CS: "I classified this as a core CS question. An AI provider is not configured, so I cannot generate a tailored explanation yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.HR: "I classified this as an HR interview request. An AI provider is not configured, so I cannot generate a tailored question yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.PROJECT_INTERVIEW: "I classified this as a project interview request. An AI provider is not configured, so I cannot generate tailored project questions yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.STUDY_PLAN: "I classified this as a study-plan request. An AI provider is not configured, so I cannot generate a tailored plan yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
    ChatIntent.GENERAL: "I classified this as a general placement-preparation request. An AI provider is not configured, so I cannot generate a tailored answer yet. Configure AI_PROVIDER, AI_API_KEY, and AI_MODEL to enable assistant responses.",
}


class PlacementAgent:
    def __init__(self, language_model: AIService = ai_service):
        self.language_model = language_model

    async def respond(self, request: ChatRequest) -> ChatResponse:
        intent = classify_intent(request.message)
        prompt_message = f"Detected intent: {intent.value}\nStudent request: {request.message}"
        response = await self.language_model.generate_response(SYSTEM_PROMPT, prompt_message)

        if response is None:
            response = OFFLINE_RESPONSES[intent]

        return ChatResponse(
            response=response,
            intent=intent,
            conversation_id=request.conversation_id,
        )


placement_agent = PlacementAgent()