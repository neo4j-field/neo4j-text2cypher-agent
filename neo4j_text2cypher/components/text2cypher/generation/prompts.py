"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_generation_prompt_template(result_limit: int = 50) -> ChatPromptTemplate:
    """
    Create a Text2Cypher generation prompt template.

    Parameters
    ----------
    result_limit : int, optional
        Maximum number of rows to return in query results, by default 50

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Given an input question, convert it to a Cypher query. No pre-amble."
                    "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
                    "Always include a LIMIT clause to prevent excessive results unless the question specifically asks for all results."
                ),
            ),
            (
                "human",
                (
                    f"""You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Begin with MATCH or WITH clauses only. Respond with a Cypher statement only!

IMPORTANT: Always end your query with LIMIT {result_limit} unless the question specifically asks for all results or a different number.

CONTEXT RULES:
- Analyze the semantic intent of the question:
  * Is this requesting ADDITIONAL information about the same entities from recent queries?
  * Is this EXPANDING or MODIFYING a previous analysis?
  * Is this a COMPLETELY NEW topic or question?
  * Does this question only make sense with context from recent queries?

- When "Recent queries from this conversation" are provided:
  * Understand the conversation flow and topic continuity
  * IMPORTANT: If recent queries filtered by specific entities or properties,
    and the current question seems to be adding/expanding the analysis, MAINTAIN those filters
  * When a question appears to be requesting more information in the same context, preserve entity filters
    even if the specific attributes being queried are different
  * Only treat as independent if the question explicitly mentions DIFFERENT entities or is clearly unrelated
  * Trust your language understanding to determine when context is relevant

- Examples of semantic intent (not rigid patterns):
  * Continuation: Brief questions that expand on previous topics
  * Reference: Questions using pronouns or incomplete references
  * Addition: Questions requesting more data about the same entities
  * New Topic: Complete questions about different entities or analyses

- Maintain consistency with node labels, properties, and patterns from the examples
- DO NOT invent new node types or properties - use only patterns shown in the examples

Below are example questions and their corresponding Cypher queries. These are your ONLY reference for valid patterns:

{{fewshot_examples}}

User input: {{question}}
Cypher query:"""
                ),
            ),
        ]
    )
