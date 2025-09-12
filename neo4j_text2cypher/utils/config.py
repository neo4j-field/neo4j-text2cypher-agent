"""Unified configuration loader for Neo4j Text2Cypher applications."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """Neo4j connection configuration."""

    database: str = Field(default="neo4j", description="Neo4j database name")
    uri: Optional[str] = Field(default=None, description="Neo4j connection URI")
    username: str = Field(default="neo4j", description="Neo4j username")
    password: Optional[str] = Field(default=None, description="Neo4j password")
    enhanced_schema: bool = Field(default=True, description="Enable enhanced schema")


class PlannerBehaviourConfig(BaseModel):
    """Configuration for planner behaviour in query processing."""
    
    break_into_subquestions: bool = Field(
        default=False,
        description="Whether to break complex questions into subquestions"
    )
    user_editable: bool = Field(
        default=True,
        description="Whether users can modify this setting in the UI"
    )


class RetrieverStrategyConfig(BaseModel):
    """Configuration for retriever strategy in query processing."""
    
    type: str = Field(
        default="semantic_similarity",
        description="Retriever type: 'semantic_similarity' or 'static'"
    )
    k_value: int = Field(
        default=10,
        description="Number of examples to retrieve for semantic similarity"
    )
    k_min: int = Field(
        default=1,
        description="Minimum k value for semantic similarity slider"
    )
    k_max: int = Field(
        default=20,
        description="Maximum k value for semantic similarity slider"
    )
    user_editable: bool = Field(
        default=True,
        description="Whether users can modify this setting in the UI"
    )


class ResultLimitConfig(BaseModel):
    """Configuration for query result limits."""
    
    default: int = Field(
        default=100,
        description="Default maximum number of query results"
    )
    options: List[int] = Field(
        default=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        description="Available options for result limit"
    )
    user_editable: bool = Field(
        default=True,
        description="Whether users can modify this setting in the UI"
    )


class SidebarQueryProcessingConfig(BaseModel):
    """Configuration for sidebar query processing settings."""
    
    show_in_sidebar: bool = Field(
        default=True,
        description="Whether to show query processing settings in the sidebar"
    )
    planner_behaviour: PlannerBehaviourConfig = Field(
        default_factory=PlannerBehaviourConfig,
        description="Planner behaviour configuration"
    )
    retriever_strategy: RetrieverStrategyConfig = Field(
        default_factory=RetrieverStrategyConfig,
        description="Retriever strategy configuration"
    )
    result_limit: ResultLimitConfig = Field(
        default_factory=ResultLimitConfig,
        description="Result limit configuration"
    )


class StreamlitUIConfig(BaseModel):
    """Streamlit UI configuration."""

    title: str = Field(description="Application title")
    scope_description: str = Field(description="Description of what the app can answer")
    example_questions: List[str] = Field(
        default=[], description="Example questions for the UI"
    )
    sidebar_query_processing: SidebarQueryProcessingConfig = Field(
        default_factory=SidebarQueryProcessingConfig,
        description="Query processing settings for the sidebar"
    )


class ExampleQuery(BaseModel):
    """Individual example query with question and CQL."""

    question: str = Field(description="Natural language question")
    cql: str = Field(description="Corresponding Cypher query")


class LLMConfig(BaseModel):
    """Language model configuration."""

    provider: str = Field(
        default="openai",
        description="LLM provider: 'openai' or 'azure_openai'"
    )
    model: str = Field(
        default="gpt-4o",
        description="Model name to use (e.g., 'gpt-4o', 'gpt-3.5-turbo')"
    )
    temperature: float = Field(
        default=0.0,
        description="Temperature for response randomness (0.0-1.0)",
        ge=0.0,
        le=1.0
    )





class UnifiedAppConfig(BaseModel):
    """Unified application configuration combining all settings."""

    streamlit_ui: StreamlitUIConfig = Field(description="Streamlit UI settings")
    neo4j: Neo4jConfig = Field(description="Neo4j connection settings")
    llm: LLMConfig = Field(
        default_factory=LLMConfig, description="Language model settings"
    )
    example_queries: List[ExampleQuery] = Field(
        default=[], description="Example question-cypher pairs"
    )


class ConfigLoader:
    """Loads and merges configuration from YAML file and environment variables."""

    def __init__(self, config_path: Union[str, Path]):
        """Initialize with path to app config YAML file."""
        self.config_path = Path(config_path)
        self._raw_config: Optional[Dict[str, Any]] = None
        self._unified_config: Optional[UnifiedAppConfig] = None

    def load_config(self) -> UnifiedAppConfig:
        """Load and parse the unified configuration."""
        if self._unified_config is not None:
            return self._unified_config

        # Load YAML file
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._raw_config = yaml.safe_load(f)

        # Extract sections
        streamlit_config = self._raw_config.get("streamlit_ui", {})
        neo4j_config = self._raw_config.get("neo4j", {})
        llm_config = self._raw_config.get("llm", {})
        example_queries = self._raw_config.get("example_queries", [])
        # Merge Neo4j config with environment variables
        merged_neo4j_config = self._merge_neo4j_config(neo4j_config)

        # Parse example queries (handle both new and legacy formats)
        parsed_queries = self._parse_example_queries(example_queries)

        # Create unified config
        self._unified_config = UnifiedAppConfig(
            streamlit_ui=StreamlitUIConfig(**streamlit_config),
            neo4j=Neo4jConfig(**merged_neo4j_config),
            llm=LLMConfig(**llm_config),
            example_queries=parsed_queries,
        )

        return self._unified_config

    def _merge_neo4j_config(self, yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge YAML Neo4j config with environment variables."""
        # Start with defaults from environment
        merged_config = {
            "database": os.getenv("NEO4J_DATABASE", "neo4j"),
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "enhanced_schema": True,
        }

        # Override with YAML config (app-specific settings take precedence)
        merged_config.update(yaml_config)

        return merged_config


    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return str(value).lower() in ("true", "1", "yes", "on")

    def _parse_example_queries(
        self, queries_data: List[Dict[str, Any]]
    ) -> List[ExampleQuery]:
        """Parse example queries from unified format."""
        if not queries_data:
            return []

        parsed_queries = []
        for query in queries_data:
            if isinstance(query, dict) and "question" in query and "cql" in query:
                parsed_queries.append(
                    ExampleQuery(question=query["question"], cql=query["cql"])
                )

        return parsed_queries

    def get_neo4j_connection_params(self) -> Dict[str, Any]:
        """Get Neo4j connection parameters from environment, falling back to config."""
        config = self.load_config()

        return {
            "url": os.getenv("NEO4J_URI", config.neo4j.uri),
            "username": os.getenv("NEO4J_USERNAME", config.neo4j.username),
            "password": os.getenv("NEO4J_PASSWORD", config.neo4j.password),
            "database": os.getenv("NEO4J_DATABASE", config.neo4j.database),
            "enhanced_schema": config.neo4j.enhanced_schema,
        }

    def get_streamlit_config(self) -> StreamlitUIConfig:
        """Get Streamlit UI configuration."""
        return self.load_config().streamlit_ui

    def get_example_queries(self) -> List[ExampleQuery]:
        """Get parsed example queries."""
        return self.load_config().example_queries
    


    def get_llm_config(self) -> LLMConfig:
        """
        Get language model configuration.
        
        Returns
        -------
        LLMConfig
            LLM configuration with provider, model, and temperature settings
        """
        return self.load_config().llm

