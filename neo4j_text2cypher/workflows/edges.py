"""LangGraph edges that are used in multiple workflows."""

from typing import List, Literal

from langgraph.types import Send

from neo4j_text2cypher.components.state import OverallState


def guardrails_conditional_edge(
    state: OverallState,
) -> Literal["planner", "final_answer"]:
    match state.get("next_action"):
        case "final_answer":
            return "final_answer"
        case "end":
            return "final_answer"
        case "planner":
            return "planner"
        case _:
            return "final_answer"


def tool_select_conditional_edge(
    state: OverallState,
) -> Literal["summarize", "final_answer"]:
    match state.get("next_action"):
        case "summarize":
            return "summarize"
        case "final_answer":
            return "final_answer"
        case _:
            return "final_answer"



def query_mapper_edge(state: OverallState) -> List[Send]:
    """Map each task question to a Text2Cypher subgraph."""

    tasks = state.get("tasks", list())
    history = state.get("history", [])  # Get conversation history

    # Extract recent SUCCESSFUL Cypher queries (check both statement AND records)
    recent_cyphers = []
    for record in history:  # Use all history (max 5 conversations as per SIZE config)
        for cypher in record.get("cyphers", []):
            # Only include successful queries with actual results
            if cypher.get("statement") and cypher.get("records"):
                recent_cyphers.append(cypher["statement"])

    print(f"\n🔄 Query mapper: Sending {len(tasks)} task(s) to text2cypher")
    print(f"   Including {len(recent_cyphers)} recent successful Cypher queries for context")
    for i, task in enumerate(tasks):
        print(f"   Task {i+1}: {task.question}")

    # Pass history and recent cyphers along with the task
    sends = [
        Send("text2cypher", {
            "task": task.question,
            "conversation_history": history,  # Pass full history
            "recent_cyphers": recent_cyphers  # Pass recent successful queries
        })
        for task in tasks
    ]
    return sends
