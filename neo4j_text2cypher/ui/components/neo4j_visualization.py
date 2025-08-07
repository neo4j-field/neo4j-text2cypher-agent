"""Neo4j graph visualization component for Streamlit."""

from typing import Optional, Dict, Tuple, List, Set
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


@st.cache_data
def _generate_color_mapping(node_labels: List[str]) -> Dict[str, str]:
    """
    Generate a color mapping for node labels.
    Cached to avoid recalculation for the same set of labels.
    
    Parameters
    ----------
    node_labels : List[str]
        List of unique node labels in order of appearance
        
    Returns
    -------
    Dict[str, str]
        Mapping of label to color hex code
    """
    color_mapping = {}
    for i, label in enumerate(node_labels):
        color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
        color_mapping[label] = color
    return color_mapping


@st.cache_data
def _compute_graph_statistics(nodes_data: List[Dict], relationships_data: List[Dict]) -> Tuple[Dict[str, int], Dict[str, int], int]:
    """
    Compute node and relationship statistics from graph data.
    Cached to avoid recalculation for the same graph structure.
    
    Parameters
    ----------
    nodes_data : List[Dict]
        List of node data dictionaries
    relationships_data : List[Dict]
        List of relationship data dictionaries
        
    Returns
    -------
    Tuple[Dict[str, int], Dict[str, int], int]
        Tuple of (node_labels_count, relationship_types_count, unique_node_count)
    """
    # Count node labels (for distribution display)
    node_labels_count = {}
    for node_dict in nodes_data:
        labels = node_dict.get('labels', [])
        for label in labels:
            node_labels_count[label] = node_labels_count.get(label, 0) + 1
    
    # Count actual unique nodes
    unique_node_count = len(nodes_data)
    
    # Count relationship types
    relationship_types_count = {}
    for rel_dict in relationships_data:
        rel_type = rel_dict.get('type', 'UNKNOWN')
        relationship_types_count[rel_type] = relationship_types_count.get(rel_type, 0) + 1
    
    return node_labels_count, relationship_types_count, unique_node_count


def render_neo4j_graph_from_result(
    result: Result,
    height: int = 600,
    node_color_property: str = "labels",
    node_size_property: Optional[str] = None,
    row_limit: int = 50,
    layout: str = "force-directed",
    direction: Optional[str] = None
) -> Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, str]], Optional[int]]:
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
    layout : str, optional
        Layout algorithm to use: "force-directed" or "hierarchical", by default "force-directed"
    direction : Optional[str], optional
        Direction for hierarchical layout: "down", "up", "left", "right", by default None
        
    Returns
    -------
    Tuple[Optional[Dict[str, int]], Optional[Dict[str, int]], Optional[Dict[str, str]], Optional[int]]
        Tuple of (node_labels_count, relationship_types_count, color_mapping, unique_node_count) for legend generation
    """
    node_labels_count = None
    relationship_types_count = None
    color_mapping = None
    unique_node_count = None
    try:
        # Create visualization from result
        viz = from_neo4j(result)
        
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
                
                # Use cached color mapping generation
                color_mapping = _generate_color_mapping(unique_labels_ordered)
                
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
            
            # Convert nodes and relationships to serializable format for caching
            nodes_data = []
            relationships_data = []
            
            if hasattr(graph_data, 'nodes'):
                for node in graph_data.nodes:
                    node_dict = {
                        'labels': list(node.labels) if hasattr(node, 'labels') else []
                    }
                    nodes_data.append(node_dict)
            
            if hasattr(graph_data, 'relationships'):
                for rel in graph_data.relationships:
                    rel_dict = {
                        'type': rel.type if hasattr(rel, 'type') else 'UNKNOWN'
                    }
                    relationships_data.append(rel_dict)
            
            # Use cached statistics computation
            node_labels_count, relationship_types_count, unique_node_count = _compute_graph_statistics(nodes_data, relationships_data)
            
        except Exception:
            # If we can't extract legend data, continue without it
            pass
        
        # Render the visualization with layout configuration
        if layout == "hierarchical":
            from neo4j_viz import Layout, HierarchicalLayoutOptions, Direction
            
            # Configure hierarchical layout options if direction is specified
            if direction:
                direction_map = {
                    "down": Direction.DOWN,
                    "up": Direction.UP, 
                    "left": Direction.LEFT,
                    "right": Direction.RIGHT
                }
                layout_options = HierarchicalLayoutOptions(
                    direction=direction_map.get(direction, Direction.DOWN)
                )
                html_content = viz.render(
                    layout=Layout.HIERARCHICAL, 
                    layout_options=layout_options,
                    max_allowed_nodes=1000  # Allow up to 1000 nodes
                )._repr_html_()
            else:
                html_content = viz.render(
                    layout=Layout.HIERARCHICAL,
                    max_allowed_nodes=1000  # Allow up to 1000 nodes
                )._repr_html_()
        else:
            # Default force-directed layout
            html_content = viz.render(
                max_allowed_nodes=1000  # Allow up to 1000 nodes
            )._repr_html_()
        
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
    
    return node_labels_count, relationship_types_count, color_mapping, unique_node_count