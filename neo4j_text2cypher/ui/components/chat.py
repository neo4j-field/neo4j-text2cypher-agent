from typing import Any, Dict, List
import hashlib

import pandas as pd
import streamlit as st
from langgraph.errors import GraphRecursionError
from neo4j.exceptions import SessionExpired
from neo4j_text2cypher.ui.components.feedback_utils import save_feedback

# Feedback reason options - edit here to change dropdown options
FEEDBACK_REASON_OPTIONS = [
    "Select a reason...",
    "Incorrect Results",
    "Invalid Cypher",
    "Incomplete Response",
    "Performance Issue",
    "Misunderstood Question"
]


from neo4j_text2cypher.components.state import (
    CypherHistoryRecord,
    HistoryRecord,
    OutputState,
)
from neo4j_text2cypher.ui.components.neo4j_visualization import (
    render_neo4j_graph_from_result
)


@st.fragment
def visualization_controls(viz_id: str, result_obj, cypher: Dict[str, Any]) -> None:
    """
    Fragment-based visualization controls that won't trigger full page reruns.
    
    Parameters
    ----------
    viz_id : str
        Unique identifier for this visualization
    result_obj : Result
        The Neo4j result object to visualize
    cypher : Dict[str, Any]
        The cypher query details
    """
    # Initialize state if needed
    layout_key = f"{viz_id}_layout"
    direction_key = f"{viz_id}_direction"
    node_limit_key = f"{viz_id}_node_limit"
    
    if layout_key not in st.session_state:
        st.session_state[layout_key] = "force-directed"
    if direction_key not in st.session_state:
        st.session_state[direction_key] = "up"
    if node_limit_key not in st.session_state:
        st.session_state[node_limit_key] = 100
    
    # Create controls
    col1, col2, col3, col4 = st.columns([2, 2, 3, 5])
    
    with col1:
        layout = st.selectbox(
            "Layout",
            options=["force-directed", "hierarchical"],
            key=layout_key,
            help="Select visualization layout"
        )
    
    with col2:
        if layout == "hierarchical":
            direction = st.selectbox(
                "Direction",
                options=["up", "down", "left", "right"],
                key=direction_key,
                help="Direction for hierarchical layout"
            )
        else:
            # Keep empty for layout consistency
            st.empty()
            direction = st.session_state[direction_key]
    
    # Create visualization container that will update when controls change
    viz_container = st.container()
    
    with viz_container:
        # Create columns for visualization and legend
        viz_col, legend_col = st.columns([5, 1])
        
        with viz_col:
            # Get the node limit from session state (default 100)
            node_limit = st.session_state.get(node_limit_key, 100)
            
            # Render with selected layout and direction
            node_labels, rel_types, color_mapping, unique_node_count = render_neo4j_graph_from_result(
                result_obj, 
                height=600,
                layout=layout,
                direction=direction if layout == "hierarchical" else None,
                row_limit=node_limit  # Use the configured limit
            )
        
        with legend_col:
            if node_labels or rel_types:
                st.markdown("### Results Overview")
                
                if node_labels:
                    # Use unique_node_count if available, otherwise fall back to sum (for backward compatibility)
                    total_nodes = unique_node_count if unique_node_count is not None else sum(node_labels.values())
                    st.markdown(f"#### **Nodes ({total_nodes})**")
                    for label, count in sorted(node_labels.items()):
                        if color_mapping and label in color_mapping:
                            color = color_mapping[label]
                            st.markdown(
                                f'<span style="background-color: {color}; color: black; padding: 2px 6px; border-radius: 12px; font-weight: bold;">{label} ({count})</span>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f"**{label} ({count})**")
                    st.write("")  # Add space
                
                if rel_types:
                    total_relationships = sum(rel_types.values())
                    st.markdown(f"#### **Relationships ({total_relationships})**")
                    for rel_type, count in sorted(rel_types.items()):
                        st.markdown(
                            f'<span style="background-color: #E0E0E0; color: black; padding: 2px 6px; border-radius: 12px; font-weight: bold;">{rel_type} ({count})</span>',
                            unsafe_allow_html=True
                        )


def _is_graph_value(value: Any) -> bool:
    """
    Check if a value is a graph object (node, relationship, or path).
    
    Parameters
    ----------
    value : Any
        The value to check
        
    Returns
    -------
    bool
        True if the value is a graph object
    """
    # Check for Neo4j Node or Relationship (they're usually dicts with specific attributes)
    if isinstance(value, dict):
        # Neo4j nodes/relationships typically have 'id', 'labels', or 'type' attributes
        # But to be safe, we'll consider any dict as potential graph object
        # unless it looks like plain data
        graph_indicators = {'id', 'labels', 'type', 'properties', 'start_node', 'end_node'}
        return bool(graph_indicators.intersection(value.keys()))
    
    # Check for paths (usually lists containing nodes and relationships)
    if isinstance(value, list) and value:
        # If it's a list of dicts, it might be a path
        first_item = value[0]
        if isinstance(first_item, dict):
            # Check if it looks like graph elements
            graph_indicators = {'id', 'labels', 'type', 'properties', 'start_node', 'end_node'}
            return bool(graph_indicators.intersection(first_item.keys()))
    
    return False


def convert_records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of records to a pandas DataFrame for better display.
    Filters out graph objects (nodes, relationships, paths) when mixed with scalar data.
    
    Parameters
    ----------
    records : List[Dict[str, Any]]
        The records from Cypher query results
        
    Returns
    -------
    pd.DataFrame
        DataFrame for interactive display with graph objects filtered out
    """
    if not records:
        return pd.DataFrame()
    
    try:
        # First, analyze which columns contain graph vs scalar data
        if records:
            first_record = records[0]
            graph_columns = set()
            scalar_columns = set()
            
            for key, value in first_record.items():
                if _is_graph_value(value):
                    graph_columns.add(key)
                else:
                    scalar_columns.add(key)
        
        # If we have both graph and scalar columns, filter out graph columns
        if graph_columns and scalar_columns:
            # Filter to only scalar columns for cleaner display
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key in scalar_columns:
                    if key in record:
                        cleaned_record[key] = _convert_value_for_dataframe(record[key])
                cleaned_records.append(cleaned_record)
        else:
            # No filtering needed - either all graph or all scalar
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    cleaned_record[key] = _convert_value_for_dataframe(value)
                cleaned_records.append(cleaned_record)
        
        return pd.DataFrame(cleaned_records)
        
    except Exception:
        # Any error - just return empty DataFrame 
        return pd.DataFrame()


def _convert_value_for_dataframe(value: Any) -> str:
    """
    Convert a value to a DataFrame-friendly representation.
    
    Parameters
    ----------
    value : Any
        The value to convert
        
    Returns
    -------
    str
        String representation suitable for DataFrame display
    """
    if value is None:
        return ""
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, list):
        return _convert_path_or_list(value)
    elif isinstance(value, dict):
        # Handle node/relationship objects - show key properties
        return _convert_node_or_relationship(value)
    else:
        return str(value)


def _convert_path_or_list(path_list: list) -> str:
    """Convert list to readable string, keeping raw data for download purposes."""
    if not path_list:
        return ""
    
    # Simple list handling - just convert to string representation
    if len(path_list) <= 5 and all(isinstance(item, (str, int, float)) for item in path_list):
        # Simple list with few items - comma separated
        return ", ".join(str(item) for item in path_list)
    else:
        # Complex or long list - keep as string representation for raw data access
        return str(path_list)


def _display_cypher_results(cypher: Dict[str, Any]) -> None:
    """
    Display results for a single cypher query (DataFrame and/or visualization).
    
    Parameters
    ----------
    cypher : Dict[str, Any]
        The cypher record containing statement, records, result, etc.
    """
    records = cypher.get("records")
    
    # Show DataFrame first if there are records with non-graph data
    if records and not _has_only_node_objects(records):
        df = convert_records_to_dataframe(records)
        if not df.empty:
            st.subheader("Results")
            st.dataframe(df, use_container_width=True)
        else:
            # Fallback: show raw data when DataFrame conversion fails
            st.subheader("Results")
            st.json(records[:10])  # Show first 10 records as JSON
            if len(records) > 10:
                st.caption(f"Showing first 10 of {len(records)} records")
    
    # Then show visualization if we have graph data
    result_obj = cypher.get("result")
    if result_obj and records:
        try:
            # Check if Result has nodes to visualize
            graph_data = result_obj.graph()
            nodes_count = len(graph_data.nodes) if hasattr(graph_data, 'nodes') else 0
            
            if nodes_count > 0:
                # Create a unique ID for this visualization instance
                # Use the Python id() of the cypher dict to ensure uniqueness
                viz_id = f"viz_{id(cypher)}"
                
                # Call the fragment that contains both controls and visualization
                visualization_controls(viz_id, result_obj, cypher)
        except Exception as e:
            st.error(f"Error displaying graph visualization: {str(e)}")


def _has_only_node_objects(records: List[Dict[str, Any]]) -> bool:
    """
    Check if records contain ONLY graph objects (nodes/relationships/paths) with no scalar data.
    
    Parameters
    ----------
    records : List[Dict[str, Any]]
        The records to check
        
    Returns
    -------
    bool
        True if records contain only graph objects
    """
    if not records:
        return False
    
    # Check first few records for performance
    for record in records[:3]:
        for value in record.values():
            # Use our graph detection helper to check if this is a graph object
            if not _is_graph_value(value):
                return False  # Found non-graph data
    return True  # All values are graph objects


def _convert_node_or_relationship(obj: dict) -> str:
    """Convert a Neo4j node or relationship to a simple label representation."""
    if not obj:
        return "Node"
    
    # Just show it's a node/object - users can see details in visualization
    return "Node"


def convert_streamlit_messages_to_history() -> List[HistoryRecord]:
    """
    Convert Streamlit session messages to HistoryRecord format.

    Returns
    -------
    List[HistoryRecord]
        List of conversation history records.
    """
    messages = st.session_state.get("messages", [])
    history_records = []

    # Process messages in pairs (user question + assistant response)
    for i in range(0, len(messages) - 1, 2):
        if i + 1 < len(messages):
            user_msg = messages[i]
            assistant_msg = messages[i + 1]

            # Ensure we have a user-assistant pair
            if (
                user_msg.get("role") == "user"
                and assistant_msg.get("role") == "assistant"
            ):
                question = user_msg.get("content", "")
                assistant_content = assistant_msg.get("content", {})

                # Handle AddableValuesDict from LangGraph - convert to regular dict
                if hasattr(assistant_content, "get") and not isinstance(
                    assistant_content, (str, dict)
                ):
                    # Convert AddableValuesDict to regular dict
                    assistant_content = dict(assistant_content)

                # Handle case where assistant_content might be a string (error messages)
                if isinstance(assistant_content, str):
                    answer = assistant_content
                    cyphers = []
                else:
                    answer = assistant_content.get("answer", "")
                    cypher_states = assistant_content.get("cyphers", [])

                    # Convert cypher states to CypherHistoryRecord format
                    cyphers = []
                    for cypher_state in cypher_states:
                        cypher_record = CypherHistoryRecord(
                            task=cypher_state.get("task", ""),
                            statement=cypher_state.get("statement", ""),
                            records=cypher_state.get("records", []),
                        )
                        cyphers.append(cypher_record)

                history_record = HistoryRecord(
                    question=question, answer=answer, cyphers=cyphers
                )
                history_records.append(history_record)

    return history_records


def append_user_question(question: str) -> None:
    st.session_state.get("messages", []).append({"role": "user", "content": question})
    st.chat_message("user").markdown(question)


async def append_llm_response(question: str) -> None:
    with st.chat_message("assistant"):
        # Create a container that will completely replace its content
        response_container = st.container()
        
        # Show only thinking status initially
        with response_container:
            thinking_placeholder = st.empty()
            with thinking_placeholder:
                st.status("thinking...")
        
        
        agent = st.session_state.get("agent")

        if agent is not None:
            try:
                # Convert Streamlit messages to HistoryRecord format
                history = convert_streamlit_messages_to_history()

                response: OutputState = await agent.ainvoke(
                    {"question": question, "data": [], "history": history},
                    config={"recursion_limit": 30},
                )
                # Add the question to the response for feedback tracking
                response["question"] = question

                # Clear thinking status and show response
                thinking_placeholder.empty()
                with response_container:
                    with st.expander("Response", expanded=True):
                        # Show the answer text
                        st.markdown(response.get("answer", ""))
                        
                        # Add feedback widget for the current response
                        render_feedback_widget(response)
                        
                        # Show response details if there are cyphers
                        show_cypher_response_information(response=response, is_latest_response=True)

                st.session_state.get("messages", []).append(
                    {"role": "assistant", "content": response}
                )
            except GraphRecursionError:
                error_msg = "Query exceeded processing limits. Please try a simpler question or break it into smaller parts."
                thinking_placeholder.empty()
                with response_container:
                    st.error(error_msg)
                st.session_state.get("messages", []).append(
                    {"role": "assistant", "content": {"answer": error_msg}}
                )
            except Exception as e:
                error_msg = f"Unexpected error occurred: {str(e)}"
                thinking_placeholder.empty()
                with response_container:
                    st.error(error_msg)
                st.session_state.get("messages", []).append(
                    {"role": "assistant", "content": {"answer": error_msg}}
                )
        else:
            error_msg = "Agent not available. Please refresh the page."
            thinking_placeholder.empty()
            with response_container:
                st.error(error_msg)
            st.session_state.get("messages", []).append(
                {"role": "assistant", "content": {"answer": error_msg}}
            )



def show_cypher_response_information(response: OutputState, is_latest_response: bool = False) -> None:
    if response.get("cyphers") and len(response.get("cyphers", list())) > 0:
        # Simple header for response details
        header_text = "📊 Response Details"
        
        # Create a collapsible expander for the entire response
        with st.expander(header_text, expanded=is_latest_response):
            cyphers = response.get("cyphers", list())
            
            if len(cyphers) > 1:
                # Show query headers only for multiple queries
                for i, cypher in enumerate(cyphers):
                    st.markdown(f"### {i+1}. {cypher.get('task', '')}")
                    
                    with st.expander("Generated Cypher / Results"):
                        st.code(cypher.get("statement"), language="cypher")
                        if cypher.get("parameters"):
                            st.write("Parameters:", cypher.get("parameters"))
                        
                        # Display results using common function
                        _display_cypher_results(cypher)
            else:
                # Single query - simpler display with auto-expanded inner section
                cypher = cyphers[0]
                with st.expander("Generated Cypher / Results", expanded=True):
                    st.write(cypher.get("task", ""))
                    st.code(cypher.get("statement"), language="cypher")
                    if cypher.get("parameters"):
                        st.write("Parameters:", cypher.get("parameters"))
                    
                    # Display results using common function
                    _display_cypher_results(cypher)


async def chat(question: str) -> None:
    try:
        append_user_question(question=question)
        await append_llm_response(question=question)
    except SessionExpired as e:
        st.error(f"Neo4j Session expired. Please restart the application. Error: {e}")


def display_message_with_feedback(message: dict, index: int) -> None:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        if role == "user":
            st.markdown(content)
        else:
            # Show assistant response with feedback buttons
            with st.expander("Response", expanded=True):
                st.markdown(content.get("answer", ""))
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"👍", key=f"up_{index}"):
                        _save_feedback_ui(content, "correct")
                with col2:
                    if st.button(f"👎", key=f"down_{index}"):
                        _save_feedback_ui(content, "incorrect")
                #show_cypher_response_information(response=content)


def display_chat_history() -> None:
    messages = st.session_state.get("messages", [])
    for i, message in enumerate(messages):
        with st.chat_message(message["role"]):
            if message.get("role") == "user":
                st.markdown(message.get("content"))
            else:
                response_content = message["content"]
                # Check if this is the latest message
                is_latest = (i == len(messages) - 1)
                
                with st.expander("Response", expanded=True):
                    st.markdown(response_content.get("answer", ""))
                    
                    # Only show feedback widget for the latest message
                    if is_latest:
                        render_feedback_widget(response_content)
                    else:
                        # For historical messages, just show if feedback was submitted
                        response_id = hashlib.md5(response_content.get("answer", "").encode()).hexdigest()[:8]
                        if st.session_state.get(f"feedback_saved_{response_id}"):
                            st.markdown("---")
                            st.success("✅ Feedback submitted")
                    
                    show_cypher_response_information(response=response_content)

def render_feedback_widget(response_content: dict) -> None:
    """
    Renders the feedback widget for a response. 
    This is used in both append_llm_response and display_chat_history to avoid duplication.
    """
    st.markdown("---")
    
    # Use a unique ID for this response
    response_id = hashlib.md5(response_content.get("answer", "").encode()).hexdigest()[:8]
    
    if st.session_state.get(f"feedback_saved_{response_id}"):
        st.success("✅ Feedback submitted")
    else:
        st.markdown("**Was this response helpful?**")
        
        # Store response in session state
        if f"response_{response_id}" not in st.session_state:
            st.session_state[f"response_{response_id}"] = response_content
        
        # Display feedback widget
        feedback_value = st.feedback(
            "thumbs", 
            key=f"feedback_{response_id}"
        )
        
        # Check feedback value
        if feedback_value == 1:
            # Thumbs up - save immediately
            _save_feedback_ui(response_content, "correct", None, response_id)
            st.rerun()
        elif feedback_value == 0:
            # Thumbs down - show reason dropdown
            st.markdown("**Please select a reason:**")
            
            reason = st.selectbox(
                "Feedback reason",
                FEEDBACK_REASON_OPTIONS,
                key=f"reason_select_{response_id}",
                label_visibility="collapsed"
            )
            
            # Auto-submit when a reason is selected
            if reason != "Select a reason...":
                _save_feedback_ui(response_content, "incorrect", reason, response_id)
                st.rerun()


def _save_feedback_ui(response_content: dict, validation: str, reason: str = None, response_id: str = None) -> None:
    question = response_content.get("question", "")
    # Handle both single cypher and multiple cyphers
    cypher_stmt = ""
    if response_content.get("cyphers") and len(response_content.get("cyphers", [])) > 0:
        # Get the first cypher statement if there are multiple
        cypher_stmt = response_content.get("cyphers", [{}])[0].get("statement", "")
    elif response_content.get("cypher"):
        cypher_stmt = response_content.get("cypher", {}).get("statement", "")
    response_text = response_content.get("answer", "")
    save_feedback(question, cypher_stmt, response_text, validation, reason)
    # Store feedback status using the response_id 
    if response_id:
        st.session_state[f"feedback_saved_{response_id}"] = True




