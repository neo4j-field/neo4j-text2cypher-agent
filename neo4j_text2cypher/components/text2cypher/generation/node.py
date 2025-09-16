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


def create_text2cypher_generation_node(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: Union[ConfigCypherExampleRetriever, SimilarityBasedCypherExampleRetriever],
    result_limit: int = 50,
) -> Callable[[CypherInputState], Coroutine[Any, Any, dict[str, Any]]]:
    generation_prompt = create_text2cypher_generation_prompt_template(result_limit)
    text2cypher_chain = generation_prompt | llm | StrOutputParser()

    async def generate_cypher(state: CypherInputState) -> Dict[str, Any]:
        """
        Generates a cypher statement based on the provided schema and user input
        """

        # Get examples based on retriever type
        question = state.get("task", "")

        # Get conversation context
        conversation_history = state.get("conversation_history", [])
        recent_cyphers = state.get("recent_cyphers", [])

        if isinstance(cypher_example_retriever, SimilarityBasedCypherExampleRetriever):
            # Use similarity-based selection for better relevance
            examples: str = cypher_example_retriever.get_relevant_examples(question, k=5)
            # Count actual examples in the returned string
            example_count = examples.count("Question:")
            print(f"\n📚 Semantic Similarity Retriever for '{question}' - Retrieved {example_count} examples:")
            print("=" * 80)
            print(examples)
            print("=" * 80)
        else:
            # Fallback to original config-based approach
            examples: str = cypher_example_retriever.get_examples()
            print(f"\n📚 Config-based Retriever - Using all configured examples")

        # Build context from recent conversation (questions + their successful Cypher)
        contextual_examples = ""
        if conversation_history:
            # Extract recent question-cypher pairs
            recent_pairs = []
            for record in conversation_history[-5:]:  # Look at last 5 conversations
                hist_question = record.get("question", "")  # Use different variable name to avoid collision
                # Get the first successful Cypher from this conversation
                for cypher in record.get("cyphers", []):
                    if cypher.get("statement") and cypher.get("records"):
                        recent_pairs.append({
                            "question": hist_question,
                            "cypher": cypher["statement"]
                        })
                        break  # Take only first successful query per question

            # Format as examples if we have any pairs
            if recent_pairs:
                contextual_examples = "\n\nRecent queries from this conversation:\n"
                for pair in recent_pairs:
                    contextual_examples += f"Question: {pair['question']}\n"
                    contextual_examples += f"Cypher: {pair['cypher']}\n\n"

                print(f"\n🔄 Adding {len(recent_pairs)} recent question-cypher pairs as context")
                print(f"   Context preview: {contextual_examples[:300]}...")

        # Append contextual examples to the main examples
        full_examples = examples + contextual_examples

        # Print the full prompt being sent to the LLM
        print(f"\n🔍 Generation Prompt Details:")
        print(f"   Question: {question}")
        print(f"   Examples length: {len(examples)} characters")
        print(f"   Context length: {len(contextual_examples)} characters")
        print(f"   Total examples length: {len(full_examples)} characters")
        print(f"   Note: Generation uses only examples, not schema (as of commit eedfcda)")

        generated_cypher = await text2cypher_chain.ainvoke(
            {
                "question": question,
                "fewshot_examples": full_examples,
            }
        )

        print(f"   Generated Cypher: {generated_cypher}")

        steps = state.get("prev_steps", list()) + ["generate_cypher"]

        return {"statement": generated_cypher, "cypher_steps": steps}

    return generate_cypher
