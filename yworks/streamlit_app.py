import asyncio
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from streamlit.components.v1 import html
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

# Import from the correct modules - matching the working app
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
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

st.set_page_config(
    page_title="Neo4j Query with yFiles Visualization",
    page_icon="🔗",
    layout="wide"
)

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
        # Default to example config
        config_path = "example_apps/iqs_data_explorer/app-config.yml"
        return ConfigLoader(config_path)


def initialize_state(config_loader: ConfigLoader) -> None:
    """Initialize the application state - matching the working app exactly."""
    
    if "agent" not in st.session_state:
        with st.spinner("Initializing LangGraph workflow..."):
            try:
                # Step 1: Configuration
                streamlit_config = config_loader.get_streamlit_config()
                
                # Step 2: Neo4j Connection Parameters
                neo4j_params = config_loader.get_neo4j_connection_params()
                # Default to enhanced schema for better validation
                neo4j_params['enhanced_schema'] = True
                
                # Step 3: Schema Extraction with Caching - EXACT same as working app
                database_name = neo4j_params.get("database", "neo4j")
                cached_schema = load_schema_cache(database_name)
                
                if cached_schema:
                    # Fast path: Load from cache
                    graph = Neo4jGraph(**neo4j_params, refresh_schema=False)
                    graph.schema = cached_schema
                else:
                    # Slow path: Extract and cache
                    graph = Neo4jGraph(**neo4j_params, refresh_schema=True)
                    save_schema_cache(database_name, graph.schema)
                
                # Step 4: LLM Setup - EXACT same as working app
                llm = create_llm(config_loader)
                llm_config = config_loader.get_llm_config()
                
                # Step 5: Examples and Workflow - EXACT same as working app
                cypher_example_retriever = ConfigCypherExampleRetriever(
                    config_path=str(config_loader.config_path)
                )
                
                # Create the workflow with settings to disable planner
                agent = create_neo4j_text2cypher_workflow(
                    llm=llm,
                    graph=graph,
                    scope_description=streamlit_config.scope_description,
                    cypher_example_retriever=cypher_example_retriever,
                    attempt_cypher_execution_on_final_attempt=False,
                    break_into_subquestions=False,  # Disabled as requested
                    result_limit=50,  # Default result limit
                )
                
                # Store in session state - matching working app
                st.session_state.agent = agent
                st.session_state.messages = []
                st.session_state.example_questions = streamlit_config.example_questions
                
                # Store system information for UI display
                st.session_state.model_name = llm_config.model
                st.session_state.database_name = database_name
                st.session_state.streamlit_config = streamlit_config
                st.session_state.graph = graph
                st.session_state.query_results = None
                
            except Exception as e:
                st.error(f"❌ Initialization failed: {str(e)}")
                st.stop()


def load_yfiles_resources():
    """Load yFiles resources for visualization"""
    bundle_path = Path('yworks/dist/yfiles.bundle.js')
    css_path = Path('yworks/dist/yfiles.css')
    license_path = Path('yworks/license.json')
    viz_html_path = Path('yworks/visualization.html')
    
    if not bundle_path.exists():
        return None, None, None, None
    
    with open(bundle_path, 'r', encoding='utf-8') as f:
        bundle_content = f.read()
    
    css_content = ""
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
    
    license_content = "{}"
    if license_path.exists():
        with open(license_path, 'r', encoding='utf-8') as f:
            license_content = f.read()
    
    html_template = ""
    if viz_html_path.exists():
        with open(viz_html_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    
    return bundle_content, css_content, license_content, html_template


def convert_neo4j_to_yfiles_format(graph_nodes, graph_relationships):
    """Convert Neo4j graph data to yFiles visualization format
    
    Args:
        graph_nodes: List of Neo4j Node objects from result.graph().nodes
        graph_relationships: List of Neo4j Relationship objects from result.graph().relationships
    """
    nodes = []
    edges = []
    node_map = {}
    node_id_counter = 1
    
    # Convert nodes
    for node in graph_nodes:
        # Use element_id as it's more stable than id (which is deprecated)
        neo4j_id = node.element_id if hasattr(node, 'element_id') else node.id
        
        # Map Neo4j ID to yFiles sequential ID
        node_map[neo4j_id] = node_id_counter
        
        # Extract labels and properties
        labels = list(node.labels) if hasattr(node, 'labels') else []
        label_text = ":".join(labels) if labels else "Node"
        props = dict(node) if hasattr(node, '__iter__') else {}
        
        # Create display label with some properties
        prop_text = ""
        if props:
            # Show first 2 properties for display
            prop_items = list(props.items())[:2]
            prop_text = "\n".join([f"{k}: {str(v)[:20]}" for k, v in prop_items])
        
        display_label = f"{label_text}\n{prop_text}" if prop_text else label_text
        
        nodes.append({
            "id": node_id_counter,
            "label": display_label,
            "properties": props,
            "labels": labels,
            "neo4j_id": neo4j_id
        })
        node_id_counter += 1
    
    # Convert relationships
    for rel in graph_relationships:
        # Get start and end node IDs
        start_neo4j_id = rel.start_node.element_id if hasattr(rel.start_node, 'element_id') else rel.start_node.id
        end_neo4j_id = rel.end_node.element_id if hasattr(rel.end_node, 'element_id') else rel.end_node.id
        
        # Only add edge if both nodes exist in our map
        if start_neo4j_id in node_map and end_neo4j_id in node_map:
            edges.append({
                "source": node_map[start_neo4j_id],
                "target": node_map[end_neo4j_id],
                "type": rel.type if hasattr(rel, 'type') else "RELATED",
                "properties": dict(rel) if hasattr(rel, '__iter__') else {}
            })
    
    return {"nodes": nodes, "edges": edges}


async def run_query(agent, question: str):
    """Run a query through the LangGraph workflow"""
    try:
        result = await agent.ainvoke({"question": question})
        return result
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return None


def main():
    """Main application function"""
    
    # Initialize configuration
    config_loader = get_config_loader()
    initialize_state(config_loader)
    
    # Load yFiles resources
    bundle_content, css_content, license_content, html_template = load_yfiles_resources()
    yfiles_available = bundle_content is not None
    
    # Title
    st.title("🔗 Neo4j yFiles Visualization")
    
    # Sidebar with connection info only
    with st.sidebar:
        st.header("📊 Configuration")
        
        # Display connection info
        if "graph" in st.session_state:
            st.success("✅ Connected to Neo4j")
            st.caption(f"Database: {st.session_state.database_name}")
            st.caption(f"Model: {st.session_state.model_name}")
    
    # Simple question input
    question = st.text_input(
        "Enter your question:",
        placeholder="e.g., Show me all customers and their orders",
        label_visibility="collapsed"
    )
    
    if st.button("Visualize", type="primary"):
        if question:
            with st.spinner("Processing..."):
                result = asyncio.run(run_query(st.session_state.agent, question))
                
                if result:
                    # Extract graph data from the result object
                    cyphers = result.get("cyphers", [])
                    if cyphers and len(cyphers) > 0:
                        # Get the first cypher result
                        first_cypher = cyphers[0]
                        result_obj = first_cypher.get("result")
                        
                        # Extract graph data if available
                        if result_obj:
                            try:
                                graph_data = result_obj.graph()
                                st.session_state.graph_nodes = list(graph_data.nodes) if hasattr(graph_data, 'nodes') else []
                                st.session_state.graph_relationships = list(graph_data.relationships) if hasattr(graph_data, 'relationships') else []
                                st.session_state.has_graph_data = len(st.session_state.graph_nodes) > 0
                            except Exception as e:
                                st.session_state.graph_nodes = []
                                st.session_state.graph_relationships = []
                                st.session_state.has_graph_data = False
                                print(f"Could not extract graph data: {e}")
                        else:
                            st.session_state.has_graph_data = False
                        
                        st.session_state.last_cypher = first_cypher.get("statement", "")
                    else:
                        st.session_state.has_graph_data = False
                    
                    st.session_state.raw_workflow_result = result  # Store for debugging
    
    # Debug output
    if st.session_state.get("raw_workflow_result"):
        with st.expander("🔍 Debug: Workflow Output", expanded=True):
            result = st.session_state.raw_workflow_result
            
            # Show the keys in the result
            st.write("**Result keys:**", list(result.keys()) if isinstance(result, dict) else "Not a dict")
            
            # Show graph extraction results
            if st.session_state.get("has_graph_data"):
                st.write("**✅ Graph data extracted successfully:**")
                st.write(f"- Nodes: {len(st.session_state.get('graph_nodes', []))}")
                st.write(f"- Relationships: {len(st.session_state.get('graph_relationships', []))}")
                
                # Show sample node
                if st.session_state.get('graph_nodes'):
                    first_node = st.session_state.graph_nodes[0]
                    st.write("**Sample Node:**")
                    st.write(f"- Labels: {list(first_node.labels) if hasattr(first_node, 'labels') else 'N/A'}")
                    st.write(f"- Properties: {dict(first_node) if hasattr(first_node, '__iter__') else 'N/A'}")
            else:
                st.write("**❌ No graph data to visualize**")
                st.write("(Query may return only scalar values)")
            
            # Show the cypher query
            if st.session_state.get("last_cypher"):
                st.write("**Cypher Query:**")
                st.code(st.session_state.last_cypher, language="cypher")
    
    # Visualization area
    if yfiles_available and st.session_state.get("has_graph_data"):
        # Convert Neo4j graph data to yFiles format
        viz_data = convert_neo4j_to_yfiles_format(
            st.session_state.get("graph_nodes", []),
            st.session_state.get("graph_relationships", [])
        )
        
        # Debug: Show what we're sending to visualization
        with st.expander("📊 Visualization Data", expanded=False):
            st.write(f"Sending {len(viz_data['nodes'])} nodes and {len(viz_data['edges'])} edges to yFiles")
            if viz_data['nodes']:
                st.write("Sample node:", viz_data['nodes'][0])
            if viz_data['edges']:
                st.write("Sample edge:", viz_data['edges'][0])
        
        if viz_data["nodes"] or viz_data["edges"]:
            # Prepare and render visualization
            final_html = html_template
            final_html = final_html.replace('{{BUNDLE_CONTENT}}', bundle_content)
            final_html = final_html.replace('{{CSS_CONTENT}}', css_content)
            final_html = final_html.replace('{{LICENSE_CONTENT}}', license_content)
            
            # Inject the Neo4j data with debug logging
            data_script = f"""
            <script>
                console.log('Visualization data:', {json.dumps(viz_data)});
                window.addEventListener('load', function() {{
                    setTimeout(function() {{
                        if (window.loadNeo4jData) {{
                            console.log('Calling loadNeo4jData with', {len(viz_data["nodes"])} + ' nodes and ' + {len(viz_data["edges"])} + ' edges');
                            window.loadNeo4jData({json.dumps(viz_data)});
                        }} else {{
                            console.error('loadNeo4jData function not found!');
                        }}
                    }}, 500);
                }});
            </script>
            """
            final_html = final_html.replace('</body>', f'{data_script}</body>')
            
            # Render visualization with larger height
            html(final_html, height=900, scrolling=False)
            
            # Show Cypher in expander for debugging
            if st.session_state.get("last_cypher"):
                with st.expander("Cypher Query"):
                    st.code(st.session_state.last_cypher, language="cypher")
        else:
            st.info("No graph data to visualize")
    elif not yfiles_available:
        st.warning("yFiles not configured. Build the bundle: `cd yworks/build && npm run bundle`")


if __name__ == "__main__":
    main()