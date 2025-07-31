"""Configuration-based Cypher example retriever."""

from typing import List

from neo4j_text2cypher.utils.config import ConfigLoader, ExampleQuery


class ConfigCypherExampleRetriever:
    """Retriever that loads examples from app configuration."""

    def __init__(self, config_path: str):
        """Initialize with path to app config file."""
        self.config_loader = ConfigLoader(config_path)

    def get_examples(self) -> str:
        """Get formatted example queries from the configuration."""
        example_queries = self.config_loader.get_example_queries()
        return self._format_examples_list(example_queries)
    

    def _format_examples_list(self, examples: List[ExampleQuery]) -> str:
        """Format example queries for use in prompts."""
        return ("\n" * 2).join(
            [
                f"Question: {example.question}\nCypher: {self._format_cypher_for_example(example.cql)}"
                for example in examples
            ]
        )

    def _format_cypher_for_example(self, cypher: str) -> str:
        """
        Formats Cypher for use in LangChain's Example Templates.
        This involves replacing '{' with '{{' and '}' with '}}'.
        """
        cypher = cypher.replace("{", "{{")
        return cypher.replace("}", "}}")
