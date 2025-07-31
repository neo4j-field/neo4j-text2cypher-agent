"""
Enhanced execution node that can optionally return graph results for visualization.
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_neo4j import Neo4jGraph
from neo4j import Result, RoutingControl

from neo4j_text2cypher.components.text2cypher.state import CypherState
from neo4j_text2cypher.components.text2cypher.state_with_viz import (
    CypherOutputStateWithViz
)
from neo4j_text2cypher.constants import NO_CYPHER_RESULTS


def create_text2cypher_execution_with_graph_node(
    graph: Neo4jGraph,
) -> Callable[
    [CypherState], Coroutine[Any, Any, Dict[str, List[CypherOutputStateWithViz] | List[str]]]
]:
    """
    Create an enhanced Text2Cypher execution node that can optionally return graph results.
    
    This node checks if visualization was requested during generation and executes accordingly:
    - If visualization is requested: Executes twice (records + graph)
    - Otherwise: Executes once (existing behavior)
    
    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    
    Returns
    -------
    Callable[[CypherState], Dict[str, List[CypherOutputStateWithViz] | List[str]]]
        The LangGraph node.
    """
    
    async def execute_cypher(
        state: CypherState,
    ) -> Dict[str, List[CypherOutputStateWithViz] | List[Any]]:
        """
        Executes the given Cypher statement with optional graph result.
        """
        statement = state.get("statement", "")
        task = state.get("task", "")
        steps = state.get("cypher_steps", list())
        steps.append("execute_cypher")
        
        # Check if visualization was requested (set by generation node)
        visualization_requested = state.get("visualization_requested", False)
        
        # Execute query for tabular results (existing behavior)
        records = graph.query(statement)
        
        # Initialize graph result
        graph_result = None
        
        # If visualization is requested AND we have results, also get graph representation
        if visualization_requested and records:
            try:
                # Use the underlying driver to execute with Result.graph transformer
                driver = graph._driver
                graph_result = driver.execute_query(
                    statement,
                    database_=graph._database,
                    routing_=RoutingControl.READ,
                    result_transformer_=Result.graph,
                )
                
                # Verify we got graph data
                if hasattr(graph_result, 'nodes') and hasattr(graph_result, 'relationships'):
                    node_count = len(graph_result.nodes)
                    rel_count = len(graph_result.relationships)
                    
                    if node_count == 0 and rel_count == 0:
                        # No graph data returned, clear the result
                        graph_result = None
                
            except Exception as e:
                # If graph execution fails, log but don't fail the whole query
                graph_result = None
        
        # Prepare the output state
        output_state = CypherOutputStateWithViz(
            **{
                "task": task,
                "statement": statement,
                "parameters": None,
                "errors": state.get("errors", list()),
                "records": records if records else NO_CYPHER_RESULTS,
                "cypher_steps": steps,
                "visualization_requested": visualization_requested,
                "graph_result": graph_result
            }
        )
        
        return {
            "cyphers": [output_state],
            "steps": [steps],
        }
    
    return execute_cypher