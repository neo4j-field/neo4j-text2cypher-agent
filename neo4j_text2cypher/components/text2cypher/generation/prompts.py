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

CRITICAL INSTRUCTIONS:
- You MUST base your Cypher query ONLY on the example templates provided below
- DO NOT invent or create new properties, labels, or relationships that are not in the examples
- Use the EXACT same node labels as shown in the examples
- Use the EXACT same property names as shown in the examples
- Study the examples carefully and follow their exact syntax and naming conventions
- If you cannot find a relevant example pattern, use the closest matching example

Below are example questions and their corresponding Cypher queries. These are your ONLY reference for valid patterns:

{{fewshot_examples}}

User input: {{question}}
Cypher query:"""
                ),
            ),
        ]
    )
