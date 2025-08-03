from typing import Literal, Union

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from neo4j_text2cypher.components.state import (
    OverallState,
)
from neo4j_text2cypher.components.text2cypher import (
    create_text2cypher_correction_node,
    create_text2cypher_execution_node,
    create_text2cypher_generation_node,
    create_text2cypher_validation_node,
)
from neo4j_text2cypher.components.text2cypher.state import CypherInputState, CypherState
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
from neo4j_text2cypher.retrievers.similarity_retriever import SimilarityBasedCypherExampleRetriever


def create_text2cypher_agent(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: Union[ConfigCypherExampleRetriever, SimilarityBasedCypherExampleRetriever],
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
    result_limit: int = 50,
) -> CompiledStateGraph:
    """
    Create a Text2Cypher agent using LangGraph.
    
    The agent contains only Text2cypher components with no guardrails, query parser or 
    summarizer, and may be used as an independent workflow or a node in a larger 
    LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM to use for processing.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_example_retriever: Union[ConfigCypherExampleRetriever, SimilarityBasedCypherExampleRetriever]
        The retriever used to collect Cypher examples for few shot prompting.
        Can be either config-based (all examples) or similarity-based (relevant examples).
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt: bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False
    result_limit: int, optional
        Maximum number of rows to return in query results, by default 50

    Returns
    -------
    CompiledStateGraph
        The compiled workflow.
    """
    
    # Create nodes
    generate_cypher = create_text2cypher_generation_node(
        llm=llm, graph=graph, cypher_example_retriever=cypher_example_retriever, result_limit=result_limit
    )
    
    validate_cypher = create_text2cypher_validation_node(
        llm=llm,
        graph=graph,
        max_attempts=max_attempts,
        attempt_cypher_execution_on_final_attempt=attempt_cypher_execution_on_final_attempt,
    )
    
    correct_cypher = create_text2cypher_correction_node(llm=llm, graph=graph)
    
    execute_cypher = create_text2cypher_execution_node(graph=graph)
    
    # Build the graph
    text2cypher_graph_builder = StateGraph(
        CypherState, input=CypherInputState, output=OverallState
    )
    
    # Add nodes
    text2cypher_graph_builder.add_node("generate_cypher", generate_cypher)
    text2cypher_graph_builder.add_node("validate_cypher", validate_cypher)
    text2cypher_graph_builder.add_node("correct_cypher", correct_cypher)
    text2cypher_graph_builder.add_node("execute_cypher", execute_cypher)
    
    # Add edges - simple linear flow with validation loop
    text2cypher_graph_builder.add_edge(START, "generate_cypher")
    text2cypher_graph_builder.add_edge("generate_cypher", "validate_cypher")
    text2cypher_graph_builder.add_conditional_edges(
        "validate_cypher",
        validate_cypher_conditional_edge,
    )
    text2cypher_graph_builder.add_edge("correct_cypher", "validate_cypher")
    text2cypher_graph_builder.add_edge("execute_cypher", END)
    
    return text2cypher_graph_builder.compile()


def validate_cypher_conditional_edge(
    state: CypherState,
) -> Literal["correct_cypher", "execute_cypher", "__end__"]:
    match state.get("next_action_cypher"):
        case "correct_cypher":
            return "correct_cypher"
        case "execute_cypher":
            return "execute_cypher"
        case "__end__":
            return "__end__"
        case _:
            return "__end__"
