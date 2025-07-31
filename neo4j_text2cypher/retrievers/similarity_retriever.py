"""Similarity-based Cypher example retriever using semantic similarity."""

from typing import TYPE_CHECKING, List

from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.vectorstores import InMemoryVectorStore

from neo4j_text2cypher.utils.llm_factory import create_embeddings

if TYPE_CHECKING:
    from neo4j_text2cypher.utils.config import ConfigLoader


class SimilarityBasedCypherExampleRetriever:
    """
    Retrieves Cypher examples using semantic similarity search.
    
    Uses LangChain's SemanticSimilarityExampleSelector with InMemoryVectorStore
    to select the most relevant few-shot examples based on question similarity.
    """

    def __init__(self, config_loader: "ConfigLoader", k: int = 5):
        """
        Initialize the similarity-based retriever.
        
        Parameters
        ----------
        config_loader : ConfigLoader
            Configuration loader containing examples and LLM settings
        k : int, optional
            Number of most similar examples to retrieve, by default 5
        """
        self.config_loader = config_loader
        self.k = k
        self._example_selector = None
        self._initialize_selector()

    def _initialize_selector(self) -> None:
        """Initialize the semantic similarity example selector."""
        # Get examples from config (same source as ConfigCypherExampleRetriever)
        examples = self._load_examples_from_config()
        
        if not examples:
            raise ValueError("No examples found in configuration file")
        
        # Create embeddings using same credentials as LLM
        embeddings = create_embeddings(self.config_loader)
        
        # Initialize the semantic similarity selector
        self._example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples=examples,
            embeddings=embeddings,
            vectorstore_cls=InMemoryVectorStore,
            k=self.k,
            input_keys=["question"]
        )

    def _load_examples_from_config(self) -> List[dict]:
        """
        Load examples from the YAML configuration file.
        
        Returns
        -------
        List[dict]
            List of examples with 'question' and 'query' keys
        """
        try:
            # Get examples from the same config source used by ConfigCypherExampleRetriever
            example_queries = self.config_loader.get_example_queries()
            
            # Convert to format expected by SemanticSimilarityExampleSelector
            examples = []
            for i, example in enumerate(example_queries):
                examples.append({
                    "id": f"example_{i}",
                    "question": example.question,
                    "query": example.cql
                })
            
            return examples
        except Exception as e:
            raise ValueError(f"Failed to load examples from configuration: {e}")

    def get_relevant_examples(self, question: str, k: int = None) -> str:
        """
        Get the most relevant examples for a given question.
        
        Parameters
        ----------
        question : str
            The user's question to find similar examples for
        k : int, optional
            Number of examples to return. If None, uses instance default
            
        Returns
        -------
        str
            Formatted string with the most relevant examples
        """
        if self._example_selector is None:
            raise RuntimeError("Example selector not initialized")
        
        # Use provided k or instance default
        num_examples = k if k is not None else self.k
        
        # Get similar examples
        selected_examples = self._example_selector.select_examples(
            {"question": question}, 
            # Note: k parameter needs to be set during initialization
            # For now, we'll get the configured number and slice if needed
        )
        
        # Limit to requested number if needed
        if len(selected_examples) > num_examples:
            selected_examples = selected_examples[:num_examples]
        
        # Format examples for prompt (same format as ConfigCypherExampleRetriever)
        return self._format_examples(selected_examples)

    def _format_examples(self, examples: List[dict]) -> str:
        """
        Format examples for inclusion in prompts.
        
        Parameters
        ----------
        examples : List[dict]
            List of selected examples with 'question' and 'query' keys
            
        Returns
        -------
        str
            Formatted string ready for prompt inclusion
        """
        if not examples:
            return ""
        
        formatted_examples = []
        for example in examples:
            formatted_examples.append(
                f"Question: {example['question']}\n"
                f"Cypher: {example['query']}"
            )
        
        return "\n\n".join(formatted_examples)

    def get_examples(self) -> str:
        """
        Get examples using default question for compatibility.
        
        This method provides compatibility with the existing interface
        used by ConfigCypherExampleRetriever.
        
        Returns
        -------
        str
            Formatted string with all available examples
        """
        # For compatibility, return a subset of examples when no specific question is provided
        # This shouldn't be the primary usage pattern for similarity-based retrieval
        if self._example_selector is None:
            raise RuntimeError("Example selector not initialized")
        
        # Get a representative sample of examples
        all_examples = self._load_examples_from_config()
        sample_examples = all_examples[:self.k] if len(all_examples) > self.k else all_examples
        
        return self._format_examples(sample_examples)