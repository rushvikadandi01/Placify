import re

from ..schemas.chat import ChatIntent


def _contains_any(message: str, phrases: tuple[str, ...]) -> bool:
    normalized_message = f" {re.sub(r'[^a-z0-9+#]+', ' ', message.lower()).strip()} "
    return any(f" {phrase} " in normalized_message for phrase in phrases)


def classify_intent(message: str) -> ChatIntent:
    if _contains_any(message, ("project",)) and _contains_any(
        message,
        ("interview", "question", "explain", "describe", "architecture", "resume", "challenge"),
    ):
        return ChatIntent.PROJECT_INTERVIEW

    if _contains_any(
        message,
        (
            "hr",
            "human resources",
            "behavioral interview",
            "behavioral question",
            "tell me about yourself",
            "strengths",
            "weaknesses",
            "why should we hire you",
        ),
    ):
        return ChatIntent.HR

    if _contains_any(
        message,
        ("study plan", "study schedule", "preparation plan", "weekly plan", "daily plan", "roadmap"),
    ):
        return ChatIntent.STUDY_PLAN

    if _contains_any(
        message,
        (
            "interview",
            "interview me",
            "mock interview",
            "technical interview",
            "hr interview",
            "project interview",
            "interview practice",
        ),
    ):
        return ChatIntent.INTERVIEW

    if _contains_any(
        message,
        (
            "aptitude",
            "quantitative",
            "percentage",
            "profit and loss",
            "profit loss",
            "ratio",
            "ratio and proportion",
            "average",
            "time and work",
            "time speed distance",
            "simple interest",
            "compound interest",
            "probability",
            "permutation",
            "combination",
            "number system",
            "number series",
            "coding decoding",
            "blood relation",
            "directions",
            "syllogism",
            "seating arrangement",
            "logical reasoning",
            "reasoning question",
            "verbal ability",
            "grammar",
            "vocabulary",
            "sentence correction",
            "reading comprehension",
        ),
    ):
        return ChatIntent.APTITUDE

    if _contains_any(
        message,
        (
            "dsa",
            "data structure",
            "algorithm",
            "array",
            "string",
            "hashmap",
            "hash map",
            "hashset",
            "hash set",
            "linked list",
            "stack",
            "queue",
            "tree",
            "trees",
            "binary tree",
            "binary trees",
            "bst",
            "heap",
            "priority queue",
            "graph",
            "recursion",
            "dynamic programming",
            "sorting",
            "searching",
        ),
    ):
        return ChatIntent.DSA

    if _contains_any(
        message,
        (
            "tcp",
            "udp",
            "network",
            "osi",
            "http",
            "dns",
            "database",
            "dbms",
            "sql",
            "operating system",
            "process",
            "thread",
            "deadlock",
            "normalization",
            "object oriented",
            "oops",
            "compiler",
            "virtual memory",
        ),
    ):
        return ChatIntent.CORE_CS

    return ChatIntent.GENERAL