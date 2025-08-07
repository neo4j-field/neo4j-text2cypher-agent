import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
from neo4j_text2cypher.ui.components import chat, display_chat_history, sidebar
from neo4j_text2cypher.utils.config import ConfigLoader
from neo4j_text2cypher.utils.llm_factory import create_llm
from neo4j_text2cypher.utils.schema_cache import load_schema_cache, save_schema_cache
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import (
    create_neo4j_text2cypher_workflow,
)

if load_dotenv():
    print("Env Loaded Successfully!")
else:
    print("Unable to Load Environment.")


def get_config_loader() -> ConfigLoader:
    """Parse the command line arguments and return config loader."""

    args = sys.argv
    if len(args) > 1:
        config_path: str = args[1]

        # Only support YAML configs
        if config_path.lower().endswith((".yml", ".yaml")):
            return ConfigLoader(config_path)
        else:
            raise ValueError(
                f"Only YAML config files (.yml/.yaml) are supported: {config_path}"
            )
    else:
        raise ValueError(
            "Config file path is required. Usage: streamlit run app.py <config.yml>"
        )


def initialize_state(config_loader: ConfigLoader) -> None:
    """Initialize the application state with progress tracking."""

    if "agent" not in st.session_state:
        # Create a temporary container for initialization UI
        init_container = st.container()
        
        with init_container:
            # Create a clean initialization UI without duplicate spinners
            st.markdown("### Initializing application...")
            init_content = st.container()
            
            with init_content:
                # Create placeholders for each step
                step_placeholders = {
                    "config": st.empty(),
                    "neo4j_params": st.empty(),
                    "schema": st.empty(),
                    "llm": st.empty(),
                    "workflow": st.empty()
                }
                
                try:
                    # Helper function to show spinner
                    def show_spinner(placeholder, message):
                        placeholder.markdown(
                            f'<div style="display: flex; align-items: center; gap: 0.5rem;">'
                            f'<div class="spinner" style="display: inline-flex;">'
                            f'<div style="'
                            f'width: 1rem; height: 1rem; border: 3px solid #f0f2f6; '
                            f'border-left-color: #0068c9; border-radius: 50%; '
                            f'animation: spin 1s linear infinite;"></div></div>'
                            f'<style>@keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}</style>'
                            f'{message}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Step 1: Configuration
                    show_spinner(step_placeholders["config"], "Loading configuration...")
                    streamlit_config = config_loader.get_streamlit_config()
                    step_placeholders["config"].write("✅ Configuration loaded")
                    
                    # Step 2: Neo4j Connection Parameters
                    show_spinner(step_placeholders["neo4j_params"], "Preparing Neo4j connection...")
                    neo4j_params = config_loader.get_neo4j_connection_params()
                    # Default to enhanced schema for better validation
                    neo4j_params['enhanced_schema'] = True
                    step_placeholders["neo4j_params"].write("✅ Neo4j connection prepared")
                    
                    # Step 3: Schema Extraction with Caching (optimized for large databases)
                    database_name = neo4j_params.get("database", "neo4j")
                    cached_schema = load_schema_cache(database_name)
                    
                    if cached_schema:
                        # Fast path: Load from cache
                        show_spinner(step_placeholders["schema"], "Loading cached schema...")
                        graph = Neo4jGraph(**neo4j_params, refresh_schema=False)
                        graph.schema = cached_schema
                        step_placeholders["schema"].write("✅ Database schema loaded from cache")
                    else:
                        # Slow path: Extract and cache
                        show_spinner(step_placeholders["schema"], "Connecting to Neo4j and extracting schema (this may take a moment for large databases)...")
                        graph = Neo4jGraph(**neo4j_params, refresh_schema=True)
                        save_schema_cache(database_name, graph.schema)
                        step_placeholders["schema"].write("✅ Database schema extracted and cached")
                    
                    # Step 4: LLM Setup
                    show_spinner(step_placeholders["llm"], "Initializing language model...")
                    llm = create_llm(config_loader)
                    llm_config = config_loader.get_llm_config()
                    step_placeholders["llm"].write("✅ Language model initialized")
                    
                    # Step 5: Examples and Workflow
                    show_spinner(step_placeholders["workflow"], "Loading examples and creating workflow...")
                    # Use semantic similarity retriever by default
                    from neo4j_text2cypher.retrievers.similarity_retriever import SimilarityBasedCypherExampleRetriever
                    cypher_example_retriever = SimilarityBasedCypherExampleRetriever(
                        config_loader=config_loader,
                        k=10  # Default k value
                    )
                    
                    # Create the workflow with default settings
                    agent = create_neo4j_text2cypher_workflow(
                        llm=llm,
                        graph=graph,
                        scope_description=streamlit_config.scope_description,
                        cypher_example_retriever=cypher_example_retriever,
                        attempt_cypher_execution_on_final_attempt=True,
                        break_into_subquestions=False,  # Default to disabled
                        result_limit=100,  # Default result limit
                    )
                    step_placeholders["workflow"].write("✅ Workflow created")
                    
                    # Step 6: Complete
                    st.session_state.agent = agent
                    st.session_state.messages = []
                    st.session_state.example_questions = streamlit_config.example_questions
                    
                    # Initialize new query processing settings
                    st.session_state.break_into_subquestions = False  # Default to disabled
                    st.session_state.similarity_type = "Semantic Similarity"  # Default to semantic retrieval
                    st.session_state.k_value = 10  # Default K value for semantic similarity
                    st.session_state.result_limit = 100  # Default result limit
                    
                    # Store system information for UI display
                    st.session_state.model_name = llm_config.model
                    st.session_state.model_provider = llm_config.provider.replace("_", " ").title()
                    st.session_state.model_temperature = llm_config.temperature
                    st.session_state.neo4j_database = neo4j_params.get("database", "neo4j")
                    st.session_state.neo4j_connected = True  # If we got here, connection succeeded
                    
                    # Store workflow components for dynamic recreation
                    st.session_state.workflow_components = {
                        "llm": llm,
                        "graph": graph,
                        "cypher_example_retriever": cypher_example_retriever,
                        "scope_description": streamlit_config.scope_description,
                        "max_attempts": 3,
                        "attempt_cypher_execution_on_final_attempt": True,
                        "config_loader": config_loader,  # Needed for similarity retriever
                        "result_limit": 100,  # Default result limit
                    }
                    
                    # Application initialization complete
                    init_container.empty()
                    init_container.success("✅ Application ready!")
                    
                except Exception as e:
                    init_container.error(f"❌ Initialization failed: {str(e)}")
                    # Set connection status to failed for UI display
                    st.session_state.neo4j_connected = False
                    st.session_state.model_name = "Failed to load"
                    st.session_state.model_provider = "Unknown"
                    st.session_state.model_temperature = "Unknown"
                    st.session_state.neo4j_database = "Unknown"
                    st.session_state.workflow_components = None  # Prevent sidebar errors
                    st.stop()
        
        # Force a rerun to clear the initialization UI and show the main app
        st.rerun()


async def run_app(
    title: str = "Simple Text2Cypher Assistant", scope_description: str = ""
) -> None:
    """
    Run the Streamlit application.
    """

    st.title(title)
    if scope_description:
        st.write(scope_description)
    sidebar()
    display_chat_history()

    # Prompt for user input and save and display
    if question := st.chat_input("Ask a question about your graph data..."):
        st.session_state["current_question"] = question
        st.session_state["submit_new_question"] = True

    if st.session_state.get("submit_new_question", False):
        await chat(str(st.session_state.get("current_question", "")))
        st.session_state["submit_new_question"] = False


def main() -> None:
    """
    Main function to run the Streamlit application.
    """

    config_loader = get_config_loader()
    streamlit_config = config_loader.get_streamlit_config()

    st.set_page_config(
        page_title=streamlit_config.title, 
        page_icon="🤖", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

    initialize_state(config_loader)

    asyncio.run(
        run_app(
            title=streamlit_config.title,
            scope_description=streamlit_config.scope_description,
        )
    )


if __name__ == "__main__":
    main()
