import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()


class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    search_results: list[dict]
    report: str
    history: list[str]


def search_web(state: ResearchState) -> ResearchState:
    try:
        tool = TavilySearch(max_results=5)
        raw = tool.invoke(state["query"])

        results = raw.get("results", []) if isinstance(raw, dict) else []
        return {"search_results": results}

    except Exception as e:
        print("Search error:", e)
        return {"search_results": []}


def synthesize_report(state: ResearchState) -> ResearchState:

    llm = ChatNVIDIA(
        model="meta/llama-3.1-8b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0,
        max_tokens=2000,
    )

    query = state["query"]
    lower_query = query.lower()

    messages = state.get("messages", [])
    history = state.get("history", [])
    updated_history = history + [query]

    # ✅ ✅ NORMALIZE MESSAGES (CRITICAL FIX)
    normalized_messages = []

    for msg in messages:
        if isinstance(msg, dict):
            normalized_messages.append(msg)

        elif isinstance(msg, HumanMessage):
            normalized_messages.append({
                "role": "user",
                "content": msg.content
            })

        elif isinstance(msg, AIMessage):
            normalized_messages.append({
                "role": "assistant",
                "content": msg.content
            })

    # ✅ NAME MEMORY FIX
    if "what is my name" in lower_query or "do you know my name" in lower_query:
        for msg in reversed(normalized_messages):
            if msg["role"] == "user" and "my name is" in msg["content"].lower():
                name = msg["content"].split("is")[-1].strip()
                return {
                    "report": f"Your name is {name}",
                    "history": updated_history,
                    "messages": normalized_messages
                }

        return {
            "report": "I don't know your name yet.",
            "history": updated_history,
            "messages": normalized_messages
        }

    # ✅ LAST QUESTION FIX
    if "last question" in lower_query:
        if len(history) >= 1:
            return {
                "report": f"Your last question was: {history[-1]}",
                "history": updated_history,
                "messages": normalized_messages
            }

    # ✅ ✅ LLM FLOW
    system_prompt = """
You are a helpful AI research assistant.

Rules:
- Answer clearly
- Use previous messages if useful
- Do NOT invent facts
- If unsure say "I don't know"
"""

    search_results = state.get("search_results", [])

    if search_results:
        web_data = "\n\n".join(
            f"{r.get('title')}\n{r.get('content')}"
            for r in search_results
        )
        system_prompt += f"\n\nWeb Data:\n{web_data}"

    chat_messages = [SystemMessage(content=system_prompt.strip())]

    # ✅ last 10 messages only
    prev_messages = normalized_messages[-10:]

    for msg in prev_messages:
        if msg["role"] == "user":
            chat_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_messages.append(AIMessage(content=msg["content"]))

    chat_messages.append(HumanMessage(content=query))

    # ✅ STREAM
    chunks = []
    for chunk in llm.stream(chat_messages):
        if chunk.content:
            chunks.append(chunk.content)

    response = "".join(chunks)

    return {
        "report": response,
        "history": updated_history[-10:],
        "messages": prev_messages + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": response},
        ],
    }


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("search", search_web)
    graph.add_node("synthesize", synthesize_report)

    graph.set_entry_point("search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
