import streamlit as st
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import create_neo4j_text2cypher_workflow


def _recreate_workflow_with_new_settings(break_into_subquestions: bool, similarity_type: str, k_value: int) -> None:
    """
    Recreate the workflow with new settings without reconnecting to Neo4j.
    
    This function uses the stored workflow components to quickly recreate the agent
    with the new settings, avoiding the need to restart the entire app.
    """
    components = st.session_state.workflow_components
    
    try:
        # Import retriever classes
        from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
        from neo4j_text2cypher.retrievers.similarity_retriever import SimilarityBasedCypherExampleRetriever
        
        # Create appropriate retriever based on similarity type
        if similarity_type == "Semantic Similarity":
            retriever = SimilarityBasedCypherExampleRetriever(
                config_loader=components["config_loader"], 
                k=k_value
            )
        else:  # Static
            retriever = ConfigCypherExampleRetriever(
                config_path=str(components["config_loader"].config_path)
            )
        
        # Recreate workflow with new settings
        new_agent = create_neo4j_text2cypher_workflow(
            llm=components["llm"],
            graph=components["graph"], 
            cypher_example_retriever=retriever,
            scope_description=components["scope_description"],
            max_attempts=components["max_attempts"],
            attempt_cypher_execution_on_final_attempt=components["attempt_cypher_execution_on_final_attempt"],
            break_into_subquestions=break_into_subquestions,  # New setting
        )
        
        # Update session state
        st.session_state.agent = new_agent
        st.session_state.break_into_subquestions = break_into_subquestions
        st.session_state.similarity_type = similarity_type
        st.session_state.k_value = k_value
        
        # Update workflow components with new retriever
        st.session_state.workflow_components["cypher_example_retriever"] = retriever
        
        # Prevent question re-submission after settings change
        st.session_state["submit_new_question"] = False
        
        # Show user that settings were updated with better formatting
        planner_status = "enabled" if break_into_subquestions else "disabled"
        st.success(f"""✅ Settings updated:

    • Break questions into subquestions: {planner_status}

    • Cypher Retriever Strategy: {similarity_type}

    • Number of examples: {k_value if similarity_type == "Semantic Similarity" else "All"}""")
        
    except Exception as e:
        st.error(f"❌ Failed to update settings: {str(e)}")
        # Revert settings to previous state - handled by Streamlit widget state


def sidebar() -> None:
    """
    The Streamlit app side bar.
    """

    # 1. Example Questions (primary entry point for usage)
    if st.session_state.get("example_questions"):
        st.sidebar.subheader("💡 Example Questions")
        for i, question in enumerate(st.session_state.example_questions):
            # Truncate long questions for better display
            display_text = question[:60] + "..." if len(question) > 60 else question
            if st.sidebar.button(
                display_text, key=f"sidebar_example_{i}", help=question
            ):
                st.session_state["current_question"] = question
                st.session_state["submit_new_question"] = True

        st.sidebar.divider()

    # 2. Query Processing Settings (controls that change behavior)
    st.sidebar.markdown("### 🔧 Query Processing Settings")
    
    # Get current settings
    current_break_into_subquestions = st.session_state.get("break_into_subquestions", True)
    current_similarity_type = st.session_state.get("similarity_type", "Static")
    current_k_value = st.session_state.get("k_value", 5)
    
    # Create an indented container for the settings
    with st.sidebar.container():
        # Add some left padding/indentation
        st.markdown("""<div style="padding-left: 20px;">""", unsafe_allow_html=True)
        
        # Planner Toggle
        break_into_subquestions = st.checkbox(
            "Break questions into subquestions", 
            value=current_break_into_subquestions,
            help="When enabled, complex questions are broken down into smaller sub-questions for better accuracy. When disabled, questions are processed as-is."
        )
        
        # Cypher Retriever Strategy with consistent header
        st.markdown("#### 🔍 Cypher Retriever Strategy")
        similarity_type = st.radio(
            "Select retriever strategy",  # Non-empty label for accessibility
            options=["Static", "Semantic Similarity"],
            index=0 if current_similarity_type == "Static" else 1,
            help="Static: Uses all configured examples for maximum context. Semantic Similarity: Selects most relevant examples based on question similarity.",
            label_visibility="collapsed"
        )
        
        # K Value slider (only show when semantic similarity is selected)
        if similarity_type == "Semantic Similarity":
            k_value = st.slider(
                "Number of examples",
                min_value=1,
                max_value=20,
                value=10 if current_k_value == 5 else current_k_value,
                help="Number of most similar examples to retrieve for query generation"
            )
        else:
            k_value = current_k_value  # Keep current value when not using semantic similarity
        
        # Close the indented div
        st.markdown("""</div>""", unsafe_allow_html=True)
    
    # If any setting changed, recreate workflow
    settings_changed = (
        break_into_subquestions != current_break_into_subquestions or
        similarity_type != current_similarity_type or
        k_value != current_k_value
    )
    
    if settings_changed and st.session_state.get("workflow_components"):
        _recreate_workflow_with_new_settings(break_into_subquestions, similarity_type, k_value)
    
    st.sidebar.divider()

    # 3. System Information (informational status)
    st.sidebar.subheader("⚙️ System Information")
    
    # LLM Details Section
    st.sidebar.write("**LLM Details**")
    model_name = st.session_state.get("model_name", "Unknown")
    model_provider = st.session_state.get("model_provider", "Unknown")
    model_temperature = st.session_state.get("model_temperature", "Unknown")
    st.sidebar.markdown(f"**Provider:** {model_provider} &nbsp;&nbsp;|&nbsp;&nbsp; **Model:** {model_name} &nbsp;&nbsp;|&nbsp;&nbsp; **Temperature:** {model_temperature}")
    
    # Neo4j Database Details
    st.sidebar.write("")  # Add some space
    st.sidebar.write("**Neo4j Database Details**")
    
    # Get Neo4j version info dynamically
    neo4j_database = st.session_state.get("neo4j_database", "Unknown")
    neo4j_status = st.session_state.get("neo4j_connected", False)
    connection_status = "🟢 Connected" if neo4j_status else "🔴 Disconnected"
    
    # Query Neo4j version if connected and agent is available
    if neo4j_status and st.session_state.get("workflow_components"):
        try:
            graph = st.session_state.workflow_components["graph"]
            version_result = graph.query("""
                CALL dbms.components() YIELD name, versions, edition
                UNWIND versions AS version
                WITH * WHERE name = 'Neo4j Kernel'
                RETURN edition, version
            """)
            if version_result and len(version_result) > 0:
                neo4j_edition = version_result[0].get('edition', 'Unknown')
                neo4j_version = version_result[0].get('version', 'Unknown')
                version_display = f"{neo4j_version} ({neo4j_edition})"
            else:
                version_display = "Unknown"
        except Exception:
            version_display = "Unknown"
    else:
        version_display = "Unknown"
    
    st.sidebar.markdown(f"**Version:** {version_display} &nbsp;&nbsp;|&nbsp;&nbsp; **Database:** {neo4j_database} &nbsp;&nbsp;|&nbsp;&nbsp; **Status:** {connection_status}")
    
    # Add some spacing before Reset Chat button
    st.sidebar.write("")
    st.sidebar.write("")
    
    # 4. Reset Chat (cleanup action at bottom)
    if len(st.session_state.get("messages", list())) > 0:
        if st.sidebar.button("Reset Chat", type="primary"):
            st.session_state["messages"] = []
            if "current_question" in st.session_state:
                del st.session_state["current_question"]
            if "submit_new_question" in st.session_state:
                del st.session_state["submit_new_question"]
            st.rerun()
