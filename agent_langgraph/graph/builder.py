from langgraph.graph import StateGraph, START, END
from graph.state import ChatState
from graph.nodes import detect_intent_node, handle_intent_node


def build_chat_graph():
    graph = StateGraph(ChatState)

    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("handle_intent", handle_intent_node)

    graph.add_edge(START, "detect_intent")
    graph.add_edge("detect_intent", "handle_intent")
    graph.add_edge("handle_intent", END)

    return graph.compile()
