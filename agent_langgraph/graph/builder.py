from langgraph.graph import StateGraph, START, END
from graph.state import ChatState
from graph.nodes import detect_intent_node, generate_response_node


def build_chat_graph():
    graph = StateGraph(ChatState)

    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("generate_response", generate_response_node)

    graph.add_edge(START, "detect_intent")
    graph.add_edge("detect_intent", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()
