from __future__ import annotations

import re
from collections.abc import Sequence

from sialabs_local_rag.schemas import ConversationMessage

_WORD_PATTERN = re.compile(r"[\w'-]+", flags=re.UNICODE)
_REFERENCE_TERMS = {
    "aquele",
    "aquela",
    "aqueles",
    "aquelas",
    "aquilo",
    "dele",
    "dela",
    "deles",
    "delas",
    "ele",
    "ela",
    "eles",
    "elas",
    "isso",
    "isto",
    "mesmo",
    "mesma",
    "mesmos",
    "mesmas",
    "it",
    "its",
    "itself",
    "same",
    "that",
    "their",
    "theirs",
    "them",
    "they",
    "this",
    "those",
}
_FOLLOW_UP_PREFIXES = (
    "and ",
    "and what",
    "and how",
    "e ",
    "e como",
    "e o ",
    "e a ",
    "e quanto",
    "e sobre",
    "how about",
    "what about",
)
_MAX_ANCHOR_CHARS = 900


def build_retrieval_query(
    question: str,
    conversation_context: Sequence[ConversationMessage],
) -> str:
    current_question = question.strip()
    if not current_question or not _needs_conversation_anchor(current_question):
        return current_question

    previous_user_message = _latest_user_message(conversation_context)
    if previous_user_message is None:
        return current_question

    anchor = previous_user_message.content.strip()
    if not anchor:
        return current_question
    if len(anchor) > _MAX_ANCHOR_CHARS:
        anchor = anchor[-_MAX_ANCHOR_CHARS:]

    return f"{anchor}\nFollow-up: {current_question}"


def _needs_conversation_anchor(question: str) -> bool:
    lowered = question.casefold().strip()
    tokens = [token.casefold() for token in _WORD_PATTERN.findall(question)]

    if any(token in _REFERENCE_TERMS for token in tokens):
        return True

    return len(tokens) <= 4 and any(
        lowered.startswith(prefix) for prefix in _FOLLOW_UP_PREFIXES
    )


def _latest_user_message(
    conversation_context: Sequence[ConversationMessage],
) -> ConversationMessage | None:
    for message in reversed(conversation_context):
        if message.role == "user" and message.content.strip():
            return message
    return None
