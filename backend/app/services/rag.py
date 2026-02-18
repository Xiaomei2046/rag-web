from app.llm.chat import ChatResult, ChatUsage, chat_complete


def build_context(retrieved: list[dict]) -> str:
    lines: list[str] = []
    for item in retrieved:
        chunk = item["chunk"]
        doc_title = item["doc_title"]
        lines.append(
            "\n".join(
                [
                    f"doc_title: {doc_title}",
                    f"chunk_id: {chunk.id}",
                    f"page_start: {chunk.page_start}",
                    f"page_end: {chunk.page_end}",
                    "content:",
                    chunk.content,
                ]
            )
        )
    return "\n\n---\n\n".join(lines)


async def answer_with_rag(
    *,
    provider: str,
    model: str,
    question: str,
    retrieved: list[dict],
    temperature: float,
) -> ChatResult:
    if not retrieved:
        return ChatResult(
            content="无法在教材中定位相关内容。请尝试换一种问法，或先确认教材已入库完成。",
            usage=ChatUsage(),
        )

    context = build_context(retrieved)
    system = (
        "你是一个面向教材的问答助手。只能使用用户提供的教材片段回答问题。"
        "如果片段不足以回答，请明确说无法定位或信息不足，不要编造。"
        "回答要简洁，优先给出结论，再给出要点。"
    )
    user = "\n\n".join(
        [
            "教材片段如下：",
            context,
            "",
            f"问题：{question}",
        ]
    )
    result = await chat_complete(
        provider=provider,
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )
    return result
