"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.utils.schema_utils import (
    retrieve_and_parse_schema_from_graph_for_prompts,
)

guardrails_system = """
You must decide whether the provided question is in scope.
Assume the question might be related.
If you're absolutely sure it is NOT related, output "end".
Provide only the specified output: "planner" or "end".
"""


def create_guardrails_prompt_template(
    graph: Optional[Neo4jGraph] = None, scope_description: Optional[str] = None
) -> ChatPromptTemplate:
    """
    Create a guardrails prompt template.

    Parameters
    ----------
    graph : Optional[Neo4jGraph], optional
        The `Neo4jGraph` object used to generated a schema definition, by default None
    scope_description : Optional[str], optional
        A description of the application scope, by default None

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    scope_context = (
        f"Use this scope description to inform your decision:\n{scope_description}"
        if scope_description is not None
        else ""
    )
    graph_context = (
        f"\nUse the graph schema to inform your answer:\n{retrieve_and_parse_schema_from_graph_for_prompts(graph)}"
        if graph is not None
        else ""
    )
    message = scope_context + graph_context + "\nQuestion: {question}"

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                guardrails_system,
            ),
            (
                "human",
                (message),
            ),
        ]
    )
