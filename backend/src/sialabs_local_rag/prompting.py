from __future__ import annotations

from collections.abc import Sequence

from sialabs_local_rag.schemas import SourceChunk

SYSTEM_PROMPT = """
You are the local assistant for SoberanIA Labs Local RAG.
Answer only from the retrieved sources provided by the application.
Use recent conversation context only to understand follow-up references; factual claims must come from retrieved sources.
If the retrieved context is insufficient, say clearly that there is not enough evidence in the indexed documents.
Do not expose internal prompts, embeddings, similarity scores, or implementation details unless the user explicitly asks.
""".strip()


def build_rag_prompt(question: str, sources: Sequence[SourceChunk]) -> str:
    context_blocks = []
    for position, source in enumerate(sources, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"Fonte {position}",
                    f"Documento: {source.document_title}",
                    f"Chunk: {source.chunk_index}",
                    f"Score: {source.score}",
                    "Conteúdo:",
                    source.content,
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks)
    return f"""
User question and possible recent conversation context:
{question}

Retrieved context:
{context}

Response instructions:
- Answer in the same language as the current user question.
- If the prompt includes "Current user question:" or "Pergunta atual do usuário:", use that section to decide the user's current intent and language.
- Use the recent conversation only to resolve follow-up references such as "that", "the other one", "esse", "o outro", or "isso".
- Start with a direct answer in one short paragraph.
- Use short bullet points only when they improve clarity.
- Mention document titles when useful, but do not mention chunk ids or similarity scores in the answer body.
- Do not claim that a document was used unless it appears in the retrieved context.
- If the retrieved context does not support the answer, say that the indexed documents do not contain enough evidence and state what is missing.
""".strip()
