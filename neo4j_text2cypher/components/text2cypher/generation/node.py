"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.text2cypher.generation.prompts import (
    create_text2cypher_generation_prompt_template,
)
from neo4j_text2cypher.components.text2cypher.state import CypherInputState
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
from neo4j_text2cypher.retrievers.similarity_retriever import SimilarityBasedCypherExampleRetriever

generation_prompt = create_text2cypher_generation_prompt_template()


def create_text2cypher_generation_node(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: Union[ConfigCypherExampleRetriever, SimilarityBasedCypherExampleRetriever],
) -> Callable[[CypherInputState], Coroutine[Any, Any, dict[str, Any]]]:
    text2cypher_chain = generation_prompt | llm | StrOutputParser()

    async def generate_cypher(state: CypherInputState) -> Dict[str, Any]:
        """
        Generates a cypher statement based on the provided schema and user input
        """
        
        # Get examples based on retriever type
        question = state.get("task", "")
        
        if isinstance(cypher_example_retriever, SimilarityBasedCypherExampleRetriever):
            # Use similarity-based selection for better relevance
            examples: str = cypher_example_retriever.get_relevant_examples(question, k=5)
        else:
            # Fallback to original config-based approach
            examples: str = cypher_example_retriever.get_examples()

        generated_cypher = await text2cypher_chain.ainvoke(
            {
                "question": question,
                "fewshot_examples": examples,
                "schema": graph.schema,
            }
        )

        steps = state.get("prev_steps", list()) + ["generate_cypher"]
        
        return {"statement": generated_cypher, "cypher_steps": steps}

    return generate_cypher
