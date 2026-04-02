"""LangGraph 多智能体客服编排模块。"""
import os
from typing import Annotated, Literal, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    current_node: str
    intent: str
    escalate_to_human: bool
    need_human_reason: Optional[str]
    ticket_id: Optional[str]


def _get_llm():
    return ChatTongyi(
        model="qwen-max",
        dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        streaming=False,
    )


def _router(state: AgentState) -> AgentState:
    """意图识别并路由到相应节点。"""
    messages = state.get("messages") or []
    if not messages:
        return {"intent": "unknown", "escalate_to_human": False, "current_node": "router"}
    last = messages[-1]
    if not hasattr(last, "content") or not last.content:
        return {"intent": "unknown", "escalate_to_human": False, "current_node": "router"}
    text = last.content.strip().lower()
    if "转人工" in text or "人工客服" in text or "转接" in text:
        return {
            "intent": "handoff",
            "escalate_to_human": True,
            "need_human_reason": "用户要求转人工",
            "current_node": "router",
        }
    try:
        llm = _get_llm()
        prompt = f"""你是一个客服意图分类器，叫老六。用户说：「{last.content}」
请只回复以下 exactly 一个词，不要其他内容：
faq  - 咨询、问答、退货、退款、配送等通用问题
ticket - 查工单、创建工单、查单号、工单状态
handoff - 明确要转人工
unknown - 无法判断"""
        out = llm.invoke([HumanMessage(content=prompt)])
        intent_raw = (out.content or "").strip().lower()
    except Exception:
        if "工单" in text or "ticket" in text:
            intent_raw = "ticket"
        else:
            intent_raw = "faq"
    if "handoff" in intent_raw:
        intent, escalate = "handoff", True
    elif "ticket" in intent_raw or "工单" in intent_raw:
        intent, escalate = "ticket", False
    elif "faq" in intent_raw or "unknown" in intent_raw:
        intent, escalate = "faq", False
    else:
        intent, escalate = "faq", False
    return {
        "intent": intent,
        "escalate_to_human": escalate,
        "need_human_reason": "用户要求转人工" if escalate else None,
        "current_node": "router",
    }


def _run_tools(tools: list, tool_calls: list, messages: list) -> list:
    """执行工具调用并返回结果。"""
    by_name = {t.name: t for t in tools}
    result = []
    for tc in tool_calls:
        name = getattr(tc, "name", None) or (tc.get("name") if isinstance(tc, dict) else None)
        args = getattr(tc, "args", None) or (tc.get("args") if isinstance(tc, dict) else {}) or {}
        tid = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None) or ""
        tool = by_name.get(name)
        if not tool:
            result.append(ToolMessage(content=f"未知工具: {name}", tool_call_id=tid))
            continue
        try:
            out = tool.invoke(args)
            result.append(ToolMessage(content=str(out) if out is not None else "完成", tool_call_id=tid))
        except Exception as e:
            result.append(ToolMessage(content=f"错误: {e}", tool_call_id=tid))
    return result


def _make_qa_agent(tools: list):
    qa_tools = [t for t in tools if getattr(t, "name", None) == "search_faq"]

    def qa_agent(state: AgentState) -> AgentState:
        if state.get("escalate_to_human"):
            return {"current_node": "qa_agent"}
        messages = list(state.get("messages") or [])
        if not messages:
            return {"messages": [AIMessage(content="请问有什么可以帮您？")], "current_node": "qa_agent"}
        if not qa_tools:
            return {
                "messages": [AIMessage(content="知识库暂不可用，建议输入「转人工」联系客服。")],
                "current_node": "qa_agent",
            }
        try:
            llm = _get_llm()
            if qa_tools:
                llm = llm.bind_tools(qa_tools)
            response = llm.invoke(messages)
        except Exception:
            if qa_tools:
                query = str(getattr(messages[-1], "content", "") or "")
                try:
                    out = qa_tools[0].invoke({"query": query})
                    return {"messages": [AIMessage(content=str(out))], "current_node": "qa_agent"}
                except Exception:
                    pass
            return {
                "messages": [AIMessage(content="模型暂不可用，请稍后重试或输入「转人工」。")],
                "current_node": "qa_agent",
            }
        if response.tool_calls:
            tool_msgs = _run_tools(qa_tools, response.tool_calls, messages)
            messages = messages + [response] + tool_msgs
            response = llm.invoke(messages)
        reply = (response.content or "").strip()
        if not reply:
            reply = "未找到相关解答，您可输入「转人工」联系客服。"
        return {"messages": [AIMessage(content=reply)], "current_node": "qa_agent"}

    return qa_agent


def _make_ticket_agent(tools: list):
    ticket_tools = [t for t in tools if getattr(t, "name", None) in ("get_ticket", "create_ticket", "update_ticket")]

    def ticket_agent(state: AgentState) -> AgentState:
        if state.get("escalate_to_human"):
            return {"current_node": "ticket_agent"}
        messages = list(state.get("messages") or [])
        if not messages:
            return {"messages": [AIMessage(content="请问需要查工单还是创建工单？")], "current_node": "ticket_agent"}
        if not ticket_tools:
            return {
                "messages": [AIMessage(content="工单服务暂不可用，建议输入「转人工」联系客服。")],
                "current_node": "ticket_agent",
            }
        try:
            llm = _get_llm()
            if ticket_tools:
                llm = llm.bind_tools(ticket_tools)
            response = llm.invoke(messages)
        except Exception:
            return {
                "messages": [AIMessage(content="模型暂不可用，请输入工单号后重试或转人工。")],
                "current_node": "ticket_agent",
            }
        if response.tool_calls:
            tool_msgs = _run_tools(ticket_tools, response.tool_calls, messages)
            messages = messages + [response] + tool_msgs
            response = llm.invoke(messages)
        reply = (response.content or "").strip() or "工单相关操作已完成。"
        return {"messages": [AIMessage(content=reply)], "current_node": "ticket_agent"}

    return ticket_agent


def _human_handoff(state: AgentState) -> AgentState:
    reason = state.get("need_human_reason") or "转接人工客服"
    msg = f"已将您转接人工客服（原因：{reason}），请稍候。"
    return {"messages": [AIMessage(content=msg)], "current_node": "human_handoff"}


def _after_router(state: AgentState) -> str:
    if state.get("escalate_to_human"):
        return "human_handoff"
    intent = state.get("intent") or "unknown"
    if intent == "ticket":
        return "ticket_agent"
    return "qa_agent"


def _after_qa(state: AgentState) -> str:
    return "human_handoff" if state.get("escalate_to_human") else "__end__"


def _after_ticket(state: AgentState) -> str:
    return "human_handoff" if state.get("escalate_to_human") else "__end__"


def get_graph(tools: list):
    """构建并编译 LangGraph 图。"""
    builder = StateGraph(AgentState)

    builder.add_node("router", _router)
    builder.add_node("qa_agent", _make_qa_agent(tools))
    builder.add_node("ticket_agent", _make_ticket_agent(tools))
    builder.add_node("human_handoff", _human_handoff)

    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", _after_router, {"qa_agent": "qa_agent", "ticket_agent": "ticket_agent", "human_handoff": "human_handoff"})
    builder.add_conditional_edges("qa_agent", _after_qa, {"human_handoff": "human_handoff", "__end__": END})
    builder.add_conditional_edges("ticket_agent", _after_ticket, {"human_handoff": "human_handoff", "__end__": END})
    builder.add_edge("human_handoff", END)

    return builder.compile(checkpointer=MemorySaver())
