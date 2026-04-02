from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="图未初始化，请检查 MCP 与 lifespan。")
    thread_id = body.session_id or "default"
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=body.message)]}
    try:
        result = await graph.ainvoke(input_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图执行失败: {e}")
    messages = result.get("messages") or []
    reply = ""
    for m in reversed(messages):
        if hasattr(m, "content") and m.content and getattr(m, "type", "") == "ai":
            reply = m.content if isinstance(m.content, str) else str(m.content)
            break
    return ChatResponse(reply=reply or "（无回复）")
