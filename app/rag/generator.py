"""Generator – produce a final answer from retrieved context + user query."""

from __future__ import annotations

from app.rag.llm import chat_completion
from app.rag.retriever import RetrievedChunk

_SYSTEM_PROMPT = """\
你是一个家用电器智能问答助手。根据提供的参考资料回答用户关于设备的问题。
规则：
1. 仅基于提供的参考资料回答，如果资料中没有相关信息，请明确告知用户。
2. 回答要准确、简洁、易懂。
3. 如果涉及操作步骤，请使用有序列表。
4. 如果涉及故障代码，请同时给出可能原因和建议操作。
"""

_USER_TEMPLATE = """\
参考资料：
{context}

用户问题：{query}
"""


def generate_answer(
    query: str,
    chunks: list[RetrievedChunk],
    extra_context: str = "",
) -> str:
    """Build context from chunks and call LLM to produce an answer."""
    context_parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        source = c.metadata.get("filename", "未知来源")
        context_parts.append(f"[{i}] ({source}) {c.text}")

    if extra_context:
        context_parts.append(f"[设备实时信息] {extra_context}")

    context = "\n\n".join(context_parts) if context_parts else "暂无相关参考资料，将基于通用知识回答您的问题。"

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _USER_TEMPLATE.format(context=context, query=query)},
    ]
    return chat_completion(messages)
