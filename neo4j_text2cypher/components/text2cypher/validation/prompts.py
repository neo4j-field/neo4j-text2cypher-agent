"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_validation_prompt_template() -> ChatPromptTemplate:
    """
    Create a Text2Cypher validation prompt template for semantic validation only.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    validate_cypher_system = """
    You are a Cypher expert reviewing the SEMANTIC correctness of a query.
    Your job is to check if the query retrieves the appropriate data that can be used to answer the user's question.

    CRITICAL: Cypher's role is DATA RETRIEVAL, not data processing.
    - The query should return the raw data needed to answer the question
    - Post-processing (formatting, analysis, summarization) happens AFTER the query executes
    - A query is correct if it returns data containing the information requested, even if that data needs further processing
    - If a query returns paths or nodes that contain the labels/properties needed to answer the question, it is correct

    Focus on whether the query gets the right data, not whether it formats or processes that data.

    DO NOT check schema validity, property existence, or label existence - those are handled separately.
    """

    validate_cypher_user = """Check ONLY these semantic issues:

    1. **Does the query answer the question?**
       - Will it return the data needed to answer the user's question?
       - Is it querying the right type of data?
       - IMPORTANT: If the user asks to "summarize" or "list", the query just needs to RETURN the relevant data
       - DO NOT expect aggregation functions for summarization - that happens after retrieval

    2. **Are there logical errors?**
       - Undefined variables used in WHERE/RETURN clauses
       - Contradictory conditions (e.g., age < 20 AND age > 60)
       - Incorrect aggregations or groupings

    3. **Are critical elements missing?**
       - Missing ORDER BY for "top N" questions
       - Missing LIMIT for questions asking for specific counts
       - Missing aggregation functions for summary questions

    4. **Semantic context validation:**
       - Based on the conversation context, determine if this question appears to be:
         * Requesting ADDITIONAL information about entities from recent queries
         * EXPANDING or MODIFYING a previous analysis
         * A completely NEW and unrelated topic
       - If the question semantically appears to be building on recent queries:
         * Check if the query appropriately maintains entity context (filters, properties)
       - If context seems missing when it should be present, flag as an error
       - Use semantic understanding, not specific word patterns

    5. **Are there obvious performance issues?**
       - Unintentional cartesian products
       - Patterns that will return excessive data

    DO NOT report errors about:
    - Properties not existing
    - Labels not existing
    - Relationships not existing
    - Case sensitivity of names
    - Schema-related issues
    - Missing aggregation/summarization functions (summarization happens AFTER data retrieval)
    - "Visualization" not happening in the query (visualization is done by the UI with the returned data)

    The user's question:
    {question}

    {conversation_context}

    The Cypher statement to validate:
    {cypher}

    Schema information (for context only, do not validate against it):
    {schema}"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                validate_cypher_system,
            ),
            (
                "human",
                (validate_cypher_user),
            ),
        ]
    )
