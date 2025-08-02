"""Neo4j graph visualization component for Streamlit."""

from typing import Optional, Dict, Tuple
import streamlit as st
import streamlit.components.v1 as components
from neo4j_viz.neo4j import from_neo4j
from neo4j import Result

# Default color palette for consistent node coloring
DEFAULT_COLORS = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#96CEB4",  # Green
    "#FECA57",  # Yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Mint
    "#F7DC6F",  # Light Yellow
    "#BB8FCE",  # Purple
    "#85C1E2",  # Light Blue
    "#FF8CC8",  # Pink
    "#A8E6CF",  # Light Green
    "#FFA07A",  # Light Salmon
    "#B0E0E6",  # Powder Blue
    "#20B2AA",  # Light Sea Green
    "#F4A460",  # Sandy Brown
]


def render_neo4j_graph_from_result(
    result: Result,
    height: int = 600,
    node_color_property: str = "labels",
    node_size_property: Optional[str] = None,
    row_limit: int = 50
) -> Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, str]]]:
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
        
    Returns
    -------
    Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, str]]]
        Tuple of (node_labels_count, relationship_types_count, color_mapping) for legend generation
    """
    node_labels_count = None
    relationship_types_count = None
    color_mapping = None
    try:
        # Create visualization directly from Neo4j result with row limit
        viz = from_neo4j(result, row_limit=row_limit)
        
        # Apply styling with custom color mapping
        if node_color_property:
            # First, extract unique labels to create color mapping
            try:
                graph_data = result.graph()
                # Use list to preserve order of appearance
                unique_labels_ordered = []
                seen_labels = set()
                
                if hasattr(graph_data, 'nodes'):
                    for node in graph_data.nodes:
                        labels = node.labels if hasattr(node, 'labels') else []
                        for label in labels:
                            if label not in seen_labels:
                                unique_labels_ordered.append(label)
                                seen_labels.add(label)
                
                # Create color mapping based on order of appearance
                color_mapping = {}
                
                for i, label in enumerate(unique_labels_ordered):
                    color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
                    color_mapping[label] = color
                
                # Apply colors to visualization using the color list
                if node_color_property == "labels":
                    viz.color_nodes(property=node_color_property, colors=DEFAULT_COLORS)
                else:
                    viz.color_nodes(property=node_color_property)
            except Exception:
                # Fallback to default coloring
                viz.color_nodes(property=node_color_property)
        
        if node_size_property:
            viz.resize_nodes(property=node_size_property)
        
        # Extract legend data before rendering
        try:
            graph_data = result.graph()
            
            # Count node labels
            node_labels_count = {}
            if hasattr(graph_data, 'nodes'):
                for node in graph_data.nodes:
                    labels = node.labels if hasattr(node, 'labels') else []
                    for label in labels:
                        node_labels_count[label] = node_labels_count.get(label, 0) + 1
            
            # Count relationship types
            relationship_types_count = {}
            if hasattr(graph_data, 'relationships'):
                for rel in graph_data.relationships:
                    rel_type = rel.type if hasattr(rel, 'type') else 'UNKNOWN'
                    relationship_types_count[rel_type] = relationship_types_count.get(rel_type, 0) + 1
        except Exception:
            # If we can't extract legend data, continue without it
            pass
        
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
            
            /* Style node labels with rounded edges (attempt) */
            .nvl-node-label,
            .node-label {{
                border-radius: 12px !important;
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
    
    return node_labels_count, relationship_types_count, color_mapping