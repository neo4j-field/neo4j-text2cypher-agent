"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_neo4j import Neo4jGraph
from neo4j import Query

from neo4j_text2cypher.components.text2cypher.state import (
    CypherOutputState,
    CypherState,
)
from neo4j_text2cypher.constants import NO_CYPHER_RESULTS

# Try to import LangChain's sanitization function
try:
    from langchain_neo4j.graphs.neo4j_graph import _value_sanitize
    HAS_SANITIZE = True
except ImportError:
    HAS_SANITIZE = False


def create_text2cypher_execution_node(
    graph: Neo4jGraph,
) -> Callable[
    [CypherState], Coroutine[Any, Any, Dict[str, List[CypherOutputState] | List[str]]]
]:
    """
    Create a Text2Cypher execution node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.

    Returns
    -------
    Callable[[CypherState], Dict[str, List[CypherOutputState] | List[str]]]
        The LangGraph node.
    """

    async def execute_cypher(
        state: CypherState,
    ) -> Dict[str, List[CypherOutputState] | List[Any]]:
        """
        Executes the given Cypher statement.
        """
        statement = state.get("statement", "")
        
        # Execute query with session approachm this is get the Result object that our viz library needs to try and render
        if statement.strip():
            try:
                with graph._driver.session(database=graph._database) as session:
                    result_obj = session.run(Query(text=statement, timeout=graph.timeout))
                    records = [r.data() for r in result_obj]
                    
                    if graph.sanitize and HAS_SANITIZE:
                        records = [_value_sanitize(el) for el in records]
            except Exception:
                records = []
                result_obj = None
        else:
            records = []
            result_obj = None
        
        steps = state.get("cypher_steps", list())
        steps.append("execute_cypher")
        
        # Handle empty results
        result_records = records if records else NO_CYPHER_RESULTS
        
        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", ""),
                        "statement": statement,
                        "parameters": None,
                        "errors": state.get("errors", list()),
                        "records": result_records,
                        "cypher_steps": steps,
                        "result": result_obj,  # Neo4j Result object with .graph() method
                    }
                )
            ],
            "steps": [steps],
        }

    return execute_cypher
