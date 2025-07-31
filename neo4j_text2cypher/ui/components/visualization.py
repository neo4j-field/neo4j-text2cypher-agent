"""Neo4j graph visualization component for Streamlit."""

from typing import Optional
import streamlit as st
import streamlit.components.v1 as components
from neo4j_viz.neo4j import from_neo4j
from neo4j import Result


def render_neo4j_graph_from_result(
    result: Result,
    height: int = 600,
    node_color_property: str = "labels",
    node_size_property: Optional[str] = None,
    row_limit: int = 50
) -> None:
    """
    Render Neo4j Result.graph as an interactive visualization.
    
    Parameters
    ----------
    result : neo4j.Result
        The Neo4j Result object with graph transformer applied
    height : int, optional
        Height of the visualization in pixels, by default 600
    node_color_property : str, optional
        Property to use for node coloring, by default "labels"
    node_size_property : Optional[str], optional
        Property to use for node sizing, by default None
    row_limit : int, optional
        Maximum number of rows to include in visualization, by default 50
    """
    try:
        # Create visualization directly from Neo4j result with row limit
        viz = from_neo4j(result, row_limit=row_limit)
        
        # Apply styling
        if node_color_property:
            viz.color_nodes(property=node_color_property)
        
        if node_size_property:
            viz.resize_nodes(property=node_size_property)
        
        # Render the visualization
        html_content = viz.render()._repr_html_()
        
        # Add CSS to hide scrollbars and ensure proper fit
        styled_content = f"""
        <style>
            body, html {{
                overflow: hidden !important;
                margin: 0;
                padding: 0;
            }}
            .neo4j-viz {{
                overflow: hidden !important;
            }}
        </style>
        {html_content}
        """
        
        # Display in Streamlit
        components.html(styled_content, height=height, scrolling=False)
        
        # Show statistics
        if hasattr(result, 'nodes') and hasattr(result, 'relationships'):
            st.caption(f"Graph contains {len(result.nodes)} nodes and {len(result.relationships)} relationships")
        
    except Exception as e:
        st.error(f"Error rendering graph visualization: {str(e)}")
        st.exception(e)