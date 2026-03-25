"""Generator – produce a final answer from retrieved context + user query."""

from __future__ import annotations

from app.rag.llm import chat_completion
from app.rag.retriever import RetrievedChunk

_SYSTEM_PROMPT = """\
你是一个家用电器智能问答助手。根据提供的参考资料回答用户关于设备的问题。
规则：
1. 优先基于 [设备实时信息] 回答，这是用户实际设备的真实数据。
2. 如果 [设备实时信息] 中包含设备型号、能力、状态等数据，请据此给出具体、确定的答案。
3. 仅当实时信息不足以回答问题时，才参考其他资料或通用知识。
4. 如果能从实时信息中获取具体型号、功能等，请直接陈述，不要使用"可能"、"也许"等不确定词汇。
5. 回答要准确、简洁、易懂。
6. 如果涉及操作步骤，请使用有序列表。
7. 如果涉及故障代码，请同时给出可能原因和建议操作。
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
    
    # Add device real-time info FIRST if available (highest priority)
    if extra_context:
        context_parts.insert(0, f"[设备实时信息 - 最高优先级]\n{extra_context}")
    
    # Then add RAG chunks
    for i, c in enumerate(chunks, 1):
        source = c.metadata.get("filename", "未知来源")
        context_parts.append(f"[参考资料 {i}] ({source}) {c.text}")
    
    if not context_parts:
        context = "暂无相关参考资料，将基于通用知识回答您的问题。"
    else:
        context = "\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _USER_TEMPLATE.format(context=context, query=query)},
    ]
    return chat_completion(messages)
