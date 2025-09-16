"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.guardrails.models import GuardrailsOutput
from neo4j_text2cypher.components.guardrails.prompts import (
    create_guardrails_prompt_template,
)
from neo4j_text2cypher.components.state import InputState


def format_conversation_history_for_guardrails(history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for the guardrails prompt.

    Parameters
    ----------
    history : List[Dict[str, Any]]
        The conversation history.

    Returns
    -------
    str
        Formatted conversation history string.
    """
    if not history:
        return "No previous conversation history."

    formatted_history = "Previous conversation context:\n"
    for i, record in enumerate(history, 1):
        formatted_history += f"{i}. Q: {record['question']}\n"
        formatted_history += f"   A: {record['answer']}\n"

    return formatted_history


def create_guardrails_node(
    llm: BaseChatModel,
    graph: Optional[Neo4jGraph] = None,
    scope_description: Optional[str] = None,
) -> Callable[[InputState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a guardrails node to be used in a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM used to process data.
    graph: Optional[Neo4jGraph], optional
        The `Neo4jGraph` object used to generated a schema definition, by default None
    scope_description : Optional[str], optional
        A description of the application scope, by default None

    Returns
    -------
    Callable[[InputState], OverallState]
        The LangGraph node.
    """

    guardrails_prompt = create_guardrails_prompt_template(
        graph=graph, scope_description=scope_description
    )

    guardrails_chain: Runnable[Dict[str, Any], Any] = (
        guardrails_prompt
        | llm.with_structured_output(GuardrailsOutput, method="function_calling")
    )

    async def guardrails(state: InputState) -> Dict[str, Any]:
        """
        Decides if the question is in scope.
        """

        print(f"📝 User Question: {state.get('question')}")

        # Get conversation history for context
        history = state.get("history", [])
        conversation_history = format_conversation_history_for_guardrails(history)

        guardrails_output: GuardrailsOutput = await guardrails_chain.ainvoke(
            {
                "question": state.get("question"),
                "conversation_history": conversation_history,
            }
        )
        summary = None
        if guardrails_output.decision == "end":
            summary = "This question is out of scope. Therefore I cannot answer this question."
        return {
            "next_action": guardrails_output.decision,
            "summary": summary,
            "steps": ["guardrails"],
        }

    return guardrails
