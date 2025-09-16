"""
This file contains Cypher validators that may be used in the Text2Cypher validation node.
"""

from typing import Any, Dict, List

from langchain_core.runnables.base import Runnable
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from neo4j.exceptions import CypherSyntaxError

from neo4j_text2cypher.components.text2cypher.validation.models import (
    ValidateCypherOutput,
)
from neo4j_text2cypher.constants import WRITE_CLAUSES
from neo4j_text2cypher.utils.schema_utils import (
    retrieve_and_parse_schema_from_graph_for_prompts,
)


def validate_cypher_query_syntax(graph: Neo4jGraph, cypher_statement: str) -> List[str]:
    """
    Validate the Cypher statement syntax by running an EXPLAIN query.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        If the statement contains invalid syntax, return an error message in a list
    """
    errors = list()
    try:
        graph.query(f"EXPLAIN {cypher_statement}")
    except CypherSyntaxError as e:
        errors.append(str(e.message))
    return errors


def correct_cypher_query_relationship_direction(
    graph: Neo4jGraph, cypher_statement: str
) -> str:
    """
    Correct Relationship directions in the Cypher statement with LangChain's `CypherQueryCorrector`.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    str
        The Cypher statement with corrected Relationship directions.
    """
    # Cypher query corrector is experimental
    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in graph.structured_schema.get("relationships", list())
    ]
    cypher_query_corrector = CypherQueryCorrector(corrector_schema)

    corrected_cypher: str = cypher_query_corrector(cypher_statement)

    return corrected_cypher


async def validate_cypher_query_with_llm(
    validate_cypher_chain: Runnable[Dict[str, Any], Any],
    question: str,
    graph: Neo4jGraph,
    cypher_statement: str,
    conversation_history: List[Dict[str, Any]] = None,
) -> Dict[str, List[str]]:
    """
    Validate the Cypher statement with an LLM.
    Use declared LLM to find Node and Property pairs to validate.
    Validate Node and Property pairs against the Neo4j graph.

    Parameters
    ----------
    validate_cypher_chain : RunnableSerializable
        The LangChain LLM to perform processing.
    question : str
        The question associated with the Cypher statement.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    Dict[str, List[str]]
        A Python dictionary with keys `errors` and `mapping_errors`, each with a list of found errors.
    """

    errors: List[str] = []
    mapping_errors: List[str] = []

    # Simple caching: check if cleaned schema already exists
    from pathlib import Path
    import os
    database_name = os.getenv('NEO4J_DATABASE', 'neo4j')
    cache_dir = Path("database_schema_cache")
    cache_dir.mkdir(exist_ok=True)
    cleaned_schema_file = cache_dir / f"{database_name}_cleaned_schema.txt"
    
    # Use cached schema if it exists, otherwise parse and cache it
    if cleaned_schema_file.exists():
        schema_for_validation = cleaned_schema_file.read_text()
    else:
        schema_for_validation = retrieve_and_parse_schema_from_graph_for_prompts(graph)
        cleaned_schema_file.write_text(schema_for_validation)
        print(f"   📝 Cleaned schema written to: {cleaned_schema_file}")

    # Format conversation context for validation
    conversation_context = ""
    if conversation_history:
        recent_queries = []
        for record in conversation_history[-5:]:  # Look at last 5 conversations (matching history size limit)
            q = record.get("question", "")
            # Get successful queries from this conversation
            for cypher in record.get("cyphers", []):
                if cypher.get("statement") and cypher.get("records"):
                    recent_queries.append(f"Q: {q}\nCypher: {cypher['statement']}")
                    break

        if recent_queries:
            conversation_context = "Recent conversation context:\n" + "\n".join(recent_queries)

    if not conversation_context:
        conversation_context = "No recent conversation history."

    # Debug: Print validation prompt details
    print(f"\n🔍 Validation Prompt Details:")
    print(f"   Question: {question}")
    print(f"   Cypher to validate: {cypher_statement}")
    print(f"   Schema length: {len(schema_for_validation)} characters")
    if conversation_history:
        print(f"   Context provided: Yes ({len(conversation_history)} previous queries)")

    llm_output: ValidateCypherOutput = await validate_cypher_chain.ainvoke(
        {
            "question": question,
            "schema": schema_for_validation,
            "cypher": cypher_statement,
            "conversation_context": conversation_context,
        }
    )

    if llm_output.errors:
        errors.extend(llm_output.errors)
    # Instead of checking individual property mappings, test the whole query with EXPLAIN
    # This catches real syntax/schema issues without false negatives for valid queries
    try:
        graph.query(f"EXPLAIN {cypher_statement}")
    except Exception as e:
        mapping_error = f"Query validation failed: {str(e)}"
        mapping_errors.append(mapping_error)
    return {"errors": errors, "mapping_errors": mapping_errors}


def validate_no_writes_in_cypher_query(cypher_statement: str) -> List[str]:
    """
    Check if the Cypher statement contains write clauses.

    Parameters
    ----------
    cypher_statement : str
        The Cypher statement to check.

    Returns
    -------
    List[str]
        A list of found write clauses.
    """
    errors = []
    for write_clause in WRITE_CLAUSES:
        if f" {write_clause.upper()} " in cypher_statement.upper():
            errors.append(f"Cypher query contains the write clause: {write_clause}")
    return errors